import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

from src.analytics import GA4Tracker


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class AnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["KTRIPPEDIA_DATA_DIR"] = str(self.root / "data")
        os.environ.pop("GA4_MEASUREMENT_ID", None)
        os.environ.pop("GA4_API_SECRET", None)

    def tearDown(self) -> None:
        os.environ.pop("KTRIPPEDIA_DATA_DIR", None)
        os.environ.pop("GA4_MEASUREMENT_ID", None)
        os.environ.pop("GA4_API_SECRET", None)
        self.temp_dir.cleanup()

    def test_track_skips_when_env_missing(self) -> None:
        tracker = GA4Tracker.from_env()
        self.assertFalse(tracker.enabled)
        tracker.track(
            date_token="20260216",
            event_name="page_view",
            client_id="cid-1",
            channel="referral",
            language="EN",
            params={"page_title": "landing"},
        )
        rows = read_rows(self.root / "data" / "analytics_events.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "skipped_env_missing")
        self.assertEqual(rows[0]["event_name"], "page_view")

    @patch("src.analytics.request.urlopen")
    def test_track_sends_when_env_present(self, mocked_urlopen) -> None:
        class _Resp:
            status = 204

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mocked_urlopen.return_value = _Resp()
        os.environ["GA4_MEASUREMENT_ID"] = "G-TEST1234"
        os.environ["GA4_API_SECRET"] = "secret-value"
        tracker = GA4Tracker.from_env()
        self.assertTrue(tracker.enabled)
        tracker.track(
            date_token="20260216",
            event_name="cta_click",
            client_id="cid-2",
            channel="community",
            language="EN",
            params={"cta_type": "pilot", "source_id": "reddit", "post_id": "r1"},
        )

        self.assertTrue(mocked_urlopen.called)
        rows = read_rows(self.root / "data" / "analytics_events.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "sent_204")
        self.assertEqual(rows[0]["event_name"], "cta_click")
        payload = json.loads(rows[0]["payload"])
        self.assertEqual(payload["events"][0]["params"]["source_id"], "reddit")
        self.assertEqual(payload["events"][0]["params"]["post_id"], "r1")

    @patch("src.analytics.request.urlopen")
    def test_track_logs_error_status_on_network_failure(self, mocked_urlopen) -> None:
        mocked_urlopen.side_effect = URLError("network down")
        os.environ["GA4_MEASUREMENT_ID"] = "G-TEST1234"
        os.environ["GA4_API_SECRET"] = "secret-value"
        tracker = GA4Tracker.from_env()

        tracker.track(
            date_token="20260216",
            event_name="cta_click",
            client_id="cid-err",
            channel="community",
            language="EN",
            params={"cta_type": "pilot"},
        )

        rows = read_rows(self.root / "data" / "analytics_events.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_name"], "cta_click")
        self.assertEqual(rows[0]["status"], "error_URLError")


if __name__ == "__main__":
    unittest.main()
