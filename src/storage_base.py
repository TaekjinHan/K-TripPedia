from __future__ import annotations

import csv
import datetime as dt
import hashlib
import os
import sqlite3
import tempfile
import threading
from pathlib import Path
from typing import Any


TABLE_EXPORTS = {
    "landing_events": (
        "landing_events.csv",
        [
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
        ],
    ),
    "landing_cvr_daily": (
        "landing_cvr.csv",
        [
            "date",
            "channel",
            "visitors",
            "pilot_cta",
            "first_scan_cta",
            "total_cta",
        ],
    ),
    "analytics_events": (
        "analytics_events.csv",
        [
            "timestamp",
            "event_name",
            "client_id",
            "channel",
            "language",
            "status",
            "payload",
        ],
    ),
    "app_reviews": (
        "app_reviews.csv",
        [
            "timestamp",
            "date",
            "service_name",
            "store",
            "app_id",
            "country",
            "language",
            "review_id",
            "review_created_at",
            "review_updated_at",
            "rating",
            "title",
            "content",
            "reviewer_name",
            "source_url",
        ],
    ),
    "community_outreach_log": (
        "community_outreach_log.csv",
        [
            "date",
            "platform",
            "community_name",
            "post_id",
            "url",
            "language",
            "impressions",
            "clicks",
            "visitors",
            "cta",
            "leads",
            "status",
            "notes",
        ],
    ),
    "trip_safety": (
        "trip_safety.csv",
        [
            "scenario_id",
            "date",
            "persona",
            "menu",
            "restriction",
            "risk_light",
            "confidence",
            "evidence_count",
            "show_mode_used",
            "quick_help_used",
            "resolved",
            "time_sec",
        ],
    ),
    "interview_log": (
        "interview_log.csv",
        [
            "interview_id",
            "date",
            "segment",
            "language",
            "pain_tags",
            "quote",
        ],
    ),
    "b2b_pipeline": (
        "b2b_pipeline.csv",
        [
            "meeting_id",
            "date",
            "partner_type",
            "partner_name",
            "status",
            "loi_signed",
            "intent_email",
            "notes",
        ],
    ),
    "trip_pass_pricing": (
        "trip_pass_pricing.csv",
        [
            "response_id",
            "date",
            "persona",
            "price_card",
            "selected",
            "willing_to_pay",
        ],
    ),
    "guardrail_checklist": (
        "guardrail_checklist.csv",
        [
            "check_id",
            "date",
            "scenario_id",
            "banned_expression_found",
            "evidence_missing",
            "confidence_missing",
            "reviewer",
            "notes",
        ],
    ),
}


_EXPORT_LOCK = threading.Lock()
_SCHEMA_LOCK = threading.Lock()
_schema_ready = False
_schema_ready_db: Path | None = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    override = os.getenv("KTRIPPEDIA_DATA_DIR", "").strip()
    if override:
        return Path(override)
    return project_root() / "data"


def db_path() -> Path:
    return data_dir() / "ktrippedia.db"


def normalize_date_token(date_token: str) -> str:
    token = (date_token or "").strip()
    if len(token) != 8 or not token.isdigit():
        raise ValueError("date_token must be YYYYMMDD")
    try:
        dt.datetime.strptime(token, "%Y%m%d")
    except ValueError as exc:
        raise ValueError("date_token must be a valid calendar date in YYYYMMDD") from exc
    return token


