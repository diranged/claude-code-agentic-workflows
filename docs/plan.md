# Claude Code Agentic Workflows — Project Plan

**Repo:** `diranged/claude-code-agentic-workflows`  
**Date:** March 2026  
**Status:** Initial scaffold pushed; ready for implementation

---

## Project Overview

A set of reusable GitHub Actions composite actions that let any org add Claude-powered automation to their repos with minimal setup. Two core actions:

- **claude-respond** — Interactive assistant triggered by `@claude` mentions in issues/PRs
- **claude-agent** — Scheduled autonomous agents that proactively analyze repos and open issues

Both actions wrap `anthropics/claude-code-action@v1` and handle authentication, prompt resolution, and argument assembly so consuming workflows stay clean.

---

## Architecture Decisions

### Composite Actions Only (No Reusable Workflows)

GitHub requires reusable workflows to live in `.github/workflows/`, which is messy for consumers importing from an external repo. Composite actions have no such constraint — they reference cleanly:

```yaml
uses: diranged/claude-agentic-workflows/claude-respond@v1
```

Consuming orgs own job-level concerns (runner selection, permissions, schedule triggers). The actions handle everything inside the job step.

### Repository Must Be Public

GitHub only allows cross-org `uses:` references to public repos. The repo must remain public for other organizations to consume the actions.

### Authentication Strategy

Dual-path auth support:

| Method | Input | Billing | Token Lifetime |
|--------|-------|---------|----------------|
| **OAuth (primary)** | `claude_code_oauth_token` | Subscription-based (fixed cost) | ~1 year via `claude setup-token` |
| **API Key (fallback)** | `anthropic_api_key` | Per-token billing | Until revoked |

Detection logic: OAuth takes precedence when both are present. The action sets an `AUTH_METHOD` env var and fails fast with an actionable error if the OAuth token is expired.

This is the key differentiator vs. GitHub Agentic Workflows (gh-aw) — Claude Max subscribers pay nothing extra per agent run.

---

## Repository Structure

```
claude-code-agentic-workflows/
├── claude-respond/action.yml       # Interactive assistant composite action
├── claude-agent/action.yml         # Scheduled agent composite action
├── agents/                         # Default agent personalities
│   ├── security-auditor.md
│   ├── janitor.md
│   ├── performance-reviewer.md
│   ├── docs-reviewer.md
│   ├── test-coverage.md
│   └── architect.md
├── examples/                       # Copy-paste workflow templates
│   ├── claude.yml                  # Interactive assistant
│   ├── agent-security.yml          # Single agent
│   ├── agent-janitor.yml           # Single agent
│   └── agents-all.yml             # All 6 agents, staggered schedule
├── docs/
└── README.md
```

---

## Action Specifications

### claude-respond/action.yml

Handles interactive `@claude` mentions in issues and PRs.

**Required inputs** (one of the auth pair):
- `claude_code_oauth_token` / `anthropic_api_key`
- `app_id` — GitHub App ID
- `app_private_key` — GitHub App private key

**Optional inputs:**
- `trigger_phrase` (default: `@claude`)
- `assignee_trigger` — trigger on issue assignment
- `label_trigger` — trigger on label application
- `max_turns` (default: 20)
- `model` — override Claude model
- `timeout_minutes` (default: 60)
- `allowed_tools` / `disallowed_tools`
- `claude_args` — multiline passthrough args
- `additional_permissions`
- `mcp_config` / `settings`
- `append_system_prompt`

**Implementation steps:**
1. Generate GitHub App token via `actions/create-github-app-token@v2`
2. Validate auth (detect OAuth vs API key), set `AUTH_METHOD` env var
3. Build `claude_args` from structured inputs
4. Invoke `anthropics/claude-code-action@v1` with conditional auth

### claude-agent/action.yml

Handles scheduled autonomous agent runs.

**Required inputs** (one of the auth pair, plus):
- `agent_name` — personality to load (e.g., `security-auditor`)
- `app_id` / `app_private_key`

**Optional inputs:**
- `agent_prompt_override` — inline prompt (skips file resolution)
- `max_turns` (default: 30)
- `model` / `timeout_minutes` (default: 30)
- `max_issues` (default: 5)
- `issue_label` (default: `agent:<name>`)
- `dry_run` (default: false)
- `allowed_tools` / `disallowed_tools`
- `claude_args` / `additional_permissions`
- `mcp_config` / `settings`

**Prompt resolution order:**
1. `.github/claude-agents/<name>.md` in the consuming repo (override)
2. `agents/<name>.md` in this action's repo (built-in default)
3. `agent_prompt_override` input (inline, for one-offs)
4. Fail if none found

**Implementation steps:**
1. Generate GitHub App token
2. Validate auth
3. Resolve agent prompt via the priority chain above
4. Wrap resolved prompt with operational guardrails:
   - Max issues cap
   - Issue labeling instructions
   - Dry-run flag behavior
   - Duplicate avoidance (check existing open issues with same label)
5. Write wrapped prompt to `/tmp/agent-prompt.md`
6. Build `claude_args`
7. Invoke `anthropics/claude-code-action@v1` with `prompt_file`

---

## Agent Personality System

Six default agents ship in `agents/`:

| Agent | Schedule | Max Issues | Focus |
|-------|----------|------------|-------|
| 🔒 security-auditor | Weekly (Mon 6am) | 5 | Injection, auth gaps, secrets exposure, CVEs |
| 🧹 janitor | Weekly (Tue 6am) | 4 | Dead code, stale TODOs, outdated deps |
| ⚡ performance-reviewer | Weekly (Wed 6am) | 3 | N+1 queries, memory leaks, bundle size |
| 📖 docs-reviewer | Weekly (Fri 6am) | 3 | README drift, broken links, missing API docs |
| 🧪 test-coverage | Bi-weekly (Thu 6am) | 3 | Untested paths, flaky tests, edge cases |
| 🏗️ architect | Monthly (1st, 8am) | 2 | Coupling, abstractions, API design, scalability |

