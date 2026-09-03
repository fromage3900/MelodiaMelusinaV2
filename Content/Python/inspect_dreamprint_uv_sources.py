"""Inspect UV-source expression modes on the dreamprint ink + grade masters.

The ink rebuild feeds its UV input from a ScreenPosition node; if its mode is
pixel-space rather than normalized 0-1, the halftone/hatch math breaks at
runtime even though the shader compiles. Prints node mode + grade's UV source.
"""
from __future__ import annotations

import unreal

INK = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"
GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"

if hasattr(unreal, "ScreenPositionMode"):
    print("SP_MODE_MEMBERS", [str(x) for x in dir(unreal.ScreenPositionMode) if not x.startswith("_")])
else:
    print("SP_MODE_MEMBERS NO_ENUM")


def show(path: str, label: str) -> None:
    mat = unreal.load_asset(path)
    print(f"== {label} ==")
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        cn = type(e).__name__
        if cn == "MaterialExpressionScreenPosition":
            try:
                print("SP", e.get_name(), "mode=", e.get_editor_property("screen_position_mode"))
            except Exception as exc:
                print("SP", e.get_name(), "mode read error:", exc)
        elif cn == "MaterialExpressionSceneTexture":
            try:
                print("ST", e.get_name(), "id=", e.get_editor_property("scene_texture_id"))
            except Exception as exc:
                print("ST", e.get_name(), "id read error:", exc)


show(INK, "INK")
show(GRADE, "GRADE")