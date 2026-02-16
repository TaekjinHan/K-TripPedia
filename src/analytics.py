"""GA4 analytics helper for Streamlit landing."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib import parse, request

from src.storage import append_analytics_event, date_token_to_iso, normalize_date_token


@dataclass
class GA4Tracker:
    measurement_id: str
    api_secret: str
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "GA4Tracker":
        measurement_id = os.getenv("GA4_MEASUREMENT_ID", "").strip()
        api_secret = os.getenv("GA4_API_SECRET", "").strip()
        enabled = bool(measurement_id and api_secret)
        return cls(
            measurement_id=measurement_id,
            api_secret=api_secret,
            enabled=enabled,
        )

    def _log_event(
        self,
        *,
        date_token: str,
        event_name: str,
        client_id: str,
        channel: str,
        language: str,
        status: str,
        payload: dict[str, Any],
    ) -> None:
        normalize_date_token(date_token)
        append_analytics_event(
            timestamp=dt.datetime.now().isoformat(timespec="seconds"),
            date_iso=date_token_to_iso(date_token),
            event_name=event_name,
            client_id=client_id,
            channel=channel,
            language=language,
            status=status,
            payload=json.dumps(payload, ensure_ascii=False),
        )

    def track(
        self,
        *,
        date_token: str,
        event_name: str,
        client_id: str,
        channel: str,
        language: str = "",
        params: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": event_name,
                    "params": {
                        "channel": channel,
                        "language": language or "",
                        **(params or {}),
                    },
                }
            ],
        }

        if not self.enabled:
            self._log_event(
                date_token=date_token,
                event_name=event_name,
                client_id=client_id,
                channel=channel,
                language=language,
                status="skipped_env_missing",
                payload=payload,
            )
            logging.info("GA4 skipped (missing env) event=%s", event_name)
            return

        query = parse.urlencode(
            {
                "measurement_id": self.measurement_id,
                "api_secret": self.api_secret,
            }
        )
        url = f"https://www.google-analytics.com/mp/collect?{query}"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=4) as resp:
                status = str(getattr(resp, "status", "200"))
            self._log_event(
                date_token=date_token,
                event_name=event_name,
                client_id=client_id,
                channel=channel,
                language=language,
                status=f"sent_{status}",
                payload=payload,
            )
            logging.info("GA4 sent event=%s status=%s", event_name, status)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:  # pragma: no cover
            self._log_event(
                date_token=date_token,
                event_name=event_name,
                client_id=client_id,
                channel=channel,
                language=language,
                status=f"error_{type(exc).__name__}",
                payload=payload,
            )
            logging.warning("GA4 send failed event=%s error=%s", event_name, exc)
