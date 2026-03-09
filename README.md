# Claude Code Agentic Workflows

**Reusable GitHub Actions composite actions for Claude-powered automation**

## Overview

This repository provides five reusable GitHub Actions composite actions that enable powerful Claude-powered automation in your workflows. The project creates a complete ecosystem for AI-driven development assistance, from interactive issue responses to autonomous engineering tasks.

The core actions include:
- **claude-respond** — Interactive assistant triggered by @claude mentions
- **claude-core** — Low-level execution wrapper for auth and prompt composition
- **claude-engineer** — Persistent autonomous engineer with dashboard management
- **claude-agent** — Scheduled autonomous agent for proactive scanning and issue creation
- **claude-report** — Execution summary and artifact upload

Together, these actions enable sophisticated AI workflows while maintaining clear separation of concerns.

Key differentiator: Claude Max subscribers can run these agents with no additional per-execution costs via OAuth authentication, making AI-powered workflows economically viable for regular use.

## Versioning

This project uses semantic versioning with a `v0` pre-release strategy:

- **`@v0`** — Pin to the latest stable v0.x.y release (recommended for most users)
- **`@v0.x.y`** — Pin to an exact version for reproducible builds
- **`@main`** — Development branch (not recommended for production use)

The project is currently pre-1.0, meaning breaking changes may occur between minor versions. All actions (claude-core, claude-respond, claude-engineer, claude-agent, claude-report) are versioned together as a monolithic release.

For release process and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Quick Start

### Prerequisites

- GitHub App with appropriate permissions (optional, for elevated access)
- Claude authentication token (OAuth preferred, API key fallback)

### Basic Setup

Add this workflow to `.github/workflows/claude.yml`:

```yaml
name: "Claude Assistant"

on:
  issue_comment:
    types: [created]
  issues:
    types: [assigned, labeled]

jobs:
  claude-respond:
    runs-on: ubuntu-latest
    if: contains(github.event.comment.body, '@claude') || github.event.action == 'labeled'
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Claude
        uses: diranged/claude-code-agentic-workflows/claude-respond@v0
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          trigger_phrase: "@claude"
          allowed_tools: "Bash(*),Read,Glob,Grep,Edit,Write"
```

## Authentication

| Method | Input | Description | Billing |
|--------|-------|-------------|---------|
| **OAuth** (Preferred) | `claude_code_oauth_token` | Token from `claude setup-token` command | Subscription-based, no per-execution cost |
| **API Key** (Fallback) | `anthropic_api_key` | Anthropic API key | Per-token billing |

### GitHub App Configuration

For elevated permissions beyond the default `GITHUB_TOKEN`:

| Input | Description |
|-------|-------------|
| `app_id` | GitHub App ID |
| `app_private_key` | GitHub App private key (PEM format) |

## Actions Reference

### claude-respond

**Interactive Claude assistant triggered by @claude mentions**

Composes `claude-core` + `claude-report` for complete interactive assistance.

| Input | Description | Required |
|-------|-------------|----------|
| `claude_code_oauth_token` | OAuth token (preferred) | false |
| `anthropic_api_key` | API key (fallback) | false |
| `trigger_phrase` | Phrase that triggers Claude | false |
| `compose_prompt` | Enable prompt composition | false |
| `agent_name` | Agent from agents/ directory | false |

📄 [Full specification](claude-respond/action.yml)

### claude-core

**Low-level execution wrapper for auth, prompt composition, and arg building**

The foundational action that handles authentication, prompt building, and Claude Code invocation.

| Input | Description | Required |
|-------|-------------|----------|
| `claude_code_oauth_token` | OAuth token | false |
| `anthropic_api_key` | API key | false |
| `compose_prompt` | Compose from instructions/skills/agent | false |
| `agent_name` | Agent personality | false |
| `model` | Claude model | false |

📄 [Full specification](claude-core/action.yml)

### claude-engineer

