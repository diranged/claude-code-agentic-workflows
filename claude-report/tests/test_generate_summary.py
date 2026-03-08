"""Unit tests for generate_summary.py."""

import json
import os
import tempfile
import unittest

# Allow importing the module from the parent directory
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generate_summary import format_cost, format_duration, generate_summary, parse_execution, validate_file_path

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestFormatDuration(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(format_duration(45200), "45.2s")

    def test_zero(self):
        self.assertEqual(format_duration(0), "0.0s")

    def test_sub_second(self):
        self.assertEqual(format_duration(500), "0.5s")


class TestFormatCost(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(format_cost(0.0542), "$0.0542")

    def test_zero(self):
        self.assertEqual(format_cost(0), "$0.0000")


class TestParseExecution(unittest.TestCase):
    def test_single_model(self):
        with open(os.path.join(FIXTURES_DIR, "single_model.json")) as f:
            data = json.load(f)
        metrics = parse_execution(data)
        self.assertEqual(metrics["duration_ms"], 45200)
        self.assertEqual(metrics["num_turns"], 5)
        self.assertEqual(metrics["total_cost_usd"], 0)
        self.assertIn("claude-sonnet-4-20250514", metrics["model_usage"])
        usage = metrics["model_usage"]["claude-sonnet-4-20250514"]
        self.assertEqual(usage["input"], 33000)
        self.assertEqual(usage["output"], 7700)
        self.assertEqual(usage["cache_read"], 20000)
        self.assertEqual(usage["cache_create"], 2500)

    def test_multi_model(self):
        with open(os.path.join(FIXTURES_DIR, "multi_model.json")) as f:
            data = json.load(f)
        metrics = parse_execution(data)
        self.assertEqual(len(metrics["model_usage"]), 2)
        self.assertIn("claude-sonnet-4-20250514", metrics["model_usage"])
        self.assertIn("claude-haiku-4-5-20251001", metrics["model_usage"])
        # Sonnet totals: 10000+12000=22000 input
        self.assertEqual(metrics["model_usage"]["claude-sonnet-4-20250514"]["input"], 22000)
        # Haiku: 3000 input
        self.assertEqual(metrics["model_usage"]["claude-haiku-4-5-20251001"]["input"], 3000)

    def test_no_usage(self):
        with open(os.path.join(FIXTURES_DIR, "no_usage.json")) as f:
            data = json.load(f)
        metrics = parse_execution(data)
        self.assertEqual(metrics["model_usage"], {})

    def test_api_key_billing(self):
        with open(os.path.join(FIXTURES_DIR, "api_key_billing.json")) as f:
            data = json.load(f)
        metrics = parse_execution(data)
        self.assertGreater(metrics["total_cost_usd"], 0)


class TestValidateFilePath(unittest.TestCase):
    def setUp(self):
        """Store original environment and create temp dirs for testing."""
        self.original_env = {}
        for env_var in ("GITHUB_WORKSPACE", "RUNNER_TEMP", "GITHUB_ACTION_PATH"):
            self.original_env[env_var] = os.environ.get(env_var)
            if env_var in os.environ:
                del os.environ[env_var]

    def tearDown(self):
        """Restore original environment."""
        for env_var, value in self.original_env.items():
            if value is not None:
                os.environ[env_var] = value
            elif env_var in os.environ:
                del os.environ[env_var]

    def test_validate_file_path_within_cwd(self):
        """A temp file in CWD passes validation (no env vars set)."""
        # Create a temporary file in the current working directory, not /tmp
        with tempfile.NamedTemporaryFile(dir=".", delete=False) as f:
            temp_path = f.name
        try:
            validated_path = validate_file_path(temp_path)
            self.assertEqual(os.path.realpath(temp_path), validated_path)
        finally:
            os.unlink(temp_path)

    def test_validate_file_path_in_workspace(self):
        """A file under GITHUB_WORKSPACE passes validation."""
        with tempfile.TemporaryDirectory() as workspace:
            os.environ["GITHUB_WORKSPACE"] = workspace
            test_file = os.path.join(workspace, "test.json")
            with open(test_file, "w") as f:
                f.write("{}")
            try:
                validated_path = validate_file_path(test_file)
                self.assertEqual(os.path.realpath(test_file), validated_path)
            finally:
                os.unlink(test_file)

    def test_validate_file_path_in_runner_temp(self):
        """A file under RUNNER_TEMP passes validation."""
        with tempfile.TemporaryDirectory() as runner_temp:
            os.environ["RUNNER_TEMP"] = runner_temp
            test_file = os.path.join(runner_temp, "execution.json")
            with open(test_file, "w") as f:
                f.write("[]")
            try:
                validated_path = validate_file_path(test_file)
                self.assertEqual(os.path.realpath(test_file), validated_path)
            finally:
                os.unlink(test_file)

    def test_validate_file_path_traversal_rejected(self):
        """Path like ../../etc/passwd is rejected when it resolves outside allowed dirs."""
        with tempfile.TemporaryDirectory() as workspace:
            os.environ["GITHUB_WORKSPACE"] = workspace
            # Try to access a file outside the workspace via path traversal
            traversal_path = os.path.join(workspace, "..", "..", "etc", "passwd")
            with self.assertRaises(ValueError) as context:
                validate_file_path(traversal_path)
            self.assertIn("outside allowed directories", str(context.exception))

    def test_validate_file_path_symlink_resolved(self):
        """Symlink pointing outside allowed dir is rejected."""
        with tempfile.TemporaryDirectory() as workspace:
            with tempfile.TemporaryDirectory() as outside_dir:
                os.environ["GITHUB_WORKSPACE"] = workspace
                # Create a file outside the workspace
                outside_file = os.path.join(outside_dir, "external.json")
                with open(outside_file, "w") as f:
                    f.write("{}")
                # Create a symlink inside workspace pointing to the external file
                symlink_path = os.path.join(workspace, "symlink.json")
                os.symlink(outside_file, symlink_path)
                try:
                    with self.assertRaises(ValueError) as context:
                        validate_file_path(symlink_path)
                    self.assertIn("outside allowed directories", str(context.exception))
                finally:
                    os.unlink(symlink_path)
                    os.unlink(outside_file)

    def test_validate_file_path_equals_allowed_directory(self):
        """File path that equals the allowed directory itself is accepted."""
        with tempfile.TemporaryDirectory() as workspace:
            os.environ["GITHUB_WORKSPACE"] = workspace
            validated_path = validate_file_path(workspace)
            self.assertEqual(os.path.realpath(workspace), validated_path)


class TestGenerateSummary(unittest.TestCase):
    def test_single_model_output(self):
        path = os.path.join(FIXTURES_DIR, "single_model.json")
        output = generate_summary(path, "sess-abc123", "success")
        self.assertIn("## Claude Execution Summary", output)
        self.assertIn("\u2705 Success", output)
        self.assertIn("45.2s", output)
        self.assertIn("claude-sonnet-4-20250514", output)
        self.assertIn("33,000", output)  # comma-formatted input tokens

    def test_multi_model_rows(self):
        path = os.path.join(FIXTURES_DIR, "multi_model.json")
        output = generate_summary(path, "sess-multi", "success")
        self.assertIn("claude-sonnet-4-20250514", output)
        self.assertIn("claude-haiku-4-5-20251001", output)

    def test_cost_row_shown_when_positive(self):
        path = os.path.join(FIXTURES_DIR, "api_key_billing.json")
        output = generate_summary(path, "sess-billing", "success")
        self.assertIn("Cost", output)
        self.assertIn("$0.0542", output)

    def test_cost_row_hidden_when_zero(self):
        path = os.path.join(FIXTURES_DIR, "single_model.json")
        output = generate_summary(path, "sess-abc123", "success")
        self.assertNotIn("Cost", output)

    def test_missing_file_fallback(self):
        output = generate_summary("/nonexistent/path.json", "sess-x", "failure")
        self.assertIn("\u274c Failed", output)
        self.assertIn("No execution file found", output)
        self.assertNotIn("Token Usage", output)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            path = f.name
        try:
            output = generate_summary(path, "sess-empty", "success")
            self.assertIn("No execution file found", output)
        finally:
            os.unlink(path)

    def test_malformed_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json")
            path = f.name
        try:
            output = generate_summary(path, "sess-bad", "failure")
            self.assertIn("No execution file found", output)
        finally:
            os.unlink(path)

    def test_non_list_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            path = f.name
        try:
            output = generate_summary(path, "sess-obj", "success")
            self.assertIn("No execution file found", output)
        finally:
            os.unlink(path)

    def test_none_execution_file(self):
        output = generate_summary(None, "sess-none", "success")
        self.assertIn("No execution file found", output)

    def test_empty_string_execution_file(self):
        output = generate_summary("", "sess-empty", "success")
        self.assertIn("No execution file found", output)

    def test_no_usage_shows_unknown(self):
        path = os.path.join(FIXTURES_DIR, "no_usage.json")
        output = generate_summary(path, "sess-nousage", "success")
        self.assertIn("_unknown_", output)

    def test_number_formatting_commas(self):
        path = os.path.join(FIXTURES_DIR, "single_model.json")
        output = generate_summary(path, "sess-fmt", "success")
        # 15000+18000 = 33000 → "33,000"
        self.assertIn("33,000", output)
        # 3200+4500 = 7700 → "7,700"
        self.assertIn("7,700", output)

    def test_failure_status(self):
        path = os.path.join(FIXTURES_DIR, "single_model.json")
        output = generate_summary(path, "sess-fail", "failure")
        self.assertIn("\u274c Failed", output)

    def test_generate_summary_traversal_fallback(self):
        """generate_summary() with a traversal path returns the fallback summary (graceful degradation)."""
        with tempfile.TemporaryDirectory() as workspace:
            # Set up GITHUB_WORKSPACE to restrict allowed directories
            old_workspace = os.environ.get("GITHUB_WORKSPACE")
            os.environ["GITHUB_WORKSPACE"] = workspace
            try:
                # Try to use a traversal path that goes outside the workspace
                traversal_path = os.path.join(workspace, "..", "..", "etc", "passwd")
                output = generate_summary(traversal_path, "sess-traversal", "success")
                # Should get fallback summary due to path validation failure
                self.assertIn("\u2705 Success", output)
                self.assertIn("No execution file found", output)
                self.assertNotIn("Token Usage", output)
                self.assertIn("sess-traversal", output)
            finally:
                # Restore original environment
                if old_workspace is not None:
                    os.environ["GITHUB_WORKSPACE"] = old_workspace
                elif "GITHUB_WORKSPACE" in os.environ:
                    del os.environ["GITHUB_WORKSPACE"]


if __name__ == "__main__":
    unittest.main()
