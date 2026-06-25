from __future__ import annotations

from unittest import mock
from uuid import uuid4

import httpx

from blacksmith.core.oidc import OidcUnavailable
from blacksmith.core.tracking import ReviewPostedEvent, TrackingClient


def _event() -> ReviewPostedEvent:
    return ReviewPostedEvent(
        project_id=uuid4(),
        pr_number=1,
        commit_sha="abc",
        model="m",
        findings_total=0,
    )


def _ok_response():
    response = mock.Mock(spec=httpx.Response)
    response.status_code = 202
    response.raise_for_status = mock.Mock()
    return response


class TestTrackingClient:
    def test_disabled_when_no_endpoint_url(self) -> None:
        assert TrackingClient(None).enabled is False
        assert TrackingClient("").enabled is False

    def test_enabled_when_endpoint_url_set(self) -> None:
        assert TrackingClient("https://example.test").enabled is True

    def test_disabled_emit_is_a_noop(self) -> None:
        client = TrackingClient(None)
        client.review_posted(_event())

    def test_posts_with_no_auth_when_oidc_audience_blank(self) -> None:
        with mock.patch("httpx.post") as post:
            post.return_value = _ok_response()
            client = TrackingClient(
                "https://api.test",
                token_minter=mock.Mock(side_effect=AssertionError(
                    "minter should not be called when audience is empty",
                )),
            )
            client.review_posted(_event())
        kwargs = post.call_args.kwargs
        assert kwargs["headers"] == {}

    def test_posts_with_oidc_bearer_when_audience_set(self) -> None:
        minter = mock.Mock(return_value="jwt.payload.sig")
        with mock.patch("httpx.post") as post:
            post.return_value = _ok_response()
            client = TrackingClient(
                "https://api.test",
                oidc_audience="https://aud",
                token_minter=minter,
            )
            client.review_posted(_event())
        minter.assert_called_once_with("https://aud")
        kwargs = post.call_args.kwargs
        assert kwargs["headers"] == {"Authorization": "Bearer jwt.payload.sig"}

    def test_oidc_unavailable_degrades_to_unauthenticated_post(self) -> None:
        # Workflow forgot `id-token: write` permission. Tracking is
        # best-effort, so we still POST — backend will reject, but we
        # don't fail the workflow over it.
        minter = mock.Mock(side_effect=OidcUnavailable("missing env"))
        with mock.patch("httpx.post") as post:
            post.return_value = _ok_response()
            client = TrackingClient(
                "https://api.test",
                oidc_audience="https://aud",
                token_minter=minter,
            )
            client.review_posted(_event())
        kwargs = post.call_args.kwargs
        assert kwargs["headers"] == {}

    def test_http_failure_is_swallowed(self) -> None:
        with mock.patch("httpx.post") as post:
            post.side_effect = httpx.ConnectError("nope")
            client = TrackingClient("https://api.test")
            # Should not raise — tracking is best-effort.
            client.review_posted(_event())


class TestReviewPostedEvent:
    def test_severity_counts_default_empty(self) -> None:
        event = ReviewPostedEvent(
            project_id=uuid4(),
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
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=2,
            findings_by_severity={"high": 1, "low": 1},
        )
        payload = event.model_dump(mode="json")
        assert payload["project_id"] == str(project_id)
        assert payload["findings_by_severity"] == {"high": 1, "low": 1}

    def test_project_id_optional(self) -> None:
        # With OIDC the backend resolves project from the JWT, so
        # project_id is optional in the body.
        event = ReviewPostedEvent(
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
        )
        assert event.project_id is None
        assert event.model_dump(mode="json")["project_id"] is None

    def test_branch_defaults_to_empty_string(self) -> None:
        # Defensive default — the backend's `branch` field is optional
        # + allow_blank, so an empty string is the safe value when the
        # action can't resolve the head ref.
        event = ReviewPostedEvent(
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
        )
        assert event.branch == ""
        assert event.model_dump(mode="json")["branch"] == ""

    def test_branch_serialises_when_set(self) -> None:
        # Backend uses this to auto-link the PR to a sprint task via
        # the branch-naming convention — losing it on the wire means
        # no linkage.
        event = ReviewPostedEvent(
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
            branch="apprentice/TXN-001-add-login",
        )
        payload = event.model_dump(mode="json")
        assert payload["branch"] == "apprentice/TXN-001-add-login"

    def test_payload_does_not_include_repo(self) -> None:
        """The project_id is enough — the backend looks repo up from the
        project linkage. Keeping repo on the wire would create the risk
        of an inconsistency (action sends one, backend has another)."""
        event = ReviewPostedEvent(
            project_id=uuid4(),
            pr_number=1,
            commit_sha="abc",
            model="m",
            findings_total=0,
        )
        assert "repo" not in event.model_dump(mode="json")
