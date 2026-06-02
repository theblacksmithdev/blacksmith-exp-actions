from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from blacksmith.actions.reviewer.severity import Severity


class Finding(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    file: str
    line: int
    severity: Severity
    title: str
    body: str

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


class FindingsResponse(BaseModel):
    findings: list[Finding]
