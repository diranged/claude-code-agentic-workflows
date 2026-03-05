#!/usr/bin/env bash
# Compose a full prompt from instructions, skills, agent definition, and runtime context.
#
# Reads markdown files from:
#   1. $ACTION_PATH/instructions/*.md  (sorted)
#   2. $EXTRA_INSTRUCTIONS_PATH/*.md  (extra instructions, sorted)
#   3. $WORKSPACE_PATH/.github/claude-instructions/*.md  (user overrides, sorted)
#   4. $ACTION_PATH/skills/*.md  (sorted)
#   5. $WORKSPACE_PATH/.github/claude-skills/*.md  (user overrides, sorted)
#   6. Agent file: user override, extra path, or built-in
#   7. Runtime context (run ID, issue number, etc.)
#   8. PROMPT_TEXT as "Task Context"
#
# Required env: ACTION_PATH, WORKSPACE_PATH, AGENT_NAME
# Optional env: EXTRA_INSTRUCTIONS_PATH, EXTRA_AGENTS_PATH, PROMPT_TEXT, ISSUE_NUMBER, COMMENT_ID, RUN_ID, RUN_URL, GITHUB_REPOSITORY, NOTIFY_OWNERS
set -euo pipefail

PROMPT=""

append_section() {
  local content="$1"
  if [ -n "$content" ]; then
    PROMPT="${PROMPT}${content}"$'\n\n'
  fi
}

# Load all .md files from a directory (sorted), if it exists
load_dir() {
  local dir="$1"
  if [ -d "$dir" ]; then
    for f in "$dir"/*.md; do
      [ -f "$f" ] || continue
      append_section "$(cat "$f")"
    done
  fi
}

# --- 1. Base instructions ---
load_dir "${ACTION_PATH}/instructions"

# --- 2. Extra instructions (from caller, e.g. claude-engineer) ---
if [ -n "${EXTRA_INSTRUCTIONS_PATH:-}" ]; then
  load_dir "${EXTRA_INSTRUCTIONS_PATH}"
fi

# --- 3. User instruction overrides ---
load_dir "${WORKSPACE_PATH}/.github/claude-instructions"

# --- 4. Skills ---
load_dir "${ACTION_PATH}/skills"

# --- 5. User skill overrides ---
load_dir "${WORKSPACE_PATH}/.github/claude-skills"

# --- 6. Agent definition ---
if [ -n "${AGENT_NAME:-}" ]; then
  AGENT_FILE=""
  USER_AGENT="${WORKSPACE_PATH}/.github/claude-agents/${AGENT_NAME}.md"
  EXTRA_AGENT="${EXTRA_AGENTS_PATH:+${EXTRA_AGENTS_PATH}/${AGENT_NAME}.md}"
  BUILTIN_AGENT="${ACTION_PATH}/agents/${AGENT_NAME}.md"

  if [ -f "$USER_AGENT" ]; then
    AGENT_FILE="$USER_AGENT"
  elif [ -n "$EXTRA_AGENT" ] && [ -f "$EXTRA_AGENT" ]; then
    AGENT_FILE="$EXTRA_AGENT"
  elif [ -f "$BUILTIN_AGENT" ]; then
    AGENT_FILE="$BUILTIN_AGENT"
  else
    echo "::error::Agent '${AGENT_NAME}' not found in ${BUILTIN_AGENT} or ${USER_AGENT}"
    exit 1
  fi

  append_section "$(cat "$AGENT_FILE")"
fi

# --- 7. Runtime context ---
CONTEXT="## Runtime Context"$'\n'
if [ -n "${RUN_ID:-}" ]; then
  CONTEXT="${CONTEXT}- Run ID: ${RUN_ID}"$'\n'
fi
if [ -n "${RUN_URL:-}" ]; then
  CONTEXT="${CONTEXT}- Run URL: ${RUN_URL}"$'\n'
fi
if [ -n "${ISSUE_NUMBER:-}" ]; then
  CONTEXT="${CONTEXT}- Issue Number: ${ISSUE_NUMBER}"$'\n'
fi
if [ -n "${COMMENT_ID:-}" ]; then
  CONTEXT="${CONTEXT}- Tracking Comment ID: ${COMMENT_ID}"$'\n'
fi
if [ -n "${GITHUB_REPOSITORY:-}" ]; then
  CONTEXT="${CONTEXT}- Repository: ${GITHUB_REPOSITORY}"$'\n'
fi
if [ -n "${NOTIFY_OWNERS:-}" ]; then
  CONTEXT="${CONTEXT}- Notify Owners: ${NOTIFY_OWNERS}"$'\n'
fi
append_section "$CONTEXT"

# --- 8. User prompt ---
if [ -n "${PROMPT_TEXT:-}" ]; then
  append_section "## Task Context
${PROMPT_TEXT}"
fi

echo "prompt<<COMPOSED_EOF" >> "$GITHUB_OUTPUT"
echo "$PROMPT" >> "$GITHUB_OUTPUT"
echo "COMPOSED_EOF" >> "$GITHUB_OUTPUT"
