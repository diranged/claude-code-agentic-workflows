#!/usr/bin/env bash
# Resolve effective GitHub token: App token > explicit token > empty (default)
set -euo pipefail

if [ -n "${APP_TOKEN:-}" ]; then
  echo "token=$APP_TOKEN" >> "$GITHUB_OUTPUT"
  echo "::notice::Using GitHub App token for authentication"
elif [ -n "${EXPLICIT_TOKEN:-}" ]; then
  echo "token=$EXPLICIT_TOKEN" >> "$GITHUB_OUTPUT"
  echo "::notice::Using explicitly provided github_token"
else
  echo "token=" >> "$GITHUB_OUTPUT"
  echo "::notice::No explicit GitHub token — upstream action will use default GITHUB_TOKEN"
fi
