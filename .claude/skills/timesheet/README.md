# timesheet

Fill in or audit a daily timesheet, by reconstructing hours worked from Claude Code session
transcripts and your git commits.

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
/timesheet
```

Or call the script directly:

```bash
python3 ~/.claude/skills/timesheet/session-time.py [options]
```

| Option | Description |
|---|---|
| *(no flags)* | **the current week, Monday to today**, every repo, split by project then ticket |
| `--last-week` | the previous full Monday–Sunday week |
| `--days N` | last N days instead of a week |
| `--from YYYY-MM-DD [--to …]` | explicit range |
| `--blocks` | each block's wall-clock span (`1:40pm-2:15pm`) — *when* the time was spent |
| `--append` | write/refresh rows in the durable CSVs (never automatic) |
| `--totals` | day totals only, without the project/ticket breakdown |
| `--this-repo` | only the current git repo |
| `--project PATH` | only this repo |
| `--day-start H` | hour a working day begins (default 2 = 2am); `0` for calendar days |
| `--gap N` | idle minutes that end a working block (default 15) |
| `--min H` | roll rows under H hours into `(other)` (default 0.1) |
| `--no-commits` | transcripts only (git commits are included by default) |
| `--commit-minutes M` | credit M min of lead-up before each commit (default 0) |
| `--dominant` | old winner-take-all attribution (erases minority repos) |
| `--ticket-prefix X` | restrict tickets to one board, e.g. `STHS` |

The everyday invocation is no flags at all — the week in progress, every repo, split by
project and then ticket. Nothing is written to disk unless you pass `--append`.

```bash
python3 ~/.claude/skills/timesheet/session-time.py --blocks
```

## What it does

1. Reads user and assistant message timestamps from `~/.claude/projects/<repo-slug>/*.jsonl`
2. Seeds in your git commit timestamps too, so work committed outside a session still counts
   (`--no-commits` to disable). Commit subjects also recover ticket keys never typed in chat
3. Clusters everything into working blocks — a gap longer than `--gap` ends a block
4. Buckets blocks into working days that begin at 2am, not midnight, so a session running
   through midnight stays whole and late-night work lands on the evening that produced it
5. Sums block durations per day as **engaged time**
6. Reports worker (worktree) sessions separately as machine time — never folded in, including
   under `--all-projects`
7. Splits each day by repo first, then by ticket within each repo, sharing a block's seconds
   proportionally
8. Optionally appends day totals and a per-day `project,ticket,hours` detail CSV

## What it measures, and what it does not

**Engaged time, not focused attention.** A short break inside a block still counts. The `--gap`
value is a judgement — 15 minutes is the default, 30 merges short breaks and raises every
total. State which gap produced a number if it is going anywhere that matters.

**Orchestrator time is the human's; worker time is not.** Worker sessions run while you are
doing something else. The two are reported as separate columns and must never be summed into a
person's hours.

**Per-ticket is an estimate.** A block's seconds are shared across the tickets mentioned in
it, weighted by how many messages mention each. Fine for a daily split; not for billing to the
minute. `--dominant` restores the old winner-take-all rule, which under `--all-projects`
silently erases a minority repo whose blocks interleave with a busier one.

**Repo attribution is structural; ticket attribution is textual.** A ticket appears only if its
key was typed in chat or in a commit subject, so untagged work shows as `(untagged)`. To answer
"did project X get captured at all", use `--by-project` — it reads the transcript's own
directory and cannot be voted away.

**A working day starts at 2am.** Work at 00:30 is credited to the previous date. Besides
matching how a day is remembered, this stops a 15-minute-gap rule from being overridden by the
calendar. Spans marked `+1d` in `--blocks` output fell on the following calendar date.

**Still invisible:** IDE-only work, terminal work, PR review, meetings. Those remain a manual
add.

## Output

Console table, plus optional CSVs at `~/.claude/timesheet/`:

- `<repo>.csv` (or `all-projects.csv`) — one row per day, recording `gap_minutes`,
  `day_start_hour`, `attribution` and `sources` alongside the hours, so an archived row still
  says which judgements produced it.
- `<repo>-detail.csv` — one row per `date,weekday,project,ticket,hours`. This is the file to
  read when filling in a daily timesheet.

Block spans are console-only and deliberately not persisted.

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
# the week so far: every repo, per project and ticket
python3 ~/.claude/skills/timesheet/session-time.py

# ...with the clock times of each working block, to check it against memory
python3 ~/.claude/skills/timesheet/session-time.py --blocks

# last week, recorded permanently
python3 ~/.claude/skills/timesheet/session-time.py --last-week --append

# one day in detail, to check it against memory
python3 ~/.claude/skills/timesheet/session-time.py \
  --from 2026-09-10 --to 2026-09-10 --blocks

# just the current repo, day totals only
python3 ~/.claude/skills/timesheet/session-time.py --this-repo --totals
```

## Dependencies

- Python 3 (standard library only)
- `git` on `$PATH` — for repo detection, commit counts, and commit-time seeding
- Claude Code session transcripts under `~/.claude/projects/`

No MCP servers, no network access, no configuration.

## Portability notes

- **Project detection** uses `git rev-parse --show-toplevel`; `--project` overrides it.
- **Ticket attribution** matches any Jira-style key (`ABC-123`), not one board. Two leading
  letters are required so code citations like `L552-565` are not read as tickets, and common
  placeholder keys are stopworded.
- **Worker hours** look for session directories containing `worktrees` — the Lattice layout.
  Outside Lattice that column reads 0; nothing breaks, there is simply no machine time to
  separate out.
