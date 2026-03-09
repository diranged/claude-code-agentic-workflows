#!/usr/bin/env python3
"""Tests for duplicate issue detection script."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestCheckDuplicateIssue(unittest.TestCase):
    """Test duplicate issue detection script."""

    def setUp(self):
        """Set up test environment."""
        # Get the script path
        self.script_dir = Path(__file__).parent.parent / "scripts"
        self.script_path = self.script_dir / "check_duplicate_issue.sh"

        # Ensure script exists and is executable
        self.assertTrue(self.script_path.exists(), f"Script not found: {self.script_path}")
        self.assertTrue(os.access(self.script_path, os.X_OK), f"Script not executable: {self.script_path}")

    def run_script(self, github_token="fake_token", github_repo="owner/repo", dashboard_label="dashboard"):
        """Run the duplicate issue detection script with given environment."""
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = github_token
        env["GITHUB_REPOSITORY"] = github_repo
        env["DASHBOARD_LABEL"] = dashboard_label

        try:
            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            self.fail(f"Failed to run script: {e}")

    def test_missing_github_token(self):
        """Test script fails when GITHUB_TOKEN is missing."""
        env = os.environ.copy()
        if "GITHUB_TOKEN" in env:
            del env["GITHUB_TOKEN"]
        env["GITHUB_REPOSITORY"] = "owner/repo"
        env["DASHBOARD_LABEL"] = "dashboard"

        result = subprocess.run(
            ["bash", str(self.script_path)],
            capture_output=True,
            text=True,
            env=env,
            check=False
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("::error::GITHUB_TOKEN is required", result.stderr)

    def test_missing_github_repository(self):
        """Test script fails when GITHUB_REPOSITORY is missing."""
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = "fake_token"
        if "GITHUB_REPOSITORY" in env:
            del env["GITHUB_REPOSITORY"]
        env["DASHBOARD_LABEL"] = "dashboard"

        result = subprocess.run(
            ["bash", str(self.script_path)],
            capture_output=True,
            text=True,
            env=env,
            check=False
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("::error::GITHUB_REPOSITORY is required", result.stderr)

    def test_missing_dashboard_label(self):
        """Test script skips check when DASHBOARD_LABEL is missing."""
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = "fake_token"
        env["GITHUB_REPOSITORY"] = "owner/repo"
        if "DASHBOARD_LABEL" in env:
            del env["DASHBOARD_LABEL"]

        result = subprocess.run(
            ["bash", str(self.script_path)],
            capture_output=True,
            text=True,
            env=env,
            check=False
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("::warning::No dashboard_label provided", result.stderr)
        self.assertIn("duplicate=false", result.stdout)
        self.assertIn("existing_issue_number=", result.stdout)

    def test_no_duplicate_issues(self):
        """Test when no duplicate issues are found."""
        # Create a mock gh script that returns empty array
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_path.write_text('#!/bin/bash\necho "[]"\n')
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("duplicate=false", result.stdout)
            self.assertIn("existing_issue_number=", result.stdout)

    def test_duplicate_issue_found(self):
        """Test when a duplicate issue is found."""
        # Mock gh to return issue array with one issue
        mock_issues = [{"number": 123, "title": "Existing Dashboard"}]

        # Create a mock gh script that returns issue array
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_path.write_text(f'#!/bin/bash\necho \'{json.dumps(mock_issues)}\'\n')
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("duplicate=true", result.stdout)
            self.assertIn("existing_issue_number=123", result.stdout)

    def test_api_error_handling(self):
        """Test graceful handling of API errors."""
        # Create a mock gh script that fails
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_path.write_text('#!/bin/bash\nexit 1\n')
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            # When gh fails, the script uses fallback "[]" so it should succeed gracefully
            self.assertIn("duplicate=false", result.stdout)
            self.assertIn("existing_issue_number=", result.stdout)

    def test_empty_result_handling(self):
        """Test handling when Python script returns empty result."""
        # Create a mock python3 that succeeds but returns no output to trigger the warning path
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_python_path = Path(tmpdir) / "python3"
            mock_python_path.write_text('#!/bin/bash\n# Return success but no output\nexit 0\n')
            mock_python_path.chmod(0o755)

            # Override PATH to use our mock python3
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            # When python3 returns empty output, the script should issue a warning
            self.assertIn("::warning::Failed to check for duplicate issues", result.stderr)
            self.assertIn("duplicate=false", result.stdout)
            self.assertIn("existing_issue_number=", result.stdout)

    def test_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        # Create a mock gh script that returns invalid JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_path.write_text('#!/bin/bash\necho "invalid json {"\n')
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("duplicate=false", result.stdout)
            self.assertIn("existing_issue_number=", result.stdout)

    def test_multiple_issues_returns_first(self):
        """Test that when multiple issues exist, the first one is returned."""
        # Mock gh to return multiple issues
        mock_issues = [
            {"number": 123, "title": "First Dashboard"},
            {"number": 456, "title": "Second Dashboard"}
        ]

        # Create a mock gh script that returns multiple issues
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_path.write_text(f'#!/bin/bash\necho \'{json.dumps(mock_issues)}\'\n')
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = "dashboard"

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("duplicate=true", result.stdout)
            self.assertIn("existing_issue_number=123", result.stdout)  # First issue

    def test_label_with_special_characters(self):
        """Test that labels with special characters are handled correctly."""
        # Test with label containing URL-special characters
        special_label = "my-label&foo=bar"

        # Create a mock gh script that captures arguments and returns empty array
        with tempfile.TemporaryDirectory() as tmpdir:
            args_file = Path(tmpdir) / "gh_args.txt"
            mock_gh_path = Path(tmpdir) / "gh"
            mock_gh_script = f'''#!/bin/bash
# Capture all arguments for verification
echo "$@" > "{args_file}"
echo "[]"
'''
            mock_gh_path.write_text(mock_gh_script)
            mock_gh_path.chmod(0o755)

            # Override PATH to use our mock gh
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
            env["GITHUB_TOKEN"] = "fake_token"
            env["GITHUB_REPOSITORY"] = "owner/repo"
            env["DASHBOARD_LABEL"] = special_label

            result = subprocess.run(
                ["bash", str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )

            # Script should succeed
            self.assertEqual(result.returncode, 0)
            self.assertIn("duplicate=false", result.stdout)

            # Verify the special label was passed correctly to gh (not mangled/split)
            captured_args = args_file.read_text().strip()
            # The mock gh should receive the label as a single argument (without shell quotes)
            self.assertIn(f'--label {special_label}', captured_args)


if __name__ == "__main__":
    unittest.main()