from __future__ import annotations

import logging
from typing import Literal

from githubkit import GitHub
from githubkit.exception import RequestFailed
from githubkit.versions.latest.models import DiffEntry, PullRequest
from pydantic import BaseModel, Field

from blacksmith.core.exceptions import GitHubAPIError

_log = logging.getLogger(__name__)


ChangedFile = DiffEntry  # githubkit's typed model is exactly what we need

__all__ = [
    "ChangedFile",
    "GitHubClient",
    "PullRequest",
    "ReviewBody",
    "ReviewComment",
]


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
    RULES_PATH = ".blacksmith/REVIEW.md"

    def __init__(self, token: str) -> None:
        self._gh = GitHub(token)

    def get_pull_request(self, repo: str, number: int) -> PullRequest:
        owner, name = self._split_repo(repo)
        return self._call(
            self._gh.rest.pulls.get,
            owner=owner,
            repo=name,
            pull_number=number,
        )

    def list_pull_request_files(
        self,
        repo: str,
        number: int,
        *,
        per_page: int = 100,
    ) -> list[ChangedFile]:
        owner, name = self._split_repo(repo)
        return self._call(
            self._gh.rest.pulls.list_files,
            owner=owner,
            repo=name,
            pull_number=number,
            per_page=per_page,
        )

    def get_raw_content(self, repo: str, path: str, ref: str) -> str | None:
        owner, name = self._split_repo(repo)
        url = f"/repos/{owner}/{name}/contents/{path}"
        try:
            response = self._gh.request(
                "GET",
                url,
                params={"ref": ref},
                headers={"Accept": "application/vnd.github.raw"},
            )
        except RequestFailed as exc:
            if exc.response.status_code == 404:
                return None
            self._log_failure("GET", url, exc)
            raise GitHubAPIError(str(exc)) from exc
        return response.text

    def create_review(self, repo: str, number: int, review: ReviewBody) -> None:
        owner, name = self._split_repo(repo)
        try:
            self._gh.rest.pulls.create_review(
                owner=owner,
                repo=name,
                pull_number=number,
                data=review.model_dump(mode="json"),
            )
        except RequestFailed as exc:
            self._log_failure("POST", f"/repos/{owner}/{name}/pulls/{number}/reviews", exc)
            raise GitHubAPIError(str(exc)) from exc

    @staticmethod
    def _split_repo(repo: str) -> tuple[str, str]:
        owner, _, name = repo.partition("/")
        if not owner or not name:
            raise GitHubAPIError(f"invalid repo identifier: {repo!r}")
        return owner, name

    @staticmethod
    def _call(method, **kwargs):
        try:
            return method(**kwargs).parsed_data
        except RequestFailed as exc:
            _log.error("GitHub API %s failed: %s\n%s", method.__name__, exc, exc.response.text)
            raise GitHubAPIError(str(exc)) from exc

    @staticmethod
    def _log_failure(verb: str, url: str, exc: RequestFailed) -> None:
        _log.error("GitHub %s %s failed: %s\n%s", verb, url, exc, exc.response.text)
