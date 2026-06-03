from __future__ import annotations

import logging
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field

_log = logging.getLogger(__name__)

__all__ = ["ReviewPostedEvent", "TrackingClient"]


class ReviewPostedEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: UUID
    pr_number: int
    commit_sha: str
    model: str
    findings_total: int
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
    mention_triggered: bool = False


class TrackingClient:
    """Emits engagement events to the Blacksmith Experience backend.

    Currently a stub. The backend endpoint that receives these events
    has not been built yet. When `endpoint_url` is empty (or the project
    isn't part of an Experience), the client no-ops so the action stays
    usable on repos outside the apprenticeship.
    """

    TIMEOUT_SECONDS = 5.0

    def __init__(self, endpoint_url: str | None) -> None:
        self._endpoint_url = endpoint_url or None

    @property
    def enabled(self) -> bool:
        return self._endpoint_url is not None

    def review_posted(self, event: ReviewPostedEvent) -> None:
        if not self.enabled:
            _log.debug("tracking disabled; skipping review_posted emit")
            return
        # TODO(blacksmith-experience): wire to the real endpoint once the
        # main project exposes it. Auth scheme (shared secret? signed
        # JWT keyed by project_id?) is also pending that work.
        assert self._endpoint_url is not None  # noqa: S101 — narrowed by `enabled`
        try:
            response = httpx.post(
                f"{self._endpoint_url.rstrip('/')}/review-posted",
                json=event.model_dump(mode="json"),
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Tracking is best-effort. A failed emit must not fail the
            # workflow run — the review has already been posted.
            _log.warning("tracking emit failed: %s", exc)
