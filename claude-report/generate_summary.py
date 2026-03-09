#!/usr/bin/env python3
"""Generate a GitHub-flavored markdown execution summary from Claude Code output.

Reads a Claude Code execution JSON file and writes a summary table to stdout.
Designed to be called from a GitHub Actions composite action and redirected
to $GITHUB_STEP_SUMMARY.

Usage:
    python3 generate_summary.py \
        --execution-file <path> \
        --session-id <id> \
        --outcome success|failure
"""

import argparse
import json
import os
import sys
from collections import defaultdict


def parse_execution(data):
    """Extract metrics from a list of execution turns.

    Returns a dict with keys: duration_ms, num_turns, total_cost_usd,
    and model_usage (dict of model -> {input, output, cache_read, cache_create}).
    """
    result_turn = None
    for turn in data:
        if turn.get("type") == "result":
            result_turn = turn
            break

    duration_ms = 0
    num_turns = "?"
    total_cost_usd = 0.0
    if result_turn:
        duration_ms = result_turn.get("duration_ms", 0) or 0
        num_turns = result_turn.get("num_turns", "?")
        total_cost_usd = result_turn.get("total_cost_usd", 0) or 0

    # Group token usage by model
    model_usage = defaultdict(lambda: {
        "input": 0, "output": 0, "cache_read": 0, "cache_create": 0,
    })
    for turn in data:
        model = turn.get("model")
        usage = turn.get("usage")
        if model and usage:
            m = model_usage[model]
            m["input"] += usage.get("input_tokens", 0) or 0
            m["output"] += usage.get("output_tokens", 0) or 0
            m["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
            m["cache_create"] += usage.get("cache_creation_input_tokens", 0) or 0

    return {
        "duration_ms": duration_ms,
        "num_turns": num_turns,
        "total_cost_usd": total_cost_usd,
        "model_usage": dict(model_usage),
    }


def format_duration(ms):
    """Format milliseconds as seconds with one decimal place."""
    return f"{ms / 1000:.1f}s"


def format_cost(cost):
    """Format cost as $X.XXXX."""
    return f"${cost:.4f}"


def validate_file_path(file_path):
    """Validate that file_path is within an allowed directory.

    Allowed directories (from environment variables):
    - GITHUB_WORKSPACE (repository checkout)
    - RUNNER_TEMP (temporary files)
    - GITHUB_ACTION_PATH (action directory)

    Falls back to current working directory if no env vars are set.
    Returns the resolved absolute path, or raises ValueError.
    """
    abs_file = os.path.realpath(file_path)

    allowed_dirs = []
    for env_var in ("GITHUB_WORKSPACE", "RUNNER_TEMP", "GITHUB_ACTION_PATH"):
        val = os.environ.get(env_var)
        if val:
            allowed_dirs.append(os.path.realpath(val))

    # Fallback: allow current working directory
    if not allowed_dirs:
        allowed_dirs.append(os.path.realpath("."))

    for allowed in allowed_dirs:
        # Use os.sep to prevent prefix matching attacks (e.g., /tmp vs /tmp2)
        if abs_file == allowed or abs_file.startswith(allowed + os.sep):
            return abs_file

    raise ValueError(
        f"File path '{file_path}' resolves to '{abs_file}' which is outside "
        f"allowed directories: {allowed_dirs}"
    )


def generate_summary(execution_file, session_id, outcome):
    """Generate the full markdown summary and return it as a string."""
    status = "\u2705 Success" if outcome == "success" else "\u274c Failed"
    lines = []

    # Try to load and parse the execution file
    data = None
    if execution_file:
        try:
            validated_path = validate_file_path(execution_file)
            with open(validated_path) as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = None
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            data = None

    if data is None:
        # Minimal fallback summary
        lines.append("## Claude Execution Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Status | {status} |")
        lines.append(f"| Session ID | `{session_id}` |")
        lines.append("")
        lines.append("> No execution file found \u2014 detailed metrics unavailable.")
        lines.append("")
        return "\n".join(lines)

    metrics = parse_execution(data)

    lines.append("## Claude Execution Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Status | {status} |")
    lines.append(f"| Duration | {format_duration(metrics['duration_ms'])} |")
    lines.append(f"| Turns | {metrics['num_turns']} |")
    if metrics["total_cost_usd"] > 0:
        lines.append(f"| Cost | {format_cost(metrics['total_cost_usd'])} |")
    lines.append(f"| Session ID | `{session_id}` |")
    lines.append("")
    lines.append("### Token Usage by Model")
    lines.append("")
    lines.append("| Model | Input | Output | Cache Read | Cache Create |")
    lines.append("|-------|------:|-------:|-----------:|-------------:|")

    if metrics["model_usage"]:
        for model in sorted(metrics["model_usage"]):
            u = metrics["model_usage"][model]
            lines.append(
                f"| {model}"
                f" | {u['input']:,}"
                f" | {u['output']:,}"
                f" | {u['cache_read']:,}"
                f" | {u['cache_create']:,} |"
            )
    else:
        lines.append("| _unknown_ | 0 | 0 | 0 | 0 |")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Claude Code execution summary markdown.",
    )
    parser.add_argument("--execution-file", required=True, help="Path to execution JSON file")
    parser.add_argument("--session-id", default="", help="Session ID to display")
    parser.add_argument("--outcome", default="success", choices=["success", "failure"],
                        help="Execution outcome")
    args = parser.parse_args()

    try:
        output = generate_summary(args.execution_file, args.session_id, args.outcome)
        print(output)
    except Exception:
        # Summary generation should never fail the build
        print("## Claude Execution Summary\n")
        print("> Summary generation encountered an error.\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
