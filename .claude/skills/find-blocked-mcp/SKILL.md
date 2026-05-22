---
name: find-blocked-mcp
description: Extract MCP tool names from a pasted Claude Code log that failed with "requires approval" errors, then offer to add them to ~/.claude/settings.json's permissions.allow list. Use when Chris pastes a log showing "MCP tool call requires approval" / "Streamable HTTP error" failures from a scheduled routine, or asks "which MCP tools need allowlisting?" / "why did my routine fail?" / "fix the approval errors".
---

# Find Blocked MCP

A small helper for the recurring case where a scheduled routine (e.g. work-briefing) fails because MCP tool calls hit `requires approval` and there's no human to click through.

## What it does

1. Reads the log Chris pasted in chat (no file I/O needed — just scan the conversation).
2. Extracts every MCP tool name that immediately preceded a `Streamable HTTP error: ... MCP tool call requires approval` line.
3. Compares them to the current `permissions.allow` list in `~/.claude/settings.json`.
4. Reports the ones that are missing.
5. Offers to add them.

## How to find the tool names in the log

The log format Chris pastes looks like:

```
Used <Connector Name>: <tool name>
<arg>: <value>
Streamable HTTP error: Error POSTing to endpoint: MCP tool call requires approval
```

The tool isn't shown as `mcp__<uuid>__<name>` in the user-facing log — only the friendly name (`getAccessibleAtlassianResources`, `search threads`, `slack search users`). To get the full `mcp__<server-id>__<tool>` identifier you need to map friendly names back to MCP server IDs.

**Best way to map them**: in the current session, the deferred MCP tools are listed by their full ID in the system. Use `ToolSearch` with the friendly tool name as the query — it returns the full `mcp__<uuid>__<toolname>` identifier. Example:

```
ToolSearch(query="search_threads", max_results=3)
ToolSearch(query="getAccessibleAtlassianResources", max_results=3)
ToolSearch(query="slack_search_users", max_results=3)
```

Friendly names in logs sometimes use spaces (`slack search users`) where the actual tool name uses underscores (`slack_search_users`) — normalize spaces → underscores before searching.

## Workflow

1. **Scan the pasted log** for blocks matching the pattern above. Collect the friendly tool names.
2. **Resolve each to its full MCP identifier** via ToolSearch.
3. **Read `~/.claude/settings.json`** and check `permissions.allow`.
4. **Report**: "Found N blocked tools, M already allowed, K need to be added: <list>".
5. **Ask Chris** if he wants to add them. If yes, use the `update-config` skill (or Edit directly) to merge them into the allow array — preserve all existing entries.
6. **Confirm** with the updated allow list.

## If a tool can't be resolved

If `ToolSearch` returns nothing for a friendly name, it means that MCP server isn't connected in *this* session — the routine probably ran in a different environment. Report the unresolved name to Chris and ask whether he wants to add a guessed allowlist entry or check the connector status.

## Don't

- Don't fetch the log from anywhere — only operate on what Chris pasted in the current conversation.
- Don't add wildcard entries (`mcp__*`) unless Chris asks for it explicitly. The point of this helper is targeted, minimal allowlist updates.
- Don't replace the `allow` array — always merge.
