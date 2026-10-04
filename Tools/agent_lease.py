#!/usr/bin/env python3
"""Editor lease - one writer at a time for any Unreal editor mutation.

This is H1 mechanism 3 of the orchestrator plan. Why it exists: the project's
single-writer rule has always been *remembered*, and remembering has already
cost real incidents (two editors against one graph; a second lane mutating while
a PIE session was live). A lease turns it into something a script can refuse.

    python Tools/agent_lease.py acquire --holder <name> --session <id> --surface monolith
    python Tools/agent_lease.py status
    python Tools/agent_lease.py release --holder <name>
    python Tools/agent_lease.py show

State: one JSON file at Saved/Agents/editor.lease
    {holder, session, surface, acquired_at, expires_at, pid, note}

Refusal rules, all of them the point:
  * a second holder is refused while the lease is live
  * an EXPIRED lease is reclaimable, and says so, rather than wedging the project
  * a `deploy/*_LOOP_STOP` sentinel refuses acquisition - the stop button wins
  * MODAL_OPEN in the newest editor log refuses acquisition - a modal dialog is
    an editor that will not take a command, and pretending otherwise is how a
    session gets wedged

This is a mutual-exclusion hint, not a distributed lock. It is deliberately
boring: a single local file, atomic writes, and no daemon. It cannot stop a human
with a keyboard; it stops agents that forget to ask.
"""

import argparse
import datetime
import errno
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEASE_PATH = os.path.join(ROOT, "Saved", "Agents", "editor.lease")
DEPLOY_DIR = os.path.join(ROOT, "deploy")
LOG_DIRS = (os.path.join(ROOT, "Saved", "Logs"),)
STOP_SUFFIX = "_LOOP_STOP"
DEFAULT_TTL_S = 900
# A modal dialog makes the editor refuse commands; a lease on top of that is a
# lie, so we refuse to hand one out.
LOG_TAIL_BYTES = 2 * 1024 * 1024


def _now():
    return time.time()


def _iso(ts):
    return (datetime.datetime.fromtimestamp(ts)
            .astimezone().replace(microsecond=0).isoformat())


def stop_sentinels():
    """deploy/*_LOOP_STOP files. Their presence means a lane was told to stop."""
    found = []
    if os.path.isdir(DEPLOY_DIR):
        for name in sorted(os.listdir(DEPLOY_DIR)):
            if name.endswith("_LOOP_STOP"):
                found.append(os.path.join("deploy", name))
    return found


def newest_editor_log():
    newest = None
    newest_ts = -1.0
    for log_dir in LOG_DIRS:
        if not os.path.isdir(log_dir):
            continue
        for name in sorted(os.listdir(log_dir)):
            if not name.lower().endswith(".log"):
                continue
            path = os.path.join(log_dir, name)
            try:
                ts = os.path.getmtime(path)
            except OSError:
                continue
            if ts > newest_ts:
                newest_ts, newest = ts, path
    return newest


def modal_open(log_path=None):
    """True when the newest editor log shows a modal dialog.

    MODAL_OPEN is a modal dialog, not a hang. An editor sitting in one will not
    service a mutation request, so we refuse to hand out a lease.
    """
    path = log_path or newest_editor_log()
    if not path:
        return False, None
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            if size > LOG_TAIL_BYTES:
                fh.seek(size - LOG_TAIL_BYTES)
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return False, path
    return "MODAL_OPEN" in tail, path


