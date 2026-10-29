#!/usr/bin/env python3
"""Hybrid-combat overnight lane guard + ledger (deterministic; no LLM logic here).

Contract: Docs/Production/ACFU_USAGE_MATRIX.md section 5. The hermes cron agent calls
`preflight` before anything and `mark` after anything. Editor/Monolith/UBT/p4/git access is
OS-level only here; every mutation is performed by the agent through Monolith's HTTP surface
under the matrix's laws. This script exists so "is the surface free" is never a judgment call.

Stdlib only. Repo-root-relative behavior via __file__.
"""
import argparse
import datetime as _dt
import glob as _glob
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEDGER_DIR = os.path.join(ROOT, "Saved", "Audit", "HybridOvernight_20261029")
LEDGER = os.path.join(LEDGER_DIR, "ledger.json")
MONOLITH = "http://127.0.0.1:9316"
EDITOR_EXE = "UnrealEditor.exe"
BUILD_EXES = ("UnrealBuildTool.exe", "MSBuild.exe", "cl.exe", "link.exe")

# Files/directories this lane may commit or p4-manage. Anything else is a blocked-note.
ALLOW_GIT = (
    "Source/BS_GodFile/MelodiaIntegration/",
    "deploy/hybrid_overnight.py",
    "Docs/Production/ACFU_USAGE_MATRIX.md",
    "CURRENT_STATE.md",
    "Saved/Audit/HybridOvernight_20261029/",
)
ALLOW_P4 = (
    "Content/MelodiaIntegration/Hybrid/",
    "Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset",
    "Content/MelodiaIntegration/Blueprints/BP_MelodiaJRPGCharacter.uasset",
)
ALLOW_DIRTY_PREFIXES = ALLOW_P4 + (
    "/Game/HoudiniEngine/Temp/",
    "/Game/Melodia/Characters/Melusina/Animations/Montages/",
)


def _now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _default_ledger():
    return {
        "lane": "acf-hybrid-overnight-lane",
        "contract": "Docs/Production/ACFU_USAGE_MATRIX.md",
        "created": _now(),
        "build_status": "running",  # the 2026-10-28 closed-editor build for the dodge code
        "steps": [
            {"n": i, "title": t, "status": s}
            for i, t, s in [
                (1, "dodge as ACFU action ability", "doing"),
                (2, "one real ACF melee exchange (teams/ASC/attack grant)", "queued"),
                (3, "scythe 3-step onto the action system", "queued"),
                (4, "perfect-grade execution (presentation-first)", "queued"),
                (5, "hit FX via ACM events + invalid-tag sweep", "queued"),
                (6, "vault/ledge on one authored Orrery run", "queued"),
                (7, "live key-prompt WBP from the ability set", "queued"),
                (8, "owner ratification bundle", "queued-owner"),
            ]
        ],
        "log": [],
    }


def _load():
    if not os.path.exists(LEDGER):
        os.makedirs(LEDGER_DIR, exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as fh:
            json.dump(_default_ledger(), fh, indent=2)
    with open(LEDGER, encoding="utf-8") as fh:
        return json.load(fh)


def _save(led):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as fh:
        json.dump(led, fh, indent=2)


def _procs():
    out = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout
    names = []
    for line in out.splitlines():
        m = re.match(r'^"([^,"]+)"', line)
        if m:
            names.append(m.group(1))
    return names


def _http(path, body=None, timeout=5):
    req = urllib.request.Request(
        MONOLITH + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _monolith_tool(tool, action, params):
    return _http("/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": {"action": action, "params": params}},
    })


def _log_idle_seconds():
    logs = sorted(
        _glob.glob(os.path.join(ROOT, "Saved", "Logs", "*.log")),
        key=os.path.getmtime, reverse=True,
    )
    if not logs:
        return 9e9
    return (_dt.datetime.now().timestamp() - os.path.getmtime(logs[0]))


def cmd_state(_args):
    print(json.dumps(_load(), indent=2))
    return 0


