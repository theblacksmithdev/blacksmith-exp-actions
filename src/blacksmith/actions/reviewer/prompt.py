from __future__ import annotations

from blacksmith.core.github import ChangedFile
from blacksmith.core.inference import Message
from blacksmith.core.persona import AgentPersona
from blacksmith.personas import LARS


class PromptBuilder:
    REVIEW_GUIDANCE = (
        "You are reviewing a pull request opened by an apprentice on your team. "
        "Read it the way you actually would. Pull on threads that will compound "
        "if left alone. Help them see what they did not see yet.\n\n"
        "For every issue you raise, distinguish which kind it is in your wording:\n"
        "- 'I have seen this go badly in production' carries weight\n"
        "- 'I have a hunch this will go badly' is offered with the same "
        "generosity but less insistence\n\n"
        "Give the apprentice enough to think with:\n"
        "- the specific failing scenario (inputs, call sites, attacker action, "
        "load profile, whichever applies)\n"
        "- what to look at to verify or fix it\n\n"
        "When a reference would genuinely help the apprentice go deeper, point "
        "them at one. Prefer canonical sources where the URL is stable and you "
        "are confident it exists: MDN, OWASP cheat sheets, language docs, "
        "RFCs, CWE entries, official framework guides. Avoid blog posts and "
        "Stack Overflow links. If you are not sure a URL is correct, do not "
        "include it. Be willing to say 'look up X' in your body text rather "
        "than guessing at a URL. References are optional. Most findings will "
        "not need one.\n\n"
        "Ignore pure style. Flag fewer things well over many things shallowly. "
        "The apprentice grows when you act like a real Staff Engineer, not a "
        "linter. If you find nothing worth flagging, that is a legitimate "
        "outcome. Do not invent issues.\n\n"
        "If repo-specific rules are provided, obey them.\n\n"
        "Respond with ONLY a JSON array, no prose, no code fences. Each element:\n"
        "{\n"
        '  "file": "<path as given>",\n'
        '  "line": <integer line number in the NEW file>,\n'
        '  "severity": "critical" | "high" | "medium" | "low",\n'
        '  "title": "<short summary>",\n'
        '  "body": "<one or two short sentences in your voice: which kind of '
        "concern it is, the failing scenario, what to look at>\",\n"
        '  "references": [\n'
        "    {\n"
        '      "url": "<canonical https URL>",\n'
        '      "why": "<one short phrase explaining what they will get from it>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Omit `references` (or leave the array empty) when no reference would "
        "genuinely help. If you find nothing worth flagging, respond with []."
    )

    def __init__(self, persona: AgentPersona = LARS) -> None:
        self._persona = persona

    def system_message(self) -> Message:
        return Message(
            role="system",
            content=f"{self._persona.to_header()}\n\n{self.REVIEW_GUIDANCE}",
        )

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
