"""Tests for claude-agent/action.yml structure."""

import os
import unittest

import yaml

AGENT_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")
RESPOND_YML = os.path.join(os.path.dirname(__file__), "..", "..", "claude-respond", "action.yml")
SECURITY_AUDITOR = os.path.join(os.path.dirname(__file__), "..", "agents", "security-auditor.md")


class TestActionYml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(AGENT_YML) as f:
            cls.agent = yaml.safe_load(f)
        with open(RESPOND_YML) as f:
            cls.respond = yaml.safe_load(f)

    def test_is_composite_action(self):
        self.assertEqual(self.agent["runs"]["using"], "composite")

    def test_has_name_and_description(self):
        self.assertIn("name", self.agent)
        self.assertIn("description", self.agent)
        self.assertEqual(self.agent["name"], "Claude Agent")

    def test_has_required_inputs(self):
        """Agent should have the required agent-specific inputs."""
        required_inputs = ["agent_name"]
        for inp in required_inputs:
            self.assertIn(inp, self.agent["inputs"])
            self.assertTrue(
                self.agent["inputs"][inp].get("required", False),
                f"Input '{inp}' should be required"
            )

    def test_has_agent_configuration_inputs(self):
        """Agent should have agent-specific configuration inputs."""
        expected = ["max_issues", "issue_label", "dry_run"]
        for inp in expected:
            self.assertIn(inp, self.agent["inputs"], f"Missing agent input: {inp}")

    def test_default_values(self):
        """Test default values match design."""
        defaults = {
            "model": "claude-sonnet-4-20250514",
            "max_issues": "5",
            "dry_run": "false",
            "timeout_minutes": "60",
            "allowed_tools": "Bash(*),Read,Glob,Grep,WebFetch,WebSearch"
        }
        for inp, expected in defaults.items():
            actual = self.agent["inputs"][inp].get("default")
            self.assertEqual(
                actual, expected,
                f"Default for '{inp}': expected {expected!r}, got {actual!r}"
            )

    def test_auth_inputs_forwarded(self):
        """Auth inputs should be forwarded from claude-respond."""
        auth_inputs = [
            "claude_code_oauth_token", "anthropic_api_key", "github_token",
            "app_id", "app_private_key"
        ]
        for inp in auth_inputs:
            self.assertIn(inp, self.agent["inputs"], f"Missing auth input: {inp}")

    def test_advanced_inputs_forwarded(self):
        """Advanced inputs like settings, claude_args, disallowed_tools should be forwarded."""
        advanced_inputs = ["settings", "claude_args", "disallowed_tools"]
        for inp in advanced_inputs:
            self.assertIn(inp, self.agent["inputs"], f"Missing advanced input: {inp}")

    def test_orchestration_inputs_exist(self):
        """Orchestration inputs should be present for forwarding to claude-respond."""
        orchestration_inputs = [
            "pre_run", "tracking_comment", "checkout",
            "checkout_ref", "checkout_fetch_depth",
        ]
        for inp in orchestration_inputs:
            self.assertIn(inp, self.agent["inputs"], f"Missing orchestration input: {inp}")

    # --- Step structure ---

    def test_has_one_step(self):
        """Agent should have exactly one step (the respond wrapper)."""
        self.assertEqual(len(self.agent["runs"]["steps"]), 1)

    def test_respond_step_uses_claude_respond(self):
        """The step should use claude-respond action."""
        step = self.agent["runs"]["steps"][0]
        self.assertIn("claude-respond", step.get("uses", ""))

    def test_respond_step_has_correct_id(self):
        """The step should have id 'respond'."""
        step = self.agent["runs"]["steps"][0]
        self.assertEqual(step.get("id"), "respond")

    def test_compose_prompt_enabled(self):
        """compose_prompt should be set to true."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        self.assertEqual(with_block.get("compose_prompt"), "true")

    def test_extra_agents_path_set(self):
        """extra_agents_path should point to this action's agents directory."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        self.assertEqual(
            with_block.get("extra_agents_path"),
            "${{ github.action_path }}/agents"
        )

    def test_agent_name_forwarded(self):
        """agent_name input should be forwarded."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        self.assertEqual(
            with_block.get("agent_name"),
            "${{ inputs.agent_name }}"
        )

    def test_auth_inputs_forwarded_to_step(self):
        """Auth inputs should be forwarded to the respond step."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        auth_inputs = [
            "claude_code_oauth_token", "anthropic_api_key", "github_token",
            "app_id", "app_private_key"
        ]
        for inp in auth_inputs:
            self.assertIn(inp, with_block, f"Auth input '{inp}' not forwarded")
            self.assertEqual(
                with_block[inp],
                f"${{{{ inputs.{inp} }}}}",
                f"Auth input '{inp}' not properly referenced"
            )

    def test_configuration_inputs_forwarded_to_step(self):
        """Configuration inputs should be forwarded to the respond step."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        config_inputs = [
            "model", "max_turns", "timeout_minutes", "allowed_tools",
            "disallowed_tools", "claude_args", "settings"
        ]
        for inp in config_inputs:
            self.assertIn(inp, with_block, f"Config input '{inp}' not forwarded")
            self.assertEqual(
                with_block[inp],
                f"${{{{ inputs.{inp} }}}}",
                f"Config input '{inp}' not properly referenced"
            )

    def test_orchestration_inputs_forwarded_to_step(self):
        """Orchestration inputs should be forwarded to the respond step."""
        step = self.agent["runs"]["steps"][0]
        with_block = step.get("with", {})
        orchestration_inputs = [
            "pre_run", "tracking_comment", "checkout",
            "checkout_ref", "checkout_fetch_depth",
        ]
        for inp in orchestration_inputs:
            self.assertIn(inp, with_block, f"Orchestration input '{inp}' not forwarded")
            self.assertEqual(
                with_block[inp],
                f"${{{{ inputs.{inp} }}}}",
                f"Orchestration input '{inp}' not properly referenced"
            )

    # --- Prompt template ---

    def test_prompt_contains_guardrails(self):
        """Prompt should reference the operational guardrails."""
        step = self.agent["runs"]["steps"][0]
        prompt = step.get("with", {}).get("prompt", "")

        # Check that operational configuration is referenced
        self.assertIn("max_issues", prompt)
        self.assertIn("issue_label", prompt)
        self.assertIn("dry_run", prompt)

        # Check that operational rules are present
        self.assertIn("Do not create more than the max issues", prompt)
        self.assertIn("search for existing open issues", prompt)
        self.assertIn("If dry_run is true", prompt)

    def test_issue_label_default_logic(self):
        """issue_label should use format() to default to agent:<name>."""
        step = self.agent["runs"]["steps"][0]
        prompt = step.get("with", {}).get("prompt", "")
        # Should contain the default logic for issue_label
        self.assertIn("format('agent:{0}', inputs.agent_name)", prompt)

    # --- Outputs ---

    def test_expected_outputs_exist(self):
        """Agent should expose execution_file and session_id outputs."""
        expected = ["execution_file", "session_id"]
        for out in expected:
            self.assertIn(out, self.agent["outputs"], f"Missing output: {out}")

    def test_outputs_reference_respond_step(self):
        """Outputs should reference the respond step."""
        for name, output in self.agent["outputs"].items():
            self.assertIn(
                "steps.respond.outputs.",
                output["value"],
                f"Output '{name}' does not reference 'respond' step"
            )

    # --- Agent files ---

    def test_security_auditor_file_exists(self):
        """security-auditor.md should exist."""
        self.assertTrue(
            os.path.exists(SECURITY_AUDITOR),
            "security-auditor.md file not found"
        )

    def test_security_auditor_has_required_sections(self):
        """security-auditor.md should have the required sections."""
        with open(SECURITY_AUDITOR) as f:
            content = f.read()

        required_sections = [
            "# Agent: Security Auditor",
            "## Instruction Overrides",
            "## Workflow",
            "## Security Focus Areas",
            "## Scanning Strategy",
            "## Issue Creation",
            "## Constraints"
        ]

        for section in required_sections:
            self.assertIn(
                section, content,
                f"Missing required section: {section}"
            )

    def test_no_secrets_in_defaults(self):
        """No input defaults should contain secrets."""
        for name, inp in self.agent["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn("sk-", str(default), f"Input '{name}' default looks like a secret")
                self.assertNotIn("ghp_", str(default), f"Input '{name}' default looks like a GitHub token")

if __name__ == "__main__":
    unittest.main()