---
name: pr
description: Stage, commit, push, and open a pull request. Pass optional args for commit message context (e.g., ticket number).
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Create Pull Request

Follow these steps to commit, push, and open a PR:

1. **Check state** — Run `git status` (no `-uall`), `git diff --staged`, and `git log --oneline -5` in parallel to understand staged/unstaged changes and recent commit style.

2. **Stage files** — Respect any files already staged by the user. For unstaged and untracked files, add them by specific file path — NEVER use `git add -A` or `git add .`. If there are untracked files, list them and ask the user which ones to include before staging. Never stage `.env`, credentials, or `settings.local.json`.

3. **Commit** — Write a concise conventional commit message (1-2 sentences) that focuses on the *why*. If args include a ticket reference, include it. End with:
   ```
   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
   Use a HEREDOC to pass the message.

4. **Push** — Push the branch with `-u` flag if it doesn't have an upstream yet.

5. **Create PR** — Use `gh pr create` with:
   - A short title (under 70 chars)
   - A body using this format (via HEREDOC):
     ```
     ## Summary
     <1-3 bullet points>

     ## Test plan
     - [ ] Testing checklist items...

     🤖 Generated with [Claude Code](https://claude.com/claude-code)
     ```
   - If the branch name contains a Jira-style ticket (e.g., `DONI-341`), reference it in the title.

6. **Report** — Output the PR URL when done.

7. **Wait for feedback** — Invoke the `/pr-feedback-fix` skill, passing the PR number. It will poll for comments from the user or CodeRabbit and address them once they arrive.

If any step fails, stop and report the error rather than retrying blindly.
