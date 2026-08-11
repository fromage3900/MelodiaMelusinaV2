"""Add the canonical Melusina RootX sprint mocap sample at speed 630."""
import json
from pathlib import Path
import unreal

BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
SPRINT = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Sprint_Mocap_RootX"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
SPEED = 630.0
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_sprint_wiring.json"


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def asset_path(obj):
    return obj.get_path_name().split(".")[0] if obj else ""

blend = unreal.load_asset(BLENDSPACE)
sprint = unreal.load_asset(SPRINT)
if not blend or not sprint:
    raise RuntimeError("Missing active blendspace or canonical sprint mocap")
if asset_path(prop(sprint, "skeleton")) != SKELETON:
    raise RuntimeError("Canonical sprint mocap is not on SK_Melusina_Skeleton")
if not bool(prop(sprint, "loop", False)):
    raise RuntimeError("Canonical sprint mocap is not configured to loop")

samples = list(prop(blend, "sample_data", []) or [])
# Keep all non-sprint authored points; replace any prior 630 point deterministically.
kept = []
for sample in samples:
    value = prop(sample, "sample_value")
    animation = prop(sample, "animation")
    if (value and abs(float(value.x) - SPEED) < 0.1) or "Sprint" in asset_path(animation):
        continue
    kept.append(sample)

new_sample = unreal.BlendSample()
new_sample.set_editor_property("animation", sprint)
new_sample.set_editor_property("sample_value", unreal.Vector(SPEED, 0.0, 0.0))
new_sample.set_editor_property("rate_scale", 1.0)
kept.append(new_sample)
blend.modify()
blend.set_editor_property("sample_data", kept)
if not unreal.EditorAssetLibrary.save_loaded_asset(blend, False):
    raise RuntimeError("Failed to save sprint-enabled locomotion blendspace")

verified = []
for sample in prop(blend, "sample_data", []) or []:
    animation = prop(sample, "animation")
    value = prop(sample, "sample_value")
    verified.append({"animation": asset_path(animation), "speed": float(value.x) if value else None})
matches = [row for row in verified if row["animation"] == SPRINT and row["speed"] is not None and abs(row["speed"] - SPEED) < 0.1]
if len(matches) != 1:
    raise RuntimeError(f"Expected exactly one sprint sample after save, found {len(matches)}")

report = {"blendspace": BLENDSPACE, "sprint": SPRINT, "speed": SPEED, "samples": verified, "ok": True}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_SPRINT_WIRED: " + json.dumps({"asset": SPRINT, "speed": SPEED, "sample_count": len(verified)}))