def cmd_preflight(args):
    led = _load()
    result = {"status": "GO", "reasons": [], "warn": [], "ts": _now()}
    procs = _procs()
    editors = procs.count(EDITOR_EXE)
    building = [p for p in procs if p in BUILD_EXES]
    disk_gb = shutil.disk_usage("C:\\").free / 2**30
    result["context"] = {
        "editors": editors, "building": building, "disk_free_gb": round(disk_gb, 2),
        "log_idle_s": int(_log_idle_seconds()), "build_status_ledger": led.get("build_status"),
    }
    if disk_gb < 2.0:
        result["status"] = "BLOCK"; result["reasons"].append("C: free < 2 GB (Zen low-disk guard)")
    if building:
        result["status"] = "WAIT"; result["reasons"].append("toolchain process running: " + ",".join(set(building)))
    if editors > 1:
        result["status"] = "BLOCK"; result["reasons"].append("more than one UnrealEditor")
    health_ok = False
    if editors == 1:
        try:
            h = _http("/health", timeout=5)
            health_ok = h.get("status") == "ok"
            result["context"]["monolith"] = h
        except Exception as exc:  # noqa: BLE001
            result["status"] = "WAIT"; result["reasons"].append("editor up, Monolith not answering: %s" % exc)
        if health_ok:
            idle = result["context"]["log_idle_s"]
            if idle < 300:
                result["status"] = "WAIT"; result["reasons"].append("editor log active %ss ago - another lane holds the surface" % idle)
            try:
                dirty = _monolith_tool("editor_query", "list_dirty_packages", {})
                pkgs = json.loads(dirty["result"]["content"][0]["text"]).get("dirty_packages", [])
                foreign = [p["package"] for p in pkgs if not any(p["package"].startswith(x) for x in ALLOW_DIRTY_PREFIXES)]
                if foreign:
                    result["warn"].append("non-lane dirty packages (do NOT save them): %s" % foreign)
                # CLOSING the editor for a build destroys foreign unsaved work. Builds are only
                # legal when every dirty package is transient Houdini temp or lane-owned.
                hard_foreign = [p for p in foreign if not p.startswith("/Game/HoudiniEngine/Temp/")]
                result["context"]["close_safe"] = not hard_foreign
                if hard_foreign and led.get("next_action") == "build":
                    result["status"] = "WAIT"
                    result["reasons"].append("close-unsafe: foreign unsaved packages %s" % hard_foreign)
            except Exception as exc:  # noqa: BLE001
                result["warn"].append("dirty readback failed: %s" % exc)
    elif editors == 0:
        if led.get("build_status") == "running":
            # Self-heal a stuck 'running': if no toolchain process survives AND the DLL is
            # newer than every source, the build objectively finished. Otherwise stay WAIT.
            src = max((os.path.getmtime(p) for p in
                       _glob.glob(os.path.join(ROOT, "Source", "**", "*.h"), recursive=True) +
                       _glob.glob(os.path.join(ROOT, "Source", "**", "*.cpp"), recursive=True)), default=0)
            dll = os.path.join(ROOT, "Binaries", "Win64", "UnrealEditor-BS_GodFile.dll")
            dll_t = os.path.getmtime(dll) if os.path.exists(dll) else 0
            if not building and dll_t >= src:
                led["build_status"] = "passed"
                led["log"].append({"ts": _now(), "step": 1, "status": "build-self-healed",
                                   "note": "dll newer than sources, no toolchain running"})
                _save(led)
                result["warn"].append("build_status auto-marked passed (dll>=sources, no UBT)")
            else:
                result["status"] = "WAIT"
                result["reasons"].append("build still recorded running (build-check for facts; "
                                         "auto-mark 'failed' + rebuild only if no UBT process for >30 min)")
        else:
            result["context"]["editor"] = "absent - launch required (allowed when steps need it)"
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["status"], "|", "; ".join(result["reasons"] + result["warn"]) or "surface free")
    return 0 if result["status"] == "GO" else (2 if result["status"] == "WAIT" else 3)