**Persistent autonomous engineer with dashboard management**

Wraps `claude-respond` with engineer-specific configuration for long-term autonomous operation.

| Input | Description | Required |
|-------|-------------|----------|
| `agent_name` | Engineer agent (e.g., 'docs-engineer') | true |
| `dashboard_label` | Label for dashboard issue | true |
| `task_label` | Label for created tasks | true |
| `rotation_days` | Days before dashboard rotation | false |

📄 [Full specification](claude-engineer/action.yml)

### claude-agent

**Scheduled autonomous agent for proactive scanning and issue creation**

Wraps `claude-respond` with agent-specific configuration and operational guardrails for scheduled autonomous operation.

| Input | Description | Required |
|-------|-------------|----------|
| `agent_name` | Agent personality (e.g., 'security-auditor') | true |
| `max_issues` | Maximum issues to create per run | false |
| `issue_label` | Label for created issues | false |
| `dry_run` | Analyze but do not create issues (true/false) | false |
| `model` | Claude model | false |
| `timeout_minutes` | Timeout in minutes | false |

📄 [Full specification](claude-agent/action.yml)

### claude-report

**Execution summary generator and artifact uploader**

Generates concise execution summaries and uploads Claude Code execution logs as artifacts.

| Input | Description | Required |
|-------|-------------|----------|
| `execution_file` | Path to Claude execution JSON | true |
| `session_id` | Claude session ID | false |
| `outcome` | Execution outcome (success/failure) | false |

📄 [Full specification](claude-report/action.yml)

## Agent Personalities

### Built-in Agents (claude-core/agents/)

| Agent | Purpose |
|-------|---------|
| **agentic-designer** | Creates implementation designs for complex tasks |
| **agentic-developer** | Implements approved designs with code changes |
| **architect** | Reviews designs for architectural concerns |
| **docs-reviewer** | Reviews documentation changes for quality |
| **janitor** | Cleans up stale branches, issues, and artifacts |
| **performance-reviewer** | Reviews code changes for performance impact |
| **test-coverage** | Analyzes and improves test coverage |

### Engineer-specific Agents (claude-engineer/agents/)

| Agent | Purpose |
|-------|---------|
| **docs-engineer** | Autonomous documentation maintenance engineer |
| **code-janitor** | Repository cleanup and maintenance automation engineer |
| **security-engineer** | Security hygiene and vulnerability detection engineer |

### Agent-specific Agents (claude-agent/agents/)

| Agent | Purpose |
|-------|---------|
| **security-auditor** | Scheduled security scanning and vulnerability detection |

### Customization

Override built-in agents by placing custom definitions in `.github/claude-agents/<name>.md`. The system searches:

1. Repository-local `.github/claude-agents/`
2. Built-in `claude-core/agents/`
3. Built-in `claude-engineer/agents/`
4. Inline prompt fallback

## Pipeline Automation

Claude supports both manual and automated pipeline workflows for issue processing:

### Manual Pipeline (Default)

Issues progress through `claude:design` → `claude:review` → `claude:implement` with human approval required at each gate. After each stage, the agent sets status to "Needs Input" and waits for a human to apply the next label.

**Workflow:**
1. Apply `claude:design` label → Designer creates implementation plan
2. Human reviews and applies `claude:review` label → Architect reviews design
3. Human reviews and applies `claude:implement` label → Developer implements

### Automated Pipeline

Adding the `claude:auto_advance` label to an issue enables automatic progression through all pipeline stages without human gates.

**Workflow:**
1. Apply both `claude:design` and `claude:auto_advance` labels → Designer creates plan and auto-advances to review
2. Architect automatically reviews design and auto-advances to implementation (with concurrency gating)
3. Developer implements the approved design

**Concurrency Gating:** When `claude:auto_advance` is active, the architect checks implementation concurrency before advancing. If at the limit, it applies `claude:queued` instead of `claude:implement`.

