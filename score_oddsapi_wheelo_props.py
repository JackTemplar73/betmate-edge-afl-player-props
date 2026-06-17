#!/usr/bin/env python3
"""Score live Odds API AFL player props against model projections."""

from __future__ import annotations

import csv
from datetime import datetime
import difflib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
LOCAL_TZ = ZoneInfo("Australia/Melbourne")
WHEELO_PLAYERS = ROOT / "wheelo_today_player_pack.csv"
EVENTS_JSON = ROOT / "oddsapi_events.json"
HISTORY_LEDGER = ROOT / "aflplayerprops_bet_history.csv"

MARKET_MAP = {
    "player_disposals": ("Disposals", "Disposals", True),
    "player_tackles_over": ("Tackles", "Tackles", False),
    "player_goals_scored_over": ("Goals", "Goals_Avg", False),
    "player_afl_fantasy_points_over": ("Ranking/Fantasy Pts", "DreamTeamPoints_Avg", False),
}
COUNT_AWARE_MARKETS = {"Goals", "Tackles", "Marks"}
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
PORTFOLIO_MAX_BETS = 10
PORTFOLIO_MAX_GOALS = 3
PORTFOLIO_MAX_PER_PLAYER = 1
PORTFOLIO_MAX_PER_GAME = 3
PREMIUM_MIN_QI = 90
PREMIUM_MIN_EDGE = 0.08
PREMIUM_MIN_EV = 0.12
PREMIUM_MIN_PRICE = 1.80
PREMIUM_MIN_SCORE = 7.0
PREMIUM_GOALS_MIN_QI = 90
PREMIUM_GOALS_MIN_EDGE = 0.18
PREMIUM_GOALS_MIN_PRICE = 3.00
PREMIUM_DISPOSALS_UNDER_MIN_QI = 92
PREMIUM_DISPOSALS_UNDER_MIN_EDGE = 0.14
PREMIUM_DISPOSALS_UNDER_MIN_EV = 0.14
PREMIUM_PRICE_DEAD_ZONE = (2.0, 2.49)
CALIBRATION_PRIOR_WEIGHT = 8.0
CALIBRATION_MIN_SAMPLE = 8
CALIBRATION_MAX_BLEND = 0.35
ROI_PENALTY_SAMPLE = 12
ROI_PENALTY_CUTOFF = -0.10
ROI_BONUS_CUTOFF = 0.08

# Walters-style tiny Bayesian nudges from the first settlement. These are not
# bans or promotions; they are conservative priors that need more samples.
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
SIGNAL_THRESHOLDS = {
    "Disposals": {
        "A": {"min_qi": 80, "min_edge": 0.04, "supports": {"Model strong support"}},
        "B": {"min_qi": 74, "min_edge": 0.03, "supports": {"Model strong support", "Model lean support"}},
        "LEAN": {"min_qi": 68, "min_edge": 0.02},
    },
    "Tackles": {
        "A": {"min_qi": 82, "min_edge": 0.05, "supports": {"Model strong support"}},
        "B": {"min_qi": 76, "min_edge": 0.04, "supports": {"Model strong support", "Model lean support"}},
        "LEAN": {"min_qi": 70, "min_edge": 0.025},
    },
    "Goals": {
        "A": {"min_qi": 85, "min_edge": 0.05, "supports": {"Model strong support"}},
        "B": {"min_qi": 999, "min_edge": 999.0, "supports": set()},
        "LEAN": {"min_qi": 72, "min_edge": 0.03},
    },
    "Marks": {
        "A": {"min_qi": 88, "min_edge": 0.06, "supports": {"Model strong support"}},
        "B": {"min_qi": 999, "min_edge": 999.0, "supports": set()},
        "LEAN": {"min_qi": 72, "min_edge": 0.03},
    },
}


def price_band(price: float) -> str:
    if price < 1.50:
        return "lt_1_50"
    if price < 1.80:
        return "1_50_1_79"
    if price < 2.00:
        return "1_80_1_99"
    if price < 2.50:
        return "2_00_2_49"
    return "2_50_plus"


def qi_band(qi: float) -> str:
    if qi < 85:
        return "80_84"
    if qi < 90:
        return "85_89"
    if qi < 95:
        return "90_94"
    return "95_plus"


def blend_probability(model_prob: float, market_prob: float, empirical_prob: float, blend: float) -> float:
    posterior = (1.0 - blend) * model_prob + blend * empirical_prob
    posterior = 0.9 * posterior + 0.1 * market_prob
    return max(0.01, min(0.99, posterior))


def historical_segment_keys(row: dict[str, Any], price: float, qi: float) -> list[tuple[str, str]]:
    market = str(row.get("market") or "")
    side = str(row.get("side") or "")
    book = str(row.get("book") or "")
    return [
        ("market_side_price", f"{market}|{side}|{price_band(price)}"),
        ("market_side", f"{market}|{side}"),
        ("qi_band", qi_band(qi)),
        ("book_market", f"{book}|{market}"),
    ]


def load_history_calibration() -> dict[tuple[str, str], dict[str, float]]:
    if not HISTORY_LEDGER.exists():
        return {}
    with HISTORY_LEDGER.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    stats: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"wins": 0.0, "losses": 0.0, "stake": 0.0, "profit": 0.0, "market_prob_sum": 0.0})
    for row in rows:
        if row.get("status") != "SETTLED":
            continue
        result = str(row.get("result") or "")
        if result not in {"WIN", "LOSS"}:
            continue
        price = to_float(row.get("bet_price")) or 0.0
        qi = to_float(row.get("live_qi")) or 0.0
        market_prob = to_float(row.get("market_probability")) or (1.0 / price if price > 1.0 else 0.5)
        profit = to_float(row.get("stake_profit")) or 0.0
        stake = to_float(row.get("stake_units")) or 0.0
        for key in historical_segment_keys(row, price, qi):
            segment = stats[key]
            if result == "WIN":
                segment["wins"] += 1.0
            else:
                segment["losses"] += 1.0
            segment["stake"] += stake
            segment["profit"] += profit
            segment["market_prob_sum"] += market_prob
    return stats


