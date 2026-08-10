#!/usr/bin/env python3
"""Export aggregated daily commit counts to activity.json.

Privacy boundary: ONLY the following leave the local database:
  - dates and per-day commit counts
  - global / per-year language → file-touch totals (allowlisted names only)

Repo names, file paths, commit messages, authors, diff stats, and raw
extensions never appear in the output.

Usage:
    python3 scripts/export.py --db /path/to/attendance.db [--out activity.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Reject anything that could be a path or extension leak.
SAFE_LANG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+#. -]{0,63}$")

# Must stay in sync with attendance-record/backend/constants/languages.py values.
ALLOWED_LANGUAGES = frozenset(
    {
        "TypeScript",
        "JavaScript",
        "Vue",
        "Python",
        "Java",
        "Kotlin",
        "Go",
        "Rust",
        "Ruby",
        "PHP",
        "C#",
        "F#",
        "Swift",
        "Objective-C",
        "C",
        "C++",
        "Scala",
        "R",
        "Dart",
        "Lua",
        "Perl",
        "Elixir",
        "Erlang",
        "Haskell",
        "Clojure",
        "Groovy",
        "Shell",
        "PowerShell",
        "SQL",
        "HTML",
        "CSS",
        "SCSS",
        "Less",
        "JSON",
        "YAML",
        "TOML",
        "XML",
        "Markdown",
        "reStructuredText",
        "TeX",
        "Jupyter Notebook",
        "GraphQL",
        "Protocol Buffer",
        "HCL",
        "Dockerfile",
        "Makefile",
        "CMake",
    }
)


def _safe_language(name: object) -> str | None:
    if not isinstance(name, str):
        return None
    if name not in ALLOWED_LANGUAGES:
        return None
    if "/" in name or "\\" in name or ".." in name:
        return None
    if name.startswith("."):
        return None
    if not SAFE_LANG_RE.match(name):
        return None
    return name


def _sorted_lang_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def _aggregate_languages(
    conn: sqlite3.Connection,
) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(git_commits)")}
    if "languages_json" not in cols:
        print(
            "warning: git_commits.languages_json missing — restart attendance-record "
            "API once, then re-sync git history to backfill languages",
            file=sys.stderr,
        )
        return {}, {}

    totals: Counter[str] = Counter()
    by_year: dict[str, Counter[str]] = defaultdict(Counter)

    for date_str, raw in conn.execute(
        "SELECT commit_date, languages_json FROM git_commits"
    ):
        if not DATE_RE.match(date_str or "") or not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue

        year = date_str[:4]
        for key, value in parsed.items():
            lang = _safe_language(key)
            if lang is None:
                continue
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                continue
            totals[lang] += value
            by_year[year][lang] += value

    languages = _sorted_lang_counts(totals)
    languages_by_year = {
        year: _sorted_lang_counts(counter)
        for year, counter in sorted(by_year.items())
    }
    return languages, languages_by_year


def _assert_lang_map(lang_map: dict[str, int]) -> None:
    assert all(
        _safe_language(k) and isinstance(v, int) and v > 0 for k, v in lang_map.items()
    )


def export(db_path: Path, out_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT commit_date, COUNT(*) FROM git_commits "
            "GROUP BY commit_date ORDER BY commit_date"
        ).fetchall()
        languages, languages_by_year = _aggregate_languages(conn)
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
        "languages": languages,
        "languages_by_year": languages_by_year,
    }

    # Guard: refuse to write anything but the expected keys.
    assert set(payload) == {
        "generated_at",
        "total",
        "counts",
        "languages",
        "languages_by_year",
    }
    _assert_lang_map(languages)
    assert all(DATE_RE.match(f"{y}-01-01") for y in languages_by_year)
    for year_map in languages_by_year.values():
        _assert_lang_map(year_map)

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
    langs = len(payload["languages"])
    years = len(payload["languages_by_year"])
    print(
        f"exported {payload['total']} commits across {days} days, "
        f"{langs} languages / {years} years -> {args.out}"
    )


if __name__ == "__main__":
    main()
