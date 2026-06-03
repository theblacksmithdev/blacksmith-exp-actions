# Contributing — Blacksmith Experience Actions

This document is for Blacksmith engineers working on this repo. If you're an apprentice using the reviewer on your PRs, see [`README.md`](./README.md) instead.

---

## What this repo is

The GitHub-runner-side infrastructure for the **Blacksmith Experience**. Every persona's PR-side behaviour (review, standup, retro, intern-PR, level review, capstone, honesty audit, …) lives here as a registered action.

The `reviewer` action is the first one shipped. The `Action` ABC + `ActionRegistry` are the framework everything else plugs into.

For the product-level context behind these decisions, see the **Blacksmith Experience** project overview.

---

## Architecture

```
action.yml                              # Reviewer composite action (root)
pyproject.toml                          # Python package config
src/blacksmith/
├── __main__.py                         # typer CLI: `python -m blacksmith <action>`
├── core/                               # shared building blocks, reusable across all actions
│   ├── diff.py                         # DiffParser (wraps unidiff)
│   ├── event.py                        # EventContext (typed via githubkit webhooks)
│   ├── github.py                       # GitHubClient (wraps githubkit) + DTOs
│   ├── inference.py                    # GitHubModelsClient (wraps openai SDK)
│   ├── logging.py                      # LoggingConfigurator
│   └── exceptions.py
└── actions/
    ├── base.py                         # Action ABC: from_env() + run()
    ├── registry.py                     # ActionRegistry (decorator-based)
    └── reviewer/
        ├── action.py                   # ReviewerAction(Action)
        ├── config.py                   # ReviewerConfig (pydantic-settings)
        ├── findings.py                 # Finding + FindingsResponse (structured-output schema)
        ├── prompt.py                   # PromptBuilder
        ├── review.py                   # ReviewBuilder
        └── severity.py                 # Severity enum
tests/
├── core/test_diff.py
└── actions/reviewer/test_findings.py, test_review.py
```

### Planned layers (not yet built)

- `src/blacksmith/personas/` — persona definitions (name, voice, opinions, developmental mandate).
- `src/blacksmith/core/auth.py` — `GitHubAppAuth` for per-persona installation tokens.
- `src/blacksmith/core/competency.py` — writer for the competency-state store.

### Planned actions

- `honesty-audit` — grades EM feedback before it reaches the user. Load-bearing for credential integrity.
- `standup` — daily standup as a PR-thread / discussion conversation.
- `intern-pr` — opens PRs from the junior Intern agent for the user to review.
- `retro` — sprint retrospective.
- `level-review` — competency-level transitions.
- `capstone` — Senior Verification at Level 5.

---

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Loop:
ruff check src tests
mypy
pytest

# CLI sanity check:
python -m blacksmith --help
python -m blacksmith reviewer  # exits 1 with a clean error if env vars missing
```

CI runs the same four checks on every push/PR (see `.github/workflows/ci.yml`).

### Running the reviewer locally against a real PR

There's no mocked dry-run mode yet. To run end-to-end against a real PR:

```bash
GITHUB_TOKEN=ghp_xxx \
REPO=owner/repo \
EVENT_NAME=pull_request \
GITHUB_EVENT_PATH=/path/to/saved/event.json \
python -m blacksmith reviewer
```

This calls real GitHub Models and posts a real review. Use against a throwaway PR. Adding `--dry-run` and an integration harness with `respx` mocking is open work.

---

## Adding a new action

1. **Create the package**: `src/blacksmith/actions/<your_action>/action.py`

   ```python
   from blacksmith.actions.base import Action
   from blacksmith.actions.registry import ActionRegistry

   @ActionRegistry.register
   class YourAction(Action):
       name = "<your_action>"

       @classmethod
       def from_env(cls) -> "YourAction":
           # build dependencies from env
           ...

       def run(self) -> int:
           # do the work, return 0 on success
           ...
   ```

2. **Wire registration**: import in `src/blacksmith/actions/__init__.py`:
   ```python
   from blacksmith.actions.your_action.action import YourAction
   __all__ = [..., "YourAction"]
   ```

3. **Add a CLI command**: in `src/blacksmith/__main__.py`:
   ```python
   @app.command()
   def your_action() -> None:
       """One-line description for `--help`."""
       _dispatch("<your_action>")
   ```

4. **Reuse `core/` plumbing** — don't re-implement HTTP, GitHub API, inference, diff parsing, event handling. That's the entire point of `core/`.

5. **Ship a sibling repo** `blacksmith-dev/<your_action>` whose `action.yml` is:
   ```yaml
   runs:
     using: composite
     steps:
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - shell: bash
         run: pip install --quiet "$GITHUB_ACTION_PATH"
       - shell: bash
         env: { ... }
         run: python -m blacksmith <your_action>
   ```

---

## Conventions

- **Strict OOP.** Module-level functions are rare. Wrap operations in classes; use `@classmethod` for factories, `@staticmethod` for stateless helpers.
- **Typed everywhere.** Code is fully annotated; `mypy` runs in CI. Use `pydantic` v2 models for any data crossing a boundary; use `pydantic-settings` for env-driven config.
- **Minimal comments.** Type hints + good names carry the load. Only add a comment when the *why* is non-obvious (hidden constraint, subtle invariant, workaround).
- **Honesty mandate.** Any action that delivers feedback must actively counteract LLM validation tendency. When in doubt, ask: would a senior engineer in a strong team say this exactly this way?

---

## Versioning + release

Tags follow `vMAJOR.MINOR.PATCH`. A moving `v1` tag tracks the latest 1.x release. The Experience product pins workflows to `@v1` — rolling the tag forward propagates fixes to every active apprentice repo without per-repo edits.

Cut a release by tagging `vX.Y.Z` and force-updating `v1` to the same commit.
