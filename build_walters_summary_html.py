#!/usr/bin/env python3
"""Build a Walters-style HTML summary report for the current portfolio card."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import score_oddsapi_wheelo_props as scorer


ROOT = Path(__file__).resolve().parent
SCORED = ROOT / "oddsapi_wheelo_ev_qi.csv"
MARKOV = ROOT / "markov_bet_justifications.csv"
LEDGER = ROOT / "aflplayerprops_bet_history.csv"
OUT = ROOT / "afl_player_props_walters_report.html"
PLAYER_PACK = ROOT / "wheelo_today_player_pack.csv"
ROUND_MAP = ROOT / "afl_round_mapping.csv"
TOKEN_FILE = ROOT / "codex_refresh_token.txt"

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


def to_float(value: str) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def refresh_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return ""


def num(value: str | float | None, digits: int = 1) -> str:
    if value in ("", None):
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def whole_num(value: str | float | None) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return str(int(round(number)))


def pct(value: str | float | None) -> str:
    if value in ("", None):
        return "-"
    try:
        return f"{100 * float(value):.1f}%"
    except (TypeError, ValueError):
        return "-"


def pct_gap(value: str | float | None) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{100 * number:.1f}%"


def fair_price(probability: str | float | None) -> str:
    prob = to_float(probability)
    if prob is None or prob <= 0:
        return "-"
    return f"{1 / prob:.2f}"


def pct_points(value: str | float | None) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{100 * number:+.1f}%"


def market_driver_label(market: str) -> str:
    if market == "Goals":
        return "finishing variance"
    if market == "Tackles":
        return "pressure volume"
    if market == "Disposals":
        return "role and possession flow"
    return "stat accumulation"


def qi_class(value: str | float | None) -> str:
    number = to_float(value)
    if number is None:
        return "qi-70"
    number = round(number)
    if number >= 95:
        return "qi-95"
    if number >= 90:
        return "qi-90"
    if number >= 85:
        return "qi-85"
    if number >= 80:
        return "qi-80"
    if number >= 75:
        return "qi-75"
    return "qi-70"


def qi_pill(value: str | float | None) -> str:
    return f'<span class="qi-pill {qi_class(value)}">{whole_num(value)}</span>'


def projection_state_label(row: dict[str, str]) -> str:
    support = str(row.get("wheelo_support", ""))
    if "strong support" in support.lower():
        return "Strong"
    if "lean support" in support.lower():
        return "Lean"
    if "neutral" in support.lower():
        return "Neutral"
    return "Against"


def probability_state_label(row: dict[str, str]) -> str:
    prob = to_float(row.get("model_probability")) or 0.0
    edge = to_float(row.get("model_edge")) or 0.0
    if edge >= 0.15 or prob >= 0.80:
        return "Dominant"
    if edge >= 0.06 or prob >= 0.65:
        return "Positive"
    if edge >= 0.02:
        return "Fair"
    return "Market low"


def price_state_label(row: dict[str, str]) -> str:
    ev = to_float(row.get("ev_per_unit")) or 0.0
    if ev >= 0.25:
        return "Mispriced"
    if ev >= 0.10:
        return "Good"
    if ev >= 0.03:
        return "Thin"
    return "No edge"


def confidence_state_label(row: dict[str, str]) -> str:
    qi = to_float(row.get("live_qi")) or 0.0
    if qi >= 90:
        return "Elite"
    if qi >= 80:
        return "High"
    if qi >= 70:
        return "Medium"
    return "Low"


def fallback_markov_path(row: dict[str, str]) -> str:
    return " -> ".join(
        [
            projection_state_label(row),
            probability_state_label(row),
            price_state_label(row),
            confidence_state_label(row),
        ]
    )


def stake_display_text(value: str | float | None, uncapped_game: bool) -> str:
    stake_value = to_float(value)
    if uncapped_game and (stake_value is None or stake_value <= 0):
        return "-"
    if stake_value is None:
        return "-"
    return f"{stake_value:.2f}u"


def resolved_stake_units(row: dict[str, str], uncapped_game: bool) -> str:
    stake_value = to_float(row.get("stake_units"))
    if stake_value is None or stake_value <= 0:
        stake_value = scorer.stake_units(row)
    return stake_display_text(stake_value, uncapped_game)


def model_line_display(value: str | float | None) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return str(int(round(number)))


def player_team(row: dict[str, str], player_teams: dict[str, str]) -> str:
    return player_teams.get(str(row.get("player", "")).strip().lower(), "")


def html_attr(value: str | None) -> str:
    return esc(value or "").replace('"', "&quot;")


def edge_source_text(row: dict[str, str], edge_pts: float) -> str:
    market = row.get("market", "")
    side = row.get("side", "")
    projection = to_float(row.get("projection")) or 0.0
    line = to_float(row.get("line")) or 0.0
    delta = to_float(row.get("projection_delta")) or 0.0

    gap = projection - line if side == "Over" else line - projection
    gap_text = f"{gap:.2f}"
    edge_text = f"{100 * edge_pts:.1f}"

    if market == "Goals":
        return (
            f"Scoring-rate edge: model sits {gap_text} goals through the line and shows a {edge_text}% probability edge. "
            f"{'Recent form is strengthening the scoring case.' if delta > 0.15 else 'This is mostly a baseline role/scoring-case, not a hot-streak bet.'}"
        )
    if market == "Tackles":
        return (
            f"Pressure-volume edge: model sits {gap_text} tackles through the line with a {edge_text}% probability edge. "
            f"{'Recent form is adding to the tackle case.' if delta > 0.2 else 'The edge is structural rather than recency-driven.'}"
        )
    if market == "Disposals":
        if side == "Under":
            return (
                f"Role/volume fade: model sits {gap_text} disposals below the line with a {edge_text}% probability edge. "
                f"{'Recent usage is weakening the player’s disposal case.' if delta < -0.2 else 'The under is being carried by the longer-run role baseline.'}"
            )
        return (
            f"Role/volume buy: model sits {gap_text} disposals above the line with a {edge_text}% probability edge. "
            f"{'Recent usage is lifting the disposal case.' if delta > 0.2 else 'The over is supported more by baseline role than recency.'}"
        )
    return (
        f"{market} {side.lower()} is being backed off a {gap_text} model cushion with a {edge_text}% probability edge. "
        f"The key driver is {market_driver_label(market)}."
    )


def bet_edge_text(row: dict[str, str]) -> str:
    market = row.get("market", "")
    side = row.get("side", "")
    projection = to_float(row.get("projection")) or 0.0
    line = to_float(row.get("line")) or 0.0
    rounded_projection = model_line_display(projection)
    if market == "Goals":
        return f"Model has this closer to {rounded_projection} goals than {num(line, 1)}, so the line is too low."
    if market == "Tackles":
        return f"Model has this closer to {rounded_projection} tackles than {num(line, 1)}, so the line is too low."
    if market == "Disposals" and side == "Under":
        return f"Model has this closer to {rounded_projection} disposals than {num(line, 1)}, so the line is too high."
    if market == "Disposals":
        return f"Model has this closer to {rounded_projection} disposals than {num(line, 1)}, so the line is too low."
    return f"Model projection of {rounded_projection} is off the market line of {num(line, 1)}."


def price_test_text(row: dict[str, str], fair: str, edge_pts: float) -> str:
    price = to_float(row.get("best_price")) or 0.0
    fair_num = to_float(fair)
    edge_text = f"{100 * edge_pts:.1f}%"
    if fair_num is None or fair_num <= 0:
        return f"Price check: market quote {price:.2f}. Fair price could not be resolved cleanly, but the model still shows a {edge_text} probability edge."
    overlay = price - fair_num
    if overlay >= 0.25:
        return f"Price check: fair is {fair_num:.2f}, market is {price:.2f}, so we are getting {overlay:.2f} of price overlay with a {edge_text} probability edge behind it."
    if overlay > 0:
        return f"Price check: fair is {fair_num:.2f}, market is {price:.2f}. The overlay is smaller at {overlay:.2f}, but the quote still sits on our side of fair with a {edge_text} probability edge."
    return f"Price check: market is close to fair ({fair_num:.2f} vs {price:.2f}); this play depends more on the model being right than on a big misprice."


def fair_line_text(row: dict[str, str], fair: str) -> str:
    fair_num = to_float(fair)
    price = to_float(row.get("best_price")) or 0.0
    if fair_num is None or fair_num <= 0:
        return f"Market is {price:.2f}. Fair price was not resolved cleanly."
    return f"We make it {fair_num:.2f}. Market is {price:.2f}."


def trigger_text(row: dict[str, str], edge_pts: float) -> str:
    market = row.get("market", "")
    side = row.get("side", "")
    projection = to_float(row.get("projection")) or 0.0
    line = to_float(row.get("line")) or 0.0
    delta = to_float(row.get("projection_delta")) or 0.0
    base = to_float(row.get("base_projection")) or 0.0
    edge = 100 * edge_pts
    shift = "up" if delta > 0 else "down"
    shift_mag = abs(delta)
    if market == "Goals":
        return (
            f"For this to hold, the player needs to keep a real scoring role. The adjusted goal projection is {model_line_display(projection)} off a {model_line_display(base)} base, "
            f"with the smoothing step moving {shift} by {shift_mag:.3f}. That still leaves a {edge:.1f}% probability edge after goal variance."
        )
    if market == "Tackles":
        return (
            f"For this to hold, the game needs enough contest and pressure for tackle volume to show up. The adjusted tackle projection is {model_line_display(projection)} from a {model_line_display(base)} base, "
            f"with the smoothing step moving {shift} by {shift_mag:.3f}. The remaining edge is {edge:.1f}%."
        )
    return (
        f"For this to hold, the player’s role and possession share need to stay intact. The adjusted projection is {model_line_display(projection)} from a {model_line_display(base)} base, "
        f"with smoothing moving {shift} by {shift_mag:.3f}. The remaining edge is {edge:.1f}%."
    )


def works_if_text(row: dict[str, str]) -> str:
    market = row.get("market", "")
    side = row.get("side", "")
    if market == "Goals":
        return "Prematch role, likely forward usage, and expected scoring opportunity all look intact."
    if market == "Tackles":
        return "Prematch role and expected contest profile point to enough pressure for tackle volume."
    if market == "Disposals" and side == "Under":
        return "Prematch role and expected ball flow do not point to a larger-than-normal disposal game."
    if market == "Disposals":
        return "Prematch role, likely minutes, and expected possession share support the over."
    return "Prematch role and expected game script support the bet."


def pass_if_text(row: dict[str, str], fair: str, risk: str) -> str:
    market = row.get("market", "")
    side = row.get("side", "")
    price = to_float(row.get("best_price")) or 0.0
    fair_num = to_float(fair)
    if fair_num is not None and fair_num > 0 and price <= fair_num:
        price_note = "price reaches fair or worse"
    elif fair_num is not None and fair_num > 0:
        price_note = f"price drops toward fair ({fair_num:.2f})"
    else:
        price_note = "price loses the current overlay"
    if risk:
        return f"Pass pregame if {risk.rstrip('.').lower()} or if the {price_note}."
    if market == "Goals":
        return f"Pass pregame if team news points to a weaker scoring role, expected forward opportunity looks thinner, or if the {price_note}."
    if market == "Tackles":
        return f"Pass pregame if the expected pressure role softens, the matchup no longer projects as contested, or if the {price_note}."
    if market == "Disposals" and side == "Under":
        return f"Pass pregame if team news suggests a bigger role, cleaner possession conditions, or if the {price_note}."
    if market == "Disposals":
        return f"Pass pregame if team news suggests a smaller role, reduced likely minutes, or if the {price_note}."
    return f"Pass pregame if role or expected script moves against the bet, or if the {price_note}."


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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


def load_player_teams() -> dict[str, str]:
    if not PLAYER_PACK.exists():
        return {}
    teams: dict[str, str] = {}
    with PLAYER_PACK.open() as f:
        for row in csv.DictReader(f):
            player = str(row.get("Player", "")).strip().lower()
            team = short_team_name(str(row.get("Team", "")).strip())
            if player and team and player not in teams:
                teams[player] = team
    return teams


def short_team_name(name: str) -> str:
    text = str(name or "").strip()
    return TEAM_NAME_MAP.get(text, text)


def short_game_name(game: str) -> str:
    if " v " not in str(game):
        return str(game)
    home, away = str(game).split(" v ", 1)
    return f"{short_team_name(home)} v {short_team_name(away)}"


def parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def display_date(value: str) -> str:
    dt = parse_utc(value)
    if dt is None:
        return "-"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def load_round_lookup() -> dict[tuple[str, str], str]:
    if not ROUND_MAP.exists():
        return {}
    lookup: dict[tuple[str, str], str] = {}
    with ROUND_MAP.open() as f:
        for row in csv.DictReader(f):
            game = row.get("game", "").strip()
            commence = row.get("commence_time", "").strip()
            round_number = row.get("round_number", "").strip()
            if game and commence and round_number:
                lookup[(game, commence)] = round_number
    return lookup


def game_sort_key(game: str, game_start_lookup: dict[str, datetime | None]) -> tuple[datetime, str]:
    start = game_start_lookup.get(game)
    if start is None:
        return (datetime.max.replace(tzinfo=timezone.utc), game)
    return (start, game)


def badge_class(signal: str) -> str:
    return {
        "A_BET": "a",
        "B_BET": "b",
        "LEAN": "lean",
        "PASS": "pass",
        "NO_MATCH": "pass",
    }.get(signal, "pass")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", default="", help="Optional exact game filter for a single-game report")
    p.add_argument("--output", type=Path, default=OUT, help="HTML output path")
    p.add_argument("--min-qi", type=float, default=70.0, help="Tracking threshold to show in the universe section")
    return p


def tracked_props_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p>No tracked props are currently in play or completed yet.</p>"
    rows = sorted(
        rows,
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(
                (to_float(row.get("model_probability")) or 0)
                - (to_float(row.get("market_probability")) or 0)
            ),
            row.get("player", ""),
        ),
    )
    player_teams = load_player_teams()
    out = [
        "<table><thead><tr>"
        "<th>QI</th><th>Team</th><th>Player</th><th>Market</th><th>Side</th><th>Model Line</th>"
        "<th>Market Line</th><th>Model Prob</th><th>Price</th><th>Bookie</th><th>Prob Edge</th><th>Stake</th>"
        "</tr></thead><tbody>"
    ]
    for row in rows:
        edge = (to_float(row.get("model_probability")) or 0) - (to_float(row.get("market_probability")) or 0)
        price = to_float(row.get("latest_price"))
        if price is None or price <= 0:
            price = to_float(row.get("bet_price"))
        out.append(
            f"<tr><td>{qi_pill(row.get('live_qi'))}</td><td>{esc(player_team(row, player_teams))}</td>"
            f"<td>{esc(row.get('player', ''))}</td><td>{esc(row.get('market', ''))}</td>"
            f"<td>{esc(row.get('side', ''))}</td><td>{num(row.get('line'), 1)}</td>"
            f"<td>{num(row.get('line'), 1)}</td><td>{pct(row.get('model_probability'))}</td>"
            f"<td>{num(price, 2)}</td><td>{esc(row.get('book', ''))}</td>"
            f"<td>{pct_gap(edge)}</td><td>{resolved_stake_units(row, False)}</td></tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def tracking_result_text(row: dict[str, str]) -> str:
    result = str(row.get("result", "")).strip().upper()
    status = str(row.get("status", "")).strip().upper()
    actual = str(row.get("actual", "")).strip()
    if result in {"WIN", "LOSS", "PUSH", "VOID", "HALF_WIN", "HALF_LOSS"}:
        return result if not actual else f"{result} ({actual})"
    if status == "SETTLED":
        return "SETTLED" if not actual else f"SETTLED ({actual})"
    if status == "OPEN":
        return "IN PLAY"
    if status == "TRACKED":
        return "TRACKING"
    return status or "-"


def tracking_tab_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p>No high-value props have started or completed yet.</p>"
    rows = sorted(
        rows,
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(
                (to_float(row.get("model_probability")) or 0)
                - (to_float(row.get("market_probability")) or 0)
            ),
            row.get("player", ""),
        ),
    )
    player_teams = load_player_teams()
    out = [
        "<table><thead><tr>"
        "<th>QI</th><th>Team</th><th>Player</th><th>Market</th><th>Side</th><th>Model Line</th>"
        "<th>Market Line</th><th>Model Prob</th><th>Bet Price</th><th>Latest Price</th><th>Bookie</th><th>Prob Edge</th><th>Stake</th><th>Result</th>"
        "</tr></thead><tbody>"
    ]
    for row in rows:
        edge = (to_float(row.get("model_probability")) or 0) - (to_float(row.get("market_probability")) or 0)
        bet_price = to_float(row.get("bet_price"))
        latest_price = to_float(row.get("latest_price"))
        if latest_price is None or latest_price <= 0:
            latest_price = bet_price
        out.append(
            f"<tr><td>{qi_pill(row.get('live_qi'))}</td><td>{esc(player_team(row, player_teams))}</td>"
            f"<td>{esc(row.get('player', ''))}</td><td>{esc(row.get('market', ''))}</td>"
            f"<td>{esc(row.get('side', ''))}</td><td>{num(row.get('line'), 1)}</td>"
            f"<td>{num(row.get('line'), 1)}</td><td>{pct(row.get('model_probability'))}</td>"
            f"<td>{num(bet_price, 2)}</td><td>{num(latest_price, 2)}</td><td>{esc(row.get('book', ''))}</td>"
            f"<td>{pct_gap(edge)}</td><td>{resolved_stake_units(row, False)}</td><td>{esc(tracking_result_text(row))}</td></tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def history_table(rows: list[dict[str, str]], round_lookup: dict[tuple[str, str], str]) -> str:
    if not rows:
        return "<p>No history rows yet.</p>"
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("commence_time", ""),
            -(to_float(row.get("live_qi")) or 0),
            row.get("player", ""),
        ),
        reverse=True,
    )
    player_teams = load_player_teams()
    out = [
        "<table><thead><tr>"
        "<th>Date</th><th>Round</th><th>QI</th><th>Team</th><th>Player</th><th>Market</th><th>Side</th><th>Model Line</th>"
        "<th>Market Line</th><th>Model Prob</th><th>Bet Price</th><th>Latest Price</th><th>Bookie</th><th>Prob Edge</th><th>Stake</th><th>Result</th>"
        "</tr></thead><tbody>"
    ]
    for row in rows:
        edge = (to_float(row.get("model_probability")) or 0) - (to_float(row.get("market_probability")) or 0)
        bet_price = to_float(row.get("bet_price"))
        latest_price = to_float(row.get("latest_price"))
        if latest_price is None or latest_price <= 0:
            latest_price = bet_price
        round_number = round_lookup.get((row.get("game", ""), row.get("commence_time", "")), "?")
        out.append(
            f"<tr><td>{esc(display_date(row.get('commence_time', '')))}</td><td>{esc(round_number)}</td>"
            f"<td>{qi_pill(row.get('live_qi'))}</td><td>{esc(player_team(row, player_teams))}</td>"
            f"<td>{esc(row.get('player', ''))}</td><td>{esc(row.get('market', ''))}</td>"
            f"<td>{esc(row.get('side', ''))}</td><td>{num(row.get('line'), 1)}</td>"
            f"<td>{num(row.get('line'), 1)}</td><td>{pct(row.get('model_probability'))}</td>"
            f"<td>{num(bet_price, 2)}</td><td>{num(latest_price, 2)}</td><td>{esc(row.get('book', ''))}</td>"
            f"<td>{pct_gap(edge)}</td><td>{resolved_stake_units(row, False)}</td><td>{esc(tracking_result_text(row))}</td></tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def grouped_history_sections(
    rows: list[dict[str, str]],
    round_lookup: dict[tuple[str, str], str],
    empty_message: str,
) -> str:
    if not rows:
        return f"<p>{esc(empty_message)}</p>"
    parts: list[str] = []
    for label, low, high in QI_GROUPS:
        band_rows = [
            row for row in rows
            if low <= round(to_float(row.get("live_qi")) or 0) <= high
        ]
        if not band_rows:
            continue
        parts.append(
            f'<section class="qi-group"><h4>{label}</h4>{history_table(band_rows, round_lookup)}</section>'
        )
    return "".join(parts) if parts else f"<p>{esc(empty_message)}</p>"


def qi_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p>No rows met the current QI threshold.</p>"
    rows = sorted(
        rows,
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(to_float(row.get("ev_per_unit")) or 0),
            row.get("player", ""),
        ),
    )
    player_teams = load_player_teams()
    out = [
        "<table><thead><tr>"
        "<th>QI</th><th>Team</th><th>Player</th><th>Market</th><th>Side</th><th>Model Line</th>"
        "<th>Market Line</th><th>Model Prob</th><th>Price</th><th>Bookie</th><th>Prob Edge</th><th>Stake</th>"
        "</tr></thead><tbody>"
    ]
    for row in rows:
        edge = (to_float(row.get("model_probability")) or 0) - (to_float(row.get("market_probability")) or 0)
        out.append(
            f"<tr><td>{qi_pill(row.get('live_qi'))}</td>"
            f"<td>{esc(player_team(row, player_teams))}</td><td>{esc(row.get('player', ''))}</td><td>{esc(row.get('market', ''))}</td>"
            f"<td>{esc(row.get('side', ''))}</td><td>{model_line_display(row.get('projection'))}</td>"
            f"<td>{num(row.get('line'), 1)}</td><td>{pct(row.get('model_probability'))}</td>"
            f"<td>{num(row.get('best_price'), 2)}</td><td>{esc(row.get('book', ''))}</td>"
            f"<td>{pct_gap(edge)}</td><td>{resolved_stake_units(row, False)}</td></tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


QI_GROUPS = [
    ("90-100 QI", 90, 100),
    ("85-89 QI", 85, 89),
    ("80-84 QI", 80, 84),
]


def grouped_qi_sections(rows: list[dict[str, str]], empty_message: str) -> str:
    if not rows:
        return f"<p>{esc(empty_message)}</p>"
    parts: list[str] = []
    for label, low, high in QI_GROUPS:
        band_rows = [
            row for row in rows
            if low <= round(to_float(row.get("live_qi")) or 0) <= high
        ]
        if not band_rows:
            continue
        parts.append(
            f'<section class="qi-group"><h4>{label}</h4>{qi_table(band_rows)}</section>'
        )
    return "".join(parts) if parts else f"<p>{esc(empty_message)}</p>"


def grouped_tracking_sections(rows: list[dict[str, str]], empty_message: str) -> str:
    if not rows:
        return f"<p>{esc(empty_message)}</p>"
    parts: list[str] = []
    for label, low, high in QI_GROUPS:
        band_rows = [
            row for row in rows
            if low <= round(to_float(row.get("live_qi")) or 0) <= high
        ]
        if not band_rows:
            continue
        parts.append(
            f'<section class="qi-group"><h4>{label}</h4>{tracking_tab_table(band_rows)}</section>'
        )
    return "".join(parts) if parts else f"<p>{esc(empty_message)}</p>"


def settled_result_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if str(row.get("result", "")).upper() in {"WIN", "LOSS", "PUSH"}]


def tracking_summary_cards(rows: list[dict[str, str]]) -> str:
    settled = settled_result_rows(rows)
    if not settled:
        return "<p>No settled results yet for this tracking window.</p>"
    wins = sum(1 for row in settled if row.get("result") == "WIN")
    losses = sum(1 for row in settled if row.get("result") == "LOSS")
    pushes = sum(1 for row in settled if row.get("result") == "PUSH")
    flat_profit = sum(to_float(row.get("flat_profit")) or 0.0 for row in settled)
    stake_profit = sum(to_float(row.get("stake_profit")) or 0.0 for row in settled)
    staked = sum((to_float(row.get("stake_units")) or 0.0) for row in settled if row.get("result") in {"WIN", "LOSS"})
    roi = stake_profit / staked if staked else 0.0
    return (
        '<section class="cards results-cards">'
        f'<div class="card"><strong>Betting Recap</strong>{wins}-{losses}-{pushes}</div>'
        f'<div class="card"><strong>Equal Bet Profit</strong>{flat_profit:+.2f}u</div>'
        f'<div class="card"><strong>Actual Profit</strong>{stake_profit:+.2f}u</div>'
        f'<div class="card"><strong>Actual ROI</strong>{roi:.1%}</div>'
        "</section>"
    )


def qi_band_results_table(rows: list[dict[str, str]]) -> str:
    settled = settled_result_rows(rows)
    if not settled:
        return "<p>No QI-band result summary yet.</p>"
    out = [
        "<table><thead><tr>"
        "<th>QI Band</th><th>Settled</th><th>W-L-P</th><th>Equal Bet Profit</th><th>Actual Profit</th><th>Actual ROI</th>"
        "</tr></thead><tbody>"
    ]
    total_wins = 0
    total_losses = 0
    total_pushes = 0
    total_flat_profit = 0.0
    total_stake_profit = 0.0
    total_staked = 0.0
    total_rows = 0
    for label, low, high in QI_GROUPS:
        band_rows = [
            row for row in settled
            if low <= round(to_float(row.get("live_qi")) or 0) <= high
        ]
        if not band_rows:
            continue
        wins = sum(1 for row in band_rows if row.get("result") == "WIN")
        losses = sum(1 for row in band_rows if row.get("result") == "LOSS")
        pushes = sum(1 for row in band_rows if row.get("result") == "PUSH")
        flat_profit = sum(to_float(row.get("flat_profit")) or 0.0 for row in band_rows)
        stake_profit = sum(to_float(row.get("stake_profit")) or 0.0 for row in band_rows)
        staked = sum((to_float(row.get("stake_units")) or 0.0) for row in band_rows if row.get("result") in {"WIN", "LOSS"})
        roi = stake_profit / staked if staked else 0.0
        total_rows += len(band_rows)
        total_wins += wins
        total_losses += losses
        total_pushes += pushes
        total_flat_profit += flat_profit
        total_stake_profit += stake_profit
        total_staked += staked
        out.append(
            f"<tr><td>{esc(label)}</td><td>{len(band_rows)}</td><td>{wins}-{losses}-{pushes}</td>"
            f"<td>{flat_profit:+.2f}u</td><td>{stake_profit:+.2f}u</td><td>{roi:.1%}</td></tr>"
        )
    total_roi = total_stake_profit / total_staked if total_staked else 0.0
    out.append(
        f"<tr><td><strong>Total</strong></td><td><strong>{total_rows}</strong></td>"
        f"<td><strong>{total_wins}-{total_losses}-{total_pushes}</strong></td>"
        f"<td><strong>{total_flat_profit:+.2f}u</strong></td>"
        f"<td><strong>{total_stake_profit:+.2f}u</strong></td>"
        f"<td><strong>{total_roi:.1%}</strong></td></tr>"
    )
    out.append("</tbody></table>")
    return "".join(out)


def best_worst_results(rows: list[dict[str, str]]) -> str:
    settled = settled_result_rows(rows)
    if not settled:
        return "<p>No best/worst props summary yet.</p>"
    player_teams = load_player_teams()
    staked_rows = [row for row in settled if abs(to_float(row.get("stake_profit")) or 0.0) > 0.0001]
    if not staked_rows:
        staked_rows = [row for row in settled if (to_float(row.get("stake_units")) or 0.0) > 0]
    wins = sorted(
        [row for row in staked_rows if row.get("result") == "WIN"],
        key=lambda row: (
            -(to_float(row.get("stake_profit")) or 0.0),
            -(to_float(row.get("live_qi")) or 0.0),
            row.get("player", ""),
        ),
    )[:5]
    losses = sorted(
        [row for row in staked_rows if row.get("result") == "LOSS"],
        key=lambda row: (
            to_float(row.get("stake_profit")) or 0.0,
            -(to_float(row.get("live_qi")) or 0.0),
            row.get("player", ""),
        ),
    )[:5]

    def render_list(title: str, subset: list[dict[str, str]], empty_text: str) -> str:
        if not subset:
            return f'<div class="result-list"><h4>{esc(title)}</h4><p>{esc(empty_text)}</p></div>'
        items = []
        for row in subset:
            stake_profit = to_float(row.get("stake_profit")) or 0.0
            items.append(
                "<li>"
                f"{esc(player_team(row, player_teams))} | {esc(row.get('player', ''))} "
                f"{esc(row.get('market', ''))} {esc(row.get('side', ''))} {num(row.get('line'), 1)} "
                f"at {esc(row.get('book', ''))} "
                f"<strong>{esc(str(row.get('result', '')))}</strong> "
                f"({esc(str(row.get('actual', '')))}), {stake_profit:+.2f}u"
                "</li>"
            )
        return f'<div class="result-list"><h4>{esc(title)}</h4><ul>{"".join(items)}</ul></div>'

    return (
        '<section class="results-grid">'
        + render_list("Best Props", wins, "No winners yet.")
        + render_list("Worst Props", losses, "No losses yet.")
        + "</section>"
    )


def settled_profit_points(rows: list[dict[str, str]], period: str) -> list[tuple[str, float]]:
    buckets: dict[str, float] = {}
    for row in settled_result_rows(rows):
        dt = parse_utc(row.get("commence_time", ""))
        if dt is None:
            continue
        dt = dt.astimezone(timezone.utc)
        if period == "week":
            iso = dt.isocalendar()
            label = f"{iso.year}-W{iso.week:02d}"
        else:
            label = dt.strftime("%Y-%m")
        buckets[label] = buckets.get(label, 0.0) + (to_float(row.get("stake_profit")) or 0.0)
    return sorted(buckets.items(), key=lambda item: item[0])


def profit_chart(title: str, rows: list[dict[str, str]], period: str) -> str:
    points = settled_profit_points(rows, period)
    if not points:
        return (
            '<section class="chart-card">'
            f"<h3>{esc(title)}</h3>"
            "<p>No settled profit history yet.</p>"
            "</section>"
        )

    width = 760
    height = 260
    left = 52
    right = 18
    top = 18
    bottom = 52
    plot_w = width - left - right
    plot_h = height - top - bottom

    profits = [value for _, value in points]
    min_val = min(0.0, min(profits))
    max_val = max(0.0, max(profits))
    if abs(max_val - min_val) < 1e-9:
        max_val += 1.0
        min_val -= 1.0
    span = max_val - min_val
    zero_y = top + ((max_val - 0.0) / span) * plot_h
    bar_gap = 12
    bar_w = max(20, int((plot_w - bar_gap * (len(points) - 1)) / max(len(points), 1)))
    total_profit = sum(profits)

    def y_for(value: float) -> float:
        return top + ((max_val - value) / span) * plot_h

    bars: list[str] = []
    for idx, (label, profit) in enumerate(points):
        x = left + idx * (bar_w + bar_gap)
        y = y_for(max(profit, 0.0))
        base_y = y_for(min(profit, 0.0))
        rect_y = min(y, base_y)
        rect_h = max(2.0, abs(base_y - y))
        fill = "#047857" if profit >= 0 else "#b91c1c"
        value_y = rect_y - 6 if profit >= 0 else rect_y + rect_h + 14
        bars.append(
            f'<rect x="{x:.1f}" y="{rect_y:.1f}" width="{bar_w:.1f}" height="{rect_h:.1f}" rx="6" fill="{fill}" opacity="0.88"></rect>'
            f'<text x="{x + bar_w / 2:.1f}" y="{value_y:.1f}" text-anchor="middle" class="chart-value">{profit:+.2f}u</text>'
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 22:.1f}" text-anchor="middle" class="chart-label">{esc(label)}</text>'
        )

    top_label = (
        f'<text x="{left - 8}" y="{top + 4}" text-anchor="end" class="chart-axis-label">{max_val:+.2f}u</text>'
        if abs(max_val) > 1e-9
        else ""
    )
    bottom_label = (
        f'<text x="{left - 8}" y="{height - bottom + 4}" text-anchor="end" class="chart-axis-label">{min_val:+.2f}u</text>'
        if abs(min_val) > 1e-9
        else ""
    )

    return (
        '<section class="chart-card">'
        f"<h3>{esc(title)}</h3>"
        f'<p class="chart-note">Actual profit from settled bets only. Total: <strong>{total_profit:+.2f}u</strong></p>'
        f'''
        <svg class="profit-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{html_attr(title)}">
          <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" class="chart-axis"></line>
          <line x1="{left}" y1="{zero_y:.1f}" x2="{width - right}" y2="{zero_y:.1f}" class="chart-zero"></line>
          <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" class="chart-axis"></line>
          {top_label}
          <text x="{left - 8}" y="{zero_y + 4:.1f}" text-anchor="end" class="chart-axis-label">0.00u</text>
          {bottom_label}
          {"".join(bars)}
        </svg>
        '''
        "</section>"
    )


def candidate_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "<p>No rows in this bucket.</p>"
    player_teams = load_player_teams()
    out = [
        "<table><thead><tr>"
        "<th>Rank</th><th>QI</th><th>Team</th><th>Player</th><th>Market</th><th>Side</th>"
        "<th>Model Line</th><th>Market Line</th><th>Model Prob</th><th>Price</th><th>Bookie</th><th>Prob Edge</th><th>Why Blocked</th>"
        "</tr></thead><tbody>"
    ]
    for row in rows:
        edge = (to_float(row.get("model_probability")) or 0) - (to_float(row.get("market_probability")) or 0)
        out.append(
            f"<tr><td>{esc(row.get('selection_rank', ''))}</td>"
            f"<td>{qi_pill(row.get('live_qi'))}</td>"
            f"<td>{esc(player_team(row, player_teams))}</td><td>{esc(row.get('player', ''))}</td><td>{esc(row.get('market', ''))}</td>"
            f"<td>{esc(row.get('side', ''))}</td><td>{model_line_display(row.get('projection'))}</td>"
            f"<td>{num(row.get('line'), 1)}</td><td>{pct(row.get('model_probability'))}</td>"
            f"<td>{num(row.get('best_price'), 2)}</td><td>{esc(row.get('book', ''))}</td>"
            f"<td>{pct_gap(edge)}</td><td>{esc(row.get('why_not_selected', ''))}</td></tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def main() -> None:
    args = parser().parse_args()
    local_refresh_token = refresh_token()
    all_scored_rows = load_rows(SCORED)
    all_markov_rows = load_rows(MARKOV)
    all_ledger_rows = load_rows(LEDGER) if LEDGER.exists() else []
    round_lookup = load_round_lookup()
    now_utc = datetime.now(timezone.utc)
    if args.game:
        scored_rows = [row for row in all_scored_rows if row.get("game") == args.game]
        ledger_rows = [row for row in all_ledger_rows if row.get("game") == args.game]
    else:
        scored_rows = list(all_scored_rows)
        ledger_rows = list(all_ledger_rows)

    current_round_games = {row.get("game", "") for row in all_scored_rows if row.get("game")}

    tracked_rows = []
    for row in ledger_rows:
        commence = parse_utc(row.get("commence_time", ""))
        if commence and commence <= now_utc:
            tracked_rows.append(row)

    round_tracked_rows = []
    for row in all_ledger_rows:
        if row.get("game", "") not in current_round_games:
            continue
        commence = parse_utc(row.get("commence_time", ""))
        if commence and commence <= now_utc:
            round_tracked_rows.append(row)

    round_high_value_tracking_rows = [
        row for row in round_tracked_rows
        if (to_float(row.get("live_qi")) or 0) >= 80
        and (to_float(row.get("ev_per_unit")) or 0) > 0
        and row.get("market") != "Ranking/Fantasy Pts"
    ]
    round_high_value_tracking_rows.sort(
        key=lambda row: (
            row.get("game", ""),
            0 if row.get("status") == "OPEN" else 1,
            -(to_float(row.get("live_qi")) or 0),
            row.get("player", ""),
        )
    )
    round_tracking_high_value_props = [
        row for row in round_high_value_tracking_rows
        if (to_float(row.get("best_price")) or to_float(row.get("bet_price")) or 0) >= 1.80
    ]
    round_tracking_multi_props = [
        row for row in round_high_value_tracking_rows
        if 0 < (to_float(row.get("best_price")) or to_float(row.get("bet_price")) or 0) < 1.80
    ]

    markov_lookup = {key(row): row for row in all_markov_rows}
    qi_universe = [
        row for row in scored_rows
        if (to_float(row.get("live_qi")) or 0) >= args.min_qi
        and (to_float(row.get("ev_per_unit")) or 0) > 0
        and row.get("matched_wheelo") == "True"
        and row.get("market") != "Ranking/Fantasy Pts"
    ]
    qi_universe.sort(key=lambda row: (row.get("game", ""), -(to_float(row.get("live_qi")) or 0), row.get("player", "")))
    qi80_universe = [
        row for row in qi_universe
        if (to_float(row.get("live_qi")) or 0) >= 80
    ]
    round_qi_universe = [
        row for row in all_scored_rows
        if (to_float(row.get("live_qi")) or 0) >= args.min_qi
        and (to_float(row.get("ev_per_unit")) or 0) > 0
        and row.get("matched_wheelo") == "True"
        and row.get("market") != "Ranking/Fantasy Pts"
    ]
    round_qi_universe.sort(key=lambda row: (row.get("game", ""), -(to_float(row.get("live_qi")) or 0), row.get("player", "")))
    round_qi80_universe = [
        row for row in round_qi_universe
        if (to_float(row.get("live_qi")) or 0) >= 80
    ]

    if args.game:
        portfolio = [
            row for row in scored_rows
            if row.get("signal") == "A_BET"
            and row.get("line_selection") == "BEST_RISK_ADJUSTED"
            and (to_float(row.get("ev_per_unit")) or 0) > 0
            and row.get("matched_wheelo") == "True"
        ]
        portfolio.sort(
            key=lambda row: (
                -(to_float(row.get("live_qi")) or 0),
                -(to_float(row.get("ev_per_unit")) or 0),
                row.get("player", ""),
            )
        )
        for row in portfolio:
            row["_report_status"] = "GAME_BET"
            if (to_float(row.get("stake_units")) or 0) <= 0:
                row["stake_units"] = str(scorer.stake_units(row))
    else:
        portfolio = [row for row in scored_rows if row.get("portfolio_selection") == "PORTFOLIO_BET"]
        portfolio.sort(key=lambda row: float(row.get("live_qi") or 0), reverse=True)
        for row in portfolio:
            row["_report_status"] = row.get("portfolio_selection", "")

    if args.game:
        round_portfolio = [
            row for row in all_scored_rows
            if row.get("signal") == "A_BET"
            and row.get("line_selection") == "BEST_RISK_ADJUSTED"
            and (to_float(row.get("ev_per_unit")) or 0) > 0
            and row.get("matched_wheelo") == "True"
        ]
        round_portfolio.sort(
            key=lambda row: (
                row.get("game", ""),
                -(to_float(row.get("live_qi")) or 0),
                -(to_float(row.get("ev_per_unit")) or 0),
                row.get("player", ""),
            )
        )
        for row in round_portfolio:
            row["_report_status"] = "GAME_BET"
            if (to_float(row.get("stake_units")) or 0) <= 0:
                row["stake_units"] = str(scorer.stake_units(row))
    else:
        round_portfolio = list(portfolio)

    singles_portfolio = [row for row in portfolio if (to_float(row.get("best_price")) or 0) >= 1.80]
    high_value_singles_portfolio = [row for row in singles_portfolio if (to_float(row.get("live_qi")) or 0) >= 80]
    multi_only_portfolio = [
        row for row in portfolio
        if 0 < (to_float(row.get("best_price")) or 0) < 1.80
        and (to_float(row.get("live_qi")) or 0) >= 80
    ]
    round_singles_portfolio = [row for row in round_portfolio if (to_float(row.get("best_price")) or 0) >= 1.80]
    round_high_value_singles_portfolio = [row for row in round_singles_portfolio if (to_float(row.get("live_qi")) or 0) >= 80]
    round_multi_only_portfolio = [
        row for row in round_portfolio
        if 0 < (to_float(row.get("best_price")) or 0) < 1.80
        and (to_float(row.get("live_qi")) or 0) >= 80
    ]
    high_value_singles_portfolio.sort(
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(to_float(row.get("ev_per_unit")) or 0),
            row.get("game", ""),
            row.get("player", ""),
        )
    )
    multi_only_portfolio.sort(
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(to_float(row.get("ev_per_unit")) or 0),
            row.get("game", ""),
            row.get("player", ""),
        )
    )
    round_high_value_singles_portfolio.sort(
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(to_float(row.get("ev_per_unit")) or 0),
            row.get("game", ""),
            row.get("player", ""),
        )
    )
    round_multi_only_portfolio.sort(
        key=lambda row: (
            -(to_float(row.get("live_qi")) or 0),
            -(to_float(row.get("ev_per_unit")) or 0),
            row.get("game", ""),
            row.get("player", ""),
        )
    )

    suppressed_goal = []
    suppressed_portfolio = []
    if not args.game:
        suppressed_goal = [
            row for row in scored_rows
            if row.get("signal") == "A_BET" and row.get("portfolio_selection") == "SUPPRESSED_GOAL_CAP"
        ]
        suppressed_goal.sort(key=lambda row: (float(row.get("selection_rank") or 9999), -(to_float(row.get("live_qi")) or 0)))
        suppressed_portfolio = [
            row for row in scored_rows
            if row.get("signal") == "A_BET" and row.get("portfolio_selection") == "SUPPRESSED_PORTFOLIO_CAP"
        ]
        suppressed_portfolio.sort(key=lambda row: (float(row.get("selection_rank") or 9999), -(to_float(row.get("live_qi")) or 0)))

    game_start_lookup: dict[str, datetime | None] = {}
    for row in all_scored_rows:
        game = row.get("game", "")
        if not game:
            continue
        start = parse_utc(row.get("commence_time", ""))
        existing = game_start_lookup.get(game)
        if existing is None or (start is not None and start < existing):
            game_start_lookup[game] = start

    games = sorted(
        {row["game"] for row in round_portfolio} if round_portfolio else {row["game"] for row in all_scored_rows if row.get("game")},
        key=lambda game: game_sort_key(game, game_start_lookup),
    )
    if args.game:
        title_game = "Player Props"
    else:
        title_game = "Round 12 Current Portfolio" if len(games) > 1 else (short_game_name(games[0]) if games else "Current AFL Props Card")
    books: dict[str, int] = {}
    for row in round_portfolio:
        books[row["book"]] = books.get(row["book"], 0) + 1
    top_qi = max((to_float(row.get("live_qi")) or 0) for row in round_portfolio) if round_portfolio else 0.0
    book_text = ", ".join(f"{k} {v}" for k, v in sorted(books.items(), key=lambda kv: (-kv[1], kv[0])))
    player_teams = load_player_teams()

    commentary = []
    for row in portfolio:
        markov_row = markov_lookup.get(key(row))
        path = markov_row.get("markov_path") if markov_row and markov_row.get("markov_path") else fallback_markov_path(row)
        risk = markov_row.get("risk", "") if markov_row else ""
        justification = markov_row.get("justification", "") if markov_row else ""
        ladder = markov_row.get("ladder_note", "") if markov_row else ""
        decision = markov_row.get("decision", "") if markov_row else ""
        model_prob = to_float(row.get("model_probability")) or 0.0
        market_prob = to_float(row.get("market_probability")) or 0.0
        edge_pts = model_prob - market_prob
        quoted_price = to_float(row.get("best_price")) or 0.0
        fair = fair_price(row.get("model_probability"))
        stake_note = stake_display_text(row.get("stake_units"), args.game)
        edge_summary = bet_edge_text(row)
        fair_summary = fair_line_text(row, fair)
        commentary.append(
            f"""
            <section class="commentary">
              <h3>{esc(player_team(row, player_teams))} | {esc(row['player'])} {esc(row['market'])} {esc(row['side'])} {num(row['line'], 1)} @ {num(row['best_price'], 2)} <span>({esc(row['book'])})</span></h3>
              <div class="trade-grid">
                <div class="trade-metric"><strong>QI</strong>{qi_pill(row['live_qi'])}</div>
                <div class="trade-metric"><strong>Model Fair Price</strong>{fair}</div>
                <div class="trade-metric"><strong>Market Price</strong>{num(row['best_price'], 2)}</div>
                <div class="trade-metric"><strong>Probability Edge</strong>{pct_points(edge_pts)}</div>
                <div class="trade-metric"><strong>Stake</strong>{stake_note}</div>
              </div>
              <p class="desk-note"><strong>Bet:</strong> {esc(row['player'])} {esc(row['market'])} {esc(row['side'])} {num(row['line'], 1)} at {num(row['best_price'], 2)} for {stake_note}.</p>
              <p><strong>Fair:</strong> {esc(fair_summary)}</p>
              <p><strong>Edge:</strong> {esc(edge_summary)}</p>
            </section>
            """
        )

    tracked_props_html = tracked_props_table(sorted(tracked_rows, key=lambda row: (row.get("game", ""), row.get("player", ""))))

    portfolio_title = "High Value Props" if args.game else "Round-Wide Player Props"
    size_label = "Round Card Size" if args.game else "Portfolio Size"
    size_copy = "round-wide qualifying props" if args.game else "final Walters bets"
    multi_intro = (
        "These are the round-wide sub-1.80 legs that qualify for multi use."
        if args.game
        else "Rows priced below <code>1.80</code> are separated here for multi use rather than standard singles selection."
    )
    multi_empty = (
        '<tr><td colspan="12">No current game-card rows below 1.80.</td></tr>'
        if args.game
        else '<tr><td colspan="12">No current portfolio rows below 1.80.</td></tr>'
    )
    blocked_section = ""
    if not args.game:
        blocked_section = f"""
    <h2>Blocked Strong Props</h2>
    <p>The AFLplayerprops default portfolio discipline includes a goal-prop cap and a top-10 overall cap. These rows are still model-positive A/B candidates; they were blocked by portfolio construction, not rejected as bad bets.</p>
    <h3>Blocked By Goal Risk Limit</h3>
    {candidate_table(suppressed_goal)}
    <h3>Blocked By Overall Portfolio Cap</h3>
    {candidate_table(suppressed_portfolio)}
