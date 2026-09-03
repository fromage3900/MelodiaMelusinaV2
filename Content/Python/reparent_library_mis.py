"""Reparent Library MI_M_* to the Universal master and route prop textures.

The MagiciansLibrary prop masters (M_<Prop>) are procedural stubs (BaseTint +
TintStrength only) - their T_<Prop>_Base/AO/Normal textures are never sampled,
so every Library prop renders flat grey. Fix:
  1. Reparent MI_M_<Prop> from M_<Prop> to M_Master_Toon_Universal.
  2. Route T_<Prop>_Base -> Albedo, T_<Prop>_Normal -> NormalMap, T_<Prop>_AO -> ORM.
  3. Set TextureWeight=1.0 + LayerA_TextureWeight=1.0.
  4. Save + re-read.

Run in the UE editor (Monolith run_python): reparent_library_mis.main()
Writes: Saved/Audit/library_mi_reparent_routing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

LIB = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
UNIVERSAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "library_mi_reparent_routing.json"

MEL = unreal.MaterialEditingLibrary


def main():
    rows = []
    fixed = 0
    if not unreal.EditorAssetLibrary.does_directory_exist(LIB):
        return {"fixed": 0}
    universal = unreal.load_asset(UNIVERSAL)
    assets = unreal.EditorAssetLibrary.list_assets(LIB, recursive=True)
    prop_folders = set()
    for f in assets:
        parts = f.split("/")
        if len(parts) > len(LIB.split("/")):
            prop_folders.add("/".join(parts[:-1]))
    for folder in sorted(prop_folders):
        fa = unreal.EditorAssetLibrary.list_assets(folder, recursive=False)
        names = {p.rsplit("/", 1)[-1].split(".", 1)[0]: p for p in fa}
        mi_path = None
        prop_name = None
        for leaf, p in names.items():
            if leaf.startswith("MI_M_"):
                mi_path = p
                prop_name = leaf[len("MI_M_"):]
                break
        if mi_path is None:
            continue
        mi = unreal.load_asset(mi_path)
        if mi is None:
            continue
        # reparent
        mi.set_editor_property("parent", universal)
        params = set()
        for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names,
                   MEL.get_vector_parameter_names):
            try:
                for p in (fn(universal) or []):
                    params.add(str(p))
            except Exception:
                pass
        applied = []
        base = names.get(f"T_{prop_name}_Base") or names.get(f"T_{prop_name}_BaseColor") \
            or names.get(f"T_{prop_name}_Albedo")
        normal = names.get(f"T_{prop_name}_Normal") or names.get(f"T_{prop_name}_Normals")
        ao = names.get(f"T_{prop_name}_AO") or names.get(f"T_{prop_name}_AmbientOcclusion")
        if base and "Albedo" in params:
            t = unreal.load_asset(base)
            if t is not None:
                MEL.set_material_instance_texture_parameter_value(mi, "Albedo", t)
                applied.append("Albedo")
        if normal and "NormalMap" in params:
            t = unreal.load_asset(normal)
            if t is not None:
                MEL.set_material_instance_texture_parameter_value(mi, "NormalMap", t)
                applied.append("NormalMap")
        if ao and "ORM" in params:
            t = unreal.load_asset(ao)
            if t is not None:
                MEL.set_material_instance_texture_parameter_value(mi, "ORM", t)
                applied.append("ORM")
        if applied:
            for scalar in ("TextureWeight", "LayerA_TextureWeight"):
                if scalar in params:
                    MEL.set_material_instance_scalar_parameter_value(mi, scalar, 1.0)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        fixed += 1
        rows.append({"prop": prop_name, "path": mi_path, "reparented": True,
                     "applied": applied, "base": base, "normal": normal, "ao": ao})
    payload = {"generated": "2026-08-14", "summary": {"fixed": fixed, "props": len(rows)},
               "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[lib_reparent] fixed={fixed}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
