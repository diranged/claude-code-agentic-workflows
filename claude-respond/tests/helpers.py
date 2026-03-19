"""Shared test helpers for claude-respond script tests."""

import os
import sys

# Add the repo root tests/ directory to sys.path for shared_helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tests"))

from shared_helpers import make_run_script, parse_github_output  # noqa: E402

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

_CLEARED_VARS = [
    "LABEL_NAME",
    "DEFAULT_AGENT",
    "DEFAULT_MODEL",
    "GITHUB_OUTPUT",
]

run_script = make_run_script(SCRIPTS_DIR, _CLEARED_VARS)
