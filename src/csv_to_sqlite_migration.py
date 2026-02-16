from __future__ import annotations

import csv
import logging
import os
import re
from collections import defaultdict
from pathlib import Path

from src.storage import (
    append_analytics_event,
    append_landing_event_if_new,
    date_token_to_iso,
    export_all_tables_to_csv,
    normalize_date_token,
    upsert_table_rows,
)


DATE_FILE_RE = re.compile(r"^\d{8}_")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_iso_date(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        return raw
    if len(raw) == 8 and raw.isdigit():
        normalize_date_token(raw)
        return date_token_to_iso(raw)
    return ""


def find_sources(data_dir: Path, suffix: str) -> list[Path]:
    direct = sorted(data_dir.glob(f"*_{suffix}"))
    archive = sorted((data_dir / "archive").glob(f"*_{suffix}"))
    matched = [p for p in (direct + archive) if DATE_FILE_RE.match(p.name)]
    cumulative = data_dir / suffix
    if cumulative.exists():
        matched.append(cumulative)
    return matched


def parse_metric_int(raw: str, *, source_path: Path, metric: str) -> int:
    text = (raw or "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        logging.warning(
            "Invalid numeric value in landing_cvr source=%s metric=%s value=%s",
            source_path,
            metric,
            text,
        )
        return 0


def migrate_landing_events(data_dir: Path, dry_run: bool) -> int:
    count = 0
    for path in find_sources(data_dir, "landing_events.csv"):
        for row in read_rows(path):
            date_iso = normalize_iso_date(row.get("date", ""))
            if not date_iso:
                continue
            if dry_run:
                count += 1
                continue
            inserted = append_landing_event_if_new(
                timestamp=(row.get("timestamp", "") or "").strip() or "1970-01-01T00:00:00",
                date_iso=date_iso,
                session_id=(row.get("session_id", "") or "").strip(),
                language=(row.get("language", "") or "").strip(),
                channel=(row.get("channel", "") or "").strip(),
                source_id=(row.get("source_id", "") or "").strip(),
                post_id=(row.get("post_id", "") or "").strip(),
                event_type=(row.get("event_type", "") or "").strip(),
                cta_type=(row.get("cta_type", "") or "").strip(),
                lead_email=(row.get("lead_email", "") or "").strip(),
                consent=(row.get("consent", "0") or "0").strip() in {"1", "true", "True"},
            )
            if inserted:
                count += 1
    return count


def migrate_landing_cvr(data_dir: Path, dry_run: bool) -> int:
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"visitors": 0, "pilot_cta": 0, "first_scan_cta": 0, "total_cta": 0}
    )
    for path in find_sources(data_dir, "landing_cvr.csv"):
        for row in read_rows(path):
            date_iso = normalize_iso_date(row.get("date", ""))
            channel = (row.get("channel", "") or "").strip()
            if not date_iso or not channel:
                continue
            key = (date_iso, channel)
            for metric in ["visitors", "pilot_cta", "first_scan_cta", "total_cta"]:
                raw = (row.get(metric, "") or "").strip()
                grouped[key][metric] += parse_metric_int(raw, source_path=path, metric=metric)

    if dry_run:
        return len(grouped)

    rows = []
    for (date_iso, channel), values in sorted(grouped.items()):
        rows.append(
            {
                "date": date_iso,
                "channel": channel,
                "visitors": str(values["visitors"]),
                "pilot_cta": str(values["pilot_cta"]),
                "first_scan_cta": str(values["first_scan_cta"]),
                "total_cta": str(values["total_cta"]),
            }
        )
    upsert_table_rows("landing_cvr_daily", rows, overwrite_date=None)
    return len(rows)


def migrate_generic(data_dir: Path, table_name: str, suffix: str, key_fields: list[str], dry_run: bool) -> int:
    by_key: dict[tuple[str, ...], dict[str, str]] = {}
    for path in find_sources(data_dir, suffix):
        for row in read_rows(path):
            if "date" in row:
                row["date"] = normalize_iso_date(row.get("date", ""))
            if not row.get("date", ""):
                continue
            key = tuple((row.get(k, "") or "").strip() for k in key_fields)
            if any(not k for k in key):
                continue
            by_key[key] = {k: (v or "").strip() for k, v in row.items()}

    if dry_run:
        return len(by_key)

    upsert_table_rows(table_name, list(by_key.values()), overwrite_date=None)
    return len(by_key)


def migrate_analytics(data_dir: Path, dry_run: bool) -> int:
    count = 0
    for path in find_sources(data_dir, "analytics_events.csv"):
        for row in read_rows(path):
            date_iso = normalize_iso_date(row.get("date", ""))
            if not date_iso:
                continue
            count += 1
            if dry_run:
                continue
            append_analytics_event(
                timestamp=(row.get("timestamp", "") or "").strip() or "1970-01-01T00:00:00",
                date_iso=date_iso,
                event_name=(row.get("event_name", "") or "").strip(),
                client_id=(row.get("client_id", "") or "").strip(),
                channel=(row.get("channel", "") or "").strip(),
                language=(row.get("language", "") or "").strip(),
                status=(row.get("status", "") or "").strip(),
                payload=(row.get("payload", "") or "").strip(),
            )
    return count


def run_migration(root: Path, dry_run: bool) -> dict[str, int]:
    data_dir = root / "data"
    os.environ.setdefault("KTRIPPEDIA_DATA_DIR", str(data_dir))

    stats: dict[str, int] = {}
    stats["landing_events"] = migrate_landing_events(data_dir, dry_run)
    stats["landing_cvr_daily"] = migrate_landing_cvr(data_dir, dry_run)
    stats["analytics_events"] = migrate_analytics(data_dir, dry_run)
    stats["trip_safety"] = migrate_generic(data_dir, "trip_safety", "trip_safety.csv", ["date", "scenario_id"], dry_run)
    stats["interview_log"] = migrate_generic(data_dir, "interview_log", "interview_log.csv", ["date", "interview_id"], dry_run)
    stats["b2b_pipeline"] = migrate_generic(data_dir, "b2b_pipeline", "b2b_pipeline.csv", ["date", "meeting_id"], dry_run)
    stats["trip_pass_pricing"] = migrate_generic(
        data_dir,
        "trip_pass_pricing",
        "trip_pass_pricing.csv",
        ["date", "response_id"],
        dry_run,
    )
    stats["guardrail_checklist"] = migrate_generic(
        data_dir,
        "guardrail_checklist",
        "guardrail_checklist.csv",
        ["date", "check_id"],
        dry_run,
    )
    stats["community_outreach_log"] = migrate_generic(
        data_dir,
        "community_outreach_log",
        "community_outreach_log.csv",
        ["date", "post_id"],
        dry_run,
    )

    if not dry_run:
        export_all_tables_to_csv()

    return stats