"""
    detail_intro = (
        "Trader-style single-game frame: best Saints/Hawks expressions only, with no round-wide blocks."
        if args.game
        else "Trader-style frame: start with the thesis, mark the fair price, compare it with the live quote, size only when the edge survives discipline, and state clearly what would invalidate the position."
    )

    round_commentary = []
    if args.game:
        for row in round_portfolio:
            risk = ""
            model_prob = to_float(row.get("model_probability")) or 0.0
            market_prob = to_float(row.get("market_probability")) or 0.0
            edge_pts = model_prob - market_prob
            fair = fair_price(row.get("model_probability"))
            stake_note = stake_display_text(row.get("stake_units"), args.game)
            edge_summary = bet_edge_text(row)
            fair_summary = fair_line_text(row, fair)
            round_commentary.append(
                f"""
                <section class="commentary">
                  <h3>{esc(player_team(row, player_teams))} | {esc(row['player'])} {esc(row['market'])} {esc(row['side'])} {num(row['line'], 1)} @ {num(row['best_price'], 2)} <span>({esc(row['book'])})</span></h3>
                  <div class="trade-grid">
                    <div class="trade-metric"><strong>QI</strong>{qi_pill(row['live_qi'])}</div>
                    <div class="trade-metric"><strong>Model Fair Price</strong>{fair}</div>
                    <div class="trade-metric"><strong>Market Price</strong>{num(row['best_price'], 2)}</div>
                    <div class="trade-metric"><strong>Probability Edge</strong>{pct_points(edge_pts)}</div>
                    <div class="trade-metric"><strong>Stake</strong>{stake_note}</div>
                  </div>
                  <p class="desk-note"><strong>Bet:</strong> {esc(row['player'])} {esc(row['market'])} {esc(row['side'])} {num(row['line'], 1)} at {num(row['best_price'], 2)} for {stake_note}.</p>
                  <p><strong>Fair:</strong> {esc(fair_summary)}</p>
                  <p><strong>Edge:</strong> {esc(edge_summary)}</p>
                </section>
                """
            )

    commentary_by_game: dict[str, list[str]] = {}
    for row, html_block in zip(round_portfolio if args.game else portfolio, round_commentary if args.game else commentary):
        commentary_by_game.setdefault(row.get("game", ""), []).append(html_block)

    game_panels: list[str] = []
    tab_buttons: list[str] = [
        '<button class="tab-btn active" type="button" data-tab="tab-summary">Round Summary</button>',
    ]
    tab_games = [game for game in games if game in ({row.get("game", "") for row in round_qi80_universe} | {row.get("game", "") for row in round_portfolio if row.get("game")})]
    for idx, game in enumerate(tab_games):
        if not game:
            continue
        game_rows = [row for row in round_qi80_universe if row.get("game") == game]
        game_tracked_rows = [
            row for row in round_high_value_tracking_rows
            if row.get("game") == game
        ]
        game_high_value_rows = [
            row for row in game_rows
            if (to_float(row.get("best_price")) or 0) >= 1.80
        ]
        game_multi_rows = [
            row for row in game_rows
            if 0 < (to_float(row.get("best_price")) or 0) < 1.80
        ]
        game_commentary = commentary_by_game.get(game, [])
        tab_id = f"tab-game-{idx}"
        tab_buttons.append(
            f'<button class="tab-btn" type="button" data-tab="{tab_id}">{esc(short_game_name(game))}</button>'
        )
        game_panels.append(
            f"""
            <section id="{tab_id}" class="tab-panel">
              <h3>High Value Props</h3>
              <p>{len(game_high_value_rows)} props for this match at <code>1.80+</code>.</p>
              {grouped_qi_sections(game_high_value_rows, "No high value props for this match.")}
              <h3 class="section-gap">Multi Props Only</h3>
              <p>{len(game_multi_rows)} props for this match below <code>1.80</code>.</p>
              {grouped_qi_sections(game_multi_rows, "No multi-only props for this match.")}
            </section>
            """
        )
    tab_buttons.append('<button class="tab-btn" type="button" data-tab="tab-history">History</button>')
    tab_buttons.append('<button class="tab-btn" type="button" data-tab="tab-tracking">Tracking</button>')

    summary_panel_html = f"""
    <section id="tab-summary" class="tab-panel active">
      <section class="cards">
        <div class="card"><strong>{size_label}</strong>{len(round_portfolio) if args.game else len(portfolio)} {size_copy}</div>
        <div class="card"><strong>High Value Props</strong>{len(round_high_value_singles_portfolio) if args.game else len(high_value_singles_portfolio)} bets at 1.80+</div>
        <div class="card"><strong>Multi Props Only</strong>{len(round_multi_only_portfolio) if args.game else len(multi_only_portfolio)} bets below 1.80</div>
        <div class="card"><strong>Top QI</strong>{qi_pill(top_qi)}</div>
        <div class="card"><strong>Book Split</strong>{esc(book_text)}</div>
        <div class="card"><strong>QI 80+ Tracked</strong>{len(round_qi80_universe) if args.game else len(qi80_universe)} current props</div>
      </section>

      <h3>High Value Props</h3>
      <p>Round-wide player props priced at <code>1.80+</code> and filtered to <code>QI 80+</code>.</p>
      {grouped_qi_sections(round_high_value_singles_portfolio if args.game else high_value_singles_portfolio, "No high value props currently qualify.")}

      <h2 class="section-gap">Multi Props Only</h2>
      <p>{multi_intro}</p>
      {grouped_qi_sections(round_multi_only_portfolio if args.game else multi_only_portfolio, "No multi-only props currently qualify.")}
      {blocked_section}
      {"" if games else "<p>No match tabs are available for this slate yet.</p>"}
    </section>
    """

    tracking_panel_html = f"""
    <section id="tab-tracking" class="tab-panel">
      <p>Started or completed Round 12 props only. Split by standard player-props pricing and multi-only pricing.</p>
      {tracking_summary_cards(round_high_value_tracking_rows)}
      <h3>Results Summary</h3>
      <p>Quick settled recap for the rows already in play or completed.</p>
      <h4>High Value Props</h4>
      {qi_band_results_table(round_tracking_high_value_props)}
      <h4 class="section-gap">Multi Props Only</h4>
      {qi_band_results_table(round_tracking_multi_props)}
      <h3 class="section-gap">Best And Worst Props</h3>
      <p>Highest and lowest stake-adjusted results from the settled tracking rows.</p>
      {best_worst_results(round_high_value_tracking_rows)}
      <section class="cards">
        <div class="card"><strong>Tracked High Value</strong>{len(round_high_value_tracking_rows)} started/completed rows</div>
        <div class="card"><strong>In Play</strong>{sum(1 for row in round_high_value_tracking_rows if row.get("status") == "OPEN")} live rows</div>
        <div class="card"><strong>Settled</strong>{sum(1 for row in round_high_value_tracking_rows if row.get("status") == "SETTLED")} graded rows</div>
      </section>
      <h3>High Value Props</h3>
      <p>{len(round_tracking_high_value_props)} started/completed props at <code>1.80+</code>.</p>
      {grouped_tracking_sections(round_tracking_high_value_props, "No started or completed high value props yet.")}
      <h3 class="section-gap">Multi Props Only</h3>
      <p>{len(round_tracking_multi_props)} started/completed props below <code>1.80</code>.</p>
      {grouped_tracking_sections(round_tracking_multi_props, "No started or completed multi-only props yet.")}
    </section>
    """

    history_high_value_rows = [
        row for row in all_ledger_rows
        if (to_float(row.get("best_price")) or to_float(row.get("bet_price")) or 0) >= 1.80
    ]
    history_multi_rows = [
        row for row in all_ledger_rows
        if 0 < (to_float(row.get("best_price")) or to_float(row.get("bet_price")) or 0) < 1.80
    ]

    history_panel_html = f"""
    <section id="tab-history" class="tab-panel">
      <p>All logged bet rows to date. This grows automatically as new games and rounds are added to the ledger.</p>
      <section class="cards">
        <div class="card"><strong>Total Rows</strong>{len(all_ledger_rows)} logged bets</div>
        <div class="card"><strong>Settled</strong>{sum(1 for row in all_ledger_rows if row.get("status") == "SETTLED")} graded rows</div>
        <div class="card"><strong>Open / Tracking</strong>{sum(1 for row in all_ledger_rows if row.get("status") != "SETTLED")} active rows</div>
      </section>
      <section class="chart-grid">
        {profit_chart("Weekly Profit", all_ledger_rows, "week")}
        {profit_chart("Monthly Profit", all_ledger_rows, "month")}
      </section>
      <h3>High Value Props</h3>
      <p>Date first, round second, then the same tracking-style prop fields for all logged rows at <code>1.80+</code>.</p>
      {grouped_history_sections(history_high_value_rows, round_lookup, "No historical high value props yet.")}
      <h3 class="section-gap">Multi Props Only</h3>
      <p>All logged rows below <code>1.80</code>, kept in the same history structure.</p>
      {grouped_history_sections(history_multi_rows, round_lookup, "No historical multi-only props yet.")}
    </section>
    """

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BetMate Edge</title>
  <style>
    :root {{
      --ink: #111827;
      --muted: #4b5563;
      --line: #d1d5db;
      --panel: #f8fafc;
      --a: #0f766e;
      --b: #1d4ed8;
      --bg: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.08), transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #ffffff 22%);
    }}
    header {{
      padding: 28px 34px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(10px);
    }}
    .header-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
    }}
    h1 {{
      margin: 0;
      font-size: 28px;
    }}
    .refresh-controls {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
      min-width: 220px;
    }}
    .refresh-btn {{
      border: 1px solid var(--ink);
      background: var(--ink);
      color: #fff;
      border-radius: 10px;
      padding: 10px 14px;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    }}
    .refresh-btn:hover {{
      background: #1f2937;
    }}
    .refresh-btn:disabled {{
      opacity: 0.75;
      cursor: wait;
    }}
    .refresh-status {{
      margin: 0;
      min-height: 18px;
      text-align: right;
      color: var(--muted);
      font-size: 12px;
    }}
    .refresh-status.error {{
      color: #b91c1c;
    }}
    h2 {{
      margin: 28px 0 12px;
      font-size: 20px;
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 16px;
    }}
    h4 {{
      margin: 18px 0 8px;
      font-size: 14px;
      color: var(--muted);
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }}
    .section-gap {{
      margin-top: 28px;
    }}
    .qi-group + .qi-group {{
      margin-top: 22px;
    }}
    h3 span {{
      color: var(--muted);
      font-weight: normal;
    }}
    p {{
      line-height: 1.45;
    }}
    main {{
      padding: 22px 34px 40px;
    }}
    .meta {{
      color: var(--muted);
      margin: 0;
      max-width: 980px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin: 0 0 18px;
    }}
    .results-cards {{
      margin-top: 12px;
    }}
    .results-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
      margin: 0 0 18px;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin: 0 0 22px;
    }}
    .chart-card {{
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }}
    .chart-card h3 {{
      margin-bottom: 6px;
    }}
    .chart-note {{
      color: var(--muted);
      margin: 0 0 10px;
      font-size: 13px;
    }}
    .profit-chart {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .chart-axis {{
      stroke: #94a3b8;
      stroke-width: 1;
    }}
    .chart-zero {{
      stroke: #cbd5e1;
      stroke-width: 1;
      stroke-dasharray: 4 4;
    }}
    .chart-label {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .chart-value {{
      fill: var(--ink);
      font-size: 11px;
      font-weight: 600;
    }}
    .chart-axis-label {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .result-list {{
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }}
    .result-list h4 {{
      margin-top: 0;
    }}
    .result-list ul {{
      margin: 0;
      padding-left: 18px;
    }}
    .result-list li {{
      margin: 0 0 8px;
      line-height: 1.4;
    }}
    .tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 0 0 18px;
    }}
    .tab-btn {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 999px;
      padding: 9px 14px;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }}
    .tab-btn.active {{
      background: var(--ink);
      color: #fff;
      border-color: var(--ink);
    }}
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
    }}
    .card {{
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #ffffff 0%, var(--panel) 100%);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }}
    .card strong {{
      display: block;
      margin-bottom: 6px;
    }}
    .qi-pill {{
      display: inline-block;
      min-width: 38px;
      padding: 3px 8px;
      border-radius: 999px;
      text-align: center;
      font-weight: 700;
      line-height: 1.2;
      border: 1px solid transparent;
    }}
    .qi-95 {{
      background: #6d28d9;
      color: #faf5ff;
      border-color: #7c3aed;
    }}
    .qi-90 {{
      background: #7c3aed;
      color: #faf5ff;
      border-color: #8b5cf6;
    }}
    .qi-85 {{
      background: #0f766e;
      color: #f0fdfa;
      border-color: #0d9488;
    }}
    .qi-80 {{
      background: #1d4ed8;
      color: #eff6ff;
      border-color: #2563eb;
    }}
    .qi-75 {{
      background: #a16207;
      color: #fffbeb;
      border-color: #ca8a04;
    }}
    .qi-70 {{
      background: #b45309;
      color: #fff7ed;
      border-color: #d97706;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--ink);
      color: white;
    }}
    tr:nth-child(even) td {{
      background: #f9fafb;
    }}
    .badge {{
      display: inline-block;
      min-width: 28px;
      text-align: center;
      color: white;
      border-radius: 4px;
      padding: 2px 6px;
      font-weight: bold;
    }}
    .badge.a {{ background: var(--a); }}
    .badge.b {{ background: var(--b); }}
    .badge.lean {{ background: #b45309; }}
    .badge.pass {{ background: #6b7280; }}
    .pos {{
      color: #047857;
      font-weight: bold;
    }}
    .commentary {{
      border-top: 1px solid var(--line);
      padding: 18px 0 24px;
      max-width: 1080px;
    }}
    .trade-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 10px 0 14px;
    }}
    .trade-metric {{
      border: 1px solid var(--line);
      background: #ffffff;
      border-radius: 10px;
      padding: 10px 12px;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
    }}
    .trade-metric strong {{
      display: block;
      font-size: 11px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    .desk-note {{
      border-left: 4px solid var(--a);
      background: #f8fffd;
      padding: 10px 12px;
      border-radius: 0 8px 8px 0;
      margin: 10px 0;
    }}
    .desk-note.alt {{
      border-left-color: var(--b);
      background: #f8fbff;
    }}
    .risk {{
      color: #7c2d12;
    }}
    code {{
      background: #eef2f7;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    @media print {{
      header {{ background: white; }}
      main {{ padding: 16px; }}
      .commentary {{ page-break-inside: avoid; }}
      .refresh-btn {{ display: none; }}
    }}
    @media (max-width: 720px) {{
      .header-row {{
        flex-direction: column;
        align-items: stretch;
      }}
      .refresh-controls {{
        align-items: stretch;
        min-width: 0;
      }}
      .refresh-btn {{
        width: 100%;
      }}
      .refresh-status {{
        text-align: left;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <h1>BetMate Edge: {esc(title_game)}</h1>
      <div class="refresh-controls">
        <button
          id="refresh-data-btn"
          class="refresh-btn"
          type="button"
          data-game="{html_attr(args.game)}"
          data-output="{html_attr(args.output.name)}"
        >Refresh Data</button>
        <p id="refresh-status" class="refresh-status" aria-live="polite"></p>
      </div>
    </div>
    <p class="meta">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}.</p>
  </header>
  <main>
    <section class="tabs">
      {''.join(tab_buttons)}
    </section>
    {summary_panel_html}
    {tracking_panel_html}
    {history_panel_html}
    {''.join(game_panels)}
  </main>
  <script>
    const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
    const tabPanels = Array.from(document.querySelectorAll('.tab-panel'));
    tabButtons.forEach((button) => {{
      button.addEventListener('click', () => {{
        const target = button.getAttribute('data-tab');
        tabButtons.forEach((item) => item.classList.toggle('active', item === button));
        tabPanels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
      }});
    }});

    const refreshButton = document.getElementById('refresh-data-btn');
    const refreshStatus = document.getElementById('refresh-status');
    const refreshToken = {json.dumps(local_refresh_token)};

    function setRefreshStatus(message, isError = false) {{
      if (!refreshStatus) {{
        return;
      }}
      refreshStatus.textContent = message || '';
      refreshStatus.classList.toggle('error', Boolean(isError));
    }}

    async function refreshData() {{
      if (!refreshButton) {{
        return;
      }}
      refreshButton.disabled = true;
      refreshButton.textContent = 'Refreshing...';
      setRefreshStatus('Fetching fresh odds and rebuilding this report...');

      try {{
        const headers = {{ 'Content-Type': 'application/json' }};
        if (refreshToken) {{
          headers.Authorization = `Bearer ${{refreshToken}}`;
        }}
        const response = await fetch('http://127.0.0.1:8765/refresh', {{
          method: 'POST',
          headers,
          body: JSON.stringify({{
            game: refreshButton.dataset.game || null,
            output: refreshButton.dataset.output || null
          }})
        }});
        const payload = await response.json().catch(() => ({{ ok: false, error: 'Refresh service returned unreadable output.' }}));
        if (!response.ok || !payload.ok) {{
          throw new Error(payload.error || `Refresh failed (${{response.status}}).`);
        }}
        setRefreshStatus(`Updated ${{payload.updated_at || 'just now'}}. Reloading...`);
        window.location.reload();
      }} catch (error) {{
        const message = error instanceof Error ? error.message : 'Refresh failed.';
        setRefreshStatus(message, true);
      }} finally {{
        refreshButton.disabled = false;
        refreshButton.textContent = 'Refresh Data';
      }}
    }}

    if (refreshButton) {{
      refreshButton.addEventListener('click', refreshData);
    }}
  </script>
</body>
</html>
"""
    args.output.write_text(html)
    print(args.output)


if __name__ == "__main__":
    main()
