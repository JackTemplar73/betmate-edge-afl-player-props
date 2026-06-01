#!/usr/bin/env python3
"""Create Markov-style row-by-row justifications for Odds API + Wheelo bets."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SCORED = ROOT / "oddsapi_wheelo_ev_qi.csv"
OUT_MD = ROOT / "markov_bet_justifications.md"
OUT_CSV = ROOT / "markov_bet_justifications.csv"
OUT_VERBOSE_MD = ROOT / "markov_bet_commentary.md"


ACTION_SIGNALS = {"A_BET", "B_BET"}
STATE_ORDER = {
    "projection": ["Against", "Neutral", "Lean", "Strong"],
    "probability": ["Market low", "Fair", "Positive", "Dominant"],
    "price": ["No edge", "Thin", "Good", "Mispriced"],
    "confidence": ["Low", "Medium", "High", "Elite"],
}


def f(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(value: Any) -> str:
    return f"{100 * f(value):.1f}%"


def money(value: Any) -> str:
    return f"{f(value):.2f}"


def projection_state(row: dict[str, str]) -> str:
    support = row["wheelo_support"]
    if "strong support" in support:
        return "Strong"
    if "lean support" in support:
        return "Lean"
    if "neutral" in support:
        return "Neutral"
    return "Against"


def probability_state(row: dict[str, str]) -> str:
    edge = f(row["model_edge"])
    prob = f(row["model_probability"])
    if edge >= 0.15 or prob >= 0.80:
        return "Dominant"
    if edge >= 0.06 or prob >= 0.65:
        return "Positive"
    if edge >= 0.02:
        return "Fair"
    return "Market low"


def price_state(row: dict[str, str]) -> str:
    ev = f(row["ev_per_unit"])
    if ev >= 0.25:
        return "Mispriced"
    if ev >= 0.10:
        return "Good"
    if ev >= 0.03:
        return "Thin"
    return "No edge"


def confidence_state(row: dict[str, str]) -> str:
    qi = f(row["live_qi"])
    if qi >= 90:
        return "Elite"
    if qi >= 80:
        return "High"
    if qi >= 70:
        return "Medium"
    return "Low"


def transition_score(state: str, family: str) -> int:
    return STATE_ORDER[family].index(state)


def markov_path(row: dict[str, str]) -> tuple[str, int]:
    states = [
        ("projection", projection_state(row)),
        ("probability", probability_state(row)),
        ("price", price_state(row)),
        ("confidence", confidence_state(row)),
    ]
    score = sum(transition_score(state, family) for family, state in states)
    label = " -> ".join(state for _, state in states)
    return label, score


def primary_risk(row: dict[str, str]) -> str:
    market = row["market"]
    if market == "Goals":
        return "Goals are highest variance; price must compensate for scoring role volatility."
    if market == "Tackles":
        return "Tackle props depend on game script and pressure exposure."
    if market == "Disposals":
        return "Disposal props are more stable, but role/rotation drift can still break projection."
    return "Market is less backtest-approved; keep as information unless separately validated."


def justification(row: dict[str, str]) -> str:
    side = row["side"].lower()
    gap = f(row["stat_gap"])
    gap_text = f"{gap:+.1f}"
    if row["market"] == "Goals":
        proj_unit = "goals avg"
    elif row["market"] == "Ranking/Fantasy Pts":
        proj_unit = "fantasy avg"
    else:
        proj_unit = row["market"].lower()
    return (
        f"Wheelo projects {row['projection']} {proj_unit} against a {row['line']} line, "
        f"creating a {gap_text} stat gap for the {side}. The Markov state path is "
        f"{markov_path(row)[0]}, meaning the row moves from projection support into a "
        f"positive probability state, then through the price/EV state, and finishes with "
        f"{row['live_qi']} QI. Model probability is {pct(row['model_probability'])} versus "
        f"market {pct(row['market_probability'])}, producing {pct(row['ev_per_unit'])} EV."
    )


def commentary(row: dict[str, str]) -> list[str]:
    path, score = markov_path(row)
    p_state = projection_state(row)
    prob_state = probability_state(row)
    pr_state = price_state(row)
    c_state = confidence_state(row)
    edge = f(row["model_edge"])
    ev = f(row["ev_per_unit"])
    gap = f(row["stat_gap"])
    market = row["market"]
    side = row["side"].lower()
    projection = f(row["projection"])
    line = f(row["line"])
    prob = f(row["model_probability"])
    market_prob = f(row["market_probability"])
    price = f(row["price"])

    if market == "Goals":
        stat_unit = "goal rate"
        distribution_note = (
            "Goal scoring is treated as a volatile scoring-chain state: player role, forward-half share, "
            "team inside-50 volume, and conversion all matter. Because of that, I want a visibly positive "
            "gap and a price that pays for variance."
        )
    elif market == "Tackles":
        stat_unit = "tackle rate"
        distribution_note = (
            "Tackles are modelled as a pressure/contact state. The bet improves when Wheelo tackle rate is "
            "above the line and the matchup projects enough contest density for repeat tackle opportunities."
        )
    elif market == "Disposals":
        stat_unit = "disposal rate"
        distribution_note = (
            "Disposals are the most stable of these prop states, but still depend on role, centre-bounce exposure, "
            "team possession share, and whether the player is used as a link option or a deeper defender."
        )
    else:
        stat_unit = "rating/fantasy rate"
        distribution_note = (
            "This market aggregates several stat channels, so it is broader but less cleanly backtest-approved "
            "than disposals, tackles, or goals."
        )

    if p_state == "Strong":
        projection_text = (
            f"The chain opens in a strong projection state: Wheelo has {row['player']} at {projection:.2f} "
            f"against a {line:.1f} line, so the {side} starts with a {gap:+.2f} {stat_unit} cushion."
        )
    elif p_state == "Lean":
        projection_text = (
            f"The chain opens in a lean projection state: Wheelo is on the right side, but the cushion is "
            f"only {gap:+.2f}. This is why the row needs the market price to do more of the work."
        )
    else:
        projection_text = (
            f"The projection state is not dominant. Wheelo is close to the line, so this row depends more "
            f"on price and probability than raw stat separation."
        )

    if prob_state == "Dominant":
        prob_text = (
            f"The probability transition is the key confirmation: model probability is {prob * 100:.1f}% "
            f"versus market {market_prob * 100:.1f}%, a {edge * 100:+.1f} point edge. That moves the chain "
            f"into a dominant probability state."
        )
    elif prob_state == "Positive":
        prob_text = (
            f"The probability transition is positive rather than dominant: {prob * 100:.1f}% model probability "
            f"against {market_prob * 100:.1f}% market. The edge is real, but thinner."
        )
    else:
        prob_text = (
            f"The probability state is only fair. This would need either a better price or extra role/news "
            f"confirmation before staking aggressively."
        )

    if pr_state == "Mispriced":
        price_text = (
            f"The price state is the strongest part of the bet. At {price:.2f}, expected value is "
            f"{ev * 100:+.1f}%, so the market is paying materially above the model's fair probability."
        )
    elif pr_state == "Good":
        price_text = (
            f"The price state is good: {price:.2f} gives {ev * 100:+.1f}% EV. That is enough to justify "
            f"a bet when the projection and probability states agree."
        )
    else:
        price_text = (
            f"The price state is thin: {price:.2f} gives {ev * 100:+.1f}% EV. This can still be playable, "
            f"but it should not be treated like the higher mispricing rows."
        )

    if c_state == "Elite":
        confidence_text = (
            f"The chain finishes in elite confidence with QI {row['live_qi']}. That means support, edge, "
            f"price, and book availability are all aligned."
        )
    elif c_state == "High":
        confidence_text = (
            f"The chain finishes in high confidence with QI {row['live_qi']}. It is still a positive setup, "
            f"but one element is less than perfect, usually price thickness or projection margin."
        )
    else:
        confidence_text = (
            f"The chain finishes below high confidence with QI {row['live_qi']}. This is a smaller-stake "
            f"or watch-only profile unless the line improves."
        )

    return [
        f"**Markov read:** `{path}` with score `{score}/12`.",
        projection_text,
        distribution_note,
        prob_text,
        price_text,
        confidence_text,
        f"**Failure mode:** {primary_risk(row)}",
    ]


def decision(row: dict[str, str], score: int) -> str:
    if row["signal"] == "A_BET" and score >= 9:
        return "A-grade: model, price, and QI all confirm."
    if row["signal"] == "A_BET":
        return "A signal, but stake conservatively if variance is high."
    if row["signal"] == "B_BET" and score >= 8:
        return "B-grade: playable edge with one modest weakness."
    return "B-grade watch: edge exists, but one Markov state is thinner."


def load_rows() -> list[dict[str, str]]:
    with SCORED.open() as f_in:
        rows = [
            row for row in csv.DictReader(f_in)
            if row["signal"] in ACTION_SIGNALS and row.get("portfolio_selection") == "PORTFOLIO_BET"
        ]
    return sorted(rows, key=lambda r: (r["signal"] == "A_BET", f(r.get("alt_line_score")), f(r["ev_per_unit"]), f(r["live_qi"])), reverse=True)


def write_outputs(rows: list[dict[str, str]]) -> None:
    out_rows = []
    for row in rows:
        path, score = markov_path(row)
        enriched = {
            "signal": row["signal"],
            "player": row["player"],
            "market": row["market"],
            "side": row["side"],
            "line": row["line"],
            "price": row["best_price"],
            "book": row["book"],
            "projection": row["projection"],
            "wheelo_support": row["wheelo_support"],
            "stat_gap": row["stat_gap"],
            "model_probability": row["model_probability"],
            "market_probability": row["market_probability"],
            "model_edge": row["model_edge"],
            "ev_per_unit": row["ev_per_unit"],
            "live_qi": row["live_qi"],
            "alt_line_score": row.get("alt_line_score", ""),
            "stake_units": row.get("stake_units", ""),
            "portfolio_selection": row.get("portfolio_selection", ""),
            "book_market_reliability": row.get("book_market_reliability", ""),
            "line_selection": row.get("line_selection", ""),
            "ladder_note": row.get("ladder_note", ""),
            "markov_path": path,
            "markov_score": score,
            "decision": decision(row, score),
            "risk": primary_risk(row),
            "justification": justification(row),
        }
        out_rows.append(enriched)

    with OUT_CSV.open("w", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    lines = [
        "# Markov Bet Justifications",
        "",
        "Scope: A_BET and B_BET rows from `oddsapi_wheelo_ev_qi.csv`.",
        "",
        "State path format: Projection support -> Probability edge -> Price/EV state -> QI confidence.",
        "",
    ]
    for idx, row in enumerate(out_rows, start=1):
        lines.extend(
            [
                f"## {idx}. {row['signal']} - {row['player']} {row['market']} {row['side']} {row['line']} @ {row['price']}",
                "",
                f"- Book: {row['book']}",
                f"- Markov path: {row['markov_path']} | score {row['markov_score']}/12",
                f"- Model: projection {row['projection']}, probability {pct(row['model_probability'])}, market {pct(row['market_probability'])}, EV {pct(row['ev_per_unit'])}, QI {row['live_qi']}",
                f"- Portfolio: {row.get('portfolio_selection', '')}; stake {row.get('stake_units', '')}u; alt-line score {row.get('alt_line_score', '')}",
                f"- Ladder: {row.get('ladder_note', '') or 'No higher-ranked alternate retained.'}",
                f"- Decision: {row['decision']}",
                f"- Justification: {row['justification']}",
                f"- Main risk: {row['risk']}",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(lines))

    verbose = [
        "# Expanded Markov Commentary",
        "",
        "Scope: every A_BET and B_BET from the live Odds API + Wheelo sheet.",
        "",
        "Interpretation: a bet is treated as a four-state chain: projection support, probability edge, price/EV, then confidence/QI. The strongest bets transition cleanly through all four states.",
        "",
    ]
    for idx, row in enumerate(out_rows, start=1):
        verbose.extend(
            [
                f"## {idx}. {row['signal']} - {row['player']} {row['market']} {row['side']} {row['line']} @ {row['price']} ({row['book']})",
                "",
            ]
        )
        verbose.extend(commentary(row))
        verbose.append("")
    OUT_VERBOSE_MD.write_text("\n\n".join(verbose))


def main() -> None:
    rows = load_rows()
    write_outputs(rows)
    print(f"Wrote {len(rows)} Markov justifications")
    print(OUT_MD.name)
    print(OUT_CSV.name)
    print(OUT_VERBOSE_MD.name)


if __name__ == "__main__":
    main()
