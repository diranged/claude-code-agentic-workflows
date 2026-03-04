"""Unit tests for generate_summary.py."""

import json
import os
import tempfile
import unittest

# Allow importing the module from the parent directory
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generate_summary import format_cost, format_duration, generate_summary, parse_execution

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


if __name__ == "__main__":
    unittest.main()
