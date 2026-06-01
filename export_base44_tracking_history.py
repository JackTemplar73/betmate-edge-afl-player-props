#!/usr/bin/env python3
"""Export Base44-ready tracking and history payloads from the AFL props ledger."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "aflplayerprops_bet_history.csv"
ROUND_MAP = ROOT / "afl_round_mapping.csv"
EXPORT_DIR = ROOT / "base44_handoff_package" / "exports"
EXPORT_CSV = EXPORT_DIR / "base44_bet_history_import.csv"
EXPORT_JSON = EXPORT_DIR / "base44_bet_history_import.json"
SUMMARY_JSON = EXPORT_DIR / "base44_tracking_summary.json"

FIELDS = [
    "betId",
    "status",
    "createdAtUtc",
    "updatedAtUtc",
    "roundNumber",
    "game",
    "commenceTime",
    "player",
    "market",
    "side",
    "line",
    "book",
    "betPrice",
    "stakeUnits",
    "signal",
    "projection",
    "modelProbability",
    "marketProbability",
    "modelEdge",
    "evPerUnit",
    "qi",
    "altLineScore",
    "markovPath",
    "bookMarketReliability",
    "portfolioSelection",
    "openLine",
    "openPrice",
    "latestLine",
    "latestPrice",
    "closeLine",
    "closePrice",
    "clvPriceDecimal",
    "clvImpliedPoints",
    "lineClv",
    "clvStatus",
    "actual",
    "result",
    "flatProfit",
    "stakeProfit",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def f(value: str) -> float:
    if value in ("", None):
        return 0.0
    return float(value)


def round_map() -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for row in read_csv(ROUND_MAP):
        mapping[(row["game"], row["commence_time"])] = row["round_number"]
    return mapping


def transform_rows(rows: list[dict[str, str]], rounds: dict[tuple[str, str], str]) -> list[dict[str, str]]:
    transformed: list[dict[str, str]] = []
    for row in rows:
        transformed.append(
            {
                "betId": row["bet_id"],
                "status": row["status"],
                "createdAtUtc": row["created_at_utc"],
                "updatedAtUtc": row["updated_at_utc"],
                "roundNumber": rounds.get((row["game"], row["commence_time"]), ""),
                "game": row["game"],
                "commenceTime": row["commence_time"],
                "player": row["player"],
                "market": row["market"],
                "side": row["side"],
                "line": row["line"],
                "book": row["book"],
                "betPrice": row["bet_price"],
                "stakeUnits": row["stake_units"],
                "signal": row["signal"],
                "projection": row["projection"],
                "modelProbability": row["model_probability"],
                "marketProbability": row["market_probability"],
                "modelEdge": row["model_edge"],
                "evPerUnit": row["ev_per_unit"],
                "qi": row["live_qi"],
                "altLineScore": row["alt_line_score"],
                "markovPath": row["markov_path"],
                "bookMarketReliability": row["book_market_reliability"],
                "portfolioSelection": row["portfolio_selection"],
                "openLine": row["open_line"],
                "openPrice": row["open_price"],
                "latestLine": row["latest_line"],
                "latestPrice": row["latest_price"],
                "closeLine": row["close_line"],
                "closePrice": row["close_price"],
                "clvPriceDecimal": row["clv_price_decimal"],
                "clvImpliedPoints": row["clv_implied_points"],
                "lineClv": row["line_clv"],
                "clvStatus": row["clv_status"],
                "actual": row["actual"],
                "result": row["result"],
                "flatProfit": row["flat_profit"],
                "stakeProfit": row["stake_profit"],
            }
        )
    return transformed


def settled_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    settled = [row for row in rows if row["status"] == "SETTLED"]
    results = Counter(row["result"] for row in settled)
    total_staked = sum(f(row["stakeUnits"]) for row in settled)
    stake_profit = sum(f(row["stakeProfit"]) for row in settled)
    flat_profit = sum(f(row["flatProfit"]) for row in settled)
    return {
        "rowCount": len(rows),
        "settledCount": len(settled),
        "results": dict(results),
        "equalBetProfit": round(flat_profit, 3),
        "actualProfit": round(stake_profit, 3),
        "totalStaked": round(total_staked, 3),
        "actualRoi": round((stake_profit / total_staked) * 100, 1) if total_staked else 0.0,
    }


def build_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    by_game: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_game[row["game"]].append(row)

    summary = {
        "generatedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "overall": settled_summary(rows),
        "byGame": {game: settled_summary(game_rows) for game, game_rows in sorted(by_game.items())},
    }
    return summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ledger_rows = read_csv(LEDGER)
    rounds = round_map()
    transformed = transform_rows(ledger_rows, rounds)
    summary = build_summary(transformed)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(EXPORT_CSV, transformed)
    EXPORT_JSON.write_text(json.dumps(transformed, indent=2))
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))

    print(f"Wrote {len(transformed)} rows to {EXPORT_CSV}")
    print(f"Wrote JSON export to {EXPORT_JSON}")
    print(f"Wrote summary to {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
