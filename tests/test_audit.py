from pathlib import Path
import csv
import tempfile
import unittest

from csv_quality_auditor.audit import audit_csv, infer_type


class AuditTests(unittest.TestCase):
    def write_csv(self, rows):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            newline="",
            encoding="utf-8",
            delete=False,
        )
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_detects_missing_duplicate_and_whitespace(self):
        path = self.write_csv([
            {"id": "1", "name": " Alice ", "email": "alice@example.com"},
            {"id": "2", "name": "Bob", "email": ""},
            {"id": "2", "name": "Bob", "email": ""},
        ])

        report = audit_csv(path, unique_columns=["id"])

        self.assertEqual(report.rows, 3)
        self.assertEqual(report.columns, 3)
        self.assertEqual(report.duplicate_rows, 1)
        self.assertEqual(report.unique_violations["id"], 1)

        by_name = {item.name: item for item in report.column_reports}
        self.assertEqual(by_name["name"].whitespace_issues, 1)
        self.assertEqual(by_name["email"].missing, 2)

    def test_email_validation(self):
        inferred, invalid = infer_type(
            "email",
            ["good@example.com", "bad-address", ""],
        )
        self.assertEqual(inferred, "email")
        self.assertEqual(invalid, 1)

    def test_unknown_unique_column_fails(self):
        path = self.write_csv([{"id": "1"}])
        with self.assertRaises(ValueError):
            audit_csv(path, unique_columns=["missing_column"])

    def test_empty_csv_with_headers_scores_zero(self):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            newline="",
            encoding="utf-8",
            delete=False,
        )
        handle.write("id,name\n")
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))

        report = audit_csv(handle.name)
        self.assertEqual(report.rows, 0)
        self.assertEqual(report.score, 0.0)


if __name__ == "__main__":
    unittest.main()
