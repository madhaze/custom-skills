#!/usr/bin/env python3
"""Reconstruct working time from Claude Code session transcripts.

Lives outside any repo so it survives MO restarts and SO teardowns.

  session-time.py                     last 7 days, summary
  session-time.py --days 30           a longer window
  session-time.py --from 2026-08-16 --to 2026-08-22
  session-time.py --by-ticket         split each day by ticket
  session-time.py --by-project        split each day by repo
  session-time.py --append            write/refresh rows in daily.csv
  session-time.py --gap 20            idle minutes that end a block (default 15)

Counts a day's ENGAGED time: user+assistant message timestamps in the
orchestrator session, clustered into blocks. A gap longer than --gap ends a
block. This is elapsed wall-clock while engaged, not focused attention.

Orchestrator time is yours. Worker (worktree) sessions are reported separately
as machine time -- they run while you are doing something else, and are never
folded into the engaged column, including under --all-projects.

Attribution is PROPORTIONAL by default: a block's seconds are split across the
tickets mentioned in it, weighted by how many messages mention each. Pass
--dominant for the old winner-take-all behaviour, which erases a minority
project when blocks span repos.
"""
import argparse, csv, datetime as dt, glob, json, os, re, subprocess, sys
from collections import defaultdict

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
OUTDIR = os.path.join(HOME, ".claude", "time-tracking")
CSV_PATH = os.path.join(OUTDIR, "daily.csv")

# Project dirs whose path contains this are worker (worktree) sessions: machine
# time, never the human's. That is the Lattice layout; harmless elsewhere.
WORKER_MARK = "worktrees"


def _slug(path):
    """Claude Code encodes a project cwd as its path with / -> -."""
    return path.replace("/", "-")


HOME_SLUG = _slug(HOME)


def _proj_label(d):
    """Human-readable repo label from a slugified project dir name."""
    b = os.path.basename(d)
    if b.startswith(HOME_SLUG):
        b = b[len(HOME_SLUG):]
    b = b.lstrip("-")
    for p in ("Sites-", "src-", "code-", "Projects-"):
        if b.startswith(p):
            b = b[len(p):]
            break
    return b or os.path.basename(d)


def _unslug(slug):
    """Reverse _slug(). Hyphens are ambiguous -- 'st-tammany' is one directory,
    not two -- so resolve greedily against the real filesystem, longest first."""
    parts = slug.split("-")
    i = 1 if parts and parts[0] == "" else 0
    path = "/" if i else ""
    while i < len(parts):
        for j in range(len(parts), i, -1):
            cand = os.path.join(path, "-".join(parts[i:j]))
            if os.path.isdir(cand):
                path, i = cand, j
                break
        else:
            return None
    return path or None


def _git_repos():
    """[(repo_path, project_label)] for every non-worker project with a .git."""
    found = {}
    for d in sorted(glob.glob(MO_GLOB or "")):
        b = os.path.basename(d)
        if MO_EXCLUDE and MO_EXCLUDE in b:
            continue
        r = _unslug(b)
        if r and os.path.isdir(os.path.join(r, ".git")):
            found[r] = _proj_label(d)
    if REPO and os.path.isdir(os.path.join(REPO, ".git")) and REPO not in found:
        found[REPO] = _proj_label(_slug(REPO))
    return sorted(found.items())


def git_events(start, end):
    """({label: [(ts, subject)]}, {date: {label: count}}) for YOUR commits.

    Authored-by is filtered to the repo's own user.email, so a shared checkout
    does not credit you with a colleague's work.
    """
    ev, counts = defaultdict(list), defaultdict(lambda: defaultdict(int))
    for repo, label in _git_repos():
        try:
            em = subprocess.run(["git", "-C", repo, "config", "user.email"],
                                capture_output=True, text=True,
                                timeout=10).stdout.strip()
            args = ["git", "-C", repo, "log", "--all", "--no-merges",
                    "--pretty=%H%x09%aI%x09%s",
                    f"--since={start} 00:00", f"--until={end} 23:59"]
            if em:
                args.insert(4, f"--author={em}")
            r = subprocess.run(args, capture_output=True, text=True, timeout=60)
        except Exception:
            continue
        seen = set()
        for line in r.stdout.splitlines():
            h, _, rest = line.partition("\t")
            iso, _, subj = rest.partition("\t")
            if h in seen:          # --all lists a commit once per ref
                continue
            seen.add(h)
            try:
                ts = dt.datetime.fromisoformat(iso).astimezone()
            except Exception:
                continue
            ev[label].append((ts, subj))
            counts[ts.date()][label] += 1
    return ev, counts


