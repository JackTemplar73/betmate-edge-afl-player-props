# Base44 Hosting Stability Plan

This document packages the recommended path to move the current AFL player props runtime off `local machine + ngrok` and into a stable hosted setup that Base44 can call reliably.

## Recommendation

Use **Railway** as the primary hosting provider for phase 1.

Why Railway is the best fit for this runtime right now:

- It is straightforward to deploy a Python web service from a repo or Dockerfile.
- It supports environment-variable secrets cleanly.
- It supports persistent volumes, which matters because this runtime updates local CSV/HTML history files.
- It supports cron jobs if we later want scheduled refreshes in addition to the Base44-triggered manual refresh flow.

Render is the best fallback if we want a more explicit split between web service, cron job, and persistent disk, but for this current package Railway is the fastest path to a stable production URL.

## Why the current setup breaks

The current integration fails because it depends on:

- a local laptop staying awake
- two local Python servers staying alive
- an `ngrok` tunnel staying alive
- a public tunnel URL that can disappear or rotate

That is why Base44 sees:

- dead refresh URLs
- `404`
- `ERR_NGROK_3200`
- intermittent `500` behavior that is hard to diagnose

## Target hosted architecture

### Phase 1 target

Keep the current Python runtime, but host it properly:

- one hosted Python service for the refresh/public runtime
- one stable HTTPS URL for Base44
- one persistent data location for ledger/history/runtime outputs

Base44 should call only:

- `GET /health`
- `POST /refresh`

The hosted service remains responsible for:

- fetching Odds API data
- fetching Wheelo data
- scoring props
- updating CLV/tracking/history files
- rebuilding HTML
- returning JSON to Base44

### Phase 2 target

Separate concerns more clearly:

- **Refresh API**
  - fetch data
  - score props
  - update tracking/history
  - return JSON
- **Static report output**
  - rebuild HTML for external sharing/export
- **Base44**
  - render live `Prop`
  - render `BetHistory`
  - become the native app layer

### Long-term target

- Base44 frontend
- Base44 entities for:
  - `Match`
  - `Prop`
  - `BetHistory`
  - `RefreshRun`
  - `AppState`
- stable hosted Python scoring API first
- optional later port into Base44 backend functions if we want full native ownership

## Provider decision

### Primary recommendation: Railway

Use Railway first if the goal is:

- fastest stable deployment
- minimal operational friction
- one project containing web service + optional cron
- easy secrets and Docker deployment

Recommended Railway shape:

1. **One web service**
   - runs the hosted BetMate Edge runtime
   - exposes the stable public URL Base44 will call

2. **One persistent volume**
   - stores mutable runtime data
   - ledger/history/runtime output files

3. **Optional cron service later**
   - scheduled refresh
   - scheduled settlement or health checks

### Fallback recommendation: Render

Use Render instead if we prefer:

- very explicit web/worker/cron separation
- more operational guardrails in the dashboard
- a platform style that feels a bit more app-ops oriented

Render is still suitable, but Railway is the cleaner first move for this exact package.

## Important caveat: persistent writable data

This runtime is not fully stateless yet.

It writes and mutates files such as:

- `aflplayerprops_bet_history.csv`
- `oddsapi_wheelo_ev_qi.csv`
- generated HTML reports
- current fixture snapshots

That means the hosted service must not be treated as a pure ephemeral container unless we also move this state into:

- Base44 entities
- managed Postgres
- object storage
- or a mounted persistent disk/volume

### Practical phase-1 rule

For the first hosted cutover, use persistent disk/volume storage.

### Practical phase-2 rule

Move `BetHistory` and other mutable operational state into proper persistent application storage so the service becomes easier to redeploy safely.

## What was added to this package

To make hosted deployment easier, these deploy-oriented files are now included:

- `code/Dockerfile`
- `code/run_hosted_betmate_edge.sh`

The runtime servers were also updated to support hosting env vars:

- `PORT`
- `BETMATE_PUBLIC_HOST`
- `BETMATE_REFRESH_HOST`
- `BETMATE_REFRESH_PORT`

