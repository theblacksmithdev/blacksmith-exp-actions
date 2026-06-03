from __future__ import annotations

from githubkit.versions.latest.models import DiffEntry

from blacksmith.actions.reviewer.action import ReviewerAction


def _file(
    filename: str,
    *,
    status: str = "modified",
    patch: str | None = "@@ -1 +1 @@\n+x",
) -> DiffEntry:
    return DiffEntry.model_construct(
        sha="x",
        filename=filename,
        status=status,
        additions=1,
        deletions=0,
        changes=1,
        blob_url="https://x",
        raw_url="https://x",
        contents_url="https://x",
        patch=patch,
    )


class TestIsReviewable:
    def test_source_file_is_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("src/app.py")) is True

    def test_markdown_is_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("docs/README.md")) is True

    def test_yaml_config_is_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file(".github/workflows/ci.yml")) is True

    def test_dockerfile_with_no_extension_is_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("Dockerfile")) is True

    def test_sql_migration_is_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("db/migrations/0042_add_index.sql")) is True

    def test_removed_file_is_not_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("src/app.py", status="removed")) is False

    def test_file_without_patch_is_not_reviewable(self) -> None:
        assert ReviewerAction._is_reviewable(_file("assets/logo.png", patch=None)) is False
