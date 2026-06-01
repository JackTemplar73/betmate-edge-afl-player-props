#!/usr/bin/env python3
"""Build a Walters-style markdown summary report for the current portfolio card."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCORED = ROOT / "oddsapi_wheelo_ev_qi.csv"
MARKOV = ROOT / "markov_bet_justifications.csv"
OUT = ROOT / "afl_player_props_walters_report.md"


def to_float(value: str) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def num(value: str | float | None, digits: int = 1) -> str:
    if value in ("", None):
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def pct(value: str | float | None) -> str:
    if value in ("", None):
        return "-"
    try:
        return f"{100 * float(value):.1f}%"
    except (TypeError, ValueError):
        return "-"


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("player", "").strip().lower(),
        row.get("market", "").strip().lower(),
        row.get("side", "").strip().lower(),
        str(to_float(row.get("line"))),
    )


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def detailed_read(row: dict[str, str], markov_row: dict[str, str] | None) -> list[str]:
    model_line = num(row.get("projection"), 3)
    market_line = num(row.get("line"), 1)
    base_line = num(row.get("base_projection"), 3)
    shift = num(row.get("projection_delta"), 3)
    ev = pct(row.get("ev_per_unit"))
    prob = pct(row.get("model_probability"))
    qi = num(row.get("live_qi"), 1)
    path = markov_row.get("markov_path", "") if markov_row else ""
    risk = markov_row.get("risk", "") if markov_row else ""

    lines = [
        f"### {row['player']} {row['market']} {row['side']} {market_line} @ {num(row['best_price'], 2)} ({row['book']})",
        f"- QI: {qi}",
        f"- Markov path: {path or '-'}",
        (
            f"- Average bettor read: the adjusted model line is `{model_line}` against a market line of `{market_line}`. "
            f"The raw season line was `{base_line}`, and the Kalman/reversion step moved it by `{shift}`. "
            f"That leaves the model showing `{prob}` win probability and `{ev}` EV at `{num(row['best_price'], 2)}`."
        ),
        (
            f"- What it means in plain English: the model still likes this side after smoothing recent form and pulling "
            f"the player back toward his longer-run baseline, so this is not just a one-hot-game bet."
        ),
    ]
    if markov_row and markov_row.get("justification"):
        lines.append(f"- Why it made the card: {markov_row['justification']}")
    if markov_row and markov_row.get("ladder_note"):
        lines.append(f"- Ladder context: {markov_row['ladder_note']}")
    if risk:
        lines.append(f"- Main risk: {risk}")
    lines.append("")
    return lines


def main() -> None:
    scored_rows = load_rows(SCORED)
    markov_rows = load_rows(MARKOV)
    portfolio = [row for row in scored_rows if row.get("portfolio_selection") == "PORTFOLIO_BET"]
    portfolio.sort(key=lambda row: float(row.get("live_qi") or 0), reverse=True)
    markov_lookup = {key(row): row for row in markov_rows}

    games = sorted({row["game"] for row in portfolio})
    title_game = "Round 12 Current Portfolio" if len(games) > 1 else (games[0] if games else "Current AFL Props Card")
    lines = [
        f"# Walters Style AFL Player Props Report: {title_game}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "This card uses the adjusted model line from a simple Kalman-style recent-form update plus mean reversion back toward the season baseline before EV/QI scoring.",
        "",
        "## Summary Card",
        "",
        "| QI | Signal | Player | Market | Side | Model Line | Market Line | Price | Bookie | EV | Stake |",
        "|---:|---|---|---|---|---:|---:|---:|---|---:|---:|",
    ]

    for row in portfolio:
        lines.append(
            f"| {num(row['live_qi'], 1)} | {row['signal']} | {row['player']} | {row['market']} | {row['side']} | "
            f"{num(row['projection'], 3)} | {num(row['line'], 1)} | {num(row['best_price'], 2)} | {row['book']} | "
            f"{pct(row['ev_per_unit'])} | {num(row['stake_units'], 2)}u |"
        )

    lines.extend(
        [
            "",
            "## Detailed Markov Analysis",
            "",
            "Plain-English frame: does the adjusted model support the bet, does the probability still beat the market after smoothing, is the price good enough, and is the confidence high enough to survive Walters-style filtering?",
            "",
        ]
    )
    for row in portfolio:
        lines.extend(detailed_read(row, markov_lookup.get(key(row))))

    OUT.write_text("\n".join(lines).rstrip() + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
