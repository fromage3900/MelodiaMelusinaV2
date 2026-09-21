# Resonance Loom - headless Blender smoke test (the harness that runs is the harness that ships).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Run:
#   blender --background --python Tools/BlenderAddons/melodia_resonance_loom/tests/blender_smoke.py
#
# Exercises the full bpy pipeline headlessly: addon register -> beatgrid import
# -> paint groups -> rhythm-key bake -> validation -> (no FBX export; that needs
# a selection export and is covered by the operator poll path). Exits non-zero
# on any failure so CI/a session can gate on it.

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLENDER_ADDONS = HERE.parent.parent
REPO = BLENDER_ADDONS.parent.parent  # Tools/BlenderAddons -> Tools -> repo root
if str(BLENDER_ADDONS) not in sys.path:
    sys.path.insert(0, str(BLENDER_ADDONS))

import addon_utils  # noqa: E402  (Blender builtin)

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[SMOKE] PASS {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"[SMOKE] FAIL {name} -- {detail}")


def main() -> None:
    import bpy

    enable_result = addon_utils.enable("melodia_resonance_loom", default_set=True)
    check("addon_enabled", enable_result is not None, f"enable returned {enable_result}")
    check(
        "scene_props_registered",
        hasattr(bpy.types.Scene, "loom"),
        "bpy.types.Scene.loom missing",
    )
    ops = ("melodia_loom.import_beatgrid", "melodia_loom.ensure_paint_groups",
           "melodia_loom.bake_rhythm_keys", "melodia_loom.validate_garment",
           "melodia_loom.export_garment")
    for op in ops:
        check(f"operator_{op}", hasattr(bpy.ops, op.split(".")[0]) or op in dir(bpy.ops))

    # Beatgrid import against the real project asset.
    beatgrid = REPO / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody_beatgrid.mid"
    if not beatgrid.exists():
        check("beatgrid_present", False, f"{beatgrid} missing")
    else:
        scene = bpy.context.scene
        scene.loom.cosmetic_id = "Cos_Dress_SmokeTest"
        result = bpy.ops.melodia_loom.import_beatgrid(midi_path=str(beatgrid))
        check("import_beatgrid_finished", "FINISHED" in result, f"result={result}")
        check("bpm_parsed_128", abs(scene.loom.bpm - 128.0) < 1.0, f"bpm={scene.loom.bpm}")
        downbeats = [m for m in scene.timeline_markers if m.name.startswith("LOOM_DOWN_")]
        accents = [m for m in scene.timeline_markers if m.name.startswith("LOOM_ACC_")]
        check("downbeat_markers", len(downbeats) > 0, f"count={len(downbeats)}")
        check("accent_markers", len(accents) > 0, f"count={len(accents)}")

    # Mesh pipeline: cube -> paint groups -> bake -> validate.
    bpy.ops.mesh.primitive_cube_add()
    mesh = bpy.context.active_object
    result = bpy.ops.melodia_loom.ensure_paint_groups()
    check("ensure_paint_groups_finished", "FINISHED" in result, f"result={result}")
    groups = {g.name for g in mesh.vertex_groups}
    check("loom_groups_created", {"LOOM_Accent", "LOOM_Hit", "LOOM_Hem"} <= groups, f"{groups}")

    # Weight every other vertex into LOOM_Accent so the bake has something to move.
    accent = mesh.vertex_groups["LOOM_Accent"]
    hit = mesh.vertex_groups["LOOM_Hit"]
    for v in mesh.data.vertices:
        if v.index % 2 == 0:
            accent.add([v.index], 0.9, "REPLACE")
        else:
            hit.add([v.index], 0.9, "REPLACE")
    result = bpy.ops.melodia_loom.bake_rhythm_keys()
    check("bake_finished", "FINISHED" in result, f"result={result}")
    keys = {kb.name for kb in mesh.data.shape_keys.key_blocks}
    check("accent_key_baked", "SK_LOOM_Accent" in keys, f"{keys}")
    check("hit_key_baked", "SK_LOOM_Hit" in keys, f"{keys}")
    accent_key = mesh.data.shape_keys.key_blocks.get("SK_LOOM_Accent")
    moved = any(
        (accent_key.data[v.index].co - v.co).length > 1e-6
        for v in mesh.data.vertices if v.index % 2 == 0
    )
    check("accent_key_displaces", moved, "no vertex moved by the accent bake")

    result = bpy.ops.melodia_loom.bake_secondary_action()
    check("secondary_action_finished", "FINISHED" in result, f"result={result}")
    anim = mesh.data.shape_keys.animation_data
    action = anim.action if anim is not None else None
    check("secondary_action_named",
          action is not None and action.name == "ACT_LoomSecondary",
          f"action={getattr(action, 'name', None)}")
    total_keys = 0
    try:
        total_keys = sum(len(fc.keyframe_points) for fc in action.fcurves) if action else 0
    except AttributeError:
        check("fcurves_readable", False, "action.fcurves unavailable in this Blender")
    check("secondary_action_keyed", total_keys > 0, f"keyframe count={total_keys}")

    result = bpy.ops.melodia_loom.validate_garment()
    check("validate_finished", "FINISHED" in result, f"result={result}")
    text = bpy.data.texts.get("LOOM_Validation_Report")
    check("report_written", text is not None and len(text.lines) > 0,
          "LOOM_Validation_Report empty")

    print("=" * 60)
    if FAILURES:
        for f in FAILURES:
            print(f"[SMOKE] FAILED: {f}")
        sys.exit(1)
    print("[SMOKE] all checks passed")


main()
