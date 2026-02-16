from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path
from typing import Any, Protocol, cast


class _StorageBaseModule(Protocol):
    TABLE_EXPORTS: dict[str, tuple[str, list[str]]]

    def ensure_schema(self) -> None: ...

    def _connect(self) -> sqlite3.Connection: ...

    def _fetch_rows(self, conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]: ...

    def pseudonymize_lead_email(self, lead_email: str) -> str: ...


class _StorageExportsModule(Protocol):
    def export_table_to_csv(self, table_name: str) -> Path: ...


def _base() -> _StorageBaseModule:
    return cast(_StorageBaseModule, cast(object, importlib.import_module("src.storage_base")))


def _exports() -> _StorageExportsModule:
    return cast(_StorageExportsModule, cast(object, importlib.import_module("src.storage_exports")))


def upsert_table_rows(table_name: str, rows: list[dict[str, str]], overwrite_date: str | None = None) -> None:
    base = _base()
    base.ensure_schema()
    if table_name not in base.TABLE_EXPORTS:
        raise ValueError(f"Unsupported table: {table_name}")
    if not rows and not overwrite_date:
        return

    with base._connect() as conn:
        if overwrite_date:
            conn.execute(f"DELETE FROM {table_name} WHERE date = ?", (overwrite_date,))

        if rows:
            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_sql = ", ".join(columns)
            update_columns = [
                c
                for c in columns
                if c
                not in {
                    "date",
                    "scenario_id",
                    "interview_id",
                    "meeting_id",
                    "response_id",
                    "check_id",
                    "post_id",
                    "store",
                    "app_id",
                    "country",
                    "review_id",
                }
            ]
            if table_name == "landing_cvr_daily":
                update_columns = ["visitors", "pilot_cta", "first_scan_cta", "total_cta"]
            set_sql = ", ".join([f"{c}=excluded.{c}" for c in update_columns])

            for row in rows:
                values = [row.get(c, "") for c in columns]
                conn.execute(
                    f"""
                    INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})
                    ON CONFLICT DO UPDATE SET {set_sql}
                    """,
                    values,
                )

    _exports().export_table_to_csv(table_name)


def upsert_landing_cvr_row(date_iso: str, channel: str) -> None:
    base = _base()
    base.ensure_schema()
    with base._connect() as conn:
        conn.execute(
            """
            INSERT INTO landing_cvr_daily (date, channel, visitors, pilot_cta, first_scan_cta, total_cta)
            VALUES (?, ?, 0, 0, 0, 0)
            ON CONFLICT(date, channel) DO NOTHING
            """,
            (date_iso, channel),
        )
    _exports().export_table_to_csv("landing_cvr_daily")


def append_landing_event_if_new(
    *,
    timestamp: str,
    date_iso: str,
    session_id: str,
    language: str,
    channel: str,
    source_id: str,
    post_id: str,
    event_type: str,
    cta_type: str,
    lead_email: str,
    consent: bool,
) -> bool:
    base = _base()
    base.ensure_schema()
    normalized_lead_email = base.pseudonymize_lead_email(lead_email)
    inserted = False
    with base._connect() as conn:
        before = conn.total_changes
        conn.execute(
            """
            INSERT INTO landing_events (
              timestamp,
              date,
              session_id,
              language,
              channel,
              source_id,
              post_id,
              event_type,
              cta_type,
              lead_email,
              consent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, session_id, channel, source_id, post_id, event_type, cta_type, lead_email) DO NOTHING
            """,
            (
                timestamp,
                date_iso,
                session_id,
                language,
                channel,
                source_id,
                post_id,
                event_type,
                cta_type,
                normalized_lead_email,
                1 if consent else 0,
            ),
        )
        inserted = conn.total_changes > before
    _exports().export_table_to_csv("landing_events")
    return inserted


