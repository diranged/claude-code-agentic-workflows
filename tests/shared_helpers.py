"""Shared test helpers for all action script tests."""

import os
import subprocess
import tempfile


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


def make_run_script(scripts_dir, cleared_vars):
    """Return a run_script function bound to the given scripts dir and cleared vars."""
    def run_script(script_name, env_vars=None):
        """Run a shell script with the given env vars and a temp GITHUB_OUTPUT.

        Returns ``(returncode, stdout, stderr, outputs_dict)``.
        """
        script_path = os.path.join(scripts_dir, script_name)

        # Build a clean environment
        clean_env = os.environ.copy()
        for var in cleared_vars:
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
    return run_script