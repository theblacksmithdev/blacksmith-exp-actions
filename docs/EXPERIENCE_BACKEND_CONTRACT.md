# Backend contract — what the Experience needs to expose

> Audience: engineers working in the main Blacksmith Experience repo (the Django app).
> Author: the `blacksmith-exp-actions` repo, which calls into the Experience backend from inside GitHub Actions workflows.

The `reviewer` action and the `lars-blacksmith-exp` GitHub App produce data the Experience needs in two shapes:

1. **Synchronous HTTP calls from the action**, made during a workflow run on an apprentice's repo. The action holds a project UUID (a secret on the apprentice repo) and uses it as the authorization identity for everything below.
2. **Asynchronous webhooks from the GitHub App**, fired by GitHub itself whenever something happens on a PR the App is installed on. These are the only way to see engagement that happens after a workflow finishes (replies, resolves, follow-up commits).

Both surfaces are stubbed in the action today (see `src/blacksmith/core/tracking.py` and `src/blacksmith/core/project.py`). Once you ship the endpoints below, we fill the TODOs and the action stops no-op'ing.

---

## Stack assumptions

- Django REST Framework (or whatever the rest of the project uses for views — match it).
- Auth model documented in §5 — open decision, please pick before implementing.
- Persistence: any of the existing models the project already uses for project state; nothing here requires new infra beyond a few tables.

---

## 1. `POST /review-posted` — tracking emit (sync)

Called by the action after every successful review post, regardless of whether findings were emitted. Best-effort from the action's side — failures here must not poison the apprentice's workflow run.

### Request

```http
POST {tracking-url}/review-posted
Authorization: <see §5>
Content-Type: application/json

{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "repo": "oluwatobimaxwell/rkbstudentaccommodation",
  "pr_number": 3,
  "commit_sha": "2ff8a5cce9e19bcffe9de3a40b653c7500a62f28",
  "model": "openai/gpt-4o-mini",
  "findings_total": 2,
  "findings_by_severity": {
    "high": 1,
    "medium": 1
  },
  "mention_triggered": false
}
```

Schema is the JSON serialization of `blacksmith.core.tracking.ReviewPostedEvent` — use that as the canonical reference. `mention_triggered` is currently always `false` in v1.5+ (mentions go through `_respond`, not `_review`) but kept on the payload for forward compat.

### Response

- `202 Accepted` is fine — no body required.
- Anything 2xx is treated as success.
- `4xx` is logged as a warning and the workflow continues. Don't expose validation errors as 5xx.

### What the Experience should do with this

At minimum: persist as a row keyed on `(project_id, repo, pr_number, commit_sha)`. This is the first leg of how the EM-side picture of "what work the apprentice is shipping" gets built.

---

## 2. Conversation state — read/write (sync, future)

The action's `Project` class is shaped for these endpoints but every method is a no-op today. When you build them, drop the `TODO(blacksmith-experience)` comments in `src/blacksmith/core/project.py` and wire `httpx` calls.

The conversation today reconstructs from GitHub's PR thread on each run, which is fine for in-thread replies but loses any context the apprentice and Lars built up over time (prior PRs, recurring topics). These endpoints are how that context lives outside one PR.

### 2.1 `GET /projects/{project_id}/prs/{repo}/{pr_number}/session`

Returns a persistent session identifier for the LLM provider. When we move from stateless `chat.completions` to OpenAI Assistants (or any provider with a server-side thread), this is where the thread id lives.

```http
200 OK
{ "session_id": "thread_abc123" }

404 Not Found
(when no session has been created for this PR yet — action will create one)
```

### 2.2 `PUT /projects/{project_id}/prs/{repo}/{pr_number}/session`

```http
PUT ...
{ "session_id": "thread_abc123" }

204 No Content
```

### 2.3 `GET /projects/{project_id}/prs/{repo}/{pr_number}/history`

Returns prior LLM message history for this PR, in OpenAI chat-completion shape. Used to seed Lars with context older than the GitHub thread can express (e.g. our own summaries, intent, what we said in a closed PR before).

```http
200 OK
{
  "messages": [
    { "role": "assistant", "content": "..." },
    { "role": "user", "content": "..." }
  ]
}
```

Empty array is a legitimate response — first encounter on this PR.

### 2.4 `POST /projects/{project_id}/prs/{repo}/{pr_number}/history`

