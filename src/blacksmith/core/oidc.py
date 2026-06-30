"""Mints short-lived GitHub Actions OIDC tokens.

The reviewer action posts back to the Blacksmith Experience backend
after every review. To authenticate that callback without writing a
per-project secret into the user's repo, the action mints an OIDC
JWT at runtime — GitHub signs it with `repository`, `actor`, and
audience claims the backend verifies against GitHub's JWKS.

This module is a thin wrapper around the GitHub Actions runner's
OIDC endpoint. The runner exposes two env vars when the workflow
grants ``permissions: id-token: write``:

    ACTIONS_ID_TOKEN_REQUEST_URL    — endpoint to POST to
    ACTIONS_ID_TOKEN_REQUEST_TOKEN  — bearer token for the request

When either is missing, we're either running outside Actions or the
workflow forgot the permission. In both cases the minter raises
`OidcUnavailable` so the caller can decide whether to soft-fail
(skip tracking) or hard-fail.
"""

from __future__ import annotations

import logging
import os

import httpx

__all__ = ["OidcError", "OidcUnavailable", "mint_id_token"]

_log = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 10


class OidcError(Exception):
    """Generic failure minting an OIDC token (network, non-200, etc.)."""


class OidcUnavailable(OidcError):
    """Runner didn't expose the OIDC env vars.

    Raised when `ACTIONS_ID_TOKEN_REQUEST_URL` or
    `ACTIONS_ID_TOKEN_REQUEST_TOKEN` is missing — either we're not in
    a GitHub Actions runner, or the workflow doesn't grant
    `id-token: write` permission.
    """


def mint_id_token(audience: str) -> str:
    """Ask the GitHub Actions runner for a JWT scoped to ``audience``.

    Raises `OidcUnavailable` when the runner doesn't expose the OIDC
    env vars; `OidcError` for everything else (network, non-200,
    malformed response).
    """
    if not audience:
        raise OidcError("audience is required to mint an OIDC token")
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not request_url or not request_token:
        raise OidcUnavailable(
            "ACTIONS_ID_TOKEN_REQUEST_URL / _TOKEN not set — workflow "
            "needs `permissions: id-token: write` and must run inside "
            "GitHub Actions"
        )
    try:
        response = httpx.get(
            request_url,
            params={"audience": audience},
            headers={
                "Authorization": f"Bearer {request_token}",
                "Accept": "application/json",
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OidcError(f"OIDC token request failed: {exc}") from exc
    try:
        token = response.json().get("value")
    except ValueError as exc:
        raise OidcError(f"OIDC response was not JSON: {exc}") from exc
    if not token:
        raise OidcError("OIDC response did not include `value`")
    return token
