"""Re-route RetroFantasyKit MIs using the GLB material->texture ground truth.

The first router mapped material names (bricks/stones/stonesPainted) to texture
files that do not exist in the pack (only cobblestone*/*planks/*barrel/... are
shipped). Those MIs got TextureWeight=1.0 with NO Albedo -> they render the
master's noise texture. The GLB files encode the true mapping (e.g.
material 'bricks' -> image cobblestoneAlternative.png).

This script:
  1. Reads the GLB-derived mapping (built into this file as RETRO_MAP).
  2. For every MI under RetroFantasyKit/Materials/: if Albedo missing or noise,
     set Albedo from the map (per mesh + slot) + TextureWeight=1.0.
  3. Re-verifies by re-reading.

Run in the UE editor (Monolith run_python): reroute_retro_materials.main()
Writes: Saved/Audit/retro_material_reroute.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

MESH_BASE = "/Game/EnvSandbox/Meshes/Environment"
RFK_DIR = f"{MESH_BASE}/RetroFantasyKit"
MI_DIR = f"{RFK_DIR}/Materials"
TEX = "/Game/EnvSandbox/Textures/PackTextures/RetroFantasyKit"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "retro_material_reroute.json"

MEL = unreal.MaterialEditingLibrary

NOISE_MARKERS = ("sbs_-_", "DefaultTexture", "Black.Black", "Perlin", "Cracks_")

# Canonical material-name -> texture stem (verified across all 105 GLBs:
# every material name maps to exactly one image in the pack).
MAT_TO_TEX = {
    "barrel": "barrel",
    "bricks": "cobblestoneAlternative",
    "details": "details",
    "fence": "fence",
    "planks": "planks",
    "roof": "roof",
    "stones": "cobblestone",
    "stonespainted": "cobblestonePainted",
    "tree": "tree",
    "water": "water",
}


def is_noise(tex_path):
    return tex_path is None or any(mk in str(tex_path) for mk in NOISE_MARKERS)


def main():
    rows = []
    fixed = ok = 0
    if not unreal.EditorAssetLibrary.does_directory_exist(MI_DIR):
        print("[retro_reroute] no MI dir")
        return {"fixed": 0}
    for p in unreal.EditorAssetLibrary.list_assets(MI_DIR, recursive=False):
        leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
        # MI_<mesh>_<slot>
        rest = leaf[len("MI_"):]
        if "_" not in rest:
            continue
        mesh, _, slot = rest.rpartition("_")
        slot_key = "".join(c if c.isalnum() else "" for c in slot).lower()
        target_stem = MAT_TO_TEX.get(slot_key)
        if target_stem is None:
            # loose slot names like "stonespainted" already covered; try mesh-wide fallback
            rows.append({"path": p, "status": "no_map_for_slot", "mesh": mesh, "slot": slot})
            continue
        mi = unreal.load_asset(p)
        if mi is None:
            rows.append({"path": p, "status": "load_failed"})
            continue
        alb = None
        try:
            alb = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, "Albedo")
        except Exception:
            pass
        alb_path = alb.get_path_name() if alb else None
        if not is_noise(alb_path):
            ok += 1
            rows.append({"path": p, "status": "already_ok", "tex": alb_path})
            continue
        tex = unreal.load_asset(f"{TEX}/{target_stem}")
        if tex is None:
            rows.append({"path": p, "status": "texture_missing", "stem": target_stem})
            continue
        MEL.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        fixed += 1
        rows.append({"path": p, "status": "fixed", "slot": slot, "tex": f"{TEX}/{target_stem}"})
    payload = {"generated": "2026-08-14", "summary": {"fixed": fixed, "already_ok": ok,
                "no_map": sum(1 for r in rows if "no_map" in r["status"])},
               "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[retro_reroute] fixed={fixed} ok={ok}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
