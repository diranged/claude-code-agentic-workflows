#!/usr/bin/env bash
# Validate that at least one Claude authentication method is provided
set -euo pipefail

if [ -z "${OAUTH_TOKEN:-}" ] && [ -z "${API_KEY:-}" ]; then
  echo "::error::No Claude authentication provided. Set either 'claude_code_oauth_token' (recommended) or 'anthropic_api_key'."
  exit 1
fi

if [ -n "${OAUTH_TOKEN:-}" ]; then
  echo "::notice::Using Claude Code OAuth token (subscription billing)"
else
  echo "::notice::Using Anthropic API key (per-token billing)"
fi
