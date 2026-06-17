#!/usr/bin/env python3
"""Publish the full BetMate Edge AFL props report to a GitHub Pages-friendly site."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
LOCAL_TZ = ZoneInfo("Australia/Melbourne")
DEFAULT_SOURCE = ROOT / "afl_player_props_stk_haw_walters_report.html"
DEFAULT_SITE_DIR = ROOT / "docs"
DEFAULT_SITE_FILE = "betmateedgeaflprops.html"
CUSTOM_DOMAIN = "aflprops.betmateedge.com"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--refresh", action="store_true", help="Run the live refresh pipeline before publishing.")
    p.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR, help="Output directory for GitHub Pages files.")
    p.add_argument("--site-file", default=DEFAULT_SITE_FILE, help="Primary HTML filename inside the site directory.")
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Existing local HTML report to publish when not refreshing.")
    p.add_argument("--min-qi", type=float, default=80.0, help="Refresh pipeline min QI when --refresh is used.")
    p.add_argument("--high-value-min-price", type=float, default=1.8, help="Refresh pipeline high-value price floor when --refresh is used.")
    p.add_argument("--round-label-override", default=None, help="Optional round label override for refresh pipeline.")
    return p


def publish_site(source_html: Path, site_dir: Path, site_file: str, payload: dict[str, object] | None) -> Path:
    site_dir.mkdir(parents=True, exist_ok=True)
    target = site_dir / site_file
    index_target = site_dir / "index.html"
    archive_target = site_dir / "full-report.html"
    premium_archive = site_dir / "premium-archive.html"

    if source_html.resolve() != target.resolve():
        shutil.copy2(source_html, target)
    shutil.copy2(source_html, index_target)
    shutil.copy2(source_html, archive_target)

    standalone_markov = ROOT / "afl_player_props_markov_summary.html"
    if standalone_markov.exists():
        shutil.copy2(standalone_markov, premium_archive)

    metadata = {
        "published_at_aest": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "source_html": str(source_html.name),
        "site_file": site_file,
        "index_file": "index.html",
        "custom_domain": CUSTOM_DOMAIN,
    }
    if payload:
        metadata.update(
            {
                "updated_at": payload.get("updated_at", ""),
                "round_label": payload.get("roundLabel", ""),
                "summary": payload.get("summary", {}),
            }
        )

    (site_dir / "latest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    (site_dir / "CNAME").write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")
    return target


def main() -> None:
    args = parser().parse_args()
    payload: dict[str, object] | None = None
    source_html = args.source

    if args.refresh:
        import betmate_edge_refresh_server as refresh_server

        output_path = args.site_dir / args.site_file
        payload = refresh_server.refresh_pipeline(
            game=None,
            output=str(output_path),
            min_qi=args.min_qi,
            high_value_min_price=args.high_value_min_price,
            round_label_override=args.round_label_override,
        )
        source_html = output_path

    if not source_html.exists():
        raise SystemExit(f"Source HTML not found: {source_html}")

    published = publish_site(source_html, args.site_dir, args.site_file, payload)
    print(f"Published GitHub Pages site to {published}")


if __name__ == "__main__":
    main()
