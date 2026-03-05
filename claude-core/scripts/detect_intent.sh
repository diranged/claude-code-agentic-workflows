#!/usr/bin/env bash
# detect_intent.sh — Determine which agent and model to use based on comment text or label.
#
# Reads COMMENT_BODY and TRIGGER_LABEL env vars, writes agent + model to $GITHUB_OUTPUT.
# Label-based routing takes priority. Comment routing uses first-match on lowercased input.

set -euo pipefail

label="${TRIGGER_LABEL:-}"

# --- Label-based routing (takes priority) ---
if [[ "$label" == "claude:implement" ]]; then
  agent="agentic-developer"
  model="claude-sonnet-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == "claude:review" ]]; then
  agent="architect"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == "claude:design" ]]; then
  agent="agentic-designer"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
elif [[ "$label" == claude:* ]]; then
  # Unknown claude: label — default to designer
  agent="agentic-designer"
  model="claude-opus-4-20250514"
  echo "agent=${agent}" >> "$GITHUB_OUTPUT"
  echo "model=${model}" >> "$GITHUB_OUTPUT"
  exit 0
fi

# --- Comment-body routing ---
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
