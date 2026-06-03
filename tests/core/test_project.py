from __future__ import annotations

from uuid import uuid4

from blacksmith.core.project import Project


class TestProject:
    def test_is_attached_when_project_id_set(self) -> None:
        assert Project(uuid4()).is_attached is True

    def test_not_attached_when_project_id_missing(self) -> None:
        assert Project(None).is_attached is False

    def test_history_is_empty_until_endpoint_exists(self) -> None:
        """While the main project's endpoint is unbuilt, the placeholder
        returns empty so the responder falls back to GitHub thread context."""
        project = Project(uuid4())
        assert project.get_conversation_history(1) == []
        assert project.get_session_id(1) is None

    def test_writes_are_no_ops_today(self) -> None:
        # No exception, no return value to assert. The point is that
        # callers can invoke these without conditional branches even when
        # the backend is not wired yet.
        project = Project(uuid4())
        project.save_session_id(1, "sess-abc")
        project.append_to_history(1, [])
