# GitHub Environment

## Available Tools

- `GITHUB_TOKEN` is set in the environment with permissions for issues, pull requests, and contents.
- The repository is checked out at the workspace root.

## GitHub API Access

- The `gh` CLI is installed and authenticated. **Always use `gh`** for GitHub API interactions — it handles authentication, pagination, and URL encoding automatically.
- **Do not fall back to `curl`.** If `gh` fails, report the error — do not attempt workarounds.
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

## File Permissions

- The GitHub token does **not** have `workflows` write permission. You **cannot push changes to `.github/workflows/` files**. If the design requires workflow file changes, implement everything else and note the workflow changes needed in the tracking comment.

## Escalating to Humans

When you are blocked and need human input (ambiguous requirements, conflicting constraints, missing context):

1. Check the runtime context for `Notify Owners`. If present, assign the issue to them:
   ```bash
   gh issue edit $ISSUE_NUMBER --repo "$GITHUB_REPOSITORY" --add-assignee "<owner>"
   ```
   For multiple owners (comma-separated), add each one.
2. Update the tracking comment with status **Needs Input** and clearly describe what you need.
3. Do **not** advance pipeline labels when escalating — leave the issue for human review.

## Shell Usage Rules

- **Always use absolute paths** in Bash commands. The working directory may not be what you expect between calls.
- The workspace root is available as `$GITHUB_WORKSPACE` or can be found via `pwd` on the first call.
- **Never use `cd`** to change directories in Bash commands — use absolute paths instead.

## Efficiency Rules

- **Use targeted searches.** Never glob the entire repository (`**/*`). Instead, use specific patterns like `.github/workflows/*.yml` or `tests/**/*.py`.
- **Don't explore action internals.** Files in `claude-core/scripts/`, `claude-core/action.yml`, and `claude-respond/` are internal plumbing — do not read them unless the issue specifically requires modifying them.
- **Check dependencies before coding.** Before writing code that requires external packages, verify they are available (`python3 -c "import yaml"`, `which jq`, etc.). Prefer solutions with zero external dependencies when possible.
- **Minimize tool calls.** Batch parallel reads when examining multiple files. Don't re-read files you've already seen.
- **Do not use TodoWrite excessively.** Track progress in the tracking comment instead. At most 2 TodoWrite calls per session.
