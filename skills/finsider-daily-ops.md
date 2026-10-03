# finsider-daily-ops — the daily maintenance loop

Run this once a day (Daniel, 2026-10-03): go through every company in the queue, tie
the books to the penny and release what is green, check that every environment is
actually serving, then move everything that is green on development into production.
The output is one short report in the shape at the end, with every number verified
against the product, never guessed.

**Invoke:** `/finsider-daily-ops` (or "run finsider maintenance").

Companion skills: `finsider-certify` (one company, in depth), `finsider-certify-unlock`
(the pending → active mechanics). This skill is the wide pass; it hands a company to
`finsider-certify` only when the wide pass finds something to fix.

---

## Standing rules

1. **Read before write.** Every probe in Phases 1–3 is read-only (`BEGIN READ ONLY`
   via Kudu, `gh`, `curl` to health endpoints). The only writes this loop makes are:
   merging green PRs, restarting a slot that did not pick up its deploy, and posting
   to Jira/GitHub. A company is never released, a ledger never touched, from here —
   that goes through `finsider-certify` with its own sign-offs.
2. **The verdict is the product's.** Certificates come from `qbo_certification_runs`
   written by the pipeline or the daily sync, and the release decision is
   `decideAutoActivation` (Mitch-be `src/api/workspace/services/onboarding-activation.js`).
   If a company is green there and still pending, something in that function's
   reason list is holding it; read the reason, do not override it.
3. **Mitch is the CPA.** Anything that holds a release on `classifications_need_review`
   is his: list the accounts, do not classify them. Anything that moves a customer
   number is a Plain English block to him (`Mitch-be/agent-docs/PLAIN-ENGLISH-BLOCK.md`).
