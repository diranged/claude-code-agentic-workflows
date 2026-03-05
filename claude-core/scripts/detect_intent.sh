#!/usr/bin/env bash
# detect_intent.sh — Determine which agent and model to use based on comment text or label.
#
# Reads COMMENT_BODY and TRIGGER_LABEL env vars, writes agent + model to $GITHUB_OUTPUT.
# Label-based routing takes priority. Comment routing uses first-match on lowercased input.

set -euo pipefail

label="${TRIGGER_LABEL:-}"

# --- Label-based routing (takes priority) ---
if [[ "$label" == "claude:implement" ]]; then
  agent="agentic-developer"
  model="claude-sonnet-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == "claude:review" ]]; then
  agent="architect"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == "claude:design" ]]; then
  agent="agentic-designer"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == claude:* ]]; then
  # Unknown claude: label — default to designer
  agent="agentic-designer"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
fi

# --- Comment-based routing ---
# No keyword matching — Claude figures out intent from the comment body.
# Default to the developer agent (most capable, can read + write).
agent="agentic-developer"
model="claude-sonnet-4-20250514"

echo "agent=${agent}" >> "$GITHUB_OUTPUT"
echo "model=${model}" >> "$GITHUB_OUTPUT"
