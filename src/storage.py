from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Protocol, cast


class _StorageBaseModule(Protocol):
    TABLE_EXPORTS: dict[str, tuple[str, list[str]]]

    def project_root(self) -> Path: ...

    def data_dir(self) -> Path: ...

    def db_path(self) -> Path: ...

    def normalize_date_token(self, date_token: str) -> str: ...

    def date_token_to_iso(self, date_token: str) -> str: ...

    def pseudonymize_lead_email(self, lead_email: str) -> str: ...

    def ensure_schema(self) -> None: ...


class _StorageExportsModule(Protocol):
    def export_table_to_csv(self, table_name: str) -> Path: ...

    def export_all_tables_to_csv(self) -> None: ...


class _StorageRecordsModule(Protocol):
    def upsert_table_rows(self, table_name: str, rows: list[dict[str, str]], overwrite_date: str | None = None) -> None: ...

    def upsert_landing_cvr_row(self, date_iso: str, channel: str) -> None: ...

    def append_landing_event_if_new(
        self,
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
    ) -> bool: ...

    def increment_landing_cvr(self, date_iso: str, channel: str, field: str, amount: int = 1) -> None: ...

    def append_analytics_event(
        self,
        *,
        timestamp: str,
        date_iso: str,
        event_name: str,
        client_id: str,
        channel: str,
        language: str,
        status: str,
        payload: str,
    ) -> None: ...

    def upsert_app_reviews(self, rows: list[dict[str, str]]) -> dict[str, int]: ...

    def fetch_metrics_rows(self, table_name: str, date_iso: str) -> list[dict[str, Any]]: ...

    def append_pre_apply_history(self, path: Path, date_iso: str, summary_line: str) -> None: ...


def _base() -> _StorageBaseModule:
    return cast(_StorageBaseModule, cast(object, importlib.import_module("src.storage_base")))


def _exports() -> _StorageExportsModule:
    return cast(_StorageExportsModule, cast(object, importlib.import_module("src.storage_exports")))


def _records() -> _StorageRecordsModule:
    return cast(_StorageRecordsModule, cast(object, importlib.import_module("src.storage_records")))


TABLE_EXPORTS = _base().TABLE_EXPORTS


def project_root() -> Path:
    return _base().project_root()


def data_dir() -> Path:
    return _base().data_dir()


def db_path() -> Path:
    return _base().db_path()


def normalize_date_token(date_token: str) -> str:
    return _base().normalize_date_token(date_token)


def date_token_to_iso(date_token: str) -> str:
    return _base().date_token_to_iso(date_token)


def pseudonymize_lead_email(lead_email: str) -> str:
    return _base().pseudonymize_lead_email(lead_email)


def ensure_schema() -> None:
    _base().ensure_schema()


def export_table_to_csv(table_name: str) -> Path:
    return _exports().export_table_to_csv(table_name)


def export_all_tables_to_csv() -> None:
    _exports().export_all_tables_to_csv()


def upsert_table_rows(table_name: str, rows: list[dict[str, str]], overwrite_date: str | None = None) -> None:
    _records().upsert_table_rows(table_name, rows, overwrite_date=overwrite_date)


def upsert_landing_cvr_row(date_iso: str, channel: str) -> None:
    _records().upsert_landing_cvr_row(date_iso, channel)


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
    return _records().append_landing_event_if_new(
        timestamp=timestamp,
        date_iso=date_iso,
        session_id=session_id,
        language=language,
        channel=channel,
        source_id=source_id,
        post_id=post_id,
        event_type=event_type,
        cta_type=cta_type,
        lead_email=lead_email,
        consent=consent,
    )


def increment_landing_cvr(date_iso: str, channel: str, field: str, amount: int = 1) -> None:
    _records().increment_landing_cvr(date_iso, channel, field, amount=amount)


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
    _records().append_analytics_event(
        timestamp=timestamp,
        date_iso=date_iso,
        event_name=event_name,
        client_id=client_id,
        channel=channel,
        language=language,
        status=status,
        payload=payload,
    )


def upsert_app_reviews(rows: list[dict[str, str]]) -> dict[str, int]:
    return _records().upsert_app_reviews(rows)


def fetch_metrics_rows(table_name: str, date_iso: str) -> list[dict[str, Any]]:
    return _records().fetch_metrics_rows(table_name, date_iso)


def append_pre_apply_history(path: Path, date_iso: str, summary_line: str) -> None:
    _records().append_pre_apply_history(path, date_iso, summary_line)


__all__ = [
    "TABLE_EXPORTS",
    "project_root",
    "data_dir",
    "db_path",
    "normalize_date_token",
    "date_token_to_iso",
    "pseudonymize_lead_email",
    "ensure_schema",
    "export_table_to_csv",
    "export_all_tables_to_csv",
    "upsert_table_rows",
    "upsert_landing_cvr_row",
    "append_landing_event_if_new",
    "increment_landing_cvr",
    "append_analytics_event",
    "upsert_app_reviews",
    "fetch_metrics_rows",
    "append_pre_apply_history",
]
