from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Literal, TypeVar, cast

from githubkit import GitHub
from githubkit.exception import RequestFailed
from githubkit.versions.latest.models import DiffEntry, IssueComment, PullRequest
from pydantic import BaseModel, Field

from blacksmith.core.exceptions import GitHubAPIError

_log = logging.getLogger(__name__)

T = TypeVar("T")

type ChangedFile = DiffEntry

__all__ = [
    "ChangedFile",
    "GitHubClient",
    "IssueComment",
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
        response = self._guard(
            lambda: self._gh.rest.pulls.get(owner=owner, repo=name, pull_number=number),
            verb="GET",
            url=f"/repos/{repo}/pulls/{number}",
        )
        return response.parsed_data

    def list_pull_request_files(
        self,
        repo: str,
        number: int,
        *,
        per_page: int = 100,
    ) -> list[ChangedFile]:
        owner, name = self._split_repo(repo)
        response = self._guard(
            lambda: self._gh.rest.pulls.list_files(
                owner=owner, repo=name, pull_number=number, per_page=per_page,
            ),
            verb="GET",
            url=f"/repos/{repo}/pulls/{number}/files",
        )
        return response.parsed_data

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

    def list_issue_comments(
        self, repo: str, number: int, *, per_page: int = 100
    ) -> list[IssueComment]:
        owner, name = self._split_repo(repo)
        response = self._guard(
            lambda: self._gh.rest.issues.list_comments(
                owner=owner, repo=name, issue_number=number, per_page=per_page,
            ),
            verb="GET",
            url=f"/repos/{repo}/issues/{number}/comments",
        )
        return response.parsed_data

    def create_issue_comment(self, repo: str, number: int, body: str) -> None:
        owner, name = self._split_repo(repo)
        self._guard(
            lambda: self._gh.rest.issues.create_comment(
                owner=owner, repo=name, issue_number=number, body=body,
            ),
            verb="POST",
            url=f"/repos/{repo}/issues/{number}/comments",
        )

    def create_review(self, repo: str, number: int, review: ReviewBody) -> None:
        owner, name = self._split_repo(repo)
        comments = cast(
            Any,
            [
                {"path": c.path, "line": c.line, "side": c.side, "body": c.body}
                for c in review.comments
            ],
        )
        self._guard(
            lambda: self._gh.rest.pulls.create_review(
                owner=owner,
                repo=name,
                pull_number=number,
                commit_id=review.commit_id,
                body=review.body,
                event=review.event,
                comments=comments,
            ),
            verb="POST",
            url=f"/repos/{repo}/pulls/{number}/reviews",
        )

    @staticmethod
    def _split_repo(repo: str) -> tuple[str, str]:
        owner, _, name = repo.partition("/")
        if not owner or not name:
            raise GitHubAPIError(f"invalid repo identifier: {repo!r}")
        return owner, name

    @classmethod
    def _guard(cls, fn: Callable[[], T], *, verb: str, url: str) -> T:
        try:
            return fn()
        except RequestFailed as exc:
            cls._log_failure(verb, url, exc)
            raise GitHubAPIError(str(exc)) from exc

    @staticmethod
    def _log_failure(verb: str, url: str, exc: RequestFailed) -> None:
        _log.error("GitHub %s %s failed: %s\n%s", verb, url, exc, exc.response.text)
