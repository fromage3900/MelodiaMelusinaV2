"""Route RetroFantasyKit pack textures onto the 105 imported retro meshes.

Each retro GLB material references one of 10 shared pack textures. The mesh set
comes from Saved/Audit/kenney_new_import.json (the import manifest - exact list,
no name heuristics).

This script:
  1. Reads every imported retro mesh's material slots.
  2. Maps slot material name -> pack texture (normalized case).
  3. Creates per-(mesh,slot) MIs under RetroFantasyKit/Materials/ with the pack
     albedo + TextureWeight=1.0 (+ roughness per texture type), assigns to slots.

Run in the UE editor (Monolith run_python): route_retro_materials.main()
Writes: Saved/Audit/retro_material_routing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

MESH_BASE = "/Game/EnvSandbox/Meshes/Environment"
RFK_DIR = f"{MESH_BASE}/RetroFantasyKit"
MI_DIR = f"{RFK_DIR}/Materials"
TEX = "/Game/EnvSandbox/Textures/PackTextures/RetroFantasyKit"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "Saved" / "Audit" / "kenney_new_import.json"
OUT = ROOT / "Saved" / "Audit" / "retro_material_routing.json"

MEL = unreal.MaterialEditingLibrary

ROUGHNESS = {
    "barrel": 0.75, "cobblestone": 0.8, "cobblestonealternative": 0.8,
    "cobblestonepainted": 0.75, "details": 0.7, "fence": 0.7, "planks": 0.72,
    "roof": 0.65, "tree": 0.85, "water": 0.15, "stones": 0.65, "bricks": 0.8,
}
TEX_STEMS = ("cobblestonepainted", "cobblestonealternative", "cobblestone",
             "stonespainted", "stones", "bricks", "barrel", "details", "fence",
             "planks", "roof", "tree", "water")


def normalize(name: str) -> str:
    return "".join(c if c.isalnum() else "" for c in (name or "").lower())


def tex_for(material_name: str) -> str | None:
    n = normalize(material_name)
    for stem in TEX_STEMS:
        if n == stem or n.startswith(stem):
            return f"{TEX}/{stem}"
    return None


def ensure_mi(mesh_name: str, slot_name: str):
    clean = "".join(c if (c.isalnum() or c == "_") else "_" for c in slot_name) or "mat"
    path = f"{MI_DIR}/MI_{mesh_name}_{clean}"
    mi = unreal.load_asset(path)
    if mi is None:
        if not unreal.EditorAssetLibrary.does_directory_exist(MI_DIR):
            unreal.EditorAssetLibrary.make_directory(MI_DIR)
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(f"MI_{mesh_name}_{clean}", MI_DIR,
                                unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    return mi


def parent_params(mi):
    parent = mi.get_editor_property("parent")
    out = set()
    for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names,
               MEL.get_vector_parameter_names):
        try:
            for p in (fn(parent) or []):
                out.add(str(p))
        except Exception:
            pass
    return out


def mesh_paths():
    """Exact retro mesh paths from the import manifest."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    meshes = manifest["packs"]["retro_fantasy_kit"]["meshes"]
    out = []
    for m in meshes:
        if m["status"] not in ("imported", "exists"):
            continue
        name = m["name"]
        path = f"{RFK_DIR}/{name}" if m.get("namespaced") else f"{MESH_BASE}/{name}"
        out.append(path)
    return out


def main():
    rows = []
    matched = unmatched = 0
    paths = mesh_paths()
    for p in paths:
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            rows.append({"mesh": p, "slots": [{"status": "load_failed"}]})
            continue
        name = p.rsplit("/", 1)[-1]
        slots = list(a.static_materials)
        rec = {"mesh": p, "slots": []}
        for i, s in enumerate(slots):
            slot_mat = s.material_interface
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            mat_name = str(slot_mat.get_name()) if slot_mat else slot_name
            tex = tex_for(mat_name) or tex_for(slot_name)
            if tex is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "unmapped",
                                     "mat_name": mat_name})
                unmatched += 1
                continue
            matched += 1
            mi = ensure_mi(name, slot_name)
            if mi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "mi_failed"})
                continue
            params = parent_params(mi)
            asset = unreal.load_asset(tex)
            if asset is not None and "Albedo" in params:
                MEL.set_material_instance_texture_parameter_value(mi, "Albedo", asset)
            if "TextureWeight" in params:
                MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
            key = normalize(mat_name)
            rough = ROUGHNESS.get(key)
            if rough is not None and "Roughness" in params:
                MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
            unreal.EditorAssetLibrary.save_loaded_asset(mi)
            a.set_material(i, mi)
            rec["slots"].append({"index": i, "name": slot_name, "status": "routed",
                                 "tex": tex, "mi": mi.get_path_name()})
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        rows.append(rec)
    payload = {
        "generated": "2026-08-14",
        "summary": {"meshes": len(rows), "slots_matched": matched, "slots_unmatched": unmatched},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[retro] meshes={len(rows)} matched={matched} unmatched={unmatched}")
    return payload


if __name__ == "__main__":
    main()