def increment_landing_cvr(date_iso: str, channel: str, field: str, amount: int = 1) -> None:
    if field not in {"visitors", "pilot_cta", "first_scan_cta", "total_cta"}:
        raise ValueError(f"Unsupported cvr field: {field}")
    base = _base()
    base.ensure_schema()
    with base._connect() as conn:
        conn.execute(
            """
            INSERT INTO landing_cvr_daily (date, channel, visitors, pilot_cta, first_scan_cta, total_cta)
            VALUES (?, ?, 0, 0, 0, 0)
            ON CONFLICT(date, channel) DO NOTHING
            """,
            (date_iso, channel),
        )
        conn.execute(
            f"UPDATE landing_cvr_daily SET {field} = {field} + ? WHERE date = ? AND channel = ?",
            (amount, date_iso, channel),
        )
    _exports().export_table_to_csv("landing_cvr_daily")


def append_analytics_event(
    *,
    timestamp: str,
    date_iso: str,
    event_name: str,
    client_id: str,
    channel: str,
    language: str,
    status: str,
    payload: str,
) -> None:
    base = _base()
    base.ensure_schema()
    with base._connect() as conn:
        conn.execute(
            """
            INSERT INTO analytics_events (timestamp, date, event_name, client_id, channel, language, status, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, date_iso, event_name, client_id, channel, language, status, payload),
        )
    _exports().export_table_to_csv("analytics_events")


def upsert_app_reviews(rows: list[dict[str, str]]) -> dict[str, int]:
    base = _base()
    base.ensure_schema()
    if not rows:
        return {"inserted": 0, "updated": 0, "total": 0}

    inserted = 0
    updated = 0
    with base._connect() as conn:
        for row in rows:
            store = str(row.get("store", "")).strip()
            app_id = str(row.get("app_id", "")).strip()
            country = str(row.get("country", "")).strip().upper()
            review_id = str(row.get("review_id", "")).strip()
            if not store or not app_id or not country or not review_id:
                raise ValueError("store, app_id, country, review_id are required for app_reviews upsert")

            exists = conn.execute(
                """
                SELECT 1
                FROM app_reviews
                WHERE store = ? AND app_id = ? AND country = ? AND review_id = ?
                LIMIT 1
                """,
                (store, app_id, country, review_id),
            ).fetchone()

            conn.execute(
                """
                INSERT INTO app_reviews (
                  timestamp,
                  date,
                  service_name,
                  store,
                  app_id,
                  country,
                  language,
                  review_id,
                  review_created_at,
                  review_updated_at,
                  rating,
                  title,
                  content,
                  reviewer_name,
                  source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(store, app_id, country, review_id) DO UPDATE SET
                  timestamp = excluded.timestamp,
                  date = excluded.date,
                  service_name = excluded.service_name,
                  language = excluded.language,
                  review_created_at = excluded.review_created_at,
                  review_updated_at = excluded.review_updated_at,
                  rating = excluded.rating,
                  title = excluded.title,
                  content = excluded.content,
                  reviewer_name = excluded.reviewer_name,
                  source_url = excluded.source_url
                """,
                (
                    str(row.get("timestamp", "")).strip(),
                    str(row.get("date", "")).strip(),
                    str(row.get("service_name", "")).strip(),
                    store,
                    app_id,
                    country,
                    str(row.get("language", "")).strip(),
                    review_id,
                    str(row.get("review_created_at", "")).strip(),
                    str(row.get("review_updated_at", "")).strip(),
                    str(row.get("rating", "")).strip(),
                    str(row.get("title", "")).strip(),
                    str(row.get("content", "")).strip(),
                    str(row.get("reviewer_name", "")).strip(),
                    str(row.get("source_url", "")).strip(),
                ),
            )
            if exists:
                updated += 1
            else:
                inserted += 1

    _exports().export_table_to_csv("app_reviews")
    return {"inserted": inserted, "updated": updated, "total": len(rows)}


def fetch_metrics_rows(table_name: str, date_iso: str) -> list[dict[str, Any]]:
    base = _base()
    base.ensure_schema()
    with base._connect() as conn:
        return base._fetch_rows(conn, f"SELECT * FROM {table_name} WHERE date = ?", (date_iso,))


def append_pre_apply_history(path: Path, date_iso: str, summary_line: str) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    history_header = "## History"
    if history_header not in lines:
        lines.extend(["", history_header])
    idx = lines.index(history_header)
    tail = lines[idx + 1 :]
    entry = f"- {date_iso}: {summary_line}"
    if entry in tail:
        return
    lines.insert(idx + 1, entry)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
