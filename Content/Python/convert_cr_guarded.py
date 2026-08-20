"""Attempt M_MS_CustomDecal_CR conversion via a guarded minimal path.

The full converter crashes the editor deterministically on this asset. This
runner logs each step so the crashing operation is identifiable. Steps:
 1. load material
 2. create SubstrateToonBSDF + assign TP_Default
 3. wire color source (MP_BASE_COLOR)
 4. connect Front Material
 5. recompile
 6. save

No legacy-output disconnection in this variant. If it still crashes, the asset
is documented as engine-incompatible rather than silently skipped.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import unreal

TARGET = "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR"


def step(msg: str) -> None:
    unreal.log(f"[CRG] {msg}")


def main() -> int:
    step("load")
    material = unreal.load_asset(TARGET)
    if not material:
        step("FAIL: material not found")
        return 1
    if isinstance(material, unreal.MaterialInstanceConstant):
        step("FAIL: is an instance")
        return 1
    step(f"loaded {material.get_name()} class={type(material).__name__}")

    exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
    step(f"expressions: {len(exprs)}")
    for e in exprs:
        step(f"  expr: {type(e).__name__}")

    step("find color source")
    color_src = None
    try:
        color_src = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_BASE_COLOR
        )
    except Exception as exc:
        step(f"  get base color node failed: {exc}")
    step(f"  color_src: {type(color_src).__name__ if color_src else None}")

    step("create toon bsdf")
    toon = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionSubstrateToonBSDF, 500, 200
    )
    step("assign profile")
    profile = unreal.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Default.TP_Default")
    toon.set_editor_property("toon_profile", profile)
    step("bUsesSubstrate")
    material.set_editor_property("bUsesSubstrate", True)

    if color_src:
        step("connect color")
        unreal.MaterialEditingLibrary.connect_material_expressions(
            color_src, "", toon, "BaseColor"
        )
    step("connect front material")
    unreal.MaterialEditingLibrary.connect_material_property(
        toon, "", unreal.MaterialProperty.MP_FRONT_MATERIAL
    )
    step("recompile")
    unreal.MaterialEditingLibrary.recompile_material(material)
    step("save")
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    step("DONE")
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
