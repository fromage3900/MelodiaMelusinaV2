#!/usr/bin/env python3
"""Bind a verified animation clip into an ABP state machine state and prove it landed.

Usage:
  python bind_and_verify.py --state Idle \
      --clip /Game/Melodia/Characters/Melusina/Animations/<path>/<Clip>

Requires: Unreal Editor running with Monolith on 127.0.0.1:9316.
Passes only if: set_state_animation OK -> compile 0 errors -> uasset written to disk
within the last 10 minutes -> live re-read shows the new clip in the state's
SequencePlayer node title.
"""
from __future__ import annotations

import argparse
import json
import stat
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "Tools"))
from mcp_client import monolith  # noqa: E402

ABP_DEFAULT = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
MACHINE_DEFAULT = "MelusinaLocomotion"
UASSET = REPO_ROOT / "Content" / "Melodia" / "Characters" / "Melusina" / "ABP_Melusina_Current.uasset"
MAX_AGE_S = 600


def is_err(r):
    return isinstance(r, str) and r.startswith("ERROR")


def die(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def clear_readonly(path: Path):
    if path.exists():
        mode = path.stat().st_mode
        if mode & stat.S_IREAD and not (mode & stat.S_IWRITE):
            path.chmod(mode | stat.S_IWRITE)
            print(f"[i] cleared ReadOnly on {path.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--abp", default=ABP_DEFAULT)
    ap.add_argument("--machine", default=MACHINE_DEFAULT)
    args = ap.parse_args()

    raw = monolith("monolith_status", {})
    if is_err(raw):
        die(f"Monolith unreachable: {str(raw)[:120]}")

    r = monolith("animation_query", {"action": "set_state_animation",
        "asset_path": args.abp, "machine_name": args.machine,
        "state_name": args.state, "anim_asset_path": args.clip, "loop": True}, timeout=180)
    if is_err(r):
        die(f"set_state_animation: {str(r)[:200]}")
    print("[ok] set_state_animation")

    r = monolith("blueprint_query", {"action": "compile_blueprint",
        "asset_path": args.abp}, timeout=240)
    try:
        d = json.loads(r)
        if d.get("error_count"):
            die(f"compile errors: {d.get('errors')}")
        print(f"[ok] compile ({d.get('warning_count', 0)} warnings)")
    except json.JSONDecodeError:
        die(f"compile unreadable: {str(r)[:200]}")

    clear_readonly(UASSET)
    r = monolith("blueprint_query", {"action": "save_asset", "asset_path": args.abp}, timeout=120)
    if is_err(r):
        die(f"save_asset: {str(r)[:200]}")

    time.sleep(1)
    age = time.time() - UASSET.stat().st_mtime
    if age > MAX_AGE_S:
        die(f"uasset not written to disk (age {age:.0f}s) — in-memory only")
    print(f"[ok] saved ({age:.0f}s ago)")

    d = json.loads(monolith("animation_query", {"action": "get_state_info",
        "asset_path": args.abp, "machine_name": args.machine,
        "state_name": args.state}, timeout=90))
    title = next((n.get("title", "").splitlines()[0] for n in d.get("nodes", [])
                  if n.get("class") == "AnimGraphNode_SequencePlayer"), None)
    expected = args.clip.rsplit("/", 1)[-1]
    if title != expected:
        die(f"live binding is '{title}', expected '{expected}'")

    print(f"[PASS] {args.state} bound to {title} (on-disk verified)")
    report = {"kind": "bind_and_verify", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "state": args.state, "clip": args.clip, "binding": title,
              "uasset_age_s": round(age, 1), "ok": True}
    out = REPO_ROOT / "Saved" / "Audit" / f"bind_and_verify_{args.state.lower()}_{int(time.time())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[i] report -> {out}")


if __name__ == "__main__":
    main()
