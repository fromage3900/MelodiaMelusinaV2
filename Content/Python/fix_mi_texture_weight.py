"""Fix TextureWeight + texture routing on EnvSandbox Universal material instances.

Root causes found by survey_mi_texture_weight_v2.py:
  1. Master default TextureWeight=0.0 (procedural base) -> 66 instances that DO
     override Albedo/NormalMap/ORM but never override TextureWeight inherit 0.0
     and render without their textures. Pipeline convention
     (ensure_portfolio_instances.py, assign_hero_zentrim.py) is TextureWeight=1.0
     on textured instances.
  2. The 7 MI_Env_ImportedPacks_* instances have ZERO overrides (the intake
     script set a non-existent 'BaseColorAtlas' param). Their pack albedo
     textures are staged in Imports/Environment/<Pack>/; import the first
     albedo-like map and route Albedo + TextureWeight=1.0.

What this does NOT touch: water masters (their own setup), procedural feature
demos (Escher ImpossibleTile, MadokaPulse, IttoSpiral, NikkiIntegrated,
Showcase2 demo row) which are intentionally tint/feature-driven.

Modes: --fix (default), --dry-run (report only).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = "/Game/EnvSandbox/Materials/Instances"
PACK_TEX_DEST = "/Game/EnvSandbox/Textures/ImportedPacks"

# Instances that intentionally render as procedural/feature demos -> keep weight as authored.
PROCEDURAL_ONLY = [
    "/Game/EnvSandbox/Materials/Instances/Environment/Escher/MI_Escher_ImpossibleTile",
    "/Game/EnvSandbox/Materials/Instances/Environment/Escher/MI_Escher_Woodcut",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/MI_NikkiIntegrated_Bloom",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/MI_NikkiIntegrated_Dream",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/MI_NikkiIntegrated_Moonlit",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_CosmicOrrery_IntegratedV1",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_CosmicOrrery",
    "/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Universal/MI_Showcase2_Universal_DisplacementParallax",
    "/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Universal/MI_Showcase2_Universal_IttoSpiral",
    "/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Universal/MI_Showcase2_Universal_MadokaPulse",
    "/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Universal/MI_Showcase2_Universal_SharpToonBands",
    "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_MelodiaVoidGradient",
    "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_MelodiaVoid_Baroque",
    "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_MelodiaVoid_Cosmic",
    "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_MelodiaVoid_Neutral",
    "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_MelodiaVoid_Sakura",
    "/Game/EnvSandbox/Materials/Instances/M_Master_Toon_Universal_Inst1",
]

# Named-surface instances that need a routed texture map (pack-style or first-party set).
SURFACE_ROUTE = {
    "/Game/EnvSandbox/Materials/Instances/Environment/House/MI_House_Railing": ("/Game/EnvSandbox/Textures/Brick01_BaseColor.Brick01_BaseColor", "/Game/EnvSandbox/Textures/Brick01_Normal.Brick01_Normal"),
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_CrystallineSpire": ("/Game/EnvSandbox/Textures/crystal1_BaseColor.crystal1_BaseColor", "/Game/EnvSandbox/Textures/crystal1_Normal.crystal1_Normal"),
    "/Game/EnvSandbox/Materials/Instances/MI_IridescentRock": ("/Game/_PROJECT/04_Materials/Textures/Textures/T_Rock_BSS_diffuseOriginal.T_Rock_BSS_diffuseOriginal", "/Game/_PROJECT/04_Materials/Textures/Textures/T_Rock_BSS_normal.T_Rock_BSS_normal"),
}

PACK_ALBEDO_CANDIDATES = [
    "colormap.png",
    "*_Albedo.png",
    "*_BaseColor.png",
    "*_basecolor.png",
    "*_diffuse.png",
    "*_albedo.png",
]

# Packs whose usable albedo is a per-item iso render (no shared colormap).
PACK_ISO_ALBEDO = {
    "MusicalInstruments": ["*_NE.png"],
    "StylizedNatureMegaKit": ["*_NE.png"],
}

PACK_SOURCE = {
    "MI_Env_CastleKit": "KenneyCastleKit",
    "MI_Env_MedievalBuilder": "KayKitMedievalBuilder",
    "MI_Env_MiniForest": "KenneyMiniForest",
    "MI_Env_ModularCave": "KenneyModularCave",
    "MI_Env_LowPolyCrystals": "LowPolyCrystals",
    "MI_Env_MusicalInstruments": "MusicalInstruments",
    "MI_Env_NatureMegaKit": "StylizedNatureMegaKit",
}


def find_pack_albedo(pack_dir: Path):
    for cand in PACK_ALBEDO_CANDIDATES:
        if cand == "colormap.png":
            hits = list(pack_dir.rglob("colormap.png"))
        else:
            hits = [p for p in pack_dir.rglob(cand) if "Preview" not in str(p) and "Previews" not in str(p)]
        if hits:
            return sorted(hits, key=lambda p: len(str(p)))[0]
    return None


def find_pack_iso_albedo(pack_dir: Path, patterns):
    if not patterns:
        return None
    for pat in patterns:
        hits = [p for p in pack_dir.rglob(pat) if "Preview" not in str(p) and "Previews" not in str(p)]
        if hits:
            return sorted(hits, key=lambda p: len(str(p)))[0]
    return None


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    lib = unreal.MaterialEditingLibrary
    assets = unreal.EditorAssetLibrary.list_assets(INSTANCE_ROOT, recursive=True, include_folder=False)
    fixed_weight: list[str] = []
    routed_packs: list[str] = []
    routed_surface: list[str] = []
    skipped_procedural: list[str] = []

    for path in assets:
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        try:
            parent = str(inst.get_editor_property("parent"))
        except Exception:
            continue
        if "M_Master_Toon_Universal" not in parent:
            continue

        if path in PROCEDURAL_ONLY:
            skipped_procedural.append(path)
            continue
        bare = path.split(".", 1)[0]
        if bare in PROCEDURAL_ONLY:
            skipped_procedural.append(path)
            continue

        # 1) Instances with any overridden core texture but no TextureWeight override.
        tex_overridden = [
            p for p in ("Albedo", "NormalMap", "ORM", "RoughnessMap", "MetallicMap", "HeightMap", "EmissiveMap",
                        "LayerB_Albedo", "LayerC_Albedo")
            if lib.is_material_instance_parameter_overridden(inst, p)
        ]
        tw_overridden = lib.is_material_instance_parameter_overridden(inst, "TextureWeight")
        if tex_overridden and not tw_overridden:
            if not dry:
                lib.set_material_instance_scalar_parameter_value(inst, "TextureWeight", 1.0)
            fixed_weight.append(path)

        # 2) ImportedPack instances -> route pack albedo.
        stem = path.rsplit("/", 1)[-1].split(".", 1)[0]
        if stem in PACK_SOURCE:
            pack = PACK_SOURCE[stem]
            src = ROOT / "Imports" / "Environment" / pack
            albedo = find_pack_albedo(src) or find_pack_iso_albedo(src, PACK_ISO_ALBEDO.get(pack, []))
            if albedo:
                tex_name = f"T_{pack}_Albedo"
                tex_path = f"{PACK_TEX_DEST}/{tex_name}"
                if not dry:
                    if not unreal.EditorAssetLibrary.does_asset_exist(tex_path):
                        task = unreal.AssetImportTask()
                        task.set_editor_property("automated", True)
                        task.set_editor_property("filename", str(albedo))
                        task.set_editor_property("destination_path", PACK_TEX_DEST)
                        task.set_editor_property("destination_name", tex_name)
                        task.set_editor_property("replace_existing", False)
                        task.set_editor_property("save", False)
                        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                    tex = unreal.load_asset(tex_path)
                    if tex:
                        lib.set_material_instance_texture_parameter_value(inst, "Albedo", tex)
                        lib.set_material_instance_scalar_parameter_value(inst, "TextureWeight", 1.0)
                        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
                        routed_packs.append(f"{path} <- {albedo.name}")
                else:
                    routed_packs.append(f"{path} <- {albedo.name} (dry)")

        # 3) Named-surface instances -> route explicit albedo/normal.
        elif bare in SURFACE_ROUTE:
            albedo_p, normal_p = SURFACE_ROUTE[bare]
            if not dry:
                alb = unreal.load_asset(albedo_p)
                nrm = unreal.load_asset(normal_p)
                if alb:
                    lib.set_material_instance_texture_parameter_value(inst, "Albedo", alb)
                if nrm:
                    lib.set_material_instance_texture_parameter_value(inst, "NormalMap", nrm)
                lib.set_material_instance_scalar_parameter_value(inst, "TextureWeight", 1.0)
                unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
                routed_surface.append(path)
            else:
                routed_surface.append(f"{path} (dry)")

    report = {
        "generated": "2026-08-13",
        "dry_run": dry,
        "fixed_texture_weight": fixed_weight,
        "routed_packs": routed_packs,
        "routed_surface": routed_surface,
        "skipped_procedural": skipped_procedural,
        "summary": {
            "fixed_texture_weight": len(fixed_weight),
            "routed_packs": len(routed_packs),
            "routed_surface": len(routed_surface),
            "skipped_procedural": len(skipped_procedural),
        },
    }
    out = ROOT / "Saved" / "Audit" / "mi_texture_weight_fix.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
