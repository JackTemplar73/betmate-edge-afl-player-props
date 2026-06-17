#!/usr/bin/env python3
"""Write an archived premium-summary stub that points to the full agent report."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_OUT = ROOT / "afl_player_props_markov_summary.html"
FULL_REPORT = ROOT / "afl_player_props_stk_haw_walters_report.html"


def main() -> None:
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Premium Bets Archive</title>
  <style>
    :root {{
      --ink: #111827;
      --muted: #4b5563;
      --line: #d1d5db;
      --panel: #f8fafc;
      --link: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    main {{
      max-width: 880px;
      margin: 0 auto;
      padding: 48px 24px 64px;
    }}
    .panel {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 12px;
      padding: 24px;
    }}
    h1 {{ margin: 0 0 12px; font-size: 28px; }}
    p {{ margin: 0 0 14px; line-height: 1.5; }}
    a {{
      color: var(--link);
      font-weight: 700;
      text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}
    code {{
      background: #eef2ff;
      border-radius: 6px;
      padding: 2px 6px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>Premium Bets Moved</h1>
      <p>This standalone page is now archived so there is only one live UI source of truth.</p>
      <p>Use the full agent report here:</p>
      <p><a href="{FULL_REPORT.as_uri()}">{FULL_REPORT.name}</a></p>
      <p>Then open the <code>Premium Bets</code> tab for the current premium card and the last-round premium results.</p>
    </section>
  </main>
</body>
</html>
"""
    HTML_OUT.write_text(html)
    print(HTML_OUT.name)


if __name__ == "__main__":
    main()
