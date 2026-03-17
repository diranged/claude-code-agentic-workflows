"""Tests for claude-respond/action.yml structure."""

import os
import unittest

import yaml

RESPOND_YML = os.path.join(os.path.dirname(__file__), "..", "action.yml")
CORE_YML = os.path.join(os.path.dirname(__file__), "..", "..", "claude-core", "action.yml")

# Inputs that claude-respond has but claude-core does not.
# These are orchestration inputs handled by claude-setup and detect_intent.
RESPOND_ONLY_INPUTS = {
    "pre_run",
    "tracking_comment",
    "reaction_emoji",
    "checkout",
    "checkout_ref",
    "checkout_fetch_depth",
    "default_agent",
}


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

    def test_respond_only_inputs_are_allowed(self):
        """claude-respond extras beyond claude-core must be in the allowlist."""
        extra = set(self.respond["inputs"]) - set(self.core["inputs"])
        unexpected = extra - RESPOND_ONLY_INPUTS
        self.assertEqual(
            unexpected,
            set(),
            f"claude-respond has unexpected extra inputs: {unexpected}",
        )

    def test_all_respond_only_inputs_exist(self):
        """All declared respond-only inputs must actually exist."""
        for inp in RESPOND_ONLY_INPUTS:
            self.assertIn(
                inp,
                self.respond["inputs"],
                f"Declared respond-only input '{inp}' not found in action.yml",
            )

    def test_defaults_match_core_for_shared_inputs(self):
        """Default values for shared inputs should be identical."""
        shared = set(self.respond["inputs"]) & set(self.core["inputs"])
        for inp_name in shared:
            respond_default = self.respond["inputs"][inp_name].get("default")
            core_default = self.core["inputs"][inp_name].get("default")
            self.assertEqual(
                respond_default,
                core_default,
                f"Default mismatch for '{inp_name}': respond={respond_default!r} core={core_default!r}",
            )

    def test_required_flags_match_core_for_shared_inputs(self):
        shared = set(self.respond["inputs"]) & set(self.core["inputs"])
        for inp_name in shared:
            respond_req = self.respond["inputs"][inp_name].get("required", False)
            core_req = self.core["inputs"][inp_name].get("required", False)
            self.assertEqual(
                respond_req,
                core_req,
                f"Required mismatch for '{inp_name}': respond={respond_req} core={core_req}",
            )

    # --- Outputs ---

    def test_expected_outputs_exist(self):
        expected = ["execution_file", "branch_name", "session_id", "skipped"]
        for out in expected:
            self.assertIn(out, self.respond["outputs"], f"Missing output: {out}")

    def test_core_outputs_reference_core_step(self):
        for name in ["execution_file", "branch_name", "session_id"]:
            self.assertIn(
                "steps.core.outputs.",
                self.respond["outputs"][name]["value"],
                f"Output '{name}' does not reference 'core' step",
            )

    def test_output_names_include_core_outputs(self):
        """claude-respond outputs should include all claude-core output names."""
        for out in self.core["outputs"]:
            self.assertIn(
                out,
                self.respond["outputs"],
                f"claude-core output '{out}' not in claude-respond",
            )

    # --- Step structure ---

    def test_has_setup_step(self):
        step = self._get_step_by_id("setup")
        self.assertIsNotNone(step, "No step with id 'setup'")
        self.assertIn("claude-setup", step.get("uses", ""))

    def test_has_detect_intent_step(self):
        step = self._get_step_by_id("intent")
        self.assertIsNotNone(step, "No step with id 'intent'")
        self.assertIn("detect_intent.sh", step.get("run", ""))

    def test_detect_intent_is_conditional(self):
        step = self._get_step_by_id("intent")
        if_cond = step.get("if", "")
        self.assertIn("label_trigger", if_cond)
        self.assertIn("skip", if_cond)

    def test_has_core_step(self):
        step = self._get_step_by_id("core")
        self.assertIsNotNone(step, "No step with id 'core'")
        self.assertIn("claude-core", step.get("uses", ""))

    def test_core_step_is_conditional_on_skip(self):
        step = self._get_step_by_id("core")
        if_cond = step.get("if", "")
        self.assertIn("skip", if_cond)

    def test_core_step_uses_intent_outputs(self):
        """Core step should prefer intent outputs for agent/model."""
        step = self._get_step_by_id("core")
        with_block = step.get("with", {})
        self.assertIn("steps.intent.outputs.agent", with_block.get("agent_name", ""))
        self.assertIn("steps.intent.outputs.model", with_block.get("model", ""))

    def test_core_step_uses_setup_comment_id(self):
        """Core step should use tracking comment from setup."""
        step = self._get_step_by_id("core")
        with_block = step.get("with", {})
        self.assertIn(
            "steps.setup.outputs.comment_id",
            with_block.get("issue_comment_id", ""),
        )

    def test_has_report_step(self):
        report_steps = [
            s for s in self.respond["runs"]["steps"] if "claude-report" in s.get("uses", "")
        ]
        self.assertEqual(len(report_steps), 1, "Expected exactly one report step")

    def test_report_step_has_if_always(self):
        report_step = self._find_step_by_uses("claude-report")
        self.assertIn("always()", report_step.get("if", ""))

    def test_report_step_receives_execution_file(self):
        report_step = self._find_step_by_uses("claude-report")
        with_block = report_step.get("with", {})
        self.assertIn("execution_file", with_block)
        self.assertIn("steps.core.outputs.execution_file", with_block["execution_file"])

    def test_report_step_receives_outcome(self):
        report_step = self._find_step_by_uses("claude-report")
        with_block = report_step.get("with", {})
        self.assertIn("outcome", with_block)
        self.assertIn("steps.core.outcome", with_block["outcome"])

    def test_setup_step_forwards_orchestration_inputs(self):
        """Setup step should forward orchestration inputs."""
        step = self._get_step_by_id("setup")
        with_block = step.get("with", {})
        for inp in ["tracking_comment", "reaction_emoji", "checkout", "checkout_ref",
                     "checkout_fetch_depth", "pre_run"]:
            self.assertIn(
                inp,
                with_block,
                f"Setup step missing orchestration input '{inp}'",
            )

    def test_no_secrets_in_defaults(self):
        for name, inp in self.respond["inputs"].items():
            default = inp.get("default", "")
            if default:
                self.assertNotIn("sk-", str(default), f"Input '{name}' default looks like a secret")

    # --- Helpers ---

    def _get_step_by_id(self, step_id):
        for step in self.respond["runs"]["steps"]:
            if step.get("id") == step_id:
                return step
        return None

    def _find_step_by_uses(self, uses_substring):
        for step in self.respond["runs"]["steps"]:
            if uses_substring in step.get("uses", ""):
                return step
        return None


if __name__ == "__main__":
    unittest.main()