def calibration_metrics(
    row: dict[str, Any],
    history_stats: dict[tuple[str, str], dict[str, float]],
    model_prob: float,
    market_prob: float,
    price: float,
    qi: float,
) -> dict[str, Any]:
    contributions = []
    roi_penalty = 0.0
    roi_bonus = 0.0
    notes: list[str] = []
    effective_weight = 0.0
    weighted_empirical = 0.0

    for key in historical_segment_keys(row, price, qi):
        segment = history_stats.get(key)
        if not segment:
            continue
        n = segment["wins"] + segment["losses"]
        if n < CALIBRATION_MIN_SAMPLE:
            continue
        avg_market_prob = segment["market_prob_sum"] / n if n else market_prob
        posterior = (segment["wins"] + CALIBRATION_PRIOR_WEIGHT * avg_market_prob) / (n + CALIBRATION_PRIOR_WEIGHT)
        weight = min(n, 40.0)
        weighted_empirical += posterior * weight
        effective_weight += weight
        roi = segment["profit"] / segment["stake"] if segment["stake"] else 0.0
        contributions.append((key[0], key[1], n, posterior, roi))
        if roi <= ROI_PENALTY_CUTOFF and n >= ROI_PENALTY_SAMPLE:
            roi_penalty += min(0.10, abs(roi) * 0.25)
            notes.append(f"{key[0]}_roi_drag")
        elif roi >= ROI_BONUS_CUTOFF and n >= ROI_PENALTY_SAMPLE:
            roi_bonus += min(0.05, roi * 0.15)
            notes.append(f"{key[0]}_roi_tailwind")

    if effective_weight > 0:
        empirical_prob = weighted_empirical / effective_weight
        blend = min(CALIBRATION_MAX_BLEND, 0.12 + effective_weight / 200.0)
    else:
        empirical_prob = market_prob
        blend = 0.0

    posterior_prob = blend_probability(model_prob, market_prob, empirical_prob, blend)
    posterior_prob = max(0.01, min(0.99, posterior_prob - roi_penalty + roi_bonus))
    return {
        "posterior_probability": round(posterior_prob, 6),
        "posterior_edge": round(posterior_prob - market_prob, 6),
        "posterior_ev_per_unit": round(posterior_prob * price - 1.0, 6),
        "calibration_blend": round(blend, 4),
        "historical_roi_penalty": round(roi_penalty, 4),
        "historical_roi_bonus": round(roi_bonus, 4),
        "historical_samples": int(effective_weight),
        "calibration_note": ", ".join(notes[:4]),
    }


def latest_snapshot_dir() -> Path:
    base = ROOT / "wheelo_snapshots"
    candidates = sorted(
        path for path in base.iterdir()
        if path.is_dir() and (path / "wheelo_player_stats_2026.json").exists()
    )
    if not candidates:
        raise RuntimeError(f"No model-data snapshot directories found in {base}")
    return candidates[-1]


def upcoming_events() -> list[dict[str, Any]]:
    if not EVENTS_JSON.exists():
        return []
    today = datetime.now(LOCAL_TZ).date()
    events = json.loads(EVENTS_JSON.read_text())

    def is_upcoming_local(event: dict[str, Any]) -> bool:
        commence = str(event.get("commence_time", "")).strip()
        if not commence:
            return False
        try:
            dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
        except ValueError:
            return False
        return dt.astimezone(LOCAL_TZ).date() >= today

    return sorted(
        [event for event in events if is_upcoming_local(event)],
        key=lambda event: event.get("commence_time", ""),
    )


def upcoming_event_ids() -> set[str]:
    return {str(event.get("id")) for event in upcoming_events() if event.get("id")}


