# Blacksmith — Experience Actions

GitHub-runner-side infrastructure for the **Blacksmith Experience** — an apprenticeship program in which a coordinated team of AI agents (Engineering Manager, Tech Lead, Staff Engineer, Senior Frontend / Backend / Database Engineers, PM, Designer, Platform, Security, QA) develops a real user from junior toward verified senior-level engineering capability through simulated team membership.

Every persona's PR-facing behaviour — reviewing the user's code, opening PRs the user is meant to review, conducting standups in PR threads, running retros — runs as a registered action in this repository. The user's growth is recorded in their **real GitHub profile**: real PRs, real reviews, real work, verifiable by future employers.

This repo is the GitHub-actor layer of the Experience. The web product at `experience.blacksmith.dev` is what learners log into; this is what the agents use on the runner.

---

## Currently shipping

### `reviewer` — senior-engineer code review

The Experience installs this action in the learner's project repository. On every pull request (and on `@blacksmith-dev` mentions in PR comments), a senior-engineer persona reviews the code: inline comments anchored to changed lines, and a summary with severity counts.

The Experience installs the following workflow at `.github/workflows/blacksmith-review.yml` in the learner's repo:

```yaml
name: Blacksmith Dev — Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]
permissions:
  contents: read
  pull-requests: write
  models: read
jobs:
  review:
    if: github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && github.event.issue.pull_request != null && github.event.comment.user.type != 'Bot' && contains(github.event.comment.body, '@blacksmith-dev'))
    runs-on: ubuntu-latest
    steps:
      - uses: blacksmith-dev/reviewer@v1
        with:
          model: openai/gpt-4o-mini
```

#### Inputs

| Input          | Required | Default               | Purpose                                                                 |
|----------------|----------|-----------------------|-------------------------------------------------------------------------|
| `model`        | no       | `openai/gpt-4o-mini`  | GitHub Models catalog id used for inference.                            |
| `github-token` | no       | `${{ github.token }}` | Token used both for inference (GitHub Models) and posting the review.   |
| `min-severity` | no       | `low`                 | Lowest severity to post. One of `low`, `medium`, `high`, `critical`.    |

#### Custom review rules (optional)

If the learner's repo has a file at `.blacksmith/REVIEW.md`, the reviewer reads it at the PR's `head` commit and includes it as project-specific rules in the prompt.

#### Current gaps (tracked, not abandoned)

The reviewer in its v1 form predates the Experience's persona layer. Three things are deliberately incomplete and will land before the Experience opens to learners:

- **Persona is a placeholder.** The current prompt addresses a generic "Dev" senior reviewer. The Experience requires named personas (Senior Frontend / Backend / Database, Staff) each with a distinct communication style, opinions, and a developmental mandate over specific competencies.
- **Identity is `github-actions[bot]`.** Each agent must instead authenticate as its own GitHub App so the PR conversation feels like a real team with distinct teammates.
- **Findings do not yet update competency state.** Every observation a senior makes about the learner is supposed to flow into a structured competency record that the Engineering Manager reads before level reviews. The reviewer currently only posts the GitHub-side artefacts.

Each of these has a planned home in the architecture below.

---

## Architecture

```
action.yml                              # Reviewer composite action (root)
pyproject.toml                          # Python package config
src/blacksmith/
├── __main__.py                         # `python -m blacksmith <action>`
├── core/                               # shared building blocks, reusable across all actions
│   ├── http.py                         # HttpClient (httpx wrapper)
│   ├── github.py                       # GitHubClient + DTOs
│   ├── inference.py                    # GitHubModelsClient
│   ├── diff.py                         # DiffParser
│   ├── event.py                        # EventContext
│   ├── logging.py                      # LoggingConfigurator
│   └── exceptions.py
└── actions/
    ├── base.py                         # Action ABC: from_env() + run()
    ├── registry.py                     # ActionRegistry (decorator-based)
    └── reviewer/
        ├── action.py                   # ReviewerAction(Action)
        ├── config.py                   # ReviewerConfig
        ├── findings.py                 # Finding + FindingsParser
        ├── prompt.py                   # PromptBuilder
        ├── review.py                   # ReviewBuilder
        └── severity.py                 # Severity enum
tests/
├── core/test_diff.py
└── actions/reviewer/test_findings.py, test_review.py
```

### Planned layers (not yet built)

- `src/blacksmith/personas/` — persona definitions (name, voice, opinions, developmental mandate over competencies). Each action selects a persona per run.
- `src/blacksmith/core/auth.py` — `GitHubAppAuth` for minting per-persona installation tokens from App private keys. Replaces the use of the default `GITHUB_TOKEN` for identity-bearing actions.
- `src/blacksmith/core/competency.py` — writer for the competency-state store (structured observations consumed by the Engineering Manager during level reviews).

### Planned actions (not yet built)

- `honesty-audit` — the separate review pass that grades the EM's feedback for honesty before it reaches the user. Load-bearing for the credential's integrity.
- `standup` — drives the daily standup as a PR-thread / discussion conversation.
- `intern-pr` — opens PRs from the junior Intern agent for the user to review (the user develops the Mentorship competency at Level 3+).
- `retro` — runs the sprint retrospective and writes the resulting observations into competency state.
- `level-review` — proctors the user's transition between competency levels.
- `capstone` — administers the Senior Verification at Level 5.

---

## Adding a new action

1. Create `src/blacksmith/actions/<your_action>/action.py` with a class that subclasses `Action`, sets `name = "<your_action>"`, and is decorated with `@ActionRegistry.register`.
2. Implement `from_env()` (build dependencies from environment) and `run() -> int`.
3. Reuse anything you need from `blacksmith.core` (HTTP, GitHub, inference, diff, event).
4. Import the new action in `src/blacksmith/actions/__init__.py` so the registry sees it at startup.
5. Ship a sibling repo `blacksmith-dev/<your_action>` whose `action.yml` runs `pip install "$GITHUB_ACTION_PATH"` then `python -m blacksmith <your_action>`.

---

## Local development

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

CI runs the same three steps on every push and PR.

---

## Versioning

Releases are tagged `vMAJOR.MINOR.PATCH`. A moving `v1` tag tracks the latest 1.x release — the Experience product pins to `@v1`, and rolling the tag forward propagates fixes and improvements to every learner repo without per-repo workflow edits.

---

## License

MIT — see [`LICENSE`](./LICENSE).
