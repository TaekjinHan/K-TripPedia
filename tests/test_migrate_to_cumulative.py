import hashlib
import unittest

from scripts.migrate_to_cumulative import merge_landing_events


class MigrateToCumulativeTest(unittest.TestCase):
    def test_merge_landing_events_keeps_distinct_source_and_post(self) -> None:
        fields = [
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
        ]
        rows = [
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
                "timestamp": "2026-02-16T10:00:00",
                "date": "2026-02-16",
                "session_id": "s1",
                "language": "EN",
                "channel": "community",
                "source_id": "facebook",
                "post_id": "f1",
                "event_type": "visit",
                "cta_type": "",
                "lead_email": "",
                "consent": "0",
            },
        ]

        merged = merge_landing_events(fields, rows)

        self.assertEqual(len(merged), 2)
        self.assertEqual({row["source_id"] for row in merged}, {"reddit", "facebook"})
        self.assertEqual({row["post_id"] for row in merged}, {"r1", "f1"})

    def test_merge_landing_events_hashes_plaintext_email(self) -> None:
        fields = [
            "timestamp",
            "date",
            "session_id",
            "channel",
            "source_id",
            "post_id",
            "event_type",
            "cta_type",
            "lead_email",
        ]
        rows = [
            {
                "timestamp": "2026-02-16T10:00:00",
                "date": "2026-02-16",
                "session_id": "s2",
                "channel": "community",
                "source_id": "reddit",
                "post_id": "r2",
                "event_type": "lead_submit",
                "cta_type": "",
                "lead_email": "User@Example.com ",
            }
        ]

        merged = merge_landing_events(fields, rows)

        expected_digest = hashlib.sha256("user@example.com".encode("utf-8")).hexdigest()
        self.assertEqual(merged[0]["lead_email"], f"sha256:{expected_digest}")


if __name__ == "__main__":
    unittest.main()
