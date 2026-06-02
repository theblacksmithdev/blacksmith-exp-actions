from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from blacksmith.core.exceptions import GitHubAPIError, HttpError
from blacksmith.core.http import HttpClient

_log = logging.getLogger(__name__)


class _PRHead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sha: str


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    title: str = ""
    head: _PRHead

    @property
    def head_sha(self) -> str:
        return self.head.sha


class ChangedFile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    status: str
    patch: str | None = None


class ReviewComment(BaseModel):
    path: str
    line: int
    side: Literal["RIGHT", "LEFT"] = "RIGHT"
    body: str


class ReviewBody(BaseModel):
    commit_id: str
    body: str
    event: Literal["COMMENT", "REQUEST_CHANGES", "APPROVE"]
    comments: list[ReviewComment] = Field(default_factory=list)


class GitHubClient:
    BASE_URL = "https://api.github.com"
    JSON_ACCEPT = "application/vnd.github+json"
    RAW_ACCEPT = "application/vnd.github.raw"

    def __init__(self, http_client: HttpClient) -> None:
        self._http = http_client

    def get_pull_request(self, repo: str, number: int) -> PullRequest:
        response = self._http.get(
            f"{self.BASE_URL}/repos/{repo}/pulls/{number}",
            headers={"Accept": self.JSON_ACCEPT},
        )
        return PullRequest.model_validate(response.json())

    def list_pull_request_files(
        self,
        repo: str,
        number: int,
        *,
        per_page: int = 100,
    ) -> list[ChangedFile]:
        response = self._http.get(
            f"{self.BASE_URL}/repos/{repo}/pulls/{number}/files?per_page={per_page}",
            headers={"Accept": self.JSON_ACCEPT},
        )
        return [ChangedFile.model_validate(item) for item in response.json()]

    def get_raw_content(self, repo: str, path: str, ref: str) -> str | None:
        url = f"{self.BASE_URL}/repos/{repo}/contents/{path}?ref={ref}"
        try:
            response = self._http.get(url, headers={"Accept": self.RAW_ACCEPT})
        except HttpError as exc:
            if exc.status_code == 404:
                return None
            _log.error("GitHub raw content failed: %s\n%s", exc, exc.response_text)
            raise GitHubAPIError(str(exc)) from exc
        return response.text

    def create_review(self, repo: str, number: int, review: ReviewBody) -> None:
        try:
            self._http.post(
                f"{self.BASE_URL}/repos/{repo}/pulls/{number}/reviews",
                json=review.model_dump(mode="json"),
                headers={"Accept": self.JSON_ACCEPT},
            )
        except HttpError as exc:
            _log.error("Posting review failed: %s\n%s", exc, exc.response_text)
            raise GitHubAPIError(str(exc)) from exc
