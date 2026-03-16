"""Shared test helpers for claude-respond script tests."""

import os
import subprocess
import tempfile

# Directory containing the shell scripts under test
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

# Env vars that scripts read — cleared before each run to prevent leakage
_CLEARED_VARS = [
    "LABEL_NAME",
    "DEFAULT_AGENT",
    "DEFAULT_MODEL",
    "GITHUB_OUTPUT",
]


def parse_github_output(path):
    """Parse a GITHUB_OUTPUT file into a dict."""
    outputs = {}
    with open(path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line:
            key, delimiter = line.strip().split("<<", 1)
            value_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != delimiter:
                value_lines.append(lines[i])
                i += 1
            outputs[key] = "".join(value_lines).rstrip("\n")
            i += 1
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

    clean_env = os.environ.copy()
    for var in _CLEARED_VARS:
        clean_env.pop(var, None)

    fd, output_path = tempfile.mkstemp(prefix="gh_output_")
    os.close(fd)
    clean_env["GITHUB_OUTPUT"] = output_path

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
