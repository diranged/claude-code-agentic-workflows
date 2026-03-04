"""Tests for scripts/validate_inputs.sh."""

import os
import tempfile
import unittest

from helpers import run_script


class TestValidateInputs(unittest.TestCase):
    def setUp(self):
        """Set up temporary workspace directory for agent file tests."""
        self.temp_workspace = tempfile.mkdtemp()
        self.temp_action_path = tempfile.mkdtemp()

        # Create test agent directories
        os.makedirs(os.path.join(self.temp_workspace, ".github", "claude-agents"))
        os.makedirs(os.path.join(self.temp_action_path, "agents"))

        # Create a test agent file in the builtin location
        with open(os.path.join(self.temp_action_path, "agents", "agentic-designer.md"), "w") as f:
            f.write("# Test agent\n")

    def tearDown(self):
        """Clean up temp directories."""
        import shutil
        shutil.rmtree(self.temp_workspace)
        shutil.rmtree(self.temp_action_path)

    # Claude Authentication Tests
    def test_fails_when_no_claude_auth(self):
        rc, stdout, _, _ = run_script("validate_inputs.sh")
        self.assertEqual(rc, 1)
        self.assertIn("Either claude_code_oauth_token or anthropic_api_key must be provided", stdout)

    def test_succeeds_with_oauth_token(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("OAuth token", stdout)

    def test_succeeds_with_api_key(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"API_KEY": "sk-123"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("API key", stdout)

    # App Credentials Tests
    def test_fails_app_id_without_private_key(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "APP_ID": "123"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("app_id and app_private_key must both be provided together", stdout)

    def test_fails_private_key_without_app_id(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "APP_PRIVATE_KEY": "pem"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("app_id and app_private_key must both be provided together", stdout)

    def test_succeeds_app_credentials_paired(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "APP_ID": "123", "APP_PRIVATE_KEY": "pem"},
        )
        self.assertEqual(rc, 0)

    # Timeout Tests
    def test_fails_timeout_zero(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "0"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '0'", stdout)

    def test_fails_timeout_negative(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "-5"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '-5'", stdout)

    def test_fails_timeout_non_numeric(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "abc"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got 'abc'", stdout)

    def test_fails_timeout_decimal(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "1.5"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '1.5'", stdout)

    def test_succeeds_timeout_valid(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "30"},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_timeout_empty(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": ""},
        )
        self.assertEqual(rc, 0)

    def test_fails_timeout_whitespace(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "  "},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '  '", stdout)

    # Compose/Agent Tests
    def test_fails_compose_without_agent(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "COMPOSE_PROMPT": "true", "AGENT_NAME": ""},
        )
        self.assertEqual(rc, 1)
        self.assertIn("agent_name is required when compose_prompt is true", stdout)

    def test_fails_agent_not_found(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {
                "OAUTH_TOKEN": "tok",
                "COMPOSE_PROMPT": "true",
                "AGENT_NAME": "nonexistent",
                "ACTION_PATH": self.temp_action_path,
                "WORKSPACE_PATH": self.temp_workspace,
            },
        )
        self.assertEqual(rc, 1)
        self.assertIn("Agent 'nonexistent' not found in agents/ or .github/claude-agents/", stdout)

    def test_succeeds_compose_with_valid_agent(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {
                "OAUTH_TOKEN": "tok",
                "COMPOSE_PROMPT": "true",
                "AGENT_NAME": "agentic-designer",
                "ACTION_PATH": self.temp_action_path,
                "WORKSPACE_PATH": self.temp_workspace,
            },
        )
        self.assertEqual(rc, 0)

    def test_succeeds_no_compose(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "COMPOSE_PROMPT": "false"},
        )
        self.assertEqual(rc, 0)

    # Comprehensive Tests
    def test_valid_inputs_all_set(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {
                "OAUTH_TOKEN": "tok",
                "APP_ID": "123",
                "APP_PRIVATE_KEY": "pem",
                "TIMEOUT_MINUTES": "30",
                "COMPOSE_PROMPT": "true",
                "AGENT_NAME": "agentic-designer",
                "ACTION_PATH": self.temp_action_path,
                "WORKSPACE_PATH": self.temp_workspace,
            },
        )
        self.assertEqual(rc, 0)

    def test_oauth_notice_message(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("OAuth token", stdout)

    def test_api_key_notice_message(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"API_KEY": "sk-123"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("API key", stdout)


if __name__ == "__main__":
    unittest.main()