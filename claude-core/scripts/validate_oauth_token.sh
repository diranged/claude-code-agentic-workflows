#!/usr/bin/env bash
# OAuth token expiry detection for Claude Code tokens
set -euo pipefail

# Exit early if no OAuth token provided
if [ -z "${OAUTH_TOKEN:-}" ]; then
  exit 0
fi

# Claude Code OAuth tokens are JWTs. Attempt to decode and check expiry.
# If token is not a JWT or decode fails, skip validation (let upstream auth handle it)

# Check if token has JWT structure (3 parts separated by dots)
if [[ ! "$OAUTH_TOKEN" =~ ^[^.]+\.[^.]+\.[^.]+$ ]]; then
  # Not a JWT structure, skip expiry check
  exit 0
fi

# Extract payload (middle segment) and decode from base64url
PAYLOAD=$(echo "$OAUTH_TOKEN" | cut -d. -f2 | tr '_-' '/+')

# Add padding if needed (base64 requires padding)
case $((${#PAYLOAD} % 4)) in
  1) PAYLOAD="${PAYLOAD}===" ;;
  2) PAYLOAD="${PAYLOAD}==" ;;
  3) PAYLOAD="${PAYLOAD}=" ;;
esac

# Decode the payload
DECODED=$(echo "$PAYLOAD" | base64 -d 2>/dev/null || echo "")

# If decode failed, skip expiry check
if [ -z "$DECODED" ]; then
  exit 0
fi

# Extract exp claim using python3 (always available on GitHub runners)
EXP=$(echo "$DECODED" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('exp', ''))
except:
    print('')
" 2>/dev/null)

# If no exp claim found, skip check
if [ -z "$EXP" ]; then
  exit 0
fi

# Get current time
NOW=$(date +%s)

# Check if token is expired
if [ "$EXP" -lt "$NOW" ]; then
  EXPIRE_DATE=$(date -d "@$EXP" 2>/dev/null || echo "unknown date")
  echo "::error::OAuth token has expired (expired at $EXPIRE_DATE). Run 'claude setup-token' to refresh."
  exit 1
fi

# Check if token expires within 5 minutes (300 seconds) and warn
FIVE_MINUTES_FROM_NOW=$((NOW + 300))
if [ "$EXP" -lt "$FIVE_MINUTES_FROM_NOW" ]; then
  MINUTES_REMAINING=$(((EXP - NOW) / 60))
  echo "::warning::OAuth token expires in $MINUTES_REMAINING minutes. Consider refreshing with 'claude setup-token'."
fi