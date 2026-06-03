from __future__ import annotations

from uuid import uuid4

from blacksmith.core.tracking import ReviewPostedEvent, TrackingClient


class TestTrackingClient:
    def test_disabled_when_no_endpoint_url(self) -> None:
        assert TrackingClient(None).enabled is False
        assert TrackingClient("").enabled is False

    def test_enabled_when_endpoint_url_set(self) -> None:
        assert TrackingClient("https://example.test").enabled is True

    def test_disabled_emit_is_a_noop(self) -> None:
        client = TrackingClient(None)
        event = ReviewPostedEvent(
            project_id=uuid4(),
            repo="o/r",
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
        )
        client.review_posted(event)


class TestReviewPostedEvent:
    def test_severity_counts_default_empty(self) -> None:
        event = ReviewPostedEvent(
            project_id=uuid4(),
            repo="o/r",
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
        )
        assert event.findings_by_severity == {}
        assert event.mention_triggered is False

    def test_uuid_serialises_to_string(self) -> None:
        project_id = uuid4()
        event = ReviewPostedEvent(
            project_id=project_id,
            repo="o/r",
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=2,
            findings_by_severity={"high": 1, "low": 1},
        )
        payload = event.model_dump(mode="json")
        assert payload["project_id"] == str(project_id)
        assert payload["findings_by_severity"] == {"high": 1, "low": 1}