def odds_files() -> list[Path]:
    target_ids = upcoming_event_ids()
    files = []
    for path in sorted(ROOT.glob("oddsapi_*_props.json")):
        if "marks_probe" in path.name:
            continue
        try:
            event = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        event_id = str(event.get("id", ""))
        commence_raw = str(event.get("commence_time", "")).strip()
        if target_ids:
            if event_id in target_ids:
                files.append(path)
        elif commence_raw:
            try:
                commence_dt = datetime.fromisoformat(commence_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if commence_dt.astimezone(LOCAL_TZ).date() >= datetime.now(LOCAL_TZ).date():
                files.append(path)
    return files


def to_float(value: Any) -> float | None:
    if value in ("", "NA", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def norm_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum() or ch.isspace()).replace("nicholas", "nick").strip()


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def poisson_cdf(k: int, mean: float) -> float:
    if k < 0:
        return 0.0
    mean = max(1e-9, mean)
    pmf = math.exp(-mean)
    total = pmf
    for x in range(1, k + 1):
        pmf *= mean / x
        total += pmf
    return max(0.0, min(1.0, total))


def negbin_cdf(k: int, mean: float, variance: float) -> float:
    if k < 0:
        return 0.0
    mean = max(1e-9, mean)
    variance = max(mean + 1e-9, variance)
    shape = (mean ** 2) / max(1e-9, variance - mean)
    success_prob = shape / (shape + mean)
    pmf = success_prob ** shape
    total = pmf
    for x in range(1, k + 1):
        pmf *= ((x - 1 + shape) / x) * (1.0 - success_prob)
        total += pmf
    return max(0.0, min(1.0, total))


def count_probability(bucket: str, side: str, projection: float, line: float, sigma: float) -> tuple[float, str]:
    threshold = int(math.floor(line))
    variance = max(0.01, sigma ** 2)
    mean = max(0.01, projection)

    if bucket == "Disposals":
        z = (line - projection) / sigma
        under = normal_cdf(z)
        prob = under if side == "Under" else 1.0 - under
        return max(0.01, min(0.99, prob)), "normal_cc"

    if variance > mean + 1e-6:
        under = negbin_cdf(threshold, mean, variance)
        model = "negative_binomial"
    else:
        under = poisson_cdf(threshold, mean)
        model = "poisson"
    prob = under if side == "Under" else 1.0 - under
    return max(0.01, min(0.99, prob)), model


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


def model_probability(bucket: str, side: str, projection: float | None, line: float, sigma: float | None = None) -> tuple[float | None, str]:
    if projection is None:
        return None, "no_projection"
    sigma = sigma or MARKET_SIGMA[bucket]
    if bucket in COUNT_AWARE_MARKETS or bucket == "Disposals":
        prob, model = count_probability(bucket, side, projection, line, sigma)
        return prob, model
    z = (line - projection) / sigma
    under = normal_cdf(z)
    prob = under if side == "Under" else 1.0 - under
    return max(0.01, min(0.99, prob)), "normal"


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


def goal_average(total: Any, matches: Any) -> float | None:
    total_value = to_float(total)
    match_count = to_float(matches)
    if total_value is None or not match_count:
        return None
    return total_value / match_count


def window_stat(payload: dict[str, Any], idx: int, projection_field: str) -> float | None:
    if projection_field == "Goals_Avg":
        return goal_average(payload.get("Goals_Total", [None])[idx], payload.get("Matches", [None])[idx])
    values = payload.get(projection_field, [])
    if idx >= len(values):
        return None
    return to_float(values[idx])


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


def thorp_allocation(row: dict[str, Any]) -> dict[str, Any]:
    signal = str(row.get("signal"))
    market = str(row.get("market"))
    qi = float(row.get("live_qi") or 0)
    price = float(row.get("best_price") or 0)
    prob = float(row.get("posterior_probability") or row.get("model_probability") or 0)
    ev = float(row.get("posterior_ev_per_unit") or row.get("ev_per_unit") or 0)

    if signal not in {"A_BET", "B_BET"} or price <= 1 or prob <= 0 or ev <= 0:
        return {
            "stake_units": 0.0,
            "full_kelly_pct": 0.0,
            "bankroll_pct": 0.0,
            "kelly_fraction": 0.0,
            "allocation_note": "No Thorp allocation: no positive executable edge.",
        }

    net_odds = price - 1.0
    full_kelly = max(0.0, ((net_odds * prob) - (1.0 - prob)) / net_odds)

    if signal == "A_BET":
        kelly_fraction = 0.25 if qi >= 90 else 0.1875
    elif signal == "B_BET":
        kelly_fraction = 0.125

    single_bet_cap_pct = 2.0 if qi >= 90 else 1.25 if qi >= 80 else 0.75

    if market == "Goals":
        kelly_fraction *= 0.5
        single_bet_cap_pct = min(single_bet_cap_pct, 0.75)
        if qi < 90 or ev < 0.15:
            kelly_fraction *= 0.5
    elif market == "Tackles":
        kelly_fraction *= 0.8
        single_bet_cap_pct = min(single_bet_cap_pct, 1.25)
    elif market == "Disposals":
        kelly_fraction *= 1.0

    reliability = float(row.get("book_market_reliability") or reliability_multiplier(str(row.get("book", "")), market))
    kelly_fraction *= max(0.70, min(1.05, reliability))
    kelly_fraction *= max(0.60, 1.0 - float(row.get("historical_roi_penalty") or 0))
    bankroll_pct = min(single_bet_cap_pct, full_kelly * kelly_fraction * 100.0)
    stake_unit = min(1.0, bankroll_pct)
    return {
        "stake_units": round(max(0.0, stake_unit), 2),
        "full_kelly_pct": round(full_kelly * 100.0, 2),
        "bankroll_pct": round(max(0.0, bankroll_pct), 2),
        "kelly_fraction": round(kelly_fraction, 4),
        "allocation_note": (
            f"Thorp fractional Kelly: full Kelly {full_kelly * 100.0:.2f}% bankroll, "
            f"{kelly_fraction:.2f}x fraction, capped at {single_bet_cap_pct:.2f}%."
        ),
    }

def stake_units(row: dict[str, Any]) -> float:
    return float(thorp_allocation(row)["stake_units"])


def load_wheelo_rows() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    snapshot_dir = latest_snapshot_dir()
    season_stats = json.loads((snapshot_dir / "wheelo_player_stats_2026.json").read_text())["Data"]
    last10_stats = json.loads((snapshot_dir / "wheelo_player_stats_last10.json").read_text())["Data"]
    last5_stats = json.loads((snapshot_dir / "wheelo_player_stats_last5.json").read_text())["Data"]
    rows: dict[str, dict[str, Any]] = {}
    with WHEELO_PLAYERS.open() as f:
        for row in csv.DictReader(f):
            rows[norm_name(row["Player"])] = row

    last10_idx = {norm_name(player): idx for idx, player in enumerate(last10_stats["Player"])}
    last5_idx = {norm_name(player): idx for idx, player in enumerate(last5_stats["Player"])}

    for idx, player in enumerate(season_stats["Player"]):
        key = norm_name(player)
        if key in rows:
            rows[key]["DreamTeamPoints_Avg"] = season_stats.get("DreamTeamPoints_Avg", [None])[idx]
            rows[key]["Season_Matches"] = season_stats.get("Matches", [None])[idx]
            for projection_field in {field for _, field, _ in MARKET_MAP.values()}:
                rows[key][f"Season_{projection_field}"] = window_stat(season_stats, idx, projection_field)

            idx10 = last10_idx.get(key)
            if idx10 is not None:
                rows[key]["Last10_Matches"] = last10_stats.get("Matches", [None])[idx10]
                for projection_field in {field for _, field, _ in MARKET_MAP.values()}:
                    rows[key][f"Last10_{projection_field}"] = window_stat(last10_stats, idx10, projection_field)

            idx5 = last5_idx.get(key)
            if idx5 is not None:
                rows[key]["Last5_Matches"] = last5_stats.get("Matches", [None])[idx5]
                for projection_field in {field for _, field, _ in MARKET_MAP.values()}:
                    rows[key][f"Last5_{projection_field}"] = window_stat(last5_stats, idx5, projection_field)

    aliases = {key: row["Player"] for key, row in rows.items()}
    return rows, aliases


def match_player(raw: str, rows: dict[str, dict[str, Any]], aliases: dict[str, str]) -> tuple[str | None, dict[str, Any] | None]:
    key = norm_name(raw)
    if key in rows:
        return aliases[key], rows[key]
    close = difflib.get_close_matches(key, rows.keys(), n=1, cutoff=0.86)
    if close:
        return aliases[close[0]], rows[close[0]]
    return None, None


def collect_prices(bookmakers: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, float], list[dict[str, Any]]]:
    prices: dict[tuple[str, str, str, str, float], list[dict[str, Any]]] = defaultdict(list)
    for book in bookmakers:
        for market in book.get("markets", []):
            if market["key"] not in MARKET_MAP:
                continue
            bucket, _, _ = MARKET_MAP[market["key"]]
            for outcome in market.get("outcomes", []):
                side = outcome.get("name", "Over")
                if side not in {"Over", "Under"}:
                    continue
                player = outcome.get("description") or outcome.get("name")
                line = to_float(outcome.get("point"))
                price = to_float(outcome.get("price"))
                if not player or line is None or price is None:
                    continue
                prices[(market["key"], bucket, player, side, line)].append(
                    {"book": book["title"], "book_key": book["key"], "price": price}
                )
    return prices


