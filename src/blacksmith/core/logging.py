from __future__ import annotations

import logging
import sys


class LoggingConfigurator:
    DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s — %(message)s"
    DEFAULT_DATEFMT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, level: int = logging.INFO) -> None:
        self._level = level

    def configure(self) -> None:
        root = logging.getLogger()
        if root.handlers:
            return
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter(self.DEFAULT_FORMAT, self.DEFAULT_DATEFMT))
        root.addHandler(handler)
        root.setLevel(self._level)
