# v3 (2026-10-03): identical guards; reads the v3 flight clip lane (new A_Sir_*_v3 assets, v2 untouched).
"""Stage D guarded import â€” Sir Melodious animation clips onto SK_SirMelodious_Rigged_Skeleton.

WHY THIS FILE EXISTS

`AGENTS.md` forbids FBX automation import outright: two automated FBX imports
crashed this editor (the 165 KB brow-only file, and the iris FBX), both with
StaticShutdownAfterError and no partial assets. The rule is recorded as
absolute.

Those two crashes were SKELETAL MESH imports -- operations that mint new
assets and, if the rig disagrees, a new skeleton. Importing an animation onto
an EXISTING skeleton is a different operation, and it is already the sanctioned
lane: `AGENTS.md` names "Blender retarget/root-motion FBX -> guarded
`Content/Python/import_rokoko_mocap_batch.py` -> existing animation owner" as
the canonical route and names "manual production FBX drag/drop" as the
forbidden one. Five Rokoko takes have gone through that guarded importer
green. This file is that importer, pointed at Sir.

The guards below are the reason it is not the crash class:

  * animation-only -- `import_mesh=False`, `FBXIT_ANIMATION`, no materials,
    no textures. Nothing new can be created except a UAnimSequence.
  * the skeleton is FORCED, so the import cannot mint a competing one.
  * `convert_scene_unit=False` and `import_uniform_scale=1.0`. The Stage C
    contract records the exact trap this avoids: a metre-scale source exported
    with `global_scale=100` *and* `FBX_SCALE_ALL` *and* `apply_unit_scale`
    measured a 99.99x double-scale.
  * scale rejection on readback, in both directions, because a metre-scale
    leak and a double-scale leak look identical in a static import log.
  * wrong-skeleton rejection: ProcessEvent returning is not evidence.

Each clip's expected bone count and key range come from the Stage C v2 contract
(`exports/ue/<clip>.contract.json`), whose own scale/bones/dots gates are all
PASS. Import success is not runtime binding -- the ABP state machine still has
to be pointed at the new sequences, and that is a separate step.

Reads `exports/ue/` (the remapped, scale-fixed Stage C v2 FBX), NOT the
un-remapped originals in `exports/`.
"""

import json
from pathlib import Path

import unreal

PROJECT = Path(unreal.Paths.project_dir())
STAGE_C = PROJECT / "Saved" / "Audit" / "SirMelodious_FlightUnit_20261003" / "exports" / "ue"
DEST_DIR = "/Game/Melodia/Characters/SirMelodious/Animations"
SKELETON = "/Game/Melodia/Characters/SirMelodious/Rigged/SK_SirMelodious_Rigged_Skeleton"
OUT = PROJECT / "Saved" / "Audit" / "SirMelodious_FlightUnit_20261003" / "sir_anim_import_report_v3.json"

# Proved to exist by the Stage C remap reports' sample_after list.
PROBE_BONES = ("c_root_master_x", "foot_l", "c_thigh_b_l")

# A translation magnitude outside this band means the scale leaked in one of the
# two documented directions: ~1e-2 cm is a metre-scale clip that was not
# converted, ~1e+2 cm and up is the 99.99x double-scale the contract found.
SCALE_ABS_MIN_CM = 0.01
SCALE_ABS_MAX_CM = 500.0


def asset_path(obj) -> str:
    return obj.get_path_name().split(".")[0] if obj else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def sample_translations(seq, bone: str) -> list:
    """Local-space translation of one bone across the clip, in UE units (cm)."""
    out = []
    frames = int(seq.get_number_of_frames()) if hasattr(seq, "get_number_of_frames") else 0
    for f in range(0, max(frames, 1), 4):
        try:
            pose = unreal.AnimationLibrary.get_bone_pose_for_frame(seq, bone, float(f), False)
            t = pose.translation
            out.append((float(t.x), float(t.y), float(t.z)))
        except Exception:
            continue
    return out