def no_vig_lookup(prices: dict[tuple[str, str, str, str, float], list[dict[str, Any]]]) -> dict[tuple[str, str, str, float, str], float]:
    out: dict[tuple[str, str, str, float, str], float] = {}
    grouped: dict[tuple[str, str, str, float, str], dict[str, float]] = defaultdict(dict)
    for (market_key, bucket, player, side, line), offers in prices.items():
        for offer in offers:
            grouped[(market_key, bucket, player, line, offer["book"])][side] = offer["price"]
    for (market_key, bucket, player, line, book), sides in grouped.items():
        if "Over" in sides and "Under" in sides:
            over_imp = 1 / sides["Over"]
            under_imp = 1 / sides["Under"]
            denom = over_imp + under_imp
            out[(market_key, player, "Over", line, book)] = over_imp / denom
            out[(market_key, player, "Under", line, book)] = under_imp / denom
    return out


def score() -> list[dict[str, Any]]:
    rows, aliases = load_wheelo_rows()
    history_stats = load_history_calibration()
    scored: list[dict[str, Any]] = []
    for odds_path in odds_files():
        event = json.loads(odds_path.read_text())
        prices = collect_prices(event.get("bookmakers", []))
        no_vig = no_vig_lookup(prices)
        for (market_key, bucket, raw_player, side, line), offers in prices.items():
            best = max(offers, key=lambda item: item["price"])
            player, wheelo = match_player(raw_player, rows, aliases)
            _, projection_field, _ = MARKET_MAP[market_key]
            base_projection = to_float(wheelo.get(f"Season_{projection_field}") if wheelo else None)
            if base_projection is None and wheelo:
                base_projection = to_float(wheelo.get(projection_field))
            projection = kalman_mean_reversion_projection(
                bucket,
                base_projection,
                to_float(wheelo.get("Season_Matches")) if wheelo else None,
                to_float(wheelo.get(f"Last10_{projection_field}")) if wheelo else None,
                to_float(wheelo.get("Last10_Matches")) if wheelo else None,
                to_float(wheelo.get(f"Last5_{projection_field}")) if wheelo else None,
                to_float(wheelo.get("Last5_Matches")) if wheelo else None,
            ) if wheelo else None
            sigma = dynamic_sigma(
                bucket,
                base_projection,
                to_float(wheelo.get("Season_Matches")) if wheelo else None,
                to_float(wheelo.get(f"Last10_{projection_field}")) if wheelo else None,
                to_float(wheelo.get("Last10_Matches")) if wheelo else None,
                to_float(wheelo.get(f"Last5_{projection_field}")) if wheelo else None,
                to_float(wheelo.get("Last5_Matches")) if wheelo else None,
            ) if wheelo else MARKET_SIGMA[bucket]
            prob, probability_model = model_probability(bucket, side, projection, line, sigma)
            support, stat_gap = support_bucket(bucket, side, projection, line)
            raw_implied = 1 / best["price"]
            nv = no_vig.get((market_key, raw_player, side, line, best["book"]))
            implied = nv if nv is not None else raw_implied
            edge = None if prob is None else prob - implied
            ev = None if prob is None else prob * best["price"] - 1
            qi = live_qi(bucket, edge, support, wheelo is not None, len(offers))
            calibration = {}
            if prob is not None:
                calibration = calibration_metrics(
                    {
                        "market": bucket,
                        "side": side,
                        "book": best["book"],
                    },
                    history_stats,
                    prob,
                    implied,
                    float(best["price"]),
                    qi,
                )
            posterior_prob = calibration.get("posterior_probability", prob)
            posterior_edge = calibration.get("posterior_edge", edge)
            posterior_ev = calibration.get("posterior_ev_per_unit", ev)
            scored.append(
                {
                    "game": f"{event.get('home_team')} v {event.get('away_team')}",
                    "commence_time": event.get("commence_time"),
                    "market_key": market_key,
                    "market": bucket,
                    "player": player or raw_player,
                    "raw_player": raw_player,
                    "side": side,
                    "line": line,
                    "best_price": best["price"],
                    "book": best["book"],
                    "books_at_line": len(offers),
                    "projection": projection,
                    "base_projection": base_projection,
                    "projection_delta": None if projection is None or base_projection is None else round(projection - base_projection, 3),
                    "dynamic_sigma": sigma,
                    "probability_model": probability_model,
                    "season_matches": wheelo.get("Season_Matches", "") if wheelo else "",
                    "last10_projection": wheelo.get(f"Last10_{projection_field}", "") if wheelo else "",
                    "last10_matches": wheelo.get("Last10_Matches", "") if wheelo else "",
                    "last5_projection": wheelo.get(f"Last5_{projection_field}", "") if wheelo else "",
                    "last5_matches": wheelo.get("Last5_Matches", "") if wheelo else "",
                    "wheelo_support": support,
                    "stat_gap": stat_gap,
                    "model_probability": prob,
                    "market_probability": implied,
                    "model_edge": edge,
                    "ev_per_unit": ev,
                    "posterior_probability": posterior_prob,
                    "posterior_edge": posterior_edge,
                    "posterior_ev_per_unit": posterior_ev,
                    "calibration_blend": calibration.get("calibration_blend", 0.0),
                    "historical_roi_penalty": calibration.get("historical_roi_penalty", 0.0),
                    "historical_roi_bonus": calibration.get("historical_roi_bonus", 0.0),
                    "historical_samples": calibration.get("historical_samples", 0),
                    "calibration_note": calibration.get("calibration_note", ""),
                    "live_qi": qi,
                    "matched_wheelo": wheelo is not None,
                    "signal": signal(bucket, posterior_edge, qi, support),
                }
            )
    return scored


