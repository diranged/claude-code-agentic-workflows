#!/usr/bin/env bash
# validate_trigger.sh — Determine if the current event should trigger a Claude run.
#
# Reads env vars for event context and trigger configuration.
# Outputs skip=true/false to $GITHUB_OUTPUT.

set -euo pipefail

event="${EVENT_NAME:-}"
action="${EVENT_ACTION:-}"
assignee_login="${ASSIGNEE_LOGIN:-}"
assignee_trigger="${ASSIGNEE_TRIGGER:-}"
label_name="${LABEL_NAME:-}"
label_trigger="${LABEL_TRIGGER:-}"
comment_body="${COMMENT_BODY:-}"
trigger_phrase="${TRIGGER_PHRASE:-}"

# --- Assignment events ---
if [ "$event" = "issues" ] && [ "$action" = "assigned" ]; then
  if [ -z "$assignee_trigger" ]; then
    echo "::notice::Skipping: issues/assigned event but no assignee_trigger configured"
    echo "skip=true" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  if [ "$assignee_login" != "$assignee_trigger" ]; then
    echo "::notice::Skipping: assigned to '$assignee_login' but assignee_trigger is '$assignee_trigger'"
    echo "skip=true" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  echo "skip=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

# --- Label events ---
if [ "$event" = "issues" ] && [ "$action" = "labeled" ]; then
  if [ -n "$label_trigger" ]; then
    # Check if label starts with the trigger prefix
    if [[ "$label_name" != "${label_trigger}:"* ]]; then
      echo "::notice::Skipping: label '$label_name' does not match prefix '${label_trigger}:'"
      echo "skip=true" >> "$GITHUB_OUTPUT"
      exit 0
    fi
    # Skip modifier labels
    suffix="${label_name#"${label_trigger}:"}"
    case "$suffix" in
      auto_advance|queued)
        echo "::notice::Skipping: modifier label '$label_name'"
        echo "skip=true" >> "$GITHUB_OUTPUT"
        exit 0
        ;;
    esac
  fi
  echo "skip=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

# --- Comment events ---
if [ "$event" = "issue_comment" ] || [ "$event" = "pull_request_review_comment" ]; then
  if [ -n "$trigger_phrase" ]; then
    if [[ "$comment_body" != *"$trigger_phrase"* ]]; then
      echo "::notice::Skipping: comment does not contain trigger phrase '$trigger_phrase'"
      echo "skip=true" >> "$GITHUB_OUTPUT"
      exit 0
    fi
  fi
  echo "skip=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

# --- Default: don't skip ---
echo "skip=false" >> "$GITHUB_OUTPUT"
