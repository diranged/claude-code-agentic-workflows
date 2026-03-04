"""Tests for scripts/validate_claude_auth.sh."""

import unittest

from helpers import run_script


class TestValidateClaudeAuth(unittest.TestCase):
    def test_fails_when_both_missing(self):
        rc, stdout, _, _ = run_script("validate_claude_auth.sh")
        self.assertEqual(rc, 1)
        self.assertIn("No Claude authentication provided", stdout)

    def test_fails_when_both_empty(self):
        rc, stdout, _, _ = run_script(
            "validate_claude_auth.sh",
            {"OAUTH_TOKEN": "", "API_KEY": ""},
        )
        self.assertEqual(rc, 1)
        self.assertIn("No Claude authentication provided", stdout)

    def test_error_message_mentions_both_inputs(self):
        rc, stdout, _, _ = run_script("validate_claude_auth.sh")
        self.assertIn("claude_code_oauth_token", stdout)
        self.assertIn("anthropic_api_key", stdout)

    def test_succeeds_with_oauth_only(self):
        rc, stdout, _, _ = run_script(
            "validate_claude_auth.sh",
            {"OAUTH_TOKEN": "oauth-token-123"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("OAuth token", stdout)

    def test_succeeds_with_api_key_only(self):
        rc, stdout, _, _ = run_script(
            "validate_claude_auth.sh",
            {"API_KEY": "sk-ant-123"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("API key", stdout)

    def test_succeeds_with_both(self):
        rc, stdout, _, _ = run_script(
            "validate_claude_auth.sh",
            {"OAUTH_TOKEN": "oauth-token-123", "API_KEY": "sk-ant-123"},
        )
        self.assertEqual(rc, 0)
        # When both provided, oauth takes priority in messaging
        self.assertIn("OAuth token", stdout)


if __name__ == "__main__":
    unittest.main()
