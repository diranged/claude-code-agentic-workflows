#!/usr/bin/env python3
"""Tests for ACTION_PATH vs WORKSPACE_PATH resolution for agent prompts."""

import os
import tempfile
import unittest
from pathlib import Path

from helpers import run_script


class TestActionPathResolution(unittest.TestCase):
    """Test that ACTION_PATH resolves correctly for all agent prompts."""

    def setUp(self):
        """Set up separate ACTION_PATH and WORKSPACE_PATH directories."""
        self.action_path = tempfile.mkdtemp()
        self.workspace_path = tempfile.mkdtemp()

        # Create directory structure in ACTION_PATH (simulating the composite action)
        os.makedirs(os.path.join(self.action_path, "agents"))
        os.makedirs(os.path.join(self.action_path, "instructions"))
        os.makedirs(os.path.join(self.action_path, "skills"))

        # Create test built-in agents in ACTION_PATH
        self.builtin_agents = [
            "agentic-designer",
            "agentic-developer",
            "architect",
            "docs-reviewer",
            "janitor",
            "performance-reviewer",
            "test-coverage"
        ]

        for agent in self.builtin_agents:
            with open(os.path.join(self.action_path, "agents", f"{agent}.md"), "w") as f:
                f.write(f"# Agent: {agent.title()}\n\nBuilt-in {agent} agent from ACTION_PATH.\n")

        # Create test instructions in ACTION_PATH
        with open(os.path.join(self.action_path, "instructions", "00-base.md"), "w") as f:
            f.write("# Base Instructions\n\nBase instructions from ACTION_PATH.\n")

        # Create test skills in ACTION_PATH
        with open(os.path.join(self.action_path, "skills", "test-skill.md"), "w") as f:
            f.write("# Skill: Test\n\nTest skill from ACTION_PATH.\n")

        # Create workspace structure
        os.makedirs(os.path.join(self.workspace_path, ".github", "claude-agents"), exist_ok=True)

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        shutil.rmtree(self.action_path)
        shutil.rmtree(self.workspace_path)

    def run_compose_prompt(self, agent_name="agentic-designer", extra_agents_path=None):
        """Run compose_prompt.sh with separate ACTION_PATH and WORKSPACE_PATH."""
        env = {
            "ACTION_PATH": self.action_path,
            "WORKSPACE_PATH": self.workspace_path,
            "AGENT_NAME": agent_name,
            "PROMPT_TEXT": "",
            "ISSUE_NUMBER": "",
            "COMMENT_ID": "",
            "RUN_ID": "",
            "RUN_URL": "",
        }
        if extra_agents_path:
            env["EXTRA_AGENTS_PATH"] = extra_agents_path

        return run_script("compose_prompt.sh", env)

    def test_all_builtin_agents_load_from_action_path(self):
        """All built-in agents should load successfully from ACTION_PATH."""
        for agent in self.builtin_agents:
            with self.subTest(agent=agent):
                rc, _, _, outputs = self.run_compose_prompt(agent_name=agent)
                self.assertEqual(rc, 0, f"Agent {agent} failed to load")
                prompt = outputs.get("prompt", "")
                self.assertIn(f"Built-in {agent} agent from ACTION_PATH", prompt)

    def test_extra_agents_path_resolution(self):
        """EXTRA_AGENTS_PATH should resolve correctly when different from ACTION_PATH."""
        extra_path = tempfile.mkdtemp()
        os.makedirs(os.path.join(extra_path), exist_ok=True)
        with open(os.path.join(extra_path, "docs-engineer.md"), "w") as f:
            f.write("# Agent: Documentation Engineer\n\nDocs engineer from EXTRA_AGENTS_PATH.\n")

        try:
            rc, _, _, outputs = self.run_compose_prompt(
                agent_name="docs-engineer",
                extra_agents_path=extra_path
            )
            self.assertEqual(rc, 0)
            prompt = outputs.get("prompt", "")
            self.assertIn("Docs engineer from EXTRA_AGENTS_PATH", prompt)
        finally:
            import shutil
            shutil.rmtree(extra_path)

    def test_action_path_with_trailing_slash(self):
        """ACTION_PATH with trailing slash should work correctly."""
        env = {
            "ACTION_PATH": self.action_path + "/",  # Note the trailing slash
            "WORKSPACE_PATH": self.workspace_path,
            "AGENT_NAME": "agentic-designer",
            "PROMPT_TEXT": "",
            "ISSUE_NUMBER": "",
            "COMMENT_ID": "",
            "RUN_ID": "",
            "RUN_URL": "",
        }

        rc, _, _, outputs = run_script("compose_prompt.sh", env)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Built-in agentic-designer agent from ACTION_PATH", prompt)

    def test_instructions_load_from_action_path(self):
        """Instructions should load from ACTION_PATH, not WORKSPACE_PATH."""
        rc, _, _, outputs = self.run_compose_prompt()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Base instructions from ACTION_PATH", prompt)

    def test_skills_load_from_action_path(self):
        """Skills should load from ACTION_PATH, not WORKSPACE_PATH."""
        rc, _, _, outputs = self.run_compose_prompt()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Test skill from ACTION_PATH", prompt)

    def test_user_override_priority_over_action_path(self):
        """User overrides in WORKSPACE_PATH should take priority over ACTION_PATH."""
        # Create user override
        with open(os.path.join(self.workspace_path, ".github", "claude-agents", "agentic-designer.md"), "w") as f:
            f.write("# Agent: Custom Designer\n\nUser override from WORKSPACE_PATH.\n")

        rc, _, _, outputs = self.run_compose_prompt()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("User override from WORKSPACE_PATH", prompt)
        self.assertNotIn("Built-in agentic-designer agent from ACTION_PATH", prompt)

    def test_error_when_action_path_missing_agents_dir(self):
        """Should fail gracefully when ACTION_PATH has no agents/ directory."""
        bad_action_path = tempfile.mkdtemp()
        # Don't create agents/ subdirectory

        env = {
            "ACTION_PATH": bad_action_path,
            "WORKSPACE_PATH": self.workspace_path,
            "AGENT_NAME": "agentic-designer",
            "PROMPT_TEXT": "",
            "ISSUE_NUMBER": "",
            "COMMENT_ID": "",
            "RUN_ID": "",
            "RUN_URL": "",
        }

        try:
            rc, stdout, stderr, _ = run_script("compose_prompt.sh", env)
            # Should fail to find the agent
            self.assertNotEqual(rc, 0)
            combined = stdout + stderr
            self.assertIn("agentic-designer", combined)
        finally:
            import shutil
            shutil.rmtree(bad_action_path)

    def test_validate_inputs_uses_action_path(self):
        """validate_inputs.sh should also resolve agents via ACTION_PATH."""
        env = {
            "OAUTH_TOKEN": "test-token",
            "COMPOSE_PROMPT": "true",
            "AGENT_NAME": "agentic-designer",
            "ACTION_PATH": self.action_path,
            "WORKSPACE_PATH": self.workspace_path,
        }

        rc, stdout, stderr, _ = run_script("validate_inputs.sh", env)
        self.assertEqual(rc, 0)
        # Should not complain about missing agent
        combined = stdout + stderr
        self.assertNotIn("not found", combined.lower())

    def test_action_path_spaces_in_path(self):
        """ACTION_PATH with spaces should be handled correctly."""
        spaced_path = tempfile.mkdtemp(suffix=" with spaces")
        os.makedirs(os.path.join(spaced_path, "agents"))

        with open(os.path.join(spaced_path, "agents", "test-agent.md"), "w") as f:
            f.write("# Agent: Space Test\n\nAgent from path with spaces.\n")

        env = {
            "ACTION_PATH": spaced_path,
            "WORKSPACE_PATH": self.workspace_path,
            "AGENT_NAME": "test-agent",
            "PROMPT_TEXT": "",
            "ISSUE_NUMBER": "",
            "COMMENT_ID": "",
            "RUN_ID": "",
            "RUN_URL": "",
        }

        try:
            rc, _, _, outputs = run_script("compose_prompt.sh", env)
            self.assertEqual(rc, 0)
            prompt = outputs.get("prompt", "")
            self.assertIn("Agent from path with spaces", prompt)
        finally:
            import shutil
            shutil.rmtree(spaced_path)


if __name__ == "__main__":
    unittest.main()