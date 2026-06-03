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
src/blacksmith/
├── core/
│   ├── persona.py                      # AgentPersona dataclass (slim mirror of main project)
│   └── tracking.py                     # TrackingClient + ReviewPostedEvent
├── personas/
│   ├── __init__.py                     # exports LARS
│   └── lars.py                         # vendored Lars persona
tests/
├── core/test_diff.py, test_persona.py, test_tracking.py
└── actions/reviewer/test_findings.py, test_review.py, test_reviewable.py, test_prompt.py
```

### Planned layers (not yet built)

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

## GitHub App: `lars-blacksmith-exp` (Lars, Staff Engineer)

The reviewer's PR comments appear under the `lars-blacksmith-exp[bot]` identity — **Lars**, the Staff Engineer on the apprentice's fictional team. That identity is a **GitHub App** owned by Blacksmith and installed on each apprentice repo. The `reviewer` action itself mints the installation token from the App's credentials at job start, so the apprentice workflow only has to pass one input: `app-private-key`.

Lars is the cross-cutting reviewer — he covers all PR types until per-domain personas (Ravi for frontend, Tunde for backend, Rosa for database) ship as separate apps with their own slugs (e.g. `ravi-blacksmith-exp`, etc.). Each persona action overrides the `app-id` default in `reviewer/action.yml`.

### App registration (one-time, per Blacksmith)

App ID `3948048`, registered under the `theblacksmithdev` org with:

- **URL slug**: `lars-blacksmith-exp` (the `[bot]` handle users see on PRs)
- **Display name**: "Lars · Staff Engineer" (or similar — free text)
- **Avatar**: Lars's headshot from the team page
- **Webhook**: disabled. The workflow is triggered by GitHub-native events, not by App webhooks.
- **Repository permissions**:
  - `Contents: read` — needed to fetch `.blacksmith/REVIEW.md` raw at the PR head.
  - `Pull requests: write` — needed to list PR files, get the PR, and post the review.
  - `Metadata: read` (implicit).
- **Account permissions**:
  - `Models: read` — needed so the same token can call the GitHub Models inference endpoint.
- **Where can this App be installed**: `Any account` (apprentice orgs install it on their own repos).

The App ID is hardcoded as the default of the `app-id` input in `reviewer/action.yml`. App IDs are not secrets — they're shown on the App's public page. Only the private key needs distribution.

Per-persona apps (Senior Frontend, Senior Backend, …) ship as separate registrations under the same naming convention (`blacksmith-frontend-senior`, etc.) — one App per identity is what gives each one a distinct face on PRs. Each persona action overrides the `app-id` default.

### Credential distribution — **open decision**

The workflow needs the App's private key at job start. Three options, blast-radius vs. operational cost:

1. **Per-repo secrets, automated by the Experience.** Experience's OAuth App (`Blacksmith Experience`) already holds `repo` scope on the apprentice's behalf. At provisioning time it writes `BLACKSMITH_REVIEWER_PRIVATE_KEY` into the apprentice's repo secrets via `PUT /repos/{owner}/{repo}/actions/secrets/{name}` (libsodium-encrypted). Apprentice never touches secrets manually. **Caveat**: an apprentice with repo admin can extract the key via their own malicious workflow (`run: echo "${{ secrets.BLACKSMITH_REVIEWER_PRIVATE_KEY }}" | base64`) and impersonate the bot on every other apprentice repo. Acceptable for vetted-cohort phase, not for general release.
2. **Per-org App registration.** Each apprentice org gets its own App (different App ID + key, same name/avatar). A leaked key only impersonates within that one org. Correct blast radius. Provisioning cost: Experience must register an App on each new apprentice org via the GitHub API.
3. **Centralized token broker.** Workflow uses GitHub OIDC (`id-token: write`, free, no setup) to prove "I'm running in workflow X of repo Y at commit Z." Sends OIDC token to a Blacksmith-hosted endpoint that validates the claim, confirms the App is installed on repo Y, mints a scoped installation token using the private key it holds, returns it. Private key never leaves Blacksmith infrastructure. Apprentice repos hold zero secrets. Real infra to deploy and operate (~100 LOC service + uptime monitoring).

The current README workflow assumes option 1. Before this ships to real apprentices outside vetted cohorts, pick 2 or 3.

---

## Engagement tracking

The reviewer emits a `review_posted` event after every successful review post, attributing it to the apprentice via `project-id` (UUID, passed as a repo secret). The payload is structured (see `src/blacksmith/core/tracking.py:ReviewPostedEvent`):

```json
{
  "project_id": "<UUID>",
  "repo": "owner/name",
  "pr_number": 42,
  "commit_sha": "...",
  "model": "openai/gpt-4o-mini",
  "findings_total": 3,
  "findings_by_severity": {"high": 1, "low": 2},
  "mention_triggered": false
}
```

The receiver endpoint on the main Blacksmith Experience project has not been built yet — see `TODO(blacksmith-experience)` in `src/blacksmith/core/tracking.py`. Until `tracking-url` is set on the action input, emits are no-op'd by `TrackingClient.enabled`. The action does not fail when the endpoint is down — tracking is best-effort and a failed emit logs a warning but lets the review-posted flow succeed.

**The full contract for the Experience backend** (every endpoint the action wants to call, the auth options, storage hints, definition of done) is written up in [`docs/EXPERIENCE_BACKEND_CONTRACT.md`](./docs/EXPERIENCE_BACKEND_CONTRACT.md). That's the doc to hand to whoever is implementing this in the main project.

### The other half: engagement signals

`review_posted` is what the action itself can see. The interesting signals come *after* the workflow finishes:

- Apprentice replies to a Lars comment in a PR thread → engaged
- Apprentice marks a conversation resolved without replying → dismissed
- Apprentice pushes a follow-up commit that touches the flagged line → addressed (silently)
- Apprentice pushes without touching the flagged line → ignored

These require **GitHub App webhooks** on `lars-blacksmith-exp`, routed to a Blacksmith-hosted webhook receiver in the main project. The reviewer GitHub Action sees none of this — it only handles the initial post. Subscribed events would be `pull_request_review_comment`, `issue_comment`, `pull_request_review`, `pull_request`, `push`. Webhook receiver is part of the next slice of work in the main project; this repo's role ends at the structured emit on review-post.

---

## Versioning + release

Tags follow `vMAJOR.MINOR.PATCH`. A moving `v1` tag tracks the latest 1.x release. The Experience product pins workflows to `@v1` — rolling the tag forward propagates fixes to every active apprentice repo without per-repo edits.

Cut a release by tagging `vX.Y.Z` and force-updating `v1` to the same commit.