4. **A deploy is live when `/api/health` uptime is younger than the deploy.** Never
   when the workflow is green. The restart step (PR #2062) now does this itself and
   fails the job if not; if that step failed, restart by hand and say so.
5. **One promotion PR per repo per pass, dev → prod, never a hotfix straight to the
   production branch.** Mitch-be: `development → master`. Mitch-fe: `development → main`.
   Backend first when the frontend reads a new route.
6. **Everything the team must act on lands on the Jira board** (active sprint from
   `/rest/agile/1.0/board/1/sprint?state=active`, field `customfield_10020`; statuses
   Assign / In Progress / In Review / CPA Review are board columns).

## Tooling you already have

- Scripts: `~/finsider-platform/.ops/daily/` (README inside). `kudu.sh [--dev] <script.js>`
  runs a Node script inside the prod (or dev slot) container; creds in
  `~/.config/finsider-stack/kudu-{prod,dev}.json` (600). Probes: `fleet-cert.js`,
  `pending-queue.js`, `blocking.js`, `redis-memory.js`, `redis-streams.js`,
  `reports-qa.mjs`. Each query runs in its own `BEGIN READ ONLY … ROLLBACK`.
- Redis probes are dependency-free RESP (the prod URL has no password; `REDIS_PASSWORD`
  is read separately). `MEMORY PURGE` is not allowed on Azure Cache.
- Health: `https://mitch-back-eah8fvhvfbapecdh.canadacentral-01.azurewebsites.net/api/health`
  (prod), `https://mitch-back-development-gzdqbeftf3e3dghv.canadacentral-01.azurewebsites.net/api/health`
  (dev), `https://staging.finsider.ai/strapi-proxy/health`, `https://app.finsider.ai/sign-in`
  (curl with `--resolve app.finsider.ai:443:$(dig +short app.finsider.ai @8.8.8.8 | tail -1)`
  because `/etc/hosts` points the apex at local Caddy).
- Headless app pass as the demo account: mint a Clerk sign-in ticket
  (`POST https://api.clerk.com/v1/sign_in_tokens`, key from `Mitch-fe/.env.local`,
  user = `demo@ycombinator.com`), open `/sign-in?__clerk_ticket=…`, then walk the
  report pages — `reports-qa.mjs` does the six reports and prints
  crashed / slides / actions / console errors per page.
- Verification MCP (`finsider-verification`: `list_workspaces`, `trigger_verification_run`,
  `get_verification_run`) when it connects; it is the `computeVerdict` path.

---

## Phase 1 — Fleet health (10 min, read-only)

1. **Environments serving.** Prod and dev `/api/health` → `healthy`, `workers` ≈ 55,
   uptime consistent with the last deploy. staging `/sign-in` 200. app.finsider.ai 200.
2. **Last deploys.** `gh run list --workflow master_mitch-back.yml --limit 1`,
   same for `development_mitch-back.yml`; Vercel production deployment READY
   (`vercel ls finsider --prod` or the Vercel MCP). Any run whose restart step failed
   → restart (`az webapp restart -g mitch-update -n mitch-back [--slot development]`),
   re-verify uptime.
3. **Redis.** `used_memory` well under `maxmemory`; no stream over ~1,100 entries
   (the cap from PR #2064). Dev at OOM means every enqueue on staging is failing.
4. **Queues.** Prod `report_snapshots_calculation`, `bulk_delete_workspace`,
   `accounting_transactions_upload`: `failed` not growing day over day; nothing
   `active` older than the stall ceiling. The SCRUM-1905 sweep posts to Slack when it
   recovers a wedged job — read #engineering for overnight alerts
   (`reauth_required`, `backfill_failed`, stuck-job recoveries).
5. **Overnight crons ran.** `dailyFinancialSync` 00:00 UTC, `nightlyVerificationReconciliation`
   05:15, `connectionHealthScan` 05:45, `integrityGateNightly` 06:15 — check the prod
   log (`/home/LogFiles/<date>_*_default_docker.log` via Kudu) for their start lines
   and any `error` after them.

## Phase 2 — The company queue (20 min, read-only)

Run the fleet query (`fleet-cert.js`): every `qbo_direct` connection with
its workspace, `onboarding_status`, connection `status`, `last_synced_at`, and the
latest certificate (`certified`, months, findings, `classification.status`,
`blockingCount`, `sourceBoundary.atRisk`). Then the pending query (`pending-queue.js`):
every `onboarding_status = 'pending'` workspace with owner email, ledger rows,
documents, uploads, connections.

For each connected company, in order:

| Observation | Meaning | Action |
|---|---|---|
| `last_synced_at` older than yesterday 01:30 UTC, status `connected` | Daily sync missed it | Read the sync log for the workspace; if the run never started, trigger the onboarding re-run (`POST /provider-connections/qbo/onboarding/run`, operator JWT recipe in memory); if it is throttled by the 2-concurrent cap, note and retry tomorrow |
| status `disconnected` / `revoked` | Intuit invalidated the grant (`last_error` says `invalid_grant`) | Nothing we can do server-side; confirm the `reauth_required` Slack alert fired; the card already offers "Refresh connection"; ticket in CPA Review for Mitch to ask the client only if older than 7 days |
| certificate red (`findings > 0`) | Books do not tie | Hand to `finsider-certify <ws> <name>`; this loop does not fix books |
| certificate green, `pending`, `blockingCount > 0` | Waiting on Mitch's classifications | List the accounts (unresolved classification names) in one comment on the company's ticket; CPA Review |
| certificate green, `pending`, `blockingCount = 0`, `sourceBoundary.atRisk` | Mixed-source seam (SCRUM-1471) | Hand to David's lane; do not release |
| certificate green, `pending`, no reason left | Should have auto-released | Read `decideAutoActivation`'s reasons from the last pipeline/sync run log; if `QBO_AUTO_ACTIVATE_ON_GREEN` is off or the certified window is shorter than the backfill, say which; only then consider the manual `POST /workspaces/:id/activate` per `finsider-certify-unlock.md` |
| certificate green, `active` | Released | Nothing; note `accuracy_status` if it is `issues` (the nightly verification found something — read the run) |

For each pending company without a connection: owner email, age, and whether it has
any data. A test name from a team email (`dev@gmail.com`, `qordev.com`, obvious
keyboard mashing) is noise — list it once a week for cleanup, not daily. A real
prospect with no data is waiting on the client, not on us.

Upload-only companies (no connection, ledger rows present): certificate lane
`manual_upload`, scope `source_set_reconciled` is the file check, not a release
certificate. Until SCRUM-1720/1721 ship, a manual company releases only by hand.

## Phase 3 — App smoke (10 min)

1. Headless pass over the six report pages as the demo account
   (`reports-qa.mjs https://app.finsider.ai <ticket> <outDir>`): zero `crashed`,
   zero page errors; slide counts roughly stable day over day (QoE ~68, Board ~32,
   Valuation ~7, Forecast ~8). A known pre-existing console line is the demo
   workspace's `cash-proof-v2` request; anything else is new.
2. Your QA account: `danielrredgar@gmail.com` is reset to a brand-new account on every
   sign-out from the account menu (memory `reference_finsider_qa_onboarding_reset_account_2026_10_02`).
   Once a week, sign in and walk the onboarding by hand.

## Phase 4 — Move development to production (30–60 min)

1. **What is waiting.** Both repos: `git log origin/<prod>..origin/development`
   grouped by merged PR; list titles and authors. Both branches must be ancestors of
   development (`main` / `master` ahead of development = a hotfix went around the
   policy; back-merge first, never cherry-pick).
2. **QA on a clean checkout of development** (worktree, `node_modules` symlinked):
   - Mitch-be: `TZ=UTC QOE_DATABASE_TESTS=1 QOE_TEST_DATABASE_URL=postgres://127.0.0.1:5432/qoe_test ACCURACY_GENERATION_TEST_DATABASE_URL=… DATAROOM_TEST_DATABASE_URL=… MANUAL_UPLOAD_PROVENANCE_TEST_DATABASE_URL=… npm test`
     with Node 20 (`/opt/homebrew/opt/node@20/bin`). A failure that is `Cannot find module`
     for a dependency new on development is the stale local `node_modules`, not code.
   - Mitch-fe: `npx tsc --noEmit` and `CI=1 npm test`. `drill-down-footing-notice`
     fails on main too (pre-existing).
   - Review migrations, schema.json changes (never a Strapi-managed column name), new
     dependencies, cron changes (a cron that ships off ships silent).
   - Dev slot: deployed on the development head, restarted, healthy, new routes answer.
3. **Promotion PRs**, Plain English block in the body, every included PR listed,
   backend first when the frontend depends on it. Wait for CI (`gh pr checks`), merge
   with `gh pr merge --merge`, never force.
4. **Verify production**, not the workflow: master run's restart step says
   "new process is serving"; prod `/api/health` uptime small; a new route answers
   401 not 404; a migration shows in `strapi_migrations` and its effect is visible in
   the data. Vercel production READY and aliased; `/sign-in` 200; rerun the Phase 3
   headless pass.
5. **Jira.** Each shipped ticket → comment "Promote development to master/main. PR #N
   is merged and live in production" and transition to Approved / In Prod (42).
   Anything that still needs Mitch → CPA Review (3) with the ask in the first line.

## Phase 5 — Report (5 min)

One message, this shape, numbers only from what you verified:

```
Finsider daily ops — <date>
Environments: prod ✅ (uptime 2h, 55 workers) · dev ✅ · staging ✅ · app.finsider.ai ✅ · Redis 1.0G / cap
Queue: 7 connected — 5 synced overnight, 2 disconnected (Wayne, CFC: Intuit invalid_grant, badge offered)
  Green & active: Ken Pools, DashClicks, MeetBeagle, eos, SocialAgency
  Waiting on Mitch: MeetBeagle 4 accounts, eos 9, Ken Pools 2, DashClicks 1, SocialAgency 1 (listed on tickets)
  Pending, no data: JMI, MedCoverage, Artificial Grass Co, 5th & Wellness (Mitch's prospects); UpTe (José test)
Promoted: BE #2065 (6 PRs) → master, restart step ✅; FE #1785 (4 PRs) → main, READY
Found today: <anything new, with the ticket>
Needs a human: <who, what, by when>
```

Then update the memory index if anything standing changed (a new trap, a new recipe,
a company's status that will matter tomorrow).
