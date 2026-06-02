from __future__ import annotations

from blacksmith.actions.reviewer.findings import Finding
from blacksmith.actions.reviewer.review import ReviewBuilder
from blacksmith.actions.reviewer.severity import Severity


def _f(file: str, line: int, sev: Severity, title: str = "t", body: str = "b") -> Finding:
    return Finding(file=file, line=line, severity=sev, title=title, body=body)


class TestReviewBuilder:
    def test_clean_review_when_no_findings(self) -> None:
        builder = ReviewBuilder([], {})
        review = builder.build("sha")
        assert review.event == "COMMENT"
        assert review.comments == []
        assert "No issues found" in review.body

    def test_critical_triggers_request_changes(self) -> None:
        findings = [_f("a.py", 1, Severity.CRITICAL)]
        builder = ReviewBuilder(findings, {"a.py": {1}})
        review = builder.build("sha")
        assert review.event == "REQUEST_CHANGES"

    def test_non_critical_is_comment(self) -> None:
        findings = [_f("a.py", 1, Severity.HIGH)]
        builder = ReviewBuilder(findings, {"a.py": {1}})
        review = builder.build("sha")
        assert review.event == "COMMENT"

    def test_splits_inline_vs_summary(self) -> None:
        findings = [
            _f("a.py", 1, Severity.LOW),
            _f("a.py", 99, Severity.MEDIUM),
            _f("b.py", 5, Severity.HIGH),
        ]
        anchors = {"a.py": {1, 2}, "b.py": {5, 6}}
        builder = ReviewBuilder(findings, anchors)
        review = builder.build("sha")
        assert builder.inline_count == 2
        assert builder.summary_only_count == 1
        assert {c.path for c in review.comments} == {"a.py", "b.py"}
        assert "a.py:99" in review.body
