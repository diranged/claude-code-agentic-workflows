"""Tests for claude-engineer/action.yml structure."""

import os
import unittest

import yaml

ENGINEER_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")
RESPOND_YML = os.path.join(
    os.path.dirname(__file__), "..", "..", "claude-respond", "action.yml"
)


class TestActionYml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ENGINEER_YML) as f:
            cls.engineer = yaml.safe_load(f)
        with open(RESPOND_YML) as f:
            cls.respond = yaml.safe_load(f)

    def test_is_composite_action(self):
        self.assertEqual(self.engineer["runs"]["using"], "composite")

    def test_has_name_and_description(self):
        self.assertIn("name", self.engineer)
        self.assertIn("description", self.engineer)

    # --- Required inputs ---

    def test_agent_name_required(self):
        self.assertTrue(self.engineer["inputs"]["agent_name"].get("required"))

    def test_dashboard_label_required(self):
        self.assertTrue(self.engineer["inputs"]["dashboard_label"].get("required"))

    def test_task_label_required(self):
        self.assertTrue(self.engineer["inputs"]["task_label"].get("required"))

    # --- Auth inputs forwarded ---

    def test_has_oauth_input(self):
        self.assertIn("claude_code_oauth_token", self.engineer["inputs"])

    def test_has_api_key_input(self):
        self.assertIn("anthropic_api_key", self.engineer["inputs"])

    def test_has_github_token_input(self):
        self.assertIn("github_token", self.engineer["inputs"])

    # --- Engineer-specific inputs ---

    def test_has_delegation_label_with_default(self):
        inp = self.engineer["inputs"]["delegation_label"]
        self.assertEqual(inp.get("default"), "claude:implement")

    def test_has_rotation_days_with_default(self):
        inp = self.engineer["inputs"]["rotation_days"]
        self.assertEqual(inp.get("default"), "7")

    def test_has_force_rotation_with_default(self):
        inp = self.engineer["inputs"]["force_rotation"]
        self.assertEqual(inp.get("default"), "false")

    def test_has_allowed_tools_with_default(self):
        inp = self.engineer["inputs"]["allowed_tools"]
        self.assertIn("Bash", inp.get("default", ""))
        self.assertNotIn("Edit", inp.get("default", ""))
        self.assertNotIn("Write", inp.get("default", ""))

    # --- Step structure ---

    def test_has_one_step(self):
        self.assertEqual(len(self.engineer["runs"]["steps"]), 1)

    def test_step_uses_claude_respond(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertIn("claude-respond", step.get("uses", ""))

    def test_step_sets_compose_prompt_true(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertEqual(step["with"]["compose_prompt"], "true")

    def test_step_forwards_agent_name(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertIn("inputs.agent_name", step["with"]["agent_name"])

    def test_step_forwards_model(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertIn("inputs.model", step["with"]["model"])

    def test_prompt_contains_dashboard_config(self):
        """The prompt should contain dashboard configuration placeholders."""
        step = self.engineer["runs"]["steps"][0]
        prompt = step["with"]["prompt"]
        self.assertIn("inputs.dashboard_label", prompt)
        self.assertIn("inputs.task_label", prompt)
        self.assertIn("inputs.delegation_label", prompt)
        self.assertIn("inputs.rotation_days", prompt)
        self.assertIn("inputs.force_rotation", prompt)

    def test_no_issue_comment_id_passed(self):
        """Engineer should not pass issue_comment_id — it manages its own."""
        step = self.engineer["runs"]["steps"][0]
        self.assertNotIn("issue_comment_id", step.get("with", {}))

    # --- Outputs ---

    def test_has_execution_file_output(self):
        self.assertIn("execution_file", self.engineer["outputs"])

    def test_has_session_id_output(self):
        self.assertIn("session_id", self.engineer["outputs"])

    # --- No secrets in defaults ---

    def test_no_secrets_in_defaults(self):
        for name, inp in self.engineer["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn(
                    "sk-", str(default), f"Input '{name}' default looks like a secret"
                )


if __name__ == "__main__":
    unittest.main()
