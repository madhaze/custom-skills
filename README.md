# custom-skills

A collection of personal Claude Code skills for local use and automated claude.ai routines.

## Why this structure?

Skills live at `.claude/skills/<name>/SKILL.md` — this exact path is required for **claude.ai Routines** to discover and load them when running scheduled agents. Keeping skills in a git repo at this path means the same skill definitions work both locally (via symlinks in your terminal Claude Code sessions) and remotely (loaded directly by claude.ai Routines from the repo).

The symlink approach for local use lets you edit skills in one place (`~/.claude/custom-skills/`) and have Claude Code pick them up from `~/.claude/skills/` without duplicating files.

## Skills

| Skill | Description |
|---|---|
| [`commit`](.claude/skills/commit/README.md) | Stage and commit changes locally without pushing |
| [`pr`](.claude/skills/pr/README.md) | Stage, commit, push, and open a pull request |
| [`pr-feedback-fix`](.claude/skills/pr-feedback-fix/README.md) | Poll a PR for review comments and address them |
| [`component-create`](.claude/skills/component-create/README.md) | End-to-end Drupal SDC component creation for Canvas |
| [`component-visual-review`](.claude/skills/component-visual-review/README.md) | Pixel-perfect visual review of a component against a design reference |
| [`find-blocked-mcp`](.claude/skills/find-blocked-mcp/README.md) | Identify MCP tools blocked by approval errors in a routine log |
| [`work-briefing`](.claude/skills/work-briefing/README.md) | Daily work briefing from Jira and Gmail, delivered in chat or Slack |

## Installation (local)

Clone into your Claude config directory and symlink each skill:

```bash
git clone https://github.com/madhaze/custom-skills ~/.claude/custom-skills

for d in ~/.claude/custom-skills/.claude/skills/*/; do
  ln -s "$d" ~/.claude/skills/"$(basename "$d")"
done
```

Skills are then available as `/skill-name` in any Claude Code session.

## Keeping in sync

```bash
# Pull updates
cd ~/.claude/custom-skills && git pull

# Push a change
cd ~/.claude/custom-skills && git add .claude/skills/<name>/SKILL.md && git commit -m "..." && git push
```

## Adding a new skill

1. Create `~/.claude/custom-skills/.claude/skills/<name>/SKILL.md`
2. Add the symlink: `ln -s ~/.claude/custom-skills/.claude/skills/<name> ~/.claude/skills/<name>`
3. Optionally add a `README.md` next to `SKILL.md`
4. Commit and push
