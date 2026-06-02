from __future__ import annotations

from blacksmith.core.github import ChangedFile
from blacksmith.core.inference import Message


class PromptBuilder:
    SYSTEM_PROMPT = (
        "You are Dev, a senior code reviewer.\n\n"
        "Review the provided pull request diff for:\n"
        "- correctness bugs\n"
        "- security issues\n"
        "- clear design problems\n\n"
        "Be adversarial but precise. Only flag an issue when you can name a concrete\n"
        "failing scenario (specific inputs, specific call sites, or a specific\n"
        "attacker action that exploits it). Ignore pure style. If repo-specific review\n"
        "rules are provided, obey them.\n\n"
        "Respond with ONLY a JSON array, no prose, no code fences. Each element:\n"
        "{\n"
        '  "file": "<path as given>",\n'
        '  "line": <integer line number in the NEW file>,\n'
        '  "severity": "critical" | "high" | "medium" | "low",\n'
        '  "title": "<short summary>",\n'
        '  "body": "<one or two sentences: the concrete failing scenario and the fix>"\n'
        "}\n\n"
        "If you find nothing worth flagging, respond with []."
    )

    def system_message(self) -> Message:
        return Message(role="system", content=self.SYSTEM_PROMPT)

    def user_message(
        self,
        *,
        pr_title: str,
        rules: str | None,
        files: list[ChangedFile],
    ) -> Message:
        parts: list[str] = [f"Pull request title: {pr_title}", ""]
        if rules:
            parts.extend(["Repo-specific review rules:", rules.strip(), ""])
        parts.append("Changed files (unified diff patches):")
        for file in files:
            parts.extend(["", f"### {file.filename}", "```diff", file.patch or "", "```"])
        return Message(role="user", content="\n".join(parts))
