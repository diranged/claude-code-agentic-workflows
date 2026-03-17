"""Tests for claude-engineer/action.yml structure."""

import os
import unittest

import yaml

ENGINEER_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")
RESPOND_YML = os.path.join(os.path.dirname(__file__), "..", "..", "claude-respond", "action.yml")
AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agents")
INSTRUCTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "instructions")


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
        self.assertEqual(self.engineer["name"], "Claude Engineer")

    # --- Inputs ---

    def test_has_required_inputs(self):
        required = ["agent_name", "dashboard_label", "task_label"]
        for inp in required:
            self.assertIn(inp, self.engineer["inputs"])
            self.assertTrue(
                self.engineer["inputs"][inp].get("required", False),
                f"Input '{inp}' should be required",
            )

    def test_has_engineer_configuration_inputs(self):
        expected = [
            "dashboard_label", "task_label", "delegation_label",
            "max_implementations", "rotation_days", "force_rotation",
        ]
        for inp in expected:
            self.assertIn(inp, self.engineer["inputs"], f"Missing engineer input: {inp}")

    def test_has_auth_inputs(self):
        auth = ["claude_code_oauth_token", "anthropic_api_key", "github_token",
                "app_id", "app_private_key"]
        for inp in auth:
            self.assertIn(inp, self.engineer["inputs"], f"Missing auth input: {inp}")

    def test_has_orchestration_inputs(self):
        orchestration = ["pre_run", "tracking_comment", "checkout",
                         "checkout_ref", "checkout_fetch_depth"]
        for inp in orchestration:
            self.assertIn(inp, self.engineer["inputs"], f"Missing orchestration input: {inp}")

    def test_default_values(self):
        defaults = {
            "model": "claude-sonnet-4-20250514",
            "delegation_label": "claude:design",
            "max_implementations": "2",
            "rotation_days": "7",
            "force_rotation": "false",
            "timeout_minutes": "60",
            "allowed_tools": "Bash(*),Read,Glob,Grep,WebFetch,WebSearch",
            "checkout_fetch_depth": "0",
            "pre_run": "",
            "tracking_comment": "true",
            "checkout": "true",
        }
        for inp, expected in defaults.items():
            actual = self.engineer["inputs"][inp].get("default")
            self.assertEqual(
                actual, expected,
                f"Default for '{inp}': expected {expected!r}, got {actual!r}",
            )

    # --- Step structure ---

    def test_has_one_step(self):
        self.assertEqual(len(self.engineer["runs"]["steps"]), 1)

    def test_respond_step_uses_claude_respond(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertIn("claude-respond", step.get("uses", ""))

    def test_respond_step_has_correct_id(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertEqual(step.get("id"), "respond")

    def test_compose_prompt_enabled(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertEqual(step["with"].get("compose_prompt"), "true")

    def test_extra_agents_path_set(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertEqual(
            step["with"].get("extra_agents_path"),
            "${{ github.action_path }}/agents",
        )

    def test_extra_instructions_path_set(self):
        step = self.engineer["runs"]["steps"][0]
        self.assertEqual(
            step["with"].get("extra_instructions_path"),
            "${{ github.action_path }}/instructions",
        )

    def test_auth_inputs_forwarded_to_step(self):
        step = self.engineer["runs"]["steps"][0]
        with_block = step.get("with", {})
        for inp in ["claude_code_oauth_token", "anthropic_api_key", "github_token",
                     "app_id", "app_private_key"]:
            self.assertIn(inp, with_block, f"Auth input '{inp}' not forwarded")
            self.assertEqual(
                with_block[inp], f"${{{{ inputs.{inp} }}}}",
                f"Auth input '{inp}' not properly referenced",
            )

    def test_orchestration_inputs_forwarded_to_step(self):
        step = self.engineer["runs"]["steps"][0]
        with_block = step.get("with", {})
        for inp in ["pre_run", "tracking_comment", "checkout",
                     "checkout_ref", "checkout_fetch_depth"]:
            self.assertIn(inp, with_block, f"Orchestration input '{inp}' not forwarded")
            self.assertEqual(
                with_block[inp], f"${{{{ inputs.{inp} }}}}",
                f"Orchestration input '{inp}' not properly referenced",
            )

    def test_prompt_contains_dashboard_config(self):
        step = self.engineer["runs"]["steps"][0]
        prompt = step["with"].get("prompt", "")
        for key in ["dashboard_label", "task_label", "delegation_label",
                     "max_implementations", "rotation_days", "force_rotation"]:
            self.assertIn(key, prompt, f"Prompt missing config key: {key}")

    # --- Outputs ---

    def test_expected_outputs_exist(self):
        for out in ["execution_file", "session_id"]:
            self.assertIn(out, self.engineer["outputs"], f"Missing output: {out}")

    def test_outputs_reference_respond_step(self):
        for name, output in self.engineer["outputs"].items():
            self.assertIn("steps.respond.outputs.", output["value"])

    # --- Agent files ---

    def test_agent_files_exist(self):
        expected_agents = ["docs-engineer.md", "code-janitor.md", "security-engineer.md"]
        for agent in expected_agents:
            path = os.path.join(AGENTS_DIR, agent)
            self.assertTrue(os.path.exists(path), f"Agent file missing: {agent}")

    def test_instructions_file_exists(self):
        path = os.path.join(INSTRUCTIONS_DIR, "00-engineer-base.md")
        self.assertTrue(os.path.exists(path), "Base instruction file missing")

    def test_no_secrets_in_defaults(self):
        for name, inp in self.engineer["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn("sk-", str(default))
                self.assertNotIn("ghp_", str(default))


if __name__ == "__main__":
    unittest.main()
