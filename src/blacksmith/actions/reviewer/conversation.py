from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from blacksmith.core.inference import Message
from blacksmith.core.persona import AgentPersona
from blacksmith.personas import LARS

__all__ = ["ConversationBuilder", "ReplyResponse", "ThreadComment"]


@dataclass(frozen=True)
class ThreadComment:
    author: str
    body: str


class ReplyResponse(BaseModel):
    body: str


class ConversationBuilder:
    CONVERSATION_GUIDANCE = (
        "You are continuing a thread on a pull request. The apprentice has "
        "replied to a review you posted earlier, or has mentioned you on the "
        "PR. Respond the way you would in any PR thread, not the way a bot "
        "would.\n\n"
        "Things you can do:\n"
        "- Engage with the argument they actually made. If they convinced "
        "you, change your mind out loud. That is the most valuable thing "
        "you can model.\n"
        "- Hold your ground if you still disagree. Same crispness as your "
        "reviews. Two sentences usually do it.\n"
        "- Ask one clarifying question only if you actually need the "
        "answer. Do not ask for the sake of asking.\n"
        "- Acknowledge briefly if they just said 'thanks' or 'I will fix "
        "this'. A line is enough.\n\n"
        "Do not:\n"
        "- Do not praise them. No 'great point', 'thanks for the pushback', "
        "'good question'. Engage with substance instead.\n"
        "- Do not apologize for your earlier review. If you were wrong, say "
        "you were wrong and what you missed. That is different from sorry.\n"
        "- Do not restate the original finding. They can scroll up.\n"
        "- Do not write a paragraph when a sentence is enough. Match the "
        "length they wrote you, give or take.\n"
        "- Do not pretend to remember anything outside the thread context "
        "you have been given.\n"
        "- Do not summarize the thread for them. They were there.\n\n"
        "Respond with ONLY a JSON object, no prose, no code fences:\n"
        "{\n"
        '  "body": "<your reply, in your voice>"\n'
        "}"
    )

    def __init__(self, persona: AgentPersona = LARS) -> None:
        self._persona = persona

    def messages(
        self,
        *,
        pr_title: str,
        pr_body: str | None,
        thread: list[ThreadComment],
        bot_login: str,
    ) -> list[Message]:
        result: list[Message] = [
            Message(
                role="system",
                content=f"{self._persona.to_header()}\n\n{self.CONVERSATION_GUIDANCE}",
            ),
            Message(
                role="user",
                content=(
                    f"PR title: {pr_title}\n\n"
                    f"PR body:\n{(pr_body or '(no description)').strip()}\n\n"
                    "Below is the PR thread, oldest first. Reply to the most "
                    "recent comment."
                ),
            ),
        ]
        for comment in thread:
            if comment.author == bot_login:
                result.append(Message(role="assistant", content=comment.body))
            else:
                result.append(
                    Message(
                        role="user",
                        content=f"[{comment.author}]: {comment.body}",
                    )
                )
        return result
