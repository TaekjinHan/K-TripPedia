import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_script_module():  # type: ignore[no-untyped-def]
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "fetch_app_reviews.py"
    spec = importlib.util.spec_from_file_location("fetch_app_reviews_script", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load fetch_app_reviews.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FetchAppReviewsScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script_module()

    def test_normalize_target_row_supports_alias_and_link_parsing(self) -> None:
        row = {
            "앱 이름": "Example App",
            "google_link": "https://play.google.com/store/apps/details?id=com.example.app",
            "apple_link": "https://apps.apple.com/us/app/example/id123456789",
            "markets": "KR, US,JP",
        }
        target = self.module.normalize_target_row(row, ["KR", "US", "JP"])
        self.assertEqual(target["service_name"], "Example App")
        self.assertEqual(target["google_app_id"], "com.example.app")
        self.assertEqual(target["apple_app_id"], "123456789")
        self.assertEqual(target["markets"], ["KR", "US", "JP"])

    def test_normalize_target_row_supports_playstore_appstore_headers(self) -> None:
        row = {
            "앱 이름": "Example App",
            "playstore": "https://play.google.com/store/apps/details?id=com.example.app",
            "appstore": "https://apps.apple.com/us/app/example/id123456789",
        }
        target = self.module.normalize_target_row(row, ["KR", "US", "JP"])
        self.assertEqual(target["google_app_id"], "com.example.app")
        self.assertEqual(target["apple_app_id"], "123456789")

    def test_normalize_target_row_treats_nan_as_empty(self) -> None:
        row = {
            "service_name": float("nan"),
            "google_app_id": float("nan"),
            "apple_app_id": float("nan"),
            "google_link": "https://play.google.com/store/apps/details?id=com.example.nan",
            "apple_link": "",
            "markets": float("nan"),
        }
        target = self.module.normalize_target_row(row, ["KR", "US", "JP"])
        self.assertEqual(target["service_name"], "com.example.nan")
        self.assertEqual(target["google_app_id"], "com.example.nan")
        self.assertEqual(target["apple_app_id"], "")
        self.assertEqual(target["markets"], ["KR", "US", "JP"])

    def test_run_collection_collects_both_stores_and_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir(parents=True, exist_ok=True)
            out_dir = root / "data" / "reviews"

            target = {
                "service_name": "Ask Before You Eat",
                "google_app_id": "com.example.app",
                "apple_app_id": "123456789",
                "markets": ["US"],
            }

            def fake_google(app_id, country, lang, limit):  # type: ignore[no-untyped-def]
                del limit
                return [
                    {
                        "review_id": f"g-{country}",
                        "review_created_at": "2026-02-16T10:00:00",
                        "review_updated_at": "2026-02-16T10:00:00",
                        "rating": "5",
                        "title": f"Google {app_id}",
                        "content": f"lang={lang}",
                        "reviewer_name": "alice",
                        "source_url": "https://play.google.com/store/apps/details?id=com.example.app",
                    }
                ]

            def fake_apple(app_id, country, lang, limit):  # type: ignore[no-untyped-def]
                del limit
                return [
                    {
                        "review_id": f"a-{country}",
                        "review_created_at": "2026-02-16T11:00:00",
                        "review_updated_at": "2026-02-16T11:00:00",
                        "rating": "4",
                        "title": f"Apple {app_id}",
                        "content": f"lang={lang}",
                        "reviewer_name": "bob",
                        "source_url": "https://apps.apple.com/us/app/id123456789",
                    }
                ]

            created_xlsx: list[Path] = []

            def fake_xlsx(path, rows, sheet_name):  # type: ignore[no-untyped-def]
                del rows, sheet_name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok", encoding="utf-8")
                created_xlsx.append(path)

            with patch.object(self.module, "write_reviews_xlsx", side_effect=fake_xlsx):
                summary = self.module.run_collection(
                    root=root,
                    date_token="20260216",
                    targets=[target],
                    limit_per_app_country=0,
                    save_xlsx=True,
                    out_dir=out_dir,
                    google_collector=fake_google,
                    apple_collector=fake_apple,
                )

            self.assertEqual(summary["apps_total"], 1)
            self.assertEqual(summary["apps_processed"], 1)
            self.assertEqual(summary["rows_collected"], 2)
            self.assertEqual(summary["rows_inserted"], 2)
            self.assertEqual(summary["rows_updated"], 0)
            self.assertEqual(summary["errors"], [])
            self.assertEqual(summary["by_store_country"]["google_play:US"], 1)
            self.assertEqual(summary["by_store_country"]["apple_app_store:US"], 1)
            self.assertEqual(len(created_xlsx), 2)

            csv_rows = read_rows(root / "data" / "app_reviews.csv")
            self.assertEqual(len(csv_rows), 2)
            self.assertEqual({row["store"] for row in csv_rows}, {"google_play", "apple_app_store"})


if __name__ == "__main__":
    unittest.main()
