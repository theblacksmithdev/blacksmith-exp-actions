# Blacksmith — Code Review

Senior-engineer code review on every pull request in your **Blacksmith Experience** apprenticeship.

You're not reviewing alone. The senior engineers on your team look at every PR you open — checking correctness, security, and design — and post their feedback as a real GitHub review. This page explains what you'll see, how to invoke them again, and how to read what they give you.

---

## What you'll see on a PR

Within ~30 seconds of opening or pushing to a PR, a review appears from **Lars** (`lars-blacksmith-exp[bot]`) — your team's Staff Engineer. (Per-persona reviewers for each Senior — Frontend, Backend, Database — are on the roadmap; today Lars covers all of it.) It has two parts:

1. **Inline comments** anchored to specific lines you added or changed. Each comment names a severity (`critical` / `high` / `medium` / `low`), a short title, and a concrete failing scenario plus the fix.
2. **A summary** at the top, in Lars's voice — one to three sentences with his overall read of the PR, the way a senior would describe it at the standup. Something like _"Looks clean. The cache-key collapse on line 84 is the only thing I would not let through, the rest is fine."_ Any findings he couldn't anchor to a specific line appear below the summary in a small notes section.

If there's nothing worth flagging, the summary will say so in his voice — _"Ship it."_, _"Nothing to add."_, something along those lines. That happens, but don't expect it on every PR. Senior reviewers find things.

If anything is `critical`, the review is posted as **`REQUEST_CHANGES`** rather than a plain comment. That doesn't block merging in GitHub, but treat it as the team telling you "fix this before we ship."

The reviewer **never auto-approves**. Approval is a teammate's judgment call, not the machine's.

---

## How to use it

### The workflow file

The Experience installs a workflow at **`.github/workflows/blacksmith-review.yml`** in your project repo. You shouldn't normally need to touch it — but here's what's running on your PRs:

```yaml
name: Blacksmith — Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]
permissions:
  models: read
jobs:
  review:
    if: github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && github.event.issue.pull_request != null && github.event.comment.user.type != 'Bot' && contains(github.event.comment.body, '@lars-blacksmith-exp'))
    runs-on: ubuntu-latest
    steps:
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          app-private-key: ${{ secrets.BLACKSMITH_REVIEWER_PRIVATE_KEY }}
          project-id: ${{ secrets.BLACKSMITH_PROJECT_ID }}
          model: openai/gpt-4o-mini
          min-severity: low
```

What each piece does:
- **`on: pull_request`** — runs when you open a PR or push more commits to it.
- **`on: issue_comment`** + the `if:` block — enables the on-demand re-review when you mention `@lars-blacksmith-exp` in a PR comment. The filter ensures it only fires on PR comments (not plain issues), and not on comments from other bots.
- **`permissions: models: read`** — needed on the workflow's `GITHUB_TOKEN` so the action can call GitHub Models for inference. The App's installation token is used to post the review under the bot identity, but inference uses the workflow token because App installation tokens don't carry the `models` permission.
- **`uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1`** — pins to the moving `v1` tag so you get improvements automatically. The `/reviewer` segment selects the reviewer action from the monorepo; future actions live at sibling paths (e.g. `/triager`, `/standup`).
- **`app-private-key`** — used in the example for simplicity. Lars's installation token comes from this. For production, prefer `app-token-broker-url` so the apprentice repo holds zero secrets and the private key stays on Blacksmith infrastructure. See the "Two ways to give the action Lars's identity" section below.
- **`with:` inputs** — see the table below.

#### Inputs you can tune

