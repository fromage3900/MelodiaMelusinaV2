"""Survey EnvSandbox material instances for TextureWeight and texture routing.

For each MI under /Game/EnvSandbox/Materials/Instances (recursive):
  - texture_weight_value : overridden scalar value of TextureWeight (or inherited/None)
  - layer_a_weight / layer_b_weight / layer_c_weight
  - texture params overridden vs inherited, and how many of the core slots
    (Albedo, NormalMap, ORM, RoughnessMap, MetallicMap, HeightMap, EmissiveMap)
    are actually overridden with a real texture
  - parent

Writes Saved/Audit/mi_texture_weight_survey.json + prints a summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = "/Game/EnvSandbox/Materials/Instances"
CORE_SLOTS = ["Albedo", "NormalMap", "ORM", "RoughnessMap", "MetallicMap", "HeightMap", "EmissiveMap", "LayerB_Albedo", "LayerB_NormalMap", "LayerB_ORM", "LayerC_Albedo", "LayerC_NormalMap", "LayerC_ORM"]
WEIGHT_PARAMS = ["TextureWeight", "LayerA_TextureWeight", "LayerB_TextureWeight", "LayerC_TextureWeight"]


def main() -> int:
    lib = unreal.MaterialEditingLibrary
    assets = unreal.EditorAssetLibrary.list_assets(INSTANCE_ROOT, recursive=True, include_folder=False)
    rows = []
    for path in assets:
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        parent = None
        try:
            parent = inst.get_editor_property("parent")
        except Exception:
            pass
        weights = {}
        for p in WEIGHT_PARAMS:
            try:
                w = lib.get_scalar_parameter_default_value(inst, p)
                weights[p] = w
            except Exception:
                weights[p] = None
        tex = {}
        for p in CORE_SLOTS:
            try:
                t = lib.get_texture_parameter_value(inst, p)
                tex[p] = str(t.get_path_name()) if t else None
            except Exception:
                tex[p] = None
        overridden = {p: t for p, t in tex.items() if t}
        rows.append({
            "path": path,
            "parent": str(parent) if parent else None,
            "weights": weights,
            "textures_overridden": overridden,
            "n_textures": len(overridden),
        })

    low_weight = [r for r in rows if (r["weights"].get("TextureWeight") or 1.0) < 0.5]
    no_textures = [r for r in rows if r["n_textures"] == 0]
    partial = [r for r in rows if 0 < r["n_textures"] < 4]

    report = {
        "generated": "2026-08-13",
        "root": INSTANCE_ROOT,
        "instances": len(rows),
        "low_texture_weight": len(low_weight),
        "no_texture_overrides": len(no_textures),
        "partial_textures_lt4": len(partial),
        "rows": rows,
    }
    out = ROOT / "Saved" / "Audit" / "mi_texture_weight_survey.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"instances: {len(rows)}")
    print(f"low TextureWeight (<0.5): {len(low_weight)}")
    print(f"zero texture overrides: {len(no_textures)}")
    print(f"1-3 texture overrides: {len(partial)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
