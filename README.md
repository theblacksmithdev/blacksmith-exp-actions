# Blacksmith — Code Review

Senior-engineer code review on every pull request in your **Blacksmith Experience** apprenticeship.

You're not reviewing alone. The senior engineers on your team look at every PR you open — checking correctness, security, and design — and post their feedback as a real GitHub review. This page explains what you'll see, how to invoke them again, and how to read what they give you.

---

## What you'll see on a PR

Within ~30 seconds of opening or pushing to a PR, a review appears from `github-actions[bot]` (the persona layer that gives each senior a distinct GitHub identity is on the roadmap). It has two parts:

1. **Inline comments** anchored to specific lines you added or changed. Each comment names a severity (`critical` / `high` / `medium` / `low`), a short title, and a concrete failing scenario plus the fix.
2. **A summary** at the top with the total count, a breakdown by severity, and any findings the reviewer couldn't anchor to a specific line.

If there's nothing worth flagging, you'll see `✅ No issues found.` That happens — but don't expect it on every PR. Senior reviewers find things.

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
  contents: read
  pull-requests: write
  models: read
jobs:
  review:
    if: github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && github.event.issue.pull_request != null && github.event.comment.user.type != 'Bot' && contains(github.event.comment.body, '@blacksmith-dev'))
    runs-on: ubuntu-latest
    steps:
      - uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1
        with:
          model: openai/gpt-4o-mini
          min-severity: low
```

What each piece does:
- **`on: pull_request`** — runs when you open a PR or push more commits to it.
- **`on: issue_comment`** + the `if:` block — enables the on-demand re-review when you mention `@blacksmith-dev` in a PR comment. The filter ensures it only fires on PR comments (not plain issues), and not on comments from other bots.
- **`permissions`** — `pull-requests: write` lets the action post the review; `models: read` lets it call GitHub Models for inference.
- **`uses: theblacksmithdev/blacksmith-exp-actions/reviewer@v1`** — pins to the moving `v1` tag so you get improvements automatically. The `/reviewer` segment selects the reviewer action from the monorepo; future actions live at sibling paths (e.g. `/triager`, `/standup`).
- **`with:` inputs** — see the table below.

#### Inputs you can tune

| Input          | Default               | What it does                                                              |
|----------------|-----------------------|---------------------------------------------------------------------------|
| `model`        | `openai/gpt-4o-mini`  | Which GitHub Models LLM the senior team uses. Any catalog id works.       |
| `github-token` | `${{ github.token }}` | The token used to call inference and post the review. Don't change this.  |
| `min-severity` | `low`                 | Lowest severity to post. `low` / `medium` / `high` / `critical`.          |

If your reviews suddenly stop appearing, the first thing to check is whether this file still exists in your repo — accidental deletions happen, and without it nothing runs.

### Day-to-day: automatic
Just work the way you normally would. Every time you open a PR or push commits to one, a review is triggered. No action on your part.

### On demand: `@blacksmith-dev`

Want the team to look again — maybe after a refactor, or because the first review felt off? Drop a comment anywhere in the PR thread mentioning **`@blacksmith-dev`**:

```
@blacksmith-dev can you take another look — I restructured the auth flow.
```

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

- Reviews currently post as **`github-actions[bot]`**, not as the distinct named persona who's reviewing you. The persona layer (Senior Frontend, Senior Backend, Senior Database, Staff, …) is being built — soon each review will come from a teammate with a name.
- On PRs from **forks**, GitHub doesn't grant the action write access to your repo, so the review will fail to post. The Experience normally won't have you working from forks; if you hit this, mention it in your standup.
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
