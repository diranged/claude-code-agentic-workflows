"""Tests for scripts/validate_workflows.sh."""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_workflows.sh")

# Check if PyYAML is available
try:
    import yaml
    PYYAML_AVAILABLE = True
except ImportError:
    PYYAML_AVAILABLE = False


class TestValidateWorkflows(unittest.TestCase):
    def _run(self, directory):
        return subprocess.run(
            ["bash", SCRIPT, directory],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHON": sys.executable},
        )

    @unittest.skipIf(not PYYAML_AVAILABLE, "PyYAML not available")
    def test_valid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_file = os.path.join(tmpdir, "workflow.yml")
            with open(valid_file, "w") as f:
                f.write("name: test\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n")
            result = self._run(tmpdir)
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS:", result.stdout)

    def test_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_file = os.path.join(tmpdir, "broken.yml")
            with open(invalid_file, "w") as f:
                f.write("key:\n  bad: indentation:\n    - item\n  : broken\n")
            result = self._run(tmpdir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL:", result.stdout)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run(tmpdir)
            self.assertEqual(result.returncode, 0)
            self.assertIn("No workflow files found", result.stdout)

    @unittest.skipIf(not PYYAML_AVAILABLE, "PyYAML not available")
    def test_finds_yaml_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, "workflow.yaml")
            with open(yaml_file, "w") as f:
                f.write("name: test\non: push\n")
            result = self._run(tmpdir)
            self.assertEqual(result.returncode, 0)
            self.assertIn("PASS:", result.stdout)
            self.assertIn("workflow.yaml", result.stdout)


if __name__ == "__main__":
    unittest.main()
