# Contributing Guide

Welcome to the claude-code-agentic-workflows project! This guide will help you get started with development and understand our contribution process.

## Getting Started

### Prerequisites

- Python 3.x
- `make` (for running tests)
- Git
- GitHub CLI (`gh`) or curl for API access

### Clone and Setup

```bash
git clone https://github.com/diranged/claude-code-agentic-workflows.git
cd claude-code-agentic-workflows
```

## Development

### Project Structure

This repository contains 6 composite actions:

- **`claude-setup/`** — Pre-Claude orchestration (trigger validation, tracking comments, checkout, pre-run setup)
- **`claude-core/`** — Foundation action handling auth, argument composition, prompt composition, and Claude invocation
- **`claude-respond/`** — Interactive assistant: orchestrates setup → intent detection → core → report
- **`claude-engineer/`** — Persistent autonomous engineer agents with dashboard management (wraps claude-respond)
- **`claude-agent/`** — Scheduled autonomous agent for proactive scanning and issue creation (wraps claude-respond)
- **`claude-report/`** — Execution summary generator and artifact uploader

Each action has its own `action.yml` specification and may include:
- `agents/` — Agent personality definitions
- `tests/` — Action-specific tests
- `Makefile` — Test runner configuration

Additional directories:
- `claude-core/instructions/` — Base behavioral instructions
- `claude-core/skills/` — Composable capability modules
- `claude-core/scripts/` — Utility scripts
- `examples/` — Example workflow files
- `docs/` — Project documentation

### Running Tests

Run all tests from the repository root:

```bash
make test
```

This discovers and runs tests in all subdirectories. If `make` is not available, you can run tests manually:

```bash
cd <directory>
python3 -m venv .venv
.venv/bin/pip install -r ../requirements-test.txt
.venv/bin/python3 -m unittest discover . -v
```

Individual action tests:
- `claude-setup/tests/` — Trigger validation, tracking, token resolution scripts
- `claude-core/tests/` — Input validation, arg building, prompt composition, intent detection
- `claude-respond/tests/` — Action structure validation, detect_intent script
- `claude-engineer/tests/` — Action structure validation, input forwarding
- `claude-agent/tests/` — Action structure, agent configuration
- `claude-report/tests/` — Report generation
- `tests/` — Workflow validation, repo-level utilities

## Conventions

### Conventional Commits

All commit messages and PR titles **must** follow conventional commit format:

```
type(scope): lowercase description
```

**Types:** `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `ci`

**Scopes:** `claude-core`, `claude-respond`, `claude-engineer`, `claude-agent`, `claude-report`, `docs`, `workflows`, `agents`

**Examples:**
- `feat(claude-core): add new authentication method`
- `fix(claude-respond): handle missing issue number`
- `docs(agents): update agentic-designer documentation`

Scope is optional unless the change affects multiple areas.

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following existing code patterns
3. Run tests: `make test`
4. Create PR with conventional commit title
5. PRs use **squash merge only** — all commits will be squashed into a single commit on merge

### Code Style

- Follow existing patterns in the codebase
- Preserve surrounding style (indentation, formatting, idioms)
- Write tests for new functionality
- Do not add unnecessary dependencies, comments, or abstractions

## Agent Development

### Built-in Agents

Agents are defined as Markdown files containing prompts and instructions:

- `claude-core/agents/` — 7 general-purpose agents
- `claude-engineer/agents/` — 3 engineer-specific agents
- `claude-agent/agents/` — 1 security-focused agent

### Custom Agents

Repository consumers can override built-in agents by creating:
```
.github/claude-agents/<name>.md
```

Override precedence:
1. Repository-local `.github/claude-agents/<name>.md` (highest)
2. Built-in action agents
3. Inline `prompt` parameter (fallback)

### Creating New Agents

When adding new built-in agents:
1. Create `<agent-name>.md` in appropriate `agents/` directory
2. Follow existing agent file structure and tone
3. Add agent to documentation
4. Consider if it belongs in general (`claude-core`) or specialized action

## Upstream Dependencies

### Security Practice

`claude-core` pins its upstream dependency to a specific commit hash:

```yaml
# claude-core/action.yml
uses: anthropics/claude-code-action@e763fe78... # pinned commit
```

This is a security best practice. When updating upstream dependencies:

1. Review the changelog and diff
2. Test thoroughly with the new version
3. Update to a specific commit hash (not a moving tag like `@main`)
4. Update the pin deliberately, don't just bump to latest

## Release Process

### Versioning Strategy

- **Monolithic versioning**: All 6 actions are versioned together
- **Semver tags**: `v0.x.y` format using annotated tags
- **Floating major tag**: `v0` points to latest `v0.x.y` release

### Release Checklist

When creating a new release:

#### 1. Update Changelog
```bash
# Move items from [Unreleased] to [0.x.y] section in CHANGELOG.md
```

#### 2. Update Internal Action References
Update these files to reference the new version tag (search for `@integ-testing`):

- `claude-respond/action.yml` — `claude-setup@v0.x.y`, `claude-core@v0.x.y`, `claude-report@v0.x.y`
- `claude-engineer/action.yml` — `claude-respond@v0.x.y`
- `claude-agent/action.yml` — `claude-respond@v0.x.y`

#### 3. Update Documentation References
- `README.md` — Update usage examples (4 references)
- `examples/*.yml` — Update all example workflow files (6 references including comments)

#### 4. Create and Push Tags
```bash
# Create annotated tag
git tag -a v0.x.y -m "v0.x.y"

# Push the version tag
git push origin v0.x.y

# Update the floating tag
git tag -fa v0 v0.x.y
git push origin v0 --force
```

#### 5. Create GitHub Release
Create a GitHub Release from the version tag with:
- Release title: `v0.x.y`
- Release notes summarizing changes from CHANGELOG.md

#### 6. Verify Cross-Repo Usage
Test that external repositories can use the new tag:
```yaml
uses: diranged/claude-code-agentic-workflows/claude-respond@v0
```

### Post-Release
After releasing, update internal references back to `@integ-testing` for development:
- Revert the 5 internal action.yml references from `@v0.x.y` back to `@integ-testing`
- The `integ-testing` tag normally points at `main` and is used for integration testing

## Getting Help

- Check existing issues and PRs
- Review the [project documentation](docs/)
- For bugs or feature requests, open an issue with detailed information
- For questions about usage, refer to the README and example workflows

## License

This project is open source. See the repository for license information.