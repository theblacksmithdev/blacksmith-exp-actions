from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel

from blacksmith.core.exceptions import HttpError, InferenceError
from blacksmith.core.http import HttpClient

_log = logging.getLogger(__name__)


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class GitHubModelsClient:
    BASE_URL = "https://models.github.ai/inference"
    DEFAULT_TEMPERATURE = 0.2

    def __init__(self, http_client: HttpClient) -> None:
        self._http = http_client

    def chat_completion(
        self,
        model: str,
        messages: list[Message],
        *,
        temperature: float | None = None,
    ) -> str:
        body = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": self.DEFAULT_TEMPERATURE if temperature is None else temperature,
        }
        try:
            response = self._http.post(f"{self.BASE_URL}/chat/completions", json=body)
        except HttpError as exc:
            _log.error("GitHub Models call failed: %s\n%s", exc, exc.response_text)
            raise InferenceError(str(exc)) from exc
        payload = response.json()
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise InferenceError(f"unexpected inference response shape: {payload}") from exc
