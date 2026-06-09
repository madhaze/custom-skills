# find-blocked-mcp

Identify MCP tools blocked by approval requirements in a failed routine log and offer to allowlist them.

## Overview

Solves the recurring problem where a scheduled Claude Routine (like `/work-briefing`) fails silently because MCP tool calls hit `requires approval` errors and there's no human present to click through. Paste the routine's output log into chat, and this skill extracts every blocked tool name, maps it to its full `mcp__<server-id>__<tool>` identifier, compares against your current allow list in `~/.claude/settings.json`, and offers to add the missing entries.

## Usage

1. Run the failing routine, copy its output log
2. Paste the log into the Claude Code chat
3. Type `/find-blocked-mcp`

No arguments needed — the skill operates entirely on what you pasted.

## What it does

1. Scans the pasted log for lines matching the `Streamable HTTP error: ... MCP tool call requires approval` pattern
2. Extracts the friendly tool name that preceded each error
3. Resolves each friendly name to its full `mcp__<server-id>__<tool>` identifier via `ToolSearch`
4. Reads `~/.claude/settings.json` and checks `permissions.allow`
5. Reports: how many blocked tools were found, how many are already allowed, which ones need to be added
6. Asks if you want to add them — if yes, merges them into the allow array without touching existing entries
7. Confirms with the updated list

## Notes

- Operates only on the pasted log text — does not fetch logs from files or URLs
- Never uses wildcard entries (`mcp__*`) unless explicitly requested
- Always merges into the existing `permissions.allow` array; never replaces it
- If an MCP server isn't connected in the current session, it reports the unresolved name and asks for guidance

## Dependencies

- `~/.claude/settings.json` readable and writable
- The relevant MCP servers must be connected in the current session for tool names to resolve via `ToolSearch`
