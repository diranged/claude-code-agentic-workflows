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

    def test_runtime_context_notify_owners(self):
        """Notify Owners should appear in runtime context when set."""
        rc, _, _, outputs = self._run({"NOTIFY_OWNERS": "alice,bob"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Notify Owners: alice,bob", prompt)

    def test_runtime_context_omits_empty_vars(self):
        """Runtime context should not include lines for empty vars."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertNotIn("Issue Number:", prompt)
        self.assertNotIn("Tracking Comment ID:", prompt)
        self.assertNotIn("Notify Owners:", prompt)

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

    def test_conventional_commit_config_auto_detected(self):
        """Conventional commit workflow should be auto-detected and injected."""
        workspace = tempfile.mkdtemp()
        wf_dir = os.path.join(workspace, ".github", "workflows")
        os.makedirs(wf_dir)
        with open(os.path.join(wf_dir, "pr-check.yml"), "w") as f:
            f.write("name: Check\nsteps:\n  - uses: amannn/action-semantic-pull-request@v5\n")

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Conventional Commit Configuration", prompt)
        self.assertIn("semantic-pull-request", prompt)

    def test_no_conventional_commit_when_absent(self):
        """No conventional commit section when no checker workflow exists."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertNotIn("Conventional Commit Configuration", prompt)

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

    def test_extra_instructions_path(self):
        """Extra instructions from EXTRA_INSTRUCTIONS_PATH should be included."""
        extra_dir = tempfile.mkdtemp()
        with open(os.path.join(extra_dir, "00-extra.md"), "w") as f:
            f.write("# Extra Engineer Instructions\n\nShared engineer behavior.\n")

        rc, _, _, outputs = self._run({"EXTRA_INSTRUCTIONS_PATH": extra_dir})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Extra Engineer Instructions", prompt)
        self.assertIn("Shared engineer behavior", prompt)

    def test_extra_instructions_before_user_overrides(self):
        """Extra instructions should appear before user instruction overrides."""
        extra_dir = tempfile.mkdtemp()
        with open(os.path.join(extra_dir, "00-extra.md"), "w") as f:
            f.write("# Extra Instructions Here\n")

        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-instructions")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "99-custom.md"), "w") as f:
            f.write("# User Override Here\n")

        rc, _, _, outputs = self._run({
            "EXTRA_INSTRUCTIONS_PATH": extra_dir,
        }, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        extra_pos = prompt.find("Extra Instructions Here")
        user_pos = prompt.find("User Override Here")
        self.assertGreater(extra_pos, -1)
        self.assertGreater(user_pos, -1)
        self.assertLess(extra_pos, user_pos)

    def test_engineer_base_loads_with_agent(self):
        """Engineer base instructions + agent should compose correctly via extra paths."""
        engineer_instructions = os.path.join(CORE_DIR, "..", "claude-engineer", "instructions")
        engineer_agents = os.path.join(CORE_DIR, "..", "claude-engineer", "agents")
        rc, _, _, outputs = self._run({
            "AGENT_NAME": "docs-engineer",
            "EXTRA_INSTRUCTIONS_PATH": engineer_instructions,
            "EXTRA_AGENTS_PATH": engineer_agents,
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        # Base engineer instructions should be present
        self.assertIn("Persistent Engineer Base", prompt)
        self.assertIn("Dashboard Management", prompt)
        # Agent-specific content should be present
        self.assertIn("Documentation Engineer", prompt)
        self.assertIn("README drift", prompt)

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

    def test_loads_code_janitor_agent_via_extra_path(self):
        """code-janitor agent should load from extra_agents_path."""
        engineer_agents = os.path.join(CORE_DIR, "..", "claude-engineer", "agents")
        rc, _, _, outputs = self._run({
            "AGENT_NAME": "code-janitor",
            "EXTRA_AGENTS_PATH": engineer_agents,
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Code Janitor", prompt)

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

    # --- auto agent mode ---

    def test_auto_includes_agent_catalog(self):
        """auto mode should include all built-in agent definitions."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "auto"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Intelligent Agent Selection", prompt)
        self.assertIn("Available Agents", prompt)
        self.assertIn("Selection Instructions", prompt)

    def test_auto_includes_all_builtin_agents(self):
        """auto mode should include every built-in agent."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "auto"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        for agent_name in [
            "Agentic Designer",
            "Agentic Developer",
            "Architect",
            "Docs Reviewer",
            "Janitor",
            "Performance Reviewer",
            "Test Coverage Reviewer",
        ]:
            with self.subTest(agent=agent_name):
                self.assertIn(agent_name, prompt)

    def test_auto_includes_extra_agents(self):
        """auto mode should include agents from extra_agents_path."""
        engineer_agents = os.path.join(CORE_DIR, "..", "claude-engineer", "agents")
        rc, _, _, outputs = self._run({
            "AGENT_NAME": "auto",
            "EXTRA_AGENTS_PATH": engineer_agents,
        })
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Documentation Engineer", prompt)
        self.assertIn("Code Janitor", prompt)

    def test_auto_user_override_deduplicates(self):
        """User agent override should replace built-in in auto catalog."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-agents")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "agentic-designer.md"), "w") as f:
            f.write("# Agent: Custom Designer Override\n\nCustom behavior.\n")

        rc, _, _, outputs = self._run({"AGENT_NAME": "auto"}, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom Designer Override", prompt)
        # Built-in designer content should NOT appear (user override takes priority)
        self.assertNotIn("read-only architectural", prompt.lower())

    def test_auto_includes_selection_instructions(self):
        """auto mode should include instructions for Claude to self-select."""
        rc, _, _, outputs = self._run({"AGENT_NAME": "auto"})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Agentic Developer", prompt)
        self.assertIn("most appropriate agent role", prompt)

    def test_heredoc_output_format(self):
        """Output should use heredoc format with COMPOSED_EOF delimiter."""
        rc, _, _, outputs = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("prompt", outputs)

    # Edge case tests
    def test_empty_user_override_dirs(self):
        """Empty user override directories should not cause failures."""
        workspace = tempfile.mkdtemp()
        # Create empty directories
        os.makedirs(os.path.join(workspace, ".github", "claude-instructions"))
        os.makedirs(os.path.join(workspace, ".github", "claude-skills"))
        os.makedirs(os.path.join(workspace, ".github", "claude-agents"))

        rc, _, _, outputs = self._run({"AGENT_NAME": "agentic-designer"}, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        # Should still load built-in content
        self.assertIn("Base Instructions", prompt)
        self.assertIn("Agentic Designer", prompt)

    def test_non_md_files_ignored_in_instructions(self):
        """Non-.md files in instruction directories should be ignored."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-instructions")
        os.makedirs(override_dir)
        # Create a non-.md file
        with open(os.path.join(override_dir, "config.txt"), "w") as f:
            f.write("This should not be included\n")
        # Create a .md file
        with open(os.path.join(override_dir, "00-custom.md"), "w") as f:
            f.write("# Custom Instructions\nThis should be included.\n")

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom Instructions", prompt)
        self.assertNotIn("This should not be included", prompt)

    def test_non_md_files_ignored_in_skills(self):
        """Non-.md files in skills directories should be ignored."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-skills")
        os.makedirs(override_dir)
        # Create a non-.md file
        with open(os.path.join(override_dir, "script.py"), "w") as f:
            f.write("print('Not a skill')\n")
        # Create a .md file
        with open(os.path.join(override_dir, "custom-skill.md"), "w") as f:
            f.write("# Skill: Custom\nCustom skill content.\n")

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Custom skill content", prompt)
        self.assertNotIn("Not a skill", prompt)

    def test_prompt_text_with_special_characters(self):
        """PROMPT_TEXT with special characters should be handled correctly."""
        special_prompt = "Fix the `login` bug in $HOME/app.py with \"quotes\" and 'apostrophes'"
        rc, _, _, outputs = self._run({"PROMPT_TEXT": special_prompt})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("login", prompt)
        self.assertIn("$HOME/app.py", prompt)
        self.assertIn('"quotes"', prompt)
        self.assertIn("'apostrophes'", prompt)

    def test_multiline_prompt_text(self):
        """PROMPT_TEXT with newlines should be preserved correctly."""
        multiline_prompt = "Line 1: Fix the bug\nLine 2: Run the tests\nLine 3: Update docs"
        rc, _, _, outputs = self._run({"PROMPT_TEXT": multiline_prompt})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Line 1: Fix the bug", prompt)
        self.assertIn("Line 2: Run the tests", prompt)
        self.assertIn("Line 3: Update docs", prompt)

    def test_missing_workspace_subdirs(self):
        """Missing .github/ subdirectories in workspace should not cause failures."""
        workspace = tempfile.mkdtemp()
        # Don't create any .github/ subdirectories

        rc, _, _, outputs = self._run(workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        # Should still load built-in content
        self.assertIn("Base Instructions", prompt)

    def test_agent_file_empty(self):
        """Empty agent files should be handled gracefully."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-agents")
        os.makedirs(override_dir)
        # Create empty agent file
        with open(os.path.join(override_dir, "empty-agent.md"), "w") as f:
            f.write("")  # Completely empty

        rc, _, _, outputs = self._run({"AGENT_NAME": "empty-agent"}, workspace=workspace)
        self.assertEqual(rc, 0)
        # Should succeed even with empty agent content

    def test_agent_file_with_unicode(self):
        """Agent files with Unicode characters should be handled correctly."""
        workspace = tempfile.mkdtemp()
        override_dir = os.path.join(workspace, ".github", "claude-agents")
        os.makedirs(override_dir)
        with open(os.path.join(override_dir, "unicode-agent.md"), "w", encoding="utf-8") as f:
            f.write("# Agent: Unicode Test\n\n你好 🌍 Café naïve résumé\n")

        rc, _, _, outputs = self._run({"AGENT_NAME": "unicode-agent"}, workspace=workspace)
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("Unicode Test", prompt)
        self.assertIn("你好", prompt)
        self.assertIn("🌍", prompt)

    def test_prompt_with_heredoc_delimiter(self):
        """PROMPT_TEXT containing heredoc delimiter should not break output."""
        problem_prompt = "Use this code:\nCOMPOSED_EOF\necho 'test'"
        rc, _, _, outputs = self._run({"PROMPT_TEXT": problem_prompt})
        self.assertEqual(rc, 0)
        prompt = outputs.get("prompt", "")
        self.assertIn("COMPOSED_EOF", prompt)
        self.assertIn("echo 'test'", prompt)


if __name__ == "__main__":
    unittest.main()
