from __future__ import annotations

from typing import Any

import httpx

from blacksmith.core.exceptions import HttpError


class HttpClient:
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
    DEFAULT_USER_AGENT = "blacksmith-dev/0.1.0"

    def __init__(
        self,
        *,
        token: str,
        user_agent: str | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent or self.DEFAULT_USER_AGENT,
            },
            timeout=timeout or self.DEFAULT_TIMEOUT,
        )

    def get(self, url: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
        response = self._client.get(url, headers=headers)
        self._raise_for_status(response)
        return response

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        response = self._client.post(url, json=json, headers=headers)
        self._raise_for_status(response)
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        raise HttpError(
            f"HTTP {response.status_code} on {response.request.method} {response.request.url}",
            status_code=response.status_code,
            response_text=response.text,
        )
