"""Route imported pack albedos onto the MI_Env_ImportedPacks_* instances."""
from __future__ import annotations

import sys
import time

import unreal

lib = unreal.MaterialEditingLibrary

ROUTES = {
    "MI_Env_CastleKit": "T_KenneyCastleKit_Albedo",
    "MI_Env_MedievalBuilder": "T_KayKitMedievalBuilder_Albedo",
    "MI_Env_MiniForest": "T_KenneyMiniForest_Albedo",
    "MI_Env_ModularCave": "T_KenneyModularCave_Albedo",
    "MI_Env_LowPolyCrystals": "T_LowPolyCrystals_Albedo",
    "MI_Env_MusicalInstruments": "T_MusicalInstruments_Albedo",
    "MI_Env_NatureMegaKit": "T_StylizedNatureMegaKit_Albedo",
}

INST_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/ImportedPacks"
TEX_DIR = "/Game/EnvSandbox/Textures/ImportedPacks"


def main() -> int:
    routed, missing = [], []
    for stem, tex_name in ROUTES.items():
        tex_path = f"{TEX_DIR}/{tex_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(tex_path):
            missing.append(tex_name)
            continue
        inst = unreal.load_asset(f"{INST_DIR}/{stem}")
        tex = unreal.load_asset(tex_path)
        if not inst or not tex:
            missing.append(f"{stem} (load failed)")
            continue
        lib.set_material_instance_texture_parameter_value(inst, "Albedo", tex)
        lib.set_material_instance_scalar_parameter_value(inst, "TextureWeight", 1.0)
        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
        routed.append(stem)
        unreal.log(f"[packroute] {stem} <- {tex_path}")

    unreal.log(f"[packroute] routed={len(routed)} missing={len(missing)}")
    print(f"routed: {routed}")
    print(f"missing: {missing}")
    return 0


if __name__ == "__main__":
    time.sleep(3)
    sys.exit(main())
