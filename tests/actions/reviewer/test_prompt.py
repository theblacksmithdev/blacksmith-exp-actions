from __future__ import annotations

from blacksmith.actions.reviewer.prompt import PromptBuilder


class TestPromptBuilder:
    def setup_method(self) -> None:
        self.builder = PromptBuilder()

    def test_system_message_includes_lars_identity(self) -> None:
        content = self.builder.system_message().content
        assert "You are Lars, a Staff Engineer." in content

    def test_system_message_includes_guidance_framing(self) -> None:
        content = self.builder.system_message().content
        assert "apprentice" in content.lower()
        assert "I have seen this" in content
        assert "I have a hunch" in content

    def test_system_message_forbids_validation_language(self) -> None:
        content = self.builder.system_message().content
        assert "Do not praise or validate" in content
        assert "Do not apologize" in content
        assert "Do not lecture" in content

    def test_system_message_specifies_json_output(self) -> None:
        content = self.builder.system_message().content
        assert '"severity"' in content
        assert '"low"' in content
        assert '"critical"' in content

    def test_system_message_requires_a_summary(self) -> None:
        content = self.builder.system_message().content
        assert '"summary"' in content
        assert "standup the next morning" in content

    def test_system_message_describes_references(self) -> None:
        content = self.builder.system_message().content
        assert '"references"' in content
        assert "canonical references" in content or "canonical reference" in content
