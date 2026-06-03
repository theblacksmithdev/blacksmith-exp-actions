from __future__ import annotations

from uuid import UUID

from blacksmith.core.inference import Message

__all__ = ["Project"]


class Project:
    """Per-apprentice project state on the Blacksmith Experience side.

    Today this is a placeholder — every method returns a no-op default
    because the main Blacksmith Experience project has not exposed the
    endpoint yet (see TODOs). The shape exists so the rest of the action
    code can call into it without conditionals, and so it's clear what
    state the main project will eventually own:

    - **Conversation history** per PR. The thread on the PR itself is
      always GitHub's source of truth; this layer is for higher-order
      context (e.g. summaries of older PRs the apprentice opened, prior
      topics Lars has flagged, etc.) that GitHub cannot reconstruct.
    - **Session id** for resumable LLM sessions. When we move from
      stateless chat completions to a persistent assistant/thread
      (OpenAI Assistants API or equivalent), the session id lives here
      so Lars can pick up across workflow runs.
    """

    def __init__(self, project_id: UUID | None) -> None:
        self._project_id = project_id

    @property
    def project_id(self) -> UUID | None:
        return self._project_id

    @property
    def is_attached(self) -> bool:
        return self._project_id is not None

    def get_session_id(self, pr_number: int) -> str | None:
        # TODO(blacksmith-experience): GET /projects/{id}/prs/{pr}/session
        del pr_number
        return None

    def save_session_id(self, pr_number: int, session_id: str) -> None:
        # TODO(blacksmith-experience): PUT /projects/{id}/prs/{pr}/session
        del pr_number, session_id

    def get_conversation_history(self, pr_number: int) -> list[Message]:
        # TODO(blacksmith-experience): GET /projects/{id}/prs/{pr}/history
        # Until this is wired, the live PR thread on GitHub is the only
        # context source — see ConversationBuilder.
        del pr_number
        return []

    def append_to_history(self, pr_number: int, messages: list[Message]) -> None:
        # TODO(blacksmith-experience): POST /projects/{id}/prs/{pr}/history
        del pr_number, messages
