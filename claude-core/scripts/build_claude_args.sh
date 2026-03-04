#!/usr/bin/env bash
# Build claude_args from structured inputs (always appends --verbose)
set -euo pipefail

ARGS=""

if [ -n "${MODEL:-}" ]; then
  ARGS="$ARGS --model $MODEL"
fi

if [ -n "${MAX_TURNS:-}" ]; then
  ARGS="$ARGS --max-turns $MAX_TURNS"
fi

if [ -n "${ALLOWED_TOOLS:-}" ]; then
  ARGS="$ARGS --allowedTools $ALLOWED_TOOLS"
fi

if [ -n "${DISALLOWED_TOOLS:-}" ]; then
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
