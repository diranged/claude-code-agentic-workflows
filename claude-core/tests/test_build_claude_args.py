"""Tests for scripts/build_claude_args.sh."""

import unittest

from helpers import run_script


class TestBuildClaudeArgs(unittest.TestCase):
    def test_no_optional_args_only_verbose(self):
        rc, _, _, outputs = run_script("build_claude_args.sh")
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["args"].strip(), "--verbose")

    def test_model_added(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"MODEL": "claude-sonnet-4-20250514"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--model claude-sonnet-4-20250514", outputs["args"])

    def test_max_turns_added(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"MAX_TURNS": "10"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--max-turns 10", outputs["args"])

    def test_allowed_tools_added(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"ALLOWED_TOOLS": "bash,read"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--allowedTools bash,read", outputs["args"])

    def test_disallowed_tools_added(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"DISALLOWED_TOOLS": "write,delete"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--disallowedTools write,delete", outputs["args"])

    def test_extra_args_appended(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"EXTRA_ARGS": "--custom-flag value"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--custom-flag value", outputs["args"])

    def test_verbose_always_last(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {
                "MODEL": "claude-sonnet-4-20250514",
                "MAX_TURNS": "5",
                "EXTRA_ARGS": "--foo bar",
            },
        )
        self.assertEqual(rc, 0)
        args = outputs["args"].strip()
        self.assertTrue(args.endswith("--verbose"))

    def test_all_flags_combined(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {
                "MODEL": "claude-sonnet-4-20250514",
                "MAX_TURNS": "10",
                "ALLOWED_TOOLS": "bash",
                "DISALLOWED_TOOLS": "write",
                "EXTRA_ARGS": "--custom flag",
            },
        )
        self.assertEqual(rc, 0)
        args = outputs["args"].strip()
        self.assertIn("--model claude-sonnet-4-20250514", args)
        self.assertIn("--max-turns 10", args)
        self.assertIn("--allowedTools bash", args)
        self.assertIn("--disallowedTools write", args)
        self.assertIn("--custom flag", args)
        self.assertTrue(args.endswith("--verbose"))

    def test_empty_env_vars_ignored(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"MODEL": "", "MAX_TURNS": ""},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["args"].strip(), "--verbose")

    def test_heredoc_output_format(self):
        """The output should use heredoc format (args<<EOF...EOF)."""
        rc, _, _, outputs = run_script("build_claude_args.sh")
        self.assertEqual(rc, 0)
        self.assertIn("args", outputs)

    def test_flag_order_model_before_max_turns(self):
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"MODEL": "m", "MAX_TURNS": "5"},
        )
        args = outputs["args"]
        self.assertLess(args.index("--model"), args.index("--max-turns"))

    # Input validation tests
    def test_model_with_shell_metacharacters_rejected(self):
        """MODEL containing semicolon should be rejected."""
        rc, _, stderr, _ = run_script(
            "build_claude_args.sh",
            {"MODEL": "claude-test; rm -rf /"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: MODEL contains disallowed characters", stderr)

    def test_max_turns_with_pipe_rejected(self):
        """MAX_TURNS containing pipe should be rejected."""
        rc, _, stderr, _ = run_script(
            "build_claude_args.sh",
            {"MAX_TURNS": "10 | malicious"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: MAX_TURNS contains disallowed characters", stderr)

    def test_allowed_tools_with_backtick_rejected(self):
        """ALLOWED_TOOLS containing backtick should be rejected."""
        rc, _, stderr, _ = run_script(
            "build_claude_args.sh",
            {"ALLOWED_TOOLS": "bash,read`cmd`"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: ALLOWED_TOOLS contains disallowed characters", stderr)

    def test_disallowed_tools_with_ampersand_rejected(self):
        """DISALLOWED_TOOLS containing ampersand should be rejected."""
        rc, _, stderr, _ = run_script(
            "build_claude_args.sh",
            {"DISALLOWED_TOOLS": "write & evil"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: DISALLOWED_TOOLS contains disallowed characters", stderr)

    def test_model_with_newline_rejected(self):
        """MODEL containing newline should be rejected."""
        rc, _, stderr, _ = run_script(
            "build_claude_args.sh",
            {"MODEL": "claude-test\nmalicious"},
        )
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: MODEL contains disallowed characters", stderr)

    def test_extra_args_not_validated(self):
        """EXTRA_ARGS with special characters should still be accepted."""
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"EXTRA_ARGS": "--timeout 60; echo test"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--timeout 60; echo test", outputs["args"])

    def test_valid_model_with_special_but_safe_chars(self):
        """MODEL with hyphens, underscores, dots should pass validation."""
        rc, _, _, outputs = run_script(
            "build_claude_args.sh",
            {"MODEL": "claude-sonnet-4-20250514"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("--model claude-sonnet-4-20250514", outputs["args"])

    def test_all_metacharacters_rejected(self):
        """Test that all dangerous metacharacters are rejected."""
        dangerous_chars = [";", "|", "&", "$", "`", "<", ">"]
        for char in dangerous_chars:
            with self.subTest(char=char):
                rc, _, stderr, _ = run_script(
                    "build_claude_args.sh",
                    {"MODEL": f"claude-test{char}evil"},
                )
                self.assertEqual(rc, 1)
                self.assertIn("ERROR: MODEL contains disallowed characters", stderr)


if __name__ == "__main__":
    unittest.main()
