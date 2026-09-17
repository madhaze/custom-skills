---
name: timesheet
description: Fill in or audit a daily timesheet by reconstructing hours worked — per day, per project and per ticket — from Claude Code session transcripts and your git commits. Use when asked "how long did I work", "how much time did I spend", for a daily or weekly total, time per ticket, a timesheet, or to log/append today's hours. Works in any project; detects the repo from the current directory.
---

# timesheet

Commit counts badly understate real effort — decisions, review and investigation leave no
commits. This reconstructs engaged time from the session transcripts Claude Code already
writes, so nothing has to be instrumented in advance.

## The tool

```bash
python3 ~/.claude/skills/timesheet/session-time.py [options]
```

With no flags it reports **the week in progress** — Monday through today, every repo,
split by project and then by ticket. Nothing is written unless you pass `--append`.

| Option | Effect |
| --- | --- |
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

`--append` with a breakdown flag also writes `<name>-detail.csv`: one row per
`date,weekday,project,ticket,hours`. That is the file to read when filling in a daily
timesheet; the day-level CSV only carries totals.

Output goes to `~/.claude/timesheet/<repo>.csv`, or `all-projects.csv` — deliberately
OUTSIDE this skill's git repo, since it is accumulated data, not code.

## What it measures, and what it does not

**Claude sessions AND your git commits, by default.** Commit timestamps are folded into the
same clustering, so work committed outside a session extends or creates a block. Pass
`--no-commits` for transcripts only. Either way, IDE work, terminal work, PR review and
meetings are still invisible — those remain a manual add. `--commit-minutes M` credits M minutes of lead-up
before each commit; it defaults to 0 because an isolated commit proves presence at an instant,
not duration — raising it invents time, so say so if you do.

The `commits` column is a COUNT, never additive hours.

**Engaged time**, not focused attention: user and assistant message timestamps in the main
session, clustered into blocks, where a gap longer than `--gap` ends a block. A short break
inside a block still counts.

**Orchestrator time is the human's.** Worker sessions in worktrees are reported separately as
machine time — they run while the human is doing something else. Never add the two together
and present it as a person's hours.

**A working day starts at 2am, not midnight.** Work at 00:30 belongs to the evening that
produced it, so it is credited to the previous date; `--day-start 0` restores calendar days.
Besides matching how a person remembers their day, this stops a session that runs through
midnight from being split into two artificial blocks. In `--blocks` output a span marked
`+1d` fell on the following calendar date.

**`--gap` is a judgement, not a fact.** 15 minutes is the default; 30 merges short breaks and
raises every total. If a number is going somewhere that matters, say which gap produced it.

**`--by-ticket` splits each block proportionally** across the tickets mentioned in it,
weighted by how many messages mention each. Fine for a daily estimate; do not bill to the
minute from it. `--dominant` restores the old winner-take-all rule, which under
`--all-projects` silently ERASES a minority repo whose blocks interleave with a busier one.

**`--by-ticket` is text-based; `--by-project` is session-based.** A ticket only appears if you
typed its key in chat, so work done without naming a ticket lands in `(untagged)` or is
absorbed by the tickets that share its block. To answer "did project X get captured at all",
use `--by-project` — it reads the transcript's own repo and cannot be voted away.

## Reporting rules

- Always state the gap value, the day-start hour, and the date range alongside any total,
  and whether it is claude-only or `claude+git` (the CSV records all of these).
- Present orchestrator and worker hours as separate columns. Never sum them.
- If a day shows no session, say so rather than reporting zero — it may mean work happened in
  another project, and `--all-projects` is the check.
- Before presenting a per-ticket breakdown across repos, run `--by-project` on the same range
  and confirm every repo you expected is there. A missing board is the failure mode this tool
  had; do not assume its absence means no work.
- Round to the nearest 0.25h when a human is going to type it into a timesheet.

## Portability

Works in any project, not just Lattice ones:

- **Project detection** is `git rev-parse --show-toplevel`, so it follows whatever repo you
  are in. `--project PATH` overrides it.
- **Ticket attribution** matches any Jira-style key (`ABC-123`), not one board. Use
  `--ticket-prefix` to narrow it when a repo's docs mention keys from several systems.
- **Worker hours** look for session directories containing `worktrees`, which is the Lattice
  layout. Outside Lattice that column simply reads 0 — nothing breaks, there is just no
  machine time to separate out.

## Durability

The transcripts are the source and can be pruned or rotated by Claude Code. The CSV is the
permanent record. Run `--append` at least weekly, or history is lost with no way to
reconstruct it.

`--append` refreshes a date's row rather than duplicating it, so re-running is safe.

## Typical use

```bash
# the week so far: every repo, per project and ticket
python3 ~/.claude/skills/timesheet/session-time.py

# ...with the clock times of each working block, to check it against memory
python3 ~/.claude/skills/timesheet/session-time.py --blocks

# last week, recorded permanently
python3 ~/.claude/skills/timesheet/session-time.py --last-week --append

# one day in detail
python3 ~/.claude/skills/timesheet/session-time.py --from 2026-09-10 --to 2026-09-10 --blocks

# just the current repo, day totals only
python3 ~/.claude/skills/timesheet/session-time.py --this-repo --totals
```
