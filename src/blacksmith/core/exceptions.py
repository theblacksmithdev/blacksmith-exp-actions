from __future__ import annotations


class BlacksmithError(Exception):
    pass


class ConfigError(BlacksmithError):
    pass


class GitHubAPIError(BlacksmithError):
    pass


class InferenceError(BlacksmithError):
    pass
