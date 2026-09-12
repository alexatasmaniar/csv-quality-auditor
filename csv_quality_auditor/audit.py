from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import csv
import re
from typing import Iterable

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{6,}$")

NULL_LIKE = {"", "null", "none", "n/a", "na", "nan"}


@dataclass
class ColumnReport:
    name: str
    missing: int
    missing_rate: float
    whitespace_issues: int
    inferred_type: str
    invalid_values: int = 0
    distinct_values: int = 0


@dataclass
class AuditReport:
    file: str
    rows: int
    columns: int
    headers: list[str]
    duplicate_rows: int
    unique_violations: dict[str, int]
    column_reports: list[ColumnReport]
    score: float

    def to_dict(self) -> dict:
        result = asdict(self)
        return result


def _is_missing(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in NULL_LIKE


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _is_bool(value: str) -> bool:
    return value.strip().lower() in {
        "true", "false", "yes", "no", "y", "n", "1", "0"
    }


def _is_date(value: str) -> bool:
    candidates = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y")
    for fmt in candidates:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            pass
    return False


def infer_type(name: str, values: Iterable[str]) -> tuple[str, int]:
    cleaned = [v.strip() for v in values if not _is_missing(v)]
    if not cleaned:
        return "empty", 0

    lowered_name = name.lower()

    if "email" in lowered_name:
        invalid = sum(not bool(EMAIL_RE.match(v)) for v in cleaned)
        return "email", invalid

    if "phone" in lowered_name or "mobile" in lowered_name or "tel" in lowered_name:
        invalid = sum(not bool(PHONE_RE.match(v)) for v in cleaned)
        return "phone", invalid

    if all(_is_int(v) for v in cleaned):
        return "integer", 0

    if all(_is_float(v) for v in cleaned):
        return "number", 0

    if all(_is_bool(v) for v in cleaned):
        return "boolean", 0

    if all(_is_date(v) for v in cleaned):
        return "date", 0

    return "text", 0


def _calculate_score(
    *,
    rows: int,
    columns: int,
    duplicate_rows: int,
    column_reports: list[ColumnReport],
    unique_violations: dict[str, int],
) -> float:
    if rows == 0 or columns == 0:
        return 0.0

    total_cells = rows * columns
    missing = sum(c.missing for c in column_reports)
    whitespace = sum(c.whitespace_issues for c in column_reports)
    invalid = sum(c.invalid_values for c in column_reports)
    unique_bad = sum(unique_violations.values())

    penalty = 0.0
    penalty += (missing / total_cells) * 35
    penalty += (whitespace / total_cells) * 15
    penalty += (invalid / total_cells) * 25
    penalty += (duplicate_rows / rows) * 20
    penalty += (unique_bad / max(rows, 1)) * 20

    return round(max(0.0, 100.0 - penalty), 1)


def audit_csv(path: str | Path, unique_columns: Iterable[str] = ()) -> AuditReport:
    path = Path(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file does not contain a header row.")

        headers = list(reader.fieldnames)
        rows = list(reader)

    row_count = len(rows)

    normalized_rows = [
        tuple((row.get(header) or "").strip() for header in headers)
        for row in rows
    ]
    row_counter = Counter(normalized_rows)
    duplicate_rows = sum(count - 1 for count in row_counter.values() if count > 1)

    column_reports: list[ColumnReport] = []

    for header in headers:
        values = [(row.get(header) or "") for row in rows]
        missing = sum(_is_missing(v) for v in values)
        whitespace_issues = sum(
            1
            for v in values
            if v and not _is_missing(v) and v != v.strip()
        )
        inferred_type, invalid_values = infer_type(header, values)

        distinct_values = len(
            {v.strip() for v in values if not _is_missing(v)}
        )

        column_reports.append(
            ColumnReport(
                name=header,
                missing=missing,
                missing_rate=round((missing / row_count * 100), 1) if row_count else 0.0,
                whitespace_issues=whitespace_issues,
                inferred_type=inferred_type,
                invalid_values=invalid_values,
                distinct_values=distinct_values,
            )
        )

    unique_violations: dict[str, int] = {}
    for column in unique_columns:
        if column not in headers:
            raise ValueError(f"Unknown unique column: {column}")

        values = [
            (row.get(column) or "").strip()
            for row in rows
            if not _is_missing(row.get(column))
        ]
        counts = Counter(values)
        unique_violations[column] = sum(
            count - 1 for count in counts.values() if count > 1
        )

    score = _calculate_score(
        rows=row_count,
        columns=len(headers),
        duplicate_rows=duplicate_rows,
        column_reports=column_reports,
        unique_violations=unique_violations,
    )

    return AuditReport(
        file=str(path),
        rows=row_count,
        columns=len(headers),
        headers=headers,
        duplicate_rows=duplicate_rows,
        unique_violations=unique_violations,
        column_reports=column_reports,
        score=score,
    )
