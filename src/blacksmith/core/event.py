from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from githubkit.versions.latest.webhooks import IssueCommentEvent, PullRequestEvent
from pydantic import TypeAdapter, ValidationError

from blacksmith.core.exceptions import ConfigError

_PULL_REQUEST_EVENT_ADAPTER: TypeAdapter[PullRequestEvent] = TypeAdapter(PullRequestEvent)
_ISSUE_COMMENT_EVENT_ADAPTER: TypeAdapter[IssueCommentEvent] = TypeAdapter(IssueCommentEvent)


class EventContext:
    def __init__(self, event_name: str, payload: dict[str, Any]) -> None:
        self._event_name = event_name
        self._payload = payload

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
    def event_name(self) -> str:
        return self._event_name

    @property
    def pr_number(self) -> int | None:
        if self._event_name == "pull_request":
            try:
                pr_event = _PULL_REQUEST_EVENT_ADAPTER.validate_python(self._payload)
            except ValidationError:
                return None
            return pr_event.pull_request.number
        if self._event_name == "issue_comment":
            try:
                comment_event = _ISSUE_COMMENT_EVENT_ADAPTER.validate_python(self._payload)
            except ValidationError:
                return None
            if comment_event.issue.pull_request is None:
                return None
            return comment_event.issue.number
        return None
