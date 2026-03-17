"""Tests for internal repo workflow files.

Validates that repo-* workflows use composite actions directly
(not shared reusable workflows) and have the correct structure.
"""

import os
import unittest

import yaml

WORKFLOWS_DIR = os.path.join(
    os.path.dirname(__file__), "..", ".github", "workflows"
)


def _load_workflow(name):
    path = os.path.join(WORKFLOWS_DIR, name)
    with open(path) as f:
        return yaml.safe_load(f)


class TestRepoClaudeResponder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = _load_workflow("repo-claude-responder.yml")

    def test_does_not_use_shared_workflow(self):
        """Should use action directly, not shared workflow."""
        for job_name, job in self.wf["jobs"].items():
            self.assertNotIn(
                "uses",
                job,
                f"Job '{job_name}' uses a reusable workflow — should use action steps instead",
            )

    def test_respond_job_uses_claude_respond_action(self):
        job = self.wf["jobs"]["respond"]
        steps = job.get("steps", [])
        action_steps = [s for s in steps if "claude-respond" in s.get("uses", "")]
        self.assertEqual(
            len(action_steps), 1,
            "Expected exactly one step using claude-respond action",
        )

    def test_respond_job_has_permissions(self):
        job = self.wf["jobs"]["respond"]
        perms = job.get("permissions", {})
        self.assertEqual(perms.get("contents"), "write")
        self.assertEqual(perms.get("issues"), "write")
        self.assertEqual(perms.get("pull-requests"), "write")

    def test_respond_job_has_runs_on(self):
        job = self.wf["jobs"]["respond"]
        self.assertIn("runs-on", job)

    def test_has_checkout_before_action(self):
        """Local ./ action references require the repo to be checked out first."""
        job = self.wf["jobs"]["respond"]
        steps = job.get("steps", [])
        checkout_steps = [s for s in steps if "checkout" in s.get("uses", "")]
        self.assertEqual(len(checkout_steps), 1)

    def test_no_secrets_block(self):
        """Composite action pattern doesn't need a secrets block."""
        for job_name, job in self.wf["jobs"].items():
            self.assertNotIn(
                "secrets",
                job,
                f"Job '{job_name}' has a secrets block — not needed with composite actions",
            )

    def test_passes_oauth_token(self):
        job = self.wf["jobs"]["respond"]
        step = [s for s in job["steps"] if "claude-respond" in s.get("uses", "")][0]
        with_block = step.get("with", {})
        self.assertIn("claude_code_oauth_token", with_block)
        self.assertIn("secrets.CLAUDE_OAUTH_TOKEN", with_block["claude_code_oauth_token"])


class TestRepoClaudeEngineers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = _load_workflow("repo-claude-engineers.yml")

    def test_does_not_use_shared_workflow(self):
        for job_name, job in self.wf["jobs"].items():
            self.assertNotIn(
                "uses",
                job,
                f"Job '{job_name}' uses a reusable workflow",
            )

    def test_no_ci_retry_job(self):
        """CI retry has been removed."""
        self.assertNotIn("ci-retry", self.wf["jobs"])

    def test_no_workflow_run_trigger(self):
        """workflow_run trigger (used for CI retry) should be removed."""
        triggers = self.wf.get(True, {})  # 'on' key in YAML parses as True
        if isinstance(triggers, dict):
            self.assertNotIn("workflow_run", triggers)

    def test_has_checkout_before_action(self):
        """Local ./ action references require the repo to be checked out first."""
        job = self.wf["jobs"]["engineers"]
        steps = job.get("steps", [])
        checkout_steps = [s for s in steps if "checkout" in s.get("uses", "")]
        self.assertEqual(len(checkout_steps), 1)

    def test_engineers_job_uses_claude_respond_action(self):
        job = self.wf["jobs"]["engineers"]
        steps = job.get("steps", [])
        action_steps = [s for s in steps if "claude-respond" in s.get("uses", "")]
        self.assertEqual(len(action_steps), 1)

    def test_engineers_job_has_label_trigger(self):
        job = self.wf["jobs"]["engineers"]
        step = [s for s in job["steps"] if "claude-respond" in s.get("uses", "")][0]
        with_block = step.get("with", {})
        self.assertEqual(with_block.get("label_trigger"), "claude")

    def test_engineers_job_has_permissions(self):
        job = self.wf["jobs"]["engineers"]
        perms = job.get("permissions", {})
        self.assertEqual(perms.get("contents"), "write")
        self.assertEqual(perms.get("issues"), "write")


class TestRepoEngineerManagers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = _load_workflow("repo-engineer-managers.yml")

    def test_has_three_engineer_jobs(self):
        expected = ["docs-engineer", "code-janitor", "security-engineer"]
        for job in expected:
            self.assertIn(job, self.wf["jobs"], f"Missing job: {job}")

    def test_all_jobs_use_claude_engineer_action(self):
        for job_name, job in self.wf["jobs"].items():
            steps = job.get("steps", [])
            action_steps = [s for s in steps if "claude-engineer" in s.get("uses", "")]
            self.assertEqual(
                len(action_steps), 1,
                f"Job '{job_name}' should have exactly one claude-engineer step",
            )

    def test_has_checkout_before_action(self):
        """Each job must checkout the repo before using local ./claude-engineer action."""
        for job_name, job in self.wf["jobs"].items():
            steps = job.get("steps", [])
            checkout_steps = [s for s in steps if "checkout" in s.get("uses", "")]
            self.assertEqual(
                len(checkout_steps), 1,
                f"Job '{job_name}' must have a checkout step for local action reference",
            )

    def test_each_job_has_unique_dashboard_label(self):
        labels = set()
        for job_name, job in self.wf["jobs"].items():
            step = [s for s in job["steps"] if "claude-engineer" in s.get("uses", "")][0]
            label = step["with"].get("dashboard_label")
            self.assertIsNotNone(label, f"Job '{job_name}' missing dashboard_label")
            self.assertNotIn(label, labels, f"Duplicate dashboard_label: {label}")
            labels.add(label)

    def test_no_shared_workflow_references(self):
        """No job should reference shared-*.yml workflows."""
        for job_name, job in self.wf["jobs"].items():
            uses = job.get("uses", "")
            self.assertNotIn("shared-", uses, f"Job '{job_name}' references shared workflow")


class TestSharedWorkflowsDeleted(unittest.TestCase):
    def test_no_shared_claude_responder(self):
        path = os.path.join(WORKFLOWS_DIR, "shared-claude-responder.yml")
        self.assertFalse(
            os.path.exists(path),
            "shared-claude-responder.yml should be deleted",
        )

    def test_no_shared_claude_engineers(self):
        path = os.path.join(WORKFLOWS_DIR, "shared-claude-engineers.yml")
        self.assertFalse(
            os.path.exists(path),
            "shared-claude-engineers.yml should be deleted",
        )


if __name__ == "__main__":
    unittest.main()
