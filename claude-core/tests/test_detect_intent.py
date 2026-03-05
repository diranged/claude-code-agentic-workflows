"""Tests for claude-core/scripts/detect_intent.sh."""

import unittest

from helpers import run_script


class TestDetectIntent(unittest.TestCase):
    """Tests for detect_intent.sh routing logic."""

    def _run(self, comment_body="", trigger_label=""):
        """Run detect_intent.sh with COMMENT_BODY/TRIGGER_LABEL and return outputs dict."""
        rc, stdout, stderr, outputs = run_script(
            "detect_intent.sh",
            {"COMMENT_BODY": comment_body, "TRIGGER_LABEL": trigger_label},
        )
        self.assertEqual(rc, 0, f"Script failed: {stderr}")
        return outputs

    # --- label-based routing ---

    def test_label_implement(self):
        outputs = self._run(trigger_label="claude:implement")
        self.assertEqual(outputs["agent"], "agentic-developer")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_label_review(self):
        outputs = self._run(trigger_label="claude:review")
        self.assertEqual(outputs["agent"], "architect")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_label_design(self):
        outputs = self._run(trigger_label="claude:design")
        self.assertEqual(outputs["agent"], "agentic-designer")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_label_unknown_claude_prefix(self):
        outputs = self._run(trigger_label="claude:something-else")
        self.assertEqual(outputs["agent"], "agentic-designer")

    def test_label_takes_priority_over_comment(self):
        """Label routing should override comment body."""
        outputs = self._run(
            comment_body="@claude implement this",
            trigger_label="claude:review",
        )
        self.assertEqual(outputs["agent"], "architect")

    def test_non_claude_label_falls_through(self):
        """Non-claude: labels should fall through to auto mode."""
        outputs = self._run(
            comment_body="@claude do something",
            trigger_label="bug",
        )
        self.assertEqual(outputs["agent"], "auto")

    def test_empty_label_falls_through(self):
        """Empty label should fall through to auto mode."""
        outputs = self._run(comment_body="@claude check something")
        self.assertEqual(outputs["agent"], "auto")

    # --- comment-based routing (auto mode) ---

    def test_comment_defaults_to_auto(self):
        """Any @claude comment should route to auto mode."""
        outputs = self._run("@claude rebase this")
        self.assertEqual(outputs["agent"], "auto")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_empty_body_defaults_to_auto(self):
        outputs = self._run("")
        self.assertEqual(outputs["agent"], "auto")

    def test_any_comment_goes_to_auto(self):
        """Claude self-selects the right agent — no keyword matching."""
        for comment in [
            "@claude review the architecture",
            "@claude fix the tests",
            "@claude check for dead code",
            "@claude do something random",
            "@claude",
        ]:
            with self.subTest(comment=comment):
                outputs = self._run(comment)
                self.assertEqual(outputs["agent"], "auto")


if __name__ == "__main__":
    unittest.main()
