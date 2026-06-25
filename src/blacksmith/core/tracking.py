from __future__ import annotations

import logging
from typing import Callable
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field

from blacksmith.core.oidc import (
    OidcError,
    OidcUnavailable,
    mint_id_token,
)

_log = logging.getLogger(__name__)

__all__ = ["ReviewPostedEvent", "TrackingClient"]


class ReviewPostedEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Optional now — when the action authenticates via OIDC, the
    # backend resolves the project from the JWT's (repository, actor)
    # claims and the body project_id is just a sanity check.
    project_id: UUID | None = None
    pr_number: int
    commit_sha: str
    # PR head branch. Backend uses this to auto-link the PR to a
    # sprint task via the branch-naming convention. Empty string when
    # the action couldn't resolve it (defensive default — won't break
    # the backend's optional `branch` serializer field).
    branch: str = ""
    model: str
    findings_total: int
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
    mention_triggered: bool = False


# Token minter is injectable so tests don't need to stub the runner's
# OIDC env vars + HTTP endpoint. Production callers pass
# `mint_id_token` directly; tests pass a lambda returning a fixed JWT.
TokenMinter = Callable[[str], str]


class TrackingClient:
    """Emits engagement events to the Blacksmith Experience backend.

    Authentication mode is decided by `oidc_audience`:

    - Set → mints a short-lived GitHub Actions OIDC JWT per request
      and sends it as `Authorization: Bearer <jwt>`. The backend
      verifies the signature against GitHub's JWKS and resolves the
      project from the JWT's `(repository, actor)` claims. No
      long-lived secret in the apprentice's repo, and two projects
      on the same repo coexist because PR authorship disambiguates
      them.
    - Empty → posts without an auth header. Useful in tests and when
      the backend isn't running auth in front of the endpoint.

    When `endpoint_url` is empty the client no-ops entirely so the
    action stays usable on repos outside the Experience.
    """

    TIMEOUT_SECONDS = 5.0

    def __init__(
        self,
        endpoint_url: str | None,
        *,
        oidc_audience: str = "",
        token_minter: TokenMinter = mint_id_token,
    ) -> None:
        self._endpoint_url = endpoint_url or None
        self._oidc_audience = oidc_audience or ""
        self._token_minter = token_minter

    @property
    def enabled(self) -> bool:
        return self._endpoint_url is not None

    def review_posted(self, event: ReviewPostedEvent) -> None:
        if not self.enabled:
            _log.debug("tracking disabled; skipping review_posted emit")
            return
        assert self._endpoint_url is not None  # noqa: S101 — narrowed by `enabled`
        try:
            response = httpx.post(
                f"{self._endpoint_url.rstrip('/')}/review-posted",
                json=event.model_dump(mode="json"),
                headers=self._auth_headers(),
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except (httpx.HTTPError, OidcError) as exc:
            # Tracking is best-effort. A failed emit must not fail the
            # workflow run — the review has already been posted.
            _log.warning("tracking emit failed: %s", exc)

    def _auth_headers(self) -> dict[str, str]:
        if not self._oidc_audience:
            return {}
        try:
            token = self._token_minter(self._oidc_audience)
        except OidcUnavailable as exc:
            _log.warning(
                "tracking: OIDC unavailable, posting without auth — %s",
                exc,
            )
            return {}
        return {"Authorization": f"Bearer {token}"}
