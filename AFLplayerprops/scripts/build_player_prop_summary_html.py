#!/usr/bin/env python3
"""Build an HTML summary of the current AFL player prop card."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BET_CSV = ROOT / "markov_bet_justifications.csv"
HTML_OUT = ROOT / "afl_player_props_markov_summary.html"


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


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_rows() -> list[dict[str, str]]:
    with BET_CSV.open() as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = load_rows()
    counts: dict[str, int] = {}
    book_counts: dict[str, int] = {}
    for row in rows:
        counts[row["signal"]] = counts.get(row["signal"], 0) + 1
        book_counts[row["book"]] = book_counts.get(row["book"], 0) + 1

    count_text = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    book_text = ", ".join(f"{k} {v}" for k, v in sorted(book_counts.items(), key=lambda kv: (-kv[1], kv[0])))

    table_rows = []
    for row in rows:
        grade = row["signal"].replace("_BET", "")
        bet = f"{row['player']} {row['market']} {row['side']} {num(row['line'])}"
        table_rows.append(
            f"""
            <tr>
              <td><span class="badge {grade.lower()}">{grade}</span></td>
              <td>{esc(bet)}</td>
              <td>{num(row.get('stake_units', '0'), 2)}u</td>
              <td>{esc(row['book'])}</td>
              <td>{num(row['price'], 2)}</td>
              <td class="pos">{pct(row['ev_per_unit'])}</td>
              <td>{num(row['live_qi'], 1)}</td>
              <td>{num(row['alt_line_score'], 4)}</td>
              <td>{esc(row['markov_path'])}</td>
            </tr>
            """
        )

    commentary = []
    for idx, row in enumerate(rows, start=1):
        commentary.append(
            f"""
            <section class="commentary">
              <h3>{idx}. {esc(row['signal'])} - {esc(row['player'])} {esc(row['market'])} {esc(row['side'])} {num(row['line'])} @ {num(row['price'], 2)} <span>{esc(row['book'])}</span></h3>
              <p><strong>Markov path:</strong> {esc(row['markov_path'])} | score {esc(row['markov_score'])}/12 | EV {pct(row['ev_per_unit'])} | QI {num(row['live_qi'], 1)} | Alt score {num(row['alt_line_score'], 4)}</p>
              <p>{esc(row['justification'])}</p>
              {"<p><strong>Ladder:</strong> " + esc(row["ladder_note"]) + "</p>" if row.get("ladder_note") else ""}
              <p class="risk"><strong>Risk:</strong> {esc(row['risk'])}</p>
            </section>
            """
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AFL Player Props Markov Summary</title>
  <style>
    :root {{
      --ink: #111827;
      --muted: #4b5563;
      --line: #d1d5db;
      --panel: #f8fafc;
      --a: #0f766e;
      --b: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      padding: 28px 34px 18px;
      border-bottom: 1px solid var(--line);
      background: #f9fafb;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 28px 0 12px; font-size: 20px; }}
    h3 {{ margin: 0 0 8px; font-size: 16px; }}
    h3 span {{ color: var(--muted); font-weight: normal; }}
    p {{ line-height: 1.45; }}
    .meta {{ color: var(--muted); margin: 0; max-width: 980px; }}
    main {{ padding: 22px 34px 40px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin: 0 0 18px;
    }}
    .card {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 14px;
    }}
    .card strong {{ display: block; margin-bottom: 6px; }}
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
    th {{ background: var(--ink); color: white; }}
    tr:nth-child(even) td {{ background: #f9fafb; }}
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
    .pos {{ color: #047857; font-weight: bold; }}
    .commentary {{
      border-top: 1px solid var(--line);
      padding: 16px 0;
      max-width: 1080px;
    }}
    .risk {{ color: #7c2d12; }}
    @media print {{
      header {{ background: white; }}
      main {{ padding: 16px; }}
      .commentary {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AFL Player Props Markov Summary</h1>
    <p class="meta">Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} from WheeloRatings + Odds API. Scope: Western Bulldogs v Melbourne only; GWS v Brisbane returned no live player prop bookmakers. Marks were unavailable through Odds API.</p>
  </header>
  <main>
    <section class="cards">
      <div class="card"><strong>Cleaned Card</strong>{len(rows)} best risk-adjusted alternate lines</div>
      <div class="card"><strong>Grades</strong>{esc(count_text)}</div>
      <div class="card"><strong>Best Book Split</strong>{esc(book_text)}</div>
    </section>

    <h2>Summary Card</h2>
    <table>
      <thead>
        <tr>
          <th>Grade</th><th>Bet</th><th>Stake</th><th>Best AU Bookie</th><th>Price</th><th>EV</th><th>QI</th><th>Alt Score</th><th>Markov Path</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>

    <h2>Detailed Markov Commentary</h2>
    <p>The chain means: does Wheelo like it, does probability agree, is the price wrong, and is confidence high?</p>
    {''.join(commentary)}
  </main>
</body>
</html>
"""
    HTML_OUT.write_text(html)
    print(HTML_OUT)


if __name__ == "__main__":
    main()