def resolve_project(explicit=None):
    """Return (main_glob, worker_glob, repo_path, label).

    Defaults to the current git repo root, so the tool works in any project.
    Worker sessions are any project dir under the repo whose path contains
    'worktrees'.
    """
    if explicit:
        repo = os.path.abspath(explicit)
    else:
        try:
            repo = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True,
                                  timeout=10).stdout.strip()
        except Exception:
            repo = ""
        repo = repo or os.getcwd()
    slug = _slug(repo)
    main_glob = os.path.join(PROJECTS, slug)
    worker_glob = os.path.join(PROJECTS, slug + "*" + WORKER_MARK + "*")
    return main_glob, worker_glob, repo, os.path.basename(repo)


MO_GLOB = SO_GLOB = REPO = None  # set in main()
MO_EXCLUDE = None                # substring of dirs to drop from engaged time

# Any Jira-style key: a project prefix of 2+ uppercase letters, a hyphen, then
# digits. Two leading letters are required so code citations like "L552-565"
# are not read as tickets. Override with --ticket-prefix when a project uses
# something else, or to narrow to one board.
DEFAULT_TICKET_RE = r"\b([A-Z]{2,}[A-Z0-9]{0,8}-\d{1,6})\b"
TICKET = re.compile(DEFAULT_TICKET_RE)

# Uppercase tokens that look like ticket keys but are not, so a project's docs
# do not pollute the attribution.
TICKET_STOPWORDS = {"UTF-8", "ISO-8601", "SHA-1", "SHA-256", "HTTP-2", "WCAG-2",
                    # placeholder keys that appear in docs, READMEs and this
                    # script's own help text -- never real work
                    "ABC-123", "FOO-1", "FOO-123", "XXX-123", "PROJ-1",
                    "PROJ-123", "TEST-1", "TEST-123", "JIRA-123"}


def _msgs(pattern, want_text=False, exclude=None):
    """Yield (timestamp, type, text, project_label) from transcripts."""
    for d in sorted(glob.glob(pattern)):
        if exclude and exclude in os.path.basename(d):
            continue
        proj = _proj_label(d)
        for f in glob.glob(os.path.join(d, "*.jsonl")):
            try:
                fh = open(f, errors="replace")
            except OSError:
                continue
            with fh:
                for line in fh:
                    if '"timestamp"' not in line:
                        continue
                    try:
                        j = json.loads(line)
                    except Exception:
                        continue
                    if j.get("type") not in ("user", "assistant"):
                        continue
                    t = j.get("timestamp")
                    if not t:
                        continue
                    try:
                        ts = dt.datetime.fromisoformat(
                            t.replace("Z", "+00:00")).astimezone()
                    except Exception:
                        continue
                    text = ""
                    if want_text:
                        c = j.get("message", {}).get("content")
                        if isinstance(c, str):
                            text = c
                        elif isinstance(c, list):
                            text = " ".join(
                                b.get("text", "") for b in c
                                if isinstance(b, dict) and b.get("type") == "text")
                    yield ts, j["type"], text, proj


def blocks(times, gap):
    """Cluster sorted timestamps into (start, end) blocks."""
    times = sorted(times)
    if not times:
        return []
    out = []
    s = p = times[0]
    for t in times[1:]:
        if (t - p).total_seconds() > gap:
            out.append((s, p))
            s = t
        p = t
    out.append((s, p))
    return out


def commits_on(day):
    if not REPO or not os.path.isdir(REPO):
        return 0
    try:
        r = subprocess.run(
            ["git", "-C", REPO, "log", "--all", "--oneline", "--no-merges",
             f"--since={day} 00:00", f"--until={day} 23:59"],
            capture_output=True, text=True, timeout=30)
        return r.stdout.count("\n")
    except Exception:
        return 0


