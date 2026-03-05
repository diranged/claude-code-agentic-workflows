# CLAUDE.md

## Project

GitHub Actions composite actions for agentic Claude Code workflows. This repository provides four reusable composite actions that enable sophisticated Claude-powered automation in GitHub workflows.

**Key differentiator:** Claude Max subscribers can run these agents with no additional per-execution costs via OAuth authentication, making AI-powered workflows economically viable for regular use.

## Architecture

### Core Components

- **`claude-core/`** — Foundation composite action handling auth, argument composition, prompt composition, and Claude invocation
- **`claude-respond/`** — Interactive assistant triggered by @claude mentions (wraps claude-core + claude-report)
- **`claude-engineer/`** — Persistent autonomous engineer agents with dashboard management and task rotation
- **`claude-report/`** — Execution summary generator and artifact uploader for workflow transparency

### Directory Structure

```
claude-code-agentic-workflows/
├── claude-core/          # Core execution action
│   ├── action.yml
│   ├── agents/           # Built-in agent personalities (7 agents)
│   ├── instructions/     # Base prompt instructions loaded every run
│   ├── skills/           # Composable skill prompts loaded every run
│   └── scripts/          # Shell scripts for arg building, validation
├── claude-respond/       # Interactive assistant action
├── claude-engineer/      # Persistent engineer action
│   └── agents/           # Engineer-specific agents (loaded via extra_agents_path)
├── claude-report/        # Execution summary action
├── scripts/              # Repo-level utility scripts
├── tests/                # Test suite
└── docs/                 # Project documentation
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

### Agent Customization

**Override Chain:**
1. Repository-local `.github/claude-agents/<name>.md` (highest priority)
2. Built-in `claude-core/agents/`
3. Built-in `claude-engineer/agents/`
4. Inline `prompt` parameter (fallback)

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

- **Use conventional commits** for all commit messages and PR titles
  - Format: `type(scope): description` (e.g., `feat(core): add notify_owners input`)
  - Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `ci`
  - Scopes: `claude-core`, `claude-respond`, `claude-engineer`, `claude-report`, `docs`, `workflows`, `agents`
- PRs use squash merge only

### Code and Testing

- Tests: `unittest` + `subprocess` pattern, each subdirectory has own `Makefile` + shared root-level `requirements-test.txt`
- Root `make test` discovers all `*/Makefile` targets
- Shell scripts in `claude-core/scripts/` are tested via Python subprocess helpers
- `claude-respond/tests/test_action_yml.py` enforces input parity between claude-respond and claude-core
- Validate workflow syntax and action specifications in test suite

### CI/Runner Environment

- **Self-hosted runner:** `diranged-claude-code`
- **`gh` CLI may NOT be installed** — agents use curl fallback with `GITHUB_TOKEN`
- **`make` may not be installed** — agents use direct venv+unittest fallback
- **GitHub token lacks `workflows` permission** — cannot push workflow files directly

### Key Design Decisions

1. **Composite Actions Only:** No reusable workflows to avoid `.github/workflows/` constraints for consumers
2. **Public Repository Required:** GitHub only allows cross-org `uses:` references to public repos
3. **OAuth-First Auth:** Enables cost-effective automation for Claude Max subscribers
4. **Modular Prompt System:** Composable instructions/skills/agents for consistency and customization
5. **Dashboard Management:** Persistent context for long-running autonomous operations

## Important File Locations

### Action Specifications
- `claude-core/action.yml` — Core action with comprehensive inputs
- `claude-respond/action.yml` — Interactive assistant wrapper
- `claude-engineer/action.yml` — Persistent engineer wrapper
- `claude-report/action.yml` — Execution summary generator

### Agent Definitions
- `claude-core/agents/` — 7 built-in agent personalities
- `claude-engineer/agents/` — Engineer-specific agents (docs-engineer)
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
