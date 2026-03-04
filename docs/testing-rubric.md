# Issue-Triggered Claude Workflows: Testing Rubric

## Overview

This rubric defines test scenarios for the issue-triggered Claude workflow system.
Each scenario specifies the trigger, expected behavior, and pass/fail criteria.

---

## Test Scenarios

### Scenario 1: Designer Agent — Simple Task

**Trigger:** Create issue, comment `@claude`

**Issue:**
> Title: Add a hello-world shell script
>
> Add a simple `hello.sh` script to the repo root that prints "Hello, World!"
> and exits with code 0. Include a basic test.

**Expected behavior:**
1. ✅ Workflow triggers (`claude-issue.yml` → `detect-intent` → `agentic-designer`)
2. ✅ 🚀 reaction appears on the `@claude` comment
3. ✅ Tracking comment created with "Initializing" status and run link
4. ✅ Claude runs the designer agent (read-only, no code changes)
5. ✅ Tracking comment updated with a design document containing:
   - Summary of proposed changes
   - Files to create/modify
   - Implementation approach
   - Test plan
6. ✅ Status set to "Needs Input"
7. ✅ Footer says: "To implement this design, comment: `@claude implement`"
8. ❌ No branches created, no PRs opened, no files modified

**Pass criteria:** 6/8 checks pass (tracking comment + design doc are critical)

---

### Scenario 2: Developer Agent — Implement After Design

**Trigger:** Comment `@claude implement` on an issue that has a design

**Prerequisite:** Scenario 1 completed successfully (design posted)

**Expected behavior:**
1. ✅ Workflow triggers with `agentic-developer` agent
2. ✅ 🚀 reaction on the `@claude implement` comment
3. ✅ New tracking comment created with "Initializing" status
4. ✅ Claude creates a feature branch (`claude/{issue_number}-*`)
5. ✅ Claude implements the changes described in the design
6. ✅ Claude runs tests (if applicable)
7. ✅ Claude opens a PR with `Closes #{issue_number}` in the body
8. ✅ Tracking comment updated to "Completed" with PR link

**Pass criteria:** PR opened with working implementation matching the design

---

### Scenario 3: Designer Agent — Multi-File Refactor

**Trigger:** Create issue, comment `@claude`

**Issue:**
> Title: Rename claude-core instructions directory to prompts/
>
> Rename `claude-core/instructions/` to `claude-core/prompts/` and update
> all references in `compose_prompt.sh` and tests. This is a refactoring
> exercise — no behavioral changes.

**Expected behavior:**
- Designer produces a design listing all files to modify
- Design correctly identifies compose_prompt.sh and test_compose_prompt.py
- No code changes made (designer is read-only)

**Pass criteria:** Design identifies all affected files accurately

---

### Scenario 4: Edge Case — No @claude Mention

**Trigger:** Create issue, comment without `@claude`

**Expected behavior:**
- Workflow does NOT trigger (or triggers but `detect-intent` gates it)
- No tracking comment, no reactions

**Pass criteria:** No workflow activity

---

### Scenario 5: Edge Case — PR Comment (Should Skip)

**Trigger:** Comment `@claude` on a pull request

**Expected behavior:**
- `claude-issue.yml` should NOT trigger (it filters out PR-linked issues)
- The existing `test-claude-respond.yml` may handle this separately

**Pass criteria:** `claude-issue.yml` does not run

---

## Evaluation Scoring

For each scenario, score on these dimensions:

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Trigger correctness** | 20% | Right workflow fires, right agent selected |
| **Setup phase** | 15% | Reaction added, tracking comment created with run link |
| **Agent behavior** | 30% | Agent follows its role (designer=read-only, developer=implements) |
| **Output quality** | 20% | Design is thorough / PR is clean and working |
| **Comment management** | 15% | Tracking comment updated properly, correct status |

**Overall score = weighted sum across dimensions**

- **Excellent (90-100%):** All critical paths work, output is high quality
- **Good (70-89%):** Core flow works, minor issues with output or tracking
- **Needs Work (50-69%):** Flow triggers but agent behavior is off
- **Broken (<50%):** Workflow doesn't trigger or fails early

---

## Iteration Log

Track test runs and fixes here:

| Run | Date | Scenario | Score | Issues Found | Fix PR |
|-----|------|----------|-------|-------------|--------|
| 1 | 2026-03-04 | S1 (issue #18) | 0% | Setup job 403 (missing permissions) | #19 |
| 2 | 2026-03-04 | S1 (issue #21) | 0% | Workflow YAML invalid (block scalar indentation), debug workflow competing | #22 |
| 3 | 2026-03-04 | S1 (issue #23) | 15% | Claude Code Bash tool denied (missing allowed_tools) | #24 |
| 4 | 2026-03-04 | S1 (issue #25) | 98% | All checks pass | - |
| 5 | 2026-03-04 | S2 (issue #25) | 100% | All checks pass, PR #26 opened | - |
