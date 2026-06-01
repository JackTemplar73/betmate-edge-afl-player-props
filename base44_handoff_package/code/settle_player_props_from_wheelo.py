#!/usr/bin/env python3
"""Settle AFL player props from official AFL.com.au stats, with Wheelo fallback."""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_BETS = ROOT / "markov_bet_justifications.csv"
DEFAULT_LEDGER = ROOT / "aflplayerprops_bet_history.csv"
DEFAULT_MATCH_MAP = ROOT / "afl_match_mapping.csv"
DEFAULT_PRE = ROOT / "wheelo_snapshots" / "20260524_123837" / "wheelo_player_stats_2026.json"
DEFAULT_POST = ROOT / "wheelo_snapshots" / "20260525_083556" / "wheelo_player_stats_2026.json"
OUT_CSV = ROOT / "player_prop_settlement.csv"
OUT_MD = ROOT / "player_prop_settlement_report.md"

TOKEN_URL = "https://api.afl.com.au/cfs/afl/WMCTok"
MATCH_PAGE_TEMPLATE = "https://www.afl.com.au/afl/matches/{match_id}"
PLAYER_STATS_TEMPLATE = "https://api.afl.com.au/cfs/afl/playerStats/match/{provider_match_id}"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
)
BOOK_ALIASES = {
    "pointsbetau": "pointsbetau",
    "pointsbet au": "pointsbetau",
    "pointsbet (au)": "pointsbetau",
}
PLAYER_NAME_ALIASES = {
    "conor nash": "conor nash",
    "connor macdonald": "connor macdonald",
    "connor macdonald": "connor macdonald",
}
MARKET_TO_STAT = {
    "Goals": "goals",
    "Disposals": "disposals",
    "Tackles": "tackles",
    "Marks": "marks",
}


