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

### Step 2: Install dependencies

```bash
npm ci          # Node.js projects
pip install -r requirements.txt  # Python projects
```

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

## Critical Rule

**The sequence is: code → format → lint → test → stage → commit → push.**

Never reorder these steps. Never skip the format/lint/test steps. If you find yourself about to run `git commit` and you have not yet run the formatter, STOP and run it first.
