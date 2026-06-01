# Base44 Transfer Packet

## BetMate Edge AFL Player Props

This document is the transfer-ready package for rebuilding the current `AFLplayerprops` / `BetMate Edge` workflow natively inside Base44.

It is designed to give Base44:
- the architecture and build intent
- the important model rules
- the exact Python scoring helpers that must be ported for parity

Primary source files in the current Codex workspace:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/score_oddsapi_wheelo_props.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/extract_wheelo_today_pack.py`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/betmate_edge_refresh_server.py`

Supporting reference docs already prepared:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_native_aflplayerprops_handoff.md`
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_port_reference.py`

---

## 1. What Base44 Is Building

Base44 should replace the current live `Codex + ngrok + local Python server` setup.

Target state:
- Base44 backend functions fetch current AFL events and player props from Odds API
- Base44 backend functions fetch Wheelo player/team inputs
- Base44 backend functions reproduce the current Python scoring logic
- Base44 entities store matches, props, refresh runs, tracking state, and history
- Base44 frontend renders the current app behavior natively
- no HTML parsing
- no iframe dependency
- no local refresh server in production

This is a true rewrite, not just a connector.

---

## 2. Current Runtime Inputs

### Odds API
Sport key:
- `aussierules_afl`

Region:
- `au`

Markets currently used:
- `player_disposals`
- `player_tackles_over`
- `player_goals_scored_over`

Also available upstream but intentionally not actionable:
- `player_afl_fantasy_points_over`

### Wheelo
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
- player match counts
- projection inputs for:
  - `Disposals`
  - `Tackles`
  - `Goals`
  - `DreamTeamPoints_Avg`

Fantasy points are excluded from actionable display.

---

## 3. High-Level Model Rules

### Market mapping
- `player_disposals` -> `Disposals`
- `player_tackles_over` -> `Tackles`
- `player_goals_scored_over` -> `Goals`
- `player_afl_fantasy_points_over` -> `Ranking/Fantasy Pts`

### Actionable markets
Only:
- `Disposals`
- `Tackles`
- `Goals`

Exclude:
- `Ranking/Fantasy Pts`
- other unvalidated markets

### Visibility rules
Visible rows only if:
- `QI >= 80`
- `EV > 0`

Segments:
- `High Value Props` if `price >= 1.80`
- `Multi Props Only` if `price < 1.80`

### Key scoring flow
1. Match Odds API player to Wheelo player
2. Pull season baseline projection
3. Pull last10 projection
4. Pull last5 projection
5. Apply Kalman-style recent-form update plus mean reversion
6. Apply dynamic player-level sigma
7. Compute model probability
   - `Goals`, `Tackles`, and `Marks` now use count-aware discrete probabilities
   - `Goals/Tackles/Marks` use `negative_binomial` when variance exceeds mean, otherwise `poisson`
   - `Disposals` use continuity-corrected normal probability
8. Compare with market implied probability
9. Compute:
   - `probEdge`
   - `EV`
   - `QI`
   - `signal`
   - `stake`
10. Split into `High Value Props` and `Multi Props Only`

---

## 4. Base44 Entity Model

### Important
Base44 should not start with an empty tracking/history state.

The existing historical ledger must be imported from:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/aflplayerprops_bet_history.csv`

Round mapping for historical rows currently lives in:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/afl_round_mapping.csv`

### RefreshRun
- `startedAt`
- `completedAt`
- `status`
- `message`
- `roundLabel`
- `gamesCount`
- `propsCount`
- `source`
- `outputVersion`

### Match
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

### Prop
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

### BetHistory
Add this as a separate Base44 entity so full historical tracking and settlement are preserved independently from the current live `Prop` table.

Fields:
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

### AppState
- `activeRoundLabel`
- `lastRefreshAt`
- `lastRefreshStatus`
- `lastRefreshMessage`

---

## 5. Base44 Backend Structure

Recommended TypeScript layout:

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

Main backend function:
- `refreshAflPlayerProps`

