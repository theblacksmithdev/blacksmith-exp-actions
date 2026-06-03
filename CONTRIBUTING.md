# Contributing — Blacksmith Experience Actions

This document is for Blacksmith engineers working on this repo. If you're an apprentice using the reviewer on your PRs, see [`README.md`](./README.md) instead.

---

## What this repo is

The GitHub-runner-side infrastructure for the **Blacksmith Experience**. Every persona's PR-side behaviour (review, standup, retro, intern-PR, level review, capstone, honesty audit, …) lives here as a registered action.

The `reviewer` action is the first one shipped. The `Action` ABC + `ActionRegistry` are the framework everything else plugs into.

For the product-level context behind these decisions, see the **Blacksmith Experience** project overview.

---

## Architecture

This repo is a **monorepo of composite actions**. Each action lives at the repo root in its own subdirectory containing an `action.yml`. All actions share one Python package (`src/blacksmith`) installed once per action run via `pip install "$GITHUB_ACTION_PATH/.."`.

```
reviewer/                               # Subdirectory action
└── action.yml                          # Referenced as theblacksmithdev/blacksmith-exp-actions/reviewer@v1
                                        # Future siblings: triager/action.yml, standup/action.yml, …
pyproject.toml                          # Python package config (shared, at repo root)
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
└── actions/reviewer/test_findings.py, test_review.py, test_reviewable.py
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

1. **Create the Python package**: `src/blacksmith/actions/<your_action>/action.py`

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

5. **Add the composite action**: create `<your_action>/action.yml` at the repo root with whatever inputs your action needs:

   ```yaml
   name: "Blacksmith — <Your Action>"
   description: "<one-line description>"
   author: "blacksmith-dev"
   branding:
     icon: <pick one from feathericons>
     color: orange

   inputs:
     github-token:
       description: "Token used for inference and writing to GitHub."
       required: false
       default: ${{ github.token }}
     # ... action-specific inputs

   runs:
     using: "composite"
     steps:
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - name: Install Blacksmith
         shell: bash
         run: pip install --quiet "$GITHUB_ACTION_PATH/.."
       - name: Run <your_action>
         shell: bash
         env:
           GITHUB_TOKEN: ${{ inputs.github-token }}
           REPO: ${{ github.repository }}
           EVENT_NAME: ${{ github.event_name }}
           # ... map inputs to env vars your action's from_env() reads
         run: python -m blacksmith <your_action>
   ```

6. **Apprentices reference it** as:
   ```yaml
   uses: theblacksmithdev/blacksmith-exp-actions/<your_action>@v1
   ```

---

## Conventions

- **Strict OOP.** Module-level functions are rare. Wrap operations in classes; use `@classmethod` for factories, `@staticmethod` for stateless helpers.
- **Typed everywhere.** Code is fully annotated; `mypy` runs in CI. Use `pydantic` v2 models for any data crossing a boundary; use `pydantic-settings` for env-driven config.
- **Minimal comments.** Type hints + good names carry the load. Only add a comment when the *why* is non-obvious (hidden constraint, subtle invariant, workaround).
- **Honesty mandate.** Any action that delivers feedback must actively counteract LLM validation tendency. When in doubt, ask: would a senior engineer in a strong team say this exactly this way?

---

## GitHub App: `blacksmith-reviewer`

The reviewer's PR comments appear under the `blacksmith-reviewer[bot]` identity. That identity is a **GitHub App** owned by Blacksmith and installed on each apprentice repo. The apprentice workflow mints a short-lived installation token at job start (`actions/create-github-app-token`) and passes it to the action as `github-token`.

### App registration (one-time, per Blacksmith)

Register the App under the Blacksmith GitHub org with:

- **Name**: `blacksmith-reviewer` (the `[bot]` slug users see)
- **Description / avatar**: whatever we want apprentices to see — this is the on-PR face of the senior team.
- **Webhook**: disabled. The workflow is triggered by GitHub-native events, not by App webhooks.
- **Repository permissions**:
  - `Contents: read` — needed to fetch `.blacksmith/REVIEW.md` raw at the PR head.
  - `Pull requests: write` — needed to list PR files, get the PR, and post the review.
  - `Metadata: read` (implicit).
- **Account permissions**:
  - `Models: read` — needed so the same token can call the GitHub Models inference endpoint.
- **Where can this App be installed**: Only on accounts owned by the Blacksmith org (or whichever org the Experience writes workflows into).

Per-persona apps (Senior Frontend, Senior Backend, …) ship as separate registrations under the same naming convention (`blacksmith-frontend-senior`, etc.) — one App per identity is what gives each one a distinct face on PRs.

### Credential distribution — **open decision**

The workflow needs two secrets at job start: the App ID and the App's private key. Two options, blast-radius vs. simplicity:

1. **Per-apprentice-org App install + repo secrets.** Experience installs the App on the apprentice's org, then writes `BLACKSMITH_REVIEWER_APP_ID` and `BLACKSMITH_REVIEWER_PRIVATE_KEY` as secrets into each apprentice repo. Simple, but the private key is now extractable by anyone with admin on any apprentice repo — and a leaked key impersonates the App on **every** repo it's installed on. Not acceptable past the prototype stage.
2. **Per-org App registration.** Each apprentice's org gets its own App registration (still named `blacksmith-reviewer`, but a different App ID + key). A leaked key only impersonates the App on that org's repos. Correct blast radius, but provisioning cost: the Experience platform has to register a new App via the GitHub API every time a new apprentice org joins.
3. **Centralized token broker.** Workflow calls a Blacksmith-hosted endpoint (OIDC-authenticated from the runner) that returns an installation token. Private key never leaves Blacksmith infrastructure. Cleanest, most operational work.

The current README workflow assumes option 1 (`secrets.BLACKSMITH_REVIEWER_APP_ID` / `secrets.BLACKSMITH_REVIEWER_PRIVATE_KEY`). Before this ships to real apprentices, pick 2 or 3 — option 1 is fine for development against throwaway repos only.

---

## Versioning + release

Tags follow `vMAJOR.MINOR.PATCH`. A moving `v1` tag tracks the latest 1.x release. The Experience product pins workflows to `@v1` — rolling the tag forward propagates fixes to every active apprentice repo without per-repo edits.

Cut a release by tagging `vX.Y.Z` and force-updating `v1` to the same commit.
