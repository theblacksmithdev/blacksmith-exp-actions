from __future__ import annotations

from blacksmith.actions.reviewer.findings import Finding, Reference
from blacksmith.actions.reviewer.review import ReviewBuilder
from blacksmith.actions.reviewer.severity import Severity

DEFAULT_SUMMARY = "Ship it."


def _f(
    file: str,
    line: int,
    sev: Severity,
    title: str = "t",
    body: str = "b",
    references: list[Reference] | None = None,
) -> Finding:
    return Finding(
        file=file,
        line=line,
        severity=sev,
        title=title,
        body=body,
        references=references or [],
    )


def _ref(url: str, why: str) -> Reference:
    return Reference(url=url, why=why)


class TestReviewBuilder:
    def test_summary_is_used_as_body_when_no_findings(self) -> None:
        builder = ReviewBuilder([], {}, summary="Looks clean. Ship it.")
        review = builder.build("sha")
        assert review.event == "COMMENT"
        assert review.comments == []
        assert review.body == "Looks clean. Ship it."

    def test_empty_summary_falls_back_to_default(self) -> None:
        builder = ReviewBuilder([], {}, summary="")
        assert builder.build("sha").body == ReviewBuilder.FALLBACK_SUMMARY

    def test_whitespace_only_summary_falls_back_to_default(self) -> None:
        builder = ReviewBuilder([], {}, summary="   \n  ")
        assert builder.build("sha").body == ReviewBuilder.FALLBACK_SUMMARY

    def test_critical_triggers_request_changes(self) -> None:
        findings = [_f("a.py", 1, Severity.CRITICAL)]
        builder = ReviewBuilder(findings, {"a.py": {1}}, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert review.event == "REQUEST_CHANGES"

    def test_non_critical_is_comment(self) -> None:
        findings = [_f("a.py", 1, Severity.HIGH)]
        builder = ReviewBuilder(findings, {"a.py": {1}}, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert review.event == "COMMENT"

    def test_body_starts_with_lars_summary_not_stats(self) -> None:
        findings = [_f("a.py", 1, Severity.HIGH)]
        builder = ReviewBuilder(
            findings, {"a.py": {1}}, summary="The auth handler is doing too much."
        )
        review = builder.build("sha")
        assert review.body.startswith("The auth handler is doing too much.")
        assert "1 finding" not in review.body
        assert "high," not in review.body

    def test_inline_comment_renders_read_more_block_for_references(self) -> None:
        finding = _f(
            "a.py",
            1,
            Severity.HIGH,
            references=[_ref("https://owasp.org/x", "OWASP on input validation")],
        )
        builder = ReviewBuilder([finding], {"a.py": {1}}, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert len(review.comments) == 1
        body = review.comments[0].body
        assert "**Read more:**" in body
        assert "[OWASP on input validation](https://owasp.org/x)" in body

    def test_inline_comment_has_no_read_more_block_when_no_references(self) -> None:
        finding = _f("a.py", 1, Severity.HIGH)
        builder = ReviewBuilder([finding], {"a.py": {1}}, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert "Read more" not in review.comments[0].body

    def test_summary_item_renders_inline_reference_links(self) -> None:
        finding = _f(
            "a.py",
            99,
            Severity.LOW,
            references=[_ref("https://mdn.io/x", "MDN reference")],
        )
        builder = ReviewBuilder([finding], {"a.py": {1}}, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert "[MDN reference](https://mdn.io/x)" in review.body

    def test_body_framing_uses_no_em_dashes(self) -> None:
        findings = [_f("a.py", 1, Severity.HIGH)]
        builder = ReviewBuilder(
            findings,
            {"a.py": {1}},
            summary="A summary without dashes.",
        )
        review = builder.build("sha")
        assert "—" not in review.body
        for comment in review.comments:
            assert "—" not in comment.body

    def test_splits_inline_vs_summary(self) -> None:
        findings = [
            _f("a.py", 1, Severity.LOW),
            _f("a.py", 99, Severity.MEDIUM),
            _f("b.py", 5, Severity.HIGH),
        ]
        anchors = {"a.py": {1, 2}, "b.py": {5, 6}}
        builder = ReviewBuilder(findings, anchors, summary=DEFAULT_SUMMARY)
        review = builder.build("sha")
        assert builder.inline_count == 2
        assert builder.summary_only_count == 1
        assert {c.path for c in review.comments} == {"a.py", "b.py"}
        assert "a.py:99" in review.body

    def test_summary_only_findings_appear_below_summary_in_their_own_section(self) -> None:
        findings = [_f("a.py", 99, Severity.MEDIUM, title="orphan note")]
        anchors: dict[str, set[int]] = {"a.py": {1}}
        builder = ReviewBuilder(
            findings, anchors, summary="The bones are right. One stray note below."
        )
        review = builder.build("sha")
        assert review.body.startswith("The bones are right. One stray note below.")
        assert "Notes I couldn't anchor" in review.body
        assert "orphan note" in review.body
