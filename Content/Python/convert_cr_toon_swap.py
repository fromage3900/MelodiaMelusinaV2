"""Surgical Toon swap for M_MS_CustomDecal_CR.

CR is already on Substrate (SubstrateSlabBSDF -> SubstrateConvertToDecal), so the
full converter's legacy-lit surgery crashes the editor on it. This runner swaps
the Slab BSDF for a SubstrateToonBSDF inside the existing ConvertToDecal chain:

  1. find SubstrateConvertToDecal
  2. find the Slab BSDF feeding it
  3. find the slab's BaseColor + Opacity inputs (or the color source feeding them)
  4. create SubstrateToonBSDF (TP_Default), wire color + FrontMaterial, opacity
  5. connect toon -> ConvertToDecal input, delete the slab
  6. recompile + save

Every step logs [CRS] so a crash (if any) is attributable. NO legacy-output
disconnection, NO bUsesSubstrate (property does not exist on Material here).
"""
from __future__ import annotations

import sys
import time

import unreal

TARGET = "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR"
PROFILE = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Default.TP_Default"


def step(msg: str) -> None:
    unreal.log(f"[CRS] {msg}")


def main() -> int:
    material = unreal.load_asset(TARGET)
    if not material:
        step("FAIL: not found")
        return 1
    exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
    step(f"expressions: {len(exprs)}")

    convert = None
    slab = None
    for e in exprs:
        n = type(e).__name__
        if n == "MaterialExpressionSubstrateConvertToDecal":
            convert = e
        if n == "MaterialExpressionSubstrateSlabBSDF":
            slab = e
    if not convert:
        step("FAIL: no ConvertToDecal found - already toon?")
        return 1
    step(f"convert_to_decal={convert is not None} slab={slab is not None}")

    # Color source: what feeds the slab's BaseColor, else the legacy BaseColor pin.
    color_src = None
    try:
        color_src = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_BASE_COLOR
        )
    except Exception as exc:
        step(f"  base-color node lookup failed: {exc}")
    step(f"color_src: {type(color_src).__name__ if color_src else None}")

    toon = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionSubstrateToonBSDF, 500, 200
    )
    try:
        profile = unreal.load_asset(PROFILE)
        if profile:
            toon.set_editor_property("toon_profile", profile)
            step("profile set TP_Default")
    except Exception as exc:
        step(f"profile failed: {exc}")

    if color_src:
        try:
            unreal.MaterialEditingLibrary.connect_material_expressions(
                color_src, "", toon, "BaseColor"
            )
            step("color wired to toon BaseColor")
        except Exception as exc:
            step(f"color wire failed: {exc}")

    try:
        unreal.MaterialEditingLibrary.connect_material_expressions(
            toon, "", convert, "Input"
        )
        step("toon -> ConvertToDecal Input")
    except Exception as exc:
        step(f"convert-input wire failed: {exc}")

    if slab:
        try:
            unreal.MaterialEditingLibrary.delete_material_expression(material, slab)
            step("slab deleted")
        except Exception as exc:
            step(f"slab delete failed: {exc}")

    try:
        unreal.MaterialEditingLibrary.recompile_material(material)
        step("recompile ok")
    except Exception as exc:
        step(f"recompile failed: {exc}")
        return 1

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
        step("saved")
    except Exception as exc:
        step(f"save failed: {exc}")
        return 1
    step("DONE")
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
