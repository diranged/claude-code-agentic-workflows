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
  BUILTIN_AGENT="${ACTION_PATH:-.}/agents/${AGENT_NAME}.md"
  if [ ! -f "$USER_AGENT" ] && [ ! -f "$BUILTIN_AGENT" ]; then
    echo "::error::Agent '${AGENT_NAME}' not found in agents/ or .github/claude-agents/"
    exit 1
  fi
fi

# Auth method notice (preserved from validate_claude_auth.sh)
if [ -n "${OAUTH_TOKEN:-}" ]; then
  echo "::notice::Using Claude Code OAuth token (subscription billing)"
else
  echo "::notice::Using Anthropic API key (per-token billing)"
fi