import unittest

from mailtm_code_report.extractor import extract_codes, normalize_message_text


class ExtractorTest(unittest.TestCase):
    def test_extracts_numeric_code_near_context(self) -> None:
        self.assertEqual(extract_codes("Your verification code is 123456"), ["123456"])

    def test_extracts_russian_context(self) -> None:
        self.assertEqual(extract_codes("Ваш код подтверждения: 9876"), ["9876"])

    def test_removes_html_tags(self) -> None:
        self.assertEqual(normalize_message_text("<p>Code&nbsp;<b>123456</b></p>"), "Code 123456")

    def test_supports_custom_regex(self) -> None:
        self.assertEqual(extract_codes("Code: ABC-123", custom_pattern=r"[A-Z]{3}-\d{3}"), ["ABC-123"])


if __name__ == "__main__":
    unittest.main()
