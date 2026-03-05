#!/usr/bin/env bash
# Label-based duplicate issue detection for dashboard creation
set -euo pipefail

# Required environment variables
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "::error::GITHUB_TOKEN is required for duplicate issue detection"
  exit 1
fi

if [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "::error::GITHUB_REPOSITORY is required for duplicate issue detection"
  exit 1
fi

if [ -z "${DASHBOARD_LABEL:-}" ]; then
  echo "::warning::No dashboard_label provided, skipping duplicate check"
  echo "duplicate=false"
  echo "existing_issue_number="
  exit 0
fi

# Query GitHub API for open issues with the dashboard label
API_URL="https://api.github.com/repos/${GITHUB_REPOSITORY}/issues?labels=${DASHBOARD_LABEL}&state=open&per_page=1"

# Use curl to query the API
RESPONSE=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "$API_URL" 2>/dev/null || echo "[]")

# Parse response with python3 to check if any issues exist
RESULT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    issues = json.load(sys.stdin)
    if isinstance(issues, list) and len(issues) > 0:
        print(f'duplicate=true')
        print(f'existing_issue_number={issues[0][\"number\"]}')
    else:
        print('duplicate=false')
        print('existing_issue_number=')
except Exception as e:
    print('duplicate=false', file=sys.stderr)
    print('existing_issue_number=', file=sys.stderr)
    print(f'Warning: Failed to parse API response: {e}', file=sys.stderr)
" 2>/dev/null)

# Output the result
if [ -n "$RESULT" ]; then
  echo "$RESULT"
else
  echo "::warning::Failed to check for duplicate issues, proceeding with creation"
  echo "duplicate=false"
  echo "existing_issue_number="
fi