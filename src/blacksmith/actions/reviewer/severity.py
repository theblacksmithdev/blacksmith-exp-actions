from __future__ import annotations

from enum import IntEnum


class Severity(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

    @classmethod
    def parse(cls, raw: str) -> Severity:
        key = (raw or "").strip().upper()
        try:
            return cls[key]
        except KeyError as exc:
            raise ValueError(f"unknown severity: {raw!r}") from exc

    @property
    def label(self) -> str:
        return self.name.lower()
