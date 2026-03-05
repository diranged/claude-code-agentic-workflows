"""Tests for claude-core/scripts/compose_prompt.sh."""

import os
import tempfile
import unittest

from helpers import parse_github_output, run_script

# Paths to built-in content directories
CORE_DIR = os.path.join(os.path.dirname(__file__), "..")
INSTRUCTIONS_DIR = os.path.join(CORE_DIR, "instructions")
SKILLS_DIR = os.path.join(CORE_DIR, "skills")
AGENTS_DIR = os.path.join(CORE_DIR, "agents")


class TestComposePrompt(unittest.TestCase):
    """Tests for compose_prompt.sh."""

    def _run(self, env_overrides=None, workspace=None):
        """Run compose_prompt.sh with default env vars, returning outputs dict."""
        if workspace is None:
            workspace = tempfile.mkdtemp()

        env = {
            "ACTION_PATH": CORE_DIR,
            "WORKSPACE_PATH": workspace,
            "AGENT_NAME": "",
            "PROMPT_TEXT": "",
            "ISSUE_NUMBER": "",
            "COMMENT_ID": "",
            "RUN_ID": "",
            "RUN_URL": "",
        }
        if env_overrides:
            env.update(env_overrides)

        rc, stdout, stderr, outputs = run_script("compose_prompt.sh", env)
        return rc, stdout, stderr, outputs

    def test_loads_instructions_sorted(self):
        """Instructions from ACTION_PATH/instructions/ should be included in sorted order."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        # 00-base.md content should appear before 10-github.md content
        base_pos = prompt.find("Base Instructions")
        github_pos = prompt.find("GitHub Environment")
        self.assertGreater(base_pos, -1, "Base instructions not found in prompt")
        self.assertGreater(github_pos, -1, "GitHub instructions not found in prompt")
        self.assertLess(base_pos, github_pos, "Instructions not in sorted order")

    def test_loads_skills(self):
        """Skills from ACTION_PATH/skills/ should be included."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("GitHub Issue Progress", prompt)

    def test_loads_agent_by_name(self):
        """Agent definition should be loaded when AGENT_NAME is set."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "agentic-designer"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Agentic Designer", prompt)

    def test_loads_developer_agent(self):
        """agentic-developer agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "agentic-developer"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Agentic Developer", prompt)

    def test_error_when_agent_not_found(self):
        """Should fail when agent name doesn't match any file."""
        rc, stdout, stderr, _ = self._run({"AGENT_NAME": "nonexistent-agent"})
        self.assertNotEqual(rc, 0)
        combined = stdout + stderr
        self.assertIn("nonexistent-agent", combined)

    def test_runtime_context_injection(self):
        """Runtime context vars should appear in the composed prompt."""
        rc, _, _, outputs = self._run({
            "ISSUE_NUMBER": "42",
            "COMMENT_ID": "12345",
            "RUN_ID": "99999",
            "RUN_URL": "https://github.com/test/repo/actions/runs/99999",
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Issue Number: 42", prompt)
        self.assertIn("Tracking Comment ID: 12345", prompt)
        self.assertIn("Run ID: 99999", prompt)
        self.assertIn("https://github.com/test/repo/actions/runs/99999", prompt)

    def test_runtime_context_omits_empty_vars(self):
        """Runtime context should not include lines for empty vars."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertNotIn("Issue Number:", prompt)
        self.assertNotIn("Tracking Comment ID:", prompt)

    def test_prompt_text_appended_as_task_context(self):
        """PROMPT_TEXT should appear under '## Task Context'."""
        rc, _, _, outputs = self._run({"PROMPT_TEXT": "Please fix the login bug"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("## Task Context", prompt)
        self.assertIn("Please fix the login bug", prompt)

    def test_no_task_context_when_prompt_empty(self):
        """No Task Context section when PROMPT_TEXT is empty."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertNotIn("## Task Context", prompt)

    def test_user_instruction_overrides(self):
        """User instruction overrides from WORKSPACE_PATH/.github/claude-instructions/ should be included."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-instructions")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "99-custom.md"), "w") as f:
            f.write("# Custom User Instruction\n\nAlways use TypeScript.\n")

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom User Instruction", prompt)
        self.assertIn("Always use TypeScript", prompt)

    def test_user_skill_overrides(self):
        """User skill overrides from WORKSPACE_PATH/.github/claude-skills/ should be included."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-skills")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "custom-skill.md"), "w") as f:
            f.write("# Skill: Custom Deployment\n\nDeploy using kubectl.\n")

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom Deployment", prompt)

    def test_user_agent_override(self):
        """User agent override should take priority over built-in agent."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-agents")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "agentic-designer.md"), "w") as f:
            f.write("# Agent: Custom Designer Override\n\nCustom behavior.\n")

        rc, _, _, outputs = self._run({
            "AGENT_NAME": "agentic-designer",
        }, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom Designer Override", prompt)
        # Should NOT contain the built-in designer content
        self.assertNotIn("read-only", prompt.lower().split("custom designer override")[0])

    def test_no_agent_when_name_empty(self):
        """No agent section when AGENT_NAME is empty."""
        rc, _, _, outputs = self._run({"AGENT_NAME": ""})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertNotIn("Agentic Designer", prompt)
        self.assertNotIn("Agentic Developer", prompt)

    def test_ordering_instructions_before_skills(self):
        """Instructions should appear before skills in the composed prompt."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        instructions_pos = prompt.find("Base Instructions")
        skills_pos = prompt.find("GitHub Issue Progress")
        self.assertGreater(instructions_pos, -1)
        self.assertGreater(skills_pos, -1)
        self.assertLess(instructions_pos, skills_pos)

    def test_ordering_skills_before_agent(self):
        """Skills should appear before agent definition."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "agentic-designer"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        skills_pos = prompt.find("GitHub Issue Progress")
        agent_pos = prompt.find("Agentic Designer")
        self.assertGreater(skills_pos, -1)
        self.assertGreater(agent_pos, -1)
        self.assertLess(skills_pos, agent_pos)

    def test_loads_janitor_agent(self):
        """janitor agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "janitor"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Janitor", prompt)

    def test_loads_performance_reviewer_agent(self):
        """performance-reviewer agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "performance-reviewer"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Performance Reviewer", prompt)

    def test_loads_docs_reviewer_agent(self):
        """docs-reviewer agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "docs-reviewer"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Docs Reviewer", prompt)

    def test_loads_test_coverage_agent(self):
        """test-coverage agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "test-coverage"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Test Coverage Reviewer", prompt)

    def test_loads_architect_agent(self):
        """architect agent should load correctly."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "architect"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Architect", prompt)

    def test_loads_docs_engineer_agent_via_extra_path(self):
        """docs-engineer agent should load from extra_agents_path."""
        engineer_agents = os.path.join(CORE_DIR, "..", "claude-engineer", "agents")
        rc, _, _, outputs = self._run({
            "AGENT_NAME": "docs-engineer",
            "EXTRA_AGENTS_PATH": engineer_agents,
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Documentation Engineer", prompt)

    def test_extra_agents_path_priority(self):
        """extra_agents_path should be checked after user overrides but before built-in."""
        extra_dir = tempfile.mkdtemp()
        with open(os.path.join(extra_dir, "agentic-designer.md"), "w") as f:
            f.write("# Agent: Extra Path Designer\n\nFrom extra path.\n")

        rc, _, _, outputs = self._run({
            "AGENT_NAME": "agentic-designer",
            "EXTRA_AGENTS_PATH": extra_dir,
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        # extra_agents_path should win over built-in
        self.assertIn("Extra Path Designer", prompt)

    def test_user_override_beats_extra_agents_path(self):
        """User .github/claude-agents/ should take priority over extra_agents_path."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-agents")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "my-agent.md"), "w") as f:
            f.write("# Agent: User Override Agent\n")

        extra_dir = tempfile.mkdtemp()
        with open(os.path.join(extra_dir, "my-agent.md"), "w") as f:
            f.write("# Agent: Extra Path Agent\n")

        rc, _, _, outputs = self._run({
            "AGENT_NAME": "my-agent",
            "EXTRA_AGENTS_PATH": extra_dir,
        }, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("User Override Agent", prompt)
        self.assertNotIn("Extra Path Agent", prompt)

    def test_heredoc_output_format(self):
        """Output should use heredoc format with COMPOSED_EOF delimiter."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("prompt", outputs)


if __name__ == "__main__":
    unittest.main()
