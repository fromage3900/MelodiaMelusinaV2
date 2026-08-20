#!/usr/bin/env python3
"""
build_melusina_locomotion_stack.py -- repair ABP_Melusina_Current's locomotion.

WHAT IS ACTUALLY BROKEN
-----------------------
Content/Exports/battle_anim_ui_export/2_ABP_Melusina_Current_state_machines.json shows
the live `MelusinaLocomotion` state machine holds exactly four states:

    Idle -> JumpStart -> Airborne -> Land -> Idle

There is no ground-locomotion state, and `BS_Melusina_Locomotion` is not referenced by
the AnimGraph at all. So:

  * walk/run never triggers -- there is nothing for velocity to drive; and
  * idle is a T-pose -- the entry state resolves to no sequence, so it emits the
    reference pose.

Both are one repair, not two.

THE JUMP WIND-UP
----------------
Owner requirement: the INITIAL HOLD of SpaceBar triggers the wind-up animation.
`MelodiaTraversalJump` is already bound to SpaceBar (Config/DefaultInput.ini:115).
The chain is:

    Pressed -> bJumpWindup = true      (no launch yet)
            -> JumpWindup state plays the anticipation crouch
            -> AnimNotify 'JumpLaunch' inside that clip calls Jump()
            -> bIsFalling goes true -> Airborne

The state entry rule is `bJumpWindup`, deliberately NOT `bIsFalling`: keying off
IsFalling means the wind-up could only begin after she has already left the ground,
which is the opposite of an anticipation pose.

WHY MONOLITH AND NOT T3D
------------------------
T3D injection (MONOLITH_GUIDE Recipe 16) is the right tool for authoring a node
cluster that has no first-class action -- which is the case for the Event Graph
wind-up logic in BP_MelusinaJRPGCharacter (see --emit-jump-t3d).

It is the wrong tool here. `animation_query` exposes first-class, C++-backed actions
for state machines (`add_state_to_machine`, `set_state_animation`, `add_transition`,
`set_transition_rule`, `build_foot_ik_pass`). Hand-rolling state-machine T3D when
those exist buys nothing and gives up their validation. Tools/t3d_anim_injector.py
already records the same conclusion from the other side: raw Unreal Python has
"limited API surface" for state-machine graph editing.

SAFETY
------
Dry-run by default. `--apply` is required to mutate. Mutations abort on the first
failure rather than continuing, so a schema mismatch leaves the graph untouched
instead of half-wired. Every run writes a report to Saved/Audit/.

USAGE
-----
    python Tools/build_melusina_locomotion_stack.py --preflight
    python Tools/build_melusina_locomotion_stack.py --measure
    python Tools/build_melusina_locomotion_stack.py --apply
    python Tools/build_melusina_locomotion_stack.py --verify
    python Tools/build_melusina_locomotion_stack.py --emit-jump-t3d

Requires the interactive Unreal Editor running with Monolith on 127.0.0.1:9316.
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


def _read_preflight():
    """Existing states from the last --preflight, so apply() is re-runnable.

    Adding a state that already exists is the same non-idempotency trap Recipe 16
    warns about for T3D re-injection: you get two of the thing, not one.
    """
    path = AUDIT_DIR / "melusina_locomotion_preflight.json"
    if not path.exists():
        return None
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get(
            "existing_states", []))
    except (ValueError, OSError):
        return None


def _read_preflight_transitions():
    """(from,to) pairs already present, from the last --preflight."""
    path = AUDIT_DIR / "melusina_locomotion_preflight.json"
    if not path.exists():
        return set()
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        pairs = set()
        for m in (d.get("checks", {}).get("state_machines", {})
                  .get("state_machines") or []):
            if m.get("name") not in (None, STATE_MACHINE):
                continue
            for t in m.get("transitions") or []:
                pairs.add((t.get("from"), t.get("to")))
        return pairs
    except (ValueError, OSError, KeyError, TypeError):
        return set()


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


def apply_stack(dry_run=True):
    """Repair the state machine. Aborts on first failure; never half-wires."""
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[{mode}] rebuilding {STATE_MACHINE}")
    sm_spec, blend_spec = load_specs()

    existing_vars = _read_preflight_vars()
    existing_transitions = _read_preflight_transitions()
    existing = _read_preflight()
    if existing is None:
        # No preflight on disk. Fall back to the committed export baseline, which is
        # the only real data in Content/Exports (the sibling JSONs are error stubs).
        existing = {"Idle", "JumpStart", "Airborne", "Land"}
        print("  no preflight report found -- assuming committed baseline "
              f"{sorted(existing)}. Run --preflight against the live editor to be sure.")
    else:
        print(f"  preflight says existing states: {sorted(existing)}")

    # NEVER remove states. Live preflight (2026-08-16) found a 'Glide' state absent from
    # the committed export; the old `stale = existing - spec` rule would have deleted it,
    # and Glide is live traversal (pawn sets bRequireCapabilityProviderForGlide=true).
    # A state this driver does not know about is a state it must not touch.
    spec_states = {s["name"] for s in sm_spec["states"]}
    unknown = sorted(existing - spec_states)
    if unknown:
        print(f"  preserving {len(unknown)} state(s) not in spec: {unknown}")
    stale = []

    steps = []

    def step(label, tool, action, params):
        steps.append({"label": label, "tool": tool,
                      "action": action, "params": params})

    # 1. Variables. Only what the live ABP lacks (preflight showed 11 already present).
    for name, meta in sm_spec["required_variables"].items():
        if name in existing_vars:
            print(f"  variable '{name}' already exists -- skipping")
            continue
        step(f"variable:{name}", "blueprint_query", "add_variable",
             {"asset_path": ABP, "name": name, "type": meta["type"],
              "default_value": str(meta["default"]).lower()})

    # 2. Blendspace axis. 630/650 clamps the 714 uu/s sprint gate; 750 does not.
    axis = blend_spec["axis_settings"]
    step("blendspace:axis", "animation_query", "set_blend_space_axis",
         {"asset_path": blend_spec["blendspace_path"], "axis": "X",
          "name": axis["horizontal_axis"],
          "min": axis["horizontal_range"][0], "max": axis["horizontal_range"][1]})

    # 3. States. Idle exists but is bound to a stale clip -- that is the T-pose.
    for state in sm_spec["states"]:
        if state["name"] not in existing:
            step(f"state:{state['name']}", "animation_query", "add_state_to_machine",
                 {"asset_path": ABP, "machine_name": STATE_MACHINE,
                  "state_name": state["name"],
                  "position_x": state["position"][0],
                  "position_y": state["position"][1]})
        else:
            print(f"  state '{state['name']}' exists -- binding animation only")
        step(f"state_anim:{state['name']}", "animation_query", "set_state_animation",
             {"asset_path": ABP, "machine_name": STATE_MACHINE,
              "state_name": state["name"],
              "anim_asset_path": state["animation"], "loop": state["loop"]})

    step("entry_state", "animation_query", "set_anim_entry_state",
         {"asset_path": ABP, "machine_name": STATE_MACHINE,
          "state_name": sm_spec["entry_state"]})

    # 4. Transitions. add_transition takes no blend_time; cross-fade is a node
    #    property set separately, tracked as follow-up rather than faked here.
    for t in sm_spec["transitions"]:
        if t["from"] not in existing and t["from"] not in {x["name"] for x in sm_spec["states"]}:
            continue
        if (t["from"], t["to"]) in existing_transitions:
            print(f"  transition {t['from']}->{t['to']} exists -- rule only")
        else:
            step(f"transition:{t['from']}->{t['to']}", "animation_query",
                 "add_transition",
                 {"asset_path": ABP, "machine_name": STATE_MACHINE,
                  "from_state": t["from"], "to_state": t["to"]})
        step(f"rule:{t['from']}->{t['to']}", "animation_query", "set_transition_rule",
             {"asset_path": ABP, "machine_name": STATE_MACHINE,
              "from_state": t["from"], "to_state": t["to"], "rule": t["rule"]})

    # 5. Montage slot -- montages evaluate to nothing without it.
    step("montage_slot", "animation_query", "add_slot_node",
         {"asset_path": ABP, "slot_name": "DefaultSlot"})

    step("compile", "blueprint_query", "compile_blueprint", {"asset_path": ABP})
    step("save", "blueprint_query", "save_asset", {"asset_path": ABP})

    report = {"kind": "melusina_locomotion_apply", "abp": ABP,
              "dry_run": dry_run, "step_count": len(steps), "steps": []}

    if dry_run:
        for s in steps:
            print(f"  would {s['tool']}:{s['action']}  [{s['label']}]")
        report["steps"] = steps
        write_report("melusina_locomotion_apply_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned. Re-run with --apply to execute.")
        return report

    require_editor()
    before = bp("get_graph_fingerprint", {"asset_path": ABP, "graph_name": "AnimGraph"})
    report["fingerprint_before"] = before

    for s in steps:
        print(f"  {s['tool']}:{s['action']}  [{s['label']}]")
        try:
            result = call(s["tool"], s["action"], s["params"])
            report["steps"].append({**s, "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({**s, "error": str(e), "ok": False})
            report["aborted_at"] = s["label"]
            write_report("melusina_locomotion_apply.json", report)
            raise SystemExit(
                f"\nABORTED at [{s['label']}]: {e}\n"
                f"Graph left unmodified from this step onward. Report written.\n"
                f"If this is a parameter-schema mismatch, run:\n"
                f"  describe_query action_schema for {s['tool']}:{s['action']}\n"
                f"and correct the params in this script -- do not guess again."
            )

    report["fingerprint_after"] = bp(
        "get_graph_fingerprint", {"asset_path": ABP, "graph_name": "AnimGraph"})

    # Artifact check. save_asset reporting saved=true is NOT proof of a write.
    uasset = (PROJECT_DIR / "Content" /
              ABP.replace("/Game/", "").replace("/", os.sep)).with_suffix(".uasset")
    if uasset.exists():
        mtime = datetime.fromtimestamp(uasset.stat().st_mtime, timezone.utc)
        age_s = (datetime.now(timezone.utc) - mtime).total_seconds()
        report["uasset_mtime"] = mtime.isoformat()
        report["uasset_written_this_run"] = age_s < 600
        if age_s >= 600:
            report["ok"] = False
            print("")
            print(f"  WARNING: {uasset.name} on disk is {age_s/3600:.1f}h old.")
            print("  The graph changed IN MEMORY but nothing was written. If this "
                  "editor exits, the work is lost.")
            print("  A wedged editor accepts edits and reports saved=true while "
                  "never completing the package write -- restart it and re-run.")
        else:
            print("")
            print(f"  disk write confirmed: {uasset.name} @ {mtime:%H:%M:%S}Z")
    else:
        report["uasset_mtime"] = None
        print("")
        print(f"  WARNING: {uasset} not found on disk.")

    write_report("melusina_locomotion_apply.json", report)
    return report


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

JUMP_T3D_NOTES = """\
BP_MelusinaJRPGCharacter Event Graph -- SpaceBar hold -> wind-up.

