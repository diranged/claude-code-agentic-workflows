"""Tests for scripts/post_review_checklist.sh."""

import os
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "post_review_checklist.sh")


class TestPostReviewChecklist(unittest.TestCase):
    def _run(self, pr_number=None, checklist_file=None, mock_gh=None, setup_custom_checklist=False):
        """Run the review checklist script with optional mocking."""
        env = dict(os.environ)
        # Remove GITHUB_WORKSPACE so the script treats the test's tmpdir as workspace root
        env.pop("GITHUB_WORKSPACE", None)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for the test
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Set up test environment
                if pr_number is not None:
                    env["PR_NUMBER"] = str(pr_number)
                if checklist_file is not None:
                    env["CHECKLIST_FILE"] = checklist_file

                # Set up custom checklist file if requested
                if setup_custom_checklist:
                    os.makedirs(".github", exist_ok=True)
                    with open(".github/review-checklist.md", "w") as f:
                        f.write("## Custom Review Checklist\n")
                        f.write("- [ ] Custom requirement 1\n")
                        f.write("- [ ] Custom requirement 2\n")

                # Mock gh command if provided
                if mock_gh is not None:
                    # Create mock gh script
                    gh_script = os.path.join(tmpdir, "gh")
                    with open(gh_script, "w") as f:
                        f.write(f"#!/bin/bash\n{mock_gh}\n")
                    os.chmod(gh_script, 0o755)

                    # Prepend to PATH
                    env["PATH"] = f"{tmpdir}:{env['PATH']}"

                return subprocess.run(
                    ["bash", SCRIPT],
                    capture_output=True,
                    text=True,
                    env=env,
                )
            finally:
                os.chdir(original_cwd)

    def test_default_checklist(self):
        """Test default checklist is used when no custom file exists."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted comment: $4"
fi
'''
        result = self._run(pr_number=123, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Using default checklist", result.stdout)
        self.assertIn("Posted comment", result.stdout)

    def test_custom_checklist(self):
        """Test custom checklist file is used when present."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted custom comment: $4"
fi
'''
        result = self._run(pr_number=123, mock_gh=mock_gh, setup_custom_checklist=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Using custom checklist from .github/review-checklist.md", result.stdout)
        self.assertIn("Posted custom comment", result.stdout)

    def test_idempotent_existing_comment(self):
        """Test script doesn't post duplicate comments."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": [{"id": "12345", "body": "## Review Checklist\\n- [ ] Test"}]}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Should not be called"
    exit 1
fi
'''
        result = self._run(pr_number=123, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Review checklist comment already exists", result.stdout)
        self.assertIn("Skipping to avoid duplicates", result.stdout)

    def test_missing_pr_number(self):
        """Test error handling when PR number is missing."""
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PR number required", result.stderr)

    def test_custom_checklist_file_env_var(self):
        """Test custom checklist file path via environment variable."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted with custom file: $4"
fi
'''
        env = dict(os.environ)
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_file = os.path.join(tmpdir, "my-checklist.md")
            with open(custom_file, "w") as f:
                f.write("## My Custom Checklist\n- [ ] Special requirement\n")

            # Mock gh command
            gh_script = os.path.join(tmpdir, "gh")
            with open(gh_script, "w") as f:
                f.write(f"#!/bin/bash\n{mock_gh}\n")
            os.chmod(gh_script, 0o755)

            env["PATH"] = f"{tmpdir}:{env['PATH']}"
            env["PR_NUMBER"] = "123"
            env["CHECKLIST_FILE"] = custom_file
            # Set GITHUB_WORKSPACE to tmpdir so absolute path to custom_file is within workspace
            env["GITHUB_WORKSPACE"] = tmpdir

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = subprocess.run(
                    ["bash", SCRIPT],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                self.assertEqual(result.returncode, 0)
                self.assertIn(f"Using custom checklist from {custom_file}", result.stdout)
            finally:
                os.chdir(original_cwd)

    def test_pr_number_from_argument(self):
        """Test PR number passed as command line argument."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" && "$3" == "456" ]]; then
    echo "Posted to PR 456"
