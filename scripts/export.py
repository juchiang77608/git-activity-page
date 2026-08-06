#!/usr/bin/env python3
"""Export aggregated daily commit counts to activity.json.

Privacy boundary: ONLY dates and per-day commit counts are exported.
Repo names, file paths, commit messages, authors, and diff stats
never leave the local database.

Usage:
    python3 scripts/export.py --db /path/to/attendance.db [--out activity.json]
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def export(db_path: Path, out_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT commit_date, COUNT(*) FROM git_commits GROUP BY commit_date ORDER BY commit_date"
        ).fetchall()
    finally:
        conn.close()

    counts = {}
    for date_str, n in rows:
        if not DATE_RE.match(date_str or ""):
            print(f"warning: skipping malformed date {date_str!r}", file=sys.stderr)
            continue
        counts[date_str] = n

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(counts.values()),
        "counts": counts,
    }

    # Guard: refuse to write anything but the expected keys.
    assert set(payload) == {"generated_at", "total", "counts"}

    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=0) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="path to attendance.db")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "activity.json",
        help="output JSON path (default: repo root activity.json)",
    )
    args = parser.parse_args()

    if not args.db.exists():
        sys.exit(f"error: database not found: {args.db}")

    payload = export(args.db, args.out)
    days = len(payload["counts"])
    print(f"exported {payload['total']} commits across {days} days -> {args.out}")


if __name__ == "__main__":
    main()
