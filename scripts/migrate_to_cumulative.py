#!/usr/bin/env python3
"""One-time migration: dated artifacts -> cumulative files + archive."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import OrderedDict
from pathlib import Path


CSV_PATTERNS = {
    "trip_safety.csv": "*_trip_safety.csv",
    "interview_log.csv": "*_interview_log.csv",
    "landing_cvr.csv": "*_landing_cvr.csv",
    "landing_events.csv": "*_landing_events.csv",
    "b2b_pipeline.csv": "*_b2b_pipeline.csv",
    "trip_pass_pricing.csv": "*_trip_pass_pricing.csv",
    "guardrail_checklist.csv": "*_guardrail_checklist.csv",
    "analytics_events.csv": "*_analytics_events.csv",
}

DATE_FILE_RE = re.compile(r"^\d{8}_")


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    return fields, rows


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in fields})


def merge_full_dedup(fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out = []
    for row in rows:
        key = tuple((row.get(f, "") or "").strip() for f in fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def merge_landing_events(fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    key_fields = ["date", "session_id", "channel", "source_id", "post_id", "event_type", "cta_type", "lead_email"]
    seen = set()
    out = []

    def normalize_or_hash_lead_email(value: str) -> str:
        normalized = (value or "").strip().lower()
        if not normalized:
            return ""
        if normalized.startswith("sha256:"):
            return normalized
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    for row in rows:
        merged_row = dict(row)
        merged_row["lead_email"] = normalize_or_hash_lead_email(row.get("lead_email", ""))
        key = tuple((merged_row.get(f, "") or "").strip() for f in key_fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(merged_row)
    return out


def merge_landing_cvr(fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: OrderedDict[tuple[str, str], dict[str, str]] = OrderedDict()
    for row in rows:
        date = (row.get("date", "") or "").strip()
        channel = (row.get("channel", "") or "").strip()
        if not date or not channel:
            continue
        key = (date, channel)
        if key not in grouped:
            grouped[key] = {f: "" for f in fields}
            grouped[key]["date"] = date
            grouped[key]["channel"] = channel
            for m in ["visitors", "pilot_cta", "first_scan_cta", "total_cta"]:
                grouped[key][m] = "0"
        for metric in ["visitors", "pilot_cta", "first_scan_cta", "total_cta"]:
            raw = (row.get(metric, "") or "").strip()
            inc = int(float(raw)) if raw else 0
            grouped[key][metric] = str(int(grouped[key][metric]) + inc)
    return list(grouped.values())


def move_to_archive(path: Path, archive_root: Path) -> None:
    archive_root.mkdir(parents=True, exist_ok=True)
    target = archive_root / path.name
    if target.exists():
        target.unlink()
    path.rename(target)


def migrate_csvs(root: Path) -> None:
    data_dir = root / "data"
    archive_dir = data_dir / "archive"

    for target_name, pattern in CSV_PATTERNS.items():
        target = data_dir / target_name
        matched = [p for p in sorted(data_dir.glob(pattern)) if DATE_FILE_RE.match(p.name)]
        matched += [p for p in sorted(archive_dir.glob(pattern)) if DATE_FILE_RE.match(p.name)]
        if not matched:
            continue

        all_fields = []
        all_rows: list[dict[str, str]] = []

        existing_fields, existing_rows = read_rows(target)
        if existing_fields:
            all_fields = existing_fields
            all_rows.extend(existing_rows)

        for path in matched:
            fields, rows = read_rows(path)
            if not all_fields and fields:
                all_fields = fields
            all_rows.extend(rows)

        if not all_fields:
            continue

        if target_name == "landing_cvr.csv":
            merged = merge_landing_cvr(all_fields, all_rows)
        elif target_name == "landing_events.csv":
            merged = merge_landing_events(all_fields, all_rows)
        else:
            merged = merge_full_dedup(all_fields, all_rows)

        write_rows(target, all_fields, merged)
        for path in matched:
            if path.parent == data_dir:
                move_to_archive(path, archive_dir)


def archive_dated_reports_and_logs(root: Path) -> None:
    reports = root / "reports"
    logs = root / "logs"
    report_archive = reports / "archive"
    log_archive = logs / "archive"

    for path in sorted(reports.glob("20*.md")):
        move_to_archive(path, report_archive)

    for path in sorted(logs.glob("20*.log")):
        move_to_archive(path, log_archive)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrate_csvs(root)
    archive_dated_reports_and_logs(root)
    print("Migration completed: cumulative files ready and dated files archived.")


if __name__ == "__main__":
    main()
