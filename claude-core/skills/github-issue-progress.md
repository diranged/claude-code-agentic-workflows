# Skill: GitHub Issue Progress Tracking

## Updating the Tracking Comment

Use this command to update the tracking comment on the issue:

```bash
gh api \
  --method PATCH \
  "/repos/${GITHUB_REPOSITORY}/issues/comments/${COMMENT_ID}" \
  -f body="$(cat <<'COMMENT_EOF'
<div data-claude-tracking-comment hidden></div>

## Status: <STATUS>

**Run:** [View workflow run](<RUN_URL>)

### Progress

- [x] Completed step
- [ ] Pending step

### Details

<details>
<summary>Click to expand</summary>

Your detailed content here.

</details>
COMMENT_EOF
)"
```

**Important:** Replace `<RUN_URL>` with the actual run URL from the runtime context. This is provided as the `Run URL` field. Always include this link so reviewers can navigate directly to the workflow logs.

Replace `<STATUS>` with one of:
- **In Progress** — actively working
- **Needs Input** — blocked, waiting for human feedback
- **Completed** — finished successfully
- **Failed** — encountered an unrecoverable error

## Rules

1. Update the tracking comment at meaningful milestones (starting work, design posted, PR created, blocked).
2. Always preserve the `<div data-claude-tracking-comment hidden></div>` HTML marker as the first line.
3. Always include the workflow run link (`**Run:** [View workflow run](...)`) so reviewers can inspect logs.
4. When blocked or needing clarification, set status to **Needs Input** and clearly describe what you need.
5. Keep the comment body concise — use `<details>` blocks for verbose content.