def signal(bucket: str, edge: float | None, qi: float, support: str) -> str:
    if bucket == "Ranking/Fantasy Pts":
        return "INFO_ONLY"
    if edge is None:
        return "NO_MATCH"
    config = SIGNAL_THRESHOLDS.get(bucket, SIGNAL_THRESHOLDS["Disposals"])
    a_rule = config["A"]
    b_rule = config["B"]
    lean_rule = config["LEAN"]
    if qi >= a_rule["min_qi"] and edge >= a_rule["min_edge"] and support in a_rule["supports"]:
        return "A_BET"
    if qi >= b_rule["min_qi"] and edge >= b_rule["min_edge"] and support in b_rule["supports"]:
        return "B_BET"
    if qi >= lean_rule["min_qi"] and edge >= lean_rule["min_edge"]:
        return "LEAN"
    return "PASS"


def alt_line_score(row: dict[str, Any]) -> float:
    prob = float(row.get("posterior_probability") or row["model_probability"] or 0)
    ev = float(row.get("posterior_ev_per_unit") or row["ev_per_unit"] or -1)
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


def apply_alt_line_selection(scored: list[dict[str, Any]]) -> None:
    actionable = {"A_BET", "B_BET", "LEAN"}
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        if row["signal"] in actionable and row["matched_wheelo"] and row["market"] != "Ranking/Fantasy Pts":
            row["alt_line_score"] = alt_line_score(row)
            groups[(row["player"], row["market"], row["side"])].append(row)
        else:
            row["alt_line_score"] = ""
            row["line_selection"] = "NOT_ACTIONABLE"
            row["ladder_note"] = ""
        row["book_market_reliability"] = "" if not row.get("book") else reliability_multiplier(str(row.get("book")), str(row.get("market")))
        row["stake_units"] = 0.0
        row["thorp_full_kelly_pct"] = 0.0
        row["thorp_bankroll_pct"] = 0.0
        row["thorp_kelly_fraction"] = 0.0
        row["thorp_allocation_note"] = "No Thorp allocation: not selected."
        row["portfolio_selection"] = "NOT_SELECTED"
        row["selection_rank"] = ""
        row["why_not_selected"] = ""
        row["premium_score"] = ""
        row["premium_rule_note"] = ""

    def signal_priority(row: dict[str, Any]) -> int:
        signal = str(row.get("signal", ""))
        if signal == "A_BET":
            return 2
        if signal == "B_BET":
            return 1
        if signal == "LEAN":
            return 0
        return -1

    for _, rows in groups.items():
        rows.sort(
            key=lambda row: (
                signal_priority(row),
                float(row["alt_line_score"]),
                float(row.get("posterior_ev_per_unit") or row["ev_per_unit"] or 0),
                float(row["live_qi"] or 0),
            ),
            reverse=True,
        )
        best = rows[0]
        positive = [row for row in rows if float(row.get("posterior_ev_per_unit") or row["ev_per_unit"] or 0) >= 0.03]
        for row in rows:
            if row is best:
                row["line_selection"] = "BEST_RISK_ADJUSTED"
            elif float(row.get("posterior_ev_per_unit") or row["ev_per_unit"] or 0) >= 0.03:
                row["line_selection"] = "LADDER_OPTION"
            else:
                row["line_selection"] = "DUPLICATE_SUPPRESSED"
            if len(positive) > 1:
                row["ladder_note"] = "; ".join(
                    f"{r['side']} {r['line']} @ {r['best_price']} EV {100 * float(r.get('posterior_ev_per_unit') or r['ev_per_unit']):.1f}%"
                    for r in positive[:4]
                )
            else:
                row["ladder_note"] = ""

    select_portfolio(scored)


