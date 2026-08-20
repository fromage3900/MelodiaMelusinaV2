"""Create showcase Nikki instances that prove the new feature gates.

Each instance parents M_Master_Nikki and flips ONE new feature gate ON with
tasteful values (the kawaii baseline Pastel+Twinkle stays on). These are the
proof + portfolio-ready presets for the expanded Nikki family.

Run in the UE editor (Monolith run_python): create_nikki_feature_shows.main()
Writes: Saved/Audit/nikki_feature_shows_2026-08-14.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "nikki_feature_shows_2026-08-14.json"
NIKKI = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki"
SHOW_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
MEL = unreal.MaterialEditingLibrary

SPECS = {
    "MI_Nikki_Show_RibbonTrim": {
        "switches": {"bNikkiSDFRibbon_Active": True},
        "scalars": {"NikkiSDFRibbon_Scale": 3.5, "NikkiSDFRibbon_Strength": 0.45,
                    "NikkiSDFRibbon_EdgeStrength": 0.6, "NikkiSDFRibbon_EdgeFalloff": 4.0},
        "vectors": {"NikkiSDFRibbon_Color": (0.98, 0.88, 0.92, 1.0)},
    },
    "MI_Nikki_Show_PearlSheen": {
        "switches": {"bNikkiPearlSheen_Active": True},
        "scalars": {"NikkiPearl_Frequency": 2.2, "NikkiPearl_SecondFrequency": 1.5,
                    "NikkiPearl_Strength": 0.6},
        "vectors": {"NikkiPearl_Tint": (1.0, 0.92, 0.96, 1.0)},
    },
    "MI_Nikki_Show_Watercolor": {
        "switches": {"bNikkiDreamWatercolor_Active": True},
        "scalars": {"NikkiWatercolor_Bleed": 0.7, "NikkiWatercolor_Jitter": 0.2,
                    "NikkiWatercolor_Strength": 0.5},
        "vectors": {"NikkiWatercolor_BleedColor": (0.78, 0.6, 0.88, 1.0)},
    },
    "MI_Nikki_Show_GlitterHalo": {
        "switches": {"bNikkiGlitterHalo_Active": True},
        "scalars": {"NikkiGlitterHalo_Scale": 28.0, "NikkiGlitterHalo_Amount": 0.18,
                    "NikkiGlitterHalo_Intensity": 0.6, "NikkiGlitterHalo_HaloStrength": 0.4,
                    "NikkiGlitterHalo_HaloPower": 5.0, "NikkiGlitterHalo_TwinkleSpeed": 1.4},
        "vectors": {"NikkiGlitterHalo_Color": (1.0, 0.96, 0.88, 1.0)},
    },
    "MI_Nikki_Show_StickerEdge": {
        "switches": {"bNikkiStickerEdge_Active": True},
        "scalars": {"NikkiStickerEdge_Width": 0.7, "NikkiStickerEdge_Bands": 4.0,
                    "NikkiStickerEdge_Softness": 0.7, "NikkiStickerEdge_Strength": 0.65},
        "vectors": {"NikkiStickerEdge_Color": (0.99, 0.9, 0.95, 1.0)},
    },
    "MI_Nikki_Show_PetalShadow": {
        "switches": {"bNikkiPetalShadow_Active": True},
        "scalars": {"NikkiPetal_Scale": 7.0, "NikkiPetal_Radius": 0.2, "NikkiPetal_Softness": 7.0,
                    "NikkiPetal_Strength": 0.5, "NikkiPetal_BloomSpeed": 1.8},
        "vectors": {"NikkiPetal_Tint": (0.99, 0.87, 0.92, 1.0)},
    },
    "MI_Nikki_Show_SquishDoll": {
        "switches": {"bKawaiiSquish_Active": True, "bNikkiSquishWPO_Active": True},
        "scalars": {"SquishAmount": 0.4, "NikkiSquish_Amount": 0.35, "NikkiSquish_Speed": 1.3},
        "vectors": {"NikkiSquish_Direction": (1.3, 2.1, 0.7, 0.0)},
    },
}


def main():
    rows = []
    if not unreal.EditorAssetLibrary.does_directory_exist(SHOW_DIR):
        unreal.EditorAssetLibrary.make_directory(SHOW_DIR)
    parent = unreal.load_asset(NIKKI)
    parent_params = set()
    for fn in (MEL.get_scalar_parameter_names, MEL.get_vector_parameter_names,
               MEL.get_static_switch_parameter_names):
        try:
            for p in (fn(parent) or []):
                parent_params.add(str(p))
        except Exception:
            pass
    for name, spec in SPECS.items():
        path = f"{SHOW_DIR}/{name}"
        mi = unreal.load_asset(path)
        if mi is None:
            tools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.MaterialInstanceConstantFactoryNew()
            mi = tools.create_asset(name, SHOW_DIR, unreal.MaterialInstanceConstant, factory)
        if mi is None:
            rows.append({"name": name, "status": "create_failed"})
            continue
        mi.set_editor_property("parent", parent)
        applied = []
        for pname, pval in spec.get("switches", {}).items():
            if pname in parent_params:
                MEL.set_material_instance_static_switch_parameter_value(mi, pname, bool(pval))
                applied.append(pname)
        for pname, pval in spec.get("scalars", {}).items():
            if pname in parent_params:
                MEL.set_material_instance_scalar_parameter_value(mi, pname, float(pval))
                applied.append(pname)
        for pname, pval in spec.get("vectors", {}).items():
            if pname in parent_params:
                MEL.set_material_instance_vector_parameter_value(
                    mi, pname, unreal.LinearColor(pval[0], pval[1], pval[2], 1.0))
                applied.append(pname)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        rows.append({"name": name, "status": "ok", "applied": applied})
    payload = {"generated": "2026-08-14", "rows": rows,
               "summary": {"created": sum(1 for r in rows if r["status"] == "ok")}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[nikki_shows] {payload['summary']}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
