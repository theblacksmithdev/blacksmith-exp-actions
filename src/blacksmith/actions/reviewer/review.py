from __future__ import annotations

from blacksmith.actions.reviewer.findings import Finding, Reference
from blacksmith.actions.reviewer.severity import Severity
from blacksmith.core.github import ReviewBody, ReviewComment


class ReviewBuilder:
    FALLBACK_SUMMARY = "Nothing to add."

    def __init__(
        self,
        findings: list[Finding],
        anchor_map: dict[str, set[int]],
        summary: str,
    ) -> None:
        self._findings = findings
        self._anchor_map = anchor_map
        self._summary = summary.strip() or self.FALLBACK_SUMMARY
        self._inline, self._summary_only = self._split()

    @property
    def inline_count(self) -> int:
        return len(self._inline)

    @property
    def summary_only_count(self) -> int:
        return len(self._summary_only)

    def build(self, head_sha: str) -> ReviewBody:
        return ReviewBody(
            commit_id=head_sha,
            body=self._body(),
            event=self._event_type(),
            comments=[self._to_comment(f) for f in self._inline],
        )

    def _split(self) -> tuple[list[Finding], list[Finding]]:
        inline: list[Finding] = []
        summary: list[Finding] = []
        for finding in self._findings:
            anchors = self._anchor_map.get(finding.file, set())
            (inline if finding.line in anchors else summary).append(finding)
        return inline, summary

    def _event_type(self) -> str:
        has_critical = any(f.severity == Severity.CRITICAL for f in self._findings)
        return "REQUEST_CHANGES" if has_critical else "COMMENT"

    def _body(self) -> str:
        if not self._summary_only:
            return self._summary
        lines = [self._summary, "", "---", "", "_Notes I couldn't anchor to a specific line:_"]
        for finding in self._summary_only:
            lines.append(self._format_summary_item(finding))
        return "\n".join(lines)

    @classmethod
    def _format_summary_item(cls, finding: Finding) -> str:
        head = (
            f"- `{finding.file}:{finding.line}` _(**{finding.severity.label}**)_ "
            f"**{finding.title}**: {finding.body}"
        )
        refs = cls._render_references(finding.references, inline=True)
        return f"{head}{refs}" if refs else head

    @classmethod
    def _to_comment(cls, finding: Finding) -> ReviewComment:
        body = f"**[{finding.severity.label}] {finding.title}**\n\n{finding.body}"
        refs = cls._render_references(finding.references, inline=False)
        return ReviewComment(
            path=finding.file,
            line=finding.line,
            side="RIGHT",
            body=f"{body}{refs}" if refs else body,
        )

    @staticmethod
    def _render_references(references: list[Reference], *, inline: bool) -> str:
        if not references:
            return ""
        if inline:
            parts = [f"[{r.why}]({r.url})" for r in references]
            return " " + " · ".join(parts)
        lines = ["", "", "**Read more:**"]
        lines.extend(f"- [{r.why}]({r.url})" for r in references)
        return "\n".join(lines)
