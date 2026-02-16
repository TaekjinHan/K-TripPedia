import csv
import os
import tempfile
import threading
import unittest
from pathlib import Path

from src.storage import (
    append_landing_event_if_new,
    date_token_to_iso,
    export_table_to_csv,
    increment_landing_cvr,
    upsert_app_reviews,
    upsert_table_rows,
)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class StorageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["KTRIPPEDIA_DATA_DIR"] = str(self.root / "data")

    def tearDown(self) -> None:
        os.environ.pop("KTRIPPEDIA_DATA_DIR", None)
        self.temp_dir.cleanup()

    def test_landing_event_idempotent_insert(self) -> None:
        date_iso = date_token_to_iso("20260216")
        inserted1 = append_landing_event_if_new(
            timestamp="2026-02-16T10:00:00",
            date_iso=date_iso,
            session_id="s1",
            language="EN",
            channel="referral",
            source_id="reddit",
            post_id="r1",
            event_type="visit",
            cta_type="",
            lead_email="",
            consent=False,
        )
        inserted2 = append_landing_event_if_new(
            timestamp="2026-02-16T10:00:00",
            date_iso=date_iso,
            session_id="s1",
            language="EN",
            channel="referral",
            source_id="reddit",
            post_id="r1",
            event_type="visit",
            cta_type="",
            lead_email="",
            consent=False,
        )

        self.assertTrue(inserted1)
        self.assertFalse(inserted2)
        rows = read_rows(self.root / "data" / "landing_events.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "reddit")
        self.assertEqual(rows[0]["post_id"], "r1")

    def test_landing_event_dedup_includes_source_and_post(self) -> None:
        date_iso = date_token_to_iso("20260216")
        inserted1 = append_landing_event_if_new(
            timestamp="2026-02-16T10:00:00",
            date_iso=date_iso,
            session_id="s1",
            language="EN",
            channel="community",
            source_id="reddit",
            post_id="r1",
            event_type="visit",
            cta_type="",
            lead_email="",
            consent=False,
        )
        inserted2 = append_landing_event_if_new(
            timestamp="2026-02-16T10:00:00",
            date_iso=date_iso,
            session_id="s1",
            language="EN",
            channel="community",
            source_id="facebook",
            post_id="f1",
            event_type="visit",
            cta_type="",
            lead_email="",
            consent=False,
        )

        self.assertTrue(inserted1)
        self.assertTrue(inserted2)
        rows = read_rows(self.root / "data" / "landing_events.csv")
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["source_id"] for row in rows}, {"reddit", "facebook"})
        self.assertEqual({row["post_id"] for row in rows}, {"r1", "f1"})

    def test_concurrent_increment(self) -> None:
        date_iso = date_token_to_iso("20260216")

        def worker() -> None:
            for _ in range(20):
                increment_landing_cvr(date_iso=date_iso, channel="referral", field="visitors", amount=1)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        rows = read_rows(self.root / "data" / "landing_cvr.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["visitors"], "100")

    def test_upsert_table_rows_updates_same_key(self) -> None:
        upsert_table_rows(
            "trip_safety",
            [
                {
                    "scenario_id": "S001",
                    "date": "2026-02-16",
                    "persona": "fit_foreign",
                    "menu": "kimchi jjigae",
                    "restriction": "peanut_allergy",
                    "risk_light": "",
                    "confidence": "",
                    "evidence_count": "",
                    "show_mode_used": "",
                    "quick_help_used": "",
                    "resolved": "",
                    "time_sec": "",
                }
            ],
        )
        upsert_table_rows(
            "trip_safety",
            [
                {
                    "scenario_id": "S001",
                    "date": "2026-02-16",
                    "persona": "fit_foreign",
                    "menu": "kimchi jjigae",
                    "restriction": "shellfish_allergy",
                    "risk_light": "CHECK_REQUIRED",
                    "confidence": "MEDIUM",
                    "evidence_count": "2",
                    "show_mode_used": "1",
                    "quick_help_used": "0",
                    "resolved": "1",
                    "time_sec": "30",
                }
            ],
        )
        export_table_to_csv("trip_safety")
        rows = read_rows(self.root / "data" / "trip_safety.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["restriction"], "shellfish_allergy")

    def test_community_outreach_table_export(self) -> None:
        upsert_table_rows(
            "community_outreach_log",
            [
                {
                    "date": "2026-02-16",
                    "platform": "reddit",
                    "community_name": "r/koreatravel",
                    "post_id": "r1",
                    "url": "http://localhost:8501/?ch=community&src=reddit&post_id=r1",
                    "language": "EN",
                    "impressions": "100",
                    "clicks": "15",
                    "visitors": "10",
                    "cta": "3",
                    "leads": "1",
                    "status": "active",
                    "notes": "",
                }
            ],
        )
        rows = read_rows(self.root / "data" / "community_outreach_log.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["post_id"], "r1")
        self.assertEqual(rows[0]["visitors"], "10")

    def test_upsert_app_reviews_dedup_updates_same_review(self) -> None:
        base_row = {
            "timestamp": "2026-02-16T10:00:00",
            "date": "2026-02-16",
            "service_name": "Ask Before You Eat",
            "store": "google_play",
            "app_id": "com.example.app",
            "country": "US",
            "language": "en",
            "review_id": "r1",
            "review_created_at": "2026-02-15T09:00:00",
            "review_updated_at": "2026-02-15T09:00:00",
            "rating": "4",
            "title": "Good",
            "content": "first",
            "reviewer_name": "alice",
            "source_url": "https://play.google.com/store/apps/details?id=com.example.app",
        }
        first = upsert_app_reviews([base_row])
        self.assertEqual(first["inserted"], 1)
        self.assertEqual(first["updated"], 0)

        updated_row = dict(base_row)
        updated_row["timestamp"] = "2026-02-16T11:00:00"
        updated_row["review_updated_at"] = "2026-02-16T11:00:00"
        updated_row["rating"] = "5"
        updated_row["content"] = "updated"
        second = upsert_app_reviews([updated_row])
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["updated"], 1)

        export_table_to_csv("app_reviews")
        rows = read_rows(self.root / "data" / "app_reviews.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rating"], "5")
        self.assertEqual(rows[0]["content"], "updated")


if __name__ == "__main__":
    unittest.main()