def date_token_to_iso(date_token: str) -> str:
    token = normalize_date_token(date_token)
    return f"{token[0:4]}-{token[4:6]}-{token[6:8]}"


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, column_type: str) -> None:
    info_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing = {row[1] for row in info_rows}
    if column_name not in existing:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def pseudonymize_lead_email(lead_email: str) -> str:
    normalized = (lead_email or "").strip().lower()
    if not normalized:
        return ""
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def ensure_schema() -> None:
    global _schema_ready
    global _schema_ready_db
    current_db = db_path().resolve()
    if _schema_ready and _schema_ready_db == current_db:
        return
    with _SCHEMA_LOCK:
        if _schema_ready and _schema_ready_db == current_db:
            return
        with _connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.executescript(
                """
            CREATE TABLE IF NOT EXISTS landing_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp TEXT NOT NULL,
              date TEXT NOT NULL,
              session_id TEXT NOT NULL,
              language TEXT,
              channel TEXT NOT NULL,
              source_id TEXT,
              post_id TEXT,
              event_type TEXT NOT NULL,
              cta_type TEXT,
              lead_email TEXT,
              consent INTEGER NOT NULL DEFAULT 0
            );
            CREATE UNIQUE INDEX IF NOT EXISTS ux_landing_events_dedup
            ON landing_events (date, session_id, channel, event_type, cta_type, lead_email);

            CREATE TABLE IF NOT EXISTS landing_cvr_daily (
              date TEXT NOT NULL,
              channel TEXT NOT NULL,
              visitors INTEGER NOT NULL DEFAULT 0,
              pilot_cta INTEGER NOT NULL DEFAULT 0,
              first_scan_cta INTEGER NOT NULL DEFAULT 0,
              total_cta INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY (date, channel)
            );

            CREATE TABLE IF NOT EXISTS analytics_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp TEXT NOT NULL,
              date TEXT NOT NULL,
              event_name TEXT NOT NULL,
              client_id TEXT NOT NULL,
              channel TEXT NOT NULL,
              language TEXT,
              status TEXT NOT NULL,
              payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_reviews (
              timestamp TEXT NOT NULL,
              date TEXT NOT NULL,
              service_name TEXT NOT NULL,
              store TEXT NOT NULL,
              app_id TEXT NOT NULL,
              country TEXT NOT NULL,
              language TEXT NOT NULL,
              review_id TEXT NOT NULL,
              review_created_at TEXT,
              review_updated_at TEXT,
              rating TEXT,
              title TEXT,
              content TEXT,
              reviewer_name TEXT,
              source_url TEXT,
              PRIMARY KEY (store, app_id, country, review_id)
            );
            CREATE INDEX IF NOT EXISTS ix_app_reviews_date_store
              ON app_reviews (date, store);

            CREATE TABLE IF NOT EXISTS trip_safety (
              scenario_id TEXT NOT NULL,
              date TEXT NOT NULL,
              persona TEXT,
              menu TEXT,
              restriction TEXT,
              risk_light TEXT,
              confidence TEXT,
              evidence_count TEXT,
              show_mode_used TEXT,
              quick_help_used TEXT,
              resolved TEXT,
              time_sec TEXT,
              PRIMARY KEY (date, scenario_id)
            );

            CREATE TABLE IF NOT EXISTS interview_log (
              interview_id TEXT NOT NULL,
              date TEXT NOT NULL,
              segment TEXT,
              language TEXT,
              pain_tags TEXT,
              quote TEXT,
              PRIMARY KEY (date, interview_id)
            );

            CREATE TABLE IF NOT EXISTS b2b_pipeline (
              meeting_id TEXT NOT NULL,
              date TEXT NOT NULL,
              partner_type TEXT,
              partner_name TEXT,
              status TEXT,
              loi_signed TEXT,
              intent_email TEXT,
              notes TEXT,
              PRIMARY KEY (date, meeting_id)
            );

            CREATE TABLE IF NOT EXISTS trip_pass_pricing (
              response_id TEXT NOT NULL,
              date TEXT NOT NULL,
              persona TEXT,
              price_card TEXT,
              selected TEXT,
              willing_to_pay TEXT,
              PRIMARY KEY (date, response_id)
            );

            CREATE TABLE IF NOT EXISTS guardrail_checklist (
              check_id TEXT NOT NULL,
              date TEXT NOT NULL,
              scenario_id TEXT,
              banned_expression_found TEXT,
              evidence_missing TEXT,
              confidence_missing TEXT,
              reviewer TEXT,
              notes TEXT,
              PRIMARY KEY (date, check_id)
            );

            CREATE TABLE IF NOT EXISTS community_outreach_log (
              date TEXT NOT NULL,
              platform TEXT NOT NULL,
              community_name TEXT,
              post_id TEXT NOT NULL,
              url TEXT,
              language TEXT,
              impressions TEXT,
              clicks TEXT,
              visitors TEXT,
              cta TEXT,
              leads TEXT,
              status TEXT,
              notes TEXT,
              PRIMARY KEY (date, post_id)
            );
                """
            )
            _ensure_column(conn, "landing_events", "source_id", "TEXT")
            _ensure_column(conn, "landing_events", "post_id", "TEXT")
            conn.execute("DROP INDEX IF EXISTS ux_landing_events_dedup")
            rows = conn.execute(
                """
                SELECT id, lead_email
                FROM landing_events
                WHERE TRIM(COALESCE(lead_email, '')) != ''
                  AND lead_email NOT LIKE 'sha256:%'
                """
            ).fetchall()
            for row in rows:
                conn.execute(
                    "UPDATE landing_events SET lead_email = ? WHERE id = ?",
                    (pseudonymize_lead_email(str(row["lead_email"])), int(row["id"])),
                )
            conn.execute(
                """
                DELETE FROM landing_events
                WHERE id NOT IN (
                  SELECT MIN(id)
                  FROM landing_events
                  GROUP BY date, session_id, channel, source_id, post_id, event_type, cta_type, lead_email
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_landing_events_dedup
                ON landing_events (
                  date,
                  session_id,
                  channel,
                  source_id,
                  post_id,
                  event_type,
                  cta_type,
                  lead_email
                )
                """
            )
        _schema_ready = True
        _schema_ready_db = current_db


def _atomic_write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _EXPORT_LOCK:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
            tmp_path = Path(handle.name)
        tmp_path.replace(path)


def _fetch_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]
