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

        # Create scripts directory and copy necessary scripts
        scripts_dir = os.path.join(self.temp_action_path, "scripts")
        os.makedirs(scripts_dir)

        # Copy validate_oauth_token.sh to temp directory
        import shutil
        real_scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        oauth_script = os.path.join(real_scripts_dir, "validate_oauth_token.sh")
        if os.path.exists(oauth_script):
            shutil.copy2(oauth_script, os.path.join(scripts_dir, "validate_oauth_token.sh"))

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
            {"OAUTH_TOKEN": "tok", "ACTION_PATH": self.temp_action_path},
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
            {"OAUTH_TOKEN": "tok", "APP_ID": "123", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("app_id and app_private_key must both be provided together", stdout)

    def test_fails_private_key_without_app_id(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "APP_PRIVATE_KEY": "pem", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("app_id and app_private_key must both be provided together", stdout)

    def test_succeeds_app_credentials_paired(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "APP_ID": "123", "APP_PRIVATE_KEY": "pem", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    # Timeout Tests
    def test_fails_timeout_zero(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "0", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '0'", stdout)

    def test_fails_timeout_negative(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "-5", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '-5'", stdout)

    def test_fails_timeout_non_numeric(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "abc", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got 'abc'", stdout)

    def test_fails_timeout_decimal(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "1.5", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '1.5'", stdout)

    def test_succeeds_timeout_valid(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "30", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_timeout_empty(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_fails_timeout_whitespace(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "TIMEOUT_MINUTES": "  ", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("timeout_minutes must be a positive integer, got '  '", stdout)

    # Compose/Agent Tests
    def test_fails_compose_without_agent(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "COMPOSE_PROMPT": "true", "AGENT_NAME": "", "ACTION_PATH": self.temp_action_path},
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
        self.assertIn("Agent 'nonexistent' not found in agents/, extra_agents_path, or .github/claude-agents/", stdout)

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

    def test_succeeds_agent_in_extra_path(self):
        """Agent found via EXTRA_AGENTS_PATH should pass validation."""
        extra_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(extra_dir), exist_ok=True)
        with open(os.path.join(extra_dir, "custom-engineer.md"), "w") as f:
            f.write("# Test agent\n")

        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {
                "OAUTH_TOKEN": "tok",
                "COMPOSE_PROMPT": "true",
                "AGENT_NAME": "custom-engineer",
                "EXTRA_AGENTS_PATH": extra_dir,
                "ACTION_PATH": self.temp_action_path,
                "WORKSPACE_PATH": self.temp_workspace,
            },
        )
        self.assertEqual(rc, 0)

    def test_succeeds_auto_agent(self):
        """auto agent mode should pass validation without a file."""
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {
                "OAUTH_TOKEN": "tok",
                "COMPOSE_PROMPT": "true",
                "AGENT_NAME": "auto",
                "ACTION_PATH": self.temp_action_path,
                "WORKSPACE_PATH": self.temp_workspace,
            },
        )
        self.assertEqual(rc, 0)

    def test_succeeds_no_compose(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "COMPOSE_PROMPT": "false", "ACTION_PATH": self.temp_action_path},
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
            {"OAUTH_TOKEN": "tok", "ACTION_PATH": self.temp_action_path},
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

    # Max Turns Tests
    def test_fails_max_turns_zero(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "0", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("max_turns must be a positive integer, got '0'", stdout)

    def test_fails_max_turns_negative(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "-3", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("max_turns must be a positive integer, got '-3'", stdout)

    def test_fails_max_turns_non_numeric(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "abc", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("max_turns must be a positive integer, got 'abc'", stdout)

    def test_fails_max_turns_decimal(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "3.5", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("max_turns must be a positive integer, got '3.5'", stdout)

    def test_succeeds_max_turns_valid(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "10", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_max_turns_empty(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MAX_TURNS": "", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    # Model Format Tests
    def test_fails_model_invalid_format(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MODEL": "gpt-4", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("model must start with 'claude-', got 'gpt-4'", stdout)

    def test_fails_model_empty_string(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MODEL": "", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)  # Empty is allowed, should not fail

    def test_succeeds_model_valid_format(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MODEL": "claude-sonnet-4", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_model_complex_name(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "MODEL": "claude-sonnet-4-20250514", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    # Dry Run Tests
    def test_fails_dry_run_invalid_value(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "DRY_RUN": "yes", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("dry_run must be 'true' or 'false', got 'yes'", stdout)

    def test_fails_dry_run_numeric(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "DRY_RUN": "1", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 1)
        self.assertIn("dry_run must be 'true' or 'false', got '1'", stdout)

    def test_succeeds_dry_run_true(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "DRY_RUN": "true", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_dry_run_false(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "DRY_RUN": "false", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)

    def test_succeeds_dry_run_empty(self):
        rc, stdout, _, _ = run_script(
            "validate_inputs.sh",
            {"OAUTH_TOKEN": "tok", "DRY_RUN": "", "ACTION_PATH": self.temp_action_path},
        )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()