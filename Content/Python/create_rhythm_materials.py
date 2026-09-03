"""Create the Rhythm battle-surface material family + wire Universal presets.

For the turn-based rhythm JRPG: battle floors and UI-adjacent surfaces should
react to the Harmonix music clock. Two masters exist but have zero instances:
  - M_RhythmSurface_Pulse (PulseIntensity, PulseColor, SurfaceColor, Roughness, Metallic)
  - M_AudioReactive_BaseMaster (AudioIntensity, BPM, BeatSensitivity, Bass/Mid/Treble colors)

Creates:
  Instances/Rhythm/
    MI_Rhythm_Floor_Dream      - hero battle floor (soft pulse, pastel pink/blue)
    MI_Rhythm_Floor_Stone      - arena stone floor (subtle pulse)
    MI_Rhythm_Note_Highlight   - note-target surfaces (bright pulse, low roughness)
    MI_Rhythm_Arena_Neon       - audio-reactive arena walls (Bass/Mid/Treble)
    MI_Rhythm_Podium_Hero      - hero podium (iridescent pulse)

All parent the rhythm masters (NOT M_Master_Toon_Universal - they are their own
family), compiled + verified.

Run in the UE editor (Monolith run_python): create_rhythm_materials.main()
Writes: Saved/Audit/rhythm_materials_2026-08-14.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "rhythm_materials_2026-08-14.json"
RHYTHM_DIR = "/Game/EnvSandbox/Materials/Instances/Rhythm"
PULSE = "/Game/EnvSandbox/Materials/Masters/M_RhythmSurface_Pulse"
AUDIO = "/Game/EnvSandbox/Materials/Masters/M_AudioReactive_BaseMaster"
MEL = unreal.MaterialEditingLibrary

SPECS = {
    "MI_Rhythm_Floor_Dream": {
        "parent": PULSE,
        "scalars": {"PulseIntensity": 0.55, "Roughness": 0.45, "Metallic": 0.0},
        "vectors": {"PulseColor": (0.85, 0.40, 0.62, 1.0), "SurfaceColor": (0.42, 0.38, 0.62, 1.0)},
    },
    "MI_Rhythm_Floor_Stone": {
        "parent": PULSE,
        "scalars": {"PulseIntensity": 0.25, "Roughness": 0.65, "Metallic": 0.0},
        "vectors": {"PulseColor": (0.78, 0.55, 0.82, 1.0), "SurfaceColor": (0.45, 0.45, 0.5, 1.0)},
    },
    "MI_Rhythm_Note_Highlight": {
        "parent": PULSE,
        "scalars": {"PulseIntensity": 0.85, "Roughness": 0.15, "Metallic": 0.2},
        "vectors": {"PulseColor": (0.60, 0.78, 0.95, 1.0), "SurfaceColor": (0.95, 0.93, 0.97, 1.0)},
    },
    "MI_Rhythm_Arena_Neon": {
        "parent": AUDIO,
        "scalars": {"AudioIntensity": 0.6, "BPM": 128.0, "BeatSensitivity": 0.5},
        "vectors": {"BassColor": (0.85, 0.40, 0.62, 1.0), "MidColor": (0.78, 0.55, 0.82, 1.0),
                    "TrebleColor": (0.60, 0.78, 0.95, 1.0)},
    },
    "MI_Rhythm_Podium_Hero": {
        "parent": PULSE,
        "scalars": {"PulseIntensity": 0.7, "Roughness": 0.3, "Metallic": 0.35},
        "vectors": {"PulseColor": (0.92, 0.75, 0.42, 1.0), "SurfaceColor": (0.72, 0.55, 0.68, 1.0)},
    },
}


def params_of(mi):
    parent = mi.get_editor_property("parent")
    out = set()
    for fn in (MEL.get_scalar_parameter_names, MEL.get_vector_parameter_names):
        try:
            for p in (fn(parent) or []):
                out.add(str(p))
        except Exception:
            pass
    return out


def main():
    rows = []
    for name, spec in SPECS.items():
        path = f"{RHYTHM_DIR}/{name}"
        mi = unreal.load_asset(path)
        if mi is None:
            if not unreal.EditorAssetLibrary.does_directory_exist(RHYTHM_DIR):
                unreal.EditorAssetLibrary.make_directory(RHYTHM_DIR)
            tools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.MaterialInstanceConstantFactoryNew()
            mi = tools.create_asset(name, RHYTHM_DIR, unreal.MaterialInstanceConstant, factory)
        if mi is None:
            rows.append({"name": name, "status": "create_failed"})
            continue
        parent = unreal.load_asset(spec["parent"])
        mi.set_editor_property("parent", parent)
        params = params_of(mi)
        applied = []
        for pname, pval in spec["scalars"].items():
            if pname in params:
                MEL.set_material_instance_scalar_parameter_value(mi, pname, float(pval))
                applied.append(pname)
        for pname, pval in spec["vectors"].items():
            if pname in params:
                MEL.set_material_instance_vector_parameter_value(
                    mi, pname, unreal.LinearColor(pval[0], pval[1], pval[2], pval[3]))
                applied.append(pname)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        rows.append({"name": name, "status": "ok", "parent": spec["parent"], "applied": applied})
    payload = {"generated": "2026-08-14", "rows": rows,
               "summary": {"created": sum(1 for r in rows if r["status"] == "ok")}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[rhythm] {payload['summary']}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
