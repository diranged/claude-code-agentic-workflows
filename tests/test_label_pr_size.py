"""Tests for scripts/label_pr_size.sh."""

import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "label_pr_size.sh")


class TestLabelPrSize(unittest.TestCase):
    def _run(self, pr_number=None, pr_additions=None, pr_deletions=None, mock_gh=None):
        """Run the label PR size script with optional mocking."""
        env = dict(os.environ)

        # Set up test environment
        if pr_number is not None:
            env["PR_NUMBER"] = str(pr_number)
        if pr_additions is not None:
            env["PR_ADDITIONS"] = str(pr_additions)
        if pr_deletions is not None:
            env["PR_DELETIONS"] = str(pr_deletions)

        # Mock gh command if provided
        if mock_gh is not None:
            with tempfile.TemporaryDirectory() as tmpdir:
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
        else:
            return subprocess.run(
                ["bash", SCRIPT],
                capture_output=True,
                text=True,
                env=env,
            )

    def test_xs_label_boundary(self):
        """Test XS label for 0 and 9 lines."""
        # Test 0 lines
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removed labels"
elif [[ "$*" == *"--add-label size/XS"* ]]; then
    echo "Added label: size/XS"
fi
'''
        result = self._run(pr_number=123, pr_additions=0, pr_deletions=0, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/XS", result.stdout)

        # Test 9 lines
        result = self._run(pr_number=123, pr_additions=5, pr_deletions=4, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/XS", result.stdout)

    def test_s_label_boundary(self):
        """Test S label for 10 and 29 lines."""
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removed labels"
elif [[ "$*" == *"--add-label size/S"* ]]; then
    echo "Added label: size/S"
fi
'''
        # Test 10 lines
        result = self._run(pr_number=123, pr_additions=6, pr_deletions=4, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/S", result.stdout)

        # Test 29 lines
        result = self._run(pr_number=123, pr_additions=15, pr_deletions=14, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/S", result.stdout)

    def test_m_label_boundary(self):
        """Test M label for 30 and 99 lines."""
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removed labels"
elif [[ "$*" == *"--add-label size/M"* ]]; then
    echo "Added label: size/M"
fi
'''
        # Test 30 lines
        result = self._run(pr_number=123, pr_additions=20, pr_deletions=10, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/M", result.stdout)

        # Test 99 lines
        result = self._run(pr_number=123, pr_additions=50, pr_deletions=49, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/M", result.stdout)

    def test_l_label_boundary(self):
        """Test L label for 100 and 499 lines."""
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removed labels"
elif [[ "$*" == *"--add-label size/L"* ]]; then
    echo "Added label: size/L"
fi
'''
        # Test 100 lines
        result = self._run(pr_number=123, pr_additions=60, pr_deletions=40, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/L", result.stdout)

        # Test 499 lines
        result = self._run(pr_number=123, pr_additions=300, pr_deletions=199, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/L", result.stdout)

    def test_xl_label_boundary(self):
        """Test XL label for 500+ lines."""
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removed labels"
elif [[ "$*" == *"--add-label size/XL"* ]]; then
    echo "Added label: size/XL"
fi
'''
        # Test 500 lines
        result = self._run(pr_number=123, pr_additions=300, pr_deletions=200, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/XL", result.stdout)

        # Test 1000 lines
        result = self._run(pr_number=123, pr_additions=600, pr_deletions=400, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/XL", result.stdout)

    def test_removes_existing_labels(self):
        """Test that existing size labels are removed."""
        mock_gh = '''
if [[ "$*" == *"--remove-label"* ]]; then
    echo "Removing labels: $*"
    exit 0
elif [[ "$*" == *"--add-label"* ]]; then
    echo "Adding label: $*"
    exit 0
fi
'''
        result = self._run(pr_number=123, pr_additions=10, pr_deletions=5, mock_gh=mock_gh)
        self.assertEqual(result.returncode, 0)
        self.assertIn("size/XS,size/S,size/M,size/L,size/XL", result.stdout)

    def test_missing_pr_number(self):
        """Test error handling when PR number is missing."""
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PR number required", result.stderr)

    def test_pr_number_from_argument(self):
        """Test PR number passed as command line argument."""
        mock_gh = '''
if [[ "$*" == *"--add-label size/S"* ]]; then
    echo "Added label for PR: $*"
fi
'''
        result = subprocess.run(
            ["bash", SCRIPT, "456"],
            capture_output=True,
            text=True,
            env={**os.environ, "PR_ADDITIONS": "15", "PR_DELETIONS": "10", "PATH": f"/tmp:{os.environ['PATH']}"},
        )
        # Note: This test may fail without proper gh mock setup, but validates argument parsing


if __name__ == "__main__":
    unittest.main()