# Base44 Complete Handover

## BetMate Edge AFL Player Props

This is the single handover document for Base44 to implement the latest production version of the AFL player props model and UI with minimal ambiguity.

Use this document as the canonical source for:
- live model behavior
- current production filters
- history/tracking import
- verification targets
- implementation order
- parity checks

---

## 1. What Base44 Must Deliver

Base44 should replace the current `Codex + local Python + ngrok` runtime with a native app that:

- fetches current AFL player prop markets from Odds API
- fetches Wheelo inputs
- reproduces the current Python model logic exactly
- stores current live props in a `Prop` entity
- stores full historical bets and performance in a `BetHistory` entity
- renders:
  - `Round Summary`
  - one tab per game
  - `History`
  - `Tracking`
- preserves last night’s settled results, including `St Kilda Saints v Hawthorn Hawks`

This is a production handover, not just a prototype brief.

---

## 2. Current Production Position

The model has been tightened to the sharpest production-safe version currently justified by replay evidence.

### Current production decisions

- Use `A_BET` only for live actionable card construction
- Keep `B_BET` and `LEAN` in the research layer, but do not rely on them for the production card
- Use count-aware probability models for low-count markets
- Keep fantasy points excluded from actionable display
- Keep `BetHistory` separate from `Prop`

### Why

The replay backtest shows:
- the elite `A_BET` layer is strong
- the softer `B_BET` layer is materially weaker
- low-count markets like goals need discrete payout-aware probability handling

---

## 3. Live Model Specification

### Inputs

#### Odds API
- Sport key: `aussierules_afl`
- Region: `au`
- Markets:
  - `player_disposals`
  - `player_tackles_over`
  - `player_goals_scored_over`

Not actionable:
- `player_afl_fantasy_points_over`

#### Wheelo
Sources:
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json`
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json`
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/2026.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last10.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last5.json`

### Projection engine

Per player / market:
1. season baseline
2. last10 input
3. last5 input
4. Kalman-style update
5. mean reversion back toward season baseline
6. market-specific projection drift cap

### Volatility engine

Use dynamic player-level sigma:
- base sigma by market
- adjusted by season vs last10 vs last5 dispersion
- sample-size penalty
- floor/cap by market

### Probability engine

#### Count-aware markets
Use discrete payout-aware probabilities for:
- `Goals`
- `Tackles`
- `Marks`

Rules:
- use `negative_binomial` when variance exceeds mean
- otherwise use `poisson`

This matters because lines like `Over 1.5 goals` are really `2+`, and count distributions must respect that.

#### Higher-count market
For:
- `Disposals`

Use:
- continuity-corrected normal probability

### Market probability

- use no-vig implied probability when both sides are present
- otherwise use raw implied probability

### EV / QI

Compute:
- `model_probability`
- `market_probability`
- `probEdge`
- `evPerUnit`
- `live_qi`

### Signal rules

Signals are market-specific.

#### Disposals
- `A_BET`: `QI >= 80`, `edge >= 0.04`, `Model strong support`
- `B_BET`: `QI >= 74`, `edge >= 0.03`, `Model strong or lean support`
- `LEAN`: `QI >= 68`, `edge >= 0.02`

#### Tackles
- `A_BET`: `QI >= 82`, `edge >= 0.05`, `Model strong support`
- `B_BET`: `QI >= 76`, `edge >= 0.04`, `Model strong or lean support`
- `LEAN`: `QI >= 70`, `edge >= 0.025`

#### Goals
- `A_BET`: `QI >= 85`, `edge >= 0.05`, `Model strong support`
- `B_BET`: disabled in production
- `LEAN`: `QI >= 72`, `edge >= 0.03`

#### Marks
- `A_BET`: `QI >= 88`, `edge >= 0.06`, `Model strong support`
- `B_BET`: disabled in production
- `LEAN`: `QI >= 72`, `edge >= 0.03`

### Stake rules

- `A_BET` base = `1.0u`
- `B_BET` base = `0.5u`
- `Goals` stake-discounted
- `Tackles` = `0.8x`
- `Disposals` = `1.0x`
- cap at `1.0u`

### Portfolio rules

Production card uses:
- `A_BET` only
- best risk-adjusted alternate line only

Caps:
- top portfolio cap
- goal cap
- one bet per player

---

## 4. Why This Is The Current Sharpest Production Version

The model was tightened after replay evidence showed:

- the upgraded probability layer holds up
- `A_BET` is strong
- `B_BET` is where quality leaks out
- `Goals` and other low-count markets required discrete treatment

### Current replay diagnostic

Source:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/wheelo_footywire_backtest_report.md`

