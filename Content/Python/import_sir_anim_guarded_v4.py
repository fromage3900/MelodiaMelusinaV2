# v4 (2026-10-08): ARP lane. Identical guards to v3; targets the NEW ARP skeleton
# created by the owner's v5_tailfix mesh drag (auto-discovered in the ARP folder),
# reads the v6 ARP clips. SAVE IS OFF per UE_IMPORT_HANDOFF.md section 2: assets
# are imported in-memory and the owner Ctrl+S saves. NOT YET RUN -- requires the
# mesh drag first (handoff section 1, owner-manual).
"""Stage D guarded import -- Sir Melodious ARP clips onto the new ARP skeleton.

WHY THIS FILE EXISTS

`AGENTS.md` forbids scripted skeletal MESH import outright: two automated FBX
imports crashed this editor (the brow-only file and the iris FBX), both with
StaticShutdownAfterError. That rule is absolute and this file does not touch
it: the mesh is dragged by the OWNER by hand (handoff section 1).

Importing an ANIMATION onto an EXISTING skeleton is the sanctioned operation --
the same guarded animation-only path five Rokoko takes proved
(`import_rokoko_mocap_batch.py`). This is that path, pointed at the ARP lane:

  * animation-only -- import_mesh=False, FBXIT_ANIMATION, no materials, no
    textures. Nothing new can be created except a UAnimSequence.
  * the skeleton is FORCED (discovered in the ARP folder), so the import
    cannot mint a competing skeleton.
  * convert_scene_unit=False and import_uniform_scale=1.0. The Stage C
    contract records the exact trap this avoids: a metre-scale source exported
    with global_scale=100 *and* FBX_SCALE_ALL *and* apply_unit_scale measured
    a 99.99x double-scale.
  * scale rejection on readback, in both directions, because a metre-scale
    leak and a double-scale leak look identical in a static import log.
  * wrong-skeleton rejection: ProcessEvent returning is not evidence.
  * save OFF -- task.save=False, no save_loaded_asset. In-memory until the
    owner saves (handoff section 2).

Run after the owner's mesh drag, via the same in-memory route v3 used. Do NOT
Python-load skill Blueprints.

Reads `exports/ue_arp/A_Sir_*_v6_ARP.fbx` (the feather-respaced lane; handoff
section 8: v6 = primary wing owner).
"""

import json
from pathlib import Path

import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "Saved" / "Audit" / "SirMelodious_FlightUnit_20261003" / "exports" / "ue_arp"
ARP_DIR = "/Game/Melodia/Characters/SirMelodious/ARP"
DEST_DIR = "/Game/Melodia/Characters/SirMelodious/ARP"
OUT = PROJECT / "Saved" / "Audit" / "SirMelodious_FlightUnit_20261003" / "sir_anim_import_report_v4.json"

CLIP_VERSION = "v6"  # handoff section 8: v6 = primary wing owner (v5 = fallback)
CLIP_NAMES = ("A_Sir_Fly_Loop", "A_Sir_Hover_Idle", "A_Sir_Glide", "A_Sir_Takeoff", "A_Sir_Land")
LOOPS = {
    "A_Sir_Fly_Loop": True,
    "A_Sir_Hover_Idle": True,
    "A_Sir_Glide": True,
    "A_Sir_Takeoff": False,
    "A_Sir_Land": False,
}

# Preferred probe bones for the scale guard; filtered against the skeleton's
# actual reference pose at run time, because the ARP bone list is only proven
# AFTER the owner's mesh drag.
PROBE_CANDIDATES = ("root.x", "spine_01.x", "foot.l", "thigh_stretch.l",
                    "cc_tie_01", "c_kilt_master_x")

# A translation magnitude outside this band means the scale leaked in one of the
# two documented directions: ~1e-2 cm is a metre-scale clip that was not
# converted, ~1e+2 cm and up is the 99.99x double-scale the Stage C contract found.
SCALE_ABS_MIN_CM = 0.01
SCALE_ABS_MAX_CM = 500.0


