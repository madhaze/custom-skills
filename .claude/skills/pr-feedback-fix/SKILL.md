---
name: pr-feedback-fix
description: Wait for PR review comments from the user or CodeRabbit, then fetch and address them. Pass optional PR number as arg (defaults to current branch PR).
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Glob
  - ScheduleWakeup
---

# Address PR Review Comments

Follow these steps to wait for and resolve PR feedback:

1. **Get PR info** — If a PR number is provided in args, use it. Otherwise detect it from the current branch with `gh pr view --json number -q .number`.

2. **Check for comments** — Run:
   ```
   gh api repos/{owner}/{repo}/pulls/<number>/comments
   gh pr view <number> --json reviews,comments
   ```
   Look for any comments from the user (non-bot, non-github-actions) or from CodeRabbit (author login contains "coderabbitai").

3. **If no comments found yet** — Schedule a wakeup and pass the same `/pr-feedback-fix <number>` prompt so this skill re-enters on the next tick. Use a 120-second interval (stays within the prompt cache window). Inform the user that you're waiting for review comments and will check back in 2 minutes. Then stop — do NOT proceed to step 4 until comments exist.

4. **List actionable items** — Once comments are present, present a numbered summary of each comment that requires a code change. Skip resolved comments and pure acknowledgements. For each item, include your recommendation (fix, skip, or alternative approach).

5. **Ask the user** — Present the numbered list and ask which items to address. Do NOT make any changes until the user confirms. Wait for explicit approval before proceeding.

6. **Address approved items** — For each approved item:
   a. Read the relevant file and understand the context around the flagged code.
   b. Implement the fix (or explain why an alternative is better).
   c. If the change affects files that require a build step or config export (e.g., Drupal `cex`), run those before committing.

7. **Show changes for review** — Run `git diff` and summarize what was changed. Do NOT commit or push yet. Ask the user to confirm the changes look correct.

8. **Commit and push** — Only after user approval, stage the changed files, commit with message:
   ```
   fix: address PR review feedback
   ```
   Then push.

9. **Report** — Summarize what was changed for each comment.

Do NOT make changes beyond what the review comments request. If a comment is ambiguous, ask before changing code.
