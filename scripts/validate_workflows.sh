#!/usr/bin/env bash

# Workflow YAML Validator
# Validates GitHub Actions workflow YAML files for syntax errors
#
# Usage:
#   validate_workflows.sh [WORKFLOWS_DIR]
#
# Arguments:
#   WORKFLOWS_DIR  - Path to workflows directory (default: .github/workflows)
#
# Environment Variables:
#   PYTHON         - Python executable to use (default: python3)
#
# Exit Codes:
#   0 - All workflow files passed YAML validation (or no files found)
#   1 - One or more files failed YAML validation
#
# Example:
#   validate_workflows.sh
#   validate_workflows.sh /path/to/workflows
#   PYTHON=python3.11 validate_workflows.sh

set -euo pipefail

WORKFLOWS_DIR="${1:-.github/workflows}"
if [[ "$WORKFLOWS_DIR" == *..* ]]; then
    echo "Error: WORKFLOWS_DIR cannot contain '..' (got: $WORKFLOWS_DIR)" >&2
    exit 1
fi

PYTHON="${PYTHON:-python3}"

# Validate PYTHON is a real executable that looks like python3
resolved=$(command -v "$PYTHON" 2>/dev/null) || {
    echo "Error: PYTHON='$PYTHON' is not a valid executable" >&2
    exit 1
}
case "$resolved" in
    *python3*) ;;
    *)
        echo "Error: PYTHON='$PYTHON' does not resolve to a python3 executable (got: $resolved)" >&2
        exit 1
        ;;
esac
PYTHON="$resolved"
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
