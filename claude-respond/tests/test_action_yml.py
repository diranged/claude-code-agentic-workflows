"""Tests for claude-respond/action.yml structure."""

import os
import unittest

import yaml

RESPOND_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")
CORE_YML = os.path.join(os.path.dirname(__file__), "..", "..", "claude-core", "action.yml")


class TestActionYml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RESPOND_YML) as f:
            cls.respond = yaml.safe_load(f)
        with open(CORE_YML) as f:
            cls.core = yaml.safe_load(f)

    def test_is_composite_action(self):
        self.assertEqual(self.respond["runs"]["using"], "composite")

    def test_has_name_and_description(self):
        self.assertIn("name", self.respond)
        self.assertIn("description", self.respond)

    # --- Input parity with claude-core ---

    def test_has_all_core_inputs(self):
        """claude-respond should expose every input that claude-core has."""
        for inp in self.core["inputs"]:
            self.assertIn(
                inp,
                self.respond["inputs"],
                f"claude-respond missing input '{inp}' that claude-core has",
            )

    def test_no_extra_inputs_beyond_core(self):
        """claude-respond should not have inputs that claude-core doesn't."""
        for inp in self.respond["inputs"]:
            self.assertIn(
                inp,
                self.core["inputs"],
                f"claude-respond has extra input '{inp}' not in claude-core",
            )

    def test_defaults_match_core(self):
        """Default values should be identical between respond and core."""
        for inp_name in self.respond["inputs"]:
            respond_default = self.respond["inputs"][inp_name].get("default")
            core_default = self.core["inputs"][inp_name].get("default")
            self.assertEqual(
                respond_default,
                core_default,
                f"Default mismatch for '{inp_name}': respond={respond_default!r} core={core_default!r}",
            )

    def test_required_flags_match_core(self):
        for inp_name in self.respond["inputs"]:
            respond_req = self.respond["inputs"][inp_name].get("required", False)
            core_req = self.core["inputs"][inp_name].get("required", False)
            self.assertEqual(
                respond_req,
                core_req,
                f"Required mismatch for '{inp_name}': respond={respond_req} core={core_req}",
            )

    # --- Input forwarding ---

    def test_all_inputs_forwarded_to_core_step(self):
        """Every input should be passed through to the core step's 'with' block."""
        core_step = self._get_step_by_id("core")
        self.assertIsNotNone(core_step, "No step with id 'core' found")
        with_block = core_step.get("with", {})
        for inp_name in self.respond["inputs"]:
            self.assertIn(
                inp_name,
                with_block,
                f"Input '{inp_name}' not forwarded to core step",
            )

    def test_core_step_forwards_use_inputs_syntax(self):
        """Each forwarded value should reference inputs.<name>."""
        core_step = self._get_step_by_id("core")
        with_block = core_step.get("with", {})
        for inp_name, value in with_block.items():
            self.assertIn(
                f"inputs.{inp_name}",
                value,
                f"Core step with.{inp_name} doesn't reference inputs.{inp_name}",
            )

    # --- Outputs ---

    def test_expected_outputs_exist(self):
        expected = ["execution_file", "branch_name", "session_id"]
        for out in expected:
            self.assertIn(out, self.respond["outputs"], f"Missing output: {out}")

    def test_outputs_reference_core_step(self):
        for name, output in self.respond["outputs"].items():
            self.assertIn(
                "steps.core.outputs.",
                output["value"],
                f"Output '{name}' does not reference 'core' step",
            )

    def test_output_names_match_core(self):
        """claude-respond outputs should match claude-core output names."""
        for out in self.respond["outputs"]:
            self.assertIn(
                out,
                self.core["outputs"],
                f"claude-respond output '{out}' not in claude-core",
            )

    # --- Step structure ---

    def test_has_two_steps(self):
        self.assertEqual(len(self.respond["runs"]["steps"]), 2)

    def test_report_step_has_if_always(self):
        report_step = self.respond["runs"]["steps"][1]
        self.assertEqual(
            report_step.get("if"),
            "always()",
            "Report step should have 'if: always()'",
        )

    def test_report_step_uses_claude_report(self):
        report_step = self.respond["runs"]["steps"][1]
        self.assertIn("claude-report", report_step.get("uses", ""))

    def test_no_inline_run_scripts(self):
        """claude-respond should have no inline shell scripts — it's pure composition."""
        for step in self.respond["runs"]["steps"]:
            self.assertNotIn(
                "run",
                step,
                f"Step '{step.get('name', '?')}' has an inline run script",
            )

    def test_core_step_uses_claude_core(self):
        core_step = self._get_step_by_id("core")
        self.assertIn("claude-core", core_step.get("uses", ""))

    def test_no_secrets_in_defaults(self):
        for name, inp in self.respond["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn("sk-", str(default), f"Input '{name}' default looks like a secret")

    def test_report_step_receives_execution_file(self):
        report_step = self.respond["runs"]["steps"][1]
        with_block = report_step.get("with", {})
        self.assertIn("execution_file", with_block)
        self.assertIn("steps.core.outputs.execution_file", with_block["execution_file"])

    def test_report_step_receives_outcome(self):
        report_step = self.respond["runs"]["steps"][1]
        with_block = report_step.get("with", {})
        self.assertIn("outcome", with_block)
        self.assertIn("steps.core.outcome", with_block["outcome"])

    # --- Helper ---

    def _get_step_by_id(self, step_id):
        for step in self.respond["runs"]["steps"]:
            if step.get("id") == step_id:
                return step
        return None


if __name__ == "__main__":
    unittest.main()
