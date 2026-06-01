# Base44 Native AFLplayerprops Handoff

## Purpose
This document is the complete handoff for rebuilding the current `AFLplayerprops` / `BetMate Edge` workflow natively inside Base44.

Target outcome:
- Base44 backend functions fetch current AFL odds and Wheelo inputs
- Base44 backend functions reproduce the current Python scoring logic
- Base44 entities store matches, props, refresh runs, history, and tracking state
- Base44 frontend reproduces the current app behavior without HTML parsing, ngrok, or a local Python server

Current Python source of truth:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/score_oddsapi_wheelo_props.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/extract_wheelo_today_pack.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/betmate_edge_refresh_server.py`

Base44 should port these rules directly, not reinterpret them.

---

## 1. Base44 Handoff Note

### Overview
We want Base44 to replace the current live Codex/ngrok refresh path.

Target state:
- Base44 backend fetches fresh AFL events and prop markets from Odds API
- Base44 backend fetches Wheelo inputs
- Base44 backend scores props using the same logic as the current Python agent
- Base44 entities store matches, props, refresh runs, and tracking state
- Base44 frontend renders the same round summary, match tabs, history, and tracking outputs
- No HTML parsing
- No iframe
- No local Python server required once parity is reached

### Data Sources

#### Odds API
Sport key:
- `aussierules_afl`

Region:
- `au`

Markets used:
- `player_disposals`
- `player_tackles_over`
- `player_goals_scored_over`

Also available but intentionally not actionable:
- `player_afl_fantasy_points_over`

#### Wheelo
Wheelo is a set of JSON feeds, not a database.

Current upstream sources:
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json`
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json`
- `https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/2026.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last10.json`
- `https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last5.json`

Wheelo provides:
- season player averages
- last10 player averages
- last5 player averages
- match counts
- base projection inputs for:
  - `Disposals`
  - `Tackles`
  - `Goals`
  - `DreamTeamPoints_Avg`

Fantasy points are currently excluded from actionable display.

### Core Business Logic

#### Market Mapping
- `player_disposals` -> market `Disposals` -> projection field `Disposals`
- `player_tackles_over` -> market `Tackles` -> projection field `Tackles`
- `player_goals_scored_over` -> market `Goals` -> projection field `Goals_Avg`
- `player_afl_fantasy_points_over` -> market `Ranking/Fantasy Pts` -> projection field `DreamTeamPoints_Avg`

#### Actionable Markets Only
Only include these in actionable display:
- `Disposals`
- `Tackles`
- `Goals`

Do not include:
- `Ranking/Fantasy Pts`
- any other unvalidated markets

#### Projection Model
For each prop:
1. Match Odds API player to Wheelo player
2. Get season baseline projection
3. Get last10 projection
4. Get last5 projection
5. Apply Kalman-style recent-form update plus mean reversion
6. Cap projection drift by market

Current market sigmas:
- `Disposals: 5.5`
- `Tackles: 2.1`
- `Goals: 0.85`
- `Ranking/Fantasy Pts: 18.0`

Projection drift caps:
- `Disposals: 4.0`
- `Tackles: 1.0`
- `Goals: 0.6`
- `Ranking/Fantasy Pts: 12.0`

Support thresholds

Strong support:
- `Disposals: 3.0`
- `Tackles: 1.0`
- `Goals: 0.25`
- `Ranking/Fantasy Pts: 8.0`

Lean support:
- `Disposals: 1.0`
- `Tackles: 0.5`
- `Goals: 0.05`
- `Ranking/Fantasy Pts: 3.0`

#### Model Probability
Use the same normal-CDF style logic as Python:
- `z = (line - projection) / sigma`
- `under probability = normal_cdf(z)`
- `over probability = 1 - under probability`
- clamp to `[0.01, 0.99]`

#### Derived Fields
Compute:
- `modelLine`
- `modelProb`
- market implied probability
- `probEdge`
- `evPerUnit`
- support bucket
- `qi`
- signal tier
- stake
- segment

#### Signal Rules
- `A_BET`
  - `qi >= 80`
  - `edge >= 0.04`
  - `support == Model strong support`
- `B_BET`
  - `qi >= 70`
  - `edge >= 0.03`
  - `support in {Model strong support, Model lean support}`
- `LEAN`
  - `qi >= 65`
  - `edge >= 0.02`
- else `PASS`

#### QI
Use the same Python `live_qi` function logic:
- starts from `50`
- adjusted by support bucket
- adjusted by model edge
- adjusted by books-at-line
- adjusted by market type

Display rule:
- show `QI` as a whole number

#### Stake Rules
- `A_BET base = 1.0u`
- `B_BET base = 0.5u`
- `Goals` scaled down
- `Tackles` scaled to `0.8x`
- `Disposals` scaled to `1.0x`
- cap final stake at `1.0u`

#### Segment Rules
Visible rows only:
- `QI >= 80`
- `EV > 0`

Then split into:
- `High Value Props = QI >= 80 and price >= 1.80`
- `Multi Props Only = QI >= 80 and price < 1.80`

### Entity Model

#### RefreshRun
Fields:
- `startedAt`
- `completedAt`
- `status`
- `message`
- `roundLabel`
- `gamesCount`
- `propsCount`
- `source`
- `outputVersion`

#### Match
Fields:
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

#### Prop
Fields:
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

#### AppState
Fields:
- `activeRoundLabel`
- `lastRefreshAt`
- `lastRefreshStatus`
- `lastRefreshMessage`

### Backend Function Structure

Main function:
- `refreshAflPlayerProps`

Recommended module structure:
- `functions/refreshAflPlayerProps.ts`
- `functions/lib/fetchOdds.ts`
- `functions/lib/fetchWheelo.ts`
- `functions/lib/normalize.ts`
- `functions/lib/scoreProps.ts`
- `functions/lib/settleProps.ts`
- `functions/lib/types.ts`

`refreshAflPlayerProps` should:
1. fetch current AFL events from Odds API
2. fetch current prop markets
3. fetch Wheelo JSONs
4. build normalized player inputs
5. score props using Python-parity logic
6. filter to actionable rows
7. split into segments
8. upsert Match records
9. replace/upsert current-round Prop records
10. update settlement/tracking for started or completed games
11. create RefreshRun
12. update AppState
13. return counts and refresh status

### Frontend Behavior

Tabs:
- `Round Summary`
- one tab per match in commence-time order
- `History`
- `Tracking` last

Sections on each match/summary tab:
- `High Value Props`
- `Multi Props Only`

Table columns:
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

Tracking tab:
- started/completed rows only
- separate results summary for:
  - `High Value Props`
  - `Multi Props Only`
- show:
  - `Equal Bet Profit`
  - `Actual Profit`
  - `Actual ROI`
- include total rows

History tab:
- all ledger/history rows
- first two columns:
  - `Date`
  - `Round`
- then same tracking-style structure
- include:
  - weekly profit chart
  - monthly profit chart

### Settlement
Current Codex version now uses official `AFL.com.au` player stats for settlement.
If settlement is ported into Base44, `AFL.com.au` should remain the official source.

### Migration Recommendation

Phase 1:
- scaffold entities
- scaffold fetchers
- scaffold normalization
- render mock/native UI

Phase 2:
- port scoring logic from Python to TypeScript
- compare row-for-row with Python

Phase 3:
- port settlement/tracking logic
- verify results and history parity

Phase 4:
- retire ngrok/local refresh path
- Base44 becomes source of truth for runtime app behavior

Important note:
Do not guess at the scoring model. Port the Python formulas directly.

---

## 2. Python-to-TypeScript Parity Checklist

### Goal
Confirm the new Base44 TypeScript pipeline matches the current Python AFLplayerprops agent closely enough to replace it in production.

### Source of Truth
Python reference files:
- `score_oddsapi_wheelo_props.py`
- `extract_wheelo_today_pack.py`
- `betmate_edge_refresh_server.py`

### Test Principle
For the same slate, same event set, and same odds snapshot:
- Python output and Base44 TypeScript output should match row-for-row on the fields below
- any intentional differences must be documented explicitly

### 1. Input Parity Checks
Before comparing model outputs, confirm both systems are using the same raw inputs.

Check:
- same Odds API sport key: `aussierules_afl`
- same region: `au`
- same markets:
  - `player_disposals`
  - `player_tackles_over`
  - `player_goals_scored_over`
- same event set
- same bookmaker set per event
- same Wheelo source windows:
  - season
  - last10
  - last5

Pass condition:
- same games
- same players
- same market/line/book combinations available before scoring

### 2. Player Matching Parity
Compare player-name matching behavior.

Check:
- exact player matches
- normalized-name matches
- fuzzy fallback matches

Important:
Python currently uses:
- normalized names
- `difflib` close match with cutoff `0.86`

Pass condition:
- no unexpected dropped players
- no incorrect player-to-Wheelo matches
- same matched/unmatched set as Python

### 3. Projection Parity
For every actionable row, compare:
- base season projection
- last10 projection
- last5 projection
- final adjusted projection
- projection delta vs baseline

Pass condition:
- exact match preferred
- acceptable tolerance:
  - projection difference `<= 0.01`

If outside tolerance:
- flag by market and player
- inspect Kalman/reversion math first

### 4. Probability Parity
Compare:
- model probability
- market implied probability
- probability edge

Pass condition:
- model probability difference `<= 0.001`
- market probability difference `<= 0.001`
- probability edge difference `<= 0.001`

If not matched:
- check:
  - sigma values
  - normal CDF implementation
  - no-vig implied probability logic
  - rounding timing

### 5. EV Parity
Compare:
- `ev_per_unit`

Pass condition:
- EV difference `<= 0.001`

### 6. Support Bucket Parity
Compare support labels:
- `Model strong support`
- `Model lean support`
- `Model neutral`
- `Model lean against`
- `Model strong against`

Pass condition:
- exact match for every row

### 7. QI Parity
Compare:
- `live_qi` before display rounding

Pass condition:
- exact match preferred
- acceptable tolerance:
  - QI difference `<= 0.1`

### 8. Signal Parity
Compare:
- `A_BET`
- `B_BET`
- `LEAN`
- `PASS`
- `INFO_ONLY`
- `NO_MATCH`

Pass condition:
- exact match for every row

### 9. Stake Parity
Compare:
- `stake_units`

Pass condition:
- exact match to `0.01`

### 10. Segment Parity
Compare:
- `High Value Props`
- `Multi Props Only`
- excluded rows

Rules to verify:
- visible only if `QI >= 80`
- visible only if `EV > 0`
- `High Value Props` if `price >= 1.80`
- `Multi Props Only` if `price < 1.80`

Pass condition:
- same visible row set
- same segment assignment per visible row

### 11. Match / Entity Parity
Compare Match-level metadata:
- `gameKey`
- `displayName`
- `homeTeam`
- `awayTeam`
- `commenceTime`
- `sortOrder`
- `hasLiveBooks`
- `bookmakersCount`

Pass condition:
- exact match or documented intentional formatting difference

### 12. Prop Identity Parity
Prop key / uniqueness must be stable.

Compare:
- game
- team
- player
- market
- side
- line
- bookie

Pass condition:
- no duplicate rows
- no missing rows
- no accidental merged rows

### 13. Tracking / Status Parity
Compare:
- `UPCOMING`
- `IN_PLAY`
- `COMPLETED`
- `result`
- `actual`

Pass condition:
- same state for the same row at the same point in time

### 14. Settlement Parity
If settlement is ported:
- compare official `AFL.com.au`-based settlement row-for-row

Check:
- `result`
- `actual`
- equal-bet profit
- actual profit

Pass condition:
- exact match on settled rows

### 15. UI Aggregation Parity
Compare summary metrics shown in the app:
- counts by segment
- top QI
- tracking counts
- results summary counts
- equal-bet profit
- actual profit
- actual ROI
- history totals
- weekly profit totals
- monthly profit totals

Pass condition:
- same aggregates as Python-backed report for the same ledger state

### 16. Recommended Test Fixture Workflow
Use a fixed snapshot test first.

Fixture should include:
- saved Wheelo JSONs
- saved Odds API events
- saved Odds API prop files
- saved ledger CSV

Then:
1. run Python
2. export normalized scored rows
3. run Base44 TypeScript against same fixture
4. compare outputs row-for-row

Only after fixture parity:
- test live refresh parity

### 17. Suggested Comparison Output
Create a parity report with:
- total rows compared
- exact matches
- mismatches by category:
  - player matching
  - projection
  - probability
  - EV
  - QI
  - signal
  - stake
  - segment
  - settlement
- top 20 worst deviations

### 18. Tolerances Summary
Recommended acceptable tolerances:
- projection `<= 0.01`
- probability `<= 0.001`
- prob edge `<= 0.001`
- EV `<= 0.001`
- QI `<= 0.1`
- stake exact to `0.01`
- signal exact
- segment exact
- settlement exact

### 19. Blockers That Should Fail Release
Do not cut over if any of these happen:
- different visible bet universe
- different signal tier for live rows
- different stake assignment on visible rows
- incorrect player matching
- fantasy points leaking into actionable display
- incorrect settlement against AFL.com.au
- aggregate profit/ROI totals not matching ledger math

### 20. Definition of Done
Base44 is ready to replace the current Python runtime only when:
- row-level parity is achieved on a fixed fixture
- live refresh parity is confirmed on a current slate
- settlement parity is confirmed on a completed game
- UI aggregates match the Codex report
- no ngrok/local server is needed for production use

---

## 3. TypeScript Module-by-Module Implementation Map

### Overview
This is the file-level translation plan from Python to Base44 TypeScript.

Python source of truth:
- `score_oddsapi_wheelo_props.py`
- `extract_wheelo_today_pack.py`
- `betmate_edge_refresh_server.py`

Base44 target structure:
- `functions/refreshAflPlayerProps.ts`
- `functions/lib/types.ts`
- `functions/lib/constants.ts`
- `functions/lib/fetchOdds.ts`
- `functions/lib/fetchWheelo.ts`
- `functions/lib/playerPack.ts`
- `functions/lib/nameMatching.ts`
- `functions/lib/projections.ts`
- `functions/lib/probability.ts`
- `functions/lib/scoring.ts`
- `functions/lib/portfolio.ts`
- `functions/lib/segments.ts`
- `functions/lib/settlement.ts`
- `functions/lib/persistence.ts`
- `functions/lib/history.ts`

### 1. `functions/refreshAflPlayerProps.ts`
Purpose:
- main orchestration entrypoint

Python equivalent:
- refresh pipeline logic from `betmate_edge_refresh_server.py`
- `score()` from `score_oddsapi_wheelo_props.py`

Responsibilities:
- load secrets
- fetch events
- fetch prop markets
- fetch Wheelo sources
- build player pack
- score props
- split segments
- update matches
- update props
- optionally settle completed games
- write refresh run
- update app state
- return summary payload

### 2. `functions/lib/types.ts`
Purpose:
- shared TypeScript interfaces and enums

Define types for:
- `OddsEvent`
- `OddsBookmaker`
- `OddsMarket`
- `OddsOutcome`
- `WheeloPlayerSeasonRow`
- `WheeloWindowRow`
- `PlayerPackRow`
- `ScoredProp`
- `MatchRecord`
- `RefreshSummary`
- `SupportBucket`
- `SignalTier`
- `SegmentType`
- `PropStatus`
- `PropResult`

### 3. `functions/lib/constants.ts`
Purpose:
- single source of truth for hard-coded model constants

Move into TS:
- `SPORT_KEY = "aussierules_afl"`
- `REGIONS = "au"`
- actionable market list
- market mapping
- market sigmas
- projection drift caps
- support thresholds
- book reliability adjustments
- QI thresholds
- stake rules
- segment thresholds

### 4. `functions/lib/fetchOdds.ts`
Purpose:
- Odds API fetch layer

Responsibilities:
- fetch current AFL events
- fetch event-level player prop markets
- return normalized raw odds payloads

Exports:
- `fetchOddsEvents()`
- `fetchOddsPropsForEvent(eventId)`
- `fetchAllOddsProps(events)`

### 5. `functions/lib/fetchWheelo.ts`
Purpose:
- fetch Wheelo JSON sources

Responsibilities:
- fetch season player stats
- fetch last10 player stats
- fetch last5 player stats
- fetch team stats if needed later

Exports:
- `fetchWheeloPlayerSeason()`
- `fetchWheeloPlayerLast10()`
- `fetchWheeloPlayerLast5()`
- `fetchWheeloInputs()`

### 6. `functions/lib/playerPack.ts`
Purpose:
- build the normalized player projection input set used by scoring

Responsibilities:
- join season/last10/last5 windows
- compute derived fields like `Goals_Avg`
- build one normalized player pack row per player

Exports:
- `buildPlayerPack(wheeloInputs)`

### 7. `functions/lib/nameMatching.ts`
Purpose:
- match Odds API player names to Wheelo player rows

Python equivalent:
- `norm_name(...)`
- `match_player(...)`

Responsibilities:
- normalize names
- exact normalized match
- fallback similarity match
- return matched pack row or null

Exports:
- `normalizePlayerName(name)`
- `matchPlayerToPack(rawPlayer, playerPack)`

### 8. `functions/lib/projections.ts`
Purpose:
- projection math layer

Python equivalent:
- `goal_average(...)`
- `window_stat(...)`
- `kalman_mean_reversion_projection(...)`

Responsibilities:
- compute season baseline
- compute last10 input
- compute last5 input
- apply Kalman-style updates
- apply mean reversion
- cap projection drift

Exports:
- `getBaseProjection(...)`
- `kalmanMeanReversionProjection(...)`
- `buildProjectionForMarket(...)`

### 9. `functions/lib/probability.ts`
Purpose:
- probability model utilities

Python equivalent:
- `normal_cdf(...)`
- `model_probability(...)`

Responsibilities:
- implement normal CDF
- convert projection + line + sigma into model probability
- clamp output

Exports:
- `normalCdf(x)`
- `modelProbability({ market, side, projection, line })`

### 10. `functions/lib/scoring.ts`
Purpose:
- score each raw odds row into a model row

Python equivalent:
- `support_bucket(...)`
- `live_qi(...)`
- `signal(...)`
- `score()`

Responsibilities:
- get projection
- compute support bucket
- compute market implied probability
- compute no-vig market probability if both sides available
- compute model probability
- compute probability edge
- compute EV
- compute QI
- compute signal tier

Exports:
- `scorePropRow(...)`
- `scoreAllProps(...)`

### 11. `functions/lib/portfolio.ts`
Purpose:
- best-risk-adjusted line choice and optional round-wide selection logic

Python equivalent:
- `alt_line_score(...)`
- `apply_alt_line_selection(...)`
- `select_portfolio(...)`

Responsibilities:
- group alternate lines by player/market/side
- score alternates
- mark `BEST_RISK_ADJUSTED`
- optionally compute round-wide selection rank
- apply portfolio caps if still needed

Exports:
- `altLineScore(row)`
- `applyAltLineSelection(rows)`
- `selectPortfolio(rows)`

### 12. `functions/lib/segments.ts`
Purpose:
- visible app segmentation rules

Responsibilities:
- exclude unvalidated markets
- exclude `qi < 80`
- exclude `ev <= 0`
- assign:
  - `High Value Props`
  - `Multi Props Only`

Exports:
- `isActionable(row)`
- `visibleRows(rows)`
- `assignSegment(row)`

### 13. `functions/lib/settlement.ts`
Purpose:
- settlement and status updates

Python equivalent:
- `settle_player_props_from_wheelo.py`
- official AFL.com settlement path

Responsibilities:
- mark `UPCOMING`, `IN_PLAY`, `COMPLETED`
- optionally fetch official AFL.com player stats
- settle completed props
- compute:
  - `result`
  - `actual`
  - equal-bet profit
  - actual profit

Exports:
- `inferStatus(...)`
- `inferResult(...)`
- `settleCompletedProps(...)`
- `buildSettlementRows(...)`

Important:
official settlement source should remain `AFL.com.au`

### 14. `functions/lib/persistence.ts`
Purpose:
- all Base44 entity writes

Responsibilities:
- upsert Match rows
- replace/upsert current-round Prop rows
- create RefreshRun row
- update AppState

Exports:
- `saveMatches(...)`
- `saveProps(...)`
- `createRefreshRun(...)`
- `updateAppState(...)`

### 15. `functions/lib/history.ts`
Purpose:
- history and results-summary aggregation

Responsibilities:
- compute history rows
- compute tracking summaries
- compute weekly profit buckets
- compute monthly profit buckets
- compute equal-bet vs actual profit aggregates

Exports:
- `buildTrackingSummary(...)`
- `buildHistorySummary(...)`
- `buildWeeklyProfitSeries(...)`
- `buildMonthlyProfitSeries(...)`

### 16. Suggested Build Order
1. `types.ts`
2. `constants.ts`
3. `fetchOdds.ts`
4. `fetchWheelo.ts`
5. `playerPack.ts`
6. `nameMatching.ts`
7. `projections.ts`
8. `probability.ts`
9. `scoring.ts`
10. `portfolio.ts`
11. `segments.ts`
12. `persistence.ts`
13. `refreshAflPlayerProps.ts`
14. `settlement.ts`
15. `history.ts`

### 17. Minimum Viable Parity Path
First get:
- fetch parity
- scoring parity
- segment parity

Then:
- persistence parity
- settlement parity
- history parity

### 18. High-Risk Modules
These need the closest row-for-row testing:
- `projections.ts`
- `probability.ts`
- `scoring.ts`
- `portfolio.ts`
- `settlement.ts`

### 19. Low-Risk Modules
Mostly plumbing:
- `types.ts`
- `constants.ts`
- `fetchOdds.ts`
- `fetchWheelo.ts`
- `persistence.ts`

### 20. Final Instruction
Do not redesign the model while porting it.
Port the Python behavior first.
Only optimize or simplify after parity has been demonstrated.
