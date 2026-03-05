# CLAUDE.md

## Project

GitHub Actions composite actions for agentic Claude Code workflows. Two-phase design->implement flow triggered by `@claude` on issues.

## Architecture

- `claude-core/` — core composite action (auth, args, prompt composition, Claude invocation)
- `claude-respond/` — wraps claude-core + claude-report (thin passthrough)
- `claude-engineer/` — persistent engineer agents with dashboard management
- `claude-report/` — execution summary and artifact upload
- `claude-core/instructions/` — base instructions loaded every run
- `claude-core/skills/` — skills loaded every run
- `claude-core/agents/` — built-in agent definitions
- `claude-engineer/agents/` — engineer-specific agent definitions (loaded via `extra_agents_path`)

## Conventions

### Commits and PRs

- **Use conventional commits** for all commit messages and PR titles.
  - Format: `type(scope): description` (e.g., `feat(core): add notify_owners input`)
  - Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `ci`
  - Scopes: `claude-core`, `claude-respond`, `claude-engineer`, `claude-report`, `docs`, `workflows`, `agents`
- PRs use squash merge only.

### Code

- Tests: `unittest` + `subprocess` pattern, each subdir has own `Makefile` + `requirements-test.txt`
- Root `make test` discovers all `*/Makefile` targets
- Shell scripts in `claude-core/scripts/` — tested via Python subprocess helpers
- `claude-respond/tests/test_action_yml.py` enforces input parity between claude-respond and claude-core

### CI/Runner

- Self-hosted runner: `diranged-claude-code`
- `gh` CLI may NOT be installed on runner — agents use curl fallback
- `make` may not be installed on runner — agents use direct venv+unittest fallback
- GitHub token lacks `workflows` permission — cannot push workflow files directly
