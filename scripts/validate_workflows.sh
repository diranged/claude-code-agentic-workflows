#!/usr/bin/env bash
set -euo pipefail

WORKFLOWS_DIR="${1:-.github/workflows}"
PYTHON="${PYTHON:-python3}"
FAILED=0
FOUND=0

for f in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
    [ -f "$f" ] || continue
    FOUND=$((FOUND + 1))
    if "$PYTHON" -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]).read())" "$f" 2>/dev/null; then
        echo "PASS: $f"
    else
        "$PYTHON" -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]).read())" "$f" 2>&1 || true
        echo "FAIL: $f"
        FAILED=$((FAILED + 1))
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo "No workflow files found in $WORKFLOWS_DIR"
    exit 0
fi

echo ""
echo "Results: $((FOUND - FAILED))/$FOUND passed"

if [ "$FAILED" -gt 0 ]; then
    echo "Error: $FAILED file(s) failed YAML validation"
    exit 1
fi

echo "All $FOUND workflow file(s) passed YAML validation"
