from __future__ import annotations

from blacksmith.core.persona import AgentPersona
from blacksmith.personas import LARS


class TestAgentPersona:
    def test_header_contains_identity_and_personality(self) -> None:
        persona = AgentPersona(
            name="Test",
            role="Tester",
            intro="hi.",
            personality="terse",
            pronouns="they/them",
        )
        header = persona.to_header()
        assert "You are Test, a Tester." in header
        assert "Pronouns: they/them." in header
        assert "Personality:" in header
        assert "terse" in header

    def test_header_omits_bio_section_when_no_bio_fields(self) -> None:
        persona = AgentPersona(
            name="Test", role="Tester", intro="hi.", personality="terse"
        )
        assert "Your life" not in persona.to_header()

    def test_header_includes_bio_bullets_when_provided(self) -> None:
        persona = AgentPersona(
            name="Test",
            role="Tester",
            intro="hi.",
            personality="terse",
            location="Lagos",
            family="lives alone",
        )
        header = persona.to_header()
        assert "Your life" in header
        assert "- Where you live: Lagos" in header
        assert "- Family: lives alone" in header
        assert "- Background" not in header

    def test_footer_carries_style_rules(self) -> None:
        header = LARS.to_header()
        assert "Stay in character" in header
        assert "em-dash" in header
        assert "No semicolons" in header


class TestLarsPersona:
    def test_lars_has_required_fields(self) -> None:
        assert LARS.name == "Lars"
        assert LARS.role == "Staff Engineer"
        assert LARS.pronouns == "he/him"

    def test_lars_personality_carries_signature_traits(self) -> None:
        text = LARS.personality
        assert "quiet" in text.lower()
        assert "professional skeptic" in text.lower()
