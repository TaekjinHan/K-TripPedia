import datetime as dt
import sys
import types
import unittest
from unittest.mock import patch

from src.review_collectors.apple_store import collect_apple_reviews
from src.review_collectors.common import parse_apple_app_id_from_link, parse_google_app_id_from_link
from src.review_collectors.google_play import collect_google_reviews


class FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class ReviewCollectorsTest(unittest.TestCase):
    def test_link_parsers_extract_ids(self) -> None:
        google = "https://play.google.com/store/apps/details?id=com.example.app&hl=en"
        apple = "https://apps.apple.com/us/app/example/id123456789"
        self.assertEqual(parse_google_app_id_from_link(google), "com.example.app")
        self.assertEqual(parse_apple_app_id_from_link(apple), "123456789")

    def test_collect_google_reviews_normalizes_and_applies_limit(self) -> None:
        fake_module = types.ModuleType("google_play_scraper")
        fake_module.Sort = types.SimpleNamespace(NEWEST="newest")

        def fake_reviews_all(*args, **kwargs):  # type: ignore[no-untyped-def]
            del args, kwargs
            return [
                {
                    "reviewId": "g-1",
                    "at": dt.datetime(2026, 2, 16, 10, 0, 0),
                    "score": 5,
                    "title": "Great",
                    "content": "Very helpful",
                    "userName": "user1",
                },
                {
                    "reviewId": "g-2",
                    "at": dt.datetime(2026, 2, 15, 9, 0, 0),
                    "score": 4,
                    "title": "Good",
                    "content": "Nice app",
                    "userName": "user2",
                },
            ]

        fake_module.reviews_all = fake_reviews_all  # type: ignore[attr-defined]

        with patch.dict(sys.modules, {"google_play_scraper": fake_module}):
            rows = collect_google_reviews(app_id="com.example.app", country="US", lang="en", limit=1)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["review_id"], "g-1")
        self.assertEqual(rows[0]["rating"], "5")
        self.assertEqual(rows[0]["reviewer_name"], "user1")
        self.assertTrue(rows[0]["source_url"].startswith("https://play.google.com/"))

    def test_collect_apple_reviews_with_fallback_id_and_limit(self) -> None:
        payload = {
            "feed": {
                "entry": [
                    {"title": {"label": "app metadata"}},
                    {
                        "id": {"label": "a-1"},
                        "updated": {"label": "2026-02-16T10:00:00-07:00"},
                        "im:rating": {"label": "5"},
                        "title": {"label": "Great"},
                        "content": {"label": "Works well"},
                        "author": {"name": {"label": "alice"}},
                    },
                    {
                        "updated": {"label": "2026-02-16T09:00:00-07:00"},
                        "im:rating": {"label": "4"},
                        "title": {"label": "Nice"},
                        "content": {"label": "Useful"},
                        "author": {"name": {"label": "bob"}},
                    },
                ]
            }
        }

        fake_requests = types.ModuleType("requests")

        def fake_get(*args, **kwargs):  # type: ignore[no-untyped-def]
            del args, kwargs
            return FakeResponse(200, payload)

        fake_requests.get = fake_get  # type: ignore[attr-defined]

        with patch.dict(sys.modules, {"requests": fake_requests}):
            rows = collect_apple_reviews(app_id="123456789", country="US", lang="en", limit=2)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["review_id"], "a-1")
        self.assertTrue(rows[1]["review_id"].startswith("hash:"))
        self.assertEqual(rows[1]["rating"], "4")
        self.assertTrue(rows[0]["source_url"].startswith("https://apps.apple.com/us/app/id123456789"))


if __name__ == "__main__":
    unittest.main()
