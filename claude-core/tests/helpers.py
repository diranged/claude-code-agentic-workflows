"""Shared test helpers for claude-core script tests."""

import os
import subprocess
import tempfile

# Directory containing the shell scripts under test
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

# Env vars that scripts read — cleared before each run to prevent leakage
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


def parse_github_output(path):
    """Parse a GITHUB_OUTPUT file into a dict.

    Handles both simple ``key=value`` lines and heredoc blocks::

        key<<EOF
        value line 1
        value line 2
        EOF
    """
    outputs = {}
    with open(path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line:
            # heredoc: key<<DELIMITER
            key, delimiter = line.strip().split("<<", 1)
            value_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != delimiter:
                value_lines.append(lines[i])
                i += 1
            # Join and strip the trailing newline that echo adds
            outputs[key] = "".join(value_lines).rstrip("\n")
            i += 1  # skip delimiter line
        elif "=" in line:
            key, value = line.strip().split("=", 1)
            outputs[key] = value
        else:
            i += 1
            continue
        i += 1

    return outputs


def run_script(script_name, env_vars=None):
    """Run a shell script with the given env vars and a temp GITHUB_OUTPUT.

    Returns ``(returncode, stdout, stderr, outputs_dict)``.
    """
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    # Build a clean environment
    clean_env = os.environ.copy()
    for var in _CLEARED_VARS:
        clean_env.pop(var, None)

    # Create temp file for GITHUB_OUTPUT
    fd, output_path = tempfile.mkstemp(prefix="gh_output_")
    os.close(fd)
    clean_env["GITHUB_OUTPUT"] = output_path

    # Apply caller-specified env vars
    if env_vars:
        clean_env.update(env_vars)

    try:
        result = subprocess.run(
            ["bash", script_path],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        outputs = parse_github_output(output_path)
        return result.returncode, result.stdout, result.stderr, outputs
    finally:
        os.unlink(output_path)