def f(value: Any) -> float | None:
    if value in ("", "NA", None, "DNP"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f_in:
        return list(csv.DictReader(f_in))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalise_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return PLAYER_NAME_ALIASES.get(cleaned, cleaned)


def normalise_book(value: str) -> str:
    cleaned = normalise_text(value)
    return BOOK_ALIASES.get(cleaned, cleaned)


def normalise_game(value: str) -> str:
    cleaned = value.replace(" Saints ", " ").replace(" Hawks ", " ").replace(" Demons", "")
    cleaned = cleaned.replace(" Swans", "").replace(" Giants", "").replace(" Cats", "")
    cleaned = cleaned.replace(" Blues", "").replace(" Bombers", "").replace(" Eagles", "")
    cleaned = cleaned.replace(" Dockers", "").replace(" Suns", "").replace(" Crows", "")
    cleaned = cleaned.replace(" Power", "").replace(" Magpies", "").replace(" Lions", "")
    cleaned = cleaned.replace(" Kangaroos", "").replace(" Tigers", "")
    return normalise_text(cleaned)


def load_snapshot(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text())["Data"]
    rows: dict[str, dict[str, Any]] = {}
    for i, player in enumerate(payload["Player"]):
        rows[player] = {
            k: payload[k][i]
            for k in payload
            if isinstance(payload[k], list) and i < len(payload[k])
        }
    return rows


def actual_stat_from_wheelo(player: str, market: str, pre: dict[str, Any], post: dict[str, Any]) -> float | None:
    pre_matches = f(pre.get("Matches"))
    post_matches = f(post.get("Matches"))
    if pre_matches is None or post_matches is None or post_matches <= pre_matches:
        return None

    if market == "Goals":
        pre_total = f(pre.get("Goals_Total"))
        post_total = f(post.get("Goals_Total"))
        if pre_total is None or post_total is None:
            return None
        return post_total - pre_total

    field = {"Disposals": "Disposals", "Tackles": "Tackles", "Marks": "Marks"}.get(market)
    if not field:
        return None
    pre_avg = f(pre.get(field))
    post_avg = f(post.get(field))
    if pre_avg is None or post_avg is None:
        return None
    return post_avg * post_matches - pre_avg * pre_matches


def settle(side: str, line: float, actual: float) -> str:
    if actual == line:
        return "PUSH"
    if side == "Over":
        return "WIN" if actual > line else "LOSS"
    return "WIN" if actual < line else "LOSS"


def unit_profit(result: str, price: float) -> float:
    if result == "WIN":
        return price - 1
    if result == "LOSS":
        return -1
    return 0.0


def request_text(url: str, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, context=ssl.create_default_context()) as resp:
        return resp.read().decode("utf-8")


def request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    return json.loads(request_text(url, headers=headers))


def fetch_afl_token() -> str:
    payload = request_json(TOKEN_URL, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"})
    token = str(payload.get("token", "")).strip()
    if not token:
        raise RuntimeError("AFL token response did not include a token")
    return token


def provider_match_id_from_reference(reference: str) -> str:
    ref = reference.strip()
    if not ref:
        raise RuntimeError("Empty AFL match reference")
    provider_match = re.search(r"(CD_M\d+)", ref)
    if provider_match:
        return provider_match.group(1)
    match_id_match = re.search(r"/matches/(\d+)", ref)
    numeric_match_id = match_id_match.group(1) if match_id_match else ref if ref.isdigit() else ""
    if not numeric_match_id:
        raise RuntimeError(f"Could not resolve AFL match reference: {reference}")
    match_url = MATCH_PAGE_TEMPLATE.format(match_id=numeric_match_id)
    html = request_text(match_url, headers={"User-Agent": DEFAULT_USER_AGENT})
    provider_match = re.search(r"(CD_M\d+)", html)
    if not provider_match:
        raise RuntimeError(f"Could not find provider match id on {match_url}")
    return provider_match.group(1)


def fetch_afl_player_stats(provider_match_id: str, match_url: str | None) -> dict[str, int]:
    token = fetch_afl_token()
    referer = match_url or MATCH_PAGE_TEMPLATE.format(match_id=provider_match_id)
    payload = request_json(
        PLAYER_STATS_TEMPLATE.format(provider_match_id=provider_match_id),
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.afl.com.au",
            "Referer": referer,
            "x-media-mis-token": token,
        },
    )
    rows = {}
    for side_key in ("homeTeamPlayerStats", "awayTeamPlayerStats"):
        for item in payload.get(side_key, []) or []:
            stats = item.get("playerStats", {})
            player = stats.get("player", {})
            name_bits = [
                player.get("playerName", {}).get("givenName", ""),
                player.get("playerName", {}).get("surname", ""),
            ]
            player_name = " ".join(bit.strip() for bit in name_bits if bit).strip()
            if not player_name:
                continue
            norm = normalise_text(player_name)
            stat_block = stats.get("stats", {})
            rows[norm] = {
                "goals": int(stat_block.get("goals") or 0),
                "disposals": int(stat_block.get("disposals") or 0),
                "tackles": int(stat_block.get("tackles") or 0),
                "marks": int(stat_block.get("marks") or 0),
            }
    return rows


def read_official_stats(args: argparse.Namespace, rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, int]], str]:
    if args.stats_json:
        payload = json.loads(args.stats_json.read_text())
        stats = {}
        for side_key in ("homeTeamPlayerStats", "awayTeamPlayerStats"):
            for item in payload.get(side_key, []) or []:
                stat_row = item.get("playerStats", {})
                player = stat_row.get("player", {})
                name_bits = [
                    player.get("playerName", {}).get("givenName", ""),
                    player.get("playerName", {}).get("surname", ""),
                ]
                player_name = " ".join(bit.strip() for bit in name_bits if bit).strip()
                if not player_name:
                    continue
                norm = normalise_text(player_name)
                stats[norm] = {
                    "goals": int(stat_row.get("stats", {}).get("goals") or 0),
                    "disposals": int(stat_row.get("stats", {}).get("disposals") or 0),
                    "tackles": int(stat_row.get("stats", {}).get("tackles") or 0),
                    "marks": int(stat_row.get("stats", {}).get("marks") or 0),
                }
        return stats, f"Official AFL.com.au stats JSON: `{args.stats_json}`"

    reference = resolve_match_reference(args, rows)
    provider_match_id = provider_match_id_from_reference(reference)
    match_url = args.afl_match_url or (MATCH_PAGE_TEMPLATE.format(match_id=args.afl_match_id) if args.afl_match_id and args.afl_match_id.isdigit() else None)
    stats = fetch_afl_player_stats(provider_match_id, match_url)
    return stats, f"Official AFL.com.au player stats: `{PLAYER_STATS_TEMPLATE.format(provider_match_id=provider_match_id)}`"


def resolve_match_reference(args: argparse.Namespace, rows: list[dict[str, str]]) -> str:
    if args.afl_match_url:
        return args.afl_match_url
    if args.afl_match_id:
        return args.afl_match_id
    if args.match_map and args.match_map.exists():
        game_keys = {normalise_game(row.get("game", "")) for row in rows if row.get("game")}
        commence_times = {row.get("commence_time", "") for row in rows if row.get("commence_time")}
        for mapping in read_csv(args.match_map):
            map_game = normalise_game(mapping.get("game", ""))
            map_commence = mapping.get("commence_time", "")
            if map_game in game_keys and (not map_commence or map_commence in commence_times):
                for field in ("afl_provider_match_id", "afl_match_url", "afl_match_id"):
                    value = str(mapping.get(field, "")).strip()
                    if value:
                        return value
    raise RuntimeError(
        "Official AFL settlement requires --afl-match-id, --afl-match-url, "
        "--stats-json, or a matching entry in afl_match_mapping.csv"
    )


