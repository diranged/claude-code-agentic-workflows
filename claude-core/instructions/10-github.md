# GitHub Environment

## Available Tools

- `GITHUB_TOKEN` is set in the environment with permissions for issues, pull requests, and contents.
- The `gh` CLI is available and authenticated. Use it for all GitHub API interactions.
- The repository is checked out at the workspace root.

## Authentication

- Use `gh api` for all GitHub API calls. The `gh` CLI is pre-configured with the correct token.
- **Do not** search for the `gh` binary or try alternative authentication methods. If `gh` fails, report the error immediately rather than attempting workarounds.
- **Never print or log token values.** If you need to verify a token exists, use `echo "TOKEN_SET: ${GITHUB_TOKEN:+yes}"` — never echo the actual value.

## Comment Management

- A **tracking comment** has been created on the issue for you to post progress updates.
- **Never create new top-level comments** on the issue — always update the existing tracking comment.
- The tracking comment ID is provided in the runtime context below.
- Use `gh api` with PATCH to update the comment body.

## Workflow Run Links

- The workflow run URL is provided in the runtime context as `Run URL`.
- **Always include this link** in your tracking comment and any PR you create so reviewers can navigate to the CI logs.
- Format: `**Run:** [View workflow run](<URL>)`

## Efficiency Rules

- **Use targeted searches.** Never glob the entire repository (`**/*`). Instead, use specific patterns like `.github/workflows/*.yml` or `tests/**/*.py`.
- **Don't explore action internals.** Files in `claude-core/scripts/`, `claude-core/action.yml`, and `claude-respond/` are internal plumbing — do not read them unless the issue specifically requires modifying them.
- **Check dependencies before coding.** Before writing code that requires external packages, verify they are available (`python3 -c "import yaml"`, `which jq`, etc.). Prefer solutions with zero external dependencies when possible.
- **Minimize tool calls.** Batch parallel reads when examining multiple files. Don't re-read files you've already seen.
