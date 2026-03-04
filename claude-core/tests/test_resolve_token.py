"""Tests for scripts/resolve_token.sh."""

import unittest

from helpers import run_script


class TestResolveToken(unittest.TestCase):
    def test_app_token_takes_priority(self):
        rc, stdout, _, outputs = run_script(
            "resolve_token.sh",
            {"APP_TOKEN": "ghs_app123", "EXPLICIT_TOKEN": "ghp_explicit456"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "ghs_app123")
        self.assertIn("App token", stdout)

    def test_falls_back_to_explicit_token(self):
        rc, stdout, _, outputs = run_script(
            "resolve_token.sh",
            {"EXPLICIT_TOKEN": "ghp_explicit456"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "ghp_explicit456")
        self.assertIn("explicitly provided", stdout)

    def test_empty_when_neither_provided(self):
        rc, stdout, _, outputs = run_script("resolve_token.sh")
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "")
        self.assertIn("default GITHUB_TOKEN", stdout)

    def test_empty_app_token_treated_as_absent(self):
        rc, _, _, outputs = run_script(
            "resolve_token.sh",
            {"APP_TOKEN": "", "EXPLICIT_TOKEN": "ghp_explicit456"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "ghp_explicit456")

    def test_empty_both_tokens(self):
        rc, _, _, outputs = run_script(
            "resolve_token.sh",
            {"APP_TOKEN": "", "EXPLICIT_TOKEN": ""},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "")

    def test_only_app_token(self):
        rc, _, _, outputs = run_script(
            "resolve_token.sh",
            {"APP_TOKEN": "ghs_only"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["token"], "ghs_only")


if __name__ == "__main__":
    unittest.main()
