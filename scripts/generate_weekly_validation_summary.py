#!/usr/bin/env python3
"""Generate weekly validation summary for community traffic KPI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.weekly_validation_summary import run_weekly_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly validation summary report")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--start", default="20260216", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="20260222", help="End date YYYYMMDD")
    parser.add_argument("--out", default="reports/weekly_validation_summary.md", help="Output markdown path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_path = run_weekly_summary(root=root, start_token=args.start, end_token=args.end, out_relative_path=args.out)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
