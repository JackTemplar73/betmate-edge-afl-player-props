#!/usr/bin/env python3
"""Score live Odds API AFL player props against WheeloRatings projections."""

from __future__ import annotations

import csv
import difflib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ODDS_FILES = [
    ROOT / "oddsapi_gws_bris_props.json",
    ROOT / "oddsapi_wb_melb_props.json",
]
WHEELO_PLAYERS = ROOT / "wheelo_today_player_pack.csv"
WHEELO_PLAYER_STATS = ROOT / "wheelo_snapshots" / "20260524_123837" / "wheelo_player_stats_2026.json"

MARKET_MAP = {
    "player_disposals": ("Disposals", "Disposals", True),
    "player_tackles_over": ("Tackles", "Tackles", False),
    "player_goals_scored_over": ("Goals", "Goals_Avg", False),
    "player_afl_fantasy_points_over": ("Ranking/Fantasy Pts", "DreamTeamPoints_Avg", False),
}
MARKET_SIGMA = {
    "Disposals": 5.5,
    "Marks": 2.2,
    "Tackles": 2.1,
    "Ranking/Fantasy Pts": 18.0,
    "Goals": 0.85,
}
PORTFOLIO_MAX_BETS = 10
PORTFOLIO_MAX_GOALS = 3
PORTFOLIO_MAX_PER_PLAYER = 1

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


def model_probability(bucket: str, side: str, projection: float | None, line: float) -> float | None:
    if projection is None:
        return None
    sigma = MARKET_SIGMA[bucket]
    z = (line - projection) / sigma
    under = normal_cdf(z)
    prob = under if side == "Under" else 1.0 - under
    return max(0.01, min(0.99, prob))


def support_bucket(bucket: str, side: str, projection: float | None, line: float) -> tuple[str, float | None]:
    if projection is None:
        return "No Wheelo match", None
    edge = line - projection if side == "Under" else projection - line
    strong = SUPPORT_STRONG[bucket]
    lean = SUPPORT_LEAN[bucket]
    if edge >= strong:
        return "Wheelo strong support", edge
    if edge >= lean:
        return "Wheelo lean support", edge
    if edge > -lean:
        return "Wheelo neutral", edge
    if edge > -strong:
        return "Wheelo lean against", edge
    return "Wheelo strong against", edge


def live_qi(bucket: str, model_edge: float | None, support: str, matched: bool, books_at_line: int) -> float:
    if model_edge is None or not matched:
        return 0.0
    score = 50.0
    score += {
        "Wheelo strong support": 18,
        "Wheelo lean support": 10,
        "Wheelo neutral": 2,
        "Wheelo lean against": -10,
        "Wheelo strong against": -18,
    }.get(support, 0)
    score += min(18.0, max(-18.0, model_edge * 100.0))
    score += min(6.0, books_at_line * 1.5)
    score += {"Disposals": 6, "Tackles": 4, "Goals": 3, "Ranking/Fantasy Pts": -4}.get(bucket, 0)
    return round(max(0.0, min(99.0, score)), 1)


def reliability_multiplier(book: str, market: str) -> float:
    return BOOK_MARKET_RELIABILITY.get((book, market), 1.0)


def stake_units(row: dict[str, Any]) -> float:
    signal = str(row.get("signal"))
    market = str(row.get("market"))
    qi = float(row.get("live_qi") or 0)
    ev = float(row.get("ev_per_unit") or 0)

    if signal == "A_BET":
        base = 1.0
    elif signal == "B_BET":
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


def load_wheelo_rows() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    rows: dict[str, dict[str, Any]] = {}
    with WHEELO_PLAYERS.open() as f:
        for row in csv.DictReader(f):
            rows[norm_name(row["Player"])] = row

    stats = json.loads(WHEELO_PLAYER_STATS.read_text())["Data"]
    for idx, player in enumerate(stats["Player"]):
        key = norm_name(player)
        if key in rows:
            rows[key]["DreamTeamPoints_Avg"] = stats.get("DreamTeamPoints_Avg", [None])[idx]

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
    scored: list[dict[str, Any]] = []
    for odds_path in ODDS_FILES:
        event = json.loads(odds_path.read_text())
        prices = collect_prices(event.get("bookmakers", []))
        no_vig = no_vig_lookup(prices)
        for (market_key, bucket, raw_player, side, line), offers in prices.items():
            best = max(offers, key=lambda item: item["price"])
            player, wheelo = match_player(raw_player, rows, aliases)
            _, projection_field, _ = MARKET_MAP[market_key]
            projection = to_float(wheelo.get(projection_field)) if wheelo else None
            prob = model_probability(bucket, side, projection, line)
            support, stat_gap = support_bucket(bucket, side, projection, line)
            raw_implied = 1 / best["price"]
            nv = no_vig.get((market_key, raw_player, side, line, best["book"]))
            implied = nv if nv is not None else raw_implied
            edge = None if prob is None else prob - implied
            ev = None if prob is None else prob * best["price"] - 1
            qi = live_qi(bucket, edge, support, wheelo is not None, len(offers))
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
                    "wheelo_support": support,
                    "stat_gap": stat_gap,
                    "model_probability": prob,
                    "market_probability": implied,
                    "model_edge": edge,
                    "ev_per_unit": ev,
                    "live_qi": qi,
                    "matched_wheelo": wheelo is not None,
                    "signal": signal(bucket, edge, qi, support),
                }
            )
    return scored


