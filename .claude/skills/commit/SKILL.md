---
name: commit
description: Stage and commit changes locally without pushing or creating a PR. Pass optional args for commit message context (e.g., ticket number).
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Local Commit

Follow these steps to stage and commit changes locally:

1. **Check state** — Run `git status` (no `-uall`), `git diff --staged`, `git diff`, and `git log --oneline -5` in parallel to understand staged/unstaged changes and recent commit style.

2. **Stage files** — Respect any files already staged by the user. For unstaged and untracked files, add them by specific file path — NEVER use `git add -A` or `git add .`. If there are untracked files, list them and ask the user which ones to include before staging. Never stage `.env`, credentials, or `settings.local.json`.

3. **Commit** — Write a concise conventional commit message (1-2 sentences) that focuses on the *why*. If args include a ticket reference, include it. End with:
   ```
   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
   Use a HEREDOC to pass the message.

4. **Verify** — Run `git status` after the commit to confirm success.

5. **Report** — Output the commit hash and a brief summary. Do NOT push or create a PR.

If any step fails, stop and report the error rather than retrying blindly.
