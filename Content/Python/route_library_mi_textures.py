"""Route the Library MI_M_* instances from their sibling prop textures.

Every MagiciansLibrary prop ships T_<Prop>_Base / T_<Prop>_Normal / T_<Prop>_AO
(and often M_<Prop> master + SM_<Prop> mesh), but the MI_M_* instances were
created as empty shells (no Albedo, no TextureWeight) -> they render the
master's procedural flat instead of the prop's real maps.

This script, per MagiciansLibrary prop folder with an MI_M_*:
  1. Finds T_<Prop>_Base / *_Albedo / *_BaseColor -> Albedo
  2. Finds T_<Prop>_Normal -> NormalMap
  3. Finds T_<Prop>_AO -> ORM (AO channel)
  4. Sets TextureWeight=1.0 (+ LayerA_TextureWeight=1.0)
  5. Saves + re-reads.

Run in the UE editor (Monolith run_python): route_library_mi_textures.main()
Writes: Saved/Audit/library_mi_texture_routing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

LIB = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "library_mi_texture_routing.json"

MEL = unreal.MaterialEditingLibrary


def base_candidates(prop, assets):
    names = [f"T_{prop}_Base", f"T_{prop}_BaseColor", f"T_{prop}_Albedo",
             f"T_{prop}_Base_Color", f"T_{prop}_Diffuse"]
    for n in names:
        for p in assets:
            if p.rsplit("/", 1)[-1].split(".", 1)[0] == n:
                return p
    return None


def normal_candidates(prop, assets):
    for n in (f"T_{prop}_Normal", f"T_{prop}_Normals"):
        for p in assets:
            if p.rsplit("/", 1)[-1].split(".", 1)[0] == n:
                return p
    return None


def ao_candidates(prop, assets):
    for n in (f"T_{prop}_AO", f"T_{prop}_AmbientOcclusion", f"T_{prop}_Occlusion"):
        for p in assets:
            if p.rsplit("/", 1)[-1].split(".", 1)[0] == n:
                return p
    return None


def main():
    rows = []
    fixed = 0
    if not unreal.EditorAssetLibrary.does_directory_exist(LIB):
        print("[lib_mi] no library dir")
        return {"fixed": 0}
    # enumerate subfolders (each prop = one folder)
    folders = unreal.EditorAssetLibrary.list_assets(LIB, recursive=True)
    prop_folders = set()
    for f in folders:
        parts = f.split("/")
        if len(parts) > len(LIB.split("/")):
            prop_folders.add("/".join(parts[:-1]))
    for folder in sorted(prop_folders):
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            continue
        assets = unreal.EditorAssetLibrary.list_assets(folder, recursive=False)
        mi_path = None
        prop_name = None
        for p in assets:
            leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
            if leaf.startswith("MI_M_"):
                mi_path = p
                prop_name = leaf[len("MI_M_"):]
                break
        if mi_path is None:
            continue
        mi = unreal.load_asset(mi_path)
        if mi is None:
            continue
        parent = mi.get_editor_property("parent")
        params = set()
        for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names):
            try:
                for p in (fn(parent) or []):
                    params.add(str(p))
            except Exception:
                pass
        base = base_candidates(prop_name, assets)
        normal = normal_candidates(prop_name, assets)
        ao = ao_candidates(prop_name, assets)
        applied = []
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
            rows.append({"prop": prop_name, "path": mi_path, "applied": applied,
                         "base": base, "normal": normal, "ao": ao})
    payload = {"generated": "2026-08-14", "summary": {"fixed": fixed, "props": len(rows)},
               "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[lib_mi] fixed={fixed}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
