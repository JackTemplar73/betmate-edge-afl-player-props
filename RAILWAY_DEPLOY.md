# Railway Deploy

This service is ready to deploy to Railway using the included:

- [Dockerfile](/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/Dockerfile)
- [railway.json](/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/railway.json)
- [run_hosted_betmate_edge.sh](/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/run_hosted_betmate_edge.sh)
- [bootstrap_railway_state.sh](/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/bootstrap_railway_state.sh)

## What this does

- runs the refresh server on internal `127.0.0.1:8765`
- runs the public proxy on Railway `PORT`
- serves:
  - `GET /health`
  - `POST /refresh`
  - static report HTML
- persists mutable state through a Railway volume mounted at `/data`

## Railway setup

1. Create a new Railway project from this folder/repo.
2. Add a volume mounted at:
   - `/data`
3. Add these secrets/environment variables:
   - `THE_ODDS_API_KEY`
   - `CODEX_REFRESH_TOKEN`
4. Deploy.

## Recommended secrets

- `THE_ODDS_API_KEY`
  - your live Odds API key
- `CODEX_REFRESH_TOKEN`
  - bearer token used by `/refresh`

## Optional env vars

- `BETMATE_STATE_DIR=/data`
- `BETMATE_REFRESH_HOST=127.0.0.1`
- `BETMATE_REFRESH_PORT=8765`
- `BETMATE_PUBLIC_HOST=0.0.0.0`

`PORT` is supplied by Railway automatically.

## Health checks

Railway health check path:

- `/health`

## After deploy

Verify:

- `https://<your-railway-domain>/health`
- `https://<your-railway-domain>/afl_player_props_stk_haw_walters_report.html`

Then use Base44:

- `CODEX_REFRESH_URL=https://<your-railway-domain>/refresh`
- `CODEX_REFRESH_TOKEN=<same raw token>`

## Persistence notes

The bootstrap script moves/symlinks mutable files into `/data`, including:

- `aflplayerprops_bet_history.csv`
- `afl_match_mapping.csv`
- `afl_round_mapping.csv`
- `player_prop_settlement.csv`
- `wheelo_snapshots/`
- `official_afl_stats_json/`
- generated report/state files

That keeps history and generated outputs alive across restarts.

## Limitation

This workspace does not currently have Railway CLI/auth configured, so the final account-side deploy click still has to happen in Railway unless you provide Railway credentials/tooling on this machine.
