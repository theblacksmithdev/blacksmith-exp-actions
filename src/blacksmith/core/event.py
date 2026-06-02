from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from blacksmith.core.exceptions import ConfigError


class EventContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_name: str
    payload: dict[str, Any]

    @classmethod
    def from_env(cls) -> EventContext:
        event_name = os.environ.get("EVENT_NAME") or os.environ.get("GITHUB_EVENT_NAME") or ""
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path:
            raise ConfigError("GITHUB_EVENT_PATH is not set")
        path = Path(event_path)
        if not path.is_file():
            raise ConfigError(f"GITHUB_EVENT_PATH does not exist: {event_path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(event_name=event_name, payload=payload)

    @property
    def pr_number(self) -> int | None:
        if self.event_name == "pull_request":
            pull = self.payload.get("pull_request") or {}
            number = pull.get("number")
            return int(number) if number is not None else None
        if self.event_name == "issue_comment":
            issue = self.payload.get("issue") or {}
            if issue.get("pull_request"):
                number = issue.get("number")
                return int(number) if number is not None else None
        return None
