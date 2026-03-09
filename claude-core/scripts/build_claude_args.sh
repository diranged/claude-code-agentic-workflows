#!/usr/bin/env bash
# Claude CLI Argument Builder
# Constructs the command-line arguments string for the Claude CLI invocation.
# Always appends --verbose for full turn-by-turn JSON output.
#
# Usage:
#   Called as a step in the claude-core composite action to build the
#   argument string before invoking the Claude CLI.
#
# Environment Variables:
#   MODEL            - Claude model to use (optional, maps to --model)
#   MAX_TURNS        - Maximum conversation turns (optional, maps to --max-turns)
#   ALLOWED_TOOLS    - Allowed tool list (optional, maps to --allowedTools)
#   DISALLOWED_TOOLS - Disallowed tool list (optional, maps to --disallowedTools)
#   EXTRA_ARGS       - Additional raw CLI arguments to append (optional)
#   GITHUB_OUTPUT    - GitHub Actions output file (set automatically)
#
# Output:
#   Sets the "args" output variable via GITHUB_OUTPUT using heredoc delimiter.
#   The --verbose flag is always included as the last argument.
#
# Exit Codes:
#   0 - Success
#   1 - Failure (pipefail from unset GITHUB_OUTPUT or write error)
set -euo pipefail

# Input validation for structured fields (defense-in-depth)
# Note: validate_inputs.sh provides format validation (MODEL must match ^claude-,
# MAX_TURNS must be positive integer), while this function provides metacharacter
# rejection for all structured fields to prevent shell injection issues.
validate_arg() {
  local name="$1" value="$2"
  if [[ "$value" =~ [\;\|\&\$\`\<\>] ]] || [[ "$value" == *$'\n'* ]]; then
    echo "ERROR: ${name} contains disallowed characters: ${value}" >&2
    exit 1
  fi
}

ARGS=""

if [ -n "${MODEL:-}" ]; then
  validate_arg "MODEL" "$MODEL"
  ARGS="$ARGS --model $MODEL"
fi

if [ -n "${MAX_TURNS:-}" ]; then
  validate_arg "MAX_TURNS" "$MAX_TURNS"
  ARGS="$ARGS --max-turns $MAX_TURNS"
fi

if [ -n "${ALLOWED_TOOLS:-}" ]; then
  validate_arg "ALLOWED_TOOLS" "$ALLOWED_TOOLS"
  ARGS="$ARGS --allowedTools $ALLOWED_TOOLS"
fi

if [ -n "${DISALLOWED_TOOLS:-}" ]; then
  validate_arg "DISALLOWED_TOOLS" "$DISALLOWED_TOOLS"
  ARGS="$ARGS --disallowedTools $DISALLOWED_TOOLS"
fi

# Append any additional raw claude_args
if [ -n "${EXTRA_ARGS:-}" ]; then
  ARGS="$ARGS $EXTRA_ARGS"
fi

# Always append --verbose for full turn-by-turn JSON output
ARGS="$ARGS --verbose"

echo "args<<EOF" >> "$GITHUB_OUTPUT"
echo "$ARGS" >> "$GITHUB_OUTPUT"
echo "EOF" >> "$GITHUB_OUTPUT"
