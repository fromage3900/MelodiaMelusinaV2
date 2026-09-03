"""Owner-directed pink/blue ShadowDream ramp across ALL EnvSandbox instances.

The 08-13 policy sweep applied a lavender dream ramp to ~400 instances. The
owner now directs the pink/blue ramp (pink shadows -> lavender mid -> sky blue
high) for ALL materials. This pass updates the dream/ramp vector+scalar
parameters on every MI under /Game/EnvSandbox/Materials + /Game/EnvSandbox/Meshes
regardless of prior override state (the prior values were agent-applied, not
owner-authored), chunked to avoid the D3D12 descriptor crash.

Run in the UE editor (Monolith run_python): apply_pinkblue_dream.py
Writes: Saved/Audit/pinkblue_dream_apply.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "pinkblue_dream_apply.json"
ROOTS = [
    "/Game/EnvSandbox/Materials",
    "/Game/EnvSandbox/Meshes/Environment/AvatarGarden/Materials",
    "/Game/EnvSandbox/Meshes/Environment/RetroFantasyKit/Materials",
    "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors",
    "/Game/EnvSandbox/Materials/Instances/Environment/Cathedral",
    "/Game/EnvSandbox/Materials/Instances/Environment/RetroTextures",
    "/Game/EnvSandbox/Materials/Instances/Environment/PatternsExtra",
]
MEL = unreal.MaterialEditingLibrary

PINK = unreal.LinearColor(0.85, 0.40, 0.62, 1.0)
LAV = unreal.LinearColor(0.78, 0.55, 0.82, 1.0)
BLUE = unreal.LinearColor(0.60, 0.78, 0.95, 1.0)
SD_TINT = unreal.LinearColor(0.82, 0.45, 0.68, 1.0)

VECTOR_MAP = {
    "ShadowDreamTint": SD_TINT,
    "RampLow": PINK,
    "RampMid": LAV,
    "RampHigh": BLUE,
    "ShadowRampLow": PINK,
    "ShadowRampMid": LAV,
    "ShadowRampHigh": BLUE,
}
SCALAR_MAP = {
    "ShadowDreamStrength": 0.3,
    "ShadowSoftness": 1.2,
    "RampStrength": 0.28,
    "RampPosMid": 0.5,
}


def main():
    seen = set()
    paths = []
    for root in ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            if p in seen:
                continue
            seen.add(p)
            a = unreal.load_asset(p)
            if a is None or a.get_class().get_name() != "MaterialInstanceConstant":
                continue
            paths.append(p)

    results = []
    n_inst = 0
    n_param = 0
    chunk = []
    for i, path in enumerate(paths):
        mi = unreal.load_asset(path)
        if mi is None:
            continue
        parent = mi.get_editor_property("parent")
        if parent is None:
            continue
        pn = set()
        for p in (MEL.get_vector_parameter_names(parent) or []):
            pn.add(str(p))
        for p in (MEL.get_scalar_parameter_names(parent) or []):
            pn.add(str(p))
        applied = []
        for name, color in VECTOR_MAP.items():
            if name in pn:
                try:
                    MEL.set_material_instance_vector_parameter_value(mi, name, color)
                    applied.append(name)
                except Exception:
                    pass
        for name, val in SCALAR_MAP.items():
            if name in pn:
                try:
                    MEL.set_material_instance_scalar_parameter_value(mi, name, val)
                    applied.append(name)
                except Exception:
                    pass
        if applied:
            n_inst += 1
            n_param += len(applied)
            results.append({"path": path, "applied": applied})
            chunk.append(path)
            # save in batches of 60 to keep the editor stable
            if len(chunk) >= 60:
                for c in chunk:
                    try:
                        unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(c))
                    except Exception:
                        pass
                chunk = []
                time.sleep(0.5)
    for c in chunk:
        try:
            unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(c))
        except Exception:
            pass

    payload = {
        "generated": "2026-08-14",
        "summary": {"instances": n_inst, "params": n_param, "scanned": len(paths)},
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[pinkblue] instances={n_inst} params={n_param} scanned={len(paths)}")
    return payload


if __name__ == "__main__":
    main()
