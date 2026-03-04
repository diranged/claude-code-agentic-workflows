# GitHub Environment

## Available Tools

- `GITHUB_TOKEN` is set in the environment with permissions for issues, pull requests, and contents.
- The `gh` CLI is available and authenticated. Use it for all GitHub API interactions.
- The repository is checked out at the workspace root.

## Comment Management

- A **tracking comment** has been created on the issue for you to post progress updates.
- **Never create new top-level comments** on the issue — always update the existing tracking comment.
- The tracking comment ID is provided in the runtime context below.
- Use `gh api` with PATCH to update the comment body.

## Workflow Run Links

- The workflow run URL is provided in the runtime context as `Run URL`.
- **Always include this link** in your tracking comment and any PR you create so reviewers can navigate to the CI logs.
- Format: `**Run:** [View workflow run](<URL>)`
