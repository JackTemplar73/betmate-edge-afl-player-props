# BetMate Edge MacBook Bundle

This bundle is prepared so you can copy it to a MacBook and run the AFL player props agent locally.

## What this bundle includes

- Python refresh server
- public proxy server
- local seeded history/state files
- HTML report builder
- settlement and ledger scripts

It does **not** include secrets.

You will need to provide:

- `THE_ODDS_API_KEY`
- optionally `CODEX_REFRESH_TOKEN` if you want to protect `/refresh`

## Folder structure

- `code/`
  - runnable scripts
- `state_seed/`
  - initial local state
- `docs/`
  - direct runtime notes

## MacBook setup

### 1. Copy the bundle to your MacBook

Recommended destination:

```bash
~/BetMateEdge
```

### 2. Open Terminal and move into the bundle

```bash
cd ~/BetMateEdge
```

### 3. Seed the local state into the runtime folder

```bash
./code/bootstrap_state.sh ./code
```

### 4. Set your Odds API key

Temporary for the current shell:

```bash
export THE_ODDS_API_KEY="YOUR_KEY_HERE"
```

Optional refresh token:

```bash
export CODEX_REFRESH_TOKEN="YOUR_REFRESH_TOKEN_HERE"
```

### 5. Run the local service

```bash
./start_betmate_edge_mac.sh
```

## What starts

This launches:

- refresh server on `127.0.0.1:8765`
- public server on `0.0.0.0:8000`

## Local URLs

Open locally in a browser:

- report:
  - `http://127.0.0.1:8000/afl_player_props_stk_haw_walters_report.html`
- health:
  - `http://127.0.0.1:8000/health`

## Public tunnel

This bundle does **not** auto-start `ngrok`.

If you want a temporary public URL:

```bash
ngrok http 8000
```

Then use the public ngrok URL plus:

- `/refresh`
- `/health`
- `/afl_player_props_stk_haw_walters_report.html`

## Stop the service

Press `Ctrl+C` in the terminal running the bundle.

## Notes

- The runtime is file-stateful.
- Preserve the files in `code/` after seeding, especially:
  - `aflplayerprops_bet_history.csv`
  - `afl_match_mapping.csv`
  - `afl_round_mapping.csv`
  - `player_prop_settlement.csv`

- If you move to a new MacBook later, copy the updated bundle state back out before switching machines.

## Quick verification

After startup, this should work:

```bash
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{"ok": true, "busy": false, "last_success_at": "", "last_error": ""}
```

