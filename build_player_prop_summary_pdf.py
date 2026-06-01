#!/usr/bin/env python3
"""Build a PDF summary of the current AFL player prop card."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
BET_CSV = ROOT / "markov_bet_justifications.csv"
PDF_OUT = ROOT / "afl_player_props_markov_summary.pdf"


def pct(value: str) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "-"


def num(value: str, digits: int = 1) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "-"


def load_rows() -> list[dict[str, str]]:
    with BET_CSV.open() as f:
        return list(csv.DictReader(f))


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("&", "&amp;"), style)


def build_pdf(rows: list[dict[str, str]]) -> None:
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title="AFL Player Props Markov Summary",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8,
    )
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=6,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1f2937"),
    )
    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#374151"),
    )

    story = []
    story.append(para("AFL Player Props Markov Summary", title))
    story.append(
        para(
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} from Model data + Odds API. "
            "Scope: current scored AFL player-prop card. "
            "Marks were unavailable through Odds API.",
            body,
        )
    )
    story.append(Spacer(1, 5))

    counts: dict[str, int] = {}
    book_counts: dict[str, int] = {}
    for row in rows:
        counts[row["signal"]] = counts.get(row["signal"], 0) + 1
        book_counts[row["book"]] = book_counts.get(row["book"], 0) + 1
    story.append(para("Summary", h1))
    summary_text = (
        f"Cleaned card: {len(rows)} best risk-adjusted alternate lines. "
        + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        + ". Best book split: "
        + ", ".join(f"{k} {v}" for k, v in sorted(book_counts.items(), key=lambda kv: (-kv[1], kv[0])))
        + "."
    )
    story.append(para(summary_text, body))
    story.append(Spacer(1, 5))

    table_rows = [[
        "Grade", "Bet", "Stake", "Book", "Price", "EV", "QI", "Alt", "Markov Path"
    ]]
    for row in rows:
        bet = f"{row['player']} {row['market']} {row['side']} {num(row['line'])}"
        table_rows.append([
            row["signal"].replace("_BET", ""),
            para(bet, small),
            f"{num(row.get('stake_units', '0'), 2)}u",
            para(row["book"], small),
            num(row["price"], 2),
            pct(row["ev_per_unit"]),
            num(row["live_qi"], 1),
            num(row["alt_line_score"], 4),
            para(row["markov_path"], small),
        ])

    table = LongTable(table_rows, colWidths=[15 * mm, 50 * mm, 16 * mm, 30 * mm, 15 * mm, 17 * mm, 14 * mm, 18 * mm, 72 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)

    story.append(PageBreak())
    story.append(para("Markov Commentary", h1))
    story.append(
        para(
            "Each bet is scored as a four-state chain: projection support -> probability edge -> price/EV state -> QI confidence. "
            "The strongest bets transition cleanly through all four states.",
            body,
        )
    )

    for idx, row in enumerate(rows, start=1):
        story.append(para(f"{idx}. {row['signal']} - {row['player']} {row['market']} {row['side']} {num(row['line'])} @ {num(row['price'], 2)} ({row['book']})", h2))
        story.append(
            para(
                f"Markov path: {row['markov_path']} | score {row['markov_score']}/12 | stake {num(row.get('stake_units', '0'), 2)}u | EV {pct(row['ev_per_unit'])} | QI {num(row['live_qi'], 1)} | Alt score {num(row['alt_line_score'], 4)}.",
                body,
            )
        )
        story.append(para(row["justification"], body))
        if row.get("ladder_note"):
            story.append(para(f"Ladder: {row['ladder_note']}", small))
        story.append(para(f"Risk: {row['risk']}", small))
        story.append(Spacer(1, 4))

    story.append(PageBreak())
    story.append(para("Method Notes", h1))
    story.append(
        para(
            "A_BET means strong Model data support plus a clear model edge and high QI. B_BET means positive EV with one softer state, usually a smaller projection cushion or thinner price. "
            "The alternate-line selector keeps one best risk-adjusted line per player/market/side using EV, hit-probability stability, QI, and a market volatility adjustment.",
            body,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        para(
            "Sources: Model data current player pack and team context, The Odds API AU bookmaker markets. This is a model output, not a guarantee; prices can move and late team/role news can invalidate an edge.",
            body,
        )
    )

    doc.build(story)


def main() -> None:
    rows = load_rows()
    build_pdf(rows)
    print(PDF_OUT)


if __name__ == "__main__":
    main()
