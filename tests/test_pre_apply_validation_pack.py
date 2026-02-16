import os
import tempfile
import unittest
from pathlib import Path

from src.pre_apply_validation_pack import (
    B2B_FIELDS,
    FIELD_INTERVIEW_COUNT,
    FIT_INTERVIEW_COUNT,
    GUARDRAIL_FIELDS,
    GUARDRAIL_REVIEW_COUNT,
    INTERVIEW_FIELDS,
    LANDING_FIELDS,
    PRICING_FIELDS,
    PRICING_RESPONSE_COUNT,
    SCENARIO_COUNT,
    TRIP_SAFETY_FIELDS,
    build_trip_scenario_rows,
    calculate_metrics,
    evaluate_targets,
    parse_bool,
    run,
    validate_date_token,
)
from src.landing_tracker import save_lead, track_cta, track_visit
from src.storage import upsert_table_rows


class ValidationPackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["KTRIPPEDIA_DATA_DIR"] = str(self.root / "data")

    def tearDown(self) -> None:
        os.environ.pop("KTRIPPEDIA_DATA_DIR", None)
        self.temp_dir.cleanup()

    def test_parse_bool(self) -> None:
        self.assertTrue(parse_bool("1"))
        self.assertTrue(parse_bool("yes"))
        self.assertFalse(parse_bool("0"))
        self.assertFalse(parse_bool("No"))
        self.assertIsNone(parse_bool(""))
        self.assertIsNone(parse_bool("maybe"))

    def test_validate_date_token(self) -> None:
        self.assertEqual(validate_date_token("20260222"), "20260222")
        with self.assertRaises(ValueError):
            validate_date_token("2026-02-22")
        with self.assertRaises(ValueError):
            validate_date_token("20260230")

    def test_build_trip_scenarios(self) -> None:
        rows = build_trip_scenario_rows("2026-02-22")
        self.assertEqual(len(rows), SCENARIO_COUNT)
        self.assertEqual(rows[0]["scenario_id"], "S001")
        self.assertEqual(rows[-1]["scenario_id"], f"S{SCENARIO_COUNT:03d}")
        self.assertEqual(rows[0]["date"], "2026-02-22")
        self.assertEqual(list(rows[0].keys()), TRIP_SAFETY_FIELDS)

    def test_metrics_and_targets(self) -> None:
        date_token = "20260222"

        interview_rows = []
        for i in range(FIT_INTERVIEW_COUNT):
            interview_rows.append(
                {
                    "interview_id": f"I{i+1:03d}",
                    "date": "2026-02-22",
                    "segment": "fit_foreign",
                    "language": "EN",
                    "pain_tags": "hidden_ingredients;translation_gap;staff_communication",
                    "quote": "Need fast confirmation with evidence.",
                }
            )
        for i in range(FIELD_INTERVIEW_COUNT):
            interview_rows.append(
                {
                    "interview_id": f"I{i+11:03d}",
                    "date": "2026-02-22",
                    "segment": "field_staff",
                    "language": "EN",
                    "pain_tags": "staff_communication;emergency_delay;trust_gap",
                    "quote": "Guests ask repetitive ingredient questions.",
                }
            )
        upsert_table_rows("interview_log", interview_rows)

        landing_rows = [
            {
                "date": "2026-02-22",
                "channel": "pre_arrival_qr",
                "visitors": "80",
                "pilot_cta": "15",
                "first_scan_cta": "20",
                "total_cta": "35",
            },
            {
                "date": "2026-02-22",
                "channel": "community",
                "visitors": "60",
                "pilot_cta": "10",
                "first_scan_cta": "12",
                "total_cta": "22",
            },
        ]
        upsert_table_rows("landing_cvr_daily", landing_rows)

        trip_rows = []
        for i in range(SCENARIO_COUNT):
            trip_rows.append(
                {
                    "scenario_id": f"S{i+1:03d}",
                    "date": "2026-02-22",
                    "persona": "fit_foreign",
                    "menu": "kimchi jjigae",
                    "restriction": "shellfish_allergy",
                    "risk_light": "CHECK_REQUIRED",
                    "confidence": "MEDIUM",
                    "evidence_count": "2",
                    "show_mode_used": "1" if i < 30 else "0",
                    "quick_help_used": "1" if i < 12 else "0",
                    "resolved": "1" if i < 32 else "0",
                    "time_sec": "45",
                }
            )
        upsert_table_rows("trip_safety", trip_rows)

        b2b_rows = [
            {
                "meeting_id": "B2B001",
                "date": "2026-02-22",
                "partner_type": "guesthouse",
                "partner_name": "A",
                "status": "completed",
                "loi_signed": "1",
                "intent_email": "1",
                "notes": "pilot possible",
            },
            {
                "meeting_id": "B2B002",
                "date": "2026-02-22",
                "partner_type": "hotel",
                "partner_name": "B",
                "status": "completed",
                "loi_signed": "0",
                "intent_email": "1",
                "notes": "follow-up",
            },
            {
                "meeting_id": "B2B003",
                "date": "2026-02-22",
                "partner_type": "hotel",
                "partner_name": "C",
                "status": "completed",
                "loi_signed": "0",
                "intent_email": "0",
                "notes": "pending",
            },
        ]
        upsert_table_rows("b2b_pipeline", b2b_rows)

        pricing_rows = []
        for i in range(PRICING_RESPONSE_COUNT):
            pricing_rows.append(
                {
                    "response_id": f"P{i+1:03d}",
                    "date": "2026-02-22",
                    "persona": "fit_foreign",
                    "price_card": "7d_pass",
                    "selected": "7d_pass",
                    "willing_to_pay": "1" if i < 12 else "0",
                }
            )
        upsert_table_rows("trip_pass_pricing", pricing_rows)

        guardrail_rows = []
        for i in range(GUARDRAIL_REVIEW_COUNT):
            guardrail_rows.append(
                {
                    "check_id": f"G{i+1:03d}",
                    "date": "2026-02-22",
                    "scenario_id": f"S{i+1:03d}",
                    "banned_expression_found": "0",
                    "evidence_missing": "0",
                    "confidence_missing": "0",
                    "reviewer": "reviewer_1",
                    "notes": "",
                }
            )
        upsert_table_rows("guardrail_checklist", guardrail_rows)

        metrics = calculate_metrics(date_token=date_token, root=self.root)
        targets = evaluate_targets(metrics)

        self.assertEqual(metrics["interview_total"], 15)
        self.assertGreaterEqual(metrics["cta_rate"], 15.0)
        self.assertEqual(metrics["scenarios_completed"], 40)
        self.assertGreaterEqual(metrics["show_mode_rate"], 50.0)
        self.assertGreaterEqual(metrics["resolved_rate"], 70.0)
        self.assertEqual(metrics["banned_count"], 0)
        self.assertTrue(all(targets.values()))

    def test_run_creates_reports_without_bootstrap(self) -> None:
        run(date_token="20260216", root=self.root, overwrite=False, bootstrap=False)

        self.assertTrue((self.root / "reports" / "pre_apply_validation.md").exists())
        self.assertTrue((self.root / "reports" / "measurement_sheet.md").exists())
        self.assertFalse((self.root / "data" / "trip_safety.csv").exists())
        report_text = (self.root / "reports" / "pre_apply_validation.md").read_text(encoding="utf-8")
        self.assertIn("## Community Breakdown", report_text)

    def test_run_bootstrap_creates_data_exports(self) -> None:
        run(date_token="20260216", root=self.root, overwrite=False, bootstrap=True)

        self.assertTrue((self.root / "data" / "trip_safety.csv").exists())
        self.assertTrue((self.root / "data" / "landing_cvr.csv").exists())

    def test_summary_includes_community_breakdown_rows(self) -> None:
        track_visit(
            date_token="20260216",
            session_id="community-1",
            channel="community",
            source_id="reddit",
            post_id="r1",
        )
        track_cta(
            date_token="20260216",
            session_id="community-1",
            channel="community",
            cta_type="pilot",
            language="EN",
            source_id="reddit",
            post_id="r1",
        )
        save_lead(
            date_token="20260216",
            session_id="community-1",
            channel="community",
            language="EN",
            lead_email="community-1@example.com",
            consent=True,
            source_id="reddit",
            post_id="r1",
        )

        run(date_token="20260216", root=self.root, overwrite=False, bootstrap=False)
        report_text = (self.root / "reports" / "pre_apply_validation.md").read_text(encoding="utf-8")
        self.assertIn("| reddit | r1 | 1 | 1 | 1 | 100.0% |", report_text)


if __name__ == "__main__":
    unittest.main()
