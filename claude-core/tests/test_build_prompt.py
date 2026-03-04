"""Tests for scripts/build_prompt.sh."""

import unittest

from helpers import run_script


class TestBuildPrompt(unittest.TestCase):
    def test_prompt_passthrough(self):
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": "Hello Claude"},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["prompt"], "Hello Claude")

    def test_empty_when_not_provided(self):
        rc, _, _, outputs = run_script("build_prompt.sh")
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["prompt"], "")

    def test_empty_string_prompt(self):
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": ""},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["prompt"], "")

    def test_multiline_prompt(self):
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": "Line 1\nLine 2\nLine 3"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("Line 1", outputs["prompt"])
        self.assertIn("Line 2", outputs["prompt"])
        self.assertIn("Line 3", outputs["prompt"])

    def test_special_characters(self):
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": "Fix the bug in $HOME & echo 'hello'"},
        )
        self.assertEqual(rc, 0)
        self.assertIn("Fix the bug", outputs["prompt"])

    def test_heredoc_output_format(self):
        """Output uses heredoc format (prompt<<EOF...EOF)."""
        rc, _, _, outputs = run_script("build_prompt.sh", {"PROMPT_TEXT": "test"})
        self.assertEqual(rc, 0)
        self.assertIn("prompt", outputs)

    def test_long_prompt(self):
        long_text = "word " * 1000
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": long_text.strip()},
        )
        self.assertEqual(rc, 0)
        self.assertEqual(outputs["prompt"], long_text.strip())

    def test_prompt_with_quotes(self):
        rc, _, _, outputs = run_script(
            "build_prompt.sh",
            {"PROMPT_TEXT": 'She said "hello" and \'goodbye\''},
        )
        self.assertEqual(rc, 0)
        self.assertIn('"hello"', outputs["prompt"])


if __name__ == "__main__":
    unittest.main()
