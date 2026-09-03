# -*- coding: utf-8 -*-
"""Remap character_rig (ARP dotted names) -> SK_Melusina_Skeleton contract names.

Cursor/Blender lane. This script RENAMES BONES IN MEMORY ONLY - it never saves
the stage blend. It is the Blender-side half of the V2 split-mesh integration:

  1. Load stage blend (or use the already-open file).
  2. Rename every character_rig bone per the verified map
     (specs/anim_presets/melusina_arp_to_contract_bones.json):
       a. dot -> underscore sanitization (DEF_eye.L -> DEF_eye_L)
       b. semantic deform-chain map (pelvis -> root_x, thigh_l -> thigh_stretch_l, ...)
       c. drop ARP IK helper bones (ik_foot_*, ik_hand_*) from the armature
  3. Rename matching vertex groups so skin weights follow the bones.
  4. Write a rename report to Saved/Audit/melusina_rig_remap_report.json
     (NOT the stage). Exit code 0 only when every deform bone resolves.

For the v22 1124-bone stage, the complete export route is
`Tools/bind_melusina_v2_pieces.py`. It performs the same in-memory semantic
remap plus collision resolution, actual mesh-group validation, synthetic
contract completion, and five-piece export. This legacy seven-helper checker
is intentionally not a promotion path for the v22 stage: a dotted-name
cleanup alone cannot prove a 465-bone contract.

DO NOT SAVE THE STAGE. If you need a persisted copy, save-as a Sidecar under
Saved/Audit/ (per AGENTS.md stage-save gate and MELUSINA_BLENDER_WARDROBE_SSOT).

Run:
  blender <stage>.blend -b -P Tools/remap_melusina_rig_to_contract.py [--apply] [--check-only]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy  # noqa: F401  (Blender API; import fails outside blender)

TOOLS = Path(__file__).resolve().parent
PROJECT = TOOLS.parent
MAP_PATH = PROJECT / "specs" / "anim_presets" / "melusina_arp_to_contract_bones.json"
REPORT_PATH = PROJECT / "Saved" / "Audit" / "melusina_rig_remap_report.json"


def log(msg: str) -> None:
    print(f"[rig-remap] {msg}", flush=True)


def load_map() -> dict:
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    return {
        "semantic": data["semantic_map"],
        "drop": set(data["drop"]),
        "target_count": data["target_bone_count"],
    }


def find_character_rig():
    for name in ("character_rig", "melusina_character_rig", "Armature"):
        ob = bpy.data.objects.get(name)
        if ob and ob.type == "ARMATURE":
            return ob
    return None


def sanitize_dots(name: str) -> str:
    return name.replace(".", "_")


def rename_plan(arm) -> dict:
    """Compute rename pairs + drops. Pure function, no mutation."""
    semantic, drop, target_count = load_map().values()
    plan = {"renames": {}, "drops": [], "unresolved": [], "pre_count": 0, "post_count": 0}
    bones = arm.data.bones
    plan["pre_count"] = len(bones)
    for bone in bones:
        src = bone.name
        dst = sanitize_dots(src)
        if dst in semantic:
            dst = semantic[dst]
        if src in drop or dst in drop:
            plan["drops"].append(src)
            continue
        if src != dst:
            plan["renames"][src] = dst
    plan["post_count"] = plan["pre_count"] - len(plan["drops"])
    return plan


def apply_plan(arm, plan) -> None:
    """Rename bones (in-memory). Renames propagate to vertex groups of bound meshes."""
    for src, dst in plan["renames"].items():
        bone = arm.data.bones.get(src)
        if bone:
            bone.name = dst
    for name in plan["drops"]:
        bone = arm.data.bones.get(name)
        if bone:
            arm.data.bones.remove(bone)
    # vertex groups: Blender renames vertex groups when bones are renamed, but
    # only for groups that exactly matched a bone name. Sanitize leftover dotted
    # groups that did not have a matching bone (they would pin weights to nothing).
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.vertex_groups:
            continue
        if obj.find_armature() is not arm:
            continue
        for vg in list(obj.vertex_groups):
            new_name = sanitize_dots(vg.name)
            if new_name != vg.name:
                if any(b.name == new_name for b in arm.data.bones):
                    vg.name = new_name
                else:
                    log(f"WARN orphan group {obj.name}:{vg.name} (no target bone)")


def main() -> int:
    apply = "--apply" in sys.argv
    check_only = "--check-only" in sys.argv
    arm = find_character_rig()
    if arm is None:
        log("FATAL character_rig not found")
        return 2
    plan = rename_plan(arm)

    unresolved = [b.name for b in arm.data.bones if "." in b.name]
    report = {
        "generated_by": "remap_melusina_rig_to_contract.py",
        "stage": Path(bpy.data.filepath or "<unsaved>").name,
        "apply": apply,
        "pre_bone_count": plan["pre_count"],
        "post_bone_count": plan["post_count"],
        "renames": plan["renames"],
        "drops": plan["drops"],
        "dotted_after": unresolved,
        "target_contract_count": load_map()["target_count"],
        "ok": plan["post_count"] == load_map()["target_count"] and not unresolved,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log(f"pre={plan['pre_count']} post={plan['post_count']} "
        f"target={load_map()['target_count']} renames={len(plan['renames'])} drops={len(plan['drops'])}")
    if plan["drops"]:
        log("drops: " + ", ".join(plan["drops"]))
    if unresolved:
        log("dotted-after: " + ", ".join(unresolved[:8]))
    if not report["ok"]:
        log("FATAL post-rename count != contract; refusing (check-only by default)")
        return 1
    if apply:
        apply_plan(arm, plan)
        log(f"applied {len(plan['renames'])} renames, {len(plan['drops'])} drops (in-memory only)")
        log("stage NOT saved. Export now with export_melusina_wardrobe.py --include-armature")
    else:
        log("dry run (no --apply). Re-run with --apply to rename in memory.")
    log(f"report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
