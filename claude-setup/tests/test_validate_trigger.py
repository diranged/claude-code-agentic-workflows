"""Tests for claude-setup/scripts/validate_trigger.sh."""

import unittest

from helpers import run_script


class TestValidateTrigger(unittest.TestCase):
    """Tests for validate_trigger.sh trigger validation logic."""

    def _run(self, **env):
        """Run validate_trigger.sh with the given env vars."""
        rc, stdout, stderr, outputs = run_script("validate_trigger.sh", env)
        self.assertEqual(rc, 0, f"Script failed: {stderr}")
        return outputs

    # --- Assignment events ---

    def test_assignment_matching_assignee(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="assigned",
            ASSIGNEE_LOGIN="claude",
            ASSIGNEE_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_assignment_non_matching_assignee(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="assigned",
            ASSIGNEE_LOGIN="someone-else",
            ASSIGNEE_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_assignment_no_trigger_configured(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="assigned",
            ASSIGNEE_LOGIN="claude",
            ASSIGNEE_TRIGGER="",
        )
        self.assertEqual(outputs["skip"], "true")

    # --- Label events ---

    def test_label_matching_prefix(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="claude:design",
            LABEL_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_label_implement(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="claude:implement",
            LABEL_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_label_non_matching_prefix(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="bug",
            LABEL_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_label_modifier_auto_advance(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="claude:auto_advance",
            LABEL_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_label_modifier_queued(self):
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="claude:queued",
            LABEL_TRIGGER="claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_label_no_trigger_configured(self):
        """When no label_trigger is set, label events should not be skipped."""
        outputs = self._run(
            EVENT_NAME="issues",
            EVENT_ACTION="labeled",
            LABEL_NAME="claude:design",
            LABEL_TRIGGER="",
        )
        self.assertEqual(outputs["skip"], "false")

    # --- Comment events ---

    def test_comment_with_trigger_phrase(self):
        outputs = self._run(
            EVENT_NAME="issue_comment",
            COMMENT_BODY="Hey @claude can you help?",
            TRIGGER_PHRASE="@claude",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_comment_without_trigger_phrase(self):
        outputs = self._run(
            EVENT_NAME="issue_comment",
            COMMENT_BODY="This is a regular comment",
            TRIGGER_PHRASE="@claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_pr_review_comment_with_trigger(self):
        outputs = self._run(
            EVENT_NAME="pull_request_review_comment",
            COMMENT_BODY="@claude review this change",
            TRIGGER_PHRASE="@claude",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_pr_review_comment_without_trigger(self):
        outputs = self._run(
            EVENT_NAME="pull_request_review_comment",
            COMMENT_BODY="Looks good to me",
            TRIGGER_PHRASE="@claude",
        )
        self.assertEqual(outputs["skip"], "true")

    def test_comment_no_trigger_phrase_configured(self):
        """When no trigger_phrase is set, any comment should pass."""
        outputs = self._run(
            EVENT_NAME="issue_comment",
            COMMENT_BODY="Any comment",
            TRIGGER_PHRASE="",
        )
        self.assertEqual(outputs["skip"], "false")

    # --- Default behavior ---

    def test_unknown_event_does_not_skip(self):
        outputs = self._run(
            EVENT_NAME="push",
        )
        self.assertEqual(outputs["skip"], "false")

    def test_empty_event_does_not_skip(self):
        outputs = self._run()
        self.assertEqual(outputs["skip"], "false")


if __name__ == "__main__":
    unittest.main()
