# CLAUDE.md

## Project

GitHub Actions composite actions for agentic Claude Code workflows. This repository provides six composite actions that enable sophisticated Claude-powered automation in GitHub workflows.

**Key differentiator:** Claude Max subscribers can run these agents with no additional per-execution costs via OAuth authentication, making AI-powered workflows economically viable for regular use.

## Architecture

### Core Components

- **`claude-setup/`** — Pre-Claude orchestration: trigger validation, tracking comments, checkout, and pre-run setup
- **`claude-core/`** — Foundation composite action handling auth, argument composition, prompt composition, and Claude invocation
- **`claude-respond/`** — Interactive assistant: orchestrates setup → detect-intent → core → report pipeline
- **`claude-engineer/`** — Persistent autonomous engineer agents with dashboard management and task rotation (wraps claude-respond)
- **`claude-agent/`** — Scheduled autonomous agent for proactive scanning and issue creation (wraps claude-respond)
- **`claude-report/`** — Execution summary generator and artifact uploader for workflow transparency

### Action Composition

```
claude-setup/     → trigger validation, gh CLI, tracking, checkout, pre_run
claude-respond/   → claude-setup → detect_intent (conditional) → claude-core → claude-report
claude-engineer/  → wraps claude-respond with engineer-specific config
claude-agent/     → wraps claude-respond with agent-specific config
```

### Directory Structure

```
claude-code-agentic-workflows/
├── .github/workflows/
│   ├── repo-claude-responder.yml     # Internal: uses ./claude-respond action
│   ├── repo-claude-engineers.yml     # Internal: uses ./claude-respond with label_trigger
│   ├── repo-engineer-managers.yml    # Internal: scheduled engineer personalities
│   ├── repo-conventional-commit.yml  # Internal: PR title validation
│   ├── repo-test.yml                 # Internal: unit tests
│   └── repo-test-claude-respond.yml  # Internal: manual Claude testing
├── claude-setup/          # Pre-Claude orchestration action
│   ├── action.yml
│   ├── scripts/           # validate_trigger.sh, setup_tracking.sh, resolve_token.sh
│   └── tests/             # Unit tests for scripts and action structure
├── claude-core/           # Core execution action
│   ├── action.yml
│   ├── agents/            # Built-in agent personalities (7 agents)
│   ├── instructions/      # Base prompt instructions loaded every run
│   ├── skills/            # Composable skill prompts loaded every run
│   └── scripts/           # Shell scripts for arg building, validation
├── claude-respond/        # Interactive assistant action
│   ├── action.yml
│   ├── scripts/           # detect_intent.sh (label routing)
│   └── tests/             # Unit tests for action and scripts
├── claude-engineer/       # Persistent engineer action
│   ├── action.yml
│   ├── agents/            # Engineer-specific agents (loaded via extra_agents_path)
│   ├── instructions/      # Engineer-specific instructions
│   └── tests/             # Unit tests for action structure
├── claude-agent/          # Scheduled agent action
│   ├── action.yml
│   ├── agents/            # Agent-specific agents (loaded via extra_agents_path)
│   └── tests/             # Unit tests for action structure
├── claude-report/         # Execution summary action
├── scripts/               # Repo-level utility scripts
├── tests/                 # Root test suite (workflow validation, utilities)
└── docs/                  # Project documentation
```

### Consumer Experience

Consuming repositories create simple workflows that use the composite actions directly. No reusable workflows or secrets blocks needed — composite actions run in the caller's job context:

```yaml
# Example: consuming repo's .github/workflows/claude-responder.yml
on:
  issue_comment:
    types: [created]

env:
  GH_PACKAGES_TOKEN: ${{ secrets.GH_PACKAGES_TOKEN }}

jobs:
  respond:
    if: contains(github.event.comment.body, '@claude')
    runs-on: my-runner
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: diranged/claude-code-agentic-workflows/claude-respond@v0
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          trigger_phrase: "@claude"
          compose_prompt: "true"
          pre_run: "GITHUB_TOKEN=${GH_PACKAGES_TOKEN} npm ci"
```

Key benefits:
- **One job, one step** per use case
- **`env:` vars available in `pre_run`** — the caller's env vars are inherited
- **Consumer controls `runs-on` and `permissions`** directly
- **No `secrets:` block** — secrets passed directly as `with:` inputs

### Authentication Strategy

Dual-path authentication with OAuth preference:

| Method | Input | Billing | Use Case |
|--------|-------|---------|----------|
| **OAuth** (Primary) | `claude_code_oauth_token` | Subscription-based (Claude Max) | Cost-effective for regular use |
| **API Key** (Fallback) | `anthropic_api_key` | Per-token billing | One-off usage or fallback |

**Detection Logic:** OAuth takes precedence when both are present. Actions set `AUTH_METHOD` env var and fail fast with actionable errors if OAuth token is expired.

