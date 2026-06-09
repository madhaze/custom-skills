# pr-feedback-fix

Wait for PR review comments, then fetch and address them with explicit user approval before committing.

## Overview

Checks a PR for comments from humans or CodeRabbit. If none exist yet, schedules a re-check in 2 minutes (staying within the prompt cache window). When comments arrive, presents a numbered list with recommendations, waits for the user to confirm which items to address, implements the fixes, shows a diff, and only commits and pushes after explicit approval.

This skill is invoked automatically by `/pr` after creating a PR, but can also be run directly on any existing PR.

## Usage

```
/pr-feedback-fix
/pr-feedback-fix 42
```

Pass an optional PR number. If omitted, it detects the PR from the current branch.

## What it does

1. Determines the PR number from args or the current branch
2. Checks for comments from non-bot users and from CodeRabbit
3. If no comments exist: schedules a 2-minute wakeup and informs you it's waiting
4. Once comments exist: presents a numbered summary with recommendations (fix / skip / alternative)
5. Asks which items to address — makes no changes until you confirm
6. Implements approved fixes (runs build steps like `cex` if needed)
7. Shows `git diff` and asks for confirmation before committing
8. Commits with `fix: address PR review feedback` and pushes

## Dependencies

- `git` and `gh` (GitHub CLI) in PATH
- `ScheduleWakeup` tool — available in Claude Code for the polling loop
- An open PR on the current branch (or a PR number passed as arg)
