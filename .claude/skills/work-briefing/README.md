# work-briefing

Generate a focused daily work briefing from Jira and Gmail, delivered in chat or via Slack DM.

## Overview

Pulls recent Jira activity (assigned tickets, @-mentions, overdue issues, newly assigned) and Gmail (direct human emails with asks or deadlines) within a configurable time window. Flags what needs attention, lists active work, and summarizes inbox activity. Delivers the summary either inline in Claude Code chat or as a Slack DM.

Designed to run both interactively and as a fully automated **Claude Routine** on a daily schedule.

## Usage

```
/work-briefing
/work-briefing mode=send
/work-briefing mode=chat window=midday
/work-briefing mode=chat window=custom:12
```

**Parameters:**

| Parameter | Default | Options |
|---|---|---|
| `mode` | `chat` | `chat` — display inline; `send` — deliver via Slack DM |
| `window` | auto | `morning` — 24h (72h on Mondays); `midday` — 6h; `custom:<hours>` |

When invoked without parameters, defaults to `mode: chat` and auto-selects `morning` or `midday` based on whether it's before or after 11am local time.

## What it does

1. Loads the Atlassian and Gmail MCP tools (they are often registered as deferred tools — the skill handles this automatically)
2. Queries Jira for: tickets you're assigned to or watching, tickets where you were @-mentioned, overdue issues, and newly assigned tickets — all within the time window
3. Queries Gmail for direct human emails with asks, deadlines, or replies to threads you started — skips newsletters, automated notifications, and digests
4. Flags items as IMPORTANT: overdue tickets, @-mentions, newly assigned tickets, emails directly addressing you with a request or deadline
5. Composes a summary under 300 words: Important section, Active work section, Recent inbox FYI section
6. Delivers in chat (inline) or sends as a Slack DM depending on `mode`

## Dependencies

- **Atlassian MCP** — for Jira queries. Requires a connected Atlassian account (configured via claude.ai Connectors)
- **Gmail MCP** — for email. Requires a connected Google account
- **Slack MCP** — only required when `mode=send`

---

## Adapting this skill for your own use

This skill is written for a specific user (`cclark@phase2.io`, `phase2tech.atlassian.net`). To use it yourself:

1. Fork or clone this repo as your own custom-skills repo (see installation below)
2. Edit `SKILL.md` and replace:
   - `cclark@phase2.io` → your email address
   - `phase2tech.atlassian.net` → your Atlassian instance URL
3. Connect your own Atlassian, Gmail, and Slack accounts in your claude.ai Connector settings
4. Update the Slack delivery step if your user ID differs

---

## Setting up as a Claude Routine

Claude Routines are scheduled agents that run automatically on a cron schedule. Setting up `/work-briefing` as a routine delivers your briefing without any manual invocation.

### Prerequisites

1. A claude.ai account with Routines access
2. This skills repo (or your fork) accessible to claude.ai — the repo must be at a path claude.ai can read from, with skills under `.claude/skills/`
3. The following MCP connectors active in your claude.ai account:
   - Atlassian (for Jira)
   - Gmail
   - Slack (if using `mode=send`)

### Creating the routine

1. Go to [claude.ai](https://claude.ai) and open **Routines** (or your org's equivalent)
2. Create a new routine with the prompt:
   ```
   /work-briefing mode=send window=morning
   ```
3. Set your schedule — e.g. weekdays at 8:00 AM in your local timezone
4. Point the routine at this skills repo so it can load the skill definition from `.claude/skills/work-briefing/SKILL.md`
5. Save and enable the routine

### Handling approval errors

The first time a routine runs unattended, MCP tool calls often fail with `requires approval` because the tools haven't been explicitly allowed. Use the [`/find-blocked-mcp`](../find-blocked-mcp/README.md) skill to fix this:

1. Copy the failed routine's output log
2. Paste it into Claude Code and run `/find-blocked-mcp`
3. It will identify the blocked tools and offer to add them to your allow list

The tools typically needed for fully unattended operation:

```json
"permissions": {
  "allow": [
    "mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources",
    "mcp__claude_ai_Atlassian_Rovo__atlassianUserInfo",
    "mcp__claude_ai_Atlassian_Rovo__lookupJiraAccountId",
    "mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql",
    "mcp__claude_ai_Gmail__search_threads",
    "mcp__claude_ai_Gmail__get_thread",
    "mcp__claude_ai_Slack__slack_search_users",
    "mcp__claude_ai_Slack__slack_send_message"
  ]
}
```

Add these to `~/.claude/settings.json` (for local use) or the routine's permission settings (for claude.ai Routines).
