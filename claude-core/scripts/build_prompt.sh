#!/usr/bin/env bash
# Build Prompt Output
# Reads a prompt from the PROMPT_TEXT environment variable and writes it
# as a multiline GitHub Actions output named "prompt".
#
# Usage:
#   Called as a step in the claude-core composite action after prompt
#   text has been determined (either raw or composed).
#
# Environment Variables:
#   PROMPT_TEXT      - The prompt text to output (optional, defaults to empty)
#   GITHUB_OUTPUT   - GitHub Actions output file (set automatically)
#
# Output:
#   Sets the "prompt" output variable via GITHUB_OUTPUT using heredoc delimiter.
#
# Exit Codes:
#   0 - Success
#   1 - Failure (pipefail from unset GITHUB_OUTPUT or write error)
set -euo pipefail

PROMPT=""
if [ -n "${PROMPT_TEXT:-}" ]; then
  PROMPT="$PROMPT_TEXT"
fi

echo "prompt<<EOF" >> "$GITHUB_OUTPUT"
echo "$PROMPT" >> "$GITHUB_OUTPUT"
echo "EOF" >> "$GITHUB_OUTPUT"
