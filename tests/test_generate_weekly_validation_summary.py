import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class WeeklyValidationSummaryScriptTest(unittest.TestCase):
    def test_generates_top2_and_kpi_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"

            write_csv(
                data_dir / "landing_cvr.csv",
                ["date", "channel", "visitors", "pilot_cta", "first_scan_cta", "total_cta"],
                [
                    {
                        "date": "2026-02-16",
                        "channel": "community",
                        "visitors": "70",
                        "pilot_cta": "10",
                        "first_scan_cta": "2",
                        "total_cta": "12",
                    },
                    {
                        "date": "2026-02-17",
                        "channel": "community",
                        "visitors": "60",
                        "pilot_cta": "7",
                        "first_scan_cta": "2",
                        "total_cta": "9",
                    },
                    {
                        "date": "2026-02-16",
                        "channel": "referral",
                        "visitors": "100",
                        "pilot_cta": "0",
                        "first_scan_cta": "0",
                        "total_cta": "0",
                    },
                ],
            )

            write_csv(
                data_dir / "landing_events.csv",
                [
                    "timestamp",
                    "date",
                    "session_id",
                    "language",
                    "channel",
                    "source_id",
                    "post_id",
                    "event_type",
                    "cta_type",
                    "lead_email",
                    "consent",
                ],
                [
                    {
                        "timestamp": "2026-02-16T10:00:00",
                        "date": "2026-02-16",
                        "session_id": "s1",
                        "language": "EN",
                        "channel": "community",
                        "source_id": "reddit",
                        "post_id": "r1",
                        "event_type": "visit",
                        "cta_type": "",
                        "lead_email": "",
                        "consent": "0",
                    },
                    {
                        "timestamp": "2026-02-16T10:00:10",
                        "date": "2026-02-16",
                        "session_id": "s1",
                        "language": "EN",
                        "channel": "community",
                        "source_id": "reddit",
                        "post_id": "r1",
                        "event_type": "cta_click",
                        "cta_type": "pilot",
                        "lead_email": "",
                        "consent": "0",
                    },
                    {
                        "timestamp": "2026-02-16T10:00:20",
                        "date": "2026-02-16",
                        "session_id": "s1",
                        "language": "EN",
                        "channel": "community",
                        "source_id": "reddit",
                        "post_id": "r1",
                        "event_type": "lead_submit",
                        "cta_type": "",
                        "lead_email": "a@example.com",
                        "consent": "1",
                    },
                    {
                        "timestamp": "2026-02-17T11:00:00",
                        "date": "2026-02-17",
                        "session_id": "s2",
                        "language": "EN",
                        "channel": "community",
                        "source_id": "facebook",
                        "post_id": "f1",
                        "event_type": "visit",
                        "cta_type": "",
                        "lead_email": "",
                        "consent": "0",
                    },
                    {
                        "timestamp": "2026-02-17T11:00:10",
                        "date": "2026-02-17",
                        "session_id": "s2",
                        "language": "EN",
                        "channel": "community",
                        "source_id": "facebook",
                        "post_id": "f1",
                        "event_type": "lead_submit",
                        "cta_type": "",
                        "lead_email": "b@example.com",
                        "consent": "1",
                    },
                ],
            )

            out_rel = Path("reports") / "weekly_validation_summary.md"
            cmd = [
                sys.executable,
                "scripts/generate_weekly_validation_summary.py",
                "--root",
                str(root),
                "--start",
                "20260216",
                "--end",
                "20260222",
                "--out",
                str(out_rel),
            ]
            subprocess.check_call(cmd)

            out_path = root / out_rel
            self.assertTrue(out_path.exists())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("Visitors: 130 (target >= 120)", text)
            self.assertIn("CTA: 21 (target >= 18)", text)
            self.assertIn("Leads: 2 (target >= 10)", text)
            self.assertIn("Status: NEEDS_DATA", text)
            self.assertIn("| reddit | r1 |", text)
            self.assertIn("| facebook | f1 |", text)


if __name__ == "__main__":
    unittest.main()
