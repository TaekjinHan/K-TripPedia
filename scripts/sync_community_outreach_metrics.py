#!/usr/bin/env python3
"""Sync community_outreach_log KPI fields from landing events."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.storage import fetch_metrics_rows, normalize_date_token, upsert_table_rows, date_token_to_iso


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync outreach metrics from landing events")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--date", default=dt.datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    os.environ["KTRIPPEDIA_DATA_DIR"] = str(root / "data")

    date_token = normalize_date_token(args.date)
    date_iso = date_token_to_iso(date_token)

    outreach_rows = fetch_metrics_rows("community_outreach_log", date_iso)
    event_rows = fetch_metrics_rows("landing_events", date_iso)

    metrics: dict[tuple[str, str], dict[str, int]] = {}
    for event in event_rows:
        if str(event.get("channel", "")).strip() != "community":
            continue
        src = str(event.get("source_id", "")).strip() or ""
        post_id = str(event.get("post_id", "")).strip() or ""
        if not post_id:
            continue
        key = (src, post_id)
        if key not in metrics:
            metrics[key] = {"visitors": 0, "cta": 0, "leads": 0}
        event_type = str(event.get("event_type", "")).strip()
        if event_type == "visit":
            metrics[key]["visitors"] += 1
        elif event_type == "cta_click":
            metrics[key]["cta"] += 1
        elif event_type == "lead_submit":
            metrics[key]["leads"] += 1

    updates = []
    for row in outreach_rows:
        platform = str(row.get("platform", "")).strip().lower()
        post_id = str(row.get("post_id", "")).strip().lower()
        values = metrics.get((platform, post_id), {"visitors": 0, "cta": 0, "leads": 0})
        updates.append(
            {
                "date": date_iso,
                "platform": platform,
                "community_name": str(row.get("community_name", "")),
                "post_id": post_id,
                "url": str(row.get("url", "")),
                "language": str(row.get("language", "EN")),
                "impressions": str(row.get("impressions", "0")),
                "clicks": str(row.get("clicks", "0")),
                "visitors": str(values["visitors"]),
                "cta": str(values["cta"]),
                "leads": str(values["leads"]),
                "status": "active" if values["visitors"] > 0 else str(row.get("status", "ready")),
                "notes": str(row.get("notes", "")),
            }
        )

    if updates:
        upsert_table_rows("community_outreach_log", updates, overwrite_date=None)

    print(f"Synced {len(updates)} outreach rows for {date_iso}")


if __name__ == "__main__":
    main()
