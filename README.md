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

### Automatically
Just work the way you normally would. Every time you:
- open a PR, or
- push new commits to an existing PR,

a review is triggered.

### On demand
Want the team to look again — maybe after a refactor, or because the first review felt off? Drop a comment anywhere in the PR thread mentioning **`@blacksmith-dev`**:

```
@blacksmith-dev can you take another look — I restructured the auth flow.
```

A fresh review will appear within a few seconds.

### With project-specific guidance
If your project has rules a generic reviewer wouldn't know — naming conventions, architectural constraints, "we always do X here" — write them into **`.blacksmith/REVIEW.md`** in your repo. The reviewer reads that file at the PR's head commit and obeys it. Treat it as a way to teach the team about your project's idioms.

Example `.blacksmith/REVIEW.md`:
```markdown
- All API handlers must validate input with our `validators.py` module.
- New database queries must go through `db.session.scope()`, not raw `db.execute()`.
- Anything under `internal/` is not part of the public API; flag any export from there.
```

---

## Reading the feedback

### Severity, what it actually means
- **`critical`** — bug or vulnerability that will hurt someone in production. Fix before merging.
- **`high`** — clearly wrong; will cause real problems even if not immediate.
- **`medium`** — design or correctness issue that a senior engineer would want addressed.
- **`low`** — minor; worth noting, won't usually block a merge.

You can raise the floor with the `min-severity` workflow input if you want only `high` and above. Your Experience setup may have configured this for you already.

### What files get reviewed
Source files in: `.py .js .ts .tsx .jsx .go .rb .java .rs`. Everything else (docs, configs, lockfiles, assets) is skipped. Deleted files are skipped. If your PR only touches non-reviewable files, you'll see no review and that's expected.

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
