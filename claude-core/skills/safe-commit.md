# Skill: Safe Commit Workflow

## How to Commit Code

**You MUST follow this exact sequence every time you commit code.** Never run `git commit` without completing the pre-commit checks first.

### Step 1: Discover project quality checks

Before your first commit, read the project's CI workflow to learn what checks run:

```bash
cat .github/workflows/ci.yml    # or test.yml, check.yml, etc.
cat package.json                 # look for "scripts" section
```

Note every command CI runs (formatters, linters, type checkers, tests).

### Step 2: Install runtime and dependencies

If the required runtime (node, python3, etc.) is not installed, install it first. Try these approaches in order:

```bash
# If `node` or `npm` is not found, try these in order:
# 1. Check for node in non-standard paths
find /usr /home /opt -name "node" -type f 2>/dev/null | head -5

# 2. Install via package manager
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs

# 3. If sudo is unavailable, try nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 22
```

Then install project dependencies:

```bash
npm ci          # Node.js projects
pip install -r requirements.txt  # Python projects
```

### CRITICAL: Fail if environment setup fails

**If you cannot install the required runtime or dependencies after exhausting all options above, you MUST stop immediately.** Do NOT proceed to write code, do NOT commit, do NOT create a PR.

Instead:
1. Update the tracking comment with status **Failed** and explain exactly what is missing (e.g., "Node.js is not installed and cannot be installed on this runner").
2. Exit with an error. Run: `exit 1`

**Never work around a missing environment by skipping quality checks.** Committing code without running the formatter and linter wastes CI cycles and creates broken PRs. It is better to fail loudly than to silently produce unverified code.

### Step 3: Write your code changes

Implement the required changes.

### Step 4: Run ALL quality checks BEFORE staging

This is the critical step that must not be skipped. Run every check that CI runs:

```bash
# Example for a Node.js project with prettier:
npx prettier --write .        # Auto-fix formatting
npm run lint -- --fix         # Auto-fix lint issues (if applicable)
npm run typecheck             # Type checking (if applicable)
npm test                      # Run tests

# Example for a Python project:
black .                       # Auto-fix formatting
ruff check --fix .            # Auto-fix lint issues
pytest                        # Run tests
```

**If any check fails, fix the issue and re-run ALL checks.**

### Step 5: Stage and commit

Only after ALL quality checks pass:

```bash
git add <files>
git commit -m "your message"
```

### Step 6: Push and verify

```bash
git push -u origin <branch>
git log origin/<branch> --oneline -1   # Verify push succeeded
```

## Critical Rules

1. **The sequence is: code → format → lint → test → stage → commit → push.** Never reorder these steps. Never skip the format/lint/test steps.

2. **If you cannot run the quality checks, do not commit.** A commit without verification is worse than no commit at all. Fail with a clear error message explaining what is missing.
