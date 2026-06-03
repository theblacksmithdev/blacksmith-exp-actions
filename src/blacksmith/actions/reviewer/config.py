from __future__ import annotations

from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from blacksmith.actions.reviewer.severity import Severity
from blacksmith.core.exceptions import ConfigError


class ReviewerConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, frozen=True, extra="ignore")

    github_token: str
    inference_token: str = ""
    repo: str
    model: str = "openai/gpt-4o-mini"
    min_severity: Severity = Severity.LOW

    @model_validator(mode="after")
    def _default_inference_token(self) -> ReviewerConfig:
        if not self.inference_token:
            object.__setattr__(self, "inference_token", self.github_token)
        return self

    @field_validator("min_severity", mode="before")
    @classmethod
    def _coerce_severity(cls, value: Any) -> Severity:
        if isinstance(value, Severity):
            return value
        if isinstance(value, int):
            return Severity(value)
        if isinstance(value, str):
            return Severity.parse(value)
        raise ValueError(f"invalid severity: {value!r}")

    @classmethod
    def from_env(cls) -> ReviewerConfig:
        try:
            return cls()
        except Exception as exc:
            raise ConfigError(str(exc)) from exc