**GitHub App Support:** Optional elevated permissions via `app_id` and `app_private_key` inputs for actions requiring more than default `GITHUB_TOKEN` access.

## Agent System

### Built-in Agents (claude-core/agents/)

| Agent | Purpose | Typical Usage |
|-------|---------|---------------|
| `agentic-designer` | Creates implementation designs for complex tasks | Two-phase design→implement workflow |
| `agentic-developer` | Implements approved designs with code changes | Implementation after design approval |
| `architect` | Reviews designs for architectural concerns | Design review and validation |
| `docs-reviewer` | Reviews documentation changes for quality | Documentation quality assurance |
| `janitor` | Cleans up stale branches, issues, and artifacts | Maintenance automation |
| `performance-reviewer` | Reviews code changes for performance impact | Performance analysis |
| `test-coverage` | Analyzes and improves test coverage | Test quality improvement |

### Engineer-specific Agents (claude-engineer/agents/)

| Agent | Purpose | Dashboard Management |
|-------|---------|---------------------|
| `docs-engineer` | Autonomous documentation maintenance | Creates persistent dashboard issues, rotates tasks |
| `code-janitor` | Repository cleanup and maintenance automation | Creates persistent dashboard issues, rotates tasks |
| `security-engineer` | Security hygiene and vulnerability detection | Creates persistent dashboard issues, rotates tasks |

### Agent-specific Agents (claude-agent/agents/)

| Agent | Purpose | Typical Usage |
|-------|---------|---------------|
| `security-auditor` | Scheduled security scanning and vulnerability detection | Weekly security audits, compliance checks |

### Agent Customization

**Override Chain:**

The agent search path is action-specific based on the `extra_agents_path` input:

1. Repository-local `.github/claude-agents/<name>.md` (highest priority)
2. Action-specific agents directory:
   - `claude-core/agents/` (for claude-respond using claude-core)
   - `claude-engineer/agents/` (for claude-engineer runs)
   - `claude-agent/agents/` (for claude-agent runs)
3. Inline `prompt` parameter (fallback)

This allows consuming repositories to customize agent behavior without modifying the actions themselves.

### Pipeline Labels

The agent system uses labels for workflow automation:

| Label | Purpose | Usage |
|-------|---------|-------|
| `claude:design` | Triggers design phase | Applied to issues requiring implementation planning |
| `claude:review` | Triggers architecture review | Applied after design completion for review |
| `claude:implement` | Triggers implementation phase | Applied after design approval for development |
| `claude:auto_advance` | Enables automatic pipeline progression | Automatically advances through design → review → implement stages |
| `claude:queued` | Implementation concurrency gating | Applied when implementation slots are full during auto-advance |

**Manual Mode:** Issues require human approval at each stage (design → human applies review → human applies implement).

**Automated Mode:** Adding `claude:auto_advance` enables autonomous progression. The designer auto-advances to architect review, and the architect auto-advances to implementation with concurrency checking.

## Prompt Composition System

When `compose_prompt: true`, the system builds sophisticated prompts by combining:

- **Base Instructions** (`claude-core/instructions/`) — Fundamental behavioral guidelines
- **Skills** (`claude-core/skills/`) — Composable capability modules
- **Agent Personalities** — Specialized roles and domain expertise

This modular approach enables consistent behavior across agents while allowing specialization.

## Integration Testing

Integration tests live in `diranged/claude-workflows-integration-tests`. That repo acts as a real consumer — its caller workflows permanently reference `@integ-testing` (a movable tag on this repo).

### How it works

1. The `integ-testing` tag normally points at `main`
2. To test changes: `git tag -f integ-testing HEAD && git push origin integ-testing --force`
3. The integration test repo's workflows now resolve your branch's code
4. Trigger tests: `gh workflow run integration-tests.yml --repo diranged/claude-workflows-integration-tests -f tests="mention"`
5. When done: `git tag -f integ-testing main && git push origin integ-testing --force`

### Nested action references

All `uses:` references between actions (e.g., `claude-respond` calling `claude-setup`) reference `@integ-testing`. This ensures the entire action chain resolves to the same version. When the `integ-testing` tag points at `main`, this is equivalent to `@main`.

### Test catalog

| Selector | What it tests |
|----------|---------------|
| `mention` | @claude comment triggers response (~5 min) |
| `design` | claude:design label triggers designer agent (~10 min) |
| `auto-advance` | Full design→review→implement pipeline (~60 min) |
| `formatting` | Claude PRs pass prettier CI (~60 min) |
| `engineer` | workflow_dispatch triggers dashboard creation (~30 min) |
| `all` | Full suite |

Use `/integration-test` in Claude Code for the complete workflow reference.

## Development Workflow

### Two-Phase Design→Implement Pattern

1. **@claude** mention triggers `agentic-designer` → creates design document
2. **claude:implement** label triggers `agentic-developer` → implements approved design

This pattern ensures complex changes are properly planned before implementation.

### Persistent Engineer Operations

