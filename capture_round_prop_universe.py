#!/usr/bin/env python3
"""Archive and validate the full raw Odds API prop universe for a mapped AFL round."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ROUND_MAP = ROOT / "afl_round_mapping.csv"
LEDGER = ROOT / "aflplayerprops_bet_history.csv"
EVENTS_JSON = ROOT / "oddsapi_events.json"
ARCHIVE_ROOT = ROOT / "round_archives"

MARKET_LABELS = {
    "player_disposals": "Disposals",
    "player_tackles_over": "Tackles",
    "player_goals_scored_over": "Goals",
    "player_marks_over": "Marks",
    "player_afl_fantasy_points_over": "Ranking/Fantasy Pts",
}


def normalise_game(value: str) -> str:
    return " ".join((value or "").strip().split())


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def round_games(round_number: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for row in read_csv(ROUND_MAP):
        if row.get("round_number") != round_number:
            continue
        game = normalise_game(row.get("game", ""))
        commence = row.get("commence_time", "").strip()
        if not game or not commence:
            continue
        out.setdefault(game, set()).add(commence)
    return out


def ledger_keys(round_game_map: dict[str, set[str]]) -> set[tuple[str, str, str, str, str, str]]:
    keys: set[tuple[str, str, str, str, str, str]] = set()
    for row in read_csv(LEDGER):
        game = normalise_game(row.get("game", ""))
        commence = row.get("commence_time", "").strip()
        if game not in round_game_map or commence not in round_game_map[game]:
            continue
        keys.add(
            (
                game,
                commence,
                row.get("player", "").strip(),
                row.get("market", "").strip(),
                row.get("side", "").strip(),
                row.get("line", "").strip(),
            )
        )
    return keys


def prop_payload_paths(round_game_map: dict[str, set[str]]) -> list[Path]:
    matched: list[Path] = []
    for path in sorted(ROOT.glob("oddsapi_*_props.json")):
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        game = normalise_game(f"{payload.get('home_team', '')} v {payload.get('away_team', '')}")
        commence = str(payload.get("commence_time", "")).strip()
        if game in round_game_map and commence in round_game_map[game]:
            matched.append(path)
    return matched


def event_summary_rows(round_game_map: dict[str, set[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    matched_payloads = {path.name: path for path in prop_payload_paths(round_game_map)}

    expected_games = set(round_game_map)

    for path in sorted(matched_payloads.values()):
        payload = json.loads(path.read_text())
        game = normalise_game(f"{payload.get('home_team', '')} v {payload.get('away_team', '')}")
        commence = str(payload.get("commence_time", "")).strip()
        bookmakers = payload.get("bookmakers", [])
        if not isinstance(bookmakers, list):
            bookmakers = []
        market_count = sum(len(book.get("markets", [])) for book in bookmakers)
        outcome_count = sum(
            len(market.get("outcomes", []))
            for book in bookmakers
            for market in book.get("markets", [])
        )
        rows.append(
            {
                "game": game,
                "commence_time": commence,
                "source_file": path.name,
                "bookmakers_count": len(bookmakers),
                "markets_count": market_count,
                "outcomes_count": outcome_count,
                "empty_bookmakers": "True" if len(bookmakers) == 0 else "False",
            }
        )
        expected_games.discard(game)

    for game in sorted(expected_games):
        rows.append(
            {
                "game": game,
                "commence_time": sorted(round_game_map.get(game, {""}))[0] if round_game_map.get(game) else "",
                "source_file": "",
                "bookmakers_count": 0,
                "markets_count": 0,
                "outcomes_count": 0,
                "empty_bookmakers": "True",
            }
        )

    return rows


def capture_rows(round_game_map: dict[str, set[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str, str, str, str]] = set()
    for path in prop_payload_paths(round_game_map):
        payload = json.loads(path.read_text())
        game = normalise_game(f"{payload.get('home_team', '')} v {payload.get('away_team', '')}")
        commence = str(payload.get("commence_time", "")).strip()
        bookmakers = payload.get("bookmakers", [])
        if not isinstance(bookmakers, list):
            bookmakers = []
        for bookmaker in bookmakers:
            book = str(bookmaker.get("title", "")).strip()
            for market in bookmaker.get("markets", []):
                market_key = str(market.get("key", "")).strip()
                market_label = MARKET_LABELS.get(market_key, market_key)
                for outcome in market.get("outcomes", []):
                    player = str(outcome.get("description", "")).strip()
                    side = str(outcome.get("name", "")).strip()
                    line = outcome.get("point", "")
                    price = outcome.get("price", "")
                    key = (
                        game,
                        commence,
                        player,
                        market_label,
                        side,
                        str(line),
                        book,
                        str(price),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "game": game,
                            "commence_time": commence,
                            "player": player,
                            "market": market_label,
                            "side": side,
                            "line": line,
                            "book": book,
                            "price": price,
                            "source_file": path.name,
                            "market_key": market_key,
                            "book_last_update": bookmaker.get("last_update", ""),
                            "market_last_update": market.get("last_update", ""),
                        }
                    )
    return rows


def archive_round_fetch(round_number: str, stamp: str) -> Path:
    games = round_games(round_number)
    archive_dir = ARCHIVE_ROOT / f"round_{round_number}" / stamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    if EVENTS_JSON.exists():
        shutil.copy2(EVENTS_JSON, archive_dir / EVENTS_JSON.name)
    for path in prop_payload_paths(games):
        shutil.copy2(path, archive_dir / path.name)
    return archive_dir


def validate_round_capture(round_number: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    games = round_games(round_number)
    summaries = event_summary_rows(games)
    raw_rows = capture_rows(games)
    ledger_match_keys = ledger_keys(games)

    missing_from_ledger: list[dict[str, Any]] = []
    for row in raw_rows:
        key = (
            row["game"],
            row["commence_time"],
            row["player"],
            row["market"],
            row["side"],
            str(row["line"]),
        )
        row["round_number"] = round_number
        row["captured_in_ledger"] = "True" if key in ledger_match_keys else "False"
        if key not in ledger_match_keys:
            missing_from_ledger.append(row)

    errors: list[str] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in summaries:
        grouped.setdefault(str(row["game"]), []).append(row)

    empty_games = []
    missing_games = []
    for game, group in grouped.items():
        has_payload = any(bool(row["source_file"]) for row in group)
        has_books = any(int(row["bookmakers_count"]) > 0 for row in group)
        if not has_payload:
            missing_games.append(group[0])
        elif not has_books:
            empty_games.append(group[0])

    if empty_games:
        game_list = ", ".join(f"{row['game']} ({row['commence_time']})" for row in empty_games)
        errors.append(f"Mapped round {round_number} games returned empty bookmaker payloads: {game_list}")

    if missing_games:
        game_list = ", ".join(f"{row['game']} ({row['commence_time']})" for row in missing_games)
        errors.append(f"Mapped round {round_number} games were missing local prop payload files: {game_list}")

    return summaries, missing_from_ledger, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--round", required=True, dest="round_number")
    parser.add_argument("--output", type=Path, default=ROOT / "round_prop_universe.csv")
    parser.add_argument("--missing-output", type=Path, default=ROOT / "round_prop_universe_missing_from_ledger.csv")
    parser.add_argument("--summary-output", type=Path, default=ROOT / "round_prop_capture_summary.csv")
    parser.add_argument("--archive-stamp", default="")
    parser.add_argument("--fail-on-empty", action="store_true")
    args = parser.parse_args()

    games = round_games(args.round_number)
    if not games:
        raise SystemExit(f"No games mapped for round {args.round_number}")

    if args.archive_stamp:
        archive_dir = archive_round_fetch(args.round_number, args.archive_stamp)
        print(f"Archived raw fetch to {archive_dir}")

    summaries, missing, errors = validate_round_capture(args.round_number)
    captured = capture_rows(games)
    for row in captured:
        row["round_number"] = args.round_number

    ledger_match_keys = ledger_keys(games)
    for row in captured:
        key = (
            row["game"],
            row["commence_time"],
            row["player"],
            row["market"],
            row["side"],
            str(row["line"]),
        )
        row["captured_in_ledger"] = "True" if key in ledger_match_keys else "False"

    fieldnames = [
        "round_number",
        "game",
        "commence_time",
        "player",
        "market",
        "side",
        "line",
        "book",
        "price",
        "captured_in_ledger",
        "source_file",
        "market_key",
        "book_last_update",
        "market_last_update",
    ]
    write_csv(args.output, captured, fieldnames)
    write_csv(args.missing_output, missing, fieldnames)
    write_csv(
        args.summary_output,
        summaries,
        [
            "game",
            "commence_time",
            "source_file",
            "bookmakers_count",
            "markets_count",
            "outcomes_count",
            "empty_bookmakers",
        ],
    )

    by_game = Counter(row["game"] for row in captured)
    missing_by_game = Counter(row["game"] for row in missing)
    print(f"Captured {len(captured)} raw prop rows for round {args.round_number}")
    for game in sorted({row['game'] for row in summaries} | set(by_game)):
        total = by_game.get(game, 0)
        missing_count = missing_by_game.get(game, 0)
        print(f"{game}: {total} rows, {missing_count} not in ledger")
    print(args.output)
    print(args.missing_output)
    print(args.summary_output)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        if args.fail_on_empty:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