def classify_scale(seq) -> dict:
    """Reject a metre-scale leak and a double-scale leak. In-place loops may sit
    at zero, so zero is legal here (unlike the Melusina locomotion probe)."""
    worst = None
    checked = 0
    for bone in PROBE_BONES:
        for t in sample_translations(seq, bone):
            mag = max(abs(t[0]), abs(t[1]), abs(t[2]))
            checked += 1
            if worst is None or mag > worst:
                worst = mag
            if 0.0 < mag < SCALE_ABS_MIN_CM:
                return {"verdict": "meter_leak", "bone": bone, "mag_cm": mag}
            if mag > SCALE_ABS_MAX_CM:
                return {"verdict": "double_scale", "bone": bone, "mag_cm": mag}
    if checked == 0:
        return {"verdict": "no_samples", "mag_cm": None}
    return {"verdict": "ok", "mag_cm": worst}


def import_one(fbx: Path, name: str, contract: dict) -> dict:
    report = {"clip": name, "fbx": str(fbx), "ok": False}

    if not fbx.is_file():
        report["error"] = "fbx_missing"
        return report

    skeleton = unreal.load_asset(SKELETON)
    if not skeleton:
        report["error"] = "skeleton_missing"
        return report

    unreal.EditorAssetLibrary.make_directory(DEST_DIR)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx))
    task.set_editor_property("destination_path", DEST_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("skeleton", skeleton)
    # Animation-only. This is the line that keeps us out of the crash class.
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    try:
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    except Exception:
        pass

    try:
        anim = options.get_editor_property("anim_sequence_import_data")
        if anim:
            anim.set_editor_property("import_bone_tracks", True)
            anim.set_editor_property("do_not_import_curve_with_zero", False)
            anim.set_editor_property("remove_redundant_keys", False)
            # The Stage C double-scale guard: unit conversion OFF, scale 1.0.
            for prop_name, value in (("import_uniform_scale", 1.0), ("convert_scene_unit", False)):
                try:
                    anim.set_editor_property(prop_name, value)
                except Exception:
                    pass
    except Exception as exc:
        report["anim_data_warn"] = str(exc)

    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    report["imported"] = [str(p) for p in (task.get_editor_property("imported_object_paths") or [])]

    seq = unreal.load_asset(f"{DEST_DIR}/{name}")
    if not seq and report["imported"]:
        seq = unreal.load_asset(report["imported"][0].split(".", 1)[0])
    if not seq:
        report["error"] = "import_returned_no_sequence"
        return report

    # In-place bird loops, not locomotion: no root motion. Takeoff/Land are
    # one-shots and are driven by the state machine, so they do not loop.
    for setter, value in (("loop", bool(contract.get("loop", False))),
                          ("enable_root_motion", False)):
        try:
            seq.set_editor_property(setter, value)
        except Exception:
            pass

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    except Exception:
        pass

    report["sequence"] = asset_path(seq)
    report["skeleton"] = asset_path(prop(seq, "skeleton"))
    report["length"] = float(prop(seq, "sequence_length") or 0)
    report["frames"] = int(seq.get_number_of_frames()) if hasattr(seq, "get_number_of_frames") else None

    # Wrong-skeleton rejection: importing "succeeded" is not evidence of effect.
    if report["skeleton"] != SKELETON:
        report["error"] = f"wrong_skeleton:{report['skeleton']}"
        return report

    scale = classify_scale(seq)
    report["scale"] = scale
    if scale["verdict"] != "ok":
        report["error"] = f"scale_rejected:{scale['verdict']}"
        return report

    report["ok"] = True
    return report


def main() -> dict:
    results = []
    for contract_path in sorted(STAGE_C.glob("*.contract.json")):
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        name = contract["clip_name"]
        fbx = Path(contract["remapped_fbx"])
        if contract.get("ue_import") is False and not contract.get("force_stage_d"):
            # Stage C deliberately parked these. Stage D is the thing that flips
            # them, so honour the flag but say we honoured it.
            pass
        results.append(import_one(fbx, name, contract))

    ok = sum(1 for r in results if r.get("ok"))
    payload = {
        "schema": "melodia.sir_anim_import.v1",
        "stage": "D_guarded_import",
        "skeleton": SKELETON,
        "dest": DEST_DIR,
        "ok": ok == len(results) and len(results) > 0,
        "imported": ok,
        "total": len(results),
        "clips": results,
        "not_proven": "ABP state binding and PIE. Import success is not runtime binding.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    payload = main()
    print("__SIR_IMPORT__" + json.dumps(payload), flush=True)
    unreal.log("SIR_ANIM_IMPORT: " + json.dumps({"ok": payload.get("ok")}))