def collect(gap, want_text=False):
    mo_ev, mo_user = defaultdict(list), defaultdict(int)
    mo_text, mo_proj = defaultdict(list), defaultdict(list)
    for ts, typ, text, proj in _msgs(MO_GLOB, want_text, exclude=MO_EXCLUDE):
        mo_ev[ts.date()].append(ts)
        mo_proj[ts.date()].append((ts, proj))
        if typ == "user":
            mo_user[ts.date()] += 1
        if want_text and text:
            mo_text[ts.date()].append((ts, text, proj))
    so_ev = defaultdict(list)
    for ts, _, _, _ in _msgs(SO_GLOB):
        so_ev[ts.date()].append(ts)
    return mo_ev, mo_user, so_ev, mo_text, mo_proj


def _split(day_blocks, items, key_of, empty_label, dominant=False):
    """Share each block's seconds across keys seen inside it.

    Proportional by default: a key mentioned in more messages takes more of the
    block. With dominant=True the whole block goes to the single top key, which
    is what silently erases a minority repo when blocks span projects.
    """
    out = defaultdict(float)
    for start, end in day_blocks:
        counts = defaultdict(int)
        for ts, payload in items:
            if start <= ts <= end:
                for k in key_of(payload):
                    counts[k] += 1
        secs = (end - start).total_seconds()
        if not counts:
            out[empty_label] += secs
        elif dominant:
            out[max(counts, key=counts.get)] += secs
        else:
            tot = sum(counts.values())
            for k, c in counts.items():
                out[k] += secs * c / tot
    return out


def _tickets_in(text):
    """Distinct ticket keys in one message -- presence, not raw occurrences, so
    a message repeating a branch name 40 times does not outvote a real block."""
    seen = set()
    for m in TICKET.finditer(text):
        k = m.group(1)
        if k not in TICKET_STOPWORDS:
            seen.add(k)
    return seen


def by_ticket(day_blocks, texts, dominant=False):
    flat = [(ts, text) for ts, text, _ in texts]
    return _split(day_blocks, flat, _tickets_in, "(untagged)", dominant)


def by_project_ticket(day_blocks, texts, projmsgs, dominant=False):
    """{project: {ticket: seconds}} -- share each block by repo first, then
    split each repo's slice across the tickets IT mentioned.

    Splitting by repo before ticket is what keeps a quiet project visible: its
    hours are settled from its own transcripts before any ticket vote happens.
    """
    out = defaultdict(lambda: defaultdict(float))
    for start, end in day_blocks:
        pcounts = defaultdict(int)
        for ts, proj in projmsgs:
            if start <= ts <= end:
                pcounts[proj] += 1
        secs = (end - start).total_seconds()
        if not pcounts:
            out["(unknown)"]["(untagged)"] += secs
            continue
        if dominant:
            slices = [(max(pcounts, key=pcounts.get), secs)]
        else:
            ptot = sum(pcounts.values())
            slices = [(p, secs * c / ptot) for p, c in pcounts.items()]
        for proj, psecs in slices:
            tcounts = defaultdict(int)
            for ts, text, tproj in texts:
                if tproj == proj and start <= ts <= end:
                    for k in _tickets_in(text):
                        tcounts[k] += 1
            if not tcounts:
                out[proj]["(untagged)"] += psecs
            elif dominant:
                out[proj][max(tcounts, key=tcounts.get)] += psecs
            else:
                ttot = sum(tcounts.values())
                for k, c in tcounts.items():
                    out[proj][k] += psecs * c / ttot
    return out


def by_project(day_blocks, projmsgs, dominant=False):
    return _split(day_blocks, projmsgs, lambda p: (p,), "(unknown)", dominant)


def block_label(start, end, texts, projmsgs, top=2):
    """Short 'repo · TICKET, TICKET' tag for one block, by message share."""
    pc = defaultdict(int)
    for ts, proj in projmsgs:
        if start <= ts <= end:
            pc[proj] += 1
    tc = defaultdict(int)
    for ts, text, _ in texts:
        if start <= ts <= end:
            for k in _tickets_in(text):
                tc[k] += 1
    proj = max(pc, key=pc.get) if pc else "?"
    if len(pc) > 1:
        proj += f" (+{len(pc) - 1})"
    tks = [k for k, _ in sorted(tc.items(), key=lambda kv: -kv[1])[:top]]
    return f"{proj:<26} {', '.join(tks) if tks else '(untagged)'}"


