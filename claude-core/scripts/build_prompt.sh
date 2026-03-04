#!/usr/bin/env bash
# Build prompt output from PROMPT_TEXT env var
set -euo pipefail

PROMPT=""
if [ -n "${PROMPT_TEXT:-}" ]; then
  PROMPT="$PROMPT_TEXT"
fi

echo "prompt<<EOF" >> "$GITHUB_OUTPUT"
echo "$PROMPT" >> "$GITHUB_OUTPUT"
echo "EOF" >> "$GITHUB_OUTPUT"
