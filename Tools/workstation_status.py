#!/usr/bin/env python3
"""Workstation status - one machine-comparable state file, desktop or laptop.

The two-workstation contract already defines the *vocabulary*: `synced`, `ahead`,
`behind`, `dirty`, `diverged`, `lfs-error`, `lfs-unavailable`, plus the PC -> laptop
handoff sequence. What it does not have is anything an AGENT can assert on. Today
`deploy/sync_workstation.ps1` prints a report for a human; a recursive loop cannot
read a console table and refuse to proceed.

So this tool does not reimplement sync. It CONSUMES the JSON that sync_workstation.ps1
already writes (`Saved/Workstation/<MACHINE>-sync-report.json`) and adds the facts a
cross-machine handoff needs and that the sync report does not carry:

  * the editor lease holder - the single-writer fact that must not differ between machines
  * Perforce client + opened-changelist state - the binary half of the handoff
  * local-tier reachability - whether the free model lane works on THIS machine
  * active agent lanes and the refs they have pinned

The result is `Saved/Workstation/<MACHINE>-workstation.json`. Two machines produce two
files with the same schema, so "is the laptop in a state where it may start work?" is a
comparison rather than a judgement call. That comparison is the point: Honcho shares
MEMORY across machines, git shares FILES, and this shares STATE.

Read-only. Nothing here mutates a repo, a depot, or an editor.

Usage:
  python Tools/workstation_status.py            # human table
  python Tools/workstation_status.py --json
  python Tools/workstation_status.py --compare <other-machine-workstation.json>
"""

import argparse
import datetime
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANES_DIR = os.path.join(ROOT, ".git", "agents", "lanes")

SCHEMA = "melodia.workstation_status/v1"