def select_portfolio(scored: list[dict[str, Any]]) -> None:
    def premium_rule_failure(row: dict[str, Any]) -> str:
        qi = float(row.get("live_qi") or 0)
        price = float(row.get("best_price") or 0)
        edge = float(row.get("posterior_edge") or row.get("model_edge") or 0)
        ev = float(row.get("posterior_ev_per_unit") or row.get("ev_per_unit") or 0)
        market = str(row.get("market") or "")
        side = str(row.get("side") or "")
        support = str(row.get("wheelo_support") or "")
        if "strong" not in support.lower():
            return "Premium rule: requires strong model support."
        if price < PREMIUM_MIN_PRICE:
            return f"Premium rule: price below {PREMIUM_MIN_PRICE:.2f}."
        if edge < PREMIUM_MIN_EDGE:
            return f"Premium rule: probability edge below {PREMIUM_MIN_EDGE * 100:.0f}%."
        if ev < PREMIUM_MIN_EV:
            return f"Premium rule: EV below {PREMIUM_MIN_EV * 100:.0f}%."
        if qi < PREMIUM_MIN_QI:
            return f"Premium rule: QI below {PREMIUM_MIN_QI}."
        if PREMIUM_PRICE_DEAD_ZONE[0] <= price <= PREMIUM_PRICE_DEAD_ZONE[1] and market != "Tackles":
            return f"Premium rule: avoid {PREMIUM_PRICE_DEAD_ZONE[0]:.2f}-{PREMIUM_PRICE_DEAD_ZONE[1]:.2f} dead-zone prices."
        if market == "Goals":
            if qi < PREMIUM_GOALS_MIN_QI:
                return f"Premium rule: goals require QI {PREMIUM_GOALS_MIN_QI}+."
            if price < PREMIUM_GOALS_MIN_PRICE:
                return f"Premium rule: goals require price {PREMIUM_GOALS_MIN_PRICE:.2f}+."
            if edge < PREMIUM_GOALS_MIN_EDGE:
                return f"Premium rule: goals require {PREMIUM_GOALS_MIN_EDGE * 100:.0f}%+ probability edge."
        if market == "Disposals" and side == "Under":
            if qi < PREMIUM_DISPOSALS_UNDER_MIN_QI:
                return f"Premium rule: disposals unders require QI {PREMIUM_DISPOSALS_UNDER_MIN_QI}+."
            if edge < PREMIUM_DISPOSALS_UNDER_MIN_EDGE:
                return f"Premium rule: disposals unders require {PREMIUM_DISPOSALS_UNDER_MIN_EDGE * 100:.0f}%+ probability edge."
            if ev < PREMIUM_DISPOSALS_UNDER_MIN_EV:
                return f"Premium rule: disposals unders require {PREMIUM_DISPOSALS_UNDER_MIN_EV * 100:.0f}%+ EV."
        return ""

    def premium_selection_score(row: dict[str, Any]) -> tuple[float, list[str]]:
        qi = float(row.get("live_qi") or 0)
        edge = float(row.get("posterior_edge") or row.get("model_edge") or 0)
        ev = float(row.get("posterior_ev_per_unit") or row.get("ev_per_unit") or 0)
        price = float(row.get("best_price") or 0)
        market = str(row.get("market") or "")
        side = str(row.get("side") or "")
        books_at_line = int(float(row.get("books_at_line") or 0))
        projection_delta = float(row.get("projection_delta") or 0)
        reliability = float(row.get("book_market_reliability") or 1.0)
        roi_penalty = float(row.get("historical_roi_penalty") or 0)
        roi_bonus = float(row.get("historical_roi_bonus") or 0)

        score = 0.0
        notes: list[str] = []

        # Historical results have been strongest in the 90-94 band. 95+ is still
        # playable, but it no longer gets an automatic extra bump.
        if 90 <= qi < 95:
            score += 2.5
            notes.append("sweet_spot_qi")
        elif qi >= 95:
            score += 2.0
            notes.append("elite_qi")

        if edge >= 0.18:
            score += 2.0
            notes.append("major_edge")
        elif edge >= 0.12:
            score += 1.5
            notes.append("clean_edge")
        else:
            score += 1.0
            notes.append("pass_edge_gate")

        if ev >= 0.35:
            score += 1.5
            notes.append("large_ev")
        elif ev >= 0.20:
            score += 1.0
            notes.append("good_ev")
        else:
            score += 0.5
            notes.append("pass_ev_gate")

        # Best realised return has been in the 1.80-1.99 band, not the mid-range.
        if 1.80 <= price < 2.00:
            score += 1.5
            notes.append("best_price_band")
        elif 2.50 <= price < 8.0:
            score += 0.75
            notes.append("long_price_compensation")
        elif 2.00 <= price < 2.50:
            score -= 1.25
            notes.append("mid_price_drag")

        if books_at_line >= 3:
            score += 1.0
            notes.append("multi_book_confirm")
        elif books_at_line >= 2:
            score += 0.5
            notes.append("two_book_confirm")

        if projection_delta > 0.12:
            score += 0.5
            notes.append("form_tailwind")
        elif projection_delta < -0.20:
            score -= 0.5
            notes.append("form_headwind")

        if reliability >= 1.02:
            score += 0.5
            notes.append("reliable_book_market")
        elif reliability <= 0.95:
            score -= 0.25
            notes.append("lower_reliability_market")
        if roi_penalty > 0:
            score -= min(1.5, roi_penalty * 12.0)
            notes.append("historical_roi_drag")
        if roi_bonus > 0:
            score += min(0.5, roi_bonus * 8.0)
            notes.append("historical_roi_tailwind")

        if market == "Goals":
            score -= 1.25
            notes.append("goals_variance_penalty")
            if price >= 3.0:
                score += 1.0
                notes.append("goal_price_compensation")
            elif price >= PREMIUM_GOALS_MIN_PRICE:
                score += 0.5
                notes.append("goal_price_paid")
        elif market == "Tackles":
            score += 1.0
            notes.append("tackle_market_bonus")
        elif market == "Disposals" and side == "Over":
            score += 1.25
            notes.append("disposals_over_bonus")
        elif market == "Disposals" and side == "Under":
            score -= 1.0
            notes.append("disposals_under_penalty")

        return round(score, 2), notes

    candidates = [
        row for row in scored
        if row.get("line_selection") == "BEST_RISK_ADJUSTED"
        and row.get("signal") == "A_BET"
        and float(row.get("alt_line_score") or -999) > 0
        and not premium_rule_failure(row)
    ]
    qualified = []
    for row in candidates:
        premium_score, score_notes = premium_selection_score(row)
        row["premium_score"] = premium_score
        row["premium_rule_note"] = ", ".join(score_notes)
        if premium_score >= PREMIUM_MIN_SCORE:
            qualified.append(row)
        else:
            row["portfolio_selection"] = "SUPPRESSED_PREMIUM_RULE"
            row["why_not_selected"] = f"Premium score {premium_score:.2f} below {PREMIUM_MIN_SCORE:.2f}."
    candidates = qualified
    candidates.sort(
        key=lambda row: (
            float(row.get("premium_score") or 0),
            float(row.get("alt_line_score") or 0),
            float(row.get("posterior_ev_per_unit") or row.get("ev_per_unit") or 0),
            float(row.get("live_qi") or 0),
        ),
        reverse=True,
    )
    for idx, row in enumerate(candidates, start=1):
        row["selection_rank"] = str(idx)
    chosen = []
    player_count: dict[str, int] = defaultdict(int)
    game_count: dict[str, int] = defaultdict(int)
    goal_count = 0
    for row in candidates:
        if player_count[str(row["player"])] >= PORTFOLIO_MAX_PER_PLAYER:
            row["portfolio_selection"] = "SUPPRESSED_PLAYER_CAP"
            row["why_not_selected"] = "Player cap: better line for same player ranked ahead."
            continue
        if row["market"] == "Goals" and goal_count >= PORTFOLIO_MAX_GOALS:
            row["portfolio_selection"] = "SUPPRESSED_GOAL_CAP"
            row["why_not_selected"] = "Goal cap: top 3 goal props already taken."
            continue
        if game_count[str(row["game"])] >= PORTFOLIO_MAX_PER_GAME:
            row["portfolio_selection"] = "SUPPRESSED_GAME_CAP"
            row["why_not_selected"] = "Game cap: too much same-game concentration."
            continue
        if len(chosen) >= PORTFOLIO_MAX_BETS:
            row["portfolio_selection"] = "SUPPRESSED_PORTFOLIO_CAP"
            row["why_not_selected"] = "Outside top 10 overall by premium score and alt-line ranking."
            continue
        row["portfolio_selection"] = "PORTFOLIO_BET"
        row["why_not_selected"] = ""
        allocation = thorp_allocation(row)
        row["stake_units"] = allocation["stake_units"]
        row["thorp_full_kelly_pct"] = allocation["full_kelly_pct"]
        row["thorp_bankroll_pct"] = allocation["bankroll_pct"]
        row["thorp_kelly_fraction"] = allocation["kelly_fraction"]
        row["thorp_allocation_note"] = allocation["allocation_note"]
        chosen.append(row)
        player_count[str(row["player"])] += 1
        game_count[str(row["game"])] += 1
        if row["market"] == "Goals":
            goal_count += 1

    for row in scored:
        if row.get("portfolio_selection") == "NOT_SELECTED":
            row["premium_score"] = row.get("premium_score", "")
            row["premium_rule_note"] = row.get("premium_rule_note", "")
            if row.get("line_selection") == "BEST_RISK_ADJUSTED" and row.get("signal") == "A_BET":
                premium_failure = premium_rule_failure(row)
                if premium_failure:
                    row["why_not_selected"] = premium_failure
                    row["portfolio_selection"] = "SUPPRESSED_PREMIUM_RULE"
                else:
                    premium_score, score_notes = premium_selection_score(row)
                    row["premium_score"] = premium_score
                    row["premium_rule_note"] = ", ".join(score_notes)
                    if premium_score < PREMIUM_MIN_SCORE:
                        row["why_not_selected"] = f"Premium score {premium_score:.2f} below {PREMIUM_MIN_SCORE:.2f}."
                        row["portfolio_selection"] = "SUPPRESSED_PREMIUM_RULE"
                    else:
                        row["why_not_selected"] = "Outside top 10 overall by premium score and alt-line ranking."
                        row["portfolio_selection"] = "SUPPRESSED_PORTFOLIO_CAP"
            elif row.get("line_selection") == "LADDER_OPTION":
                row["why_not_selected"] = "Alternate ladder line; better risk-adjusted version kept."
            elif row.get("line_selection") == "DUPLICATE_SUPPRESSED":
                row["why_not_selected"] = "Duplicate or thin alternate line suppressed."
            elif row.get("signal") == "LEAN":
                row["why_not_selected"] = "Lean only: positive angle but not strong enough for portfolio."