**Trust Model:** Engineer agents apply `claude:auto_advance` to their delegated issues by default, enabling fully autonomous operation. Human-initiated work remains gated unless the label is manually applied.

**Apply the label:**
```bash
gh issue edit <NUMBER> --add-label "claude:auto_advance"
```

## Repository Structure

```
claude-code-agentic-workflows/
├── claude-core/          # Core execution action
│   ├── action.yml
│   ├── agents/           # Built-in agent personalities (7 agents)
│   ├── instructions/     # Base prompt instructions
│   ├── skills/           # Composable skill prompts
│   └── scripts/          # Shell scripts for arg building, validation
├── claude-respond/       # Interactive assistant action
│   └── action.yml
├── claude-engineer/      # Persistent engineer action
│   ├── action.yml
│   └── agents/           # Engineer-specific agents
├── claude-agent/         # Scheduled agent action
│   ├── action.yml
│   └── agents/           # Agent-specific agents
├── claude-report/        # Execution summary action
│   └── action.yml
├── scripts/              # Repo-level utility scripts
├── tests/                # Test suite
├── docs/                 # Project documentation
└── .github/workflows/    # This repo's own CI workflows
```

## Usage Examples

### Interactive Assistant (Issue Comments)

Triggered by `@claude` mentions in issues and PRs:

```yaml
name: "Claude Issue Assistant"

on:
  issue_comment:
    types: [created]
  issues:
    types: [assigned, labeled]

jobs:
  detect-intent:
    runs-on: ubuntu-latest
    # Intent detection and setup...

  claude-run:
    runs-on: ubuntu-latest
    needs: [detect-intent, setup]
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Claude
        uses: diranged/claude-code-agentic-workflows/claude-respond@v0
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          compose_prompt: "true"
          agent_name: ${{ needs.detect-intent.outputs.agent }}
          issue_comment_id: ${{ needs.setup.outputs.comment_id }}
```

### Scheduled Engineer (Daily Autonomous Operation)

Runs daily with dashboard management:

```yaml
name: "Claude Engineers"

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am UTC
  workflow_dispatch:

jobs:
  docs-engineer:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Documentation Engineer
        uses: diranged/claude-code-agentic-workflows/claude-engineer@v0
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          agent_name: "docs-engineer"
          dashboard_label: "claude-engineer:docs"
          task_label: "claude-engineer:docs-task"
```

### Scheduled Agent (Autonomous Scanning)

Runs on a schedule for proactive issue detection:

```yaml
name: "Claude Security Agent"

on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Mondays at 9am UTC
  workflow_dispatch:

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Security Auditor
        uses: diranged/claude-code-agentic-workflows/claude-agent@v0
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          agent_name: "security-auditor"
          max_issues: "5"
          issue_label: "security:audit"
```

## Prompt Composition

The `compose_prompt` system combines multiple sources to create sophisticated agent prompts:

### Components

- **Instructions** (`claude-core/instructions/`) — Base behavioral instructions
- **Skills** (`claude-core/skills/`) — Composable capability modules
- **Agent personalities** (`claude-core/agents/`) — Specialized roles and behaviors

### Override Chain

1. Repository-local `.github/claude-agents/<name>.md`
2. Built-in agents (`claude-core/agents/`, `claude-engineer/agents/`)
3. Inline `prompt` parameter

### Usage

```yaml
- uses: diranged/claude-code-agentic-workflows/claude-respond@v0
  with:
    compose_prompt: "true"
    agent_name: "agentic-designer"
    extra_agents_path: ".github/claude-agents"
```

## Contributing

This project uses `make test` for validation. The test suite covers:

- Input validation for all actions
- Prompt composition correctness
- Script functionality
- Workflow syntax validation

For detailed documentation, see the [`docs/`](docs/) directory.

## License

This project is provided as-is for educational and development purposes. See individual action files for specific licensing terms.