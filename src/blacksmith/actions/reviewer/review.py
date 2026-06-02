from __future__ import annotations

from blacksmith.actions.reviewer.findings import Finding
from blacksmith.actions.reviewer.severity import Severity
from blacksmith.core.github import ReviewBody, ReviewComment


class ReviewBuilder:
    HEADING = "### Blacksmith review"
    CLEAN_BODY = f"{HEADING}\n\n✅ No issues found."

    def __init__(
        self,
        findings: list[Finding],
        anchor_map: dict[str, set[int]],
    ) -> None:
        self._findings = findings
        self._anchor_map = anchor_map
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
        if not self._findings:
            return self.CLEAN_BODY
        total = len(self._findings)
        counts = {sev: 0 for sev in Severity}
        for finding in self._findings:
            counts[finding.severity] += 1
        plural = "s" if total != 1 else ""
        header = (
            f"{self.HEADING}\n\n"
            f"**{total} finding{plural}** — "
            f"{counts[Severity.CRITICAL]} critical, "
            f"{counts[Severity.HIGH]} high, "
            f"{counts[Severity.MEDIUM]} medium, "
            f"{counts[Severity.LOW]} low."
        )
        if not self._summary_only:
            return header
        lines = [header, "", "#### Comments without an inline anchor"]
        for finding in self._summary_only:
            lines.append(
                f"- `{finding.file}:{finding.line}` _(**{finding.severity.label}**)_ — "
                f"**{finding.title}** — {finding.body}"
            )
        return "\n".join(lines)

    @staticmethod
    def _to_comment(finding: Finding) -> ReviewComment:
        return ReviewComment(
            path=finding.file,
            line=finding.line,
            side="RIGHT",
            body=f"**[{finding.severity.label}] {finding.title}**\n\n{finding.body}",
        )
