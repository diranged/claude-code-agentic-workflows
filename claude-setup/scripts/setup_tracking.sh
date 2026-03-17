#!/usr/bin/env bash
# setup_tracking.sh — Add reaction to triggering comment and create tracking comment.
#
# Reads env vars for event context and configuration.
# Outputs comment_id and issue_number to $GITHUB_OUTPUT.

set -euo pipefail

event_name="${EVENT_NAME:-}"
issue_number="${ISSUE_NUMBER:-}"
comment_id="${COMMENT_ID:-}"
reaction_emoji="${REACTION_EMOJI:-rocket}"
create_tracking="${CREATE_TRACKING_COMMENT:-true}"
run_url="${RUN_URL:-}"
repo="${GITHUB_REPOSITORY:-}"

# Extract issue number from event context if not provided
if [ -z "$issue_number" ]; then
  echo "::warning::No issue number available"
  echo "issue_number=" >> "$GITHUB_OUTPUT"
  echo "comment_id=" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "issue_number=${issue_number}" >> "$GITHUB_OUTPUT"

# Add reaction to triggering comment (if comment-based event)
if [ -n "$reaction_emoji" ] && [ -n "$comment_id" ]; then
  if [ "$event_name" = "issue_comment" ] || [ "$event_name" = "pull_request_review_comment" ]; then
    echo "Adding ${reaction_emoji} reaction to comment ${comment_id}"
    gh api \
      --method POST \
      "/repos/${repo}/issues/comments/${comment_id}/reactions" \
      -f content="${reaction_emoji}" 2>/dev/null || echo "::warning::Failed to add reaction"
  fi
fi

# Create tracking comment
if [ "$create_tracking" = "true" ] && [ -n "$issue_number" ]; then
  BODY='<div data-claude-tracking-comment hidden></div>'
  BODY="${BODY}"$'\n'"## Status: Initializing"
  BODY="${BODY}"$'\n\n'"**Run:** [View workflow run](${run_url})"
  BODY="${BODY}"$'\n\n'"Claude is initializing..."

  TRACKING_ID=$(gh api \
    --method POST \
    "/repos/${repo}/issues/${issue_number}/comments" \
    -f body="${BODY}" \
    --jq '.id')
  echo "comment_id=${TRACKING_ID}" >> "$GITHUB_OUTPUT"
  echo "Created tracking comment: ${TRACKING_ID}"
else
  echo "comment_id=" >> "$GITHUB_OUTPUT"
fi
