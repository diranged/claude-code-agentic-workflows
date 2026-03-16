#!/usr/bin/env bash
# detect_intent.sh — Route label to agent/model pair.
#
# Reads LABEL_NAME and DEFAULT_AGENT env vars.
# Writes agent, model, and skip to $GITHUB_OUTPUT.

set -euo pipefail

label="${LABEL_NAME:-}"
default_agent="${DEFAULT_AGENT:-agentic-designer}"
default_model="${DEFAULT_MODEL:-claude-opus-4-20250514}"

# --- Label-based routing ---
case "$label" in
  claude:implement)
    echo "agent=agentic-developer" >> "$GITHUB_OUTPUT"
    echo "model=claude-sonnet-4-20250514" >> "$GITHUB_OUTPUT"
    ;;
  claude:design)
    echo "agent=agentic-designer" >> "$GITHUB_OUTPUT"
    echo "model=claude-opus-4-20250514" >> "$GITHUB_OUTPUT"
    ;;
  claude:review)
    echo "agent=architect" >> "$GITHUB_OUTPUT"
    echo "model=claude-opus-4-20250514" >> "$GITHUB_OUTPUT"
    ;;
  claude:auto_advance|claude:queued)
    echo "skip=true" >> "$GITHUB_OUTPUT"
    echo "Skipping execution for modifier label: $label" >&2
    ;;
  claude:*)
    echo "agent=${default_agent}" >> "$GITHUB_OUTPUT"
    echo "model=${default_model}" >> "$GITHUB_OUTPUT"
    ;;
  *)
    # Non-claude label — use defaults
    echo "agent=${default_agent}" >> "$GITHUB_OUTPUT"
    echo "model=${default_model}" >> "$GITHUB_OUTPUT"
    ;;
esac
