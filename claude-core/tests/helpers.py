"""Shared test helpers for claude-core script tests."""

import os
import sys

# Add the repo root tests/ directory to sys.path for shared_helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tests"))

from shared_helpers import make_run_script, parse_github_output  # noqa: E402

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

_CLEARED_VARS = [
    "APP_TOKEN",
    "EXPLICIT_TOKEN",
    "OAUTH_TOKEN",
    "API_KEY",
    "APP_ID",
    "APP_PRIVATE_KEY",
    "TIMEOUT_MINUTES",
    "COMPOSE_PROMPT",
    "MODEL",
    "MAX_TURNS",
    "ALLOWED_TOOLS",
    "DISALLOWED_TOOLS",
    "EXTRA_ARGS",
    "COMMENT_BODY",
    "TRIGGER_LABEL",
    "PROMPT_TEXT",
    "ACTION_PATH",
    "WORKSPACE_PATH",
    "AGENT_NAME",
    "EXTRA_INSTRUCTIONS_PATH",
    "EXTRA_AGENTS_PATH",
    "NOTIFY_OWNERS",
    "ISSUE_NUMBER",
    "COMMENT_ID",
    "RUN_ID",
    "RUN_URL",
    "GITHUB_OUTPUT",
]

run_script = make_run_script(SCRIPTS_DIR, _CLEARED_VARS)
