from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .audit import audit_csv
from .render import to_html, to_json, to_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-quality-auditor",
        description="Audit common CSV data-quality problems.",
    )
    parser.add_argument("csv_file", help="Path to the CSV file to audit.")
    parser.add_argument(
        "--unique",
        action="append",
        default=[],
        metavar="COLUMN",
        help="Require a column to contain unique non-empty values. Repeatable.",
    )
    parser.add_argument("--json", dest="json_path", help="Write JSON report to this path.")
    parser.add_argument("--html", dest="html_path", help="Write HTML report to this path.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Exit with code 2 if the quality score is below this value.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = audit_csv(args.csv_file, unique_columns=args.unique)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(to_text(report))

    if args.json_path:
        Path(args.json_path).write_text(to_json(report), encoding="utf-8")

    if args.html_path:
        Path(args.html_path).write_text(to_html(report), encoding="utf-8")

    if args.min_score is not None and report.score < args.min_score:
        return 2

    return 0