| Input                       | Default               | What it does                                                                                   |
|-----------------------------|-----------------------|------------------------------------------------------------------------------------------------|
| `model`                     | `openai/gpt-4o-mini`  | Which GitHub Models LLM the senior team uses. Any catalog id works.                            |
| `app-token-broker-url`      | _(none)_              | URL of the Blacksmith token broker. Set this for the keyless production path; the apprentice repo holds no App secrets and the broker mints the installation token after verifying the workflow's OIDC claims. Provisioned by the Experience platform. |
| `app-token-broker-audience` | _(broker URL)_        | Audience claim for the broker's OIDC JWT. Defaults to the broker URL.                          |
| `app-private-key`           | _(none)_              | PEM-formatted private key for the `lars-blacksmith-exp` GitHub App. Local-dev / fallback path when no broker is configured. |
| `app-id`                    | `3948048`             | App ID for `lars-blacksmith-exp`. Hardcoded — not a secret. Don't change this.                 |
| `github-token`              | `${{ github.token }}` | Last-resort fallback. Used only when neither the broker nor the private key is set. Posts as `github-actions[bot]`. |
| `min-severity`              | `low`                 | Lowest severity to post. `low` / `medium` / `high` / `critical`.                               |
| `project-id`                | _(none)_              | UUID of your Blacksmith Experience project. Provisioned for you as a repo secret. Links Lars's reviews back to your apprenticeship state. |
| `tracking-url`              | _(none)_              | Base URL of the Experience tracking endpoint. Set by the Experience platform.                  |

#### Two ways to give the action Lars's identity

Pick one. Both end with the same outcome: the action holds a short-lived installation token and posts as `lars-blacksmith-exp[bot]`. They differ in where the App's private key lives.

**Broker mode (preferred for production)** — apprentice repo holds nothing. The workflow grants `id-token: write`, mints a GitHub Actions OIDC JWT, and POSTs it to the Blacksmith-hosted broker. The broker verifies the JWT signature and claims, confirms the App is installed on the calling repo, mints an installation token with the private key it holds centrally, and returns it. Set `app-token-broker-url` and leave `app-private-key` empty.

```yaml
permissions:
  models: read
  id-token: write          # required for the OIDC mint
jobs:
  review:
    steps:
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          app-token-broker-url: https://broker.blacksmith.dev/installation-token
          project-id: ${{ secrets.BLACKSMITH_PROJECT_ID }}
```

**Local-key mode (fallback)** — the App's private key sits in the apprentice repo as a secret. The action mints the installation token directly. Simpler to wire up, no broker needed, but the key is per-repo. Use this for local dev, smoke tests, or repos that can't reach the broker.

```yaml
permissions:
  models: read
jobs:
  review:
    steps:
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          app-private-key: ${{ secrets.BLACKSMITH_REVIEWER_PRIVATE_KEY }}
          project-id: ${{ secrets.BLACKSMITH_PROJECT_ID }}
```

If both are set, the broker wins. If neither is set, the action falls back to `${{ github.token }}` and posts as `github-actions[bot]` — that's the signal to check your wiring.

If your reviews suddenly stop appearing, the first thing to check is whether this workflow file still exists in your repo — accidental deletions happen, and without it nothing runs.

### Day-to-day: automatic
Just work the way you normally would. Every time you open a PR or push commits to one, a review is triggered. No action on your part.

### Talking to Lars in the thread: `@lars-blacksmith-exp`

Lars can take part in the PR conversation. If you want him to look at a refactor, or you disagree with a finding, or you want to argue back on a call he made, just mention **`@lars-blacksmith-exp`** in any PR comment. He reads the thread he's been pinged on and replies in-line, the way a teammate would.

```
@lars-blacksmith-exp this isn't actually wrong — the caller upstream already
validates the input, see auth/middleware.py:42.
```

A few notes on how he responds:
- He reads the PR thread on this PR only. He won't remember other PRs, other conversations from yesterday, or things you discussed in your standup.
- He'll change his mind out loud if you convince him. He won't soften his position to be polite if you don't.
- He won't auto-trigger a fresh review when you mention him — to get a new review pass, push a new commit. Mentions are for conversation.

A fresh review will appear within a few seconds.

### With project-specific guidance: `.blacksmith/REVIEW.md`

If your project has rules a generic reviewer wouldn't know — naming conventions, architectural constraints, "we always do X here" — write them into **`.blacksmith/REVIEW.md`** in your repo. The reviewer reads that file at the PR's head commit and obeys it. Treat it as a way to teach the team about your project's idioms.

