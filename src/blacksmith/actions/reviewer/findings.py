from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

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


class FindingsParser:
    _FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)

    def parse(self, raw: str) -> list[Finding]:
        if not raw:
            return []
        text = self._strip_fence(raw.strip())
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        findings: list[Finding] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                findings.append(Finding.model_validate(item))
            except ValidationError:
                continue
        return findings

    @classmethod
    def _strip_fence(cls, text: str) -> str:
        match = cls._FENCE_RE.match(text)
        return match.group(1).strip() if match else text
