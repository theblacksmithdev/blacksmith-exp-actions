from __future__ import annotations

from collections import Counter
from typing import ClassVar

from blacksmith.actions.base import Action
from blacksmith.actions.registry import ActionRegistry
from blacksmith.actions.reviewer.config import ReviewerConfig
from blacksmith.actions.reviewer.findings import Finding, FindingsResponse
from blacksmith.actions.reviewer.prompt import PromptBuilder
from blacksmith.actions.reviewer.review import ReviewBuilder
from blacksmith.core.diff import DiffParser
from blacksmith.core.event import EventContext
from blacksmith.core.github import ChangedFile, GitHubClient
from blacksmith.core.inference import GitHubModelsClient
from blacksmith.core.tracking import ReviewPostedEvent, TrackingClient


@ActionRegistry.register
class ReviewerAction(Action):
    name: ClassVar[str] = "reviewer"

    def __init__(
        self,
        *,
        config: ReviewerConfig,
        github_client: GitHubClient,
        inference_client: GitHubModelsClient,
        tracking_client: TrackingClient,
        event: EventContext,
        diff_parser: DiffParser | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._github = github_client
        self._inference = inference_client
        self._tracking = tracking_client
        self._event = event
        self._diff_parser = diff_parser or DiffParser()
        self._prompt_builder = prompt_builder or PromptBuilder()

    @classmethod
    def from_env(cls) -> ReviewerAction:
        config = ReviewerConfig.from_env()
        return cls(
            config=config,
            github_client=GitHubClient(config.github_token),
            inference_client=GitHubModelsClient(config.inference_token),
            tracking_client=TrackingClient(config.tracking_url),
            event=EventContext.from_env(),
        )

    def run(self) -> int:
        pr_number = self._event.pr_number
        if pr_number is None:
            self._logger.info("no PR number resolvable from event; nothing to do")
            return 0

        pr = self._github.get_pull_request(self._config.repo, pr_number)
        files = self._github.list_pull_request_files(self._config.repo, pr_number)
        reviewable = [f for f in files if self._is_reviewable(f)]
        if not reviewable:
            self._logger.info("no reviewable changes; skipping")
            return 0

        anchor_map = {
            f.filename: self._diff_parser.anchorable_lines(self._patch_text(f))
            for f in reviewable
        }
        rules = self._github.get_raw_content(
            self._config.repo, self._github.RULES_PATH, pr.head.sha
        )

        messages = [
            self._prompt_builder.system_message(),
            self._prompt_builder.user_message(
                pr_title=pr.title or "", rules=rules, files=reviewable
            ),
        ]
        response = self._inference.parse(
            model=self._config.model,
            messages=messages,
            response_format=FindingsResponse,
        )
        findings = [f for f in response.findings if f.severity >= self._config.min_severity]

        builder = ReviewBuilder(findings, anchor_map)
        self._github.create_review(self._config.repo, pr_number, builder.build(pr.head.sha))

        self._logger.info(
            "posted review: %d inline, %d summary-only",
            builder.inline_count,
            builder.summary_only_count,
        )
        self._emit_review_posted(pr_number=pr_number, commit_sha=pr.head.sha, findings=findings)
        return 0

    def _emit_review_posted(
        self, *, pr_number: int, commit_sha: str, findings: list[Finding]
    ) -> None:
        if self._config.project_id is None:
            return
        by_severity = Counter(f.severity.name.lower() for f in findings)
        self._tracking.review_posted(
            ReviewPostedEvent(
                project_id=self._config.project_id,
                repo=self._config.repo,
                pr_number=pr_number,
                commit_sha=commit_sha,
                model=self._config.model,
                findings_total=len(findings),
                findings_by_severity=dict(by_severity),
                mention_triggered=self._event.event_name == "issue_comment",
            )
        )

    @classmethod
    def _is_reviewable(cls, file: ChangedFile) -> bool:
        if file.status == "removed":
            return False
        return cls._patch_text(file) is not None

    @staticmethod
    def _patch_text(file: ChangedFile) -> str | None:
        return file.patch if isinstance(file.patch, str) else None
