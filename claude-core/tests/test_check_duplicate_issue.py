#!/usr/bin/env python3
"""Tests for duplicate issue detection script."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


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

    @patch('subprocess.run')
    def test_no_duplicate_issues(self, mock_run):
        """Test when no duplicate issues are found."""
        # Mock curl to return empty array, but let python3 run normally
        # Store the original subprocess.run function before patching
        original_subprocess_run = subprocess.run

        def side_effect(*args, **kwargs):
            # Check if this is a curl call by looking at command args
            command = args[0] if args else []
            if isinstance(command, list) and len(command) > 0 and 'curl' in command[0]:
                # Mock the curl call
                mock_result = MagicMock()
                mock_result.stdout = "[]"
                mock_result.returncode = 0
                return mock_result
            # For all other calls (including python3, bash), run normally
            return original_subprocess_run(*args, **kwargs)

        mock_run.side_effect = side_effect

        returncode, stdout, stderr = self.run_script()
        self.assertEqual(returncode, 0)
        self.assertIn("duplicate=false", stdout)
        self.assertIn("existing_issue_number=", stdout)

    @patch('subprocess.run')
    def test_duplicate_issue_found(self, mock_run):
        """Test when a duplicate issue is found."""
        # Mock curl to return issue array with one issue
        mock_issues = [{"number": 123, "title": "Existing Dashboard"}]

        def side_effect(*args, **kwargs):
            # Check if this is a curl call by looking at command args
            command = args[0] if args else []
            if isinstance(command, list) and len(command) > 0 and 'curl' in command[0]:
                # Mock the curl call
                mock_result = MagicMock()
                mock_result.stdout = json.dumps(mock_issues)
                mock_result.returncode = 0
                return mock_result
            # For all other calls (including python3, bash), run normally
            return subprocess.run(*args, **kwargs)

        mock_run.side_effect = side_effect

        returncode, stdout, stderr = self.run_script()
        self.assertEqual(returncode, 0)
        self.assertIn("duplicate=true", stdout)
        self.assertIn("existing_issue_number=123", stdout)

    @patch('subprocess.run')
    def test_api_error_handling(self, mock_run):
        """Test graceful handling of API errors."""

        def side_effect(*args, **kwargs):
            # Check if this is a curl call by looking at command args
            command = args[0] if args else []
            if isinstance(command, list) and len(command) > 0 and 'curl' in command[0]:
                # Mock the curl call to fail
                mock_result = MagicMock()
                mock_result.stdout = ""
                mock_result.returncode = 1
                return mock_result
            # For all other calls (including python3, bash), run normally
            return subprocess.run(*args, **kwargs)

        mock_run.side_effect = side_effect

        returncode, stdout, stderr = self.run_script()
        self.assertEqual(returncode, 0)
        self.assertIn("::warning::Failed to check for duplicate issues", stderr)
        self.assertIn("duplicate=false", stdout)
        self.assertIn("existing_issue_number=", stdout)

    @patch('subprocess.run')
    def test_invalid_json_response(self, mock_run):
        """Test handling of invalid JSON response."""

        def side_effect(*args, **kwargs):
            # Check if this is a curl call by looking at command args
            command = args[0] if args else []
            if isinstance(command, list) and len(command) > 0 and 'curl' in command[0]:
                # Mock the curl call to return invalid JSON
                mock_result = MagicMock()
                mock_result.stdout = "invalid json {"
                mock_result.returncode = 0
                return mock_result
            # For all other calls (including python3, bash), run normally
            return subprocess.run(*args, **kwargs)

        mock_run.side_effect = side_effect

        returncode, stdout, stderr = self.run_script()
        self.assertEqual(returncode, 0)
        self.assertIn("duplicate=false", stdout)
        self.assertIn("existing_issue_number=", stdout)

    @patch('subprocess.run')
    def test_multiple_issues_returns_first(self, mock_run):
        """Test that when multiple issues exist, the first one is returned."""
        # Mock curl to return multiple issues
        mock_issues = [
            {"number": 123, "title": "First Dashboard"},
            {"number": 456, "title": "Second Dashboard"}
        ]

        def side_effect(*args, **kwargs):
            # Check if this is a curl call by looking at command args
            command = args[0] if args else []
            if isinstance(command, list) and len(command) > 0 and 'curl' in command[0]:
                # Mock the curl call
                mock_result = MagicMock()
                mock_result.stdout = json.dumps(mock_issues)
                mock_result.returncode = 0
                return mock_result
            # For all other calls (including python3, bash), run normally
            return subprocess.run(*args, **kwargs)

        mock_run.side_effect = side_effect

        returncode, stdout, stderr = self.run_script()
        self.assertEqual(returncode, 0)
        self.assertIn("duplicate=true", stdout)
        self.assertIn("existing_issue_number=123", stdout)  # First issue

    def test_label_with_special_characters(self):
        """Test that labels with special characters are handled correctly."""
        returncode, stdout, stderr = self.run_script(dashboard_label="docs-engineer:dashboard")
        # Should not crash - specific API behavior depends on GitHub's URL encoding
        self.assertEqual(returncode, 0)


if __name__ == "__main__":
    unittest.main()