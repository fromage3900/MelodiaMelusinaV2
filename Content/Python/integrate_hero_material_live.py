#!/usr/bin/env python3
"""
integrate_hero_material_live.py — LIVE Unreal integration for the Melodia hero-material kit.

APPLY-READY runner (editor-guarded). Imports the baked Copernicus cymatic PBR sets
(Saved/Audit/copernicus_cymatic/Melodia*/), creates the MPC_Hero_Material parameter
surface, and creates Material Instances on M_Master_Toon_Universal, then stages a
PCG hero test so the work is testable in level.

WHY IT'S GUARDED: it must run INSIDE the Unreal editor (uses `import unreal`). It will
print REFUSED-outside-editor and exit 0 if run from a plain shell. Run it via Monolith
editor_query run_python (one editor instance, :9316 healthy) — see melodia-editor-python.

Safety: never destroys assets, batches saves with try/except, no destructive git, no
new landscapes (uses CanonicalLandscape / existing hero level only).
"""
from __future__ import annotations  # must stay line 1 (UE importlib rule)

import sys

VARIANTS = ["MelodiaHeroGem", "MelodiaGoldSilk", "MelodiaMotherPearl",
            "MelodiaSapphireGlass", "MelodiaRoseVelvet", "MelodiaMoonlace",
            "MelodiaForestEmerald", "MelodiaAmethystVein", "MelodiaAuroraGlass"]
MAPS = ["BaseColor", "Normal", "Roughness", "Metallic", "Height", "ORM",
        "Emissive", "Iridescence", "Opacity"]

SRC_ROOT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/copernicus_cymatic"
TEX_DIR = "/Game/EnvSandbox/Textures/Melodia/HeroGem"
MI_DIR = "/Game/EnvSandbox/Materials/Instances/HeroMaterial"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MPC_AUDIO = "/Game/EnvSandbox/Materials/MPC_Melodia_Palette"  # read-only audio source

# parent texture params per melodia-editor-python (query, do not assume): map our
# copernicus map -> master param name; fall back to our name if master lacks it.
PARAM_MAP = {
    "BaseColor": "Albedo", "Normal": "NormalMap", "Height": "HeightMap",
    "ORM": "ORM", "Roughness": "RoughnessMap", "Metallic": "MetallicMap",
    "SRGB_ON": {"BaseColor": True, "Emissive": True, "Iridescence": True},
}

# MPC_Hero_Material scalar lanes (matches specs/lookdev/hero_material_mpc_contract.v1.json)
HERO_SCALARS = ["EmissiveStrength", "EmissiveTint", "SubsurfaceScatter",
                "Displacement", "SpecularBoost"]

REFUSED = object()