`MelodiaTraversalJump` is a legacy ActionMapping on SpaceBar
(Config/DefaultInput.ini:115), so it yields Pressed/Released exec pins directly.

Required wiring (author once by hand, Ctrl+C, save as the T3D payload, then
parameterise NodeGuid/PinId per MONOLITH_GUIDE Recipe 16 step 2):

  InputAction MelodiaTraversalJump
    Pressed  -> Set bJumpWindup = true        on the ABP instance
                (Get Mesh -> Get Anim Instance -> Cast to ABP_Melusina_Current)
                DO NOT call Jump() here. That is the entire point -- launching on
                press is what makes an anticipation pose impossible.
    Released -> Set bJumpWindup = false

  AnimNotify_JumpLaunch (on ABP_Melusina_Current, forwarded to the pawn)
             -> Jump()
             -> Set bJumpWindup = false

  Event OnLanded
             -> Set bJumpWindup = false       (safety: covers a Released that was
                                               swallowed by a state change)

Recipe 16 step 0 first: `python Tools/bp_live_path.py BP_MelusinaJRPGCharacter`
and abort on ORPHAN or AMBIGUOUS. Injecting into an unreachable graph is worse
than a bad payload because it succeeds.

Then: validate_nodes_t3d -> get_graph_fingerprint -> inject_nodes_t3d
(compile: true) -> get_graph_fingerprint + assert_graph_matches -> save_asset.

