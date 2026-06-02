from __future__ import annotations

import logging
from typing import Literal, TypeVar, cast

from openai import APIError, OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from blacksmith.core.exceptions import InferenceError

_log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class GitHubModelsClient:
    BASE_URL = "https://models.github.ai/inference"
    DEFAULT_TEMPERATURE = 0.2

    def __init__(self, token: str) -> None:
        self._client = OpenAI(api_key=token, base_url=self.BASE_URL)

    def parse(
        self,
        *,
        model: str,
        messages: list[Message],
        response_format: type[T],
        temperature: float | None = None,
    ) -> T:
        message_params = cast(
            list[ChatCompletionMessageParam], [m.model_dump() for m in messages]
        )
        try:
            completion = self._client.beta.chat.completions.parse(
                model=model,
                messages=message_params,
                response_format=response_format,
                temperature=self.DEFAULT_TEMPERATURE if temperature is None else temperature,
            )
        except APIError as exc:
            _log.error("GitHub Models inference failed: %s", exc)
            raise InferenceError(str(exc)) from exc
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise InferenceError("inference returned no parsed structured output")
        return parsed
