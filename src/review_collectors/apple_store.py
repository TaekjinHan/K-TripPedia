"""Apple App Store review collector."""

from __future__ import annotations

from src.review_collectors.common import (
    NormalizedReview,
    build_fallback_review_id,
    normalize_country,
    to_text,
)


def _extract_review_entries(entries: list[dict]) -> list[dict]:
    return [entry for entry in entries if isinstance(entry, dict) and "im:rating" in entry]


def _parse_entry(entry: dict, app_id: str, country: str) -> NormalizedReview:
    updated = to_text(entry.get("updated", {}).get("label"))
    title = to_text(entry.get("title", {}).get("label"))
    content = to_text(entry.get("content", {}).get("label"))
    reviewer_name = to_text(entry.get("author", {}).get("name", {}).get("label"))
    review_id = to_text(entry.get("id", {}).get("label")) or build_fallback_review_id(
        updated,
        reviewer_name,
        title,
        content,
    )
    return {
        "review_id": review_id,
        "review_created_at": updated,
        "review_updated_at": updated,
        "rating": to_text(entry.get("im:rating", {}).get("label")),
        "title": title,
        "content": content,
        "reviewer_name": reviewer_name,
        "source_url": f"https://apps.apple.com/{country.lower()}/app/id{app_id}",
    }


def collect_apple_reviews(
    app_id: str,
    country: str,
    lang: str,
    limit: int = 0,
) -> list[NormalizedReview]:
    del lang  # kept for signature symmetry with google collector
    app = to_text(app_id)
    if not app:
        raise ValueError("app_id is required")

    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for Apple App Store review collection") from exc

    country_code = normalize_country(country)
    reviews: list[NormalizedReview] = []
    page = 1

    while True:
        url = (
            f"https://itunes.apple.com/{country_code}/rss/customerreviews/"
            f"page={page}/id={app}/sortBy=mostRecent/json"
        )
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            break

        payload = response.json()
        entries = payload.get("feed", {}).get("entry", [])
        if not entries:
            break

        review_entries = _extract_review_entries(entries)
        if not review_entries:
            break

        for entry in review_entries:
            reviews.append(_parse_entry(entry=entry, app_id=app, country=country_code))
            if limit > 0 and len(reviews) >= limit:
                return reviews[:limit]

        if len(entries) < 50:
            break
        page += 1

    if limit > 0:
        return reviews[:limit]
    return reviews
