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
if [ "${AGENT_NAME:-}" = "auto" ]; then
  # Dynamic agent catalog — Claude self-selects the right role
  CATALOG="# Intelligent Agent Selection"$'\n\n'
  CATALOG="${CATALOG}You have multiple specialized agent roles available. Analyze the task context at the end of this prompt and adopt the most appropriate role."$'\n\n'
  CATALOG="${CATALOG}## Available Agents"$'\n\n'

  # Collect agents with deduplication (user override > extra > built-in)
  _seen_agents=""
  _add_agent() {
    local name="$1" file="$2"
    case ",$_seen_agents," in
      *",$name,"*) return ;;
    esac
    _seen_agents="${_seen_agents}${name},"
    CATALOG="${CATALOG}---"$'\n\n'"$(cat "$file")"$'\n\n'
  }

  # User overrides first (highest priority)
  if [ -d "${WORKSPACE_PATH}/.github/claude-agents" ]; then
    for f in "${WORKSPACE_PATH}/.github/claude-agents/"*.md; do
      [ -f "$f" ] || continue
      _add_agent "$(basename "$f" .md)" "$f"
    done
  fi

  # Extra agents path (e.g., claude-engineer agents)
  if [ -n "${EXTRA_AGENTS_PATH:-}" ] && [ -d "${EXTRA_AGENTS_PATH}" ]; then
    for f in "${EXTRA_AGENTS_PATH}/"*.md; do
      [ -f "$f" ] || continue
      _add_agent "$(basename "$f" .md)" "$f"
    done
  fi

  # Built-in agents
  for f in "${ACTION_PATH}/agents/"*.md; do
    [ -f "$f" ] || continue
    _add_agent "$(basename "$f" .md)" "$f"
  done

  CATALOG="${CATALOG}---"$'\n\n'
  CATALOG="${CATALOG}## Selection Instructions"$'\n\n'
  CATALOG="${CATALOG}1. Read the task context carefully to understand the user's intent"$'\n'
  CATALOG="${CATALOG}2. Choose the single most appropriate agent role from those listed above"$'\n'
  CATALOG="${CATALOG}3. Adopt that role's behavior, constraints, and output format completely"$'\n'
  CATALOG="${CATALOG}4. If the user explicitly mentions a role (e.g., \"use the design agent\"), follow their preference"$'\n'
  CATALOG="${CATALOG}5. If the request doesn't clearly match a specialized role, default to **Agentic Developer** (the most versatile role with read/write access)"$'\n'
  CATALOG="${CATALOG}6. State which role you've adopted at the beginning of your response"$'\n'

  append_section "$CATALOG"
elif [ -n "${AGENT_NAME:-}" ]; then
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

# --- 7b. Auto-detect conventional commit config from workspace workflows ---
CC_CONFIG=""
WORKFLOWS_DIR="${WORKSPACE_PATH}/.github/workflows"
if [ -d "$WORKFLOWS_DIR" ]; then
  for wf in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
    [ -f "$wf" ] || continue
    if grep -q -E "semantic-pull-request|conventional" "$wf" 2>/dev/null; then
      CC_CONFIG="$(cat "$wf")"
      break
    fi
  done
fi
if [ -n "$CC_CONFIG" ]; then
  append_section "## Conventional Commit Configuration

The following workflow enforces conventional commit formatting on PR titles. Your PR titles and commit messages **must** conform to the types and scopes defined here:

\`\`\`yaml
${CC_CONFIG}
\`\`\`"
fi

# --- 8. User prompt ---
if [ -n "${PROMPT_TEXT:-}" ]; then
  append_section "## Task Context
${PROMPT_TEXT}"
fi

echo "prompt<<CLAUDE_PROMPT_EOF_DELIMITER_582f9b" >> "$GITHUB_OUTPUT"
echo "$PROMPT" >> "$GITHUB_OUTPUT"
echo "CLAUDE_PROMPT_EOF_DELIMITER_582f9b" >> "$GITHUB_OUTPUT"
