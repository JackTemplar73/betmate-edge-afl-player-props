#!/usr/bin/env python3
"""Extract today's AFL player-prop inputs directly from WheeloRatings."""

from __future__ import annotations

import csv
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PREVIEW_HTML = ROOT / "wheelo_match_previews.html"
EVENTS_JSON = ROOT / "oddsapi_events.json"
ROUND_MAP = ROOT / "afl_round_mapping.csv"
TEAM_STATS_FILES = {
    "season": "wheelo_team_stats_2026.json",
    "last5": "wheelo_team_stats_last5.json",
    "last10": "wheelo_team_stats_last10.json",
}
PLAYER_FIELDS = [
    "Team",
    "Player",
    "Position",
    "PredictedRating",
    "RatingPoints_Avg",
    "TimeOnGround",
    "Disposals",
    "Marks",
    "Tackles",
    "Goals_Total",
    "Goals_Avg",
    "Inside50s",
    "Rebound50s",
    "MetresGained",
    "TotalClearances",
    "IsSelected",
]
TEAM_FIELDS = [
    "RatingPoints",
    "Disposals",
    "Marks",
    "Tackles",
    "Goals",
    "Inside50s",
    "Clearances",
    "CentreClearances",
    "StoppageClearances",
    "PressureActs",
    "MetresGained",
]
TEAM_NAME_MAP = {
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


def latest_snapshot_dir() -> Path:
    base = ROOT / "wheelo_snapshots"
    candidates = sorted(
        path for path in base.iterdir()
        if path.is_dir() and (path / "wheelo_team_stats_2026.json").exists()
    )
    if not candidates:
        raise RuntimeError(f"No Wheelo snapshot directories found in {base}")
    return candidates[-1]


def clean(value: Any) -> Any:
    if value in ("NA", "", None):
        return None
    return value


def to_float(value: Any) -> float | None:
    value = clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def js_object(html: str, name: str) -> dict[str, Any]:
    pattern = rf"{name}\s*=\s*(\{{.*?\}})\s*</script>"
    match = re.search(pattern, html, flags=re.S)
    if not match:
        raise RuntimeError(f"Could not find {name} in {PREVIEW_HTML}")
    return json.loads(match.group(1))


def upcoming_teams(match_summary: dict[str, Any]) -> list[str]:
    if EVENTS_JSON.exists():
        events = json.loads(EVENTS_JSON.read_text())
        round_lookup: dict[tuple[str, str], str] = {}
        if ROUND_MAP.exists():
            with ROUND_MAP.open() as f:
                for row in csv.DictReader(f):
                    game = row.get("game", "").strip()
                    commence = row.get("commence_time", "").strip()
                    round_number = row.get("round_number", "").strip()
                    if game and commence and round_number:
                        round_lookup[(game, commence)] = round_number
                        round_lookup.setdefault((game, ""), round_number)

        def round_number_for_event(game: str, commence: str) -> str:
            return round_lookup.get((game, commence), "") or round_lookup.get((game, ""), "")

        mapped_rounds: list[str] = []
        for event in events:
            game = f"{event.get('home_team', '')} v {event.get('away_team', '')}"
            commence = str(event.get("commence_time", ""))
            round_number = round_number_for_event(game, commence)
            if round_number:
                mapped_rounds.append(round_number)

        target_round = ""
        if mapped_rounds:
            target_round = max(mapped_rounds, key=lambda value: int(value) if value.isdigit() else value)

        teams: list[str] = []
        for event in sorted(events, key=lambda row: row.get("commence_time", "")):
            game = f"{event.get('home_team', '')} v {event.get('away_team', '')}"
            commence = str(event.get("commence_time", ""))
            if target_round:
                if round_number_for_event(game, commence) != target_round:
                    continue
            for raw in (event.get("home_team"), event.get("away_team")):
                team = TEAM_NAME_MAP.get(str(raw), str(raw))
                if team and team not in teams:
                    teams.append(team)
        if teams:
            return teams

    teams: list[str] = []
    for home, away in zip(match_summary["Home"], match_summary["Away"]):
        for team in (home, away):
            if team not in teams:
                teams.append(team)
        if len(teams) >= 4:
            break
    return teams


def explode_player_rows(player_stats: dict[str, Any], today_teams: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for team in today_teams:
        if team not in player_stats:
            continue
        table = player_stats[team]["data"][0]
        count = len(table["Player"])
        for i in range(count):
            row = {"Team": team}
            for field in PLAYER_FIELDS:
                if field == "Team":
                    continue
                if field == "Goals_Avg":
                    row[field] = None
                    continue
                row[field] = clean(table.get(field, [None] * count)[i])
            goals = to_float(row.get("Goals_Total"))
            matches = to_float(table.get("Matches", [None] * count)[i])
            row["Goals_Avg"] = round(goals / matches, 3) if goals is not None and matches else None
            if int(row.get("IsSelected") or 0) == 1:
                rows.append(row)
    return rows


def load_team_stats(today_teams: list[str], snapshot_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {team: {} for team in today_teams}
    for label, path in TEAM_STATS_FILES.items():
        payload = json.loads((snapshot_dir / path).read_text())
        table = payload["Data"]
        for team in today_teams:
            idx = table["Team"].index(team)
            stats = {}
            for field in TEAM_FIELDS:
                values = table.get(field)
                stats[field] = clean(values[idx]) if values and idx < len(values) else None
            out[team][label] = stats
    return out


def write_players(rows: list[dict[str, Any]]) -> None:
    path = ROOT / "wheelo_today_player_pack.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PLAYER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_team_stats(team_stats: dict[str, dict[str, dict[str, Any]]]) -> None:
    path = ROOT / "wheelo_today_team_context.csv"
    fields = ["Team", "Window", *TEAM_FIELDS]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for team, windows in team_stats.items():
            for window, stats in windows.items():
                writer.writerow({"Team": team, "Window": window, **stats})


def top(rows: list[dict[str, Any]], field: str, n: int = 5) -> list[dict[str, Any]]:
    return sorted(
        [row for row in rows if to_float(row.get(field)) is not None],
        key=lambda row: to_float(row[field]) or -999,
        reverse=True,
    )[:n]


def fmt(value: Any, digits: int = 1) -> str:
    value = to_float(value)
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def write_report(
    rows: list[dict[str, Any]],
    match_summary: dict[str, Any],
    team_stats: dict[str, dict[str, dict[str, Any]]],
    today_teams: list[str],
    snapshot_dir: Path,
) -> None:
    lines: list[str] = []
    lines.append("# WheeloRatings Today Player Prop Pack")
    lines.append("")
    lines.append("Source: https://www.wheeloratings.com/afl_match_previews.html")
    lines.append(f"Snapshot: wheelo_snapshots/{snapshot_dir.name}")
    lines.append("")
    lines.append("## Today Matches In Wheelo Match Summary")
    for i, match_no in enumerate(match_summary["MatchNumber"]):
        home = match_summary["Home"][i]
        away = match_summary["Away"][i]
        if home in today_teams or away in today_teams:
            lines.append(f"- Match {match_no}: {home} v {away}")
    lines.append("")
    lines.append("## Selected Player Shortlist")
    for team in today_teams:
        team_rows = [row for row in rows if row["Team"] == team]
        lines.append(f"### {team}")
        lines.append(f"Selected players in Wheelo preview: {len(team_rows)}")
        lines.append("")
        lines.append("| Player | Pos | PredRtg | RatingAvg | Disp | Marks | Tackles | GoalsAvg | TOG |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in top(team_rows, "PredictedRating", 10):
            lines.append(
                f"| {row['Player']} | {row.get('Position') or '-'} | {fmt(row['PredictedRating'], 2)} | "
                f"{fmt(row['RatingPoints_Avg'], 1)} | {fmt(row['Disposals'], 1)} | {fmt(row['Marks'], 1)} | "
                f"{fmt(row['Tackles'], 1)} | {fmt(row['Goals_Avg'], 2)} | {fmt(row['TimeOnGround'], 1)} |"
            )
        lines.append("")
        season = team_stats[team]["season"]
        last5 = team_stats[team]["last5"]
        lines.append(
            f"Team context: season disposals {fmt(season.get('Disposals'), 1)}, marks {fmt(season.get('Marks'), 1)}, "
            f"tackles {fmt(season.get('Tackles'), 1)}; last5 disposals {fmt(last5.get('Disposals'), 1)}, "
            f"marks {fmt(last5.get('Marks'), 1)}, tackles {fmt(last5.get('Tackles'), 1)}."
        )
        lines.append("")
    lines.append("## Market Driver Leaders")
    for field in ["Disposals", "Marks", "Tackles", "Goals_Avg", "RatingPoints_Avg"]:
        lines.append(f"### {field}")
        for row in top(rows, field, 12):
            lines.append(f"- {row['Player']} ({row['Team']}): {fmt(row[field], 1)}")
        lines.append("")
    (ROOT / "wheelo_today_player_pack.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    snapshot_dir = latest_snapshot_dir()
    html = PREVIEW_HTML.read_text()
    player_stats = js_object(html, "playerStatsData")
    match_summary = js_object(html, "matchSummary")
    today_teams = [team for team in upcoming_teams(match_summary) if team in player_stats]
    rows = explode_player_rows(player_stats, today_teams)
    team_stats = load_team_stats(today_teams, snapshot_dir)
    write_players(rows)
    write_team_stats(team_stats)
    write_report(rows, match_summary, team_stats, today_teams, snapshot_dir)
    print(f"Selected player rows: {len(rows)}")
    print(f"Teams: {', '.join(today_teams)}")
    print(f"Snapshot: {snapshot_dir.name}")
    print("Wrote wheelo_today_player_pack.csv")
    print("Wrote wheelo_today_team_context.csv")
    print("Wrote wheelo_today_player_pack.md")


if __name__ == "__main__":
    main()