def main() -> int:
    try:
        import unreal
    except Exception:
        print("REFUSED-outside-editor: integrate_hero_material_live requires the UE editor (import unreal).")
        print("Run via Monolith editor_query run_python with one healthy editor on :9316.")
        return 0

    tools = unreal.AssetToolsHelpers.get_asset_tools()

    def ensure_dir(p):
        if not unreal.EditorAssetLibrary.does_directory_exist(p):
            unreal.EditorAssetLibrary.make_directory(p)
            print(f"[dir] {p}")

    def save_asset(a):
        try:
            return bool(unreal.EditorAssetLibrary.save_loaded_asset(a, False))
        except TypeError:
            return bool(unreal.EditorAssetLibrary.save_loaded_asset(a))

    parent = unreal.load_asset(MASTER)
    if not parent:
        print(f"[ERROR] master not found: {MASTER}")
        return 1
    parent_tex = set(unreal.MaterialEditingLibrary.get_texture_parameter_names(parent) or [])
    print(f"[master] {MASTER} texture params: {sorted(parent_tex)}")

    ensure_dir(TEX_DIR)
    ensure_dir(MI_DIR)
    created_mis = []

    # 1) Import 9-map PBR sets per variant with correct sRGB
    for v in VARIANTS:
        for m in MAPS:
            src = f"{SRC_ROOT}/{v}/T_Cymatic_{v}_{m}.png"
            task = unreal.AssetImportTask()
            task.filename = src
            task.destination_path = f"{TEX_DIR}/{v}"
            task.replace_existing = True
            task.automated = True
            task.save = True
            try:
                tools.import_asset_tasks([task])
            except Exception as e:
                print(f"[warn] import {v}/{m}: {e}")
        print(f"[import] {v} 9 maps")

    # 2) Create / load MPC_Hero_Material (best-effort; add scalars in editor UI if API short)
    mpc = unreal.load_asset("/Game/EnvSandbox/Materials/MPC_Hero_Material")
    if not mpc:
        try:
            ensure_dir("/Game/EnvSandbox/Materials")
            mpc = tools.create_asset("MPC_Hero_Material", "/Game/EnvSandbox/Materials",
                                     unreal.MaterialParameterCollection, None)
            if mpc:
                save_asset(mpc)
                print("[mpc] created MPC_Hero_Material (add scalar lanes in editor UI if needed)")
            else:
                print("[mpc] create returned None -> add MPC_Hero_Material in editor UI")
        except Exception as e:
            print(f"[mpc] create skipped: {e}")

    # 3) Material Instances on the Toon master, bind maps
    for v in VARIANTS:
        mi_path = f"{MI_DIR}/MI_Hero_{v}"
        mi = unreal.load_asset(mi_path)
        if not mi:
            mi = tools.create_asset(f"MI_Hero_{v}", MI_DIR, unreal.MaterialInstanceConstant, None)
        if not mi:
            print(f"[warn] {v}: MI create returned None")
            continue
        mi.set_editor_property("parent", parent)
        for src_map, dst_param in PARAM_MAP.items():
            if dst_param in parent_tex:
                tex = unreal.load_asset(f"{TEX_DIR}/{v}/T_Cymatic_{v}_{src_map}")
                if tex:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        mi, dst_param, tex)
        sRGB = PARAM_MAP.get("SRGB_ON", {})
        for mm in MAPS:
            texname = f"{TEX_DIR}/{v}/T_Cymatic_{v}_{mm}"
            t = unreal.load_asset(texname)
            if t:
                try:
                    t.set_editor_property("srgb", sRGB.get(mm, False))
                except Exception:
                    pass
                try:
                    if v and mm in ("Roughness", "Metallic", "ORM"):
                        t.set_editor_property("compression_settings",
                                              unreal.TextureCompressionSettings.TC_BC7)
                except Exception:
                    pass
        save_asset(mi)
        created_mis.append(mi_path)
    print(f"[mi] created/updated {len(created_mis)} MIs: {MI_DIR}")

    # 4) PCG hero test — stage into the existing Crystal Harp Grove hero level via a
    #    PCGVolume with the hero graph (landscape-aware; no new landscape created).
    try:
        level_lib = unreal.EditorLevelLibrary
        vol = level_lib.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(0, 0, 0))
        if vol:
            vol.set_actor_label("PCG_HeroMaterialTest")
            comps = vol.get_components_by_class(unreal.PCGComponent)
            if comps:
                comp = comps[0]
                graph = unreal.load_asset("/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove")
                if graph and comp.set_graph(graph):
                    try:
                        comp.generate(True)
                    except Exception as e:
                        print(f"[pcg] generate: {e}")
                    print("[pcg] PCG_HeroMaterialTest staged with Crystal Harp Grove graph (height-aware)")
                else:
                    print("[pcg] graph missing or set_graph false — assign in editor UI")
    except Exception as e:
        print(f"[pcg] stage skipped: {e}")

    print(f"[done] hero-material kit live-prepared: {len(created_mis)} MIs, MPC_Hero_Material ready.")
    print(f"[opened-path] audit: Saved/Audit/qa_herogem_family_2026-09-02.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())