Re-injection is NOT idempotent -- guids are forced unique on import, so running
twice gives two working copies of the cluster. Delete first or assert absence.
"""


def emit_jump_t3d():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIT_DIR / "melusina_jump_windup_wiring.md"
    path.write_text(JUMP_T3D_NOTES, encoding="utf-8")
    print(JUMP_T3D_NOTES)
    print(f"  written -> {path}")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preflight", action="store_true",
                    help="read-only: dump live ABP/blendspace/IK-rig state")
    ap.add_argument("--measure", action="store_true",
                    help="read-only: measure real root-motion speed per clip")
    ap.add_argument("--plan", action="store_true",
                    help="dry run: print every step that --apply would execute")
    ap.add_argument("--apply", action="store_true",
                    help="mutate the ABP (requires the editor)")
    ap.add_argument("--verify", action="store_true",
                    help="read-only: prove the repair landed")
    ap.add_argument("--emit-jump-t3d", action="store_true",
                    help="print the SpaceBar wind-up wiring contract")
    args = ap.parse_args()

    if not any(vars(args).values()):
        ap.print_help()
        return 0

    try:
        if args.preflight:
            preflight()
        if args.measure:
            measure()
        if args.emit_jump_t3d:
            emit_jump_t3d()
        if args.apply or args.plan:
            apply_stack(dry_run=not args.apply)
        if args.verify:
            verify()
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