Append the latest turn(s) to the history. Idempotency is nice-to-have but not required (the action will dedupe on its side if you don't).

```http
POST ...
{
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}

204 No Content
```

---

## 3. App webhook receiver (async)

The `lars-blacksmith-exp` GitHub App currently has webhooks **disabled**. Enable them and point the webhook URL at this endpoint to start capturing engagement signals the action can't see.

### Endpoint

```
POST {webhook-url}/github
```

GitHub signs requests with the webhook secret (HMAC SHA-256 in `X-Hub-Signature-256`). Verify it. Reject if signature doesn't match.

### Events to subscribe to

| Event                          | Why it matters                                                                  |
|--------------------------------|---------------------------------------------------------------------------------|
| `pull_request_review_comment`  | Apprentice replied to one of Lars's inline review threads — engaged.            |
| `issue_comment`                | PR-level thread activity. Includes the apprentice replying to Lars's summary.   |
| `pull_request_review`          | `submitted`, `dismissed`, `edited` on reviews — including someone marking conversations resolved. |
| `pull_request`                 | `synchronize` events tell us the apprentice pushed a follow-up commit.          |
| `pull_request_review_thread`   | `resolved` / `unresolved` — apprentice closed a thread, possibly without replying. |

### What to do with each

Roughly the signal taxonomy from `CONTRIBUTING.md`'s engagement-tracking section:

- **Replied with substance** → engaged. Persist the comment.
- **Resolved a thread without replying** → dismissed. Persist with a flag.
- **Pushed a commit that touches the flagged line** → addressed (silently). Requires looking at the patch against the original finding's `file:line`.
- **Pushed a commit that does not touch the flagged line** → ignored.

The classification logic can start crude and tighten over time. The webhook receiver's first job is just storing the raw events keyed on `(project_id, repo, pr_number)`. Aggregation/classification can be a separate cron or on-demand query.

---

## 4. Persona fetch (optional, future)

Currently each `*-blacksmith-exp` action vendors its persona from `src/blacksmith/personas/<name>.py` (see `MEMORY.md` entry on persona vendoring). If you want the Experience to be the single source of truth for personas, expose:

```
GET /personas/{slug}
```

Returns an `AgentPersona`-shaped JSON object that the action can deserialize. Until this exists, vendoring is fine and probably preferable — fewer network round-trips at workflow start.

---

## 5. Auth — **open decision, pick before implementing**

The action holds three things at the moment of an API call:
- The project UUID (a secret on the apprentice repo).
- The GitHub App's installation token (minted at workflow start from the App's private key).
- A GitHub OIDC token (free, automatic in workflows with `id-token: write`).

Pick one of:

1. **Project UUID as a bearer token.** Simplest. Apprentice repo holds the UUID as a secret; treat it as a static API key. Downside: a compromised repo means a permanent identity leak; rotation is per-apprentice.
2. **HMAC-signed requests.** Action signs the body with a shared secret; backend verifies. Same blast radius as #1 if the shared secret leaks.
3. **OIDC + JWT exchange.** Action sends its GitHub OIDC token to a `/auth/exchange` endpoint, you verify the `repository` claim matches the project's known repo, return a short-lived JWT. Cleanest. Same kind of model the cred-broker option for the App private key would use.

I'd lean #3 long-term, #1 for first ship if the apprentice cohort is small and vetted. Whichever you pick, document it on the endpoint contracts above (replace `<see §5>` in the Authorization header).

---

## 6. Storage hints (not requirements)

Rough sketch — design as you see fit:

- `ProjectReview` row: `(project_id, repo, pr_number, commit_sha, posted_at, findings_total, findings_by_severity)`. Append-only.
- `ConversationSession` row: `(project_id, repo, pr_number, session_id, provider)`. One per PR.
- `ConversationMessage` row: `(project_id, repo, pr_number, role, content, created_at, source)`. `source` distinguishes "from the action" vs "reconstructed from GitHub webhook".
- `EngagementSignal` row: `(project_id, repo, pr_number, kind, payload_json, received_at)`. Raw webhook events, classified later.

---

## 7. Out of scope for first ship

- Bulk import of past PRs.
- Cross-PR memory queries (Lars asking "what have I flagged for this apprentice before?"). Build later from the persisted history.
- Persona editing through the API. Personas are code today and that's fine.
- Multi-tenant separation between Blacksmith orgs. Single tenant for now.

---

## 8. Definition of done

The receiver is shippable when:

1. `POST /review-posted` accepts the schema in §1 and `curl`-tested locally returns 2xx.
2. App webhooks (§3) are enabled on `lars-blacksmith-exp` with a verified signature path, and at least one event lands in storage end-to-end.
3. Auth scheme (§5) is decided and documented.
4. Conversation endpoints (§2) can stay stubbed for the v1 receiver — they're not on the critical path until we move Lars off stateless inference.

When you ship §1 and §3, ping back and we'll drop the no-op stubs in the action and cut a `v1.6.0` of `blacksmith-exp-actions` that actually emits.
