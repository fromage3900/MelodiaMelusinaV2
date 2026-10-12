#!/usr/bin/env python3
"""Read-only legacy locomotion inventory and measurement utilities.

The stale bootstrap writer and delayed Space wind-up instructions are retired.
They predate the current six-state ABP, accepted Shinbi idle, corrected glide and
immediate native jump. Reapplying that recipe can regress working runtime.

Use CURRENT_STATE.md and the existing guarded animation promotion lane for
current work. Retained diagnostics are historical comparisons, not current
presentation, input or contact certification.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parents[1]
SPEC_DIR = PROJECT_DIR / "specs" / "anim_presets"
AUDIT_DIR = PROJECT_DIR / "Saved" / "Audit"

SM_SPEC = SPEC_DIR / "melusina_locomotion_state_machine.json"
BLEND_SPEC = SPEC_DIR / "melusina_locomotion_blend.json"

ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
STATE_MACHINE = "MelusinaLocomotion"


# ---------------------------------------------------------------------------
# Monolith plumbing
# ---------------------------------------------------------------------------

class MonolithError(RuntimeError):
    pass


def call(namespace_tool, action, params=None, timeout=60):
    """One Monolith action. Returns parsed JSON when possible, else raw text."""
    payload = {"action": action, "params": params or {}}
    raw = monolith(namespace_tool, payload, timeout=timeout)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise MonolithError(f"{namespace_tool}:{action} -> {raw}")
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {"_raw": raw}
    # A JSON body can report failure while the transport succeeded. Treat an
    # explicit false success/ok, or a populated error field, as a failure --
    # otherwise a "clean" run silently leaves the graph half-authored.
    if isinstance(parsed, dict):
        for key in ("success", "ok"):
            if parsed.get(key) is False:
                raise MonolithError(
                    f"{namespace_tool}:{action} -> {key}=false: "
                    f"{parsed.get('error') or parsed.get('message') or parsed}")
        if parsed.get("error"):
            raise MonolithError(f"{namespace_tool}:{action} -> {parsed['error']}")
    return parsed


def anim(action, params=None, timeout=60):
    return monolith("animation_query", {"action": action, **(params or {})}, timeout)


def bp(action, params=None, timeout=60):
    return monolith("blueprint_query", {"action": action, **(params or {})}, timeout)


def require_editor():
    raw = monolith("monolith_status", {}, timeout=10)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise MonolithError(
            "Monolith unreachable on 127.0.0.1:9316. Start the interactive Unreal Editor "
            "(a UnrealEditor-Cmd commandlet does not serve Monolith) and retry."
        )
    return raw


def load_specs():
    sm = json.loads(SM_SPEC.read_text(encoding="utf-8"))
    blend = json.loads(BLEND_SPEC.read_text(encoding="utf-8"))
    return sm, blend


def write_report(name, data):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    data.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    path = AUDIT_DIR / name
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  report -> {path}")
    return path


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def preflight():
    """Read-only. Establish what is actually in the ABP before touching it.

    The exported _abp_info / _variables / _graphs JSONs in Content/Exports are all
    Monolith connection-error stubs -- only _state_machines.json carries real data.
    Do not trust them; re-read here.
    """
    print("[preflight] reading live ABP state")
    require_editor()
    sm_spec, blend_spec = load_specs()

    report = {"kind": "melusina_locomotion_preflight", "abp": ABP, "checks": {}}

    def probe(label, fn):
        try:
            report["checks"][label] = fn()
        except MonolithError as e:
            report["checks"][label] = {"error": str(e)}

    probe("state_machines", lambda: anim("get_state_machines", {"asset_path": ABP}))
    probe("abp_variables", lambda: anim("get_abp_variables", {"asset_path": ABP}))
    probe("abp_info", lambda: anim("get_abp_info", {"asset_path": ABP}))
    probe("blend_space", lambda: anim(
        "get_blend_space_info", {"asset_path": blend_spec["blendspace_path"]}))
    probe("ik_rig", lambda: anim(
        "get_ikrig_info", {"asset_path": sm_spec["foot_ik"]["ik_rig"]}))

    # Which states already exist decides add vs. skip in apply().
    existing = _existing_state_names(report["checks"].get("state_machines"))
    report["existing_states"] = sorted(existing)
    report["states_to_add"] = [
        s["name"] for s in sm_spec["states"] if s["name"] not in existing
    ]
    report["baseline_matches_export"] = existing == {
        "Idle", "JumpStart", "Airborne", "Land"}

    write_report("melusina_locomotion_preflight.json", report)
    print(f"  existing states: {report['existing_states']}")
    print(f"  states to add:   {report['states_to_add']}")
    if not report["baseline_matches_export"]:
        print("  NOTE: live SM differs from the committed export baseline. Read the "
              "report before running --apply.")
    return report


def _existing_state_names(sm_payload):
    """Pull state names out of get_state_machines, tolerating shape drift."""
    names = set()
    if not isinstance(sm_payload, dict):
        return names
    machines = sm_payload.get("state_machines") or sm_payload.get("machines") or []
    for machine in machines:
        if not isinstance(machine, dict):
            continue
        if machine.get("name") not in (None, STATE_MACHINE):
            continue
        for state in machine.get("states") or []:
            if isinstance(state, dict) and state.get("name"):
                names.add(state["name"])
            elif isinstance(state, str):
                names.add(state)
    return names


def measure():
    """Measure real ground speed per locomotion clip.

    The blendspace samples were placed at guessed X positions because the clips are
    root-locked (root_motion_speed_known: false). Guessed positions are why the feet
    skate: the blend plays a clip at a speed it was not authored for.
    """
    print("[measure] sampling root motion speed per clip")
    require_editor()
    _, blend_spec = load_specs()

    rows = []
    for sample in blend_spec["samples"]:
        path = sample["animation"]
        row = {"animation": path, "authored_speed": sample["speed"],
               "label": sample["label"]}
        try:
            row["measured"] = anim("get_root_motion_speed", {"asset_path": path})
        except MonolithError as e:
            row["error"] = str(e)
        rows.append(row)
        print(f"  {sample['label']:<14} authored={sample['speed']:>6.1f}  "
              f"measured={row.get('measured', row.get('error'))}")

    report = {"kind": "melusina_locomotion_measured_speeds",
              "blendspace": blend_spec["blendspace_path"], "samples": rows,
              "note": "Reposition blendspace samples onto measured values, or set "
                      "rate_scale where a clip's natural speed differs from its "
                      "sample position. rate_scale is not a fudge for bad placement."}
    write_report("melusina_locomotion_measured_speeds.json", report)
    return report






def _read_preflight_vars():
    """Variable names already on the live ABP, from the last --preflight."""
    path = AUDIT_DIR / "melusina_locomotion_preflight.json"
    if not path.exists():
        return set()
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return {v["name"] for v in
                d.get("checks", {}).get("abp_variables", {}).get("variables", [])}
    except (ValueError, OSError, KeyError, TypeError):
        return set()




def verify():
    """Prove the repair landed in the graph we named."""
    print("[verify] re-reading state machine")
    require_editor()
    sm_spec, blend_spec = load_specs()

    live = anim("get_state_machines", {"asset_path": ABP})
    existing = _existing_state_names(live)
    expected = {s["name"] for s in sm_spec["states"]}

    missing = sorted(expected - existing)

    # Duplicate transitions compile to "will never be taken" because only one of
    # each pair carries the rule. Assert none exist rather than trusting the run.
    import collections
    dupes = {}
    for m in (live.get("state_machines") or []):
        if m.get("name") not in (None, STATE_MACHINE):
            continue
        c = collections.Counter((t.get("from"), t.get("to"))
                                for t in (m.get("transitions") or []))
        dupes = {f"{a}->{b}": n for (a, b), n in c.items() if n > 1}
    ok = (not missing) and (not dupes)

    report = {"kind": "melusina_locomotion_verify", "abp": ABP,
              "expected_states": sorted(expected),
              "live_states": sorted(existing),
              "missing_states": missing,
              "duplicate_transitions": dupes,
              "ok": ok,
              "state_machines": live}

    try:
        report["blend_space"] = anim(
            "get_blend_space_info", {"asset_path": blend_spec["blendspace_path"]})
    except MonolithError as e:
        report["blend_space"] = {"error": str(e)}

    write_report("melusina_locomotion_verify.json", report)
    print(f"  live states: {sorted(existing)}")
    if missing:
        print(f"  MISSING: {missing}")
    else:
        print("  all expected states present")
    if dupes:
        print(f"  DUPLICATE TRANSITIONS: {dupes}")
        print("  (each duplicate compiles to 'will never be taken' -- only one "
              "of the pair carries the rule)")
    else:
        print("  no duplicate transitions")
    print("\n  Static verification only. Runtime acceptance is owner-owned:")
    print("   - stand still  -> breathing idle, NOT a T-pose")
    print("   - hold Space   -> wind-up crouch plays on the PRESS, then she launches")
    print("   - walk/run     -> cycles blend by speed; 714 uu/s sprint does not clamp")
    print("   - land at speed-> resumes locomotion, does not stall in Idle")
    return report


# ---------------------------------------------------------------------------
# Jump wind-up Event Graph payload (T3D -- no first-class action for this)
# ---------------------------------------------------------------------------





def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight', action='store_true', help='read-only live inventory')
    ap.add_argument('--measure', action='store_true', help='read-only root-motion measurement')
    ap.add_argument('--verify', action='store_true', help='historical comparison; not current runtime acceptance')
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.preflight: preflight()
        if args.measure: measure()
        if args.verify: verify()
    except MonolithError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
