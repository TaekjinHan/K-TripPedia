import csv
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from src.landing_tracker import normalize_channel, save_lead, track_cta, track_visit


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class LandingTrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data"
        os.environ["KTRIPPEDIA_DATA_DIR"] = str(self.data_dir)

    def tearDown(self) -> None:
        os.environ.pop("KTRIPPEDIA_DATA_DIR", None)
        self.temp_dir.cleanup()

    def test_normalize_channel(self) -> None:
        self.assertEqual(normalize_channel("pre_arrival_qr"), "pre_arrival_qr")
        self.assertEqual(normalize_channel("COMMUNITY"), "community")
        self.assertEqual(normalize_channel("invalid"), "referral")
        self.assertEqual(normalize_channel(""), "referral")

    def test_track_visit_deduplicates_by_session(self) -> None:
        date_token = "20260222"
        session_id = "session-1"
        track_visit(
            date_token=date_token,
            session_id=session_id,
            channel="pre_arrival_qr",
            source_id="reddit",
            post_id="r1",
        )
        track_visit(
            date_token=date_token,
            session_id=session_id,
            channel="pre_arrival_qr",
            source_id="reddit",
            post_id="r1",
        )

        cvr_rows = read_rows(self.data_dir / "landing_cvr.csv")
        self.assertEqual(len(cvr_rows), 1)
        self.assertEqual(cvr_rows[0]["date"], "2026-02-22")
        self.assertEqual(cvr_rows[0]["channel"], "pre_arrival_qr")
        self.assertEqual(cvr_rows[0]["visitors"], "1")

        event_rows = read_rows(self.data_dir / "landing_events.csv")
        visit_events = [row for row in event_rows if row["event_type"] == "visit"]
        self.assertEqual(len(visit_events), 1)
        self.assertEqual(visit_events[0]["source_id"], "reddit")
        self.assertEqual(visit_events[0]["post_id"], "r1")

    def test_track_visit_keeps_source_post_attribution(self) -> None:
        date_token = "20260222"
        session_id = "session-attr"
        track_visit(
            date_token=date_token,
            session_id=session_id,
            channel="community",
            source_id="reddit",
            post_id="r1",
        )
        track_visit(
            date_token=date_token,
            session_id=session_id,
            channel="community",
            source_id="facebook",
            post_id="f1",
        )

        event_rows = read_rows(self.data_dir / "landing_events.csv")
        visit_events = [row for row in event_rows if row["event_type"] == "visit"]
        self.assertEqual(len(visit_events), 2)
        self.assertEqual({row["source_id"] for row in visit_events}, {"reddit", "facebook"})
        self.assertEqual({row["post_id"] for row in visit_events}, {"r1", "f1"})

    def test_track_cta_updates_pilot_firstscan_and_total(self) -> None:
        date_token = "20260222"
        session_id = "session-2"
        track_cta(
            date_token=date_token,
            session_id=session_id,
            channel="community",
            cta_type="pilot",
            language="EN",
            source_id="reddit",
            post_id="r2",
        )
        track_cta(
            date_token=date_token,
            session_id=session_id,
            channel="community",
            cta_type="first_scan",
            language="JP",
            source_id="facebook",
            post_id="f1",
        )

        cvr_rows = read_rows(self.data_dir / "landing_cvr.csv")
        self.assertEqual(len(cvr_rows), 1)
        self.assertEqual(cvr_rows[0]["pilot_cta"], "1")
        self.assertEqual(cvr_rows[0]["first_scan_cta"], "1")
        self.assertEqual(cvr_rows[0]["total_cta"], "2")

        events = read_rows(self.data_dir / "landing_events.csv")
        cta_events = [row for row in events if row["event_type"] == "cta_click"]
        self.assertEqual(len(cta_events), 2)
        self.assertEqual({row["cta_type"] for row in cta_events}, {"pilot", "first_scan"})
        self.assertEqual({row["source_id"] for row in cta_events}, {"reddit", "facebook"})
        self.assertEqual({row["post_id"] for row in cta_events}, {"r2", "f1"})

    def test_save_lead_requires_consent(self) -> None:
        date_token = "20260222"
        session_id = "session-3"
        save_lead(
            date_token=date_token,
            session_id=session_id,
            channel="sns_shortform",
            language="EN",
            lead_email="no-consent@example.com",
            consent=False,
        )
        save_lead(
            date_token=date_token,
            session_id=session_id,
            channel="sns_shortform",
            language="EN",
            lead_email="ok@example.com",
            consent=True,
            source_id="reddit",
            post_id="r3",
        )

        events = read_rows(self.data_dir / "landing_events.csv")
        lead_events = [row for row in events if row["event_type"] == "lead_submit"]
        self.assertEqual(len(lead_events), 1)
        expected_hash = hashlib.sha256("ok@example.com".encode("utf-8")).hexdigest()
        self.assertEqual(lead_events[0]["lead_email"], f"sha256:{expected_hash}")
        self.assertEqual(lead_events[0]["consent"], "1")
        self.assertEqual(lead_events[0]["source_id"], "reddit")
        self.assertEqual(lead_events[0]["post_id"], "r3")

    def test_track_visit_rejects_invalid_date_token(self) -> None:
        with self.assertRaises(ValueError):
            track_visit(date_token="2026-02-22", session_id="session-err", channel="community")

    def test_track_cta_rejects_blank_session(self) -> None:
        with self.assertRaises(ValueError):
            track_cta(
                date_token="20260222",
                session_id="",
                channel="community",
                cta_type="pilot",
                language="EN",
            )

    def test_save_lead_rejects_invalid_email_when_consented(self) -> None:
        with self.assertRaises(ValueError):
            save_lead(
                date_token="20260222",
                session_id="session-5",
                channel="sns_shortform",
                language="EN",
                lead_email="invalid-email",
                consent=True,
            )

    def test_save_lead_rejects_email_with_whitespace(self) -> None:
        with self.assertRaises(ValueError):
            save_lead(
                date_token="20260222",
                session_id="session-6",
                channel="sns_shortform",
                language="EN",
                lead_email="bad email@example.com",
                consent=True,
            )

    def test_save_lead_rejects_email_without_domain_dot(self) -> None:
        with self.assertRaises(ValueError):
            save_lead(
                date_token="20260222",
                session_id="session-7",
                channel="sns_shortform",
                language="EN",
                lead_email="name@example",
                consent=True,
            )


if __name__ == "__main__":
    unittest.main()
