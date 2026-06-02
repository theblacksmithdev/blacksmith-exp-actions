from __future__ import annotations

import typer

import blacksmith.actions  # noqa: F401  (side-effect: action registration)
from blacksmith.actions.registry import ActionRegistry
from blacksmith.core.exceptions import BlacksmithError
from blacksmith.core.logging import LoggingConfigurator

app = typer.Typer(
    name="blacksmith",
    help="Blacksmith Experience Actions runner.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root() -> None:
    """Run a registered Blacksmith action."""


@app.command()
def reviewer() -> None:
    """Run the senior-engineer code review on the triggering pull request."""
    _dispatch("reviewer")


def _dispatch(name: str) -> None:
    LoggingConfigurator().configure()
    try:
        action_cls = ActionRegistry.get(name)
        exit_code = action_cls.from_env().run()
    except BlacksmithError as exc:
        typer.echo(f"blacksmith: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    raise typer.Exit(code=exit_code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