def asset_path(obj) -> str:
    return obj.get_path_name().split(".")[0] if obj else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def find_arp_skeleton() -> tuple:
    """Exactly one Skeleton under the ARP folder, or (None, error)."""
    if not unreal.EditorAssetLibrary.does_directory_exist(ARP_DIR):
        return None, "arp_folder_missing: drag SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx first (handoff section 1)"
    found = []
    for path in unreal.EditorAssetLibrary.list_assets(ARP_DIR, recursive=True, include_folder=False):
        try:
            obj = unreal.load_asset(path)
        except Exception:
            continue
        if isinstance(obj, unreal.Skeleton):
            found.append((asset_path(obj), obj))
    if not found:
        return None, "arp_skeleton_not_found: the mesh drag is the step that creates it (handoff section 1)"
    if len(found) > 1:
        crest = [f for f in found if "CrestTie" in f[0]]
        if len(crest) == 1:
            return crest[0][0], None
        return None, "multiple_skeletons_in_arp:" + ",".join(f[0] for f in found)
    return found[0][0], None


def probe_bones(skeleton) -> list:
    try:
        names = [str(n) for n in skeleton.get_reference_pose().get_bone_names()]
    except Exception:
        names = []
    picked = [b for b in PROBE_CANDIDATES if b in names]
    if not picked:
        picked = names[:4]
    return picked


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


def classify_scale(seq, bones: list) -> dict:
    """Reject a metre-scale leak and a double-scale leak. In-place loops may sit
    at zero, so zero is legal here (unlike the Melusina locomotion probe)."""
    worst = None
    checked = 0
    for bone in bones:
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


def import_one(fbx: Path, name: str, skeleton_path: str, skeleton, bones: list) -> dict:
    report = {"clip": name, "fbx": str(fbx), "ok": False, "saved": False}

    if not fbx.is_file():
        report["error"] = "fbx_missing"
        return report

    unreal.EditorAssetLibrary.make_directory(DEST_DIR)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx))
    task.set_editor_property("destination_path", DEST_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    # In-memory only: the owner saves (handoff section 2).
    task.set_editor_property("save", False)
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
    # one-shots driven by the state machine.
    for setter, value in (("loop", LOOPS.get(name, False)),
                          ("enable_root_motion", False),
                          ("force_root_lock", False)):
        try:
            seq.set_editor_property(setter, value)
        except Exception:
            pass

    report["sequence"] = asset_path(seq)
    report["skeleton"] = asset_path(prop(seq, "skeleton"))
    report["length"] = float(prop(seq, "sequence_length") or 0)
    report["frames"] = int(seq.get_number_of_frames()) if hasattr(seq, "get_number_of_frames") else None

    # Wrong-skeleton rejection: importing "succeeded" is not evidence of effect.
    if report["skeleton"] != skeleton_path:
        report["error"] = f"wrong_skeleton:{report['skeleton']}"
        return report

    scale = classify_scale(seq, bones)
    report["scale"] = scale
    if scale["verdict"] != "ok":
        report["error"] = f"scale_rejected:{scale['verdict']}"
        return report

    report["ok"] = True
    return report


def main() -> dict:
    skeleton_path, err = find_arp_skeleton()
    payload = {
        "schema": "melodia.sir_anim_import.v4",
        "stage": "D_guarded_import_arp",
        "skeleton": skeleton_path,
        "dest": DEST_DIR,
        "clip_version": CLIP_VERSION,
        "ok": False,
        "imported": 0,
        "total": 0,
        "clips": [],
        "saved": False,
        "not_proven": ("ABP state binding, PIE, Downstroke sync markers, Wingbeat curve adds. "
                       "Import success is not runtime binding. Assets are in-memory until the owner Ctrl+S."),
    }
    if err or not skeleton_path:
        payload["error"] = err or "arp_skeleton_not_found"
        _write(payload)
        return payload

    skeleton = unreal.load_asset(skeleton_path)
    bones = probe_bones(skeleton)
    payload["probe_bones"] = bones

    results = []
    for name in CLIP_NAMES:
        fbx = SOURCE / f"{name}_{CLIP_VERSION}_ARP.fbx"
        results.append(import_one(fbx, name, skeleton_path, skeleton, bones))

    ok = sum(1 for r in results if r.get("ok"))
    payload["clips"] = results
    payload["imported"] = ok
    payload["total"] = len(results)
    payload["ok"] = ok == len(results) and len(results) > 0
    _write(payload)
    return payload


def _write(payload: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    payload = main()
    print("__SIR_IMPORT_V4__" + json.dumps(payload), flush=True)
    unreal.log("SIR_ANIM_IMPORT_V4: " + json.dumps({"ok": payload.get("ok"), "imported": payload.get("imported")}))
