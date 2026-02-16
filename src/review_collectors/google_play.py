"""Google Play review collector."""

from __future__ import annotations

from typing import Any

from src.review_collectors.common import NormalizedReview, build_fallback_review_id, normalize_country, to_text


def _to_iso(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return to_text(value)


def collect_google_reviews(
    app_id: str,
    country: str,
    lang: str,
    limit: int = 0,
) -> list[NormalizedReview]:
    app = to_text(app_id)
    if not app:
        raise ValueError("app_id is required")

    try:
        from google_play_scraper import Sort, reviews_all
    except ImportError as exc:
        raise RuntimeError("google-play-scraper is required for Google Play review collection") from exc

    country_code = normalize_country(country)
    language = to_text(lang).lower() or "en"

    raw_reviews = reviews_all(
        app,
        sleep_milliseconds=300,
        lang=language,
        country=country_code.lower(),
        sort=Sort.NEWEST,
    )

    if limit > 0:
        raw_reviews = raw_reviews[:limit]

    source_url = f"https://play.google.com/store/apps/details?id={app}"
    normalized_rows: list[NormalizedReview] = []
    for raw in raw_reviews:
        created = _to_iso(raw.get("at"))
        review_id = to_text(raw.get("reviewId")) or build_fallback_review_id(
            created,
            to_text(raw.get("userName")),
            to_text(raw.get("content")),
        )
        normalized_rows.append(
            {
                "review_id": review_id,
                "review_created_at": created,
                "review_updated_at": created,
                "rating": to_text(raw.get("score")),
                "title": to_text(raw.get("title")),
                "content": to_text(raw.get("content")),
                "reviewer_name": to_text(raw.get("userName")),
                "source_url": source_url,
            }
        )
    return normalized_rows
