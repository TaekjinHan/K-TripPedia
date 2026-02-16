"""Common helpers for app-review collectors."""

from __future__ import annotations

import hashlib
import math
import re
from typing import TypedDict
from urllib.parse import parse_qs, urlparse


COUNTRY_LANGUAGE_MAP = {
    "KR": "ko",
    "US": "en",
    "JP": "ja",
}


class NormalizedReview(TypedDict):
    """Normalized review record used across store collectors."""

    review_id: str
    review_created_at: str
    review_updated_at: str
    rating: str
    title: str
    content: str
    reviewer_name: str
    source_url: str


def to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def normalize_app_id(value: object) -> str:
    text = to_text(value)
    if not text:
        return ""
    if text.endswith(".0") and text.replace(".", "", 1).isdigit():
        return text[:-2]
    return text


def parse_google_app_id_from_link(link: str) -> str:
    raw = to_text(link)
    if not raw:
        return ""
    parsed = urlparse(raw)
    query = parse_qs(parsed.query)
    if "id" in query and query["id"]:
        return to_text(query["id"][0])
    return ""


def parse_apple_app_id_from_link(link: str) -> str:
    raw = to_text(link)
    if not raw:
        return ""
    match = re.search(r"/id(\d+)", raw)
    if not match:
        return ""
    return to_text(match.group(1))


def normalize_country(country: str) -> str:
    return to_text(country).upper()


def default_language_for_country(country: str) -> str:
    normalized = normalize_country(country)
    return COUNTRY_LANGUAGE_MAP.get(normalized, "en")


def normalize_markets(raw: object, fallback: list[str]) -> list[str]:
    text = to_text(raw)
    if not text:
        return [normalize_country(code) for code in fallback]
    tokens = [token.strip().upper() for token in re.split(r"[,\s;]+", text) if token.strip()]
    if not tokens:
        return [normalize_country(code) for code in fallback]
    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def sanitize_filename(value: str) -> str:
    text = to_text(value)
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    sanitized = re.sub(r"\s+", "_", sanitized)
    return sanitized or "unnamed"


def build_fallback_review_id(*parts: str) -> str:
    joined = "||".join([to_text(part) for part in parts])
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return f"hash:{digest[:24]}"
