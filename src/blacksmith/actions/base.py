from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar


class Action(ABC):
    name: ClassVar[str]

    def __init__(self) -> None:
        cls_name = getattr(type(self), "name", type(self).__name__)
        self._logger = logging.getLogger(f"blacksmith.{cls_name}")

    @classmethod
    @abstractmethod
    def from_env(cls) -> Action: ...

    @abstractmethod
    def run(self) -> int: ...
