#!/usr/bin/env python3
"""Export SQLite source-of-truth tables back to cumulative CSV files."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.storage import export_all_tables_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Export SQLite SoT to CSV")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    os.environ.setdefault("KTRIPPEDIA_DATA_DIR", str(root / "data"))
    export_all_tables_to_csv()
    print("Exported SQLite tables to cumulative CSV files.")


if __name__ == "__main__":
    main()