That means the hosted service can bind to the provider-injected port rather than assuming local `8000`.

## Recommended deployment path

### Step 1: deploy the existing Python runtime unchanged in logic

Do **not** rewrite the scoring system yet.

Deploy the current runtime first so we get:

- stable URL
- stable refresh path
- Base44 unblocked

### Step 2: point Base44 to the hosted service

Update Base44 secrets:

- `CODEX_REFRESH_URL`
- `CODEX_REFRESH_TOKEN`

After this, Base44 should no longer rely on `ngrok`.

### Step 3: lock in historical tracking persistence

Base44 must use `BetHistory` as the source of truth for:

- Tracking
- History
- results summaries
- profit/ROI charts

Do **not** reconstruct tracking from live `Prop` rows.

### Step 4: add operational visibility

Add:

- health checks
- structured logs
- refresh status tracking
- failure alerts
- lock handling for overlapping refresh attempts

### Step 5: make refresh idempotent

Ensure:

- `Match` upsert by `gameKey`
- `Prop` upsert by `propKey`
- `BetHistory` upsert by `betId`

### Step 6: version the model/runtime

Store:

- output version
- model version
- refresh timestamp

That makes Base44/Codex parity checks easier and reduces unexplained output drift.

## Exact files to deploy first

Minimum deploy set from `code/`:

- `betmate_edge_refresh_server.py`
- `betmate_edge_public_server.py`
- `run_hosted_betmate_edge.sh`
- `Dockerfile`
- `build_walters_summary_html.py`
- `extract_wheelo_today_pack.py`
- `score_oddsapi_wheelo_props.py`
- `aflplayerprops_history.py`
- `settle_player_props_from_wheelo.py`
- `base44_port_reference.py`
- `afl_match_mapping.csv`
- `afl_round_mapping.csv`

Required supporting runtime data at first deployment:

- current fixture/history files from `fixtures/`
- current import/export files from `exports/`

## Required secrets / env vars

### Required immediately

- `THE_ODDS_API_KEY`
- `CODEX_REFRESH_TOKEN`

### Runtime networking

- `PORT`
- `BETMATE_PUBLIC_HOST`
- `BETMATE_REFRESH_HOST`
- `BETMATE_REFRESH_PORT`

### Recommended later

- `BETMATE_DATA_DIR`

This should be introduced in the next hardening pass so mutable runtime files are clearly separated from code.

## Base44 changes required next

### Immediate Base44 changes

1. point Base44 to the hosted refresh URL
2. import `BetHistory`
3. render `Tracking` and `History` from `BetHistory`
4. keep `Prop` for live current-round views only

### After hosted cutover

Add safer Base44 backend behavior:

- log fetch status before entity writes
- write `RefreshRun` first
- then `Match`
- then `Prop`
- isolate failures by write step

## Recommended implementation order

1. Deploy hosted runtime on Railway
2. Update Base44 `CODEX_REFRESH_URL`
3. Import and verify `BetHistory`
4. Add health/logging/locking improvements
5. Add explicit writable data path separation
6. Decide later whether to port scoring into Base44 backend functions

## My recommendation

Do not jump straight to a full Base44 rewrite.

The lowest-risk path is:

1. stabilize hosting first
2. stabilize history persistence second
3. migrate runtime ownership later only after the hosted service is boring and reliable

That gets us:

- stable now
- native later
- no rushed rewrite

## Sources

- Railway Python deploy docs: <https://docs.railway.com/guides/python>
- Railway volumes docs: <https://docs.railway.com/guides/volumes>
- Railway healthchecks docs: <https://docs.railway.com/reference/healthchecks>
- Railway cron docs: <https://docs.railway.com/guides/cron-jobs>
- Render Python deploy docs: <https://render.com/docs/deploy-python>
- Render persistent disks docs: <https://render.com/docs/disks>
- Render cron jobs docs: <https://render.com/docs/cronjobs>
