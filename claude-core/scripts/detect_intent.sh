#!/usr/bin/env bash
# detect_intent.sh — Determine which agent and model to use based on comment text.
#
# Reads COMMENT_BODY env var, writes agent + model to $GITHUB_OUTPUT.
# Routing uses first-match on lowercased input.

set -euo pipefail

body="$(echo "${COMMENT_BODY:-}" | tr '[:upper:]' '[:lower:]')"

# Routing table: first match wins
if [[ "$body" =~ @claude[[:space:]]+implement ]] || [[ "$body" =~ implement[[:space:]]+(this|the|it|now) ]]; then
  agent="agentic-developer"
  model="claude-sonnet-4-20250514"

elif [[ "$body" =~ dead[[:space:]]*code ]] || [[ "$body" =~ stale ]] || \
     [[ "$body" =~ (^|[[:space:]])todo([[:space:]]|$) ]] || [[ "$body" =~ cleanup ]] || \
     [[ "$body" =~ janitor ]] || [[ "$body" =~ (^|[[:space:]])unused([[:space:]]|$) ]] || \
     [[ "$body" =~ deprecated ]] || [[ "$body" =~ outdated[[:space:]]*dep ]]; then
  agent="janitor"
  model="claude-sonnet-4-20250514"

elif [[ "$body" =~ performance ]] || [[ "$body" =~ n\+1 ]] || \
     [[ "$body" =~ memory[[:space:]]*leak ]] || [[ "$body" =~ bundle[[:space:]]*size ]] || \
     [[ "$body" =~ (^|[[:space:]])slow([[:space:]]|$) ]] || [[ "$body" =~ latency ]] || \
     [[ "$body" =~ (^|[[:space:]])perf([[:space:]]|$) ]]; then
  agent="performance-reviewer"
  model="claude-sonnet-4-20250514"

elif [[ "$body" =~ documentation ]] || [[ "$body" =~ (^|[[:space:]])docs?([[:space:]]|$) ]] || \
     [[ "$body" =~ readme ]] || [[ "$body" =~ broken[[:space:]]*link ]] || \
     [[ "$body" =~ api[[:space:]]*doc ]] || [[ "$body" =~ changelog ]]; then
  agent="docs-reviewer"
  model="claude-sonnet-4-20250514"

elif [[ "$body" =~ (^|[[:space:]])tests?([[:space:]]|$) ]] || [[ "$body" =~ coverage ]] || \
     [[ "$body" =~ flaky ]] || [[ "$body" =~ untested ]] || \
     [[ "$body" =~ edge[[:space:]]*case ]] || [[ "$body" =~ (^|[[:space:]])spec([[:space:]]|$) ]]; then
  agent="test-coverage"
  model="claude-sonnet-4-20250514"

elif [[ "$body" =~ architect ]] || [[ "$body" =~ coupling ]] || \
     [[ "$body" =~ abstraction ]] || [[ "$body" =~ api[[:space:]]*design ]] || \
     [[ "$body" =~ scalab ]] || [[ "$body" =~ layering ]] || \
     [[ "$body" =~ circular[[:space:]]*dep ]] || [[ "$body" =~ design[[:space:]]*review ]]; then
  agent="architect"
  model="claude-opus-4-20250514"

elif [[ "$body" =~ review ]]; then
  # Generic "review" catch-all → architect
  agent="architect"
  model="claude-opus-4-20250514"

else
  # Default: design phase
  agent="agentic-designer"
  model="claude-opus-4-20250514"
fi

echo "agent=${agent}" >> "$GITHUB_OUTPUT"
echo "model=${model}" >> "$GITHUB_OUTPUT"
