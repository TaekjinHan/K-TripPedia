#!/usr/bin/env python3
"""Migrate cumulative/date CSV files into SQLite SoT."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.csv_to_sqlite_migration import run_migration


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate CSV datasets into SQLite")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--dry-run", action="store_true", help="Do not write; print counts only")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    stats = run_migration(root=root, dry_run=bool(args.dry_run))
    for name, count in stats.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
