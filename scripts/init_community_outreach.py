#!/usr/bin/env python3
"""Initialize community outreach tracking rows and share links."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.storage import date_token_to_iso, normalize_date_token, upsert_table_rows


def build_rows(date_iso: str, base_url: str) -> list[dict[str, str]]:
    base = base_url.rstrip("/")
    rows: list[dict[str, str]] = []
    presets = [
        ("reddit", "r1"),
        ("reddit", "r2"),
        ("reddit", "r3"),
        ("reddit", "r4"),
        ("facebook", "f1"),
        ("facebook", "f2"),
        ("facebook", "f3"),
        ("facebook", "f4"),
    ]
    for platform, post_id in presets:
        query = urlencode(
            {
                "ch": "community",
                "src": platform,
                "post_id": post_id,
            }
        )
        rows.append(
            {
                "date": date_iso,
                "platform": platform,
                "community_name": "",
                "post_id": post_id,
                "url": f"{base}/?{query}",
                "language": "EN",
                "impressions": "0",
                "clicks": "0",
                "visitors": "0",
                "cta": "0",
                "leads": "0",
                "status": "ready",
                "notes": "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Init community outreach log and links")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--date", default=dt.datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    parser.add_argument("--base-url", default="http://localhost:8501", help="Landing base URL")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite same-date rows")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    os.environ["KTRIPPEDIA_DATA_DIR"] = str(root / "data")

    date_token = normalize_date_token(args.date)
    date_iso = date_token_to_iso(date_token)
    rows = build_rows(date_iso=date_iso, base_url=args.base_url)
    overwrite_date = date_iso if args.overwrite else None
    upsert_table_rows("community_outreach_log", rows, overwrite_date=overwrite_date)

    print(f"Initialized community_outreach_log for {date_iso}")
    for row in rows:
        print(f"{row['post_id']}: {row['url']}")


if __name__ == "__main__":
    main()
