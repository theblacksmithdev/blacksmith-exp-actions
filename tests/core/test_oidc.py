from __future__ import annotations

from unittest import mock

import httpx
import pytest

from blacksmith.core.oidc import (
    OidcError,
    OidcUnavailable,
    mint_id_token,
)


_VALID_ENV = {
    "ACTIONS_ID_TOKEN_REQUEST_URL": "https://gha.test/oidc/request",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request-token-xyz",
}


def _mock_response(json_body: dict | None = None, status_code: int = 200):
    response = mock.Mock(spec=httpx.Response)
    response.status_code = status_code
    response.raise_for_status = mock.Mock()
    response.json = mock.Mock(return_value=json_body or {})
    return response


class TestMintIdToken:
    def test_returns_token_from_runner_response(self) -> None:
        with mock.patch.dict("os.environ", _VALID_ENV, clear=True), \
             mock.patch("httpx.get") as get:
            get.return_value = _mock_response({"value": "jwt-token-here"})
            assert mint_id_token("https://blacksmith.dev") == "jwt-token-here"

    def test_sends_audience_param_and_bearer_header(self) -> None:
        with mock.patch.dict("os.environ", _VALID_ENV, clear=True), \
             mock.patch("httpx.get") as get:
            get.return_value = _mock_response({"value": "jwt-token-here"})
            mint_id_token("https://aud")
            kwargs = get.call_args.kwargs
            assert kwargs["params"] == {"audience": "https://aud"}
            assert kwargs["headers"]["Authorization"] == "Bearer request-token-xyz"

    def test_missing_env_raises_unavailable(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with pytest.raises(OidcUnavailable):
                mint_id_token("https://aud")

    def test_partial_env_raises_unavailable(self) -> None:
        # URL set but token missing — same outcome.
        env = {"ACTIONS_ID_TOKEN_REQUEST_URL": "https://gha.test/oidc/request"}
        with mock.patch.dict("os.environ", env, clear=True):
            with pytest.raises(OidcUnavailable):
                mint_id_token("https://aud")

    def test_empty_audience_raises(self) -> None:
        with mock.patch.dict("os.environ", _VALID_ENV, clear=True):
            with pytest.raises(OidcError):
                mint_id_token("")

    def test_http_failure_raises_oidc_error(self) -> None:
        with mock.patch.dict("os.environ", _VALID_ENV, clear=True), \
             mock.patch("httpx.get") as get:
            response = _mock_response(status_code=500)
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "boom", request=mock.Mock(), response=response,
            )
            get.return_value = response
            with pytest.raises(OidcError):
                mint_id_token("https://aud")

    def test_missing_value_in_response_raises(self) -> None:
        with mock.patch.dict("os.environ", _VALID_ENV, clear=True), \
             mock.patch("httpx.get") as get:
            get.return_value = _mock_response({})
            with pytest.raises(OidcError):
                mint_id_token("https://aud")