def rollup(shares, min_hours):
    """Fold rows below min_hours into (other), preserving the day total."""
    if min_hours <= 0:
        return shares
    keep, other = {}, 0.0
    for k, secs in shares.items():
        if secs / 3600 >= min_hours:
            keep[k] = secs
        else:
            other += secs
    if other:
        keep["(other)"] = keep.get("(other)", 0.0) + other
    return keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    ap.add_argument("--gap", type=int, default=15, help="idle minutes ending a block")
    ap.add_argument("--by-ticket", action="store_true")
    ap.add_argument("--by-project", action="store_true",
                    help="split each day by repo; the check that no project vanished")
    ap.add_argument("--dominant", action="store_true",
                    help="winner-take-all attribution (old behaviour)")
    ap.add_argument("--append", action="store_true", help="write rows to daily.csv")
    ap.add_argument("--project", help="repo path (default: current git root)")
    ap.add_argument("--all-projects", action="store_true",
                    help="every project Claude Code has transcripts for")
    ap.add_argument("--blocks", action="store_true",
                    help="show each working block's clock times, not just the "
                         "day total -- when the time was actually spent")
    ap.add_argument("--no-commits", dest="with_commits", action="store_false",
                    help="Claude transcripts only; do NOT seed blocks with your "
                         "git commit times (default: commits ARE included)")
    ap.set_defaults(with_commits=True)
    ap.add_argument("--commit-minutes", type=int, default=0, metavar="M",
                    help="with --with-commits, credit M minutes of lead-up work "
                         "before each commit (default 0: never invent time)")
    ap.add_argument("--min", type=float, default=0.1, metavar="H",
                    help="roll rows under H hours into (other); 0 shows all")
    ap.add_argument("--timesheet", action="store_true",
                    help="preset: every repo, nested project/ticket breakdown, "
                         "written to the CSVs. Equivalent to "
                         "--all-projects --by-project --by-ticket --append")
    ap.add_argument("--ticket-prefix",
                    help="restrict --by-ticket to one board, e.g. STHS")
    a = ap.parse_args()
    if a.timesheet:
        a.all_projects = a.by_project = a.by_ticket = a.append = True

    global MO_GLOB, SO_GLOB, REPO, CSV_PATH, MO_EXCLUDE
    if a.all_projects:
        MO_GLOB = os.path.join(PROJECTS, "*")
        SO_GLOB = os.path.join(PROJECTS, "*" + WORKER_MARK + "*")
        MO_EXCLUDE = WORKER_MARK      # workers are machine time, never engaged
        REPO = ""
        label = "ALL PROJECTS"
    else:
        MO_GLOB, SO_GLOB, REPO, label = resolve_project(a.project)
    CSV_PATH = os.path.join(OUTDIR, ("all-projects.csv" if a.all_projects
                                     else f"{os.path.basename(REPO) or 'daily'}.csv"))
    mode = "dominant" if a.dominant else "proportional"
    src = "claude+git" if a.with_commits else "claude sessions only"
    print(f"project: {label}   (gap {a.gap}m, {mode} attribution, {src})\n")

    global TICKET
    if a.ticket_prefix:
        TICKET = re.compile(r"\b(" + re.escape(a.ticket_prefix) + r"-\d{1,6})\b")

    gap = a.gap * 60
    today = dt.date.today()
    if a.frm:
        start = dt.date.fromisoformat(a.frm)
        end = dt.date.fromisoformat(a.to) if a.to else today
    else:
        end = today
        start = today - dt.timedelta(days=a.days - 1)

    mo_ev, mo_user, so_ev, mo_text, mo_proj = collect(gap, want_text=a.by_ticket or a.blocks)
    detail = []   # (date, project, ticket, hours) for the detail CSV

    # Commit counts always work now, including under --all-projects, where REPO
    # is empty and the old per-repo git call silently returned 0 for every day.
    git_ev, git_counts = git_events(start, end)
    sources = "claude"
    if a.with_commits:
        sources = "claude+git"
        pad = dt.timedelta(minutes=a.commit_minutes)
        for label, items in git_ev.items():
            for ts, subj in items:
                for point in ((ts - pad, ts) if pad else (ts,)):
                    mo_ev[point.date()].append(point)
                    mo_proj[point.date()].append((point, label))
                if (a.by_ticket or a.blocks) and subj:
                    mo_text[ts.date()].append((ts, subj, label))

    rows = []
    print(f"{'date':<12} {'day':<4} {'engaged':>8} {'blocks':>7} {'msgs':>6} "
          f"{'worker':>7} {'commits':>8}")
    print("-" * 60)
    total = 0.0
    for i in range((end - start).days + 1):
        day = start + dt.timedelta(days=i)
        if day not in mo_ev:
            print(f"{day}  {day:%a}  {'—':>8}")
            continue
        bl = blocks(mo_ev[day], gap)
        secs = sum((b - x).total_seconds() for x, b in bl)
        so_secs = sum((b - x).total_seconds()
                      for x, b in blocks(so_ev.get(day, []), gap))
        n = sum(git_counts.get(day, {}).values())
        total += secs
        print(f"{day}  {day:%a}  {secs/3600:>7.2f}h {len(bl):>7} {mo_user[day]:>6} "
              f"{so_secs/3600:>6.2f}h {n:>8}")
        rows.append({
            "date": day.isoformat(), "weekday": f"{day:%a}",
            "engaged_hours": round(secs / 3600, 2),
            "blocks": len(bl), "your_messages": mo_user[day],
            "worker_hours": round(so_secs / 3600, 2), "commits": n,
            "gap_minutes": a.gap, "attribution": mode, "sources": sources,
        })
        if a.blocks:
            for bs, be in bl:
                dur = (be - bs).total_seconds() / 3600
                tag = block_label(bs, be, mo_text.get(day, []), mo_proj.get(day, []))
                print(f"{'':<14} {bs:%H:%M}-{be:%H:%M} {dur:>6.2f}h  {tag}")
        if a.by_project and a.by_ticket:
            nested = by_project_ticket(bl, mo_text.get(day, []),
                                       mo_proj.get(day, []), a.dominant)
            for pj, tks in sorted(nested.items(),
                                  key=lambda kv: -sum(kv[1].values())):
                ph = sum(tks.values()) / 3600
                if ph < a.min:
                    continue
                print(f"{'':<14} {pj:<34} {ph:>6.2f}h")
                for tk, s in sorted(rollup(tks, a.min).items(), key=lambda kv: -kv[1]):
                    print(f"{'':<18} {tk:<30} {s/3600:>6.2f}h")
                    detail.append({"date": day.isoformat(), "weekday": f"{day:%a}",
                                   "project": pj, "ticket": tk,
                                   "hours": round(s / 3600, 2)})
        elif a.by_project:
            for pj, s in sorted(rollup(by_project(bl, mo_proj.get(day, []), a.dominant), a.min).items(),
                                key=lambda kv: -kv[1]):
                print(f"{'':<18} {pj:<34} {s/3600:>6.2f}h")
                detail.append({"date": day.isoformat(), "weekday": f"{day:%a}",
                               "project": pj, "ticket": "", "hours": round(s / 3600, 2)})
        elif a.by_ticket:
            for tk, s in sorted(rollup(by_ticket(bl, mo_text.get(day, []), a.dominant), a.min).items(),
                                key=lambda kv: -kv[1]):
                print(f"{'':<18} {tk:<16} {s/3600:>6.2f}h")
                detail.append({"date": day.isoformat(), "weekday": f"{day:%a}",
                               "project": "", "ticket": tk, "hours": round(s / 3600, 2)})
    print("-" * 60)
    print(f"{'TOTAL':<18} {total/3600:>7.2f}h over {len(rows)} active days")

    if a.append and rows:
        existing = {}
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH) as fh:
                for r in csv.DictReader(fh):
                    existing[r["date"]] = r
        for r in rows:
            existing[r["date"]] = r          # refresh, never duplicate
        os.makedirs(OUTDIR, exist_ok=True)
        cols = list(rows[0].keys())
        with open(CSV_PATH, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for d in sorted(existing):
                row = {c: existing[d].get(c, "") for c in cols}
                w.writerow(row)
        print(f"\nwrote {len(existing)} rows -> {CSV_PATH}")

        if detail:
            dpath = CSV_PATH.replace(".csv", "-detail.csv")
            keep = []
            if os.path.exists(dpath):
                dates = {r["date"] for r in detail}
                with open(dpath) as fh:
                    keep = [r for r in csv.DictReader(fh) if r["date"] not in dates]
            with open(dpath, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(detail[0].keys()),
                                   extrasaction="ignore")
                w.writeheader()
                for r in sorted(keep + detail,
                                key=lambda r: (r["date"], r.get("project", ""),
                                               r.get("ticket", ""))):
                    w.writerow(r)
            print(f"wrote {len(keep) + len(detail)} rows -> {dpath}")


if __name__ == "__main__":
    main()
