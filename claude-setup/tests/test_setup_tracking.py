"""Tests for claude-setup/scripts/setup_tracking.sh.

These tests validate the script's output logic without making real API calls.
The script calls gh api which would fail without a valid token, so we only test
the cases where the script exits early (no issue number, tracking disabled).
Full integration testing of reaction/comment creation is done via the
integration test repo.
"""

import unittest

from helpers import run_script


class TestSetupTracking(unittest.TestCase):
    """Tests for setup_tracking.sh output logic."""

    def _run(self, **env):
        """Run setup_tracking.sh with the given env vars."""
        return run_script("setup_tracking.sh", env)

    def test_no_issue_number_outputs_empty(self):
        """When no issue number is available, outputs should be empty."""
        rc, stdout, stderr, outputs = self._run(
            ISSUE_NUMBER="",
            CREATE_TRACKING_COMMENT="true",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs.get("issue_number", ""), "")
        self.assertEqual(outputs.get("comment_id", ""), "")

    def test_tracking_disabled_outputs_issue_number(self):
        """When tracking is disabled, should output issue_number but empty comment_id."""
        rc, stdout, stderr, outputs = self._run(
            ISSUE_NUMBER="42",
            CREATE_TRACKING_COMMENT="false",
            EVENT_NAME="issues",
            COMMENT_ID="",
            REACTION_EMOJI="",
            GITHUB_REPOSITORY="test/repo",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["issue_number"], "42")
        self.assertEqual(outputs.get("comment_id", ""), "")

    def test_issue_number_passed_through(self):
        """Issue number should always be passed through when available."""
        rc, stdout, stderr, outputs = self._run(
            ISSUE_NUMBER="123",
            CREATE_TRACKING_COMMENT="false",
            EVENT_NAME="issues",
            COMMENT_ID="",
            REACTION_EMOJI="",
            GITHUB_REPOSITORY="test/repo",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["issue_number"], "123")


if __name__ == "__main__":
    unittest.main()
