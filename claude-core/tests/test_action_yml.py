"""Tests for claude-core/action.yml structure."""

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

    def test_expected_inputs_exist(self):
        expected = [
            "claude_code_oauth_token",
            "anthropic_api_key",
            "github_token",
            "app_id",
            "app_private_key",
            "trigger_phrase",
            "assignee_trigger",
            "label_trigger",
            "model",
            "max_turns",
            "timeout_minutes",
            "allowed_tools",
            "disallowed_tools",
            "claude_args",
            "additional_permissions",
            "settings",
            "prompt",
            "agent_name",
            "compose_prompt",
            "issue_comment_id",
            "display_report",
        ]
        for inp in expected:
            self.assertIn(inp, self.action["inputs"], f"Missing input: {inp}")

    def test_expected_outputs_exist(self):
        expected = ["execution_file", "branch_name", "session_id"]
        for out in expected:
            self.assertIn(out, self.action["outputs"], f"Missing output: {out}")

    def test_default_values(self):
        inputs = self.action["inputs"]
        self.assertEqual(inputs["trigger_phrase"]["default"], "@claude")
        self.assertEqual(inputs["timeout_minutes"]["default"], "60")
        self.assertEqual(inputs["compose_prompt"]["default"], "false")
        self.assertEqual(inputs["display_report"]["default"], "true")

    def test_all_steps_use_bash_shell(self):
        for step in self.action["runs"]["steps"]:
            if "run" in step:
                self.assertEqual(
                    step.get("shell"),
                    "bash",
                    f"Step '{step.get('name', '?')}' does not use bash shell",
                )

    def test_script_steps_reference_external_files(self):
        """Steps with run: should reference scripts/ directory."""
        for step in self.action["runs"]["steps"]:
            if "run" in step:
                self.assertIn(
                    "scripts/",
                    step["run"],
                    f"Step '{step.get('name', '?')}' does not reference a script file",
                )

    def test_outputs_reference_correct_step_ids(self):
        outputs = self.action["outputs"]
        for name, output in outputs.items():
            self.assertIn(
                "steps.claude.outputs.",
                output["value"],
                f"Output '{name}' does not reference 'claude' step",
            )

    def test_no_secrets_in_defaults(self):
        """No default values should contain secret-like strings."""
        for name, inp in self.action["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn("sk-", str(default), f"Input '{name}' default looks like a secret")
                self.assertNotIn("ghp_", str(default), f"Input '{name}' default looks like a secret")
                self.assertNotIn("ghs_", str(default), f"Input '{name}' default looks like a secret")

    def test_no_required_inputs_without_defaults(self):
        """Inputs marked required should not have defaults (and vice versa is fine)."""
        for name, inp in self.action["inputs"].items():
            if inp.get("required") is True:
                self.assertNotIn(
                    "default",
                    inp,
                    f"Input '{name}' is required but has a default",
                )

    def test_step_count(self):
        """Should have 7 steps: validate-inputs, app-token, resolve-token, build-args, build-prompt, compose-prompt, claude."""
        self.assertEqual(len(self.action["runs"]["steps"]), 7)

    def test_first_step_validates_inputs(self):
        """First step should use validate_inputs.sh script."""
        first_step = self.action["runs"]["steps"][0]
        self.assertEqual(first_step["name"], "Validate Inputs")
        self.assertIn("validate_inputs.sh", first_step["run"])


if __name__ == "__main__":
    unittest.main()
