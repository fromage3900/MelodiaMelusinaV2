"""Survey EnvSandbox material instances for TextureWeight + texture routing (v2).

Uses the correct API:
  - get_material_default_scalar_parameter_value / get_material_instance_scalar_parameter_value
  - is_material_instance_parameter_overridden
  - get_material_instance_texture_parameter_value

Reports per instance: effective TextureWeight (inherited 0.0 from master counts as
"zero"), whether overridden, and which core texture slots carry a real texture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = "/Game/EnvSandbox/Materials/Instances"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
CORE_SLOTS = ["Albedo", "NormalMap", "ORM", "RoughnessMap", "MetallicMap", "HeightMap", "EmissiveMap",
              "LayerB_Albedo", "LayerB_NormalMap", "LayerB_ORM",
              "LayerC_Albedo", "LayerC_NormalMap", "LayerC_ORM"]
WEIGHT_PARAMS = ["TextureWeight", "LayerA_TextureWeight", "LayerB_TextureWeight", "LayerC_TextureWeight"]


def main() -> int:
    lib = unreal.MaterialEditingLibrary
    master_obj = unreal.load_asset(MASTER)
    master_default_tw = lib.get_material_default_scalar_parameter_value(master_obj, "TextureWeight")
    assets = unreal.EditorAssetLibrary.list_assets(INSTANCE_ROOT, recursive=True, include_folder=False)
    rows = []
    for path in assets:
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        parent = None
        try:
            parent = str(inst.get_editor_property("parent"))
        except Exception:
            pass
        weights = {}
        for p in WEIGHT_PARAMS:
            try:
                over = lib.is_material_instance_parameter_overridden(inst, p)
                val = lib.get_material_instance_scalar_parameter_value(inst, p)
                weights[p] = {"overridden": over, "value": val}
            except Exception:
                weights[p] = {"overridden": False, "value": None}
        tex = {}
        for p in CORE_SLOTS:
            try:
                over = lib.is_material_instance_parameter_overridden(inst, p)
                t = lib.get_material_instance_texture_parameter_value(inst, p)
                tex[p] = {"overridden": over, "value": str(t.get_path_name()) if t else None}
            except Exception:
                tex[p] = {"overridden": False, "value": None}
        eff_tw = weights["TextureWeight"]["value"] if weights["TextureWeight"]["value"] is not None else master_default_tw
        n_tex = sum(1 for v in tex.values() if v["value"])
        n_tex_overridden = sum(1 for v in tex.values() if v["overridden"] and v["value"])
        rows.append({
            "path": path,
            "parent": parent,
            "effective_texture_weight": eff_tw,
            "texture_weight_overridden": weights["TextureWeight"]["overridden"],
            "weights": weights,
            "textures": tex,
            "n_textures_effective": n_tex,
            "n_textures_overridden": n_tex_overridden,
        })

    zero_tw = [r for r in rows if (r["effective_texture_weight"] or 0.0) == 0.0]
    no_tex = [r for r in rows if r["n_textures_effective"] == 0]
    no_tex_override = [r for r in rows if r["n_textures_overridden"] == 0]

    report = {
        "generated": "2026-08-13",
        "master_default_texture_weight": master_default_tw,
        "instances": len(rows),
        "zero_effective_texture_weight": len(zero_tw),
        "no_effective_textures": len(no_tex),
        "no_overridden_textures": len(no_tex_override),
        "rows": rows,
    }
    out = ROOT / "Saved" / "Audit" / "mi_texture_weight_survey_v2.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"master TextureWeight default: {master_default_tw}")
    print(f"instances: {len(rows)}")
    print(f"zero effective TextureWeight: {len(zero_tw)}")
    print(f"zero effective textures: {len(no_tex)}")
    print(f"zero overridden textures: {len(no_tex_override)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
