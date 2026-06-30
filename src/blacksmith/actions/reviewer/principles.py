from __future__ import annotations

from pydantic import BaseModel

from blacksmith.core.inference import Message
from blacksmith.core.persona import AgentPersona
from blacksmith.personas import LARS

__all__ = ["PrinciplesBuilder", "PrinciplesResponse"]


class PrinciplesResponse(BaseModel):
    body: str


class PrinciplesBuilder:
    """Builds the prompt for the principles-based fallback note.

    Used when the normal line-by-line review cannot run. The note speaks in
    Lars's voice and points the apprentice at standard engineering
    principles to self-audit against. Kept deliberately tiny so the second
    call lands even when the first one didn't.
    """

    PRINCIPLES_GUIDANCE = (
        "You cannot give the apprentice a line-by-line review on this PR "
        "right now. Rather than say nothing, write a short note in your "
        "voice pointing them at the standard engineering principles you "
        "would walk this change against, and ask them to do that walk "
        "themselves before merging.\n\n"
        "The principles you actually care about:\n"
        "- Small, focused PRs. One logical concern per PR.\n"
        "- Clear module boundaries. Each module has a single reason to "
        "change. New code lives where its responsibility already lives.\n"
        "- Naming. Names make the intent obvious without a comment.\n"
        "- Tests. New behaviour gets a test that would fail without it.\n"
        "- Readability over cleverness. The next reader pays for the "
        "choice you make today.\n"
        "- Error handling at boundaries, not sprinkled through the body.\n\n"
        "Pick two or three of those, no more, that you would emphasise "
        "for this change given its title and shape. Do not list all of "
        "them. Do not explain each one. Two to four sentences total. The "
        "apprentice should leave the comment knowing what you would be "
        "looking for and able to walk the PR through it themselves.\n\n"
        "Do not:\n"
        "- Do not mention models, AI, tools, tokens, context windows, or "
        "input limits. None of that is your concern or theirs.\n"
        "- Do not list the files. They wrote the PR.\n"
        "- Do not apologise for not reviewing in depth.\n"
        "- Do not lecture. A senior says less, not more.\n"
        "- Do not threaten or moralise.\n\n"
        "Respond with ONLY a JSON object, no prose, no code fences:\n"
        "{\n"
        '  "body": "<your note, in your voice>"\n'
        "}"
    )

    def __init__(self, persona: AgentPersona = LARS) -> None:
        self._persona = persona

    def messages(
        self,
        *,
        pr_title: str,
        file_count: int,
        additions: int,
        deletions: int,
    ) -> list[Message]:
        title = pr_title.strip() or "(no title)"
        return [
            Message(
                role="system",
                content=f"{self._persona.to_header()}\n\n{self.PRINCIPLES_GUIDANCE}",
            ),
            Message(
                role="user",
                content=(
                    f"PR title: {title}\n"
                    f"Files changed: {file_count}\n"
                    f"Lines added: {additions}\n"
                    f"Lines removed: {deletions}"
                ),
            ),
        ]
