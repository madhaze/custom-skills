# commit

Stage and commit changes locally without pushing or creating a PR.

## Overview

Handles the full local commit flow safely: checks git state, identifies staged and unstaged changes, asks about any untracked files before staging, writes a conventional commit message, and verifies success. Never pushes or opens a PR — use `/pr` for that.

## Usage

```
/commit
/commit TICKET-123
```

Pass an optional ticket number or context string as args and it will be included in the commit message.

## What it does

1. Runs `git status`, `git diff --staged`, `git diff`, and `git log` in parallel to understand current state and recent commit style
2. Stages files by specific path — never uses `git add -A` or `git add .`
3. Lists any untracked files and asks which ones to include before staging
4. Writes a concise conventional commit message focused on the *why*
5. Runs `git status` after the commit to confirm success
6. Reports the commit hash and a brief summary

## Safety rules

- Never stages `.env`, credentials, or `settings.local.json`
- Never pushes or creates a PR
- Stops and reports on failure rather than retrying blindly

## Dependencies

- `git` available in PATH
- A git repository in the working directory
