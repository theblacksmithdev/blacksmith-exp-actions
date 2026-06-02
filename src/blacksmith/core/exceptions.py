from __future__ import annotations


class BlacksmithError(Exception):
    pass


class ConfigError(BlacksmithError):
    pass


class HttpError(BlacksmithError):
    def __init__(self, message: str, *, status_code: int, response_text: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class GitHubAPIError(BlacksmithError):
    pass


class InferenceError(BlacksmithError):
    pass
