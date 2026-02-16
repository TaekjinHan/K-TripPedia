#!/usr/bin/env python3
"""Generate and track the pre-apply demand-validation package for K-TripPedia."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.storage import (
    append_pre_apply_history,
    date_token_to_iso,
    fetch_metrics_rows,
    normalize_date_token,
    upsert_table_rows,
)


TRIP_SAFETY_FIELDS = [
    "scenario_id",
    "date",
    "persona",
    "menu",
    "restriction",
    "risk_light",
    "confidence",
    "evidence_count",
    "show_mode_used",
    "quick_help_used",
    "resolved",
    "time_sec",
]

INTERVIEW_FIELDS = [
    "interview_id",
    "date",
    "segment",
    "language",
    "pain_tags",
    "quote",
]

LANDING_FIELDS = [
    "date",
    "channel",
    "visitors",
    "pilot_cta",
    "first_scan_cta",
    "total_cta",
]

B2B_FIELDS = [
    "meeting_id",
    "date",
    "partner_type",
    "partner_name",
    "status",
    "loi_signed",
    "intent_email",
    "notes",
]

PRICING_FIELDS = [
    "response_id",
    "date",
    "persona",
    "price_card",
    "selected",
    "willing_to_pay",
]

GUARDRAIL_FIELDS = [
    "check_id",
    "date",
    "scenario_id",
    "banned_expression_found",
    "evidence_missing",
    "confidence_missing",
    "reviewer",
    "notes",
]

MENU_50 = [
    "kimchi jjigae",
    "sundubu jjigae",
    "doenjang jjigae",
    "bibimbap",
    "tteokbokki",
    "gimbap",
    "dakgalbi",
    "samgyeopsal",
    "galbi tang",
    "naengmyeon",
    "jajangmyeon",
    "jjamppong",
    "haemul pajeon",
    "mandu",
    "kimchi bokkeumbap",
    "yukgaejang",
    "seolleongtang",
    "galbitang",
    "bossam",
    "jokbal",
    "budae jjigae",
    "odeng soup",
    "hotteok",
    "bungeoppang",
    "tteokgalbi",
    "korean fried chicken",
    "dakjuk",
    "kongguksu",
    "patbingsu",
    "tteokguk",
    "kongnamul gukbap",
    "soondae",
    "gopchang gui",
    "haejang guk",
    "jeonbok juk",
    "saengseon gui",
    "kalguksu",
    "sujebi",
    "mul naengmyeon",
    "bibim naengmyeon",
    "jjimdak",
    "gomtang",
    "tteok mandu guk",
    "samgyetang",
    "nakji bokkeum",
    "webfoot octopus stir fry",
    "chueotang",
    "soy sauce crab",
    "spicy marinated crab",
    "hwe deopbap",
]

SCENARIO_COUNT = 40
FIT_INTERVIEW_COUNT = 10
FIELD_INTERVIEW_COUNT = 5
PRICING_RESPONSE_COUNT = 50
GUARDRAIL_REVIEW_COUNT = 10

RESTRICTION_SEQUENCE = [
    ("fit_foreign", "peanut_allergy"),
    ("fit_foreign", "shellfish_allergy"),
    ("fit_foreign", "vegan"),
    ("fit_foreign", "halal"),
]


def validate_date_token(date_token: str) -> str:
    return normalize_date_token(date_token)


def to_iso_date(date_token: str) -> str:
    return date_token_to_iso(date_token)


def parse_bool(value: str) -> bool | None:
    value = (value or "").strip().lower()
    if value in {"1", "true", "yes", "y", "t"}:
        return True
    if value in {"0", "false", "no", "n", "f"}:
        return False
    return None


def parse_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_trip_scenario_rows(date_iso: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(SCENARIO_COUNT):
        persona, restriction = RESTRICTION_SEQUENCE[index % len(RESTRICTION_SEQUENCE)]
        rows.append(
            {
                "scenario_id": f"S{index + 1:03d}",
                "date": date_iso or "",
                "persona": persona,
                "menu": MENU_50[index],
                "restriction": restriction,
                "risk_light": "",
                "confidence": "",
                "evidence_count": "",
                "show_mode_used": "",
                "quick_help_used": "",
                "resolved": "",
                "time_sec": "",
            }
        )
    return rows


def build_interview_rows(date_iso: str) -> list[dict[str, str]]:
    rows = []
    for i in range(1, FIT_INTERVIEW_COUNT + 1):
        rows.append(
            {
                "interview_id": f"I{i:03d}",
                "date": date_iso,
                "segment": "fit_foreign",
                "language": "EN",
                "pain_tags": "",
                "quote": "",
            }
        )
    start = FIT_INTERVIEW_COUNT + 1
    end = FIT_INTERVIEW_COUNT + FIELD_INTERVIEW_COUNT + 1
    for i in range(start, end):
        rows.append(
            {
                "interview_id": f"I{i:03d}",
                "date": date_iso,
                "segment": "field_staff",
                "language": "EN",
                "pain_tags": "",
                "quote": "",
            }
        )
    return rows


def build_landing_rows(date_iso: str) -> list[dict[str, str]]:
    channels = ["pre_arrival_qr", "community", "sns_shortform", "referral"]
    return [
        {
            "date": date_iso,
            "channel": channel,
            "visitors": "0",
            "pilot_cta": "0",
            "first_scan_cta": "0",
            "total_cta": "0",
        }
        for channel in channels
    ]


def build_b2b_rows(date_iso: str) -> list[dict[str, str]]:
    return [
        {
            "meeting_id": "B2B001",
            "date": date_iso,
            "partner_type": "guesthouse",
            "partner_name": "",
            "status": "",
            "loi_signed": "",
            "intent_email": "",
            "notes": "",
        },
        {
            "meeting_id": "B2B002",
            "date": date_iso,
            "partner_type": "hotel",
            "partner_name": "",
            "status": "",
            "loi_signed": "",
            "intent_email": "",
            "notes": "",
        },
        {
            "meeting_id": "B2B003",
            "date": date_iso,
            "partner_type": "hotel",
            "partner_name": "",
            "status": "",
            "loi_signed": "",
            "intent_email": "",
            "notes": "",
        },
    ]


def build_pricing_rows(date_iso: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    cards = ["3d_pass", "7d_pass", "30d_pass"]
    personas = ["fit_foreign", "fit_foreign", "fit_foreign", "field_staff_proxy"]
    for i in range(1, PRICING_RESPONSE_COUNT + 1):
        rows.append(
            {
                "response_id": f"P{i:03d}",
                "date": date_iso,
                "persona": personas[i % len(personas)],
                "price_card": cards[i % len(cards)],
                "selected": "",
                "willing_to_pay": "",
            }
        )
    return rows


def build_guardrail_rows(date_iso: str) -> list[dict[str, str]]:
    rows = []
    for i in range(1, GUARDRAIL_REVIEW_COUNT + 1):
        rows.append(
            {
                "check_id": f"G{i:03d}",
                "date": date_iso,
                "scenario_id": f"S{i:03d}",
                "banned_expression_found": "",
                "evidence_missing": "",
                "confidence_missing": "",
                "reviewer": "",
                "notes": "",
            }
        )
    return rows


def pass_fail(value: bool) -> str:
    return "PASS" if value else "NEEDS_DATA"


def calculate_metrics(date_token: str, root: Path | None = None) -> dict[str, float | int]:
    date_iso = to_iso_date(date_token)

    interviews = fetch_metrics_rows("interview_log", date_iso)
    completed_interviews = [r for r in interviews if (r.get("quote", "").strip() or r.get("pain_tags", "").strip())]
    interview_total = len(completed_interviews)
    interview_fit = sum(1 for r in completed_interviews if r.get("segment", "").strip() == "fit_foreign")
    interview_field = sum(1 for r in completed_interviews if r.get("segment", "").strip() == "field_staff")

    pain_counter: Counter[str] = Counter()
    for row in completed_interviews:
        tags = [tag.strip().lower() for tag in row.get("pain_tags", "").split(";") if tag.strip()]
        pain_counter.update(tags)
    repeated_pain_points = sum(1 for _, count in pain_counter.items() if count >= 2)

    landing_rows = fetch_metrics_rows("landing_cvr_daily", date_iso)
    visitors = sum(parse_int(str(r.get("visitors", ""))) or 0 for r in landing_rows)
    total_cta = sum(parse_int(str(r.get("total_cta", ""))) or 0 for r in landing_rows)
    cta_rate = (total_cta / visitors * 100.0) if visitors else 0.0

    trip_rows = fetch_metrics_rows("trip_safety", date_iso)
    completed_trip_rows = [r for r in trip_rows if parse_bool(str(r.get("resolved", ""))) is not None]
    scenarios_completed = len(completed_trip_rows)
    show_mode_count = sum(1 for r in completed_trip_rows if parse_bool(str(r.get("show_mode_used", ""))) is True)
    resolved_count = sum(1 for r in completed_trip_rows if parse_bool(str(r.get("resolved", ""))) is True)
    show_mode_rate = (show_mode_count / scenarios_completed * 100.0) if scenarios_completed else 0.0
    resolved_rate = (resolved_count / scenarios_completed * 100.0) if scenarios_completed else 0.0

    b2b_rows = fetch_metrics_rows("b2b_pipeline", date_iso)
    completed_meetings = sum(1 for r in b2b_rows if str(r.get("status", "")).strip().lower() == "completed")
    loi_count = sum(1 for r in b2b_rows if parse_bool(str(r.get("loi_signed", ""))) is True)
    intent_count = sum(1 for r in b2b_rows if parse_bool(str(r.get("intent_email", ""))) is True)

    pricing_rows = fetch_metrics_rows("trip_pass_pricing", date_iso)
    completed_pricing = [r for r in pricing_rows if parse_bool(str(r.get("willing_to_pay", ""))) is not None]
    pricing_total = len(completed_pricing)
    willing_count = sum(1 for r in completed_pricing if parse_bool(str(r.get("willing_to_pay", ""))) is True)
    willing_rate = (willing_count / pricing_total * 100.0) if pricing_total else 0.0

    guardrail_rows = fetch_metrics_rows("guardrail_checklist", date_iso)
    reviewed_guardrails = [
        r
        for r in guardrail_rows
        if (
            parse_bool(str(r.get("banned_expression_found", ""))) is not None
            or parse_bool(str(r.get("evidence_missing", ""))) is not None
            or parse_bool(str(r.get("confidence_missing", ""))) is not None
        )
    ]
    banned_count = sum(1 for r in reviewed_guardrails if parse_bool(str(r.get("banned_expression_found", ""))) is True)
    evidence_missing_count = sum(1 for r in reviewed_guardrails if parse_bool(str(r.get("evidence_missing", ""))) is True)
    confidence_missing_count = sum(1 for r in reviewed_guardrails if parse_bool(str(r.get("confidence_missing", ""))) is True)

    return {
        "interview_total": interview_total,
        "interview_fit": interview_fit,
        "interview_field": interview_field,
        "repeated_pain_points": repeated_pain_points,
        "visitors": visitors,
        "total_cta": total_cta,
        "cta_rate": round(cta_rate, 2),
        "scenarios_completed": scenarios_completed,
        "show_mode_rate": round(show_mode_rate, 2),
        "resolved_rate": round(resolved_rate, 2),
        "completed_meetings": completed_meetings,
        "loi_count": loi_count,
        "intent_count": intent_count,
        "pricing_total": pricing_total,
        "willing_count": willing_count,
        "willing_rate": round(willing_rate, 2),
        "reviewed_guardrails": len(reviewed_guardrails),
        "banned_count": banned_count,
        "evidence_missing_count": evidence_missing_count,
        "confidence_missing_count": confidence_missing_count,
    }


def evaluate_targets(metrics: dict[str, float | int]) -> dict[str, bool]:
    return {
        "interview_target": (
            metrics["interview_total"] >= 15
            and metrics["interview_fit"] >= 10
            and metrics["interview_field"] >= 5
            and metrics["repeated_pain_points"] >= 3
        ),
        "landing_target": metrics["visitors"] >= 120 and metrics["cta_rate"] >= 15.0,
        "concierge_target": (
            metrics["scenarios_completed"] >= 40
            and metrics["show_mode_rate"] >= 50.0
            and metrics["resolved_rate"] >= 70.0
        ),
        "b2b_target": metrics["completed_meetings"] >= 3 and (metrics["loi_count"] >= 1 or metrics["intent_count"] >= 2),
        "pricing_target": metrics["pricing_total"] >= 50 and metrics["willing_rate"] >= 10.0,
        "guardrail_target": (
            metrics["banned_count"] == 0
            and metrics["evidence_missing_count"] == 0
            and metrics["confidence_missing_count"] == 0
            and metrics["reviewed_guardrails"] > 0
        ),
    }


def build_community_breakdown(date_token: str) -> list[dict[str, int | float | str]]:
    date_iso = to_iso_date(date_token)
    rows = fetch_metrics_rows("landing_events", date_iso)
    grouped: dict[tuple[str, str], dict[str, int]] = {}

    for row in rows:
        if str(row.get("channel", "")).strip() != "community":
            continue
        source_id = str(row.get("source_id", "")).strip() or "unknown"
        post_id = str(row.get("post_id", "")).strip() or "unknown"
        key = (source_id, post_id)
        if key not in grouped:
            grouped[key] = {"visitors": 0, "cta": 0, "leads": 0}
        event_type = str(row.get("event_type", "")).strip()
        if event_type == "visit":
            grouped[key]["visitors"] += 1
        elif event_type == "cta_click":
            grouped[key]["cta"] += 1
        elif event_type == "lead_submit":
            grouped[key]["leads"] += 1

    table: list[dict[str, int | float | str]] = []
    for (source_id, post_id), values in sorted(grouped.items()):
        visitors = values["visitors"]
        leads = values["leads"]
        source_cvr = round((leads / visitors * 100.0), 2) if visitors else 0.0
        table.append(
            {
                "source_id": source_id,
                "post_id": post_id,
                "visitors": visitors,
                "cta": values["cta"],
                "leads": leads,
                "source_cvr": source_cvr,
            }
        )
    return table


def _upsert_markdown_section(path: Path, section_header: str, section_body: list[str]) -> None:
    ensure_dir(path.parent)
    marker = f"## {section_header}"
    new_section = [marker, *section_body]
    if not path.exists():
        path.write_text("\n".join(new_section) + "\n", encoding="utf-8")
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    start = -1
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == marker:
            start = i
            break
    if start >= 0:
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("## "):
                end = j
                break
        updated = lines[:start] + new_section + lines[end:]
    else:
        updated = lines + [""] + new_section
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def build_decision_cards(date_token: str, root: Path) -> None:
    date_iso = to_iso_date(date_token)
    out_path = root / "reports" / "decision_cards.md"
    rows = fetch_metrics_rows("trip_safety", date_iso)[:10]

    body = [
        "",
        "Guardrail: no diagnosis, no prescription, no definitive medical judgment.",
        "",
    ]
    for idx, row in enumerate(rows, start=1):
        restriction = str(row.get("restriction", "")).strip() or "confirm_with_staff"
        menu = str(row.get("menu", "")).strip() or "menu_not_set"
        scenario_id = str(row.get("scenario_id", "")).strip() or f"S{idx:03d}"
        body.extend(
            [
                f"### Card {idx:02d} - {scenario_id}",
                f"- Menu: {menu}",
                f"- Restriction: {restriction}",
                "- Risk Light: CHECK_REQUIRED",
                "- Confidence: LOW_TO_MEDIUM",
                "- Show Mode Questions:",
                f"  - Does this dish include any {restriction.replace('_', ' ')} ingredients?",
                "  - Is fish sauce, broth powder, or cooking wine used?",
                "",
            ]
        )
    _upsert_markdown_section(out_path, f"Date {date_iso}", body)
    logging.info("Updated report: %s", out_path)


def build_summary_report(date_token: str, root: Path) -> None:
    date_iso = to_iso_date(date_token)
    report_path = root / "reports" / "pre_apply_validation.md"
    metrics = calculate_metrics(date_token=date_token, root=root)
    targets = evaluate_targets(metrics)
    community_rows = build_community_breakdown(date_token=date_token)

    lines = [
        f"# Pre-Apply Demand Validation (Latest: {date_iso})",
        "",
        "## KPI Status",
        "",
        "| Track | Current | Target | Status |",
        "|---|---:|---:|---|",
        (
            f"| Problem interviews | {metrics['interview_total']} "
            f"(fit {metrics['interview_fit']}, field {metrics['interview_field']}, repeated pain {metrics['repeated_pain_points']}) "
            "| 15 total / fit>=10 / field>=5 / repeated pain>=3 | "
            f"{pass_fail(targets['interview_target'])} |"
        ),
        (
            f"| Landing demand | visitors {metrics['visitors']}, CTA {metrics['total_cta']}, rate {metrics['cta_rate']}% "
            "| visitors>=120, CTA rate>=15% | "
            f"{pass_fail(targets['landing_target'])} |"
        ),
        (
            f"| Concierge PoC | scenarios {metrics['scenarios_completed']}, show mode {metrics['show_mode_rate']}%, resolved {metrics['resolved_rate']}% "
            "| scenarios>=40, show mode>=50%, resolved>=70% | "
            f"{pass_fail(targets['concierge_target'])} |"
        ),
        (
            f"| B2B lite demand | meetings {metrics['completed_meetings']}, LOI {metrics['loi_count']}, intent emails {metrics['intent_count']} "
            "| meetings>=3 and (LOI>=1 or intent>=2) | "
            f"{pass_fail(targets['b2b_target'])} |"
        ),
        (
            f"| Pricing willingness | responses {metrics['pricing_total']}, willing {metrics['willing_count']} ({metrics['willing_rate']}%) "
            "| responses>=50, willing rate>=10% | "
            f"{pass_fail(targets['pricing_target'])} |"
        ),
        (
            f"| Safety guardrails | reviewed {metrics['reviewed_guardrails']}, banned {metrics['banned_count']}, "
            f"evidence missing {metrics['evidence_missing_count']}, confidence missing {metrics['confidence_missing_count']} "
            "| banned=0, evidence missing=0, confidence missing=0 | "
            f"{pass_fail(targets['guardrail_target'])} |"
        ),
        "",
    ]
    lines.extend(
        [
            "## Community Breakdown",
            "",
        ]
    )
    if community_rows:
        lines.extend(
            [
                "| source_id | post_id | visitors | cta | leads | source_cvr |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in community_rows:
            lines.append(
                f"| {row['source_id']} | {row['post_id']} | {row['visitors']} | {row['cta']} | {row['leads']} | {row['source_cvr']}% |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "- No community source data yet for this date.",
                "",
            ]
        )
    lines.append("## History")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_pre_apply_history(
        report_path,
        date_iso,
        f"visitors={metrics['visitors']}, cta={metrics['total_cta']}, interviews={metrics['interview_total']}",
    )
    logging.info("Updated report: %s", report_path)


def build_interview_guide(root: Path) -> None:
    out_path = root / "reports" / "interview_guide.md"
    content = [
        "# Interview Guide",
        "",
        "## Objective",
        "",
        "- Validate demand and pain intensity before application submission.",
        "- Cover 10 fit_foreign interviews and 5 field_staff interviews.",
        "",
        "## Core Questions",
        "",
        "1. When did food safety uncertainty block your order decision?",
        "2. Which hidden ingredients are most difficult to verify on-site?",
        "3. What exact question would you want to show staff immediately?",
        "4. In emergency context, what delayed your next action most?",
        "5. Would you pay for a 3/7/30 day pass to reduce this uncertainty?",
    ]
    out_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    logging.info("Updated guide: %s", out_path)


def build_landing_copy(root: Path) -> None:
    out_path = root / "reports" / "landing_copy_en_jp.md"
    content = [
        "# Landing Copy (EN/JP)",
        "",
        "## English",
        "",
        "### Headline",
        "Ask first. Decide safer in 10 seconds.",
        "",
        "### Subcopy",
        "See evidence, check confidence, and show the right question before you order.",
        "",
        "### CTA",
        "- Join pilot",
        "- Try first scan",
        "",
        "## Japanese",
        "",
        "### Headline",
        "先に聞く。10秒でより安全な判断へ。",
        "",
        "### Subcopy",
        "根拠と確信度を確認し、注文前に店員へ見せる質問をすぐ提示します。",
        "",
        "### CTA",
        "- パイロット参加",
        "- はじめてのスキャンを試す",
    ]
    out_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    logging.info("Updated copy: %s", out_path)


def build_measurement_sheet(root: Path) -> None:
    out_path = root / "reports" / "measurement_sheet.md"
    content = [
        "# Measurement Sheet",
        "",
        "| Track | Source file | Metric | Target |",
        "|---|---|---|---|",
        "| Interview demand | data/interview_log.csv | total/segment/repeated pain | 15 / fit>=10 / field>=5 / repeated pain>=3 |",
        "| Landing demand | data/landing_cvr.csv | visitors, CTA rate | visitors>=120, CTA>=15% |",
        "| Concierge PoC | data/trip_safety.csv | completed scenarios, show mode rate, resolved rate | 40, >=50%, >=70% |",
        "| B2B demand | data/b2b_pipeline.csv | meetings, LOI, intent | >=3, LOI>=1 or intent>=2 |",
        "| Pricing willingness | data/trip_pass_pricing.csv | completed responses, willing rate | >=50, >=10% |",
        "| Safety guardrails | data/guardrail_checklist.csv | banned/evidence/confidence issues | all 0 |",
        "| Community execution | data/community_outreach_log.csv | post_id visitors/cta/leads/source_cvr | weekly visitors>=120, lead>=10 |",
    ]
    out_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    logging.info("Updated measurement sheet: %s", out_path)


def setup_logging(log_path: Path) -> None:
    ensure_dir(log_path.parent)
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def bootstrap_for_date(date_iso: str, overwrite: bool) -> None:
    overwrite_date = date_iso if overwrite else None
    upsert_table_rows("trip_safety", build_trip_scenario_rows(date_iso), overwrite_date=overwrite_date)
    upsert_table_rows("interview_log", build_interview_rows(date_iso), overwrite_date=overwrite_date)
    upsert_table_rows("landing_cvr_daily", build_landing_rows(date_iso), overwrite_date=overwrite_date)
    upsert_table_rows("b2b_pipeline", build_b2b_rows(date_iso), overwrite_date=overwrite_date)
    upsert_table_rows("trip_pass_pricing", build_pricing_rows(date_iso), overwrite_date=overwrite_date)
    upsert_table_rows("guardrail_checklist", build_guardrail_rows(date_iso), overwrite_date=overwrite_date)


def run(date_token: str, root: Path, overwrite: bool, bootstrap: bool = False) -> None:
    date_iso = to_iso_date(date_token)
    if bootstrap:
        bootstrap_for_date(date_iso=date_iso, overwrite=overwrite)

    build_decision_cards(date_token=date_token, root=root)
    build_summary_report(date_token=date_token, root=root)
    build_interview_guide(root=root)
    build_landing_copy(root=root)
    build_measurement_sheet(root=root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build K-TripPedia pre-apply validation package.")
    parser.add_argument("--date", default=dt.datetime.now().strftime("%Y%m%d"), help="Date token in YYYYMMDD format")
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite current date rows (bootstrap only)")
    parser.add_argument("--bootstrap", action="store_true", help="Create template rows for the target date")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    os.environ["KTRIPPEDIA_DATA_DIR"] = str(root / "data")
    validated_date_token = validate_date_token(args.date)
    log_path = root / "logs" / "validation.log"
    setup_logging(log_path=log_path)
    logging.info("Start validation package build. root=%s date=%s", root, validated_date_token)
    run(date_token=validated_date_token, root=root, overwrite=args.overwrite, bootstrap=args.bootstrap)
    logging.info("Completed validation package build.")


if __name__ == "__main__":
    main()
