"""Landing page tracking utilities for K-TripPedia."""

from __future__ import annotations

import datetime as dt
import logging
import re

from src.storage import (
    append_landing_event_if_new,
    date_token_to_iso,
    increment_landing_cvr,
    normalize_date_token,
)


ALLOWED_CHANNELS = {
    "pre_arrival_qr",
    "community",
    "sns_shortform",
    "referral",
}

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_session_id(session_id: str) -> str:
    normalized = (session_id or "").strip()
    if not normalized:
        raise ValueError("session_id is required")
    return normalized


def _validate_lead_email(lead_email: str) -> str:
    email = (lead_email or "").strip()
    if not email:
        raise ValueError("lead_email is required when consent is True")
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("lead_email must be a valid email address")
    return email


def normalize_source_id(source_id: str) -> str:
    normalized = (source_id or "").strip().lower()
    return normalized


def normalize_post_id(post_id: str) -> str:
    normalized = (post_id or "").strip().lower()
    return normalized


def normalize_channel(channel: str) -> str:
    normalized = (channel or "").strip().lower()
    if normalized in ALLOWED_CHANNELS:
        return normalized
    if normalized:
        logging.warning("Unknown channel '%s'; fallback to referral", normalized)
    return "referral"


def track_visit(
    date_token: str,
    session_id: str,
    channel: str,
    source_id: str = "",
    post_id: str = "",
) -> None:
    normalize_date_token(date_token)
    normalized_session_id = _normalize_session_id(session_id)
    normalized_channel = normalize_channel(channel)
    normalized_source_id = normalize_source_id(source_id)
    normalized_post_id = normalize_post_id(post_id)
    date_iso = date_token_to_iso(date_token)
    now = dt.datetime.now().isoformat(timespec="seconds")

    inserted = append_landing_event_if_new(
        timestamp=now,
        date_iso=date_iso,
        session_id=normalized_session_id,
        language="",
        channel=normalized_channel,
        source_id=normalized_source_id,
        post_id=normalized_post_id,
        event_type="visit",
        cta_type="",
        lead_email="",
        consent=False,
    )
    if not inserted:
        logging.info("Skip duplicate visit session=%s channel=%s", normalized_session_id, normalized_channel)
        return

    increment_landing_cvr(date_iso=date_iso, channel=normalized_channel, field="visitors")
    logging.info(
        "Track visit session=%s channel=%s source=%s post_id=%s",
        normalized_session_id,
        normalized_channel,
        normalized_source_id,
        normalized_post_id,
    )


def track_cta(
    date_token: str,
    session_id: str,
    channel: str,
    cta_type: str,
    language: str,
    source_id: str = "",
    post_id: str = "",
) -> None:
    normalize_date_token(date_token)
    normalized_session_id = _normalize_session_id(session_id)
    normalized_channel = normalize_channel(channel)
    normalized_source_id = normalize_source_id(source_id)
    normalized_post_id = normalize_post_id(post_id)
    normalized_cta = (cta_type or "").strip().lower()
    if normalized_cta not in {"pilot", "first_scan"}:
        raise ValueError(f"Unsupported cta_type: {cta_type}")

    date_iso = date_token_to_iso(date_token)
    now = dt.datetime.now().isoformat(timespec="seconds")
    append_landing_event_if_new(
        timestamp=now,
        date_iso=date_iso,
        session_id=normalized_session_id,
        language=(language or "").strip().upper(),
        channel=normalized_channel,
        source_id=normalized_source_id,
        post_id=normalized_post_id,
        event_type="cta_click",
        cta_type=normalized_cta,
        lead_email="",
        consent=False,
    )

    if normalized_cta == "pilot":
        increment_landing_cvr(date_iso=date_iso, channel=normalized_channel, field="pilot_cta")
    else:
        increment_landing_cvr(date_iso=date_iso, channel=normalized_channel, field="first_scan_cta")
    increment_landing_cvr(date_iso=date_iso, channel=normalized_channel, field="total_cta")

    logging.info(
        "Track cta session=%s channel=%s cta=%s language=%s source=%s post_id=%s",
        normalized_session_id,
        normalized_channel,
        normalized_cta,
        language,
        normalized_source_id,
        normalized_post_id,
    )


def save_lead(
    date_token: str,
    session_id: str,
    channel: str,
    language: str,
    lead_email: str,
    consent: bool,
    source_id: str = "",
    post_id: str = "",
) -> None:
    normalize_date_token(date_token)
    normalized_session_id = _normalize_session_id(session_id)
    if not consent:
        logging.info("Skip lead save without consent session=%s", normalized_session_id)
        return

    normalized_channel = normalize_channel(channel)
    normalized_source_id = normalize_source_id(source_id)
    normalized_post_id = normalize_post_id(post_id)
    normalized_email = _validate_lead_email(lead_email)
    date_iso = date_token_to_iso(date_token)
    now = dt.datetime.now().isoformat(timespec="seconds")

    append_landing_event_if_new(
        timestamp=now,
        date_iso=date_iso,
        session_id=normalized_session_id,
        language=(language or "").strip().upper(),
        channel=normalized_channel,
        source_id=normalized_source_id,
        post_id=normalized_post_id,
        event_type="lead_submit",
        cta_type="",
        lead_email=normalized_email,
        consent=True,
    )
    logging.info(
        "Saved lead session=%s channel=%s source=%s post_id=%s",
        normalized_session_id,
        normalized_channel,
        normalized_source_id,
        normalized_post_id,
    )
