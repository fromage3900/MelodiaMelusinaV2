"""Read-only sprint candidate audit for Melusina's active locomotion blendspace."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved" / "Audit" / "melusina_sprint_candidates.json"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
CANDIDATES = [
    "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Sprint_Mocap_RootX",
    "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Sprint",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint_Loop",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint",
]


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def path(obj):
    return obj.get_path_name().split(".")[0] if obj else ""

rows = []
for candidate in CANDIDATES:
    anim = unreal.load_asset(candidate)
    model = prop(anim, "data_model_interface") if anim else None
    rows.append({
        "asset": candidate,
        "loads": bool(anim),
        "skeleton": path(prop(anim, "skeleton")) if anim else "",
        "skeleton_compatible": bool(anim) and path(prop(anim, "skeleton")) == SKELETON,
        "loop": bool(prop(anim, "loop", False)) if anim else False,
        "duration": float(prop(anim, "sequence_length", 0.0) or 0.0) if anim else 0.0,
        "deform_track_count": int(model.get_num_bone_tracks()) if model and hasattr(model, "get_num_bone_tracks") else 0,
        "enable_root_motion": bool(prop(anim, "enable_root_motion", False)) if anim else False,
        "root_motion_root_lock": str(prop(anim, "root_motion_root_lock", "")) if anim else "",
    })

# Prefer the canonical RootX locomotion derivative used alongside Walk/Run RootX.
selected = next((row for row in rows if row["asset"].endswith("A_Melusina_Sprint_Mocap_RootX") and row["skeleton_compatible"] and row["loop"] and row["deform_track_count"] > 0), None)
report = {"required_skeleton": SKELETON, "candidates": rows, "selected": selected, "ok": selected is not None}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_SPRINT_CANDIDATE_AUDIT: " + json.dumps({"ok": report["ok"], "selected": selected["asset"] if selected else ""}))
