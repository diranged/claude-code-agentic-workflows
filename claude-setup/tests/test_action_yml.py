"""Tests for claude-setup/action.yml structure."""

import os
import unittest

import yaml

ACTION_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")


class TestActionYml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ACTION_YML) as f:
            cls.action = yaml.safe_load(f)

    def test_is_composite_action(self):
        self.assertEqual(self.action["runs"]["using"], "composite")

    def test_has_name_and_description(self):
        self.assertIn("name", self.action)
        self.assertIn("description", self.action)

    # --- Inputs ---

    def test_expected_inputs_exist(self):
        expected = [
            "trigger_phrase",
            "assignee_trigger",
            "label_trigger",
            "tracking_comment",
            "reaction_emoji",
            "checkout",
            "checkout_ref",
            "checkout_fetch_depth",
            "pre_run",
            "github_token",
            "app_id",
            "app_private_key",
        ]
        for inp in expected:
            self.assertIn(inp, self.action["inputs"], f"Missing input: {inp}")

    def test_no_claude_specific_inputs(self):
        """claude-setup should NOT have Claude execution inputs."""
        forbidden = [
            "claude_code_oauth_token",
            "anthropic_api_key",
            "model",
            "max_turns",
            "allowed_tools",
            "compose_prompt",
            "agent_name",
            "prompt",
        ]
        for inp in forbidden:
            self.assertNotIn(
                inp,
                self.action.get("inputs", {}),
                f"claude-setup should not have Claude input '{inp}'",
            )

    def test_default_values(self):
        defaults = {
            "trigger_phrase": "@claude",
            "tracking_comment": "true",
            "reaction_emoji": "rocket",
            "checkout": "true",
            "checkout_ref": "",
            "checkout_fetch_depth": "1",
            "pre_run": "",
        }
        for inp, expected in defaults.items():
            actual = self.action["inputs"][inp].get("default")
            self.assertEqual(
                actual,
                expected,
                f"Default mismatch for '{inp}': {actual!r} != {expected!r}",
            )

    # --- Outputs ---

    def test_expected_outputs_exist(self):
        expected = ["skip", "comment_id", "issue_number", "github_token"]
        for out in expected:
            self.assertIn(out, self.action["outputs"], f"Missing output: {out}")

    # --- Step structure ---

    def test_has_validate_trigger_step(self):
        step = self._get_step_by_id("validate")
        self.assertIsNotNone(step, "No step with id 'validate'")
        self.assertIn("validate_trigger.sh", step.get("run", ""))

    def test_has_app_token_step(self):
        step = self._get_step_by_id("app-token")
        self.assertIsNotNone(step, "No step with id 'app-token'")
        self.assertIn("create-github-app-token", step.get("uses", ""))

    def test_app_token_step_is_conditional(self):
        step = self._get_step_by_id("app-token")
        self.assertIn("app_id", step.get("if", ""))
        self.assertIn("app_private_key", step.get("if", ""))

    def test_has_resolve_token_step(self):
        step = self._get_step_by_id("resolve-token")
        self.assertIsNotNone(step, "No step with id 'resolve-token'")
        self.assertIn("resolve_token.sh", step.get("run", ""))

    def test_has_tracking_step(self):
        step = self._get_step_by_id("tracking")
        self.assertIsNotNone(step, "No step with id 'tracking'")
        self.assertIn("setup_tracking.sh", step.get("run", ""))

    def test_has_checkout_step(self):
        checkout_steps = [
            s for s in self.action["runs"]["steps"] if "checkout" in s.get("uses", "")
        ]
        self.assertEqual(len(checkout_steps), 1, "Expected exactly one checkout step")

    def test_checkout_step_is_conditional(self):
        checkout_steps = [
            s for s in self.action["runs"]["steps"] if "checkout" in s.get("uses", "")
        ]
        step = checkout_steps[0]
        self.assertIn("checkout", step.get("if", ""))
        self.assertIn("skip", step.get("if", ""))

    def test_has_pre_run_step(self):
        pre_run_steps = [
            s
            for s in self.action["runs"]["steps"]
            if s.get("name", "").lower() == "pre-run setup"
        ]
        self.assertEqual(len(pre_run_steps), 1, "Expected exactly one pre-run step")

    def test_pre_run_step_is_conditional(self):
        pre_run_steps = [
            s
            for s in self.action["runs"]["steps"]
            if s.get("name", "").lower() == "pre-run setup"
        ]
        step = pre_run_steps[0]
        self.assertIn("pre_run", step.get("if", ""))

    def test_steps_after_validate_check_skip(self):
        """All steps after validate should check skip != 'true'."""
        found_validate = False
        for step in self.action["runs"]["steps"]:
            if step.get("id") == "validate":
                found_validate = True
                continue
            if found_validate and step.get("if"):
                self.assertIn(
                    "skip",
                    step["if"],
                    f"Step '{step.get('name', '?')}' doesn't check skip condition",
                )

    # --- Helper ---

    def _get_step_by_id(self, step_id):
        for step in self.action["runs"]["steps"]:
            if step.get("id") == step_id:
                return step
        return None


if __name__ == "__main__":
    unittest.main()
