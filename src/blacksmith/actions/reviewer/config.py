from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from blacksmith.actions.reviewer.severity import Severity
from blacksmith.core.exceptions import ConfigError


class ReviewerConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    DEFAULT_MODEL: ClassVar[str] = "openai/gpt-4o-mini"

    github_token: str
    repo: str
    model: str
    min_severity: Severity

    @classmethod
    def from_env(cls) -> ReviewerConfig:
        token = os.environ.get("GITHUB_TOKEN") or ""
        repo = os.environ.get("REPO") or ""
        model = os.environ.get("MODEL") or cls.DEFAULT_MODEL
        min_sev_raw = os.environ.get("MIN_SEVERITY") or "low"

        if not token:
            raise ConfigError("GITHUB_TOKEN is not set")
        if not repo:
            raise ConfigError("REPO is not set")
        try:
            min_severity = Severity.parse(min_sev_raw)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc

        return cls(
            github_token=token,
            repo=repo,
            model=model,
            min_severity=min_severity,
        )
