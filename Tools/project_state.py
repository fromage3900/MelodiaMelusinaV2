#!/usr/bin/env python3
"""
project_state.py - what is actually true right now, derived, not asserted.

WHY

CLAUDE.md opens with this warning: "A doc's filename date is when it was
written, not when it was last true. This project moves faster than its
documentation." Today alone produced four separate cases of a document or a
finding outliving the truth it described -- a canonical wiring doc pointing at
a disabled MCP server, a scope doc whose "Proven now" list was retracted, a
handoff naming a commit that did not contain what it claimed, and a triage
conclusion built on a substring search that silently missed its target.

So this file reads STATE, not PROSE. Everything below is computed from git, the
filesystem, committed baselines, and (with --live) the running editor. Where it
reports on a document, it reports whether that document is older than the code
it describes -- never what the document says.

    python Tools/project_state.py                 # offline, fast
    python Tools/project_state.py --live          # adds editor-derived facts
    python Tools/project_state.py --out Saved/Dashboards/state.txt

Views: git | gates | baselines | staleness | tools | integration | session_start | live | all
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
WIDTH = 78

# Documents that make claims about the code, mapped to the source they describe.
# A doc older than its subject is not necessarily wrong -- it is UNVERIFIED, and
# that is the distinction this project keeps losing.
#
# This covered 4 of 442 tracked docs until 2026-08-13 while the view's own
# summary line ("N of M tracked docs are behind their subject") read as if it
# meant project-wide coverage. It does not: this is a hand-picked watchlist of
# the docs an agent is most likely to trust at face value, not an audit of
# every doc in the repo. See the summary line in view_staleness() for the
# corrected wording.
DOC_SUBJECTS = {
    "Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md": [
        "Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h",
        "Source/BS_GodFile/MelodiaIntegration/MelodiaInputContextSubsystem.h",
    ],
    "_VERTICAL_SLICE_SCOPE.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "Plugins/Monolith/Docs/MONOLITH_GUIDE.md": [
        "Tools/bp_live_path.py",
        "Tools/graph_reachability.py",
    ],
    "_SESSION_HANDOFF.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "AGENTS.md": [
        "Tools",
        "_AGENT_WORKING_AGREEMENT.md",
    ],
    "_TASK_QUEUE.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "CURRENT_STATE.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "AGENT_START_HERE.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "MELODIA_TECHNICAL_VERTICAL_SLICE.md": [
        "Source/BS_GodFile/MelodiaIntegration",
    ],
    "Docs/PhoneOps/BACKLOG.md": [
        "Docs/P0_TASK_LEDGER.json",
    ],
    ".jcode/coordinator-bootstrap.md": [
        "AGENTS.md",
        "Docs/PhoneOps/BACKLOG.md",
    ],
    "README.md": [
        "Source/BS_GodFile",
    ],
    "COLLABORATOR_SETUP.md": [
        "Tools",
        "specs",
    ],
    "Docs/AGENT_TOOLS.md": [
        "Tools",
    ],
    "Docs/echo/campaign_01_rhythm_damage_delta.md": [
        "specs/echo_pipeline.json",
        "Tools/echo_run.py",
    ],
    "Docs/echo/campaign_02_save_round_trip.md": [
        "specs/echo_pipeline.json",
        "Tools/echo_run.py",
    ],
    "Docs/echo/campaign_03_package_launch.md": [
        "specs/echo_pipeline.json",
        "Tools/echo_run.py",
    ],
    "Docs/echo/campaign_04_result_matrix.md": [
        "specs/echo_pipeline.json",
        "Tools/echo_run.py",
    ],
}


def rule(ch="-"):
    return ch * WIDTH


def header(title, sub=""):
    out = ["", "=" * WIDTH, f" {title}"]
    if sub:
        out.append(f" {sub}")
    out.append("=" * WIDTH)
    return out


def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=PROJECT, capture_output=True,
                           text=True, timeout=60)
        return r.stdout.strip()
    except Exception as e:
        return f"(git failed: {e})"


def newest_mtime(relpath):
    """Newest mtime under a file or directory, or None."""
    path = os.path.join(PROJECT, relpath)
    if os.path.isfile(path):
        return os.path.getmtime(path)
    if not os.path.isdir(path):
        return None
    newest = None
    for root, _dirs, files in os.walk(path):
        for f in files:
            if not f.endswith((".h", ".cpp", ".py")):
                continue
            try:
                m = os.path.getmtime(os.path.join(root, f))
            except OSError:
                continue
            newest = m if newest is None else max(newest, m)
    return newest


def ago(ts):
    if ts is None:
        return "?"
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(ts)
    days = delta.days
    if days > 0:
        return f"{days}d ago"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    return f"{delta.seconds // 60}m ago"


# ---------------------------------------------------------------- views

def view_git():
    lines = header("GIT", "what is committed, and what is loose")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    lines.append(f"  branch            {branch}")
    lines.append("")
    lines.append("  recent commits:")
    for c in git("log", "--oneline", "-8").splitlines():
        lines.append(f"    {c}")

    porcelain = git("status", "--porcelain").splitlines()
    modified = [l for l in porcelain if l[:2].strip() in ("M", "MM", "AM")]
    staged = [l for l in porcelain if l[0] in ("M", "A", "D") and l[0] != " "]
    untracked = [l for l in porcelain if l.startswith("??")]
    lines += [
        "",
        f"  modified          {len(modified)}",
        f"  staged            {len(staged)}",
        f"  untracked         {len(untracked)}",
    ]
    if modified:
        lines.append("")
        lines.append("  modified files (verify ownership before committing --")
        lines.append("  more than one agent writes to this tree):")
        for l in modified[:12]:
            lines.append(f"    {l[3:]}")
    return lines


def view_gates():
    lines = header("FOUNDATION GATES", "parsed from _VERTICAL_SLICE_SCOPE.md checkboxes")
    path = os.path.join(PROJECT, "_VERTICAL_SLICE_SCOPE.md")
    if not os.path.exists(path):
        lines.append("  _VERTICAL_SLICE_SCOPE.md not found")
        return lines
    text = open(path, encoding="utf-8").read()
    done = re.findall(r"^- \[x\] (.+)$", text, re.M | re.I)
    todo = re.findall(r"^- \[ \] (.+)$", text, re.M)
    total = len(done) + len(todo)
    pct = (len(done) / total * 100) if total else 0
    filled = int(pct / 100 * 40)
    lines += [
        f"  {len(done)}/{total} complete  ({pct:.0f}%)",
        f"  [{'#' * filled}{'.' * (40 - filled)}]",
        "",
        "  OPEN:",
    ]
    for t in todo:
        clean = re.sub(r"\*\*|`", "", t).strip()
        lines.append(f"    [ ] {clean[:70]}")
    lines += ["", "  DONE:"]
    for t in done:
        clean = re.sub(r"\*\*|`", "", t).strip()
        lines.append(f"    [x] {clean[:70]}")
    return lines


def view_baselines():
    lines = header("VERIFICATION BASELINES", "the records the gates compare against")
    checks = [
        ("T3D material catalog", "Docs/T3D_Baseline/material_catalog.json"),
        ("BP fingerprints", "Docs/T3D_Baseline/bp_fingerprints.json"),
        ("battle controller export", "Exports/bp_battlecontroller_eventgraph_live.json"),
    ]
    for label, rel in checks:
        path = os.path.join(PROJECT, rel)
        if not os.path.exists(path):
            lines.append(f"  MISSING  {label:<28} {rel}")
            continue
        size = os.path.getsize(path)
        tracked = git("ls-files", rel).strip() != ""
        entries = ""
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                if "families" in data:
                    entries = f"{sum(f['count'] for f in data['families'].values())} assets"
                elif "nodes" in data:
                    entries = f"{len(data.get('nodes', []))} nodes"
                else:
                    entries = f"{len(data)} entries"
        except Exception:
            entries = "(unparseable)"
        flag = "tracked" if tracked else "UNTRACKED - lost on clean checkout"
        lines.append(f"  ok       {label:<28} {entries:<14} {ago(os.path.getmtime(path)):<9} {flag}")
    return lines


def _git_commit_ts(rel):
    """Last COMMIT timestamp for a path, or None.

    Filesystem mtime is unusable in this repo: a bulk touch/clone flattened them, so
    406 of 477 docs report an mtime inside the last 7 days regardless of real age.
    Comparing mtimes therefore reported 14 of 14 watched docs as STALE, most at "0h
    behind" -- pure noise, and noise in a radar is worse than no radar because people
    learn to ignore it. Commit time survives a checkout and is the honest signal.
    """
    out = git("log", "-1", "--format=%ct", "--", rel).strip()
    try:
        return int(out) if out else None
    except ValueError:
        return None


def _newest_commit_ts(subject):
    """Newest commit timestamp across a subject path (file or directory)."""
    return _git_commit_ts(subject)


# Drift below this is treated as simultaneous. Docs and the code they describe are
# routinely committed in the same session; flagging a 40-minute gap as staleness
# trains the reader to ignore the tool.
STALENESS_THRESHOLD_HOURS = 48


def _staleness_rows():
    """(status, doc, note, src) per DOC_SUBJECTS entry. Shared by views."""
    rows = []
    for doc, subjects in DOC_SUBJECTS.items():
        dpath = os.path.join(PROJECT, doc)
        if not os.path.exists(dpath):
            rows.append(("MISSING", doc, "", ""))
            continue
        dm = _git_commit_ts(doc)
        if dm is None:
            rows.append(("?", doc, "untracked - no commit history", ""))
            continue
        newest, newest_src = None, ""
        for sub in subjects:
            m = _newest_commit_ts(sub)
            if m and (newest is None or m > newest):
                newest, newest_src = m, sub
        if newest is None:
            rows.append(("?", doc, "subject not found", ""))
            continue
        drift_h = (newest - dm) / 3600
        if drift_h > STALENESS_THRESHOLD_HOURS:
            rows.append(("STALE", doc, f"{drift_h:.0f}h behind", os.path.basename(newest_src)))
        elif drift_h > 0:
            rows.append(("recent", doc, f"{drift_h:.0f}h (within {STALENESS_THRESHOLD_HOURS}h)", ""))
        else:
            rows.append(("fresh", doc, "", ""))
    return rows


def view_staleness():
    lines = header("DOC STALENESS RADAR",
                   "a doc older than the code it describes is UNVERIFIED, not wrong")
    rows = _staleness_rows()

    for status, doc, note, src in rows:
        mark = {"STALE": "STALE", "?": "  ?  ", "MISSING": "MISS ", "recent": "  ~  "}.get(status, "fresh")
        lines.append(f"  {mark:<7}{doc[:46]:<48}{note}")
        if src:
            lines.append(f"         └─ newer: {src}")
    stale = [r for r in rows if r[0] == "STALE"]
    total_tracked_md = len([l for l in git("ls-files", "*.md").splitlines() if l.strip()])
    lines += [
        "",
        f"  {len(stale)} of {len(rows)} WATCHED docs are more than "
        f"{STALENESS_THRESHOLD_HOURS}h behind their subject.",
        f"  Coverage: {len(rows)} of {total_tracked_md or '?'} tracked .md. This is a "
        "hand-picked watchlist (DOC_SUBJECTS), not project-wide.",
        "  Signal is git COMMIT time, not filesystem mtime -- mtimes in this repo were "
        "flattened by a bulk touch and are meaningless.",
    ]
    if stale:
        lines.append("  Re-verify these against source before acting on any claim they make.")
    return lines


def _ledger_latest() -> dict:
    """Latest recorded status per gate id from Saved/gate_ledger.json."""
    path = os.path.join(PROJECT, "Saved", "gate_ledger.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        return {"_error": f"unreadable: {e}"}
    latest = {}
    for g in ledger.get("gates", []):
        latest[g["id"]] = g
    return latest


def view_integration():
    lines = header("INTEGRATION LOOP", "completion = runtime, save/load, repeat-consume, package launch")
    ledger = _ledger_latest()
    if "_error" in ledger:
        lines.append(f"  gate ledger: {ledger['_error']}")

    # The four gates AGENTS.md says block claiming completion. Ledger ids
    # match the echo manifest completion_gates (runtime/save_load/
    # repeat_consume/package_launch) and record_gate.py KNOWN_GATES.
    completion = [
        ("runtime", "runtime", "Victory/Defeat/Fled/unavailable; each resumes/aborts Quill once"),
        ("save_load", "save_load", "Canonical BP_JRPGSaveGame slot across a full process restart"),
        ("repeat_consume", "repeat_consume", "Flag+reward restore without duplication; stat idempotent"),
        ("package_launch", "package_launch", "Development launch outside the editor"),
    ]
    lines += ["", "  completion gates (ledger-backed):"]
    for label, gid, what in completion:
        rec = ledger.get(gid)
        status = (rec or {}).get("last_status") or (rec or {}).get("status")
        if status == "pass":
            mark, date = "PASS", rec.get("date", "")
            note = rec.get("note", "")[:40]
        elif status == "fail":
            mark, date = "FAIL", rec.get("date", "")
            note = rec.get("note", "")[:40]
        else:
            mark, date, note = "OPEN", "", ""
        lines.append(f"    [{mark:<4}] {label:<16} {date}  {what}")
        if note:
            lines.append(f"                note: {note}")

    # Summary of the scope doc gates (compact), then narrative detail.
    path = os.path.join(PROJECT, "_VERTICAL_SLICE_SCOPE.md")
    if os.path.exists(path):
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            text = ""
        done = len(re.findall(r"^- \[x\] (.+)$", text, re.M | re.I))
        todo = len(re.findall(r"^- \[ \] (.+)$", text, re.M))
        pct = (done / (done + todo) * 100) if (done + todo) else 0
        lines.append(f"  scope checkboxes: {done}/{done + todo} checked ({pct:.0f}%)")
    return lines


def view_session_start():
    """Cold-open orientation. Run before opening any prose.

    Tip, tree, latest ledger row per gate, ledger age, staleness flags.
    Counts and latest-rows only -- no notes, no history. Fails closed:
    an unreadable ledger prints as unreadable, never as empty.
    """
    lines = header("SESSION START", "run first; derived, not asserted")
    lines.append(f"  tip               {git('log', '-1', '--oneline')}")
    lines.append(f"  branch            {git('rev-parse', '--abbrev-ref', 'HEAD')}")
    porcelain = git("status", "--porcelain").splitlines()
    lines.append(f"  dirty             "
                 f"{len([l for l in porcelain if not l.startswith('??')])} tracked, "
                 f"{len([l for l in porcelain if l.startswith('??')])} untracked")
    for l in porcelain[:6]:
        lines.append(f"    {l}")
    lines += ["", "  latest row per gate id (this is standing; older rows are history):"]
    ledger = _ledger_latest()
    if "_error" in ledger:
        lines.append(f"    gate ledger: {ledger['_error']}")
    else:
        for gid in sorted(ledger):
            rec = ledger[gid]
            status = rec.get("status", "?").upper()
            lines.append(f"    [{status:<4}] {gid:<24} {rec.get('date', '')} {rec.get('time', '')}")
    try:
        with open(os.path.join(PROJECT, "Docs", "P0_TASK_LEDGER.json"), encoding="utf-8") as fh:
            as_of = json.load(fh).get("as_of", "?")
        lines.append(f"  p0_task_ledger    as_of {as_of}")
    except Exception:
        lines.append("  p0_task_ledger    unreadable")
    stale = [r for r in _staleness_rows() if r[0] in ("STALE", "MISSING")]
    lines.append(f"  stale watched docs {len(stale)} (see --view staleness)")
    for _, doc, note, _ in stale[:8]:
        lines.append(f"    {doc}  {note}")
    return lines


def view_tools():
    lines = header("VERIFICATION TOOLING", "what exists to check work with")
    tools = [
        ("bp_live_path.py", "is an asset reachable from a configured entry point"),
        ("graph_reachability.py", "dead exec islands inside a graph"),
        ("bp_regression_checker.py", "Blueprint topology drift vs tracked baseline"),
        ("t3d_dashboard.py", "material spine dashboards"),
        ("project_state.py", "this report"),
        ("pie_smoke_runner.py", "PIE smoke with must_present/must_absent"),
        ("regression_suite.py", "composed quick/full regression"),
    ]
    for name, what in tools:
        path = os.path.join(HERE, name)
        mark = "ok     " if os.path.exists(path) else "MISSING"
        lines.append(f"  {mark}{name:<28}{what}")
    lines += ["", "  gates in Docs/T3D_Patterns/wiring/:"]
    wdir = os.path.join(PROJECT, "Docs", "T3D_Patterns", "wiring")
    if os.path.isdir(wdir):
        for f in sorted(os.listdir(wdir)):
            if f.endswith(".py"):
                lines.append(f"    {f}")
    return lines


def view_live():
    lines = header("LIVE EDITOR", "facts that require the running editor")
    sys.path.insert(0, HERE)
    try:
        from mcp_client import monolith
    except Exception as e:
        lines.append(f"  cannot import mcp_client: {e}")
        return lines
    raw = monolith("monolith_status", {})
    if isinstance(raw, str) and raw.startswith("ERROR"):
        lines.append("  editor not reachable on 9316.")
        lines.append("  If it is running but silent, grep the log for MODAL_OPEN before")
        lines.append("  assuming the plugin is at fault -- a modal dialog blocks the game")
        lines.append("  thread and Monolith answers on the game thread.")
        return lines
    try:
        st = json.loads(raw)
        lines.append(f"  monolith {st.get('version')}  port {st.get('server_port')}  "
                     f"{st.get('total_actions')} actions")
        lines.append(f"  engine {st.get('engine_version')}")
        lines.append(f"  project {st.get('project_name')}")
    except Exception:
        lines.append(f"  {str(raw)[:200]}")

    dirty = monolith("editor_query", {"action": "list_dirty_packages"})
    try:
        d = json.loads(dirty)
        n = d.get("count", 0)
        lines += ["", f"  unsaved packages  {n}"]
        for p in d.get("dirty_packages", [])[:12]:
            lines.append(f"    {p.get('package')}")
        if n:
            lines.append("  Unsaved work is lost if the editor is killed. Save before any")
            lines.append("  closed-editor rebuild.")
    except Exception:
        pass
    return lines


VIEWS = {
    "git": view_git,
    "gates": view_gates,
    "baselines": view_baselines,
    "staleness": view_staleness,
    "tools": view_tools,
    "integration": view_integration,
    "session_start": view_session_start,
}


def main():
    # Windows consoles default to cp1252, which cannot encode the box-drawing /
    # arrow characters this report emits. Reconfigure stdout so the report never
    # crashes on encode (reported 2026-08-09: UnicodeEncodeError on '\\u2192').
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Derived project state. Reads state, not prose.")
    ap.add_argument("--view", default="all", choices=list(VIEWS) + ["live", "all"])
    ap.add_argument("--live", action="store_true", help="include editor-derived facts")
    ap.add_argument("--out", help="also write to this path")
    args = ap.parse_args()

    lines = [
        "",
        rule("="),
        f" MELODIA PROJECT STATE - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        " derived from git, filesystem and baselines. no document is quoted as fact.",
        rule("="),
    ]
    if args.view == "all":
        for fn in VIEWS.values():
            lines += fn()
    elif args.view == "live":
        lines += view_live()
    else:
        lines += VIEWS[args.view]()

    if args.live and args.view != "live":
        lines += view_live()

    lines.append("")
    text = "\n".join(lines)
    print(text)

    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(PROJECT, args.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
        print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
