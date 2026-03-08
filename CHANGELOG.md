# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `claude:auto_advance` label for automatic pipeline progression through design → review → implement stages

## [0.1.0] - 2026-03-05

### Added

- Initial versioning system with v0 release strategy
- All 5 composite actions: `claude-core`, `claude-respond`, `claude-engineer`, `claude-agent`, `claude-report`
- 10 agent personalities across 3 action directories:
  - 7 built-in agents in `claude-core/agents/`: agentic-designer, agentic-developer, architect, docs-reviewer, janitor, performance-reviewer, test-coverage
  - 2 engineer agents in `claude-engineer/agents/`: code-janitor, docs-engineer
  - 1 security agent in `claude-agent/agents/`: security-auditor
- Prompt composition system with base instructions and composable skills
- Agent override chain allowing repository-local customization
- OAuth-first authentication with API key fallback
- Dual-path billing support (Claude Max subscription vs per-token)
- Comprehensive test suite with action input parity validation
- Example workflow files demonstrating all action usage patterns

### Changed

- Internal action references updated from `@main` to `@v0` for version coherence
- README usage examples updated to reference `@v0` instead of `@main`
- Example workflows updated to use `@v0` versioning

[unreleased]: https://github.com/diranged/claude-code-agentic-workflows/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/diranged/claude-code-agentic-workflows/releases/tag/v0.1.0