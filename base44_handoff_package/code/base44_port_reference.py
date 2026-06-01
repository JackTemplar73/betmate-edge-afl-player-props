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
COUNT_AWARE_MARKETS = {"Goals", "Tackles", "Marks"}

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


def to_float(value: Any) -> float | None:
    if value in ("", "NA", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
