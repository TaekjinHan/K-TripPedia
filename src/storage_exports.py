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

    def data_dir(self) -> Path: ...

    def _atomic_write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None: ...


def _base() -> _StorageBaseModule:
    return cast(_StorageBaseModule, cast(object, importlib.import_module("src.storage_base")))


def export_table_to_csv(table_name: str) -> Path:
    base = _base()
    table_exports = base.TABLE_EXPORTS
    if table_name not in table_exports:
        raise ValueError(f"Unsupported export table: {table_name}")
    base.ensure_schema()
    filename, fieldnames = table_exports[table_name]

    with base._connect() as conn:
        if table_name == "landing_events":
            rows = base._fetch_rows(
                conn,
                """
                SELECT
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
                FROM landing_events
                ORDER BY timestamp ASC, id ASC
                """,
            )
            for row in rows:
                row["consent"] = str(int(row.get("consent") or 0))
        elif table_name == "landing_cvr_daily":
            rows = base._fetch_rows(
                conn,
                """
                SELECT date, channel, visitors, pilot_cta, first_scan_cta, total_cta
                FROM landing_cvr_daily
                ORDER BY date ASC, channel ASC
                """,
            )
        elif table_name == "analytics_events":
            rows = base._fetch_rows(
                conn,
                """
                SELECT timestamp, event_name, client_id, channel, language, status, payload
                FROM analytics_events
                ORDER BY timestamp ASC, id ASC
                """,
            )
        elif table_name == "app_reviews":
            rows = base._fetch_rows(
                conn,
                """
                SELECT
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
                FROM app_reviews
                ORDER BY date ASC, timestamp ASC, store ASC, app_id ASC, country ASC
                """,
            )
        else:
            rows = base._fetch_rows(conn, f"SELECT * FROM {table_name} ORDER BY date ASC")

    out_path = base.data_dir() / filename
    base._atomic_write_csv(out_path, fieldnames, rows)
    return out_path


def export_all_tables_to_csv() -> None:
    for table_name in _base().TABLE_EXPORTS:
        export_table_to_csv(table_name)
