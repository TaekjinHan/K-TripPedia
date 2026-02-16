from __future__ import annotations

import csv
from pathlib import Path

from src.storage import date_token_to_iso, normalize_date_token


def to_iso(date_token: str) -> str:
    return date_token_to_iso(normalize_date_token(date_token))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_int(value: str) -> int:
    raw = (value or "").strip()
    if not raw:
        return 0
    try:
        return int(float(raw))
    except ValueError:
        return 0


def in_range(date_iso: str, start_iso: str, end_iso: str) -> bool:
    return start_iso <= date_iso <= end_iso


def build_summary(root: Path, start_iso: str, end_iso: str) -> tuple[dict[str, float | int], list[dict[str, float | int | str]]]:
    cvr_rows = read_csv(root / "data" / "landing_cvr.csv")
    event_rows = read_csv(root / "data" / "landing_events.csv")

    visitors = 0
    cta = 0
    leads = 0

    for row in cvr_rows:
        date_iso = (row.get("date", "") or "").strip()
        if (row.get("channel", "") or "").strip() != "community":
            continue
        if not in_range(date_iso, start_iso, end_iso):
            continue
        visitors += parse_int(row.get("visitors", ""))
        cta += parse_int(row.get("total_cta", ""))

    source_map: dict[tuple[str, str], dict[str, int]] = {}
    for row in event_rows:
        date_iso = (row.get("date", "") or "").strip()
        if (row.get("channel", "") or "").strip() != "community":
            continue
        if not in_range(date_iso, start_iso, end_iso):
            continue

        source_id = (row.get("source_id", "") or "").strip() or "unknown"
        post_id = (row.get("post_id", "") or "").strip() or "unknown"
        event_type = (row.get("event_type", "") or "").strip()
        key = (source_id, post_id)
        if key not in source_map:
            source_map[key] = {"visitors": 0, "cta": 0, "leads": 0}

        if event_type == "visit":
            source_map[key]["visitors"] += 1
        elif event_type == "cta_click":
            source_map[key]["cta"] += 1
        elif event_type == "lead_submit":
            source_map[key]["leads"] += 1
            leads += 1

    cta_rate = round((cta / visitors * 100.0), 2) if visitors else 0.0
    lead_rate = round((leads / visitors * 100.0), 2) if visitors else 0.0

    source_rows: list[dict[str, float | int | str]] = []
    for (source_id, post_id), values in source_map.items():
        s_visitors = values["visitors"]
        s_leads = values["leads"]
        source_rows.append(
            {
                "source_id": source_id,
                "post_id": post_id,
                "visitors": s_visitors,
                "cta": values["cta"],
                "leads": s_leads,
                "source_cvr": round((s_leads / s_visitors * 100.0), 2) if s_visitors else 0.0,
            }
        )

    source_rows.sort(key=lambda r: (int(r["leads"]), float(r["source_cvr"]), int(r["visitors"])), reverse=True)

    summary = {
        "visitors": visitors,
        "cta": cta,
        "leads": leads,
        "cta_rate": cta_rate,
        "lead_rate": lead_rate,
        "kpi_pass": visitors >= 120 and cta >= 18 and leads >= 10,
    }
    return summary, source_rows


def write_markdown(
    out_path: Path,
    start_iso: str,
    end_iso: str,
    summary: dict[str, float | int],
    source_rows: list[dict[str, float | int | str]],
) -> None:
    lines = [
        "# Weekly Community Validation Summary",
        "",
        f"- Period: {start_iso} ~ {end_iso}",
        "- Scope: demand-validation landing only (not product launch)",
        "",
        "## KPI Result",
        "",
        f"- Visitors: {summary['visitors']} (target >= 120)",
        f"- CTA: {summary['cta']} (target >= 18)",
        f"- Leads: {summary['leads']} (target >= 10)",
        f"- CTA rate: {summary['cta_rate']}%",
        f"- Lead rate: {summary['lead_rate']}%",
        f"- Status: {'PASS' if summary['kpi_pass'] else 'NEEDS_DATA'}",
        "",
        "## Top Sources (Top 2)",
        "",
    ]

    top_rows = source_rows[:2]
    if top_rows:
        lines.extend(
            [
                "| source_id | post_id | visitors | cta | leads | source_cvr |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in top_rows:
            lines.append(
                f"| {row['source_id']} | {row['post_id']} | {row['visitors']} | {row['cta']} | {row['leads']} | {row['source_cvr']}% |"
            )
    else:
        lines.append("- No community source data in selected period.")

    lines.extend(
        [
            "",
            "## Full Source Breakdown",
            "",
        ]
    )
    if source_rows:
        lines.extend(
            [
                "| source_id | post_id | visitors | cta | leads | source_cvr |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in source_rows:
            lines.append(
                f"| {row['source_id']} | {row['post_id']} | {row['visitors']} | {row['cta']} | {row['leads']} | {row['source_cvr']}% |"
            )
    else:
        lines.append("- No data.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_weekly_summary(root: Path, start_token: str, end_token: str, out_relative_path: str) -> Path:
    start_iso = to_iso(start_token)
    end_iso = to_iso(end_token)
    if start_iso > end_iso:
        raise ValueError("start must be <= end")

    summary, source_rows = build_summary(root=root, start_iso=start_iso, end_iso=end_iso)
    out_path = root / out_relative_path
    write_markdown(out_path=out_path, start_iso=start_iso, end_iso=end_iso, summary=summary, source_rows=source_rows)
    return out_path
