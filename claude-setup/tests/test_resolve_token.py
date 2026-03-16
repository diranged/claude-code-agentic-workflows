"""Tests for claude-setup/scripts/resolve_token.sh."""

import unittest

from helpers import run_script


class TestResolveToken(unittest.TestCase):
    """Tests for resolve_token.sh token resolution logic."""

    def _run(self, **env):
        rc, stdout, stderr, outputs = run_script("resolve_token.sh", env)
        self.assertEqual(rc, 0, f"Script failed: {stderr}")
        return outputs

    def test_app_token_takes_priority(self):
        outputs = self._run(APP_TOKEN="app-tok-123", EXPLICIT_TOKEN="explicit-tok")
        self.assertEqual(outputs["token"], "app-tok-123")

    def test_explicit_token_when_no_app_token(self):
        outputs = self._run(EXPLICIT_TOKEN="explicit-tok")
        self.assertEqual(outputs["token"], "explicit-tok")

    def test_empty_when_no_tokens(self):
        outputs = self._run()
        self.assertEqual(outputs["token"], "")


if __name__ == "__main__":
    unittest.main()