def cmd_mark(args):
    led = _load()
    step = next((s for s in led["steps"] if s["n"] == args.step), None)
    if step is None:
        print("no such step", file=sys.stderr); return 1
    step["status"] = args.status
    step["updated"] = _now()
    if args.evidence:
        step["evidence"] = args.evidence
    if args.note:
        step["note"] = args.note
    if args.build_status:
        led["build_status"] = args.build_status
    led["log"].append({"ts": _now(), "step": args.step, "status": args.status,
                       "note": args.note or "", "evidence": args.evidence or ""})
    _save(led)
    print(json.dumps(step, indent=2))
    return 0


def _check_paths(paths, allow):
    bad = []
    for p in paths:
        if any(ch in p for ch in "*?[]"):
            bad.append(p + " (glob)")
            continue
        norm = p.replace("\\", "/")
        if not any(norm.startswith(a) for a in allow):
            bad.append(p + " (outside lane allowlist)")
    return bad


def cmd_commit(args):
    paths = [p for p in args.paths.split(",") if p.strip()]
    bad = _check_paths(paths, ALLOW_GIT)
    if bad:
        print("REFUSED: " + "; ".join(bad), file=sys.stderr); return 1
    # Exact-path commit ONLY. Never a bare `git commit`: other lanes' staged files may sit in
    # the index and a bare commit would swallow them. --only + pathspec commits just these paths.
    subprocess.run(["git", "add", "--"] + paths, cwd=ROOT, check=True)
    r = subprocess.run(["git", "commit", "--only", "-m", args.msg, "--"] + paths,
                       cwd=ROOT, capture_output=True, text=True)
    print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "?")
    if r.returncode != 0:
        return r.returncode
    if args.push:
        p = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT,
                           capture_output=True, text=True)
        print((p.stdout or p.stderr or "").strip().splitlines()[-1] if (p.stdout or p.stderr) else "push silent")
        if p.returncode != 0:
            print("PUSH FAILED (remote moved?): fetch + rebase this lane's commit manually; "
                  "never force-push.", file=sys.stderr)
            return p.returncode
    return 0