Engineer agents operate autonomously with dashboard management:
- Create persistent dashboard issues for task tracking
- Rotate dashboards based on `rotation_days`
- Apply consistent labeling for task organization
- Maintain long-term context across runs

## Conventions

### Commits and PRs

- **Use conventional commits** for ALL commit messages and PR titles. This is enforced by CI.
  - Format: `type(scope): description`
  - The description (subject) MUST start with a lowercase letter
  - **Before creating any commit or PR**, read `.github/workflows/repo-conventional-commit.yml` to discover the valid types and scopes. That file is the single source of truth — do not guess.
- PRs use squash merge only — the PR title becomes the commit message, so it MUST be conventional

### CI Checks — Reading and Fixing Failures

- When asked to fix CI failures, **check ALL failing checks**, not just the test suite. Use `gh pr checks <PR_NUMBER>` or the GitHub API to list every check and its status.
- The `check-title` job validates the PR title against conventional commit rules. If it fails, the PR title is wrong — fix it with:
  ```bash
  gh pr edit <PR_NUMBER> --title "type(scope): description"
  ```
- **Do not assume "CI is failing" means "tests are failing."** Read the actual check names and their output before deciding what to fix.
- After pushing fixes, verify the push succeeded by running `git log origin/<branch> --oneline -1` and confirming your commit appears on the remote.

### Code and Testing

- Tests: `unittest` + `subprocess` pattern, each subdirectory has own `Makefile` + shared root-level `requirements-test.txt`
- Root `make test` discovers all `*/Makefile` targets
- Shell scripts tested via Python subprocess helpers (see `helpers.py` in each test directory)
- `claude-respond/tests/test_action_yml.py` enforces claude-respond is a superset of claude-core inputs
- `tests/test_repo_workflows.py` validates internal workflow files use actions directly (no shared workflows)
- Validate workflow syntax and action specifications in test suite

### CI/Runner Environment

- **Self-hosted runner:** `diranged-claude-code`
- **`gh` CLI is installed** automatically by `claude-setup` via `dev-hanz-ops/install-gh-cli-action`
- **`make` may not be installed** — agents use direct venv+unittest fallback
- **GitHub token lacks `workflows` permission** — cannot push workflow files directly

### Key Design Decisions

1. **Pure Composite Actions:** All orchestration in composite actions — no reusable workflows. Actions run in the caller's job context, inheriting env vars and allowing direct secret access.
2. **`claude-setup` as orchestration layer:** Separates pre-Claude concerns (trigger validation, tracking, checkout, pre_run) from Claude execution concerns, keeping each action focused.
3. **Public Repository Required:** GitHub only allows cross-org `uses:` references to public repos
4. **OAuth-First Auth:** Enables cost-effective automation for Claude Max subscribers
5. **Modular Prompt System:** Composable instructions/skills/agents for consistency and customization
6. **Dashboard Management:** Persistent context for long-running autonomous operations

## Important File Locations

### Internal Workflows (this repo only)
- `.github/workflows/repo-claude-responder.yml` — Uses ./claude-respond for @claude mentions
- `.github/workflows/repo-claude-engineers.yml` — Uses ./claude-respond with label_trigger for claude:* labels
- `.github/workflows/repo-engineer-managers.yml` — Scheduled engineer personalities
- `.github/workflows/repo-conventional-commit.yml` — PR title validation
- `.github/workflows/repo-test.yml` — Unit tests
- `.github/workflows/repo-test-claude-respond.yml` — Manual Claude testing

### Action Specifications
- `claude-setup/action.yml` — Pre-Claude orchestration (trigger, tracking, checkout, pre_run)
- `claude-core/action.yml` — Core action with comprehensive inputs
- `claude-respond/action.yml` — Interactive assistant (setup → intent → core → report)
- `claude-engineer/action.yml` — Persistent engineer wrapper
- `claude-agent/action.yml` — Scheduled agent wrapper
- `claude-report/action.yml` — Execution summary generator

### Agent Definitions
- `claude-core/agents/` — 7 built-in agent personalities
- `claude-engineer/agents/` — Engineer-specific agents (docs-engineer, code-janitor, security-engineer)
- `claude-agent/agents/` — Agent-specific agents (security-auditor)
- `.github/claude-agents/` — Repository-local overrides (in consuming repos)

### Prompt Components
- `claude-core/instructions/` — Base behavioral instructions
- `claude-core/skills/` — Composable capability modules

### Scripts and Utilities
- `claude-setup/scripts/` — Trigger validation, tracking comments, token resolution
- `claude-core/scripts/` — Auth validation, argument building, prompt composition
- `claude-respond/scripts/` — Label-to-agent routing (detect_intent)
- `scripts/` — Repository-level utilities
- `tests/` — Comprehensive test suite covering all actions

### Documentation
- `docs/plan.md` — Comprehensive project plan and architecture decisions
- `README.md` — User-facing documentation and quick start guide
