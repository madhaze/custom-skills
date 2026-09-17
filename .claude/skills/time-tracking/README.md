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
| `--timesheet` | **The preset.** Equivalent to `--all-projects --by-project --by-ticket --append` |
| `--days N` | Last N days (default 7) |
| `--from YYYY-MM-DD [--to YYYY-MM-DD]` | Explicit date range |
| `--blocks` | Each block's wall-clock span (`1:40pm-2:15pm`) — *when* the time was spent |
| `--by-project` | Split each day by repo — the check that no project vanished |
| `--by-ticket` | Split each day by ticket, proportional to mentions per block |
| `--by-project --by-ticket` | Nested: repo, then the tickets inside it |
| `--day-start H` | Hour a working day begins (default 2 = 2am); `0` for calendar days |
| `--gap N` | Idle minutes that end a working block (default 15) |
| `--min H` | Roll rows under H hours into `(other)` (default 0.1) |
| `--no-commits` | Transcripts only; git commits are included by default |
| `--commit-minutes M` | Credit M minutes of lead-up before each commit (default 0) |
| `--dominant` | Old winner-take-all attribution (erases minority repos) |
| `--append` | Write or refresh rows in the durable CSVs |
| `--project PATH` | Another repo (default: current git root) |
| `--all-projects` | Every project, for a true personal total |
| `--ticket-prefix X` | Restrict `--by-ticket` to one board, e.g. `STHS` |

The everyday invocation is one flag plus a range:

```bash
python3 ~/.claude/skills/time-tracking/session-time.py --timesheet --days 7 --blocks
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

Console table, plus optional CSVs at `~/.claude/time-tracking/`:

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
# what the current project cost this week
python3 ~/.claude/skills/time-tracking/session-time.py --days 7

# the weekly timesheet run: every repo, per-day project/ticket, block times, persisted
python3 ~/.claude/skills/time-tracking/session-time.py --timesheet --days 7 --blocks

# one day in detail, to check it against memory
python3 ~/.claude/skills/time-tracking/session-time.py \
  --all-projects --from 2026-09-10 --to 2026-09-10 --blocks --by-project --by-ticket

# capture today permanently
python3 ~/.claude/skills/time-tracking/session-time.py --days 1 --append

# everything, across every repo
python3 ~/.claude/skills/time-tracking/session-time.py --days 30 --all-projects
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
