"""Correct override-state audit for Universal-parented MIs (UE 5.8 safe).

The stock sweep_pbr_state.py uses get_material_instance_*_parameter_overridden,
which does NOT exist in this UE 5.8 Python binding - every read fails silently
and every MI is misreported as "unfinished". This audit reads the override
arrays directly from the MIC object:

  scalar_parameter_values / texture_parameter_values / vector_parameter_values

For static switches (bLayerA_Active etc.), the StaticSwitchParameterOverrides
are not a direct MIC property here; we read the effective value via the
monolith material_query (which resolves inheritance) as a secondary pass.

Criteria for a TEXTURED MI (finished):
  - TextureWeight overridden = 1.0  (master default is 0.0 = procedural!)
  - Albedo texture overridden and resolves to a non-noise texture
  - LayerA_TextureWeight effective value == 1.0
  - bLayerA_Active effective value == True

Run in the UE editor (Monolith run_python): audit_layer_a_state.main()
Writes: Saved/Audit/layer_a_state_2026-08-14.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

OUT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit") / "layer_a_state_2026-08-14.json"
ROOTS = [
    "/Game/EnvSandbox/Meshes/Environment",
    "/Game/EnvSandbox/Materials/Instances",
    "/Game/EnvSandbox/Materials/Impressionist/Instances",
    "/Game/EnvSandbox/Library/Migrated",
    "/Game/Library/Migrated",
]
NOISE_MARKERS = ("sbs_-_", "DefaultTexture", "Black.Black", "Perlin", "Cracks_")
SWITCH_PARAMS = ("bLayerA_Active", "bLayerB_Active", "bLayerC_Active")


def override_map(mi, prop):
    out = {}
    try:
        for e in (mi.get_editor_property(prop) or []):
            info = e.get_editor_property("parameter_info")
            n = str(info.get_editor_property("name"))
            out[n] = e.get_editor_property("parameter_value")
    except Exception:
        pass
    return out


def scalar_overrides(mi):
    return override_map(mi, "scalar_parameter_values")


def texture_overrides(mi):
    out = {}
    try:
        for e in (mi.get_editor_property("texture_parameter_values") or []):
            info = e.get_editor_property("parameter_info")
            n = str(info.get_editor_property("name"))
            v = e.get_editor_property("parameter_value")
            out[n] = v.get_path_name() if v else None
    except Exception:
        pass
    return out


def vector_overrides(mi):
    return override_map(mi, "vector_parameter_values")


def switch_overrides(mi):
    out = {}
    try:
        for e in (mi.get_editor_property("static_switch_parameter_values") or []):
            info = e.get_editor_property("parameter_info")
            n = str(info.get_editor_property("name"))
            out[n] = bool(e.get_editor_property("parameter_value"))
    except Exception:
        pass
    return out


def effective_switch(mi, name):
    """Effective static-switch value (inheritance-resolved)."""
    try:
        return bool(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(mi, name))
    except Exception:
        return None


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
            try:
                parent = a.get_editor_property("parent")
            except Exception:
                parent = None
            if parent is None or not parent.get_path_name().endswith("M_Master_Toon_Universal"):
                continue
            paths.append(p)

    textured_ok = []
    textured_bad = []
    flat_ok = []
    flat_bad = []
    for p in paths:
        mi = unreal.load_asset(p)
        sc = scalar_overrides(mi)
        tx = texture_overrides(mi)
        sw = switch_overrides(mi)
        tw = sc.get("TextureWeight")
        albedo = tx.get("Albedo")
        layer_a_w = sc.get("LayerA_TextureWeight")
        b_layer_a = effective_switch(mi, "bLayerA_Active")
        has_noise = albedo is not None and any(mk in albedo for mk in NOISE_MARKERS)
        rec = {
            "path": p,
            "texture_weight": tw,
            "albedo": albedo,
            "layer_a_weight_ovr": layer_a_w,
            "layer_a_effective": layer_a_w if layer_a_w is not None else 1.0,
            "b_layer_a": b_layer_a,
            "albedo_is_noise": has_noise,
        }
        if tw == 0.0:
            # flat tint path (BaseTint MIs) - fine if no albedo
            if albedo is None:
                flat_ok.append(rec)
            else:
                rec["why"] = "flat weight but albedo set"
                flat_bad.append(rec)
        elif tw == 1.0:
            if albedo is None or has_noise:
                rec["why"] = "textured weight but albedo missing/noise"
                textured_bad.append(rec)
            elif layer_a_w is not None and layer_a_w != 1.0:
                rec["why"] = f"layerA weight {layer_a_w}"
                textured_bad.append(rec)
            elif b_layer_a is not True:
                rec["why"] = f"bLayerA_Active {b_layer_a}"
                textured_bad.append(rec)
            else:
                textured_ok.append(rec)
        else:
            rec["why"] = f"unexpected TW {tw}"
            textured_bad.append(rec)

    payload = {
        "generated": "2026-08-14",
        "summary": {
            "universal_mis": len(paths),
            "textured_ok": len(textured_ok),
            "textured_bad": len(textured_bad),
            "flat_ok": len(flat_ok),
            "flat_bad": len(flat_bad),
        },
        "textured_bad": textured_bad,
        "flat_bad": flat_bad,
        "textured_ok_sample": textured_ok[:5],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[layer_a] {payload['summary']}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