def cmd_p4_open(args):
    paths = [p for p in args.paths.split(",") if p.strip()]
    bad = _check_paths(paths, ALLOW_P4)
    if bad:
        print("REFUSED: " + "; ".join(bad), file=sys.stderr); return 1
    for p in paths:
        disk = os.path.join(ROOT, p)
        op = "edit" if os.path.exists(disk) else "add"
        if op == "add":
            os.makedirs(os.path.dirname(disk), exist_ok=True)
            open(disk, "ab").close()
        r = subprocess.run(["p4", op, p], cwd=ROOT, capture_output=True, text=True)
        print(p, op, "->", (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "?")
    return 0


def cmd_p4_submit(args):
    """Stage+verify+submit EXACTLY the lane's files - gated by explicit owner authorization.

    Front-door law (binding): 'Explicit owner permission is still required for ... any
    Perforce submit.' The 2026-10-28 owner night directive covers STAGING (p4-open + saves)
    and lane git commits; it does not substitute a submit. Without --owner-authorized this
    refuses, period. With it: empty dedicated CL -> reopen exact files -> two-way verify ->
    submit; any mismatch reopens the lane's files back to default and deletes the CL.
    Never speculates depot paths."""
    if not args.owner_authorized:
        print("p4 submit needs explicit owner permission (AGENTS binding rule). The overnight "
              "lane STAGES ONLY: p4-open the exact paths, save the assets, list the pending CL "
              "in the receipt, and leave the submit to the owner.", file=sys.stderr)
        return 2
    paths = [p for p in args.paths.split(",") if p.strip()]
    bad = _check_paths(paths, ALLOW_P4)
    if bad:
        print("REFUSED: " + "; ".join(bad), file=sys.stderr); return 1
    m = re.search(r"P4CLIENT=(\S+)", subprocess.run(
        ["p4", "set", "P4CLIENT"], cwd=ROOT, capture_output=True, text=True).stdout)
    if not m:
        print("cannot read P4CLIENT", file=sys.stderr); return 1
    cl_out = subprocess.run(
        ["p4", "change", "-i"], cwd=ROOT,
        input="Client: %s\nDescription:\n\t%s\n" % (m.group(1), args.desc),
        capture_output=True, text=True)
    cm = re.search(r"Change (\d+) created", cl_out.stdout)
    if not cm:
        print("p4 change failed:", cl_out.stdout, cl_out.stderr, file=sys.stderr); return 1
    cl = cm.group(1)
    try:
        for p in paths:
            r = subprocess.run(["p4", "reopen", "-c", cl, "--", p], cwd=ROOT,
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError("reopen failed %s: %s" % (p, (r.stderr or r.stdout).strip()))
            v = subprocess.run(["p4", "opened", "--", p], cwd=ROOT,
                               capture_output=True, text=True).stdout
            if ("change " + cl) not in v:
                raise RuntimeError("verify failed: %s not in CL %s (%s)" % (p, cl, v.strip()))
        opened = subprocess.run(["p4", "opened", "-c", cl], cwd=ROOT,
                                capture_output=True, text=True).stdout
        n = len([ln for ln in opened.splitlines() if ln.strip()])
        if n != len(paths):
            raise RuntimeError("CL %s holds %d files, expected exactly %d" % (cl, n, len(paths)))
        sub = subprocess.run(["p4", "submit", "-c", cl], cwd=ROOT,
                             capture_output=True, text=True)
        if "submitted" not in (sub.stdout or "").lower():
            raise RuntimeError("submit unconfirmed: %s %s" % (sub.stdout, sub.stderr))
        print((sub.stdout.strip().splitlines() or ["?"])[-1])
        return 0
    except RuntimeError as exc:
        for p in paths:  # touch only our own lane's files, never anyone else's
            subprocess.run(["p4", "reopen", "-c", "default", "--", p], cwd=ROOT,
                           capture_output=True, text=True)
        subprocess.run(["p4", "change", "-d", cl], cwd=ROOT, capture_output=True, text=True)
        print("NOT SUBMITTED, rolled back CL %s: %s" % (cl, exc), file=sys.stderr)
        return 1


def cmd_build_check(_args):
    """Deterministic 'is the DLL older than our sources' answer for the lane agent.
    The opencode-shell that launched the 2026-10-28 build is session-local; the ledger
    says running until someone records passed/failed. build-check gives that someone facts."""
    src = max((os.path.getmtime(p) for p in _glob.glob(os.path.join(ROOT, "Source", "**", "*.h"), recursive=True) +
               _glob.glob(os.path.join(ROOT, "Source", "**", "*.cpp"), recursive=True)), default=0)
    dll = os.path.join(ROOT, "Binaries", "Win64", "UnrealEditor-BS_GodFile.dll")
    dll_t = os.path.getmtime(dll) if os.path.exists(dll) else 0
    print(json.dumps({
        "dll": dll, "dll_mtime": _dt.datetime.fromtimestamp(dll_t).isoformat(timespec="seconds") if dll_t else None,
        "newest_source": _dt.datetime.fromtimestamp(src).isoformat(timespec="seconds") if src else None,
        "up_to_date": dll_t >= src, "build_process_seen": any(
            p in BUILD_EXES for p in _procs()),
    }, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_preflight)
    p = sub.add_parser("state"); p.set_defaults(fn=cmd_state)
    p = sub.add_parser("build-check"); p.set_defaults(fn=cmd_build_check)
    p = sub.add_parser("mark"); p.add_argument("--step", type=int, required=True)
    p.add_argument("--status", required=True); p.add_argument("--note"); p.add_argument("--evidence")
    p.add_argument("--build-status", choices=["running", "passed", "failed"],
                   help="record the closed-editor build result (step 1a)")
    p.set_defaults(fn=cmd_mark)
    p = sub.add_parser("commit"); p.add_argument("--paths", required=True); p.add_argument("--msg", required=True)
    p.add_argument("--push", action="store_true"); p.set_defaults(fn=cmd_commit)
    p = sub.add_parser("p4-open"); p.add_argument("--paths", required=True); p.set_defaults(fn=cmd_p4_open)
    p = sub.add_parser("p4-submit"); p.add_argument("--paths", required=True); p.add_argument("--desc", required=True)
    p.add_argument("--owner-authorized", action="store_true",
                   help="affirm explicit owner permission for THIS submit (binding rule; loop never passes it)")
    p.set_defaults(fn=cmd_p4_submit)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