def fmt(value: Any, digits: int = 1) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}"


def write_outputs(scored: list[dict[str, Any]]) -> None:
    apply_alt_line_selection(scored)
    fields = [
        "game",
        "commence_time",
        "market",
        "player",
        "side",
        "line",
        "best_price",
        "book",
        "books_at_line",
        "projection",
        "base_projection",
        "projection_delta",
        "dynamic_sigma",
        "probability_model",
        "season_matches",
        "last10_projection",
        "last10_matches",
        "last5_projection",
        "last5_matches",
        "wheelo_support",
        "stat_gap",
        "model_probability",
        "market_probability",
        "model_edge",
        "ev_per_unit",
        "posterior_probability",
        "posterior_edge",
        "posterior_ev_per_unit",
        "calibration_blend",
        "historical_roi_penalty",
        "historical_roi_bonus",
        "historical_samples",
        "calibration_note",
        "live_qi",
        "signal",
        "alt_line_score",
        "book_market_reliability",
        "stake_units",
        "thorp_full_kelly_pct",
        "thorp_bankroll_pct",
        "thorp_kelly_fraction",
        "thorp_allocation_note",
        "portfolio_selection",
        "selection_rank",
        "why_not_selected",
        "premium_score",
        "premium_rule_note",
        "line_selection",
        "ladder_note",
        "matched_wheelo",
        "market_key",
        "raw_player",
    ]
    with (ROOT / "oddsapi_wheelo_ev_qi.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in scored:
            writer.writerow(row)

    availability_lines = []
    prop_files = odds_files()
    props_by_id: dict[str, dict[str, Any]] = {}
    for path in prop_files:
        event = json.loads(path.read_text())
        props_by_id[str(event.get("id"))] = event

    for event in upcoming_events():
        game = f"{event.get('home_team')} v {event.get('away_team')}"
        prop_event = props_by_id.get(str(event.get("id")))
        if prop_event is None:
            availability_lines.append(f"- {game}: no local player-prop snapshot available for this event.")
            continue
        bookmakers = prop_event.get("bookmakers", [])
        if not bookmakers:
            availability_lines.append(f"- {game}: 0 bookmakers returned for requested player prop markets.")
            continue
        markets = sorted({market.get("key") for book in bookmakers for market in book.get("markets", []) if market.get("key")})
        availability_lines.append(f"- {game}: {len(bookmakers)} bookmakers returned for {', '.join(markets)}.")
    if not availability_lines and not scored:
        availability_lines.append("- No upcoming Odds API event snapshots were available to score.")

    eligible = [row for row in scored if row["matched_wheelo"] and row["market"] != "Ranking/Fantasy Pts"]
    selected = [row for row in eligible if row.get("portfolio_selection") == "PORTFOLIO_BET"]
    leaders = sorted(
        [row for row in selected if row["ev_per_unit"] is not None],
        key=lambda row: (
            row["signal"] in {"A_BET", "B_BET"},
            row["alt_line_score"],
            row.get("posterior_ev_per_unit", row["ev_per_unit"]),
            row["live_qi"],
        ),
        reverse=True,
    )
    lines = [
        "# Odds API + Model Data EV/QI",
        "",
        "Source markets: The Odds API + current Model data player pack.",
        "Marks: Odds API returned INVALID_MARKET for player_marks/player_marks_over.",
        "",
        "## Availability",
        *availability_lines,
        "",
        "## Walters Portfolio Card",
        f"Rules: max {PORTFOLIO_MAX_BETS} bets, max {PORTFOLIO_MAX_GOALS} goal props, max {PORTFOLIO_MAX_PER_PLAYER} per player; Thorp fractional Kelly sizes every selected edge and goals are stake-discounted.",
        f"Calibration: posterior probability blends model, market, and settled-history segments; max per game {PORTFOLIO_MAX_PER_GAME}.",
        "",
        "| Signal | Stake | Bankroll | Full Kelly | Player | Market | Side | Line | Price | Book | Proj | Post Prob | Post EV | QI | AltScore |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in leaders:
        lines.append(
            f"| {row['signal']} | {fmt(row['stake_units'], 2)}u | {fmt(row['thorp_bankroll_pct'], 2)}% | {fmt(row['thorp_full_kelly_pct'], 2)}% | "
            f"{row['player']} | {row['market']} | {row['side']} | {fmt(row['line'], 1)} | "
            f"{fmt(row['best_price'], 2)} | {row['book']} | {fmt(row['projection'], 1)} | "
            f"{fmt(100 * row['posterior_probability'], 1)}% | {fmt(100 * row['posterior_ev_per_unit'], 1)}% | "
            f"{fmt(row['live_qi'], 1)} | {fmt(row['alt_line_score'], 4)} |"
        )
    all_best = [row for row in eligible if row.get("line_selection") == "BEST_RISK_ADJUSTED"]
    suppressed = [row for row in all_best if row.get("signal") in {"A_BET", "B_BET"} and row.get("portfolio_selection") != "PORTFOLIO_BET"]
    lines.append("")
    lines.append("## Suppressed A/B Edges")
    lines.append("These remain model-positive but were removed by Walters portfolio discipline.")
    for row in sorted(suppressed, key=lambda r: float(r.get("alt_line_score") or 0), reverse=True)[:20]:
        lines.append(
            f"- {row['player']} {row['market']} {row['side']} {fmt(row['line'], 1)} @ {fmt(row['best_price'], 2)} "
            f"({row['book']}): {row['portfolio_selection']}, post EV {fmt(100 * row['posterior_ev_per_unit'], 1)}%, QI {fmt(row['live_qi'], 1)}"
        )
    lines.append("")
    lines.append("## Ladder Notes")
    for row in leaders:
        if row.get("ladder_note"):
            lines.append(f"- {row['player']} {row['market']} {row['side']}: {row['ladder_note']}")
    lines.append("")
    lines.append("## Signal Counts")
    counts = defaultdict(int)
    for row in scored:
        counts[row["signal"]] += 1
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.append("")
    lines.append("QI note: `live_qi` is a current-line confidence score derived from Model data support, model edge, market reliability, and book availability. It is not the historical BetMate QI field.")
    (ROOT / "oddsapi_wheelo_ev_qi.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    scored = score()
    write_outputs(scored)
    print(f"Scored outcomes: {len(scored)}")
    print(f"Upcoming event snapshots: {len(odds_files())}")
    print("Wrote oddsapi_wheelo_ev_qi.csv")
    print("Wrote oddsapi_wheelo_ev_qi.md")


if __name__ == "__main__":
    main()
