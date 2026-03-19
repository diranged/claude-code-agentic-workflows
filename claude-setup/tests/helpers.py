"""Shared test helpers for claude-setup script tests."""

import os
import sys

# Add the repo root tests/ directory to sys.path for shared_helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tests"))

from shared_helpers import make_run_script, parse_github_output  # noqa: E402

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

_CLEARED_VARS = [
    "EVENT_NAME",
    "EVENT_ACTION",
    "ASSIGNEE_LOGIN",
    "ASSIGNEE_TRIGGER",
    "LABEL_NAME",
    "LABEL_TRIGGER",
    "COMMENT_BODY",
    "TRIGGER_PHRASE",
    "GH_TOKEN",
    "ISSUE_NUMBER",
    "COMMENT_ID",
    "REACTION_EMOJI",
    "CREATE_TRACKING_COMMENT",
    "RUN_URL",
    "GITHUB_REPOSITORY",
    "APP_TOKEN",
    "EXPLICIT_TOKEN",
    "GITHUB_OUTPUT",
]

run_script = make_run_script(SCRIPTS_DIR, _CLEARED_VARS)
