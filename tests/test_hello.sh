#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

passed=0
failed=0

run_test() {
  local name="$1"
  local result="$2"
  if [ "$result" = "pass" ]; then
    echo "PASS: $name"
    passed=$((passed + 1))
  else
    echo "FAIL: $name"
    failed=$((failed + 1))
  fi
}

# Test: output is exactly "Hello, World!"
output=$("$REPO_ROOT/hello.sh")
if [ "$output" = "Hello, World!" ]; then
  run_test "output is 'Hello, World!'" pass
else
  run_test "output is 'Hello, World!'" fail
fi

# Test: exit code is 0
"$REPO_ROOT/hello.sh" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  run_test "exit code is 0" pass
else
  run_test "exit code is 0" fail
fi

echo ""
echo "Results: $passed passed, $failed failed"
[ "$failed" -eq 0 ]