Headline:
- `A_BET`: `345` bets, `75.7%` hit rate, `+$70.74`, `28.3% ROI`
- `A/B_BET`: `442` bets, `71.9%` hit rate, `+$67.01`, `22.6% ROI`

Notable market observations:
- `Tackles A_BET`: very strong
- `Goals A_BET`: strong
- `Disposals A_BET`: strong
- `B_BET`: weaker, especially in the old fringe layer

### Important caveat

This is a replay diagnostic, not pure archived-snapshot walk-forward.

It is strong enough to justify the production tightening above, but not enough to claim institutional proof yet.

---

## 5. Required Base44 Entity Model

### `RefreshRun`
- `startedAt`
- `completedAt`
- `status`
- `message`
- `roundLabel`
- `gamesCount`
- `propsCount`
- `source`
- `outputVersion`

### `Match`
- `gameKey`
- `roundLabel`
- `commenceTime`
- `homeTeam`
- `awayTeam`
- `displayName`
- `sortOrder`
- `hasLiveBooks`
- `bookmakersCount`
- `refreshRun`

### `Prop`
- `propKey`
- `roundLabel`
- `gameKey`
- `commenceTime`
- `team`
- `player`
- `market`
- `side`
- `modelLine`
- `marketLine`
- `modelProb`
- `marketProb`
- `probEdge`
- `evPerUnit`
- `price`
- `bookie`
- `qi`
- `stake`
- `support`
- `signal`
- `segment`
- `status`
- `result`
- `actual`
- `sourceSelection`
- `refreshRun`

### `BetHistory`
- `betId`
- `status`
- `createdAtUtc`
- `updatedAtUtc`
- `roundNumber`
- `game`
- `commenceTime`
- `player`
- `market`
- `side`
- `line`
- `book`
- `betPrice`
- `stakeUnits`
- `signal`
- `projection`
- `modelProbability`
- `marketProbability`
- `modelEdge`
- `evPerUnit`
- `qi`
- `altLineScore`
- `markovPath`
- `bookMarketReliability`
- `portfolioSelection`
- `openLine`
- `openPrice`
- `latestLine`
- `latestPrice`
- `closeLine`
- `closePrice`
- `clvPriceDecimal`
- `clvImpliedPoints`
- `lineClv`
- `clvStatus`
- `actual`
- `result`
- `flatProfit`
- `stakeProfit`

### `AppState`
- `activeRoundLabel`
- `lastRefreshAt`
- `lastRefreshStatus`
- `lastRefreshMessage`

---

## 6. Absolute Source Of Truth Rules

Use:
- `Prop` for current live/current-round state
- `BetHistory` for all tracking, settlement, and history

Do **not**:
- build `Tracking` from `Prop`
- build `History` from `Prop`
- wipe `BetHistory` during refresh

If Base44 violates this, Saints/Hawks and other settled results will disappear from the app even though the ledger still exists.

---

## 7. Files Base44 Must Use

### Primary code references
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/score_oddsapi_wheelo_props.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/extract_wheelo_today_pack.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/wheelo_footywire_backtest.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_port_reference.py`

### Base44 package references
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/code/score_oddsapi_wheelo_props.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/code/base44_port_reference.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/code/wheelo_footywire_backtest.py`

### History import files
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_bet_history_import.csv`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_bet_history_import.json`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_tracking_summary.json`

### Current rendered outputs
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/artifacts/afl_player_props_walters_report.html`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/artifacts/afl_player_props_stk_haw_walters_report.html`

### Final bundle
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package_20260529_sharpest_model.zip`

---

## 8. Backend Functions Base44 Must Implement

### `refreshAflPlayerProps`

