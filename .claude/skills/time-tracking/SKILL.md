---
name: time-tracking
description: Reconstruct how much time was actually spent working, from Claude Code session transcripts, for time tracking and billing. Use when asked "how long did I work", "how much time did I spend", for a daily or weekly total, time per ticket, a timesheet, or to log/append today's hours. Works in any project; detects the repo from the current directory.
---

# time-tracking

Commit counts badly understate real effort — decisions, review and investigation leave no
commits. This reconstructs engaged time from the session transcripts Claude Code already
writes, so nothing has to be instrumented in advance.

## The tool

```bash
python3 ~/.claude/skills/time-tracking/session-time.py [options]
```

| Option | Effect |
| --- | --- |
| `--days N` | last N days (default 7) |
| `--from YYYY-MM-DD [--to …]` | explicit range |
| `--by-ticket` | split each day by ticket, proportional to mentions per block |
| `--by-project` | split each day by repo — the check that no project vanished |
| `--by-project --by-ticket` | **the daily timesheet view**: repo, then tickets inside it |
| `--blocks` | each block's wall-clock span (`1:40pm-2:15pm`) — WHEN time was spent, for checking a day against memory |
| `--timesheet` | **the preset**: all repos, project/ticket breakdown, appended |
| `--no-commits` | Claude transcripts only (commits are ON by default) |
| `--commit-minutes M` | credit M min of lead-up before each commit (default 0) |
| `--dominant` | old winner-take-all attribution (erases minority repos) |
| `--min H` | roll rows under H hours into `(other)` (default 0.1) |
| `--append` | write/refresh rows in the durable CSV |
| `--gap N` | idle minutes that end a working block (default 15) |
| `--day-start H` | hour a working day begins (default 2 = 2am); work before it counts toward the previous day. `0` for strict calendar days |
| `--project PATH` | another repo (default: current git root) |
| `--all-projects` | every project, for a true personal total |
| `--ticket-prefix X` | restrict `--by-ticket` to one board, e.g. `STHS` |

`--append` with a breakdown flag also writes `<name>-detail.csv`: one row per
`date,weekday,project,ticket,hours`. That is the file to read when filling in a daily
timesheet; the day-level CSV only carries totals.

Output goes to `~/.claude/time-tracking/<repo>.csv`, or `all-projects.csv` — deliberately
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
# what the current project cost this week
python3 ~/.claude/skills/time-tracking/session-time.py --days 7

# a timesheet week, split by ticket
python3 ~/.claude/skills/time-tracking/session-time.py --from 2026-08-24 --to 2026-08-30 --by-ticket

# which repos did the week actually touch? run this BEFORE trusting a ticket split
python3 ~/.claude/skills/time-tracking/session-time.py --from 2026-08-24 --all-projects --by-project

# when was the time spent? wall-clock spans per block, to verify a day
# (composes with --timesheet: --timesheet --days 7 --blocks)
python3 ~/.claude/skills/time-tracking/session-time.py --all-projects --days 1 --blocks

# THE DAILY TIMESHEET VIEW: per day, per repo, per ticket -- and persist it
python3 ~/.claude/skills/time-tracking/session-time.py --timesheet --days 7

# capture today permanently
python3 ~/.claude/skills/time-tracking/session-time.py --days 1 --append

# everything, across every repo
python3 ~/.claude/skills/time-tracking/session-time.py --days 30 --all-projects
```
