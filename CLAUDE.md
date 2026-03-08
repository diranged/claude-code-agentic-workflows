# CLAUDE.md

## Project

GitHub Actions composite actions for agentic Claude Code workflows. This repository provides five reusable composite actions that enable sophisticated Claude-powered automation in GitHub workflows.

**Key differentiator:** Claude Max subscribers can run these agents with no additional per-execution costs via OAuth authentication, making AI-powered workflows economically viable for regular use.

## Architecture

### Core Components

- **`claude-core/`** — Foundation composite action handling auth, argument composition, prompt composition, and Claude invocation
- **`claude-respond/`** — Interactive assistant triggered by @claude mentions (wraps claude-core + claude-report)
- **`claude-engineer/`** — Persistent autonomous engineer agents with dashboard management and task rotation
- **`claude-agent/`** — Scheduled autonomous agent for proactive scanning and issue creation (wraps claude-respond)
- **`claude-report/`** — Execution summary generator and artifact uploader for workflow transparency

### Directory Structure

```
claude-code-agentic-workflows/
├── .github/workflows/
│   ├── shared-claude-responder.yml   # Reusable: @claude mention handler
│   ├── shared-claude-engineers.yml   # Reusable: claude:* label lifecycle
│   ├── repo-claude-responder.yml     # Internal: calls shared responder
│   ├── repo-claude-engineers.yml     # Internal: calls shared engineers
│   ├── repo-engineer-managers.yml    # Internal: scheduled engineer personalities
│   ├── repo-conventional-commit.yml  # Internal: PR title validation
│   ├── repo-test.yml                 # Internal: unit tests
│   └── repo-test-claude-respond.yml  # Internal: manual Claude testing
├── claude-core/          # Core execution action
│   ├── action.yml
│   ├── agents/           # Built-in agent personalities (7 agents)
│   ├── instructions/     # Base prompt instructions loaded every run
│   ├── skills/           # Composable skill prompts loaded every run
│   └── scripts/          # Shell scripts for arg building, validation
├── claude-respond/       # Interactive assistant action
├── claude-engineer/      # Persistent engineer action
│   └── agents/           # Engineer-specific agents (loaded via extra_agents_path)
├── claude-agent/         # Scheduled agent action
│   └── agents/           # Agent-specific agents (loaded via extra_agents_path)
├── claude-report/        # Execution summary action
├── scripts/              # Repo-level utility scripts
├── tests/                # Test suite
└── docs/                 # Project documentation
```

### Workflow Architecture

Workflows follow a `shared-*` / `repo-*` naming convention:

- **`shared-*`** — Reusable workflows (`workflow_call`) consumed by other repositories
- **`repo-*`** — Internal workflows specific to this repository

Consuming repositories create thin caller workflows that invoke the shared workflows with their own configuration:

```yaml
# Example: consuming repo's .github/workflows/claude-responder.yml
on:
  issue_comment:
    types: [created]
jobs:
  respond:
    uses: diranged/claude-code-agentic-workflows/.github/workflows/shared-claude-responder.yml@v0
    with:
      runner: my-self-hosted-runner
    secrets:
      claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
```

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

## Prompt Composition System

When `compose_prompt: true`, the system builds sophisticated prompts by combining:

- **Base Instructions** (`claude-core/instructions/`) — Fundamental behavioral guidelines
- **Skills** (`claude-core/skills/`) — Composable capability modules
- **Agent Personalities** — Specialized roles and domain expertise

This modular approach enables consistent behavior across agents while allowing specialization.

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
- Shell scripts in `claude-core/scripts/` are tested via Python subprocess helpers
- `claude-respond/tests/test_action_yml.py` enforces input parity between claude-respond and claude-core
- Validate workflow syntax and action specifications in test suite

### CI/Runner Environment

- **Self-hosted runner:** `diranged-claude-code`
- **`gh` CLI is installed** via `dev-hanz-ops/install-gh-cli-action` in workflow steps
- **`make` may not be installed** — agents use direct venv+unittest fallback
- **GitHub token lacks `workflows` permission** — cannot push workflow files directly

### Key Design Decisions

1. **Composite Actions + Reusable Workflows:** Actions provide building blocks; shared workflows provide batteries-included orchestration
2. **`shared-*` / `repo-*` Convention:** Clear separation between reusable and internal workflows
3. **Public Repository Required:** GitHub only allows cross-org `uses:` references to public repos
4. **OAuth-First Auth:** Enables cost-effective automation for Claude Max subscribers
5. **Modular Prompt System:** Composable instructions/skills/agents for consistency and customization
6. **Dashboard Management:** Persistent context for long-running autonomous operations

## Important File Locations

### Reusable Workflows (consumed by other repos)
- `.github/workflows/shared-claude-responder.yml` — Handles @claude mentions and issue assignment
- `.github/workflows/shared-claude-engineers.yml` — Handles claude:* label lifecycle and CI retry

### Internal Workflows (this repo only)
- `.github/workflows/repo-claude-responder.yml` — Calls shared responder with our config
- `.github/workflows/repo-claude-engineers.yml` — Calls shared engineers with our config
- `.github/workflows/repo-engineer-managers.yml` — Scheduled engineer personalities
- `.github/workflows/repo-conventional-commit.yml` — PR title validation
- `.github/workflows/repo-test.yml` — Unit tests
- `.github/workflows/repo-test-claude-respond.yml` — Manual Claude testing

### Action Specifications
- `claude-core/action.yml` — Core action with comprehensive inputs
- `claude-respond/action.yml` — Interactive assistant wrapper
- `claude-engineer/action.yml` — Persistent engineer wrapper
- `claude-agent/action.yml` — Scheduled agent wrapper
- `claude-report/action.yml` — Execution summary generator

### Agent Definitions
- `claude-core/agents/` — 7 built-in agent personalities
- `claude-engineer/agents/` — Engineer-specific agents (docs-engineer, code-janitor)
- `claude-agent/agents/` — Agent-specific agents (security-auditor)
- `.github/claude-agents/` — Repository-local overrides (in consuming repos)

### Prompt Components
- `claude-core/instructions/` — Base behavioral instructions
- `claude-core/skills/` — Composable capability modules

### Scripts and Utilities
- `claude-core/scripts/` — Auth validation, argument building, prompt composition
- `scripts/` — Repository-level utilities
- `tests/` — Comprehensive test suite covering all actions

### Documentation
- `docs/plan.md` — Comprehensive project plan and architecture decisions
- `README.md` — User-facing documentation and quick start guide
