#!/usr/bin/env bash
# Input Validator for claude-core Composite Action
# Validates all required and conditional inputs before Claude execution begins.
# Fails fast with actionable GitHub Actions error annotations.
#
# Usage:
#   Called as the first step in the claude-core composite action to catch
#   configuration errors before any expensive operations.
#
# Environment Variables:
#   OAUTH_TOKEN      - Claude Code OAuth token (one of OAUTH_TOKEN or API_KEY required)
#   API_KEY          - Anthropic API key (one of OAUTH_TOKEN or API_KEY required)
#   APP_ID           - GitHub App ID (must be paired with APP_PRIVATE_KEY)
#   APP_PRIVATE_KEY  - GitHub App private key (must be paired with APP_ID)
#   TIMEOUT_MINUTES  - Execution timeout in minutes (must be a positive integer if set)
#   COMPOSE_PROMPT   - Whether to compose a full prompt ("true"/"false")
#   AGENT_NAME       - Agent personality name (required when COMPOSE_PROMPT=true)
#   WORKSPACE_PATH   - Repository workspace root (for user agent overrides)
#   ACTION_PATH      - Path to the claude-core action directory
#   EXTRA_AGENTS_PATH - Additional agent search path (optional)
#
# Validations Performed:
#   1. Auth: Either OAUTH_TOKEN or API_KEY must be provided
#   2. App credentials: APP_ID and APP_PRIVATE_KEY must both be present or both absent
#   3. Timeout: TIMEOUT_MINUTES must be a positive integer if set
#   4. Compose prompt: AGENT_NAME is required when COMPOSE_PROMPT=true
#   5. Agent file: Agent definition must exist in one of the search paths
#
# Exit Codes:
#   0 - All validations passed
#   1 - Validation failure (with ::error:: annotation describing the issue)
set -euo pipefail

# 1. Claude auth: either OAUTH_TOKEN or API_KEY must be non-empty
if [ -z "${OAUTH_TOKEN:-}" ] && [ -z "${API_KEY:-}" ]; then
  echo "Either claude_code_oauth_token or anthropic_api_key must be provided"
  exit 1
fi

# 2. App credentials must be paired
if [ -n "${APP_ID:-}" ] && [ -z "${APP_PRIVATE_KEY:-}" ]; then
  echo "app_id and app_private_key must both be provided together"
  exit 1
fi
if [ -z "${APP_ID:-}" ] && [ -n "${APP_PRIVATE_KEY:-}" ]; then
  echo "app_id and app_private_key must both be provided together"
  exit 1
fi

# 3. Timeout must be a positive integer
if [ -n "${TIMEOUT_MINUTES:-}" ]; then
  if ! [[ "$TIMEOUT_MINUTES" =~ ^[1-9][0-9]*$ ]]; then
    echo "timeout_minutes must be a positive integer, got '${TIMEOUT_MINUTES}'"
    exit 1
  fi
fi

# 4. compose_prompt=true requires agent_name
if [ "${COMPOSE_PROMPT:-}" = "true" ] && [ -z "${AGENT_NAME:-}" ]; then
  echo "agent_name is required when compose_prompt is true"
  exit 1
fi

# 5. Agent file must exist (when compose_prompt=true and agent_name is set)
# "auto" is a special routing mode — no agent file needed.
if [ "${COMPOSE_PROMPT:-}" = "true" ] && [ -n "${AGENT_NAME:-}" ] && [ "${AGENT_NAME}" != "auto" ]; then
  USER_AGENT="${WORKSPACE_PATH:-.}/.github/claude-agents/${AGENT_NAME}.md"
  EXTRA_AGENT="${EXTRA_AGENTS_PATH:+${EXTRA_AGENTS_PATH}/${AGENT_NAME}.md}"
  BUILTIN_AGENT="${ACTION_PATH:-.}/agents/${AGENT_NAME}.md"
  if [ ! -f "$USER_AGENT" ] && { [ -z "$EXTRA_AGENT" ] || [ ! -f "$EXTRA_AGENT" ]; } && [ ! -f "$BUILTIN_AGENT" ]; then
    echo "Agent '${AGENT_NAME}' not found in agents/, extra_agents_path, or .github/claude-agents/"
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
    echo "max_turns must be a positive integer, got '${MAX_TURNS}'"
    exit 1
  fi
fi

# 8. model must start with 'claude-' when set
if [ -n "${MODEL:-}" ]; then
  if ! [[ "$MODEL" =~ ^claude- ]]; then
    echo "model must start with 'claude-', got '${MODEL}'"
    exit 1
  fi
fi

# 9. dry_run must be 'true', 'false', or empty
if [ -n "${DRY_RUN:-}" ]; then
  if [ "$DRY_RUN" != "true" ] && [ "$DRY_RUN" != "false" ]; then
    echo "dry_run must be 'true' or 'false', got '${DRY_RUN}'"
    exit 1
  fi
fi

# Auth method notice (preserved from validate_claude_auth.sh)
if [ -n "${OAUTH_TOKEN:-}" ]; then
  echo "Using Claude Code OAuth token (subscription billing)"
else
  echo "Using Anthropic API key (per-token billing)"
fi