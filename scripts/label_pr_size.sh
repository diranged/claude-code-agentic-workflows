#!/bin/bash

# PR Size Labeler
# Automatically labels pull requests based on the number of changed lines
#
# Usage:
#   label_pr_size.sh [PR_NUMBER]
#
# Environment Variables:
#   PR_NUMBER      - Pull request number (alternative to first argument)
#   PR_ADDITIONS   - Number of line additions (for testing, skips gh query)
#   PR_DELETIONS   - Number of line deletions (for testing, skips gh query)
#   GH_TOKEN       - GitHub token (usually set automatically in Actions)
#
# Size Labels:
#   size/XS: 0-9 lines
#   size/S:  10-29 lines
#   size/M:  30-99 lines
#   size/L:  100-499 lines
#   size/XL: 500+ lines

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

# Get line counts - use env vars if set (for testing), otherwise query GitHub
if [[ -n "${PR_ADDITIONS:-}" && -n "${PR_DELETIONS:-}" ]]; then
    echo "Using provided line counts: +$PR_ADDITIONS -$PR_DELETIONS"
    additions="$PR_ADDITIONS"
    deletions="$PR_DELETIONS"
else
    echo "Fetching PR stats for #$PR_NUMBER..."
    pr_stats=$(gh pr view "$PR_NUMBER" --json additions,deletions)
    additions=$(echo "$pr_stats" | jq -r '.additions')
    deletions=$(echo "$pr_stats" | jq -r '.deletions')
    echo "PR #$PR_NUMBER: +$additions -$deletions"
fi

# Calculate total lines changed
total_lines=$((additions + deletions))
echo "Total lines changed: $total_lines"

# Determine size label
if [[ $total_lines -le 9 ]]; then
    size_label="size/XS"
elif [[ $total_lines -le 29 ]]; then
    size_label="size/S"
elif [[ $total_lines -le 99 ]]; then
    size_label="size/M"
elif [[ $total_lines -le 499 ]]; then
    size_label="size/L"
else
    size_label="size/XL"
fi

echo "Applying label: $size_label"

# Remove all existing size labels first (ignore failures if labels don't exist)
echo "Removing existing size labels..."
gh pr edit "$PR_NUMBER" --remove-label "size/XS,size/S,size/M,size/L,size/XL" || true

# Add the new size label
echo "Adding new size label: $size_label"
gh pr edit "$PR_NUMBER" --add-label "$size_label"

echo "✓ PR #$PR_NUMBER labeled as $size_label"