def read_lease():
    if not os.path.exists(LEASE_PATH):
        return None
    try:
        with open(LEASE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        # A corrupt lease must not be silently treated as "no lease": that is how
        # two holders get in. Treat it as held by an unknown holder.
        return {"holder": "<unreadable lease>", "corrupt": True,
                "acquired_at": None, "expires_at": 0}
    return data


def lease_is_live(lease, now=None):
    if not lease:
        return False
    if lease.get("corrupt"):
        return True
    expires = lease.get("expires_at") or 0
    try:
        expires = float(expires)
    except (TypeError, ValueError):
        return True
    if expires <= 0:
        return True
    return expires > (now or _now())


def write_lease(lease):
    """Atomic replace. A half-written lease that parses as 'free' is the worst
    possible outcome for a lock file."""
    os.makedirs(os.path.dirname(LEASE_PATH), exist_ok=True)
    tmp = LEASE_PATH + ".%d.tmp" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(lease, fh, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, LEASE_PATH)
    return LEASE_PATH


def acquire(holder, session, surface="monolith", ttl_s=DEFAULT_TTL_S, note="", force=False):
    """Return (lease_dict, refusal_or_None)."""
    now = _now()

    sentinels = stop_sentinels()
    if sentinels and not force:
        return None, ("refused: stop sentinel present (%s). The stop button outranks any lane."
                      % ", ".join(sentinels))

    modal, log_path = modal_open()
    if modal and not force:
        return None, ("refused: %s contains MODAL_OPEN. A modal editor will not take a command; "
                      "clear it before mutating." % log_path)

    existing = read_lease()
    if lease_is_live(existing, now) and not force:
        if existing.get("holder") == holder and existing.get("session") == session:
            # Re-acquire by the same holder refreshes, it does not deadlock.
            lease = dict(existing)
            lease["expires_at"] = now + ttl_s
            lease["note"] = note or existing.get("note", "")
            write_lease(lease)
            return lease, None
        return None, ("refused: lease held by holder=%r session=%r surface=%r until %s"
                      % (existing.get("holder"), existing.get("session"),
                         existing.get("surface"),
                         existing.get("expires_at") and _iso(existing["expires_at"]) or "unknown"))

    lease = {
        "holder": holder,
        "session": session,
        "surface": surface,
        "acquired_at": _iso(now),
        "expires_at": now + ttl_s,
        "ttl_s": ttl_s,
        "pid": os.getpid(),
        "note": note,
    }
    write_lease(lease)
    return lease, None


def release(holder, session=None):
    existing = read_lease()
    if not existing:
        return None, "refused: no lease held"
    if existing.get("holder") != holder:
        return None, ("refused: lease is held by %r; only the holder may release it"
                      % existing.get("holder"))
    if session is not None and existing.get("session") != session:
        return None, ("refused: lease session is %r, not %r"
                      % (existing.get("session"), session))
    try:
        os.remove(LEASE_PATH)
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            return None, "refused: %s" % exc
    return {"released": True, "holder": holder, "session": session or existing.get("session")}, None


def status():
    lease = read_lease()
    live = lease_is_live(lease)
    sentinels = stop_sentinels()
    modal, log_path = modal_open()
    return {
        "lease_path": os.path.relpath(LEASE_PATH, ROOT),
        "held": live,
        "lease": lease,
        "stop_sentinels": sentinels,
        "modal_open": modal,
        "modal_log": log_path,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Editor lease - one writer at a time.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_acq = sub.add_parser("acquire")
    p_acq.add_argument("--holder", required=True)
    p_acq.add_argument("--session", required=True)
    p_acq.add_argument("--surface", default="monolith")
    p_acq.add_argument("--ttl", type=int, default=DEFAULT_TTL_S)
    p_acq.add_argument("--note", default="")
    p_acq.add_argument("--force", action="store_true",
                       help="override a stop sentinel / MODAL_OPEN. Still refuses a live holder.")

    p_rel = sub.add_parser("release")
    p_rel.add_argument("--holder", required=True)
    p_rel.add_argument("--session")

    sub.add_parser("status")
    sub.add_parser("show")

    args = ap.parse_args()

    if args.cmd == "acquire":
        lease, refusal = acquire(args.holder, args.session, args.surface,
                                 ttl_s=args.ttl, note=args.note, force=args.force)
        if refusal:
            sys.stderr.write(refusal + "\n")
            return 2
        print("LEASE GRANTED holder=%s session=%s surface=%s until %s"
              % (lease["holder"], lease["session"], lease["surface"], _iso(lease["expires_at"])))
        return 0

    if args.cmd == "release":
        result, refusal = release(args.holder, args.session)
        if refusal:
            sys.stderr.write(refusal + "\n")
            return 2
        print("LEASE RELEASED holder=%s session=%s" % (result["holder"], result["session"]))
        return 0

    state = status()
    if args.cmd == "show":
        print(json.dumps(state, indent=2, ensure_ascii=False))
        return 0
    if state["held"] and state["lease"]:
        lease = state["lease"]
        print("HELD   holder=%s session=%s surface=%s until %s"
              % (lease.get("holder"), lease.get("session"), lease.get("surface"),
                 _iso(lease["expires_at"]) if lease.get("expires_at") else "unknown"))
    else:
        print("FREE   no live lease at %s" % state["lease_path"])
    if state["stop_sentinels"]:
        print("STOP   %s" % ", ".join(state["stop_sentinels"]))
    if state["modal_open"]:
        print("MODAL  %s contains MODAL_OPEN - the editor will not take a command" % state["modal_log"])
    return 0


if __name__ == "__main__":
    sys.exit(main())