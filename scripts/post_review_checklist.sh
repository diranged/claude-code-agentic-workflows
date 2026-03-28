#!/bin/bash

# Review Checklist Commenter
# Posts a review checklist comment on newly opened pull requests
#
# Usage:
#   post_review_checklist.sh [PR_NUMBER]
#
# Environment Variables:
#   PR_NUMBER         - Pull request number (alternative to first argument)
#   CHECKLIST_FILE    - Path to custom checklist file (default: .github/review-checklist.md)
#   GH_TOKEN          - GitHub token (usually set automatically in Actions)
#
# Behavior:
#   - Reads checklist content from CHECKLIST_FILE or uses default
#   - Only posts if no "## Review Checklist" comment already exists (idempotent)
#   - Posts comment as current authenticated user/bot

set -euo pipefail

# Get PR number from argument or environment
PR_NUMBER="${1:-${PR_NUMBER:-}}"

if [[ -z "$PR_NUMBER" ]]; then
    echo "Error: PR number required as argument or PR_NUMBER env var" >&2
    echo "Usage: $0 [PR_NUMBER]" >&2
    exit 1
fi

# Validate PR_NUMBER is a positive integer (prevent command injection)
if [[ ! "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "Error: PR_NUMBER must be a positive integer (got: '$PR_NUMBER')" >&2
    exit 1
fi

# Default checklist content
DEFAULT_CHECKLIST="## Review Checklist
- [ ] Code follows existing patterns and conventions
- [ ] Tests are included for new functionality
- [ ] No secrets or credentials in the diff
- [ ] CI passes"

# Get checklist content from file or use default
CHECKLIST_FILE="${CHECKLIST_FILE:-.github/review-checklist.md}"

# Path traversal guard: validate file is within workspace
resolved_path=$(realpath "$CHECKLIST_FILE" 2>/dev/null || echo "")
workspace_root=$(realpath "${GITHUB_WORKSPACE:-.}" 2>/dev/null || realpath "." 2>/dev/null)

# Security check: ensure file is within workspace
if [[ -n "$resolved_path" && "$resolved_path" == "$workspace_root"/* ]] && [[ -f "$resolved_path" ]]; then
    echo "Using custom checklist from $CHECKLIST_FILE"
    checklist_content=$(cat "$resolved_path")
elif [[ -n "$resolved_path" && "$resolved_path" != "$workspace_root"/* ]]; then
    echo "Error: Checklist file must be within the workspace directory" >&2
    echo "Using default checklist for security" >&2
    checklist_content="$DEFAULT_CHECKLIST"
elif [[ -f "$CHECKLIST_FILE" ]]; then
    # realpath failed but file exists - fall back to direct read for simple relative paths
    echo "Using custom checklist from $CHECKLIST_FILE"
    checklist_content=$(cat "$CHECKLIST_FILE")
else
    echo "Using default checklist (no custom file found at $CHECKLIST_FILE)"
    checklist_content="$DEFAULT_CHECKLIST"
fi

# Check if a review checklist comment already exists
echo "Checking for existing review checklist comment on PR #$PR_NUMBER..."
comments_json=$(gh pr view "$PR_NUMBER" --json comments)
existing_comment=$(echo "$comments_json" | jq -r '.comments | map(select(.body | contains("## Review Checklist"))) | .[0].id // empty' 2>/dev/null || true)

if [[ -n "$existing_comment" ]]; then
    echo "Review checklist comment already exists (comment ID: $existing_comment)"
    echo "Skipping to avoid duplicates"
    exit 0
fi

# Content validation: check size limit
if [[ ${#checklist_content} -gt 65536 ]]; then
    echo "Error: Checklist content exceeds maximum size (64KB)" >&2
    exit 1
fi

# Post the checklist comment
echo "Posting review checklist comment on PR #$PR_NUMBER..."
gh pr comment "$PR_NUMBER" --body "$checklist_content"

echo "✓ Review checklist posted on PR #$PR_NUMBER"