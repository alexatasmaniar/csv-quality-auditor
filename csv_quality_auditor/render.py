from __future__ import annotations

from html import escape
import json

from .audit import AuditReport


def to_json(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def to_text(report: AuditReport) -> str:
    lines = [
        f"File: {report.file}",
        f"Rows: {report.rows}",
        f"Columns: {report.columns}",
        f"Duplicate rows: {report.duplicate_rows}",
        f"Quality score: {report.score}/100",
        "",
        "Column summary:",
    ]

    for column in report.column_reports:
        extra = ""
        if column.invalid_values:
            extra = f", invalid={column.invalid_values}"

        lines.append(
            f"- {column.name}: missing={column.missing}, "
            f"whitespace={column.whitespace_issues}, "
            f"inferred={column.inferred_type}{extra}"
        )

    if report.unique_violations:
        lines.append("")
        lines.append("Unique constraints:")
        for column, count in report.unique_violations.items():
            lines.append(f"- {column}: duplicate values={count}")

    return "\n".join(lines)


def to_html(report: AuditReport) -> str:
    rows = []
    for column in report.column_reports:
        rows.append(
            "<tr>"
            f"<td>{escape(column.name)}</td>"
            f"<td>{column.missing}</td>"
            f"<td>{column.missing_rate}%</td>"
            f"<td>{column.whitespace_issues}</td>"
            f"<td>{escape(column.inferred_type)}</td>"
            f"<td>{column.invalid_values}</td>"
            f"<td>{column.distinct_values}</td>"
            "</tr>"
        )

    unique_html = ""
    if report.unique_violations:
        items = "".join(
            f"<li><strong>{escape(name)}</strong>: {count} duplicate value(s)</li>"
            for name, count in report.unique_violations.items()
        )
        unique_html = f"<h2>Unique constraints</h2><ul>{items}</ul>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CSV Quality Audit</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 1100px;
      margin: 40px auto;
      padding: 0 20px;
      line-height: 1.5;
    }}
    .score {{
      font-size: 2rem;
      font-weight: 700;
      margin: 0.5rem 0 1.5rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid #ddd;
      padding: 10px 8px;
    }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 2px 5px; }}
  </style>
</head>
<body>
  <h1>CSV Quality Audit</h1>
  <p><strong>File:</strong> <code>{escape(report.file)}</code></p>
  <p>Rows: {report.rows} · Columns: {report.columns} · Duplicate rows: {report.duplicate_rows}</p>
  <div class="score">Quality score: {report.score}/100</div>

  <h2>Columns</h2>
  <table>
    <thead>
      <tr>
        <th>Column</th>
        <th>Missing</th>
        <th>Missing rate</th>
        <th>Whitespace</th>
        <th>Type</th>
        <th>Invalid</th>
        <th>Distinct</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>

  {unique_html}
</body>
</html>
"""
