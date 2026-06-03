from __future__ import annotations

from blacksmith.actions.reviewer.conversation import (
    ConversationBuilder,
    ReplyResponse,
    ThreadComment,
)


class TestReplyResponse:
    def test_round_trip(self) -> None:
        reply = ReplyResponse.model_validate({"body": "Fair point. I was wrong on the locking."})
        assert reply.body.startswith("Fair point")


class TestConversationBuilder:
    def setup_method(self) -> None:
        self.builder = ConversationBuilder()

    def _build(
        self,
        *,
        thread: list[ThreadComment],
        bot_login: str = "lars-blacksmith-exp[bot]",
        pr_title: str = "Refactor auth handler",
        pr_body: str | None = "Splits the login flow.",
    ) -> list[object]:
        return list(
            self.builder.messages(
                pr_title=pr_title,
                pr_body=pr_body,
                thread=thread,
                bot_login=bot_login,
            )
        )

    def test_first_message_is_system_with_lars_identity(self) -> None:
        messages = self._build(thread=[])
        assert messages[0].role == "system"  # type: ignore[attr-defined]
        assert "You are Lars" in messages[0].content  # type: ignore[attr-defined]

    def test_system_prompt_forbids_validation_and_apology(self) -> None:
        messages = self._build(thread=[])
        system_content = messages[0].content  # type: ignore[attr-defined]
        assert "Do not praise them" in system_content
        assert "Do not apologize for your earlier review" in system_content

    def test_bot_comments_become_assistant_role(self) -> None:
        thread = [
            ThreadComment(author="lars-blacksmith-exp[bot]", body="I would not let this through."),
            ThreadComment(author="apprentice", body="Why not?"),
        ]
        messages = self._build(thread=thread)
        assistant_messages = [m for m in messages if m.role == "assistant"]  # type: ignore[attr-defined]
        assert len(assistant_messages) == 1
        assert assistant_messages[0].content == "I would not let this through."  # type: ignore[attr-defined]

    def test_apprentice_comments_become_user_role_with_author_tag(self) -> None:
        thread = [ThreadComment(author="apprentice", body="thoughts?")]
        messages = self._build(thread=thread)
        user_msgs = [m for m in messages if m.role == "user"]  # type: ignore[attr-defined]
        # First user message is the PR context, second is the apprentice comment
        assert "[apprentice]: thoughts?" in user_msgs[-1].content  # type: ignore[attr-defined]

    def test_pr_context_includes_title_and_body(self) -> None:
        messages = self._build(thread=[], pr_title="My title", pr_body="My body.")
        user_msgs = [m for m in messages if m.role == "user"]  # type: ignore[attr-defined]
        assert any("My title" in m.content for m in user_msgs)  # type: ignore[attr-defined]
        assert any("My body." in m.content for m in user_msgs)  # type: ignore[attr-defined]

    def test_missing_pr_body_renders_as_no_description(self) -> None:
        messages = self._build(thread=[], pr_body=None)
        user_msgs = [m for m in messages if m.role == "user"]  # type: ignore[attr-defined]
        assert any("(no description)" in m.content for m in user_msgs)  # type: ignore[attr-defined]
