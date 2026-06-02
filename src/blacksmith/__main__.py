from __future__ import annotations

import argparse
import sys

import blacksmith.actions  # noqa: F401  (side-effect: action registration)
from blacksmith.actions.registry import ActionRegistry
from blacksmith.core.exceptions import BlacksmithError
from blacksmith.core.logging import LoggingConfigurator


class Cli:
    PROG = "blacksmith"

    def __init__(self, argv: list[str] | None = None) -> None:
        self._argv = argv

    def run(self) -> int:
        LoggingConfigurator().configure()
        args = self._parse_args()
        try:
            action_cls = ActionRegistry.get(args.action)
            action = action_cls.from_env()
            return action.run()
        except BlacksmithError as exc:
            print(f"{self.PROG}: {exc}", file=sys.stderr)
            return 1

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog=self.PROG,
            description="Blacksmith Dev GitHub Actions runner.",
        )
        parser.add_argument(
            "action",
            choices=ActionRegistry.names(),
            help="The Blacksmith action to run.",
        )
        return parser.parse_args(self._argv)


def main() -> int:
    return Cli().run()


if __name__ == "__main__":
    sys.exit(main())
