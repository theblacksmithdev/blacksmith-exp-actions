from __future__ import annotations

from typing import TYPE_CHECKING

from blacksmith.core.exceptions import ConfigError

if TYPE_CHECKING:
    from blacksmith.actions.base import Action


class ActionRegistry:
    _actions: dict[str, type[Action]] = {}

    @classmethod
    def register(cls, action_cls: type[Action]) -> type[Action]:
        name = getattr(action_cls, "name", None)
        if not name:
            raise ConfigError(
                f"{action_cls.__name__} must define a class-level `name` to register"
            )
        if name in cls._actions:
            raise ConfigError(f"action name '{name}' is already registered")
        cls._actions[name] = action_cls
        return action_cls

    @classmethod
    def get(cls, name: str) -> type[Action]:
        if name not in cls._actions:
            raise ConfigError(f"unknown action: {name}")
        return cls._actions[name]

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._actions.keys())