Example `.blacksmith/REVIEW.md`:
```markdown
- All API handlers must validate input with our `validators.py` module.
- New database queries must go through `db.session.scope()`, not raw `db.execute()`.
- Anything under `internal/` is not part of the public API; flag any export from there.
- Migrations are forward-only — never edit a migration that's already been merged.
```

### Tuning the workflow

If you want a stricter floor (only `high` and above, say) you can edit your workflow file:

```yaml
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          model: openai/gpt-4o-mini
          min-severity: high
```

Or switch the model:

```yaml
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          model: openai/gpt-4o
          min-severity: low
```

Check with your EM before bumping `min-severity` — they may want all findings visible for level-review evidence even if a few are nits.

---

## Reading the feedback

### Severity, what it actually means
- **`critical`** — bug or vulnerability that will hurt someone in production. Fix before merging.
- **`high`** — clearly wrong; will cause real problems even if not immediate.
- **`medium`** — design or correctness issue that a senior engineer would want addressed.
- **`low`** — minor; worth noting, won't usually block a merge.

You can raise the floor with the `min-severity` workflow input if you want only `high` and above. Your Experience setup may have configured this for you already.

### What files get reviewed
Every file with a textual diff — source code, configs, docs, migrations, Dockerfiles, shell scripts, SQL, YAML, Markdown, whatever. If the team would care about it in a real PR review, the team here will too. Binary files (GitHub doesn't produce a diff for those) and deleted files are skipped automatically; otherwise everything in your PR is on the table.

---

## If you disagree with a finding

You will, eventually. Pushing back is part of the apprenticeship, not a violation of it.

- **Reply in the PR thread.** Make your argument the same way you would with a human teammate. Be specific: name the assumption you think the reviewer got wrong, or the constraint they didn't see.
- **Don't silently dismiss.** "I disagree" without engagement is something a junior does. Stating *why* you disagree, in a way a senior teammate would find compelling, is the muscle the Experience is building.
- **Sometimes the reviewer is wrong.** It happens. When it does, your reasoning gets recorded as evidence of your judgment — which feeds into how your competencies are tracked.
- **Sometimes the reviewer is right and the feedback stings.** That's the calibration working as designed. Senior engineers in strong teams give feedback you'd rather not hear; one of the things the Experience is investing in is your ability to receive it without flinching.

If you think a review is *systematically* off — not one finding, but a pattern — talk to your Engineering Manager in the Experience web app. That's exactly the kind of issue they're there for.

---

## What you should *not* do

- **Don't disable or modify the workflow file** the Experience installed. Your level reviews depend on the team having a continuous record of the work you shipped and the feedback you got on it. If you turn this off, your EM has nothing to calibrate against.
- **Don't game the reviewer** by structuring PRs to avoid flagged patterns rather than fixing the underlying issue. The team observes the *pattern* of your work over many PRs; the per-PR score isn't what matters.

---

## Known limitations (today)

These are gaps the Experience knows about and is closing:

- Today every review is from **Lars**, regardless of whether the PR is frontend, backend, or database work. Per-domain reviewers — Ravi (Senior Frontend), Tunde (Senior Backend), Rosa (Senior Database) — each as their own GitHub app, are being built; soon a frontend PR will come from Ravi, a database migration from Rosa, and so on.
- On PRs from **forks**, GitHub doesn't grant the workflow the secrets needed to mint the app token, so the review will fail to post. The Experience normally won't have you working from forks; if you hit this, mention it in your standup.
- **One review pass per PR.** No multi-pass voting, no self-fix suggestions. The hosted Blacksmith reviewer (separate, post-graduation product) does more.

---

## Questions

- **About a specific review** → reply on the PR. The team reads PR threads.
- **About how the reviewer works** → ask your Tech Lead in the Experience.
- **About your growth / whether the reviews are landing fairly** → that's a 1:1 with your EM.

---

## For Blacksmith engineers

If you're maintaining this codebase or adding new actions, see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## License

MIT — see [`LICENSE`](./LICENSE).
