# time-tracking

Reconstruct how much time was actually spent working, from Claude Code session transcripts.

## Overview

Commit counts badly understate real effort. Deciding, reviewing, investigating and correcting
leave no commits — one observed day showed nine hours of work behind seventeen commits, the
lowest count of that fortnight.

This reads the session transcripts Claude Code already writes and reconstructs engaged time
from message timestamps. Nothing has to be instrumented in advance, and it works
retroactively: history back to whenever transcripts began is available immediately.

Works in any project. Detects the repo from the current directory.

## Usage

```
/time-tracking
```

Or call the script directly:

```bash
python3 ~/.claude/skills/time-tracking/session-time.py [options]
```

| Option | Description |
|---|---|
| `--days N` | Last N days (default 7) |
| `--from YYYY-MM-DD [--to YYYY-MM-DD]` | Explicit date range |
| `--by-ticket` | Split each day by the ticket that dominated each block |
| `--append` | Write or refresh rows in the durable CSV |
| `--gap N` | Idle minutes that end a working block (default 15) |
| `--project PATH` | Another repo (default: current git root) |
| `--all-projects` | Every project, for a true personal total |
| `--ticket-prefix X` | Restrict `--by-ticket` to one board, e.g. `STHS` |

## What it does

1. Reads user and assistant message timestamps from `~/.claude/projects/<repo-slug>/*.jsonl`
2. Clusters them into working blocks — a gap longer than `--gap` ends a block
3. Sums block durations per day as **engaged time**
4. Reports worker (worktree) sessions separately as machine time
5. Cross-checks against commit counts for the same day
6. Optionally attributes each block to the ticket most mentioned inside it
7. Optionally appends the day's row to a permanent CSV

## What it measures, and what it does not

**Engaged time, not focused attention.** A short break inside a block still counts. The `--gap`
value is a judgement — 15 minutes is the default, 30 merges short breaks and raises every
total. State which gap produced a number if it is going anywhere that matters.

**Orchestrator time is the human's; worker time is not.** Worker sessions run while you are
doing something else. The two are reported as separate columns and must never be summed into a
person's hours.

**Per-ticket is an estimate.** Each block is credited entirely to its dominant ticket, so a
block spanning two goes to one. Fine for a daily split; not for billing to the minute.

## Output

Console table, plus an optional CSV at `~/.claude/time-tracking/<repo>.csv`
(or `all-projects.csv`).

The CSV lives **outside this repo deliberately** — it is accumulated per-machine data, not
code. Tracking it would mean merge conflicts on a file every machine appends to independently.

## Durability

Transcripts are the source and can be pruned or rotated by Claude Code. The CSV is the
permanent record.

**Run `--append` at least weekly.** Once transcripts rotate, that history cannot be
reconstructed from anything else.

`--append` refreshes a date's row rather than duplicating it, so re-running is always safe.

## Examples

```bash
# what the current project cost this week
python3 ~/.claude/skills/time-tracking/session-time.py --days 7

# a timesheet week, split by ticket
python3 ~/.claude/skills/time-tracking/session-time.py \
  --from 2026-08-24 --to 2026-08-30 --by-ticket

# capture today permanently
python3 ~/.claude/skills/time-tracking/session-time.py --days 1 --append

# everything, across every repo
python3 ~/.claude/skills/time-tracking/session-time.py --days 30 --all-projects
```

## Dependencies

- Python 3 (standard library only)
- `git` on `$PATH` — for repo detection and the commit cross-check
- Claude Code session transcripts under `~/.claude/projects/`

No MCP servers, no network access, no configuration.

## Portability notes

- **Project detection** uses `git rev-parse --show-toplevel`; `--project` overrides it.
- **Ticket attribution** matches any Jira-style key (`ABC-123`), not one board.
- **Worker hours** look for session directories containing `worktrees` — the Lattice layout.
  Outside Lattice that column reads 0; nothing breaks, there is simply no machine time to
  separate out.