Responsibilities:
1. fetch Odds API events
2. fetch player prop markets
3. fetch Wheelo sources
4. normalize players and games
5. compute projections
6. compute dynamic sigma
7. compute count-aware or continuity-corrected probability by market
8. compute EV / QI / signal / stake
9. keep only current live/current-round `Prop` rows
10. update `Match`
11. update `RefreshRun`
12. update `AppState`

### `importBetHistory`

Responsibilities:
1. load the exported ledger
2. upsert into `BetHistory` by `betId`
3. preserve all settled rows
4. preserve Saints/Hawks

### `syncBetHistory`

Responsibilities:
1. read latest exported ledger rows
2. upsert changed rows by `betId`
3. update:
   - `status`
   - `actual`
   - `result`
   - CLV fields
   - `flatProfit`
   - `stakeProfit`
4. never delete prior history rows

---

## 9. Frontend Rules

### Top-level tabs
- `Round Summary`
- one tab per match in game start order
- `History`
- `Tracking` last

### Columns
Use this table order everywhere:
- `QI`
- `Team`
- `Player`
- `Market`
- `Side`
- `Model Line`
- `Market Line`
- `Model Prob`
- `Price`
- `Bookie`
- `Prob Edge`
- `Stake`

### Filtering

Visible current props only if:
- `QI >= 80`
- `EV > 0`

Segments:
- `High Value Props` if `price >= 1.80`
- `Multi Props Only` if `price < 1.80`

### Tracking

Tracking must read from `BetHistory`.

### History

History must read from `BetHistory`.

---

## 10. Verification Targets

### Current history import totals

From:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_tracking_summary.json`

Overall:
- `rowCount`: `178`
- `settledCount`: `44`
- `WIN`: `27`
- `LOSS`: `14`
- `PUSH`: `3`
- `Equal Bet Profit`: `7.45`
- `Actual Profit`: `4.131`
- `Total Staked`: `12.25`
- `Actual ROI`: `33.7%`

### Saints/Hawks must survive

Game:
- `St Kilda Saints v Hawthorn Hawks`

Required:
- `rowCount`: `34`
- `settledCount`: `34`
- `WIN`: `21`
- `LOSS`: `10`
- `PUSH`: `3`
- `Equal Bet Profit`: `6.63`
- `Actual Profit`: `3.266`
- `Total Staked`: `7.2`
- `Actual ROI`: `45.4%`

If Base44 does not show these exact Saints/Hawks totals, the migration is not complete.

---

## 11. Recommended Implementation Order

### Phase 1: Data foundation
1. create entities
2. wire secrets
3. build Odds API fetchers
4. build Wheelo fetchers

### Phase 2: Model parity
1. port player matching
2. port Kalman-style projection
3. port dynamic sigma
4. port count-aware probability engine
5. port QI / signal / stake logic

### Phase 3: Current live app
1. build `refreshAflPlayerProps`
2. write `Match`
3. write `Prop`
4. render round summary and match tabs

### Phase 4: History/tracking migration
1. create `BetHistory`
2. import history CSV
3. verify Saints/Hawks
4. wire `Tracking` and `History` to `BetHistory`

### Phase 5: Final parity checks
1. compare current props against Python outputs
2. compare history totals against exported summary
3. compare HTML artifacts against Base44 UI behavior

---

## 12. Definition Of Done

Base44 is not done until all of the following are true:

- current live props match the upgraded production scorer
- low-count markets use count-aware probabilities
- actionable card reflects `A_BET` only production logic
- `BetHistory` is imported
- Saints/Hawks appears in both `Tracking` and `History`
- overall history totals match the exported summary
- refreshes do not wipe historical tracking

---

## 13. Short Instruction To Base44

If a shorter summary is needed, use this:

> Implement the current Python model exactly as packaged in `base44_handoff_package_20260529_sharpest_model.zip`. The live card is now `A_BET` only, with count-aware probabilities for `Goals`, `Tackles`, and `Marks`, and continuity-corrected normal for `Disposals`. Import `base44_bet_history_import.csv` into a separate `BetHistory` entity keyed by `betId`, and drive `Tracking` and `History` from `BetHistory`, not `Prop`. Verify that `St Kilda Saints v Hawthorn Hawks` shows 34 settled rows, 21-10-3, +6.63 equal-bet profit, +3.266 actual profit, and 45.4% actual ROI.
