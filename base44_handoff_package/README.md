# Base44 Handoff Package

This package is the curated handoff bundle for rebuilding and operating the AFL player props workflow in Base44.

## What is included

- `docs/`
  - Base44 handoff specifications
  - current bettor-facing reports and settlement notes
- `code/`
  - current Python scoring, refresh, history, settlement, and report-generation logic
  - the focused Base44 parity reference
- `fixtures/`
  - latest sample Odds API and Wheelo inputs
  - latest scored outputs and portfolio selections
- `exports/`
  - Base44-ready history import files
  - current tracking/performance summary, including settled Saints v Hawthorn results
- `artifacts/`
  - rendered HTML/PDF outputs useful for UI parity checks

## Suggested reading order

1. `docs/base44_complete_handover_20260529.md`
2. `docs/base44_direct_runtime_transfer_20260529.md`
3. `docs/base44_ui_parity_transfer_20260529.md`
4. `direct_runtime/docs/README.md`
5. `docs/base44_hosting_stability_plan_20260529.md`
6. `docs/base44_tracking_history_import_package.md`
7. `docs/base44_native_aflplayerprops_handoff.md`
8. `docs/base44_betmate_edge_full_build_spec.md`
9. `code/base44_port_reference.py`
10. `code/betmate_edge_refresh_server.py`
11. `code/score_oddsapi_wheelo_props.py`

## Important notes

- This bundle intentionally excludes secrets and local-only tokens.
- `codex_refresh_token.txt` is not included.
- `__pycache__/` content is not included.
- The included fixture files reflect the current workspace state as of 2026-05-29 AEST.
- `code/Dockerfile` and `code/run_hosted_betmate_edge.sh` are included to make hosted deployment easier.
- `direct_runtime/` is the self-contained Base44 execution bundle for running the Python agent without Codex as the live runtime owner.
- The current scorer now uses count-aware probability models for low-count markets:
  - `Goals`, `Tackles`, and `Marks` use `negative_binomial` or `poisson`
  - `Disposals` use continuity-corrected normal probability
- Import `exports/base44_bet_history_import.csv` or `exports/base44_bet_history_import.json` into Base44 `BetHistory` before go-live so existing tracking/performance is preserved.
- `exports/base44_tracking_summary.json` is the quick verification file for current performance totals.

## Handoff goal

Base44 should be able to use this package to:

- understand the product and data model
- reproduce scoring and portfolio logic
- ingest current structured outputs
- compare Base44 behavior against current Python outputs
