# custom-skills

Personal Claude Code skills used both locally and by claude.ai routines.

## Structure

Skills live at `.claude/skills/<name>/SKILL.md`. This path is required for claude.ai routines to discover them. Do not restructure.

## Local setup

Clone the repo into your Claude config directory and symlink each skill into `~/.claude/skills/`:

```bash
git clone https://github.com/madhaze/custom-skills ~/.claude/custom-skills

for d in ~/.claude/custom-skills/.claude/skills/*/; do
  ln -s "$d" ~/.claude/skills/"$(basename "$d")"
done
```

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
3. Commit and push from `~/.claude/custom-skills`