It should:
1. fetch events
2. fetch player props
3. fetch Wheelo sources
4. build player pack
5. score props
6. split actionable segments
7. save Match rows
8. save Prop rows
9. update settlement/tracking
10. write RefreshRun
11. update AppState
12. return summary counts

### Additional History Functions
Base44 also needs a one-time history import path and an ongoing history sync path.

Recommended functions:
- `importAflPlayerPropsHistory`
- `syncAflPlayerPropsHistory`

`importAflPlayerPropsHistory` should:
1. read the historical ledger export
2. map `roundNumber` using `afl_round_mapping.csv`
3. upsert all rows into `BetHistory`
4. preserve `betId` as the stable unique key

`syncAflPlayerPropsHistory` should:
1. run after every refresh
2. write any new or updated ledger rows into `BetHistory`
3. update result, CLV, actual, equal-bet profit, and actual profit fields if settlement changed

---

## 6. Frontend Structure

Tabs:
- `Round Summary`
- one tab per match in commence-time order
- `History`
- `Tracking` last

Sections:
- `High Value Props`
- `Multi Props Only`

Standard columns:
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
- metrics:
  - `Equal Bet Profit`
  - `Actual Profit`
  - `Actual ROI`
- total row on each summary table

History tab:
- all `BetHistory` rows
- `Date` first column
- `Round` second column
- then tracking-style fields
- weekly profit chart
- monthly profit chart

---

## 7. Parity Rule

Do not redesign the model on the first pass.

Base44 should first achieve row-for-row parity against Python for:
- player matching
- projection
- dynamic sigma
- model probability
- market probability
- probability edge
- EV
- QI
- signal
- stake
- segment
- settlement
- history / tracking rows

Only optimize after parity is demonstrated.

---

## 8. Immediate Base44 Requirements

Base44 secrets needed:
- `THE_ODDS_API_KEY`

Recommended build order:
1. fetchers
2. player pack
3. scoring helpers
4. persistence
5. one-time `BetHistory` import
6. settlement/history sync

### Historical Data Transfer Requirement
Base44 must ingest the existing tracking/history ledger before the app goes live.

Primary source:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/aflplayerprops_bet_history.csv`

Round mapping source:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/afl_round_mapping.csv`

Current ledger columns:
- `bet_id`
- `status`
- `created_at_utc`
- `updated_at_utc`
- `game`
- `commence_time`
- `player`
- `market`
- `side`
- `line`
- `book`
- `bet_price`
- `stake_units`
- `signal`
- `projection`
- `model_probability`
- `market_probability`
- `model_edge`
- `ev_per_unit`
- `live_qi`
- `alt_line_score`
- `markov_path`
- `book_market_reliability`
- `portfolio_selection`
- `open_line`
- `open_price`
- `latest_line`
- `latest_price`
- `close_line`
- `close_price`
- `clv_price_decimal`
- `clv_implied_points`
- `line_clv`
- `clv_status`
- `actual`
- `result`
- `flat_profit`
- `stake_profit`

Round number is currently attached by joining ledger rows to:
- `afl_round_mapping.csv`

### Migration Rule
Do not derive history from current `Prop` rows only.

Use:
- `Prop` for current live/current-round state
- `BetHistory` for the full historical ledger and tracking record

This matters because settled results, CLV, and prior-round tracking must survive even when the live `Prop` table is replaced on refresh.

---

## 9. Exact Python Port Reference

Below is the exact minimal Python scoring reference Base44 should port directly into TypeScript.

