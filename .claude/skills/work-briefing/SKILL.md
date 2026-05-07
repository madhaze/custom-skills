---
name: work-briefing
description: Generate Chris's work briefing by pulling recent Jira and Gmail activity, identifying what's important, and either displaying it in chat or delivering it via Slack DM and email. Use when Chris asks for his "work briefing", "morning briefing", "midday check-in", "what should I work on", "what's on my plate", "what's important today", or when invoked by a scheduled task. Default mode is `chat` (display the summary inline). Mode `send` delivers the same summary to Slack DM and to cclark@phase2.io via email.
---

# Work Briefing

Generates a focused summary of what Chris should work on, based on recent Jira and Gmail activity.

## Inputs

- **mode** (default: `chat`)
  - `chat` — display the summary inline in the current conversation. Do NOT send to Slack or email.
  - `send` — deliver the summary via Slack DM AND email. Do NOT also display it inline (just confirm delivery).
- **window** (default: `morning`)
  - `morning` — look back 24h. On Mondays, look back 72h to cover Friday EOD through the weekend.
  - `midday` — look back 6h. Focus on what's *new since this morning's briefing*.
  - `custom:<hours>` — look back the given number of hours.

If invoked without parameters, default to `mode: chat`, `window: morning` (or `window: midday` if it's after 11am local time).

## 1. Gather Jira activity

Use the Atlassian MCP tools. If `currentUser()` doesn't resolve, use `lookupJiraAccountId` for `cclark@phase2.io` and substitute the accountId.

Compute the JQL window:
- `morning` on Monday → `updated >= -3d`
- `morning` other days → `updated >= -1d`
- `midday` → `updated >= -6h`
- `custom:N` → `updated >= -Nh`

Run via `searchJiraIssuesUsingJql`:

a) Recent activity where Chris is involved:
   `(assignee = currentUser() OR comment ~ currentUser() OR watcher = currentUser()) AND <window> ORDER BY priority DESC, updated DESC`

b) Overdue or due-today open issues (always, regardless of window):
   `assignee = currentUser() AND duedate <= now() AND statusCategory != Done`

c) Newly assigned to Chris in the window:
   `assignee = currentUser() AND assignee changed AFTER <window-start>`

For each issue, extract: key, summary, status, priority, due date, last comment author + short snippet, browse URL.

## 2. Gather Gmail activity

Use the Gmail MCP. Search threads in the same window.

**Skip:** newsletters, marketing, automated notifications (GitHub, Jira, Linear, Datadog, monitoring), calendar invites that don't require action, social media notifications, mailing-list digests.

**Keep:** direct human emails to Chris, threads where Chris is addressed by name, anything with explicit asks or deadlines, replies in threads Chris started.

For each kept email: sender, subject, one-line snippet, thread URL.

## 3. Flag important items

Mark an item as IMPORTANT if any are true:
- Jira ticket due today or overdue
- Chris @-mentioned in a Jira comment within the window
- Chris newly assigned a Jira ticket within the window
- Email is from a real person directly addressing Chris with a question, request, or deadline

## 4. Compose summary

Use Slack mrkdwn (renders well in Slack and is readable as plain text in email/chat):

```
*Work Briefing — <today's date> (<window-label>)*

*Important — needs attention <today|this afternoon>*
- [TICKET-KEY] Title — _why flagged_ — <Jira URL>
- Email from <Name>: <Subject> — _why flagged_
(or: "Nothing critical flagged.")

*Active work*
- [TICKET-KEY] Title — status, last update one-liner
- ...

*Recent inbox activity (FYI)*
- Brief one-liners
```

Window labels: `morning`, `midday check-in`, or for custom: `last <N>h`.

**Rules:**
- Under 300 words total
- No padding — if nothing's important, say so explicitly
- For midday, focus on what's *new since this morning*
- Always include real Jira URLs so they're clickable

## 5. Deliver

### If mode = chat
- Render the summary directly in the conversation as the response.
- Do NOT send anything to Slack or email.
- Don't include preamble like "Here's your briefing" — just the summary itself.

### If mode = send
- **Slack DM:** Find Chris's Slack user_id (search by email `cclark@phase2.io`), then send a direct message to that user_id. DMing yourself is supported — use the user's own ID as the channel. Use Slack mrkdwn formatting.
- **Email:** Use the Gmail MCP to send to `cclark@phase2.io`. Subject: `Work Briefing — <date> (<window-label>)`. Body: same content as Slack.
- After both deliveries, respond with a one-line confirmation: `Sent to Slack DM and cclark@phase2.io.` (or note any failures).
- Attempt both channels independently — if one fails, still try the other.
- Do NOT also render the summary inline when mode is send.

## Edge cases

- If Atlassian or Gmail MCP isn't connected, note which one and proceed with whichever is available.
- If both fail, report the failures clearly.
- If there's literally zero relevant activity, send/display a one-line summary saying so — don't fabricate items.
- Never include credentials, tokens, or full email bodies in the summary.
