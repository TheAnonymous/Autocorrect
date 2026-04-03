import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autocorrect import detect_language, clean_response


class TestDetectLanguage(unittest.TestCase):
    def test_german_chars(self):
        self.assertEqual(detect_language("Das ist ein Test mit öäüß Wörtern"), "de")

    def test_german_words(self):
        self.assertEqual(detect_language("Der Hund ist groß und nicht klein"), "de")

    def test_english_words(self):
        self.assertEqual(detect_language("The dog is big and not small"), "en")

    def test_mixed_german_heavy(self):
        self.assertEqual(detect_language("Das und ist nicht von dem den die"), "de")

    def test_mixed_english_heavy(self):
        self.assertEqual(detect_language("The and is not with from that this have"), "en")

    def test_short_german(self):
        self.assertEqual(detect_language("der Hund"), "de")

    def test_short_english(self):
        self.assertEqual(detect_language("the dog"), "en")

    def test_empty(self):
        self.assertEqual(detect_language(""), "en")


class TestCleanResponse(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(clean_response("Hello world"), "Hello world")

    def test_code_fence_python(self):
        self.assertEqual(clean_response("```python\nHello world\n```"), "Hello world")

    def test_code_fence_no_lang(self):
        self.assertEqual(clean_response("```\nHello world\n```"), "Hello world")

    def test_quotation_marks_english(self):
        self.assertEqual(clean_response('"Hello world"'), "Hello world")

    def test_quotation_marks_german(self):
        self.assertEqual(clean_response("\u201eHello world\u201c"), "Hello world")

    def test_leading_trailing_whitespace(self):
        self.assertEqual(clean_response("  Hello world  "), "Hello world")

    def test_code_fence_with_trailing_newline(self):
        self.assertEqual(clean_response("```javascript\nSome code\n```\n"), "Some code")

    def test_nested_quotes(self):
        self.assertEqual(clean_response('"She said hello"'), "She said hello")


if __name__ == "__main__":
    unittest.main()
