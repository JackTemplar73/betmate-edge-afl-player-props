#!/usr/bin/env python3
"""Persistent history and CLV ledger for AFLplayerprops."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_LEDGER = ROOT / "aflplayerprops_bet_history.csv"
DEFAULT_CARD = ROOT / "markov_bet_justifications.csv"
DEFAULT_SCORED = ROOT / "oddsapi_wheelo_ev_qi.csv"
DEFAULT_SETTLEMENT = ROOT / "player_prop_settlement.csv"

FIELDS = [
    "bet_id",
    "status",
    "created_at_utc",
    "updated_at_utc",
    "game",
    "commence_time",
    "player",
    "market",
    "side",
    "line",
    "book",
    "bet_price",
    "stake_units",
    "signal",
    "projection",
    "model_probability",
    "market_probability",
    "model_edge",
    "ev_per_unit",
    "live_qi",
    "alt_line_score",
    "markov_path",
    "book_market_reliability",
    "portfolio_selection",
    "open_line",
    "open_price",
    "latest_line",
    "latest_price",
    "close_line",
    "close_price",
    "clv_price_decimal",
    "clv_implied_points",
    "line_clv",
    "clv_status",
    "actual",
    "result",
    "flat_profit",
    "stake_profit",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def f(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_float(value: Any, digits: int = 6) -> str:
    number = f(value)
    if number is None:
        return ""
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def normalise_book(book: str) -> str:
    return book.strip().lower().replace(" ", "").replace("(", "").replace(")", "")


def bet_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("player", "")).strip().lower(),
        str(row.get("market", "")).strip().lower(),
        str(row.get("side", "")).strip().lower(),
        fmt_float(row.get("line"), 3),
        normalise_book(str(row.get("book", ""))),
        str(row.get("commence_time", "")).strip(),
    )


def bet_id(row: dict[str, Any]) -> str:
    raw = "|".join(bet_key(row))
    safe = "".join(ch if ch.isalnum() else "_" for ch in raw)
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")[:180]


def implied(price: Any) -> float | None:
    p = f(price)
    if not p:
        return None
    return 1.0 / p


def calc_clv(row: dict[str, Any]) -> None:
    bet_price = f(row.get("bet_price"))
    close_price = f(row.get("close_price")) or f(row.get("latest_price"))
    if bet_price is None or close_price is None:
        row["clv_price_decimal"] = ""
        row["clv_implied_points"] = ""
        row["clv_status"] = "NO_CLV"
    else:
        row["clv_price_decimal"] = fmt_float(bet_price - close_price, 4)
        bet_imp = implied(bet_price)
        close_imp = implied(close_price)
        if bet_imp is not None and close_imp is not None:
            # Positive means our price was better than the later/closing market.
            row["clv_implied_points"] = fmt_float((close_imp - bet_imp) * 100, 3)
            if abs(close_imp - bet_imp) < 1e-9:
                row["clv_status"] = "FLAT_CLOSE"
            else:
                row["clv_status"] = "BEAT_CLOSE" if close_imp > bet_imp else "MISSED_CLOSE"
        else:
            row["clv_implied_points"] = ""
            row["clv_status"] = "NO_CLV"

    open_line = f(row.get("open_line"))
    close_line = f(row.get("close_line")) or f(row.get("latest_line"))
    if open_line is not None and close_line is not None:
        if str(row.get("side")) == "Over":
            line_clv = close_line - open_line
        else:
            line_clv = open_line - close_line
        row["line_clv"] = fmt_float(line_clv, 3)
    else:
        row["line_clv"] = ""


def card_row_to_ledger(
    row: dict[str, str],
    scored_lookup: dict[tuple[str, str, str, str, str, str], dict[str, str]],
    loose_lookup: dict[tuple[str, str, str, str, str], dict[str, str]],
) -> dict[str, Any]:
    key = bet_key(row)
    loose_key = (
        row.get("player", "").strip().lower(),
        row.get("market", "").strip().lower(),
        row.get("side", "").strip().lower(),
        fmt_float(row.get("line"), 3),
        normalise_book(row.get("book", "")),
    )
    scored = scored_lookup.get(key) or loose_lookup.get(loose_key, {})
    price = row.get("price") or row.get("best_price")
    line = row.get("line")
    created = now()
    ledger_row = {
        "bet_id": bet_id({**row, **scored}),
        "status": "OPEN",
        "created_at_utc": created,
        "updated_at_utc": created,
        "game": scored.get("game", ""),
        "commence_time": scored.get("commence_time", ""),
        "player": row.get("player", ""),
        "market": row.get("market", ""),
        "side": row.get("side", ""),
        "line": line,
        "book": row.get("book", ""),
        "bet_price": price,
        "stake_units": row.get("stake_units", "1"),
        "signal": row.get("signal", ""),
        "projection": row.get("projection", ""),
        "model_probability": row.get("model_probability", ""),
        "market_probability": row.get("market_probability", ""),
        "model_edge": row.get("model_edge", ""),
        "ev_per_unit": row.get("ev_per_unit", ""),
        "live_qi": row.get("live_qi", ""),
        "alt_line_score": row.get("alt_line_score", ""),
        "markov_path": row.get("markov_path", ""),
        "book_market_reliability": row.get("book_market_reliability", ""),
        "portfolio_selection": row.get("portfolio_selection", ""),
        "open_line": line,
        "open_price": price,
        "latest_line": line,
        "latest_price": price,
    }
    calc_clv(ledger_row)
    return ledger_row


def scored_row_to_ledger(row: dict[str, str], tracked_status: str = "TRACKED") -> dict[str, Any]:
    created = now()
    price = row.get("best_price", "")
    line = row.get("line", "")
    stake_units = row.get("stake_units", "0")
    if tracked_status == "TRACKED" and (stake_units in ("", None) or float(stake_units or 0) == 0.0):
        stake_units = "0"
    ledger_row = {
        "bet_id": bet_id({
            "player": row.get("player", ""),
            "market": row.get("market", ""),
            "side": row.get("side", ""),
            "line": line,
            "book": row.get("book", ""),
            "commence_time": row.get("commence_time", ""),
        }),
        "status": tracked_status,
        "created_at_utc": created,
        "updated_at_utc": created,
        "game": row.get("game", ""),
        "commence_time": row.get("commence_time", ""),
        "player": row.get("player", ""),
        "market": row.get("market", ""),
        "side": row.get("side", ""),
        "line": line,
        "book": row.get("book", ""),
        "bet_price": price,
        "stake_units": stake_units,
        "signal": row.get("signal", ""),
        "projection": row.get("projection", ""),
        "model_probability": row.get("model_probability", ""),
        "market_probability": row.get("market_probability", ""),
        "model_edge": row.get("model_edge", ""),
        "ev_per_unit": row.get("ev_per_unit", ""),
        "live_qi": row.get("live_qi", ""),
        "alt_line_score": row.get("alt_line_score", ""),
        "markov_path": row.get("markov_path", ""),
        "book_market_reliability": row.get("book_market_reliability", ""),
        "portfolio_selection": row.get("portfolio_selection", ""),
        "open_line": line,
        "open_price": price,
        "latest_line": line,
        "latest_price": price,
    }
    calc_clv(ledger_row)
    return ledger_row


def scored_lookup(scored_rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str, str, str], dict[str, str]]:
    return {bet_key({**row, "book": row.get("book", ""), "line": row.get("line", "")}): row for row in scored_rows}


def loose_scored_lookup(scored_rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str, str], dict[str, str]]:
    out = {}
    for row in scored_rows:
        key = (
            row.get("player", "").strip().lower(),
            row.get("market", "").strip().lower(),
            row.get("side", "").strip().lower(),
            fmt_float(row.get("line"), 3),
            normalise_book(row.get("book", "")),
        )
        out[key] = row
    return out


def log_card(args: argparse.Namespace) -> None:
    ledger = read_csv(args.ledger)
    existing = {row["bet_id"]: row for row in ledger}
    scored_rows = read_csv(args.scored)
    scored = scored_lookup(scored_rows)
    loose = loose_scored_lookup(scored_rows)
    added = 0
    promoted = 0
    for row in read_csv(args.card):
        new_row = card_row_to_ledger(row, scored, loose)
        existing_row = existing.get(new_row["bet_id"])
        if existing_row is not None:
            if existing_row.get("status") == "TRACKED":
                for field, value in new_row.items():
                    if field in {"bet_id", "created_at_utc"}:
                        continue
                    existing_row[field] = value
                existing_row["status"] = "OPEN"
                existing_row["updated_at_utc"] = now()
                promoted += 1
            continue
        ledger.append(new_row)
        existing[new_row["bet_id"]] = new_row
        added += 1
    write_csv(args.ledger, ledger)
    print(f"Logged {added} new bets to {args.ledger}; promoted {promoted} tracked bets")


def track_qi(args: argparse.Namespace) -> None:
    ledger = read_csv(args.ledger)
    existing = {row["bet_id"]: row for row in ledger}
    scored_rows = read_csv(args.scored)
    keep_ids: set[str] = set()
    added = 0
    for row in scored_rows:
        if row.get("matched_wheelo") != "True":
            continue
        if row.get("market") == "Ranking/Fantasy Pts":
            continue
        if f(row.get("live_qi")) is None or (f(row.get("live_qi")) or 0) < args.min_qi:
            continue
        if f(row.get("ev_per_unit")) is None or (f(row.get("ev_per_unit")) or 0) <= args.min_ev:
            continue
        new_row = scored_row_to_ledger(
            row,
            tracked_status="OPEN" if row.get("portfolio_selection") == "PORTFOLIO_BET" else "TRACKED",
        )
        keep_ids.add(new_row["bet_id"])
        if new_row["bet_id"] in existing:
            continue
        ledger.append(new_row)
        existing[new_row["bet_id"]] = new_row
        added += 1
    ledger = [
        row for row in ledger
        if row.get("status") != "TRACKED" or row.get("bet_id") in keep_ids
    ]
    write_csv(args.ledger, ledger)
    print(f"Tracked {added} new QI>={args.min_qi:.1f} and EV>{args.min_ev:.3f} props in {args.ledger}")


def update_clv(args: argparse.Namespace) -> None:
    ledger = read_csv(args.ledger)
    scored_rows = read_csv(args.scored)
    # Prefer exact same book/line; if not present, fall back to same player/market/side/book.
    exact = {bet_key(row): row for row in scored_rows}
    loose: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in scored_rows:
        key = (
            row.get("player", "").strip().lower(),
            row.get("market", "").strip().lower(),
            row.get("side", "").strip().lower(),
            normalise_book(row.get("book", "")),
        )
        loose.setdefault(key, []).append(row)

    updated = 0
    ts = now()
    now_dt = datetime.now(timezone.utc)
    for row in ledger:
        commence_dt = parse_iso_datetime(str(row.get("commence_time", "")))
        if args.only_started and (commence_dt is None or commence_dt > now_dt):
            continue
        current = exact.get(bet_key(row))
        if current is None:
            lkey = (
                row.get("player", "").strip().lower(),
                row.get("market", "").strip().lower(),
                row.get("side", "").strip().lower(),
                normalise_book(row.get("book", "")),
            )
            candidates = loose.get(lkey, [])
            current = max(candidates, key=lambda r: f(r.get("best_price")) or 0, default=None)
        if current is None:
            continue
        row["latest_line"] = current.get("line", row.get("latest_line", ""))
        row["latest_price"] = current.get("best_price", row.get("latest_price", ""))
        row["updated_at_utc"] = ts
        if args.close:
            row["close_line"] = row["latest_line"]
            row["close_price"] = row["latest_price"]
            if row.get("status") == "OPEN":
                row["status"] = "CLOSED_PRICE"
        calc_clv(row)
        updated += 1
    write_csv(args.ledger, ledger)
    print(f"Updated CLV for {updated} bets in {args.ledger}")


def settle(args: argparse.Namespace) -> None:
    ledger = read_csv(args.ledger)
    settlements = {bet_id(row): row for row in read_csv(args.settlement)}
    updated = 0
    ts = now()
    for row in ledger:
        match = settlements.get(row["bet_id"])
        if match is None:
            # settlement files may lack game/commence_time, so use a looser key.
            row_key = (
                row.get("player", "").strip().lower(),
                row.get("market", "").strip().lower(),
                row.get("side", "").strip().lower(),
                fmt_float(row.get("line"), 3),
                normalise_book(row.get("book", "")),
            )
            for candidate in settlements.values():
                cand_key = (
                    candidate.get("player", "").strip().lower(),
                    candidate.get("market", "").strip().lower(),
                    candidate.get("side", "").strip().lower(),
                    fmt_float(candidate.get("line"), 3),
                    normalise_book(candidate.get("book", "")),
                )
                if cand_key == row_key:
                    match = candidate
                    break
        if match is None:
            continue
        row["actual"] = match.get("actual", "")
        row["result"] = match.get("result", "")
        row["flat_profit"] = match.get("unit_profit", "")
        row["stake_profit"] = match.get("stake_profit", "")
        row["status"] = "SETTLED"
        row["updated_at_utc"] = ts
        updated += 1
    write_csv(args.ledger, ledger)
    print(f"Settled {updated} bets in {args.ledger}")


def summary(args: argparse.Namespace) -> None:
    rows = read_csv(args.ledger)
    settled = [row for row in rows if row.get("status") == "SETTLED"]
    open_rows = [row for row in rows if row.get("status") != "SETTLED"]
    wins = sum(1 for row in settled if row.get("result") == "WIN")
    losses = sum(1 for row in settled if row.get("result") == "LOSS")
    pushes = sum(1 for row in settled if row.get("result") == "PUSH")
    stake_profit = sum(f(row.get("stake_profit")) or 0 for row in settled)
    staked = sum(f(row.get("stake_units")) or 0 for row in settled if row.get("result") in {"WIN", "LOSS"})
    beat = sum(1 for row in rows if row.get("clv_status") == "BEAT_CLOSE")
    clv_count = sum(1 for row in rows if row.get("clv_status") in {"BEAT_CLOSE", "MISSED_CLOSE", "FLAT_CLOSE"})
    print(f"Ledger: {args.ledger}")
    print(f"Total bets: {len(rows)} | Open/non-settled: {len(open_rows)} | Settled: {len(settled)}")
    print(f"Settled record: {wins}-{losses}-{pushes} | Stake profit: {stake_profit:+.2f}u | Stake ROI: {(stake_profit / staked if staked else 0):.1%}")
    print(f"CLV beat rate: {(beat / clv_count if clv_count else 0):.1%} ({beat}/{clv_count})")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = p.add_subparsers(dest="cmd", required=True)

    log = sub.add_parser("log-card", help="Append current portfolio card to history")
    log.add_argument("--card", type=Path, default=DEFAULT_CARD)
    log.add_argument("--scored", type=Path, default=DEFAULT_SCORED)
    log.set_defaults(func=log_card)

    clv = sub.add_parser("update-clv", help="Update latest/closing price from refreshed scored odds")
    clv.add_argument("--scored", type=Path, default=DEFAULT_SCORED)
    clv.add_argument("--close", action="store_true", help="Mark latest odds as closing odds")
    clv.add_argument(
        "--only-started",
        action="store_true",
        help="Only update bets whose commence_time is at or before the current UTC time",
    )
    clv.set_defaults(func=update_clv)

    st = sub.add_parser("settle", help="Merge settlement results into the history")
    st.add_argument("--settlement", type=Path, default=DEFAULT_SETTLEMENT)
    st.set_defaults(func=settle)

    tq = sub.add_parser("track-qi", help="Track all current scored props above a QI threshold")
    tq.add_argument("--scored", type=Path, default=DEFAULT_SCORED)
    tq.add_argument("--min-qi", type=float, default=70.0)
    tq.add_argument("--min-ev", type=float, default=0.0)
    tq.set_defaults(func=track_qi)

    sm = sub.add_parser("summary", help="Print history summary")
    sm.set_defaults(func=summary)
    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
