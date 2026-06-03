from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from blacksmith.actions.reviewer.severity import Severity


class Reference(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    url: str
    why: str

    @field_validator("url")
    @classmethod
    def _must_be_http_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"url scheme must be http or https: {value!r}")
        if not parsed.netloc:
            raise ValueError(f"url is missing a host: {value!r}")
        return value.strip()


class Finding(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    file: str
    line: int
    severity: Severity
    title: str
    body: str
    references: list[Reference] = Field(default_factory=list)

    @field_validator("severity", mode="before")
    @classmethod
    def _coerce_severity(cls, value: Any) -> Severity:
        if isinstance(value, Severity):
            return value
        if isinstance(value, int):
            return Severity(value)
        if isinstance(value, str):
            return Severity.parse(value)
        raise ValueError(f"invalid severity: {value!r}")

    @field_validator("references", mode="before")
    @classmethod
    def _drop_invalid_references(cls, value: Any) -> Any:
        """Silently drop malformed references rather than failing the whole
        finding. Lars losing a bad link is better than Lars losing a real
        finding because the model hallucinated a URL on the side."""
        if not isinstance(value, list):
            return value
        valid: list[Any] = []
        for item in value:
            try:
                Reference.model_validate(item)
            except Exception:
                continue
            valid.append(item)
        return valid


class FindingsResponse(BaseModel):
    summary: str
    findings: list[Finding]
