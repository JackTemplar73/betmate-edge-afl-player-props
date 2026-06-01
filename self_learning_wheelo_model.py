#!/usr/bin/env python3
"""
Self-learning WheeloRatings + Footywire AFL prop model.

This script consumes `wheelo_footywire_backtest_detailed.csv`, learns market-specific
decision thresholds on an earlier chronological slice, then evaluates those learned
rules on a later holdout slice.

It is intentionally simple and auditable:
- No random split.
- No opaque model package.
- No using holdout to tune thresholds.
- Ranking/fantasy is excluded unless it proves itself separately.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path("/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related")
INPUT = ROOT / "wheelo_footywire_backtest_detailed.csv"
OUT_MD = ROOT / "self_learning_wheelo_model_report.md"
OUT_CSV = ROOT / "self_learning_wheelo_model_scored.csv"

APPROVED_MARKETS = {"Disposals", "Marks", "Tackles", "Goals"}
SUPPORT_LEVELS = {
    "strong": {"Model strong support"},
    "lean_or_strong": {"Model strong support", "Model lean support"},
    "neutral_plus": {"Model strong support", "Model lean support", "Model neutral"},
}


def to_float(value: str) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with INPUT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            market = row["market_bucket"]
            if market not in APPROVED_MARKETS:
                continue
            model_edge = to_float(row["model_edge"])
            qi = to_float(row.get("model_qi_num") or row.get("qi"))
            price = to_float(row["best_price"])
            profit = to_float(row["profit"])
            if None in (model_edge, qi, price, profit):
                continue
            row["match_dt"] = parse_dt(row["match_datetime"])
            row["model_edge_num"] = model_edge
            row["qi_num"] = qi
            row["price_num"] = price
            row["profit_num"] = profit
            row["stake_num"] = to_float(row["bet_size"].replace("$", "")) or 1.0
            row["win_bool"] = row["win"] == "True"
            rows.append(row)
    return sorted(rows, key=lambda r: (r["match_dt"], r["captured_datetime"], r["player"], r["market"]))


def split_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    dates = sorted({r["match_dt"].date() for r in rows})
    # Four-date sample: train first three match dates, hold out the final date.
    cutoff_dates = set(dates[:-1])
    train = [r for r in rows if r["match_dt"].date() in cutoff_dates]
    test = [r for r in rows if r["match_dt"].date() not in cutoff_dates]
    return train, test


def summary(rows: list[dict[str, object]]) -> dict[str, float]:
    bets = len(rows)
    wins = sum(1 for r in rows if r["win_bool"])
    stake = sum(float(r["stake_num"]) for r in rows)
    profit = sum(float(r["profit_num"]) for r in rows)
    return {
        "bets": bets,
        "wins": wins,
        "hit_rate": wins / bets if bets else 0.0,
        "stake": stake,
        "profit": profit,
        "roi": profit / stake if stake else 0.0,
    }


def apply_rule(rows: list[dict[str, object]], rule: dict[str, object]) -> list[dict[str, object]]:
    supports = SUPPORT_LEVELS[str(rule["support_mode"])]
    return [
        r for r in rows
        if r["market_bucket"] == rule["market"]
        and r["model_support"] in supports
        and float(r["qi_num"]) >= float(rule["min_qi"])
        and float(r["model_edge_num"]) >= float(rule["min_edge"])
        and float(r["price_num"]) >= float(rule["min_price"])
        and float(r["price_num"]) <= float(rule["max_price"])
    ]


def learn_market_rule(market: str, train: list[dict[str, object]]) -> dict[str, object] | None:
    market_rows = [r for r in train if r["market_bucket"] == market]
    if not market_rows:
        return None

    candidates: list[tuple[float, float, int, dict[str, object], dict[str, float]]] = []
    for support_mode in ("strong", "lean_or_strong", "neutral_plus"):
        for min_qi in (55, 60, 65, 70, 75, 80, 85):
            for min_edge in (-0.02, 0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20):
                for min_price, max_price in ((1.01, 10.0), (1.20, 3.00), (1.40, 2.60), (1.60, 2.40)):
                    rule = {
                        "market": market,
                        "support_mode": support_mode,
                        "min_qi": min_qi,
                        "min_edge": min_edge,
                        "min_price": min_price,
                        "max_price": max_price,
                    }
                    selected = apply_rule(market_rows, rule)
                    stats = summary(selected)
                    if stats["bets"] < 15:
                        continue
                    if stats["roi"] <= 0:
                        continue
                    # Prefer robust profitable samples. ROI matters, but sample size
                    # and hit rate keep tiny high-variance pockets from dominating.
                    score = stats["roi"] * min(stats["bets"], 120) / 120 + 0.10 * stats["hit_rate"]
                    candidates.append((score, stats["roi"], stats["bets"], rule, stats))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[2]), reverse=True)
    _, _, _, best_rule, best_stats = candidates[0]
    return {**best_rule, "train_stats": best_stats}


def learn_rules(train: list[dict[str, object]]) -> list[dict[str, object]]:
    rules = []
    for market in sorted(APPROVED_MARKETS):
        rule = learn_market_rule(market, train)
        if rule:
            rules.append(rule)
    return rules


def score_rows(rows: list[dict[str, object]], rules: list[dict[str, object]]) -> list[dict[str, object]]:
    scored = []
    for row in rows:
        label = "PASS"
        for rule in rules:
            if row in apply_rule([row], rule):
                label = f"SELF_{rule['market'].upper()}"
                break
        row = dict(row)
        row["self_learning_rule"] = label
        scored.append(row)
    return scored


def expanding_walk_forward(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    dates = sorted({r["match_dt"].date() for r in rows})
    scored_oos: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []

    for index in range(1, len(dates)):
        train_dates = set(dates[:index])
        test_date = dates[index]
        train = [r for r in rows if r["match_dt"].date() in train_dates]
        test = [r for r in rows if r["match_dt"].date() == test_date]
        rules = learn_rules(train)
        scored = score_rows(test, rules)
        selected = [r for r in scored if str(r["self_learning_rule"]).startswith("SELF_")]
        scored_oos.extend(scored)
        stats = summary(selected)
        audit_rows.append({
            "test_date": str(test_date),
            "train_dates": ", ".join(str(d) for d in dates[:index]),
            "rules": len(rules),
            **stats,
        })

    return scored_oos, audit_rows


def markdown_stats(label: str, stats: dict[str, float]) -> str:
    return f"| {label} | {stats['bets']:.0f} | {stats['hit_rate']:.1%} | ${stats['profit']:,.2f} | {stats['roi']:.1%} |"


def main() -> None:
    rows = load_rows()
    train, test = split_rows(rows)
    rules = learn_rules(train)
    walk_forward_scored, walk_forward_audit = expanding_walk_forward(rows)

    scored_train = score_rows(train, rules)
    scored_test = score_rows(test, rules)
    scored_all = score_rows(rows, rules)

    train_selected = [r for r in scored_train if str(r["self_learning_rule"]).startswith("SELF_")]
    test_selected = [r for r in scored_test if str(r["self_learning_rule"]).startswith("SELF_")]
    all_selected = [r for r in scored_all if str(r["self_learning_rule"]).startswith("SELF_")]
    wf_selected = [r for r in walk_forward_scored if str(r["self_learning_rule"]).startswith("SELF_")]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "match_datetime", "game", "player", "market", "type", "line", "best_price",
            "bookie", "qi", "final_stat", "market_bucket", "wheelo_support",
            "model_support", "model_qi_num",
            "model_probability", "market_implied_probability", "model_edge",
            "bet_rule", "self_learning_rule", "win", "profit",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in scored_all:
            writer.writerow({field: row.get(field, "") for field in fields})

    report: list[str] = [
        "# Self-Learning Wheelo AFL Prop Model",
        "",
        "Method:",
        "- Input: direct WheeloRatings.com player stats joined to BetMate lines.",
        "- Truth: Footywire-settled `final_stat`.",
        "- Training: first three chronological match dates.",
        "- Holdout: final chronological match date.",
        "- Learner: market-specific threshold search over QI, model edge, support level, and price band.",
        "- Excluded: ranking/fantasy points until they can be priced separately.",
        "",
        "## Learned Rules",
        "",
        "| Market | Support | Min QI | Min Edge | Price Band | Train Bets | Train ROI |",
        "|---|---|---:|---:|---|---:|---:|",
    ]
    for rule in rules:
        ts = rule["train_stats"]
        report.append(
            f"| {rule['market']} | {rule['support_mode']} | {rule['min_qi']} | "
            f"{rule['min_edge']:.2f} | {rule['min_price']:.2f}-{rule['max_price']:.2f} | "
            f"{ts['bets']:.0f} | {ts['roi']:.1%} |"
        )

    report.extend([
        "",
        "## Performance",
        "",
        "| Split | Bets | Hit Rate | Profit | ROI |",
        "|---|---:|---:|---:|---:|",
        markdown_stats("Train selected", summary(train_selected)),
        markdown_stats("Holdout selected", summary(test_selected)),
        markdown_stats("Expanding walk-forward selected", summary(wf_selected)),
        markdown_stats("All selected", summary(all_selected)),
        markdown_stats("All available approved markets", summary(rows)),
        "",
        "## Expanding Walk-Forward Audit",
        "",
        "| Test Date | Prior Train Dates | Rules | Bets | Hit Rate | Profit | ROI |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for audit in walk_forward_audit:
        report.append(
            f"| {audit['test_date']} | {audit['train_dates']} | {audit['rules']} | "
            f"{audit['bets']:.0f} | {audit['hit_rate']:.1%} | ${audit['profit']:,.2f} | {audit['roi']:.1%} |"
        )

    report.extend([
        "",
        "## Holdout By Market",
        "",
        "| Market | Bets | Hit Rate | Profit | ROI |",
        "|---|---:|---:|---:|---:|",
    ])

    by_market: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in test_selected:
        by_market[str(row["market_bucket"])].append(row)
    for market, group in sorted(by_market.items()):
        report.append(markdown_stats(market, summary(group)))

    report.extend([
        "",
        "## Interpretation",
        "",
        "This is the sharpest current version because it learns market-specific gates from prior settled rows, then tests them chronologically out-of-sample. It still needs prop CLV and timestamped pre-bounce Wheelo snapshots for an institutional-grade proof.",
        "",
    ])

    OUT_MD.write_text("\n".join(report), encoding="utf-8")

    print(f"Rules learned: {len(rules)}")
    print(f"Train selected: {summary(train_selected)}")
    print(f"Holdout selected: {summary(test_selected)}")
    print(f"Expanding walk-forward selected: {summary(wf_selected)}")
    print(f"All selected: {summary(all_selected)}")
    print(f"Report: {OUT_MD}")
    print(f"Scored CSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
