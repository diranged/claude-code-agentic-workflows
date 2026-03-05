#!/usr/bin/env bash
# Unified input validation for claude-core composite action
set -euo pipefail

# 1. Claude auth: either OAUTH_TOKEN or API_KEY must be non-empty
if [ -z "${OAUTH_TOKEN:-}" ] && [ -z "${API_KEY:-}" ]; then
  echo "::error::Either claude_code_oauth_token or anthropic_api_key must be provided"
  exit 1
fi

# 2. App credentials must be paired
if [ -n "${APP_ID:-}" ] && [ -z "${APP_PRIVATE_KEY:-}" ]; then
  echo "::error::app_id and app_private_key must both be provided together"
  exit 1
fi
if [ -z "${APP_ID:-}" ] && [ -n "${APP_PRIVATE_KEY:-}" ]; then
  echo "::error::app_id and app_private_key must both be provided together"
  exit 1
fi

# 3. Timeout must be a positive integer
if [ -n "${TIMEOUT_MINUTES:-}" ]; then
  if ! [[ "$TIMEOUT_MINUTES" =~ ^[1-9][0-9]*$ ]]; then
    echo "::error::timeout_minutes must be a positive integer, got '${TIMEOUT_MINUTES}'"
    exit 1
  fi
fi

# 4. compose_prompt=true requires agent_name
if [ "${COMPOSE_PROMPT:-}" = "true" ] && [ -z "${AGENT_NAME:-}" ]; then
  echo "::error::agent_name is required when compose_prompt is true"
  exit 1
fi

# 5. Agent file must exist (when compose_prompt=true and agent_name is set)
if [ "${COMPOSE_PROMPT:-}" = "true" ] && [ -n "${AGENT_NAME:-}" ]; then
  USER_AGENT="${WORKSPACE_PATH:-.}/.github/claude-agents/${AGENT_NAME}.md"
  EXTRA_AGENT="${EXTRA_AGENTS_PATH:+${EXTRA_AGENTS_PATH}/${AGENT_NAME}.md}"
  BUILTIN_AGENT="${ACTION_PATH:-.}/agents/${AGENT_NAME}.md"
  if [ ! -f "$USER_AGENT" ] && { [ -z "$EXTRA_AGENT" ] || [ ! -f "$EXTRA_AGENT" ]; } && [ ! -f "$BUILTIN_AGENT" ]; then
    echo "::error::Agent '${AGENT_NAME}' not found in agents/, extra_agents_path, or .github/claude-agents/"
    exit 1
  fi
fi

# 6. OAuth token expiry check (when OAuth token is provided)
if [ -n "${OAUTH_TOKEN:-}" ]; then
  "${ACTION_PATH}/scripts/validate_oauth_token.sh"
fi

# 7. max_turns must be a positive integer when set
if [ -n "${MAX_TURNS:-}" ]; then
  if ! [[ "$MAX_TURNS" =~ ^[1-9][0-9]*$ ]]; then
    echo "::error::max_turns must be a positive integer, got '${MAX_TURNS}'"
    exit 1
  fi
fi

# 8. model must start with 'claude-' when set
if [ -n "${MODEL:-}" ]; then
  if ! [[ "$MODEL" =~ ^claude- ]]; then
    echo "::error::model must start with 'claude-', got '${MODEL}'"
    exit 1
  fi
fi

# 9. dry_run must be 'true', 'false', or empty
if [ -n "${DRY_RUN:-}" ]; then
  if [ "$DRY_RUN" != "true" ] && [ "$DRY_RUN" != "false" ]; then
    echo "::error::dry_run must be 'true' or 'false', got '${DRY_RUN}'"
    exit 1
  fi
fi

# Auth method notice (preserved from validate_claude_auth.sh)
if [ -n "${OAUTH_TOKEN:-}" ]; then
  echo "::notice::Using Claude Code OAuth token (subscription billing)"
else
  echo "::notice::Using Anthropic API key (per-token billing)"
fi