def signal(bucket: str, edge: float | None, qi: float, support: str) -> str:
    if bucket == "Ranking/Fantasy Pts":
        return "INFO_ONLY"
    if edge is None:
        return "NO_MATCH"
    if qi >= 80 and edge >= 0.04 and support == "Wheelo strong support":
        return "A_BET"
    if qi >= 70 and edge >= 0.03 and support in {"Wheelo strong support", "Wheelo lean support"}:
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
        row["portfolio_selection"] = "NOT_SELECTED"

    for _, rows in groups.items():
        rows.sort(key=lambda row: (float(row["alt_line_score"]), float(row["ev_per_unit"] or 0), float(row["live_qi"] or 0)), reverse=True)
        best = rows[0]
        positive = [row for row in rows if float(row["ev_per_unit"] or 0) >= 0.03]
        for row in rows:
            if row is best:
                row["line_selection"] = "BEST_RISK_ADJUSTED"
            elif float(row["ev_per_unit"] or 0) >= 0.03:
                row["line_selection"] = "LADDER_OPTION"
            else:
                row["line_selection"] = "DUPLICATE_SUPPRESSED"
            if len(positive) > 1:
                row["ladder_note"] = "; ".join(
                    f"{r['side']} {r['line']} @ {r['best_price']} EV {100 * float(r['ev_per_unit']):.1f}%"
                    for r in positive[:4]
                )
            else:
                row["ladder_note"] = ""

    select_portfolio(scored)


def select_portfolio(scored: list[dict[str, Any]]) -> None:
    candidates = [
        row for row in scored
        if row.get("line_selection") == "BEST_RISK_ADJUSTED"
        and row.get("signal") in {"A_BET", "B_BET"}
        and float(row.get("alt_line_score") or -999) > 0
    ]
    candidates.sort(
        key=lambda row: (
            float(row.get("alt_line_score") or 0),
            float(row.get("ev_per_unit") or 0),
            float(row.get("live_qi") or 0),
        ),
        reverse=True,
    )
    chosen = []
    player_count: dict[str, int] = defaultdict(int)
    goal_count = 0
    for row in candidates:
        if len(chosen) >= PORTFOLIO_MAX_BETS:
            break
        if player_count[str(row["player"])] >= PORTFOLIO_MAX_PER_PLAYER:
            row["portfolio_selection"] = "SUPPRESSED_PLAYER_CAP"
            continue
        if row["market"] == "Goals" and goal_count >= PORTFOLIO_MAX_GOALS:
            row["portfolio_selection"] = "SUPPRESSED_GOAL_CAP"
            continue
        row["portfolio_selection"] = "PORTFOLIO_BET"
        row["stake_units"] = stake_units(row)
        chosen.append(row)
        player_count[str(row["player"])] += 1
        if row["market"] == "Goals":
            goal_count += 1


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
        "wheelo_support",
        "stat_gap",
        "model_probability",
        "market_probability",
        "model_edge",
        "ev_per_unit",
        "live_qi",
        "signal",
        "alt_line_score",
        "book_market_reliability",
        "stake_units",
        "portfolio_selection",
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

    eligible = [row for row in scored if row["matched_wheelo"] and row["market"] != "Ranking/Fantasy Pts"]
    selected = [row for row in eligible if row.get("portfolio_selection") == "PORTFOLIO_BET"]
    leaders = sorted(
        [row for row in selected if row["ev_per_unit"] is not None],
        key=lambda row: (row["signal"] in {"A_BET", "B_BET"}, row["alt_line_score"], row["ev_per_unit"], row["live_qi"]),
        reverse=True,
    )
    lines = [
        "# Odds API + Wheelo EV/QI",
        "",
        "Source markets: The Odds API + WheeloRatings current player pack.",
        "Marks: Odds API returned INVALID_MARKET for player_marks/player_marks_over.",
        "",
        "## Availability",
        "- Greater Western Sydney v Brisbane: 0 bookmakers returned for requested player prop markets.",
        "- Western Bulldogs v Melbourne: player_disposals, player_tackles_over, player_goals_scored_over, player_afl_fantasy_points_over returned.",
        "",
        "## Walters Portfolio Card",
        f"Rules: max {PORTFOLIO_MAX_BETS} bets, max {PORTFOLIO_MAX_GOALS} goal props, max {PORTFOLIO_MAX_PER_PLAYER} per player; goals are stake-discounted.",
        "",
        "| Signal | Stake | Player | Market | Side | Line | Price | Book | Proj | Prob | EV | QI | AltScore |",
        "|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in leaders:
        lines.append(
            f"| {row['signal']} | {fmt(row['stake_units'], 2)}u | {row['player']} | {row['market']} | {row['side']} | {fmt(row['line'], 1)} | "
            f"{fmt(row['best_price'], 2)} | {row['book']} | {fmt(row['projection'], 1)} | "
            f"{fmt(100 * row['model_probability'], 1)}% | {fmt(100 * row['ev_per_unit'], 1)}% | "
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
            f"({row['book']}): {row['portfolio_selection']}, EV {fmt(100 * row['ev_per_unit'], 1)}%, QI {fmt(row['live_qi'], 1)}"
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
    lines.append("QI note: `live_qi` is a current-line confidence score derived from Wheelo support, model edge, market reliability, and book availability. It is not the historical BetMate QI field.")
    (ROOT / "oddsapi_wheelo_ev_qi.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    scored = score()
    write_outputs(scored)
    print(f"Scored outcomes: {len(scored)}")
    print("Wrote oddsapi_wheelo_ev_qi.csv")
    print("Wrote oddsapi_wheelo_ev_qi.md")


if __name__ == "__main__":
    main()
