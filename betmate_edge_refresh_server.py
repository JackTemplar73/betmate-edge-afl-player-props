#!/usr/bin/env python3
"""Local refresh service for BetMate Edge AFL player props reports."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import capture_round_prop_universe as round_capture

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("BETMATE_REFRESH_HOST", "127.0.0.1")
PORT = int(os.environ.get("BETMATE_REFRESH_PORT", "8765"))
SPORT_KEY = "aussierules_afl"
REGIONS = "au"
MARKETS = ",".join(
    [
        "player_disposals",
        "player_tackles_over",
        "player_goals_scored_over",
        "player_afl_fantasy_points_over",
    ]
)

TEAM_CODES = {
    "Adelaide Crows": "ade",
    "Brisbane Lions": "bris",
    "Carlton Blues": "car",
    "Collingwood Magpies": "coll",
    "Essendon Bombers": "ess",
    "Fremantle Dockers": "fre",
    "Geelong Cats": "gee",
    "Gold Coast Suns": "gc",
    "Greater Western Sydney Giants": "gws",
    "Hawthorn Hawks": "haw",
    "Melbourne Demons": "melb",
    "North Melbourne Kangaroos": "nm",
    "Port Adelaide Power": "port",
    "Richmond Tigers": "rich",
    "St Kilda Saints": "stk",
    "Sydney Swans": "syd",
    "West Coast Eagles": "wce",
    "Western Bulldogs": "wb",
}

WHEELO_URLS = {
    "wheelo_player_stats_2026.json": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json",
    "wheelo_player_stats_last5.json": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json",
    "wheelo_player_stats_last10.json": "https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json",
    "wheelo_team_stats_2026.json": "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/2026.json",
    "wheelo_team_stats_last5.json": "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last5.json",
    "wheelo_team_stats_last10.json": "https://www.wheeloratings.com/src/afl_stats/team_stats/afl/last10.json",
}

SCORED_CSV = ROOT / "oddsapi_wheelo_ev_qi.csv"
LEDGER_CSV = ROOT / "aflplayerprops_bet_history.csv"
EVENTS_JSON = ROOT / "oddsapi_events.json"
PLAYER_PACK_CSV = ROOT / "wheelo_today_player_pack.csv"
MATCH_MAP_CSV = ROOT / "afl_match_mapping.csv"
ROUND_MAP_CSV = ROOT / "afl_round_mapping.csv"
TEAM_DISPLAY_NAMES = {
    "Adelaide Crows": "Adelaide",
    "Brisbane Lions": "Brisbane",
    "Carlton Blues": "Carlton",
    "Collingwood Magpies": "Collingwood",
    "Essendon Bombers": "Essendon",
    "Fremantle Dockers": "Fremantle",
    "Geelong Cats": "Geelong",
    "Gold Coast Suns": "Gold Coast",
    "Greater Western Sydney Giants": "Greater Western Sydney",
    "GWS Giants": "Greater Western Sydney",
    "Hawthorn Hawks": "Hawthorn",
    "Melbourne Demons": "Melbourne",
    "North Melbourne Kangaroos": "North Melbourne",
    "Port Adelaide Power": "Port Adelaide",
    "Richmond Tigers": "Richmond",
    "St Kilda Saints": "St Kilda",
    "Sydney Swans": "Sydney",
    "West Coast Eagles": "West Coast",
    "Western Bulldogs": "Western Bulldogs",
}


class RefreshState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.busy = False
        self.last_success_at = ""
        self.last_error = ""


STATE = RefreshState()


def refresh_token() -> str:
    value = os.environ.get("CODEX_REFRESH_TOKEN", "").strip()
    if value:
        return value

    token_file = ROOT / "codex_refresh_token.txt"
    if token_file.exists():
        value = token_file.read_text().strip()
        if value:
            return value
    return ""


def odds_api_key() -> str:
    for env_name in ("THE_ODDS_API_KEY", "ODDS_API_KEY"):
        value = os.environ.get(env_name)
        if value:
            return value

    key_file = ROOT / "odds_api_key.txt"
    if key_file.exists():
        value = key_file.read_text().strip()
        if value:
            return value

    raise RuntimeError("Odds API key not configured for refresh service.")


def fetch_bytes(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "BetMateEdgeRefresh/1.0",
            "Accept": "application/json,text/html,*/*",
        },
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def fetch_json(url: str) -> object:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def to_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def display_team(name: str) -> str:
    return TEAM_DISPLAY_NAMES.get(name, name)


def short_game_name(game: str) -> str:
    home, _, away = game.partition(" v ")
    return f"{display_team(home)} v {display_team(away)}"


def slug_part(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def event_game_key(home_team: str, away_team: str, commence_time: str) -> str:
    date_part = commence_time[:10].replace("-", "_") if commence_time else "unknown_date"
    return f"{team_code(home_team)}_v_{team_code(away_team)}_{date_part}"


def prop_key(game_key: str, row: dict[str, str], team_name: str) -> str:
    return "_".join(
        [
            game_key,
            slug_part(team_name),
            slug_part(row.get("player", "")),
            slug_part(row.get("market", "")),
            slug_part(row.get("side", "")),
            slug_part(str(row.get("line", ""))),
            slug_part(row.get("book", "")),
        ]
    )


def parse_commence(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def infer_status(commence_time: str, result: str) -> str:
    if result in {"WIN", "LOSS", "PUSH"}:
        return "COMPLETED"
    commence = parse_commence(commence_time)
    if commence is None:
        return "UPCOMING"
    now = datetime.now(timezone.utc)
    return "IN_PLAY" if now >= commence else "UPCOMING"


def infer_result(status: str, ledger_result: str) -> str:
    if ledger_result in {"WIN", "LOSS", "PUSH"}:
        return ledger_result
    if status == "IN_PLAY":
        return "IN PLAY"
    return ""


def load_round_lookup() -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    if not ROUND_MAP_CSV.exists():
        return lookup
    for row in read_csv_rows(ROUND_MAP_CSV):
        game = row.get("game", "").strip()
        commence = row.get("commence_time", "").strip()
        round_number = row.get("round_number", "").strip()
        if game and commence and round_number:
            lookup[(game, commence)] = round_number
            lookup.setdefault((game, ""), round_number)
    return lookup


def round_number_for_event(round_lookup: dict[tuple[str, str], str], game: str, commence: str) -> str:
    return round_lookup.get((game, commence), "") or round_lookup.get((game, ""), "")


def current_round_numbers(events: list[dict[str, object]]) -> list[str]:
    round_lookup = load_round_lookup()
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        game = f"{str(event.get('home_team', '')).strip()} v {str(event.get('away_team', '')).strip()}"
        commence = str(event.get("commence_time", "")).strip()
        round_number = round_number_for_event(round_lookup, game, commence)
        if round_number:
            counts[round_number] += 1
    return [round_number for round_number, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def archive_and_validate_round_capture(events: list[dict[str, object]], logs: list[str]) -> None:
    round_numbers = current_round_numbers(events)
    if not round_numbers:
        logs.append("Round capture guardrail skipped: no mapped round number matched current events.")
        return

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for round_number in round_numbers:
        archive_dir = round_capture.archive_round_fetch(round_number, stamp)
        summary_rows, missing_rows, errors = round_capture.validate_round_capture(round_number)
        round_games = round_capture.round_games(round_number)
        ledger_match_keys = round_capture.ledger_keys(round_games)
        captured_rows = round_capture.capture_rows(round_games)
        for row in captured_rows:
            row["round_number"] = round_number
            key = (
                row["game"],
                row["commence_time"],
                row["player"],
                row["market"],
                row["side"],
                str(row["line"]),
            )
            row["captured_in_ledger"] = "True" if key in ledger_match_keys else "False"

        round_capture.write_csv(
            ROOT / f"round{round_number}_prop_universe.csv",
            captured_rows,
            [
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
            ],
        )
        round_capture.write_csv(
            ROOT / f"round{round_number}_prop_universe_missing_from_ledger.csv",
            missing_rows,
            [
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
            ],
        )
        round_capture.write_csv(
            ROOT / f"round{round_number}_prop_capture_summary.csv",
            summary_rows,
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

        logs.append(
            f"Round {round_number} archive written: {archive_dir.name} with {len(summary_rows)} event summaries and {len(missing_rows)} missing-vs-ledger rows."
        )
        if errors:
            raise RuntimeError(" ; ".join(errors))


def current_round_label(events: list[dict[str, object]], override: str | None) -> str:
    if override:
        return override
    round_lookup = load_round_lookup()
    round_numbers = {
        round_number_for_event(round_lookup, str(event.get("game", "")), str(event.get("commenceTime", "")))
        for event in events
    }
    round_numbers.discard("")
    if len(round_numbers) == 1:
        return f"Round {next(iter(round_numbers))}"
    if round_numbers:
        ordered = sorted(round_numbers, key=lambda value: int(value) if value.isdigit() else value)
        return f"Round {ordered[-1]}"
    return "Current Round"


def load_event_metadata() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    events_raw = json.loads(EVENTS_JSON.read_text()) if EVENTS_JSON.exists() else []
    round_lookup = load_round_lookup()
    mapped_rounds = {
        round_number_for_event(
            round_lookup,
            f"{str(event.get('home_team', ''))} v {str(event.get('away_team', ''))}",
            str(event.get("commence_time", "")),
        )
        for event in events_raw
        if isinstance(event, dict)
    }
    mapped_rounds.discard("")
    target_round = ""
    if mapped_rounds:
        target_round = max(mapped_rounds, key=lambda value: int(value) if value.isdigit() else value)

    events: list[dict[str, object]] = []
    by_game_name: dict[str, dict[str, object]] = {}
    for sort_order, event in enumerate(sorted(events_raw, key=lambda item: item.get("commence_time", "")), start=1):
        if not isinstance(event, dict):
            continue
        home_team = str(event.get("home_team", ""))
        away_team = str(event.get("away_team", ""))
        commence_time = str(event.get("commence_time", ""))
        game_name = f"{home_team} v {away_team}"
        if target_round and round_number_for_event(round_lookup, game_name, commence_time) != target_round:
            continue
        event_record = {
            "game": game_name,
            "gameKey": event_game_key(home_team, away_team, commence_time),
            "displayName": short_game_name(game_name),
            "homeTeam": display_team(home_team),
            "awayTeam": display_team(away_team),
            "commenceTime": commence_time,
            "sortOrder": sort_order,
        }
        events.append(event_record)
        by_game_name[game_name] = event_record
    return events, by_game_name


def load_bookmaker_counts() -> dict[str, tuple[bool, int]]:
    counts: dict[str, tuple[bool, int]] = {}
    for path in ROOT.glob("oddsapi_*_props.json"):
        if "marks_probe" in path.name:
            continue
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        game_name = f"{payload.get('home_team')} v {payload.get('away_team')}"
        bookmakers = payload.get("bookmakers", [])
        if not isinstance(bookmakers, list):
            bookmakers = []
        counts[game_name] = (len(bookmakers) > 0, len(bookmakers))
    return counts


def load_ledger_lookup() -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    for row in read_csv_rows(LEDGER_CSV):
        key = (
            row.get("player", ""),
            row.get("market", ""),
            row.get("side", ""),
            row.get("line", ""),
            row.get("book", ""),
        )
        lookup[key] = row
    return lookup


def load_player_team_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in read_csv_rows(PLAYER_PACK_CSV):
        player = row.get("Player", "").strip().lower()
        team = display_team(row.get("Team", ""))
        if player and team:
            lookup[player] = team
    return lookup


def load_match_map() -> list[dict[str, str]]:
    return read_csv_rows(MATCH_MAP_CSV)


def settle_completed_games(current_round_games: set[str], logs: list[str]) -> None:
    now_utc = datetime.now(timezone.utc)
    settled_games = 0
    for mapping in load_match_map():
        game = mapping.get("game", "")
        if not game or game not in current_round_games:
            continue
        commence = parse_commence(mapping.get("commence_time", ""))
        if commence is None or commence + timedelta(hours=4) > now_utc:
            continue
        command = ["python3", "settle_player_props_from_wheelo.py", "--game", game, "--only-unsettled"]
        if mapping.get("afl_provider_match_id"):
            command.extend(["--afl-match-id", mapping["afl_provider_match_id"]])
        elif mapping.get("afl_match_url"):
            command.extend(["--afl-match-url", mapping["afl_match_url"]])
        elif mapping.get("afl_match_id"):
            command.extend(["--afl-match-id", mapping["afl_match_id"]])
        else:
            logs.append(f"Skipped settlement for {game}: no AFL match reference in afl_match_mapping.csv")
            continue
        try:
            run_local_command(command, logs)
            run_local_command(
                ["python3", "aflplayerprops_history.py", "settle", "--settlement", "player_prop_settlement.csv"],
                logs,
            )
            settled_games += 1
        except RuntimeError as exc:
            message = str(exc)
            if "No unsettled ledger rows remain" in message:
                logs.append(f"Settlement skipped for {game}: already settled.")
                continue
            raise
    if settled_games:
        logs.append(f"Official AFL settlement refreshed for {settled_games} completed mapped games")


def build_payload(min_qi: float, high_value_min_price: float, round_override: str | None) -> dict[str, object]:
    scored_rows = read_csv_rows(SCORED_CSV)
    ledger_lookup = load_ledger_lookup()
    player_team_lookup = load_player_team_lookup()
    event_rows, event_by_game = load_event_metadata()
    bookmaker_counts = load_bookmaker_counts()
    round_label = current_round_label(event_rows, round_override)

    games: list[dict[str, object]] = []
    for event in event_rows:
        game_name = str(event["game"])
        has_live_books, bookmakers_count = bookmaker_counts.get(game_name, (False, 0))
        games.append(
            {
                "gameKey": event["gameKey"],
                "displayName": event["displayName"],
                "homeTeam": event["homeTeam"],
                "awayTeam": event["awayTeam"],
                "commenceTime": event["commenceTime"],
                "sortOrder": event["sortOrder"],
                "hasLiveBooks": has_live_books,
                "bookmakersCount": bookmakers_count,
            }
        )

    props: list[dict[str, object]] = []
    for row in scored_rows:
        if row.get("matched_wheelo") != "True":
            continue
        market = row.get("market", "")
        if market not in {"Disposals", "Tackles", "Goals"}:
            continue
        qi = to_float(row.get("live_qi"))
        ev = to_float(row.get("ev_per_unit"))
        price = to_float(row.get("best_price"))
        if qi is None or qi < min_qi or ev is None or ev <= 0 or price is None or price <= 0:
            continue
        segment = "High Value Props" if price >= high_value_min_price else "Multi Props Only"
        game_name = row.get("game", "")
        event = event_by_game.get(game_name)
        if event is None:
            continue
        player_name = row.get("player", "")
        team_name = player_team_lookup.get(player_name.strip().lower(), "")
        if not team_name:
            home_team = game_name.partition(" v ")[0]
            team_name = display_team(home_team)
        key = (
            row.get("player", ""),
            row.get("market", ""),
            row.get("side", ""),
            row.get("line", ""),
            row.get("book", ""),
        )
        ledger_row = ledger_lookup.get(key, {})
        status = infer_status(str(event["commenceTime"]), ledger_row.get("result", ""))
        result = infer_result(status, ledger_row.get("result", ""))
        stake = to_float(row.get("stake_units"))
        if stake is None or stake <= 0:
            stake = 0.0
        thorp_bankroll_pct = to_float(row.get("thorp_bankroll_pct"))
        thorp_full_kelly_pct = to_float(row.get("thorp_full_kelly_pct"))
        thorp_kelly_fraction = to_float(row.get("thorp_kelly_fraction"))
        props.append(
            {
                "propKey": prop_key(str(event["gameKey"]), row, team_name),
                "roundLabel": round_label,
                "gameKey": event["gameKey"],
                "commenceTime": event["commenceTime"],
                "team": team_name,
                "player": player_name,
                "market": market,
                "side": row.get("side", ""),
                "modelLine": safe_int(to_float(row.get("projection"))),
                "marketLine": to_float(row.get("line")),
                "modelProb": to_float(row.get("model_probability")),
                "price": price,
                "bookie": row.get("book", ""),
                "probEdge": to_float(row.get("model_edge")),
                "stake": round(stake, 2),
                "stakeBankrollPct": round(thorp_bankroll_pct, 2) if thorp_bankroll_pct is not None else None,
                "fullKellyPct": round(thorp_full_kelly_pct, 2) if thorp_full_kelly_pct is not None else None,
                "kellyFraction": round(thorp_kelly_fraction, 4) if thorp_kelly_fraction is not None else None,
                "allocationModel": "Thorp fractional Kelly",
                "allocationNote": row.get("thorp_allocation_note", ""),
                "qi": safe_int(qi),
                "segment": segment,
                "status": status,
                "result": result,
                "sourceSelection": row.get("portfolio_selection") or "TRACKED",
            }
        )

    props.sort(key=lambda item: (-int(item["qi"] or 0), -(item["probEdge"] or 0), str(item["player"])))
    high_value_count = sum(1 for row in props if row["segment"] == "High Value Props")
    multi_only_count = sum(1 for row in props if row["segment"] == "Multi Props Only")
    top_qi = max((int(row["qi"] or 0) for row in props), default=0)
    return {
        "roundLabel": round_label,
        "games": games,
        "props": props,
        "summary": {
            "gamesCount": len(games),
            "propsCount": len(props),
            "highValueCount": high_value_count,
            "multiOnlyCount": multi_only_count,
            "topQi": top_qi,
        },
    }


def team_code(team_name: str) -> str:
    code = TEAM_CODES.get(team_name)
    if code:
        return code
    parts = "".join(ch.lower() if ch.isalnum() else " " for ch in team_name).split()
    return "".join(parts[:2])[:8] or "game"


def fetch_wheelo_snapshot(logs: list[str]) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "wheelo_snapshots" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in WHEELO_URLS.items():
        write_bytes(out_dir / filename, fetch_bytes(url))
    source_lines = [f"Captured: {stamp}", "Sources:"] + [f"- {url}" for url in WHEELO_URLS.values()]
    (out_dir / "SOURCE.txt").write_text("\n".join(source_lines) + "\n")
    logs.append(f"Wheelo snapshot refreshed: {stamp}")

    preview_url = "https://www.wheeloratings.com/afl_match_previews.html"
    write_bytes(ROOT / "wheelo_match_previews.html", fetch_bytes(preview_url))
    logs.append("Wheelo match previews refreshed")


def fetch_oddsapi(logs: list[str]) -> list[dict[str, object]]:
    api_key = odds_api_key()
    events_url = (
        f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events?"
        + urlencode({"apiKey": api_key})
    )
    events = fetch_json(events_url)
    if not isinstance(events, list):
        raise RuntimeError("Odds API events response was not a list.")

    events_path = ROOT / "oddsapi_events.json"
    events_path.write_text(json.dumps(events, separators=(",", ":")))
    logs.append(f"Odds API events refreshed: {len(events)} games")

    prop_count = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id", "")).strip()
        if not event_id:
            continue
        home_team = str(event.get("home_team", "")).strip()
        away_team = str(event.get("away_team", "")).strip()
        filename = f"oddsapi_{team_code(home_team)}_{team_code(away_team)}_props.json"
        odds_url = (
            f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events/{event_id}/odds?"
            + urlencode(
                {
                    "apiKey": api_key,
                    "regions": REGIONS,
                    "markets": MARKETS,
                    "oddsFormat": "decimal",
                }
            )
        )
        payload = fetch_bytes(odds_url)
        write_bytes(ROOT / filename, payload)
        prop_count += 1
    logs.append(f"Odds API props refreshed: {prop_count} event files")
    return [event for event in events if isinstance(event, dict)]


def run_local_command(args: list[str], logs: list[str]) -> None:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    command_label = " ".join(args)
    if completed.stdout.strip():
        logs.append(f"$ {command_label}\n{completed.stdout.strip()}")
    else:
        logs.append(f"$ {command_label}")
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "Command failed."
        raise RuntimeError(f"{command_label} failed: {stderr}")


def refresh_pipeline(
    game: str | None,
    output: str | None,
    min_qi: float,
    high_value_min_price: float,
    round_label_override: str | None,
) -> dict[str, object]:
    logs: list[str] = []
    fetch_wheelo_snapshot(logs)
    events = fetch_oddsapi(logs)
    archive_and_validate_round_capture(events, logs)
    current_round_games = {
        f"{str(event.get('home_team', ''))} v {str(event.get('away_team', ''))}"
        for event in events
        if isinstance(event, dict)
    }
    run_local_command(["python3", "extract_wheelo_today_pack.py"], logs)
    run_local_command(["python3", "score_oddsapi_wheelo_props.py"], logs)
    run_local_command(["python3", "aflplayerprops_history.py", "update-clv"], logs)
    run_local_command(
        ["python3", "aflplayerprops_history.py", "track-qi", "--min-qi", "80", "--min-ev", "0"],
        logs,
    )
    settle_completed_games(current_round_games, logs)
    run_local_command(["python3", "build_walters_summary_html.py"], logs)

    if output:
        command = ["python3", "build_walters_summary_html.py"]
        if game:
            command.extend(["--game", game])
        command.extend(["--output", output])
        run_local_command(command, logs)

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = build_payload(min_qi, high_value_min_price, round_label_override)
    logs.append(
        f"Serialized {payload['summary']['propsCount']} props across {payload['summary']['gamesCount']} games for Base44"
    )
    return {
        "ok": True,
        "updated_at": updated_at,
        "roundLabel": payload["roundLabel"],
        "games": payload["games"],
        "props": payload["props"],
        "summary": payload["summary"],
        "logs": logs,
    }


class RefreshHandler(BaseHTTPRequestHandler):
    server_version = "BetMateEdgeRefresh/1.0"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/health":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
            return
        self.send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "busy": STATE.busy,
                "last_success_at": STATE.last_success_at,
                "last_error": STATE.last_error,
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/refresh":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
            return

        expected_token = refresh_token()
        if expected_token:
            auth_header = self.headers.get("Authorization", "")
            if auth_header != f"Bearer {expected_token}":
                self.send_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "Unauthorized"})
                return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw_body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            payload = {}

        if not STATE.lock.acquire(blocking=False):
            self.send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "Refresh already running."})
            return

        STATE.busy = True
        try:
            result = refresh_pipeline(
                payload.get("game"),
                payload.get("output"),
                float(payload.get("minQi", 80) or 80),
                float(payload.get("highValueMinPrice", 1.8) or 1.8),
                payload.get("roundLabelOverride"),
            )
            STATE.last_success_at = str(result.get("updated_at", ""))
            STATE.last_error = ""
            self.send_json(HTTPStatus.OK, result)
        except Exception as exc:  # noqa: BLE001
            STATE.last_error = str(exc)
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
        finally:
            STATE.busy = False
            STATE.lock.release()

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RefreshHandler)
    print(f"BetMate Edge refresh server listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
