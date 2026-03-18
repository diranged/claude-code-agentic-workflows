---
description: "Run integration tests against claude-workflows-integration-tests. Manages the integ-testing tag, triggers tests, monitors results, and iterates on failures."
---

# Integration Test Workflow

You manage integration testing between two repositories:

- **Main repo** (local): `diranged/claude-code-agentic-workflows` at `/Users/diranged/git/diranged/claude-code-agentic-workflows`
- **Integration test repo** (remote only): `diranged/claude-workflows-integration-tests`

Never clone the integration test repo locally. All operations on it use `gh` CLI.

## How It Works

The integration test repo's caller workflows permanently reference `@integ-testing` (a movable tag on the main repo). To test changes, you move the tag to your commit. When done, you move it back to `main`.

```
Main repo                          Integration test repo
─────────                          ─────────────────────
feature-branch ← integ-testing     workflows always use @integ-testing
                   (tag)           no changes needed in this repo
```

## Test Catalog

| Selector | Script | What It Tests | Timeout |
|----------|--------|---------------|---------|
| `mention` | test-mention-responder.sh | @claude comment triggers response | ~5 min |
| `design` | test-label-design.sh | claude:design label triggers designer agent | ~10 min |
| `auto-advance` | test-label-auto-advance.sh | Full design->review->implement pipeline | ~60 min |
| `formatting` | test-formatting-enforcement.sh | Claude PRs pass prettier CI | ~60 min |
| `engineer` | test-engineer-manager.sh | workflow_dispatch triggers dashboard creation | ~30 min |
| `all` | All of the above | Full suite | ~90 min |

## Iteration Workflow

### Step 1: Point the Tag at Your Work

```bash
git tag -f integ-testing HEAD
git push origin integ-testing --force
```

Verify:
```bash
git rev-parse integ-testing
git rev-parse HEAD
# Both should match
```

### Step 2: Run Tests

Trigger a specific test:
```bash
gh workflow run integration-tests.yml \
  --repo diranged/claude-workflows-integration-tests \
  -f tests="mention"
```

Or run the full suite:
```bash
gh workflow run integration-tests.yml \
  --repo diranged/claude-workflows-integration-tests \
  -f tests="all"
```

### Step 3: Monitor

```bash
sleep 15
RUN_ID=$(gh run list \
  --repo diranged/claude-workflows-integration-tests \
  --workflow integration-tests.yml \
  --limit 1 \
  --json databaseId --jq '.[0].databaseId')

gh run watch "$RUN_ID" --repo diranged/claude-workflows-integration-tests --exit-status
```

On failure:
```bash
gh run view "$RUN_ID" --repo diranged/claude-workflows-integration-tests --log-failed
```

### Step 4: Iterate on Failures

1. Read the failed logs
2. Fix the issue locally in the main repo
3. Move the tag: `git tag -f integ-testing HEAD && git push origin integ-testing --force`
4. Re-trigger: `gh workflow run integration-tests.yml --repo diranged/claude-workflows-integration-tests -f tests="<selector>"`

### Step 5: Cleanup

When done testing, point the tag back at main:
```bash
git tag -f integ-testing main
git push origin integ-testing --force
```

## One-Time Setup (already done)

The integration test repo's caller workflows on `main` use `@integ-testing`:
- `.github/workflows/claude-responder.yml` — `uses: .../claude-respond@integ-testing`
- `.github/workflows/claude-engineers.yml` — `uses: .../claude-respond@integ-testing` (with `label_trigger: 'claude'`)
- `.github/workflows/claude-engineer-managers.yml` — `uses: .../claude-engineer@integ-testing`

The `integ-testing` tag on the main repo normally points to `main`. It only diverges during active testing.

## Quick Reference

```bash
# Point tag at current work
git tag -f integ-testing HEAD && git push origin integ-testing --force

# Point tag back at main
git tag -f integ-testing main && git push origin integ-testing --force

# Check where the tag points
git ls-remote origin refs/tags/integ-testing

# Check what ref integration test repo uses
gh api repos/diranged/claude-workflows-integration-tests/contents/.github/workflows/claude-responder.yml --jq '.content' | base64 -d | grep '@'

# List recent integration test runs
gh run list --repo diranged/claude-workflows-integration-tests --workflow integration-tests.yml --limit 5

# View failed run logs
gh run view <RUN_ID> --repo diranged/claude-workflows-integration-tests --log-failed

# List open test issues (for manual cleanup)
gh issue list --repo diranged/claude-workflows-integration-tests --search "Integration Test" --state open

# Trigger single test
gh workflow run integration-tests.yml --repo diranged/claude-workflows-integration-tests -f tests="mention"
```

## Integration Test Repo Structure

```
claude-workflows-integration-tests/
├── .github/
│   ├── claude-instructions/
│   │   └── 00-formatting.md          # Prettier formatting instructions
│   └── workflows/
│       ├── ci.yml                     # PR CI: prettier check + FAIL_CI marker
│       ├── claude-responder.yml       # Caller: @claude mentions → shared workflow
│       ├── claude-engineers.yml       # Caller: claude:* labels → shared workflow
│       ├── claude-engineer-managers.yml # Caller: workflow_dispatch → action
│       └── integration-tests.yml      # Orchestrator: runs all test scenarios
├── scripts/
│   ├── lib.sh                         # Shared: create_test_issue, wait_for_*, cleanup
│   ├── run-tests.sh                   # Sequential test runner
│   ├── test-mention-responder.sh      # Test: @claude → response
│   ├── test-label-design.sh           # Test: claude:design → designer
│   ├── test-label-auto-advance.sh     # Test: full pipeline with auto_advance
│   ├── test-formatting-enforcement.sh # Test: PR passes prettier
│   └── test-engineer-manager.sh       # Test: dashboard creation
├── src/example.ts                     # Formatting test fixture
├── CLAUDE.md, README.md, .prettierrc, package.json
```

## Required Secrets (in integration test repo)

- `CLAUDE_OAUTH_TOKEN` — Claude Code OAuth token for agent execution
- `INTEGRATION_APP_ID` — GitHub App ID (for triggering workflows as non-bot)
- `INTEGRATION_APP_KEY` — GitHub App private key
