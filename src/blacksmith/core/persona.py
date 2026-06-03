from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AgentPersona"]


@dataclass(frozen=True)
class AgentPersona:
    """Slim mirror of the main Blacksmith Experience `AgentPersona`.

    Source of truth lives in the main project at `framework/persona.py`.
    Keep field names and semantics aligned so personas can be swapped
    in/out if we ever pip-install the main package as a dependency.
    Fields not relevant to PR review (email, phone, voice, image_url)
    are omitted intentionally.
    """

    name: str
    role: str
    intro: str
    personality: str
    pronouns: str = "they/them"
    location: str | None = None
    family: str | None = None
    background: str | None = None
    interests: str | None = None

    def to_header(self) -> str:
        sections: list[str] = [
            f"You are {self.name}, a {self.role}.",
            f"Pronouns: {self.pronouns}.",
            "",
            "Personality:",
            self.personality,
        ]
        bio = self._render_bio()
        if bio:
            sections.extend(["", bio])
        sections.extend(["", self._instruction_footer()])
        return "\n".join(sections)

    def _render_bio(self) -> str:
        bullets: list[str] = []
        for label, value in (
            ("Where you live", self.location),
            ("Family", self.family),
            ("Background", self.background),
            ("Outside of work", self.interests),
        ):
            if value:
                bullets.append(f"- {label}: {value}")
        if not bullets:
            return ""
        return "Your life (reference naturally when relevant):\n" + "\n".join(bullets)

    def _instruction_footer(self) -> str:
        return (
            f"Stay in character. Write in first person as {self.name}. Be willing "
            f"to disagree, hold a position, and ask hard questions when the "
            f"situation calls for it. Never claim to be an AI unless the user "
            f"directly asks.\n\n"
            f"STYLE RULES for everything you write:\n"
            f"- Do not use em-dashes or any long dash. Use commas, periods, or a "
            f"new sentence instead. Long dashes read as performative and put "
            f"people off.\n"
            f"- No semicolons.\n"
            f"- Short to medium sentences. Speak in messages, not paragraphs.\n"
            f"- No product jargon. Never say 'calibrate', 'calibration', 'signal', "
            f"'phase', or 'starting level'. Those are internal words.\n"
            f"- No corporate filler: 'engineering excellence', 'growth journey', "
            f"'your success matters'."
        )
