#!/usr/bin/env python3
"""
WheeloRatings + Footywire AFL prop backtest.

Inputs:
- BetMate prop CSV with captured lines/prices and Footywire-settled final_stat.
- WheeloRatings player stats snapshots available locally: season, last5, last10.

This is a reproducible replay backtest. It is not labelled pure walk-forward unless
timestamped Wheelo snapshots exist for each prop capture time.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import score_oddsapi_wheelo_props as scorer


ROOT = Path("/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related")
PROPS = Path("/Users/merlin/Desktop/Claude/AFL/AFL/BETMATE 1.6/Props/AFLbetmate_props.csv")
WHEELO_PLAYER = Path("/Users/merlin/Desktop/Claude/AFL/Wheelo Stats/Player Stats")

OUT_CSV = ROOT / "wheelo_footywire_backtest_detailed.csv"
OUT_MD = ROOT / "wheelo_footywire_backtest_report.md"


WHEELO_FILES = {
    "season": WHEELO_PLAYER / "AFL_Player_Stats_2026.csv",
    "l5": WHEELO_PLAYER / "AFL_Player_Stats_Last5.csv",
    "l10": WHEELO_PLAYER / "AFL_Player_Stats_Last10.csv",
}

WHEELO_LIVE_JSON = {
    "season": ROOT / "wheelo_live_2026.json",
    "l5": ROOT / "wheelo_live_last5.json",
    "l10": ROOT / "wheelo_live_last10.json",
}

WHEELO_URLS = {
    "season": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json",
    "l5": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json",
    "l10": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json",
}

APPROVED_MARKETS = {"Disposals", "Marks", "Tackles", "Goals"}


def clean_name(name: str | None) -> str:
    return re.sub(r"[^a-z ]", "", (name or "").lower()).strip()


def to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if not text or text.upper() == "NA":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return None if math.isnan(number) else number


def load_wheelo(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return {clean_name(row.get("Player")): row for row in rows if row.get("Player")}


def load_wheelo_json(path: Path) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    data = payload.get("Data", payload)
    metadata = payload.get("Metadata", {})
    if not data or "Player" not in data:
        return {}, metadata

    keys = list(data.keys())
    row_count = len(data["Player"])
    rows: list[dict[str, object]] = []
    for index in range(row_count):
        rows.append({key: data[key][index] if index < len(data[key]) else "" for key in keys})

    return {clean_name(str(row.get("Player"))): row for row in rows if row.get("Player")}, metadata


def load_wheelo_sources() -> tuple[dict[str, dict[str, dict[str, object]]], dict[str, dict[str, object]], dict[str, str]]:
    wheelo: dict[str, dict[str, dict[str, object]]] = {}
    metadata: dict[str, dict[str, object]] = {}
    source_paths: dict[str, str] = {}

    for source in ("season", "l5", "l10"):
        json_path = WHEELO_LIVE_JSON[source]
        if json_path.exists():
            wheelo[source], metadata[source] = load_wheelo_json(json_path)
            source_paths[source] = str(json_path)
        else:
            wheelo[source] = load_wheelo(WHEELO_FILES[source])
            metadata[source] = {}
            source_paths[source] = str(WHEELO_FILES[source])

    return wheelo, metadata, source_paths


def match_player(index: dict[str, dict[str, object]], player: str) -> dict[str, object] | None:
    key = clean_name(player)
    if key in index:
        return index[key]

    parts = key.split()
    if len(parts) < 2:
        return None

    candidates = [row for name, row in index.items() if parts[0] in name and parts[-1] in name]
    if len(candidates) == 1:
        return candidates[0]

    last_candidates = [row for name, row in index.items() if parts[-1] in name]
    if len(last_candidates) == 1:
        return last_candidates[0]

    return None


def market_to_stat(market: str) -> tuple[str | None, str]:
    text = market.lower()
    if "disposal" in text:
        return "Disposals", "Disposals"
    if "mark" in text:
        return "Marks", "Marks"
    if "tackle" in text:
        return "Tackles", "Tackles"
    if "fantasy" in text:
        return "DreamTeamPoints_Avg", "Ranking/Fantasy Pts"
    if "supercoach" in text:
        return "Supercoach_Avg", "Ranking/Fantasy Pts"
    if "ranking" in text or "rating" in text:
        return "RatingPoints_Avg", "Ranking/Fantasy Pts"
    if "goal" in text:
        return "Goals_Avg", "Goals"
    return None, "Other"


def weighted_wheelo_projection(
    player: str,
    stat: str,
    wheelo: dict[str, dict[str, dict[str, str]]],
) -> tuple[float | None, str]:
    components: list[tuple[str, float, float]] = []
    for source, weight in (("season", 0.50), ("l5", 0.30), ("l10", 0.20)):
        row = match_player(wheelo[source], player)
        if not row:
            continue
        value = to_float(row.get(stat))
        if value is not None:
            components.append((source, value, weight))

    if not components:
        return None, "no_match"

    weight_total = sum(weight for _, _, weight in components)
    projection = sum(value * weight for _, value, weight in components) / weight_total
    sources = "+".join(source for source, _, _ in components)
    return projection, sources


def market_implied_probability(price: float) -> float:
    # Only one side is in the BetMate export. Use raw implied probability as a
    # conservative hurdle; future two-sided capture should replace this with no-vig.
    return 1.0 / price


def model_grade_rule(row: dict[str, object]) -> str:
    bucket = str(row["market_bucket"])
    support = str(row["model_support"])
    model_edge = row.get("model_edge")
    qi = float(row["model_qi_num"])

    if bucket not in APPROVED_MARKETS:
        return "PASS_EXCLUDED_MARKET"
    if model_edge == "":
        return "PASS_NO_MODEL"
    edge = float(model_edge)
    return scorer.signal(bucket, edge, qi, support)


def qi_tier(qi: float) -> str:
    if qi >= 90:
        return "QI 90+"
    if qi >= 80:
        return "QI 80-89"
    if qi >= 70:
        return "QI 70-79"
    if qi >= 60:
        return "QI 60-69"
    return "QI <60"


def settled_win(side: str, line: float, final_stat: float) -> bool:
    if "under" in side.lower():
        return final_stat < line
    return final_stat > line


def summary(rows: list[dict[str, object]]) -> dict[str, float]:
    count = len(rows)
    wins = sum(1 for row in rows if row["win"])
    stake = sum(float(row["stake"]) for row in rows)
    profit = sum(float(row["profit"]) for row in rows)
    return {
        "bets": count,
        "wins": wins,
        "hit_rate": wins / count if count else 0.0,
        "stake": stake,
        "profit": profit,
        "roi": profit / stake if stake else 0.0,
    }


def group_table(rows: list[dict[str, object]], key: str, min_n: int = 1) -> list[tuple[str, dict[str, float]]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)
    output = [(name, summary(group)) for name, group in groups.items() if len(group) >= min_n]
    return sorted(output, key=lambda item: (-item[1]["roi"], -item[1]["bets"], item[0]))


def composite_group(rows: list[dict[str, object]], keys: tuple[str, ...], min_n: int) -> list[tuple[str, dict[str, float]]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        name = " | ".join(str(row[key]) for key in keys)
        groups[name].append(row)
    output = [(name, summary(group)) for name, group in groups.items() if len(group) >= min_n]
    return sorted(output, key=lambda item: (-item[1]["roi"], -item[1]["bets"], item[0]))


def markdown_table(items: list[tuple[str, dict[str, float]]], label: str) -> str:
    lines = [
        f"### {label}",
        "",
        "| Segment | Bets | Hit Rate | Profit | ROI |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, stats in items:
        lines.append(
            f"| {name} | {stats['bets']:.0f} | {stats['hit_rate']:.1%} | "
            f"${stats['profit']:,.2f} | {stats['roi']:.1%} |"
        )
    return "\n".join(lines)


def main() -> None:
    wheelo, wheelo_metadata, source_paths = load_wheelo_sources()
    rows: list[dict[str, object]] = []

    with PROPS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (row.get("result_checked") or "").strip().lower() != "yes":
                continue

            stat, market_bucket = market_to_stat(row.get("market", ""))
            if stat is None or market_bucket == "Other":
                continue

            line = to_float(row.get("line") or row.get("sharp_line"))
            final_stat = to_float(row.get("final_stat"))
            price = to_float(row.get("best_price"))
            qi = to_float(row.get("qi"))
            stake = to_float(row.get("bet_size")) or 1.0
            if None in (line, final_stat, price, qi):
                continue

            assert line is not None and final_stat is not None and price is not None and qi is not None
            season_row = match_player(wheelo["season"], row.get("player", "")) or {}
            l5_row = match_player(wheelo["l5"], row.get("player", "")) or {}
            l10_row = match_player(wheelo["l10"], row.get("player", "")) or {}

            season_projection = to_float(season_row.get(stat))
            last5_projection = to_float(l5_row.get(stat))
            last10_projection = to_float(l10_row.get(stat))
            season_matches = to_float(season_row.get("Matches"))
            last5_matches = to_float(l5_row.get("Matches"))
            last10_matches = to_float(l10_row.get("Matches"))

            projection = scorer.kalman_mean_reversion_projection(
                market_bucket,
                season_projection,
                season_matches,
                last10_projection,
                last10_matches,
                last5_projection,
                last5_matches,
            )
            sigma = scorer.dynamic_sigma(
                market_bucket,
                season_projection,
                season_matches,
                last10_projection,
                last10_matches,
                last5_projection,
                last5_matches,
            ) if season_projection is not None else scorer.MARKET_SIGMA.get(market_bucket)
            support, edge = scorer.support_bucket(market_bucket, row.get("type", ""), projection, line)
            model_prob, probability_model = scorer.model_probability(market_bucket, row.get("type", ""), projection, line, sigma)
            market_prob = market_implied_probability(price)
            model_edge = None if model_prob is None else model_prob - market_prob
            model_qi = scorer.live_qi(market_bucket, model_edge, support, projection is not None, 1)
            win = settled_win(row.get("type", ""), line, final_stat)
            signal_preview = scorer.signal(market_bucket, model_edge, model_qi, support)
            model_stake = scorer.stake_units(
                {
                    "signal": signal_preview,
                    "market": market_bucket,
                    "live_qi": model_qi,
                    "ev_per_unit": "" if model_prob is None else (model_prob * price - 1),
                }
            )
            profit = model_stake * (price - 1) if win else -model_stake

            out_row = (
                {
                    **row,
                    "stat": stat,
                    "market_bucket": market_bucket,
                    "line_num": line,
                    "final_stat_num": final_stat,
                    "price_num": price,
                    "captured_qi_num": qi,
                    "captured_qi_tier": qi_tier(qi),
                    "stake": model_stake,
                    "wheelo_projection": "" if projection is None else round(projection, 4),
                    "season_projection": "" if season_projection is None else round(season_projection, 4),
                    "last5_projection": "" if last5_projection is None else round(last5_projection, 4),
                    "last10_projection": "" if last10_projection is None else round(last10_projection, 4),
                    "dynamic_sigma": "" if sigma is None else round(sigma, 4),
                    "probability_model": probability_model,
                    "model_stat_edge": "" if edge is None else round(edge, 4),
                    "model_support": support,
                    "model_probability": "" if model_prob is None else round(model_prob, 4),
                    "market_implied_probability": round(market_prob, 4),
                    "model_edge": "" if model_edge is None else round(model_edge, 4),
                    "model_qi_num": model_qi,
                    "model_qi_tier": qi_tier(model_qi),
                    "win": win,
                    "profit": round(profit, 2),
                }
            )
            out_row["bet_rule"] = model_grade_rule(out_row)
            rows.append(out_row)

    detailed_fields = [
        "captured_datetime",
        "match_datetime",
        "game",
        "player",
        "market",
        "type",
        "line",
        "best_price",
        "bookie",
        "qi",
        "bet_size",
        "final_stat",
        "stat",
        "market_bucket",
        "captured_qi_tier",
        "wheelo_projection",
        "season_projection",
        "last5_projection",
        "last10_projection",
        "dynamic_sigma",
        "probability_model",
        "model_stat_edge",
        "model_support",
        "model_probability",
        "market_implied_probability",
        "model_edge",
        "model_qi_num",
        "model_qi_tier",
        "bet_rule",
        "win",
        "profit",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=detailed_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in detailed_fields})

    overall = summary(rows)
    rule_70 = [
        row
        for row in rows
        if float(row["model_qi_num"]) >= 70
        and row["model_support"] in {"Model strong support", "Model lean support"}
    ]
    rule_80_strong = [
        row
        for row in rows
        if float(row["model_qi_num"]) >= 80 and row["model_support"] == "Model strong support"
    ]
    rule_a = [row for row in rows if row["bet_rule"] == "A_BET"]
    rule_ab = [row for row in rows if row["bet_rule"] in {"A_BET", "B_BET"}]

    report = [
        "# WheeloRatings + Footywire AFL Prop Backtest",
        "",
        "Source contract:",
        "- Model input: WheeloRatings.com player season, Last5, Last10 data.",
        "- Settlement truth: Footywire final player stat written into `final_stat`.",
        "- Market input: BetMate captured line, price, book, QI, and stake.",
        "",
        "Wheelo source URLs:",
        f"- Season: {WHEELO_URLS['season']}",
        f"- Last5: {WHEELO_URLS['l5']}",
        f"- Last10: {WHEELO_URLS['l10']}",
        "",
        "Loaded Wheelo snapshots:",
        f"- Season: `{source_paths['season']}`",
        f"- Last5: `{source_paths['l5']}`",
        f"- Last10: `{source_paths['l10']}`",
        "",
        "Wheelo metadata:",
        f"- Season latest games: {wheelo_metadata.get('season', {}).get('LatestGames', [''])[0]}",
        f"- Last5 latest games: {wheelo_metadata.get('l5', {}).get('LatestGames', [''])[0]}",
        f"- Last10 latest games: {wheelo_metadata.get('l10', {}).get('LatestGames', [''])[0]}",
        "",
        "Status: replay diagnostic, not pure timestamped walk-forward. Full walk-forward requires archived Wheelo snapshots for each `captured_datetime`.",
        "",
        "## Overall",
        "",
        "| Bets | Hit Rate | Profit | ROI |",
        "|---:|---:|---:|---:|",
        f"| {overall['bets']:.0f} | {overall['hit_rate']:.1%} | ${overall['profit']:,.2f} | {overall['roi']:.1%} |",
        "",
        "## Decision Rules",
        "",
        "| Rule | Bets | Hit Rate | Profit | ROI |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, group in (
        ("Model QI >= 70 + model lean/strong support", rule_70),
        ("Model QI >= 80 + model strong support", rule_80_strong),
        ("A_BET: approved market + model QI>=80 + strong model support + edge>=4%", rule_a),
        ("A/B_BET: approved market + model QI>=70 + model support + edge", rule_ab),
    ):
        stats = summary(group)
        report.append(
            f"| {label} | {stats['bets']:.0f} | {stats['hit_rate']:.1%} | "
            f"${stats['profit']:,.2f} | {stats['roi']:.1%} |"
        )

    report.extend(
        [
            "",
            markdown_table(group_table(rows, "model_support"), "By Model Support"),
            "",
            markdown_table(group_table(rows, "market_bucket"), "By Market"),
            "",
            markdown_table(group_table(rows, "bet_rule"), "By New Bet Rule"),
            "",
            markdown_table(composite_group(rows, ("market_bucket", "model_support"), 50), "Market x Model Support"),
            "",
            markdown_table(composite_group(rows, ("market_bucket", "bet_rule"), 20), "Market x New Bet Rule"),
            "",
            markdown_table(composite_group(rows, ("model_support", "model_qi_tier"), 50), "Model Support x Model QI Tier"),
            "",
            markdown_table(composite_group(rows, ("market_bucket", "bookie"), 30), "Market x Book"),
            "",
        ]
    )
    OUT_MD.write_text("\n".join(report), encoding="utf-8")

    print(f"Rows backtested: {len(rows)}")
    print(f"Detailed CSV: {OUT_CSV}")
    print(f"Report: {OUT_MD}")
    print(
        "Rule QI>=70 + Wheelo support:",
        summary(rule_70),
    )
    print(
        "Rule QI>=80 + Wheelo strong:",
        summary(rule_80_strong),
    )
    print("Rule A_BET:", summary(rule_a))
    print("Rule A/B_BET:", summary(rule_ab))


if __name__ == "__main__":
    main()
