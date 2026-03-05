"""Tests for claude-core/scripts/detect_intent.sh."""

import unittest

from helpers import run_script


class TestDetectIntent(unittest.TestCase):
    """Tests for detect_intent.sh routing logic."""

    def _run(self, comment_body="", trigger_label=""):
        """Run detect_intent.sh with COMMENT_BODY/TRIGGER_LABEL and return outputs dict."""
        rc, stdout, stderr, outputs = run_script(
            "detect_intent.sh",
            {"COMMENT_BODY": comment_body, "TRIGGER_LABEL": trigger_label},
        )
        self.assertEqual(rc, 0, f"Script failed: {stderr}")
        return outputs

    # --- implement ---

    def test_implement_direct(self):
        outputs = self._run("@claude implement")
        self.assertEqual(outputs["agent"], "agentic-developer")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_implement_this(self):
        outputs = self._run("@claude implement this")
        self.assertEqual(outputs["agent"], "agentic-developer")

    def test_implement_case_insensitive(self):
        outputs = self._run("@Claude Implement This")
        self.assertEqual(outputs["agent"], "agentic-developer")

    # --- janitor ---

    def test_janitor_dead_code(self):
        outputs = self._run("@claude check for dead code")
        self.assertEqual(outputs["agent"], "janitor")

    def test_janitor_stale(self):
        outputs = self._run("@claude find stale references")
        self.assertEqual(outputs["agent"], "janitor")

    def test_janitor_todo(self):
        outputs = self._run("@claude review TODO items")
        self.assertEqual(outputs["agent"], "janitor")

    def test_janitor_cleanup(self):
        outputs = self._run("@claude cleanup the codebase")
        self.assertEqual(outputs["agent"], "janitor")

    def test_janitor_deprecated(self):
        outputs = self._run("@claude find deprecated APIs")
        self.assertEqual(outputs["agent"], "janitor")

    def test_janitor_unused(self):
        outputs = self._run("@claude find unused imports")
        self.assertEqual(outputs["agent"], "janitor")

    # --- performance-reviewer ---

    def test_perf_performance(self):
        outputs = self._run("@claude check performance")
        self.assertEqual(outputs["agent"], "performance-reviewer")

    def test_perf_n_plus_1(self):
        outputs = self._run("@claude look for N+1 queries")
        self.assertEqual(outputs["agent"], "performance-reviewer")

    def test_perf_memory_leak(self):
        outputs = self._run("@claude check for memory leak issues")
        self.assertEqual(outputs["agent"], "performance-reviewer")

    def test_perf_slow(self):
        outputs = self._run("@claude this endpoint is slow")
        self.assertEqual(outputs["agent"], "performance-reviewer")

    # --- docs-reviewer ---

    def test_docs_documentation(self):
        outputs = self._run("@claude review documentation")
        self.assertEqual(outputs["agent"], "docs-reviewer")

    def test_docs_readme(self):
        outputs = self._run("@claude check the README")
        self.assertEqual(outputs["agent"], "docs-reviewer")

    def test_docs_broken_link(self):
        outputs = self._run("@claude find broken link issues")
        self.assertEqual(outputs["agent"], "docs-reviewer")

    def test_docs_doc_singular(self):
        outputs = self._run("@claude review the doc")
        self.assertEqual(outputs["agent"], "docs-reviewer")

    # --- test-coverage ---

    def test_coverage_tests(self):
        outputs = self._run("@claude review tests")
        self.assertEqual(outputs["agent"], "test-coverage")

    def test_coverage_coverage(self):
        outputs = self._run("@claude check coverage gaps")
        self.assertEqual(outputs["agent"], "test-coverage")

    def test_coverage_flaky(self):
        outputs = self._run("@claude find flaky tests")
        self.assertEqual(outputs["agent"], "test-coverage")

    def test_coverage_untested(self):
        outputs = self._run("@claude find untested code")
        self.assertEqual(outputs["agent"], "test-coverage")

    def test_coverage_edge_case(self):
        outputs = self._run("@claude check for edge case coverage")
        self.assertEqual(outputs["agent"], "test-coverage")

    # --- architect ---

    def test_architect_direct(self):
        outputs = self._run("@claude architect review")
        self.assertEqual(outputs["agent"], "architect")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_architect_coupling(self):
        outputs = self._run("@claude check for coupling issues")
        self.assertEqual(outputs["agent"], "architect")

    def test_architect_design_review(self):
        outputs = self._run("@claude do a design review")
        self.assertEqual(outputs["agent"], "architect")

    # --- generic review catch-all → architect ---

    def test_review_catchall(self):
        outputs = self._run("@claude review this issue")
        self.assertEqual(outputs["agent"], "architect")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    # --- default fallback → agentic-designer ---

    def test_default_bare_claude(self):
        outputs = self._run("@claude")
        self.assertEqual(outputs["agent"], "agentic-designer")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_default_unrecognized(self):
        outputs = self._run("@claude do something random")
        self.assertEqual(outputs["agent"], "agentic-designer")

    # --- edge cases ---

    def test_empty_body(self):
        outputs = self._run("")
        self.assertEqual(outputs["agent"], "agentic-designer")

    def test_multiline_body(self):
        body = "Hey team,\n\n@claude implement this feature\n\nThanks!"
        outputs = self._run(body)
        self.assertEqual(outputs["agent"], "agentic-developer")

    def test_mid_sentence(self):
        outputs = self._run("Can you @claude review the architecture?")
        self.assertEqual(outputs["agent"], "architect")

    # --- label-based routing ---

    def test_label_implement(self):
        outputs = self._run(trigger_label="claude:implement")
        self.assertEqual(outputs["agent"], "agentic-developer")
        self.assertEqual(outputs["model"], "claude-sonnet-4-20250514")

    def test_label_review(self):
        outputs = self._run(trigger_label="claude:review")
        self.assertEqual(outputs["agent"], "architect")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_label_design(self):
        outputs = self._run(trigger_label="claude:design")
        self.assertEqual(outputs["agent"], "agentic-designer")
        self.assertEqual(outputs["model"], "claude-opus-4-20250514")

    def test_label_unknown_claude_prefix(self):
        outputs = self._run(trigger_label="claude:something-else")
        self.assertEqual(outputs["agent"], "agentic-designer")

    def test_label_takes_priority_over_comment(self):
        """Label routing should override comment body routing."""
        outputs = self._run(
            comment_body="@claude implement this",
            trigger_label="claude:review",
        )
        self.assertEqual(outputs["agent"], "architect")

    def test_non_claude_label_falls_through(self):
        """Non-claude: labels should fall through to comment body routing."""
        outputs = self._run(
            comment_body="@claude implement",
            trigger_label="bug",
        )
        self.assertEqual(outputs["agent"], "agentic-developer")

    def test_empty_label_falls_through(self):
        """Empty label should fall through to comment body routing."""
        outputs = self._run(comment_body="@claude check performance")
        self.assertEqual(outputs["agent"], "performance-reviewer")


if __name__ == "__main__":
    unittest.main()
