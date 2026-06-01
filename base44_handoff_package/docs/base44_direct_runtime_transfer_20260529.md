# Base44 Direct Runtime Transfer

This package is the direct-runtime handoff for Base44 to run the AFL player props agent **without Codex acting as the live runtime owner**.

The intent is simple:

- Base44 owns execution
- Base44 owns refresh
- Base44 owns history persistence
- Base44 owns the app UI
- Codex is no longer required to be online for production refreshes

## What this package is for

Use this package when Base44 is going to run the Python agent directly in its own environment.

That means Base44 should:

- execute the Python runtime itself
- store secrets itself
- expose the refresh endpoint itself
- persist the ledger/history itself
- serve or consume the generated outputs itself

## What “all aspects of the agent” means

The transferred runtime includes:

1. **Data refresh**
   - fetch current Wheelo stats
   - fetch current Odds API events and player props

2. **Scoring**
   - build the Wheelo player pack
   - score player props
   - apply QI / EV / signal / stake rules

3. **History and CLV**
   - update the persistent bet ledger
   - track current QI rows
   - update latest and close prices

4. **Settlement**
   - settle completed games from official AFL.com.au stats
   - update ledger outcomes and profits

5. **Report output**
   - rebuild the HTML reports
   - expose JSON for Base44 native ingestion

## Package contents

The direct runtime bundle lives in:

- `direct_runtime/`

Inside it:

- `code/`
  - runnable Python scripts
  - startup shell script
  - Dockerfile
- `state_seed/`
  - initial CSV/JSON files needed to preserve current state
- `docs/`
  - deploy/runbook notes

## Runtime ownership model

Once moved:

- Base44 should run the Python service directly
- Base44 should no longer call the Codex-hosted/ngrok endpoint
- Base44 should call its own hosted runtime URL

## Required secrets

Base44 runtime secrets:

- `THE_ODDS_API_KEY`
- `CODEX_REFRESH_TOKEN`

Recommended runtime env:

- `PORT`
- `BETMATE_PUBLIC_HOST`
- `BETMATE_REFRESH_HOST`
- `BETMATE_REFRESH_PORT`

Optional next-hardening env:

- `BETMATE_DATA_DIR`

## Source of truth rules

### Live props

Use live scored output for:

- `Match`
- `Prop`

### History and tracking

Use persistent ledger/history for:

- `BetHistory`
- `Tracking`
- `History`
- results summaries
- weekly profit
- monthly profit

Never reconstruct history from current live props.

## Files Base44 should run

Primary runtime files:

- `code/run_hosted_betmate_edge.sh`
- `code/betmate_edge_refresh_server.py`
- `code/betmate_edge_public_server.py`

Primary scoring files:

- `code/extract_wheelo_today_pack.py`
- `code/score_oddsapi_wheelo_props.py`
- `code/build_walters_summary_html.py`

Primary history/settlement files:

- `code/aflplayerprops_history.py`
- `code/settle_player_props_from_wheelo.py`

Reference parity file:

- `code/base44_port_reference.py`

## State files that must survive deployment

These are the important mutable files:

- `state_seed/aflplayerprops_bet_history.csv`
- `state_seed/afl_match_mapping.csv`
- `state_seed/afl_round_mapping.csv`
- `state_seed/player_prop_settlement.csv`

These should seed the runtime and then be preserved in Base44-controlled persistent storage.

## Go-live definition

Base44 owns the runtime successfully when:

1. Base44 can call its own `/health`
2. Base44 can call its own `/refresh`
3. `Tracking` and `History` show the imported Saints/Hawks results
4. future refreshes do not wipe `BetHistory`
5. Base44 does not rely on any Codex-hosted tunnel URL

## Saints/Hawks verification target

The preserved `St Kilda Saints v Hawthorn Hawks` history must remain visible:

- `34` settled rows
- `21 WIN`
- `10 LOSS`
- `3 PUSH`
- `+6.63u` equal-bet profit
- `+3.266u` actual profit
- `45.4%` actual ROI

## Deployment recommendation

If Base44 can directly run this Python package, deploy this bundle in Base44-managed runtime first.

If Base44 cannot keep durable file state cleanly, then Base44 should:

- still run the Python runtime
- but persist ledger/history into Base44 entities immediately after each refresh

## Reading order

1. `docs/base44_complete_handover_20260529.md`
2. `docs/base44_tracking_history_import_package.md`
3. `docs/base44_hosting_stability_plan_20260529.md`
4. `docs/base44_direct_runtime_transfer_20260529.md`
5. `direct_runtime/docs/README.md`