def load_target_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    ledger_rows = read_csv(args.ledger)
    if ledger_rows:
        rows = ledger_rows
        if args.game:
            target = normalise_game(args.game)
            rows = [row for row in rows if normalise_game(row.get("game", "")) == target]
            if not rows:
                raise RuntimeError(f"No ledger rows matched game: {args.game}")
        if args.only_unsettled:
            rows = [row for row in rows if row.get("status") != "SETTLED"]
            if args.game and not rows:
                raise RuntimeError(f"No unsettled ledger rows remain for game: {args.game}")
        if rows:
            return rows
        if args.game or args.only_unsettled:
            raise RuntimeError("No eligible ledger rows were found for settlement.")
    rows = read_csv(args.card)
    if not rows:
        raise RuntimeError("No rows found in ledger or card for settlement")
    return rows


def settle_from_official(args: argparse.Namespace, rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    official_stats, source_note = read_official_stats(args, rows)
    settled = []
    dnp_count = 0
    for row in rows:
        player = row["player"]
        market = row["market"]
        line = f(row["line"])
        price = f(row.get("bet_price", row.get("price")))
        stake = f(row.get("stake_units")) or 1.0
        actual: str | int = ""
        result = "NO_STAT"
        profit = 0.0
        norm_player = normalise_text(player)
        stat_name = MARKET_TO_STAT.get(market)
        if line is not None and price is not None and stat_name:
            player_stats = official_stats.get(norm_player)
            if player_stats is None:
                actual = "DNP"
                result = "PUSH"
                dnp_count += 1
            else:
                actual_value = float(player_stats[stat_name])
                result = settle(row["side"], line, actual_value)
                profit = unit_profit(result, price)
                actual = int(round(actual_value))
        stake_profit = profit * stake
        settled.append(
            {
                "bet_id": row.get("bet_id", ""),
                "game": row.get("game", ""),
                "commence_time": row.get("commence_time", ""),
                "player": player,
                "market": market,
                "side": row["side"],
                "line": row["line"],
                "book": row.get("book", ""),
                "actual": actual,
                "result": result,
                "unit_profit": round(profit, 3),
                "stake_profit": round(stake_profit, 3),
                "stake_units": stake,
                "signal": row.get("signal", ""),
            }
        )
    notes = [
        f"Settlement source: {source_note}.",
        "Missing official player-stat rows are treated as DNP and settled as PUSH.",
        f"DNP/PUSH rows: {dnp_count}.",
    ]
    return settled, notes


def settle_from_wheelo(args: argparse.Namespace, rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    pre = load_snapshot(args.pre)
    post = load_snapshot(args.post)
    settled = []
    for row in rows:
        player = row["player"]
        market = row["market"]
        line = f(row["line"])
        price = f(row.get("bet_price", row.get("price")))
        stake = f(row.get("stake_units")) or 1.0
        if line is None or price is None or player not in pre or player not in post:
            actual = None
            result = "NO_STAT"
            profit = 0.0
        else:
            actual = actual_stat_from_wheelo(player, market, pre[player], post[player])
            if actual is None:
                result = "NO_STAT"
                profit = 0.0
            else:
                result = settle(row["side"], line, actual)
                profit = unit_profit(result, price)
        stake_profit = profit * stake
        actual_display = "" if actual is None else int(round(actual))
        settled.append(
            {
                "bet_id": row.get("bet_id", ""),
                "game": row.get("game", ""),
                "commence_time": row.get("commence_time", ""),
                "player": player,
                "market": market,
                "side": row["side"],
                "line": row["line"],
                "book": row.get("book", ""),
                "actual": actual_display,
                "result": result,
                "unit_profit": round(profit, 3),
                "stake_profit": round(stake_profit, 3),
                "stake_units": stake,
                "signal": row.get("signal", ""),
            }
        )
    notes = [
        "Settlement source: Wheelo pre/post player-stat snapshots.",
        f"- Pre-game snapshot: `{args.pre}`",
        f"- Post-game snapshot: `{args.post}`",
        "- Method: latest stat = post average x post matches - pre average x pre matches; goals use post total - pre total.",
    ]
    return settled, notes


def build_report(rows: list[dict[str, Any]], source_notes: list[str]) -> str:
    wins = sum(1 for r in rows if r["result"] == "WIN")
    losses = sum(1 for r in rows if r["result"] == "LOSS")
    pushes = sum(1 for r in rows if r["result"] == "PUSH")
    profit = sum(float(r["unit_profit"]) for r in rows)
    staked = sum((f(r.get("stake_units")) or 1.0) for r in rows if r["result"] in {"WIN", "LOSS"})
    stake_profit = sum(float(r.get("stake_profit") or 0) for r in rows)
    risked = wins + losses
    roi = profit / risked if risked else 0.0
    stake_roi = stake_profit / staked if staked else 0.0

    by_grade = []
    for grade in sorted({r.get("signal", "") for r in rows if r.get("signal", "")}):
        grade_rows = [r for r in rows if r.get("signal", "") == grade]
        w = sum(1 for r in grade_rows if r["result"] == "WIN")
        l = sum(1 for r in grade_rows if r["result"] == "LOSS")
        p = sum(1 for r in grade_rows if r["result"] == "PUSH")
        prof = sum(float(r["unit_profit"]) for r in grade_rows)
        s = sum((f(r.get("stake_units")) or 1.0) for r in grade_rows if r["result"] in {"WIN", "LOSS"})
        sp = sum(float(r.get("stake_profit") or 0) for r in grade_rows)
        n = w + l
        by_grade.append((grade, w, l, p, prof, prof / n if n else 0.0, s, sp, sp / s if s else 0.0))

    lines = [
        "# AFL Player Prop Settlement",
        "",
        *source_notes,
        "",
        f"Flat staking: **{wins}-{losses}-{pushes}**, profit **{profit:+.2f} units**, ROI **{roi:.1%}** on one unit per non-push.",
        f"Walters staking: staked **{staked:.2f} units**, profit **{stake_profit:+.2f} units**, ROI **{stake_roi:.1%}**.",
        "",
        "## By Grade",
        "| Grade | W | L | Push | Units | ROI |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for grade, w, l, p, prof, grade_roi, _, _, _ in by_grade:
        lines.append(f"| {grade} | {w} | {l} | {p} | {prof:+.2f} | {grade_roi:.1%} |")
    lines.extend(["", "## By Grade - Walters Stake", "| Grade | Staked | Units | ROI |", "|---|---:|---:|---:|"])
    for grade, _, _, _, _, _, staked_grade, stake_profit_grade, stake_roi_grade in by_grade:
        lines.append(f"| {grade} | {staked_grade:.2f} | {stake_profit_grade:+.2f} | {stake_roi_grade:.1%} |")
    lines.extend(["", "## Bet Results", "| Grade | Stake | Bet | Book | Actual | Result | Flat Units | Stake Units |", "|---|---:|---|---|---:|---|---:|---:|"])
    for row in rows:
        bet = f"{row['player']} {row['market']} {row['side']} {row['line']}"
        stake = f(row.get("stake_units")) or 1.0
        lines.append(
            f"| {row.get('signal', '')} | {stake:.2f}u | {bet} | {row['book']} | "
            f"{row['actual']} | {row['result']} | {float(row['unit_profit']):+.2f} | {float(row.get('stake_profit') or 0):+.2f} |"
        )
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    p.add_argument("--card", type=Path, default=DEFAULT_BETS)
    p.add_argument("--game", help="Filter settlement to one game name from the ledger")
    p.add_argument("--only-unsettled", action="store_true", help="When reading the ledger, only settle rows not already marked SETTLED")
    p.add_argument("--source", choices=("official", "wheelo"), default="official")
    p.add_argument("--afl-match-id", help="AFL match page id (for example 8139) or provider match id (for example CD_M20260141201)")
    p.add_argument("--afl-match-url", help="Full AFL.com.au match URL")
    p.add_argument("--match-map", type=Path, default=DEFAULT_MATCH_MAP)
    p.add_argument("--stats-json", type=Path, help="Local AFL player-stats JSON file for offline settlement or testing")
    p.add_argument("--pre", type=Path, default=DEFAULT_PRE)
    p.add_argument("--post", type=Path, default=DEFAULT_POST)
    p.add_argument("--output-csv", type=Path, default=OUT_CSV)
    p.add_argument("--output-md", type=Path, default=OUT_MD)
    return p


def main() -> None:
    args = parser().parse_args()
    rows = load_target_rows(args)
    if args.source == "official":
        settled, source_notes = settle_from_official(args, rows)
    else:
        settled, source_notes = settle_from_wheelo(args, rows)

    write_csv(args.output_csv, settled)
    args.output_md.write_text(build_report(settled, source_notes))

    wins = sum(1 for r in settled if r["result"] == "WIN")
    losses = sum(1 for r in settled if r["result"] == "LOSS")
    pushes = sum(1 for r in settled if r["result"] == "PUSH")
    profit = sum(float(r["unit_profit"]) for r in settled)
    risked = wins + losses
    roi = profit / risked if risked else 0.0
    print(f"{wins}-{losses}-{pushes} profit {profit:+.2f} ROI {roi:.1%}")
    print(args.output_csv)
    print(args.output_md)


if __name__ == "__main__":
    main()
