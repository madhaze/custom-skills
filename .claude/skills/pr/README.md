# pr

Stage, commit, push, and open a pull request — then automatically watch for and address review comments.

## Overview

Full end-to-end PR workflow: stages files (prompts about untracked ones), writes a conventional commit message, pushes the branch, creates the PR via `gh pr create` with a formatted summary and test-plan body, then automatically invokes `/pr-feedback-fix` to poll for and address review comments.

## Usage

```
/pr
/pr TICKET-123
```

Pass a ticket number as args to include it in the commit message and PR title (branch names containing a Jira-style key like `DONI-341` are detected automatically).

## What it does

1. Checks git state: status, staged diff, and recent commit log
2. Stages files by specific path — never uses `git add -A` or `git add .`; prompts about untracked files
3. Writes a conventional commit message with optional ticket reference
4. Pushes the branch (`-u` flag if no upstream yet)
5. Creates the PR with a short title and a body containing a summary and testing checklist
6. Reports the PR URL
7. Invokes `/pr-feedback-fix` to watch for review comments and address them

## Safety rules

- Never stages `.env`, credentials, or `settings.local.json`
- Stops and reports on failure rather than retrying blindly

## Dependencies

- `git` available in PATH
- `gh` (GitHub CLI) authenticated and configured for the repo
- [`pr-feedback-fix`](../pr-feedback-fix/README.md) skill (invoked automatically after PR creation)