Each agent prompt is a Markdown file describing focus areas, standards, and output format. The `claude-agent` action wraps these with operational guardrails at runtime.

**Customization:** Consuming repos can override any agent by placing a file at `.github/claude-agents/<agent-name>.md`. This takes precedence over the built-in default.

---

## Example Workflow Patterns

### Interactive Assistant (claude.yml)

Triggers: `issue_comment`, `pull_request_review_comment`, `issues` (opened/assigned)

```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]

jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - uses: diranged/claude-code-agentic-workflows/claude-respond@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          app_id: ${{ secrets.CLAUDE_APP_ID }}
          app_private_key: ${{ secrets.CLAUDE_APP_PRIVATE_KEY }}
```

### All Agents on Staggered Schedule (agents-all.yml)

Uses `github.event.schedule` matching to run different agents from a single workflow file with multiple cron entries:

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'   # Mon — security
    - cron: '0 6 * * 2'   # Tue — janitor
    - cron: '0 6 * * 3'   # Wed — performance
    - cron: '0 6 * * 4'   # Thu (bi-weekly) — test coverage
    - cron: '0 6 * * 5'   # Fri — docs
    - cron: '0 8 1 * *'   # 1st of month — architect
  workflow_dispatch:
    inputs:
      agent:
        description: 'Agent to run manually'
        type: choice
        options: [security-auditor, janitor, performance-reviewer, docs-reviewer, test-coverage, architect]

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: diranged/claude-code-agentic-workflows/claude-agent@v1
        with:
          agent_name: <resolved from schedule or input>
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          app_id: ${{ secrets.CLAUDE_APP_ID }}
          app_private_key: ${{ secrets.CLAUDE_APP_PRIVATE_KEY }}
```

---

## Rate Limiting Strategy

- Stagger agent schedules across different days/times (see table above)
- Start conservative (weekly), scale up after understanding headroom
- Use `max_turns` to cap token consumption per run
- Monitor HTTP 429 errors in workflow logs
- Reserve headroom for unpredictable interactive `@claude` usage
- `max_issues` caps output volume per agent run

---

## Comparison with GitHub Agentic Workflows (gh-aw)

| Dimension | gh-aw | This Project |
|-----------|-------|-------------|
| Config format | Markdown → compiled YAML | Standard Actions YAML |
| Security | safe-outputs isolation, threat detection | Standard Actions permissions |
| Models | Multi-model (Copilot, Claude, Codex, Gemini) | Claude-only |
| Auth | API key / Copilot subscription | OAuth token (Claude Max) or API key |
| Agent definition | Markdown workflow files | Markdown personality prompts |
| CLI dependency | `gh-aw` CLI for compilation | None |
| Maturity | Technical preview (GitHub-backed) | New / community |

**Biggest gap:** gh-aw has stronger security via safe-outputs isolation and threat detection. This project relies on standard GitHub Actions permissions.

**Key advantage:** Claude Max subscribers avoid per-token API costs entirely via OAuth auth. gh-aw currently has no equivalent subscription-based path.

**Convergence path:** If gh-aw adds OAuth/subscription auth support, migrating agent definitions to their Markdown format would be straightforward.

---

## Implementation Priorities

### Phase 1: Core Actions (Now)
- [x] Repository structure and scaffold
- [x] README with quick start guide
- [x] `claude-respond/action.yml` — full implementation
- [x] `claude-agent/action.yml` — full implementation
- [x] All 6 agent personality prompts
- [x] Example workflow files
- [ ] Test with a real repo (end-to-end validation)

### Phase 2: Hardening
- [ ] Validate OAuth token expiry detection and error messaging
- [ ] Test prompt resolution chain (override → built-in → inline → fail)
- [ ] Verify `${{ github.action_path }}` resolves correctly for agent prompts
- [ ] Duplicate issue detection (label-based dedup before creating new issues)
- [ ] Dry-run mode validation

### Phase 3: Documentation & Polish
- [ ] CLAUDE.md for the repo itself (so Claude Code sessions have full context)
- [ ] Contributing guide
- [ ] Versioning strategy (tag `v1` for stable composite action references)
- [ ] Changelog

### Phase 4: Future Enhancements
- [ ] Security hardening (consider safe-outputs-like isolation)
- [ ] Agent run summaries (post to a tracking issue or Slack)
- [ ] Multi-repo support (org-level agent runs)
- [ ] Cost tracking / token usage reporting
- [ ] Local model fallback via Ollama (for lower-complexity agent runs on K3S cluster)

---

## Key Technical Notes

- `${{ github.action_path }}` in composite actions resolves relative to the action directory, making built-in agent prompt resolution work correctly
- Auth detection uses conditional expressions: `${{ env.AUTH_METHOD == 'oauth' && inputs.claude_code_oauth_token || '' }}`
- Multiline outputs use heredoc syntax: `echo "args<<EOF" >> "$GITHUB_OUTPUT"`
- `anthropics/claude-code-action@v1` accepts both `prompt` (inline string) and `prompt_file` (path to .md file) — the agent action uses `prompt_file`

---

## Context Transfer

This plan was developed in a claude.ai conversation. To bridge context into Claude Code CLI sessions working on this repo:

1. Drop this file as `PLAN.md` in the repo root
2. Generate a `CLAUDE.md` capturing conventions and architectural decisions
3. Claude Code will pick up both files automatically when opened in the repo directory
