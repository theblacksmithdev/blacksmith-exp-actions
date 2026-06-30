from __future__ import annotations

from blacksmith.actions.reviewer.principles import PrinciplesBuilder, PrinciplesResponse


class TestPrinciplesBuilder:
    def setup_method(self) -> None:
        self.builder = PrinciplesBuilder()

    def test_system_message_keeps_lars_in_character(self) -> None:
        messages = self.builder.messages(
            pr_title="Big refactor", file_count=40, additions=2400, deletions=900
        )
        assert messages[0].role == "system"
        assert "You are Lars, a Staff Engineer." in messages[0].content

    def test_system_message_names_standard_engineering_principles(self) -> None:
        # The fallback note's whole job is to point the apprentice at the
        # principles a senior would walk the change against.
        content = self.builder.messages(
            pr_title="x", file_count=1, additions=1, deletions=0
        )[0].content
        assert "Small, focused PRs" in content
        assert "module boundaries" in content
        assert "Naming" in content
        assert "Tests" in content

    def test_system_message_forbids_tool_aware_language(self) -> None:
        # The whole point of this path is that the apprentice gets a humanly
        # comment back. The guidance must explicitly bar leaking tool words.
        content = self.builder.messages(
            pr_title="x", file_count=1, additions=1, deletions=0
        )[0].content
        assert "Do not mention" in content
        assert "context windows" in content
        assert "tokens" in content
        assert "AI" in content

    def test_user_message_carries_only_pr_metadata(self) -> None:
        messages = self.builder.messages(
            pr_title="Add billing dashboard",
            file_count=42,
            additions=2400,
            deletions=900,
        )
        user_content = messages[1].content
        assert messages[1].role == "user"
        assert "Add billing dashboard" in user_content
        assert "42" in user_content
        assert "2400" in user_content
        assert "900" in user_content
        # No diff payload — the fallback runs when the first call already
        # failed, so the prompt must stay minimal.
        assert "```" not in user_content
        assert "diff" not in user_content.lower()

    def test_empty_title_falls_back_to_placeholder(self) -> None:
        messages = self.builder.messages(
            pr_title="", file_count=1, additions=1, deletions=0
        )
        assert "(no title)" in messages[1].content

    def test_response_schema_only_carries_a_body(self) -> None:
        # Lock the shape so the action stays able to read `.body` directly.
        assert set(PrinciplesResponse.model_fields.keys()) == {"body"}
