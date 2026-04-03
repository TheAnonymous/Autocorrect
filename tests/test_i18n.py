import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from i18n import tr, TRANSLATIONS


class TestI18nKeysExist(unittest.TestCase):
    def test_app_name_exists(self):
        self.assertIn("app_name", TRANSLATIONS)

    def test_error_keys_exist(self):
        self.assertIn("err_ollama_unreachable", TRANSLATIONS)
        self.assertIn("err_timeout", TRANSLATIONS)

    def test_status_keys_exist(self):
        self.assertIn("status_running", TRANSLATIONS)
        self.assertIn("status_stopped", TRANSLATIONS)


class TestTrFunction(unittest.TestCase):
    def test_returns_string(self):
        result = tr("app_name")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_with_args(self):
        result = tr("err_cmd_missing", "curl")
        self.assertIn("curl", result)

    def test_unknown_key_returns_key(self):
        self.assertEqual(tr("nonexistent_key"), "nonexistent_key")

    def test_format_multiple_args(self):
        result = tr("model_changed", "gemma4:e2b")
        self.assertIn("gemma4:e2b", result)


class TestTranslationsConsistency(unittest.TestCase):
    def test_all_keys_have_two_entries(self):
        for key, value in TRANSLATIONS.items():
            self.assertEqual(len(value), 2, f"Key '{key}' should have exactly 2 translations")

    def test_no_empty_translations(self):
        for key, value in TRANSLATIONS.items():
            self.assertTrue(value[0], f"German translation for '{key}' is empty")
            self.assertTrue(value[1], f"English translation for '{key}' is empty")


if __name__ == "__main__":
    unittest.main()
