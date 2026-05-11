import json
import tempfile
import unittest
from pathlib import Path

from mailtm_code_report.scanner import AccountCredentials, load_accounts


class ScannerTest(unittest.TestCase):
    def test_load_accounts_from_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accounts.json"
            path.write_text(
                json.dumps({"accounts": [{"address": "user@example.test", "password": "secret"}]}),
                encoding="utf-8",
            )

            self.assertEqual(load_accounts(path), [AccountCredentials("user@example.test", "secret")])

    def test_load_accounts_rejects_missing_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accounts.json"
            path.write_text(json.dumps({"accounts": [{"address": "user@example.test"}]}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_accounts(path)


if __name__ == "__main__":
    unittest.main()
