# CSV Quality Auditor

A small, dependency-light command-line tool for quickly auditing CSV files before they enter an analysis or automation pipeline.

It checks:

- row and column counts;
- missing values per column;
- duplicate rows;
- duplicate values for selected key columns;
- leading/trailing whitespace;
- basic type inference;
- invalid email addresses for email-like columns;
- invalid phone numbers for phone-like columns;
- simple quality scoring.

The tool can export both JSON and standalone HTML reports.

## Why this project exists

CSV files are everywhere in operations, analytics, support, imports, migrations and internal tooling. A quick automated audit catches common issues before they become production problems.

## Requirements

- Python 3.10+
- No runtime dependencies

## Quick start

```bash
python -m csv_quality_auditor examples/customers.csv
```

Export reports:

```bash
python -m csv_quality_auditor examples/customers.csv \
  --json report.json \
  --html report.html
```

Check uniqueness of one or more columns:

```bash
python -m csv_quality_auditor examples/customers.csv \
  --unique email \
  --unique customer_id
```

Fail CI when the score is below a threshold:

```bash
python -m csv_quality_auditor examples/customers.csv \
  --min-score 90
```

The process exits with code `2` when the score is below the requested threshold.

## Example output

```text
File: examples/customers.csv
Rows: 6
Columns: 5
Duplicate rows: 1
Quality score: 86.5/100

Column summary:
- customer_id: missing=0, whitespace=0, inferred=integer
- name: missing=0, whitespace=1, inferred=text
- email: missing=2, whitespace=0, inferred=email, invalid=1
- phone: missing=0, whitespace=0, inferred=phone, invalid=1
- age: missing=2, whitespace=0, inferred=integer
```

## Project structure

```text
csv-quality-auditor/
├── .github/
│   └── workflows/
│       └── ci.yml
├── csv_quality_auditor/
│   ├── __init__.py
│   ├── __main__.py
│   ├── audit.py
│   ├── cli.py
│   └── render.py
├── examples/
│   └── customers.csv
├── tests/
│   └── test_audit.py
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## Design choices

The first version intentionally uses only the Python standard library. That makes it easy to run in restricted environments, CI jobs, servers and one-off automation scripts.

The code separates:

- data inspection (`audit.py`);
- command-line behavior (`cli.py`);
- report rendering (`render.py`).

That keeps the project small while still making it easy to extend.

## Continuous integration

GitHub Actions automatically runs the test suite and a CLI smoke test on every push and pull request.

The workflow currently checks the project with Python 3.12.

## Possible next steps

- delimiter and encoding auto-detection;
- schema files;
- date-format validation;
- configurable validation rules;
- XLSX support;
- directory/batch mode;
- richer HTML visualizations.

## License

MIT