```python
#!/usr/bin/env python3
"""Minimal Python reference for Base44 parity porting.

This file isolates the exact scoring helpers that Base44 needs to port from the
full AFL player props scorer.
"""

from __future__ import annotations

import math
from typing import Any


MARKET_SIGMA = {
    "Disposals": 5.5,
    "Marks": 2.2,
    "Tackles": 2.1,
    "Ranking/Fantasy Pts": 18.0,
    "Goals": 0.85,
}

MARKET_SIGMA_FLOOR = {
    "Disposals": 4.0,
    "Marks": 1.6,
    "Tackles": 1.5,
    "Ranking/Fantasy Pts": 12.0,
    "Goals": 0.65,
}

MARKET_SIGMA_CAP = {
    "Disposals": 8.5,
    "Marks": 3.4,
    "Tackles": 3.2,
    "Ranking/Fantasy Pts": 28.0,
    "Goals": 1.45,
}

PROJECTION_DRIFT_CAP = {
    "Disposals": 4.0,
    "Marks": 1.5,
    "Tackles": 1.0,
    "Ranking/Fantasy Pts": 12.0,
    "Goals": 0.6,
}

BOOK_MARKET_RELIABILITY = {
    ("PointsBet (AU)", "Goals"): 0.92,
    ("PointsBet (AU)", "Disposals"): 0.98,
    ("TAB", "Tackles"): 1.04,
    ("TABtouch", "Tackles"): 1.04,
    ("Neds", "Disposals"): 1.01,
    ("SportsBet", "Disposals"): 0.99,
}

SUPPORT_STRONG = {
    "Disposals": 3.0,
    "Marks": 1.0,
    "Tackles": 1.0,
    "Ranking/Fantasy Pts": 8.0,
    "Goals": 0.25,
}

SUPPORT_LEAN = {
    "Disposals": 1.0,
    "Marks": 0.5,
    "Tackles": 0.5,
    "Ranking/Fantasy Pts": 3.0,
    "Goals": 0.05,
}


def to_float(value: Any) -> float | None:
    if value in ("", "NA", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def dynamic_sigma(
    market: str,
    season_projection: float | None,
    season_matches: float | None,
    last10_projection: float | None,
    last10_matches: float | None,
    last5_projection: float | None,
    last5_matches: float | None,
) -> float:
    base = MARKET_SIGMA[market]
    floor = MARKET_SIGMA_FLOOR[market]
    cap = MARKET_SIGMA_CAP[market]

    anchors = [value for value in (season_projection, last10_projection, last5_projection) if value is not None]
    if not anchors:
        return base

    center = season_projection if season_projection is not None else sum(anchors) / len(anchors)
    recent_weights = [
        (last10_projection, max(0.0, min(1.0, (last10_matches or 0.0) / 10.0)), 0.8),
        (last5_projection, max(0.0, min(1.0, (last5_matches or 0.0) / 5.0)), 1.1),
    ]
    weighted_deviation = 0.0
    total_weight = 0.0
    for projection, sample_weight, recency_weight in recent_weights:
        if projection is None:
            continue
        weight = max(0.25, sample_weight) * recency_weight
        weighted_deviation += abs(projection - center) * weight
        total_weight += weight
    dispersion = weighted_deviation / total_weight if total_weight else 0.0

    season_sample = season_matches or 0.0
    sample_penalty = max(0.0, 10.0 - season_sample) / 10.0
    sigma = base + 0.35 * dispersion + 0.12 * base * sample_penalty
    return round(max(floor, min(cap, sigma)), 3)


def model_probability(bucket: str, side: str, projection: float | None, line: float, sigma: float | None = None) -> float | None:
    if projection is None:
        return None
    sigma = sigma or MARKET_SIGMA[bucket]
    z = (line - projection) / sigma
    under = normal_cdf(z)
    prob = under if side == "Under" else 1.0 - under
    return max(0.01, min(0.99, prob))


def support_bucket(bucket: str, side: str, projection: float | None, line: float) -> tuple[str, float | None]:
    if projection is None:
        return "No Model data match", None
    edge = line - projection if side == "Under" else projection - line
    strong = SUPPORT_STRONG[bucket]
    lean = SUPPORT_LEAN[bucket]
    if edge >= strong:
        return "Model strong support", edge
    if edge >= lean:
        return "Model lean support", edge
    if edge > -lean:
        return "Model neutral", edge
    if edge > -strong:
        return "Model lean against", edge
    return "Model strong against", edge


def live_qi(bucket: str, model_edge: float | None, support: str, matched: bool, books_at_line: int) -> float:
    if model_edge is None or not matched:
        return 0.0
    score = 50.0
    score += {
        "Model strong support": 18,
        "Model lean support": 10,
        "Model neutral": 2,
        "Model lean against": -10,
        "Model strong against": -18,
    }.get(support, 0)
    score += min(18.0, max(-18.0, model_edge * 100.0))
    score += min(6.0, books_at_line * 1.5)
    score += {"Disposals": 6, "Tackles": 4, "Goals": 3, "Ranking/Fantasy Pts": -4}.get(bucket, 0)
    return round(max(0.0, min(99.0, score)), 1)


def reliability_multiplier(book: str, market: str) -> float:
    return BOOK_MARKET_RELIABILITY.get((book, market), 1.0)


def kalman_mean_reversion_projection(
    market: str,
    season_projection: float | None,
    season_matches: float | None,
    last10_projection: float | None,
    last10_matches: float | None,
    last5_projection: float | None,
    last5_matches: float | None,
) -> float | None:
    if season_projection is None:
        return None

    sigma = dynamic_sigma(
        market,
        season_projection,
        season_matches,
        last10_projection,
        last10_matches,
        last5_projection,
        last5_matches,
    )
    state = season_projection
    variance = sigma ** 2 * 1.5

    updates = [
        (last10_projection, last10_matches, 10.0),
        (last5_projection, last5_matches, 5.0),
    ]
    for measurement, matches, window_size in updates:
        if measurement is None:
            continue
        sample = max(1.0, min(window_size, matches or window_size))
        measurement_variance = sigma ** 2 * (window_size / sample)
        gain = variance / (variance + measurement_variance)
        state = state + gain * (measurement - state)
        variance = max(sigma ** 2 * 0.15, (1.0 - gain) * variance)

    match_count = season_matches or 0.0
    reversion_strength = min(0.30, 0.10 + max(0.0, 8.0 - match_count) * 0.02)
    state = season_projection + (state - season_projection) * (1.0 - reversion_strength)

    cap = PROJECTION_DRIFT_CAP[market]
    state = max(season_projection - cap, min(season_projection + cap, state))
    return round(state, 3)


def signal(bucket: str, edge: float | None, qi: float, support: str) -> str:
    if bucket == "Ranking/Fantasy Pts":
        return "INFO_ONLY"
    if edge is None:
        return "NO_MATCH"
    if qi >= 80 and edge >= 0.04 and support == "Model strong support":
        return "A_BET"
    if qi >= 70 and edge >= 0.03 and support in {"Model strong support", "Model lean support"}:
        return "B_BET"
    if qi >= 65 and edge >= 0.02:
        return "LEAN"
    return "PASS"


def alt_line_score(row: dict[str, Any]) -> float:
    prob = float(row["model_probability"] or 0)
    ev = float(row["ev_per_unit"] or -1)
    qi = float(row["live_qi"] or 0) / 100.0
    market = str(row["market"])
    if ev <= 0 or prob <= 0:
        return -999.0
    stability = prob ** 0.75
    if market == "Goals":
        stability *= 0.82
    elif market == "Tackles":
        stability *= 0.92
    elif market == "Disposals":
        stability *= 1.04
    reliability = reliability_multiplier(str(row.get("book", "")), market)
    return round(ev * stability * qi * reliability, 5)


def stake_units(row: dict[str, Any]) -> float:
    signal_name = str(row.get("signal"))
    market = str(row.get("market"))
    qi = float(row.get("live_qi") or 0)
    ev = float(row.get("ev_per_unit") or 0)

    if signal_name == "A_BET":
        base = 1.0
    elif signal_name == "B_BET":
        base = 0.5
    else:
        return 0.0

    if market == "Goals":
        base *= 0.5
        if qi < 90 or ev < 0.15:
            base *= 0.5
    elif market == "Tackles":
        base *= 0.8
    elif market == "Disposals":
        base *= 1.0

    return round(max(0.0, min(1.0, base)), 2)
```

---

## 10. Final Instruction to Base44

Port the Python behavior first.
Do not simplify the scoring or volatility logic during the first implementation pass.
Only optimize after parity is demonstrated.
Import the full existing ledger before go-live.
Keep `BetHistory` as the source of truth for History and Tracking views.
Do not reconstruct historical tracking from current `Prop` snapshots only.
