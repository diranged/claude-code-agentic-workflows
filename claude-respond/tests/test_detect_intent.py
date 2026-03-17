"""Tests for claude-respond/scripts/detect_intent.sh."""

import unittest

from helpers import run_script


class TestDetectIntent(unittest.TestCase):
    """Tests for detect_intent.sh label routing logic."""

    def _run(self, label_name="", default_agent="", default_model=""):
        rc, stdout, stderr, outputs = run_script(
            "detect_intent.sh",
            {
                "LABEL_NAME": label_name,
                "DEFAULT_AGENT": default_agent,
                "DEFAULT_MODEL": default_model,
            },
        )
        self.assertEqual(rc, 0, f"Script failed: {stderr}")
        return outputs

    # --- Known pipeline labels ---

    def test_label_implement(self):
        outputs = self._run(label_name="claude:implement")
        self.assertEqual(outputs["agent"], "agentic-developer")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_label_design(self):
        outputs = self._run(label_name="claude:design")
        self.assertEqual(outputs["agent"], "agentic-designer")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_label_review(self):
        outputs = self._run(label_name="claude:review")
        self.assertEqual(outputs["agent"], "architect")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    # --- Modifier labels ---

    def test_modifier_auto_advance(self):
        outputs = self._run(label_name="claude:auto_advance")
        self.assertEqual(outputs["skip"], "true")
        self.assertNotIn("agent", outputs)

    def test_modifier_queued(self):
        outputs = self._run(label_name="claude:queued")
        self.assertEqual(outputs["skip"], "true")
        self.assertNotIn("agent", outputs)

    # --- Unknown claude: labels ---

    def test_unknown_claude_label_uses_default_agent(self):
        outputs = self._run(
            label_name="claude:something-else",
            default_agent="my-custom-agent",
            default_model="claude-sonnet-4-20250514",
        )
        self.assertEqual(outputs["agent"], "my-custom-agent")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_unknown_claude_label_fallback_defaults(self):
        outputs = self._run(label_name="claude:unknown")
        self.assertEqual(outputs["agent"], "agentic-designer")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    # --- Non-claude labels ---

    def test_non_claude_label_uses_defaults(self):
        outputs = self._run(
            label_name="bug",
            default_agent="my-agent",
            default_model="my-model",
        )
        self.assertEqual(outputs["agent"], "my-agent")
        self.assertEqual(outputs["model"], "my-model")

    def test_empty_label_uses_defaults(self):
        outputs = self._run(label_name="")
        self.assertEqual(outputs["agent"], "agentic-designer")


if __name__ == "__main__":
    unittest.main()
