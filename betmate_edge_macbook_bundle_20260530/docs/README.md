# Base44 Direct Runtime Bundle

This folder is the minimal runnable bundle for Base44 to execute the AFL player props agent directly.

## Structure

- `code/`
  - runtime scripts
  - Dockerfile
  - startup script
- `state_seed/`
  - initial mutable state files that should be copied into persistent storage before first run

## Start command

From the bundle root:

```bash
./code/bootstrap_state.sh ./code
./code/run_hosted_betmate_edge.sh
```

Or with Docker:

```bash
docker build -t betmate-edge-runtime ./code
docker run -p 8000:8000 \
  -e THE_ODDS_API_KEY=... \
  -e CODEX_REFRESH_TOKEN=... \
  betmate-edge-runtime
```

## HTTP endpoints

- `GET /health`
- `POST /refresh`

## Required secrets

- `THE_ODDS_API_KEY`
- `CODEX_REFRESH_TOKEN`

## Required persistence rule

Before first production run, seed persistent storage with the contents of `state_seed/`.

At minimum preserve:

- `aflplayerprops_bet_history.csv`
- `afl_match_mapping.csv`
- `afl_round_mapping.csv`
- `player_prop_settlement.csv`

You can seed the runtime directory with:

```bash
./code/bootstrap_state.sh ./code
```

## Important

If Base44 uses entities for `BetHistory`, the ledger should still be imported first from:

- `state_seed/aflplayerprops_bet_history.csv`

Do not start with an empty history.