def shared_root():
    """The primary checkout, not necessarily the directory we are standing in.

    `Saved/` is gitignored, so a lane worktree has no `Saved/Workstation/` of its
    own. Reading only the local one would report `never-synced` on a perfectly
    healthy machine and block work for no reason - which is how a status tool
    teaches people to ignore it. The git common dir points at the real checkout.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
        common = out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        common = ""
    if common:
        common = os.path.abspath(os.path.join(ROOT, common))
        # <checkout>/.git -> <checkout>
        if os.path.basename(common).lower() in (".git",) or os.path.basename(common).lower() == "":
            candidate = os.path.dirname(common)
            if os.path.isdir(candidate):
                return candidate
    return ROOT


def workstation_dir():
    return os.path.join(shared_root(), "Saved", "Workstation")


def _machine():
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown"


def _run(args, default=None):
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.SubprocessError):
        return default
    if out.returncode != 0:
        return default
    return out.stdout.strip()


def git_state():
    head = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    dirty = _run(["git", "status", "--porcelain"])
    if head is None:
        return {"available": False}
    return {
        "available": True,
        "head": head,
        "branch": branch,
        "dirty_file_count": len([l for l in (dirty or "").splitlines() if l.strip()]),
    }


def sync_state():
    """Read the report sync_workstation.ps1 already produced. Absent is a real
    answer, not an error - it means this machine has not run the handoff command,
    which is exactly the thing the laptop agent needs to be told before it starts."""
    report_dir = workstation_dir()
    path = os.path.join(report_dir, "%s-sync-report.json" % _machine())
    if not os.path.exists(path):
        newest = sorted(glob.glob(os.path.join(report_dir, "*-sync-report.json")))
        if not newest:
            return {"report": None, "sync_state": "never-synced",
                    "detail": "no sync report on this machine; run "
"deploy/sync_workstation.ps1 -Mode Check"}
        path = newest[-1]
    try:
        # utf-8-sig, not utf-8: sync_workstation.ps1 writes this file through
        # PowerShell, which prefixes a UTF-8 BOM. Plain utf-8 raises on the first
        # byte and the report reads as "unreadable" on the one machine where the
        # whole point is to trust it.
        with open(path, "r", encoding="utf-8-sig") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as exc:
        return {"report": path, "sync_state": "unreadable", "detail": str(exc)}
    age_note = ""
    try:
        age_h = (datetime.datetime.now().timestamp()
                 - os.path.getmtime(path)) / 3600.0
        if age_h > 24:
            age_note = "report is %.0fh old - re-run -Mode Check before trusting it" % age_h
    except OSError:
        pass
    return {
        "report": path,
        "generated_at": report.get("generated_at"),
        "sync_state": report.get("sync_state"),
        "recommended_action": report.get("recommended_action"),
        "branch_ahead": report.get("branch_ahead"),
        "branch_behind": report.get("branch_behind"),
        "lfs": report.get("lfs"),
        "note": age_note,
    }


def p4_state():
    """Binary half of the handoff. `p4 opened` is a count, never a submit."""
    info = _run(["p4", "info"])
    if info is None:
        return {"available": False,
                "detail": "p4 not answering - start p4d (-r D:/perforce/root -p 1666) "
                          "or the binary lane has no depot"}
    root = next((l.split(":", 1)[1].strip() for l in info.splitlines()
                 if l.startswith("Server root")), None)
    client = next((l.split(":", 1)[1].strip() for l in info.splitlines()
                   if l.startswith("Client name")), None)
    opened = _run(["p4", "opened"])
    default = _run(["p4", "opened", "-c", "default"])
    pending = _run(["p4", "changes", "-s", "pending", "-u", "froma"])
    return {
        "available": True,
        "server_root": root,
        "client": client,
        "opened_count": len([l for l in (opened or "").splitlines() if l.strip()]),
        "default_cl_count": len([l for l in (default or "").splitlines() if l.strip()]),
        "pending_changelists": len([l for l in (pending or "").splitlines() if l.strip()]),
        "note": "opened files are NOT submitted; a depot submit is owner-only",
    }


def lease_state():
    sys.path.insert(0, HERE)
    try:
        import agent_lease
    except ImportError:
        return {"available": False}
    state = agent_lease.status()
    return {
        "available": True,
        "held": state["held"],
        "holder": (state.get("lease") or {}).get("holder"),
        "session": (state.get("lease") or {}).get("session"),
        "expires_at": (state.get("lease") or {}).get("expires_at"),
        "stop_sentinels": state["stop_sentinels"],
        "modal_open": state["modal_open"],
    }


def lanes():
    out = []
    if not os.path.isdir(LANES_DIR):
        return out
    for name in sorted(os.listdir(LANES_DIR)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(LANES_DIR, name), "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        out.append({
            "lane": data.get("lane") or name[:-5],
            "ref": data.get("ref") or data.get("branch"),
            "claims": len(data.get("paths") or data.get("claims") or []),
            "heartbeat": data.get("heartbeat"),
        })
    return out


def local_tier():
    """Is the free model lane usable on THIS machine? The registry routes
    git_vcs_automation to T4_LOCAL, so a laptop where Ollama is asleep will
    return classical-fallback for doc/git work and quietly spend a paid tier
    instead. That is worth knowing BEFORE the loop starts."""
    sys.path.insert(0, HERE)
    try:
        import model_router
    except ImportError:
        return {"reachable": None, "detail": "model_router not importable"}
    probe = getattr(model_router, "local_endpoint_reachable", None)
    if probe is None:
        # The router's `route` surface lands separately from this one. Report the
        # fact as unknown rather than guessing - a status file that invents a
        # green is worse than one that admits a gap.
        return {"reachable": None,
                "base_url": getattr(model_router, "LOCAL_BASE", ""),
                "detail": "model_router has no local_endpoint_reachable yet "
                          "(lands with the H1 route subcommand)"}
    return {"reachable": probe(), "base_url": getattr(model_router, "LOCAL_BASE", "")}


def collect():
    status = {
        "schema": SCHEMA,
        "machine": _machine(),
        "generated_at": (datetime.datetime.now().astimezone()
                         .replace(microsecond=0).isoformat()),
        "git": git_state(),
        "sync": sync_state(),
        "p4": p4_state(),
        "editor_lease": lease_state(),
        "lanes": lanes(),
        "local_tier": local_tier(),
    }
    status["may_start_work"] = may_start_work(status)
    return status


def may_start_work(status):
    """The contract's rule, expressed once so both machines agree.

    `Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`: require
    sync_state == 'synced' before starting edits; 'diverged' means STOP - no
    rebase, no reset, no force. This is that rule as a boolean.
    """
    blockers = []
    sync = status.get("sync") or {}
    state = sync.get("sync_state")
    if state in ("diverged",):
        blockers.append("sync_state=diverged: explicit review required, no automatic pull")
    elif state in ("ahead",):
        blockers.append("sync_state=ahead: push unpublished commits before switching machines")
    elif state in ("dirty",):
        blockers.append("sync_state=dirty: commit the intended work before handoff")
    elif state in ("lfs-error",):
        blockers.append("lfs-error: refs may match but binary hydration failed")
    elif state in ("lfs-unavailable",):
        blockers.append("lfs-unavailable: install/fix git-lfs first")
    elif state in (None, "never-synced", "unreadable"):
        blockers.append("no usable sync report: run deploy/sync_workstation.ps1 -Mode Check")

    git = status.get("git") or {}
    if git.get("available") and git.get("dirty_file_count", 0) > 0:
        blockers.append("git worktree has %d uncommitted change(s)"
                        % git["dirty_file_count"])

    lease = status.get("editor_lease") or {}
    if lease.get("available") is False:
        # FAIL CLOSED. Found 2026-10-02: when Tools/agent_lease.py was not
        # importable (it lives in another lane), `held` came back None, and
        # `if lease.get("held")` read that as "no lease" - so the single-writer
        # check silently stopped applying. An unknown lease state is not a free
        # editor.
        blockers.append("editor lease state UNKNOWN (Tools/agent_lease.py not importable): "
                        "the single-writer check cannot be trusted here")
    elif lease.get("held") is None:
        blockers.append("editor lease state UNKNOWN (no 'held' field): "
                        "treat the editor as possibly held")
    elif lease.get("held"):
        blockers.append("editor lease HELD by %s - a second writer is refused"
                        % lease.get("holder"))
    if lease.get("stop_sentinels"):
        blockers.append("stop sentinel present: %s" % ", ".join(lease["stop_sentinels"]))
    if lease.get("modal_open"):
        blockers.append("MODAL_OPEN in the newest editor log - the editor will not take a command")

    p4 = status.get("p4") or {}
    if not p4.get("available"):
        blockers.append("perforce unreachable: the binary lane has no depot")
    return {"ok": not blockers, "blockers": blockers}


def compare(mine, other_path):
    """Two machines, one schema. Only the facts that must NOT differ are listed;
    everything else is allowed to be different (that is the point of two machines).
    """
    with open(other_path, "r", encoding="utf-8-sig") as fh:
        other = json.load(fh)
    rows = []

    def add(name, a, b, must_match):
        same = (a == b)
        rows.append({"fact": name, "this_machine": a, "other": b,
                     "agrees": same, "must_match": must_match})

    add("git.head", (mine.get("git") or {}).get("head"), (other.get("git") or {}).get("head"), True)
    add("sync_state", (mine.get("sync") or {}).get("sync_state"),
        (other.get("sync") or {}).get("sync_state"), True)
    add("p4.client", (mine.get("p4") or {}).get("client"), (other.get("p4") or {}).get("client"), False)
    add("p4.server_root", (mine.get("p4") or {}).get("server_root"),
        (other.get("p4") or {}).get("server_root"), False)
    add("editor_lease.held", (mine.get("editor_lease") or {}).get("held"),
        (other.get("editor_lease") or {}).get("held"), False)
    add("local_tier.reachable", (mine.get("local_tier") or {}).get("reachable"),
        (other.get("local_tier") or {}).get("reachable"), False)
    return rows


def render(status):
    print("=" * 72)
    print(" WORKSTATION %s   %s" % (status["machine"], status["generated_at"]))
    print("=" * 72)
    git = status.get("git") or {}
    print("\nGIT")
    if git.get("available"):
        print("  %s  %s" % (git["branch"], (git["head"] or "")[:12]))
        print("  uncommitted files: %d" % git["dirty_file_count"])
    else:
        print("  unavailable")
    sync = status.get("sync") or {}
    print("\nSYNC (from sync_workstation.ps1)")
    print("  state: %s" % sync.get("sync_state"))
    if sync.get("recommended_action"):
        print("  action: %s" % sync["recommended_action"])
    if sync.get("note"):
        print("  NOTE: %s" % sync["note"])
    p4 = status.get("p4") or {}
    print("\nPERFORCE")
    if p4.get("available"):
        print("  client %s   server_root %s" % (p4.get("client"), p4.get("server_root")))
        print("  opened %d (default CL %d)   pending CLs %d   [none submitted]"
              % (p4.get("opened_count", 0), p4.get("default_cl_count", 0),
                 p4.get("pending_changelists", 0)))
    else:
        print("  %s" % p4.get("detail"))
    lease = status.get("editor_lease") or {}
    print("\nEDITOR LEASE")
    print("  %s" % ("HELD by %s (%s)" % (lease.get("holder"), lease.get("session"))
                     if lease.get("held") else "free"))
    if lease.get("stop_sentinels"):
        print("  STOP: %s" % ", ".join(lease["stop_sentinels"]))
    if lease.get("modal_open"):
        print("  MODAL_OPEN in %s" % lease.get("modal_log"))
    print("\nLOCAL TIER (free model lane)")
    print("  reachable: %s  %s" % (status["local_tier"].get("reachable"),
                                   status["local_tier"].get("base_url") or ""))
    if status.get("lanes"):
        print("\nLANES")
        for lane in status["lanes"]:
            print("  %-18s %-32s claims=%s" % (lane["lane"], lane.get("ref") or "?",
                                               lane.get("claims")))
    gate = status.get("may_start_work") or {}
    print("\nMAY START WORK: %s" % ("YES" if gate.get("ok") else "NO"))
    for blocker in gate.get("blockers", []):
        print("  BLOCKED: %s" % blocker)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Machine-comparable workstation state.")
    ap.add_argument("--json", dest="json_out", action="store_true")
    ap.add_argument("--compare", metavar="OTHER_JSON",
                    help="diff against another machine's workstation.json")
    ap.add_argument("--write", action="store_true",
                    help="also write Saved/Workstation/<MACHINE>-workstation.json")
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 when may_start_work is false")
    args = ap.parse_args()

    status = collect()

    if args.compare:
        try:
            rows = compare(status, args.compare)
        except (OSError, ValueError) as exc:
            sys.stderr.write("cannot compare: %s\n" % exc)
            return 2
        print("%-22s %-22s %-22s %s" % ("FACT", "THIS", "OTHER", "AGREES"))
        print("-" * 78)
        for row in rows:
            flag = "same" if row["agrees"] else ("DIFFER" if row["must_match"] else "differs (ok)")
            print("%-22s %-22s %-22s %s"
                  % (row["fact"], str(row["this_machine"])[:21],
                     str(row["other"])[:21], flag))
        mismatched = [r for r in rows if r["must_match"] and not r["agrees"]]
        if mismatched:
            print("\n%s machine(s) disagree on a must-match fact: %s"
                  % (len(mismatched), ", ".join(r["fact"] for r in mismatched)))
            return 2
        print("\nno must-match disagreement")
        return 0

    if args.write:
        os.makedirs(workstation_dir(), exist_ok=True)
        path = os.path.join(workstation_dir(), "%s-workstation.json" % status["machine"])
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(status, fh, indent=2)
            fh.write("\n")
        print("wrote %s" % os.path.relpath(path, ROOT))
        if args.json_out:
            print(json.dumps(status, indent=2))
        return 0

    if args.json_out:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        render(status)
    if args.strict and not status["may_start_work"]["ok"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