fi
'''
        # Test with PR number as argument
        env = dict(os.environ)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock gh command
            gh_script = os.path.join(tmpdir, "gh")
            with open(gh_script, "w") as f:
                f.write(f"#!/bin/bash\n{mock_gh}\n")
            os.chmod(gh_script, 0o755)

            # Prepend to PATH
            env["PATH"] = f"{tmpdir}:{env['PATH']}"

            result = subprocess.run(
                ["bash", SCRIPT, "456"],
                capture_output=True,
                text=True,
                env=env,
            )
            # This validates argument parsing works
            self.assertIn("Posted to PR 456", result.stdout)

    def test_detects_existing_comment_by_header(self):
        """Test that existing comments are detected by the Review Checklist header."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": [
        {"id": "11111", "body": "Some other comment"},
        {"id": "22222", "body": "## Review Checklist\\n- [x] Already done"},
        {"id": "33333", "body": "Another comment"}
    ]}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Should not post duplicate"
    exit 1
fi
'''
        result = self._run(pr_number=123, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment already exists", result.stdout)
        self.assertIn("comment ID: 22222", result.stdout)

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected but fallback to default."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted comment: $4"
fi
'''
        result = self._run(pr_number=123, checklist_file="../../etc/passwd", mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)  # Should continue with fallback
        self.assertIn("Error: Checklist file must be within the workspace directory", result.stderr)
        self.assertIn("Using default checklist for security", result.stderr)
        # Should use default checklist as fallback
        self.assertIn("Posted comment", result.stdout)

    def test_absolute_path_outside_workspace_rejected(self):
        """Test that absolute paths outside workspace are rejected but fallback to default."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted comment: $4"
fi
'''
        result = self._run(pr_number=123, checklist_file="/etc/passwd", mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)  # Should continue with fallback
        self.assertIn("Error: Checklist file must be within the workspace directory", result.stderr)
        self.assertIn("Using default checklist for security", result.stderr)
        # Should use default checklist as fallback
        self.assertIn("Posted comment", result.stdout)

    def test_valid_relative_path_within_workspace(self):
        """Test that valid relative paths within workspace work normally."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted comment: $4"
fi
'''
        result = self._run(pr_number=123, checklist_file=".github/review-checklist.md",
                          mock_gh=mock_gh, setup_custom_checklist=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Using custom checklist from .github/review-checklist.md", result.stdout)
        self.assertNotIn("Error: Checklist file must be within the workspace directory", result.stderr)

    def test_oversized_content_rejected(self):
        """Test that oversized content (>64KB) is rejected."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Should not be called for oversized content"
    exit 1
fi
'''

        # Create large file within the test workspace
        env = dict(os.environ)
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Create oversized checklist file (>64KB)
                with open("large-checklist.md", "w") as f:
                    f.write("## Large Checklist\n")
                    # Write >66KB of content to exceed 64KB limit
                    f.write("- [ ] Test\n" * 6000)  # Each line is ~11 bytes, 6000 * 11 = 66KB

                # Mock gh command
                gh_script = os.path.join(tmpdir, "gh")
                with open(gh_script, "w") as f:
                    f.write(f"#!/bin/bash\n{mock_gh}\n")
                os.chmod(gh_script, 0o755)
                env["PATH"] = f"{tmpdir}:{env['PATH']}"
                env["PR_NUMBER"] = "123"
                env["CHECKLIST_FILE"] = "large-checklist.md"
                # Unset GITHUB_WORKSPACE so script uses current directory as workspace
                env.pop("GITHUB_WORKSPACE", None)

                result = subprocess.run(
                    ["bash", SCRIPT],
                    capture_output=True,
                    text=True,
                    env=env,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Error: Checklist content exceeds maximum size (64KB)", result.stderr)
            finally:
                os.chdir(original_cwd)

    def test_symlink_traversal_rejected(self):
        """Test that symlinks pointing outside workspace are rejected."""
        mock_gh = '''
if [[ "$1" == "pr" && "$2" == "view" ]]; then
    echo '{"comments": []}'
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
    echo "Posted comment: $4"
fi
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a symlink pointing to /etc/passwd
            symlink_file = os.path.join(tmpdir, "evil-symlink.md")
            try:
                os.symlink("/etc/passwd", symlink_file)
            except OSError:
                # Skip test if symlinks not supported (e.g., Windows without admin)
                self.skipTest("Symlinks not supported on this system")

            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                result = self._run(pr_number=123, checklist_file=symlink_file, mock_gh=mock_gh)
                self.assertEqual(result.returncode, 0)  # Should continue with fallback
                self.assertIn("Error: Checklist file must be within the workspace directory", result.stderr)
                self.assertIn("Using default checklist for security", result.stderr)
                # Should use default checklist as fallback
                self.assertIn("Posted comment", result.stdout)
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()