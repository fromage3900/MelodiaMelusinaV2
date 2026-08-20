"""Wire a gated opacity path into a masked toon master for Atlantis foliage masks.

Design (gated, default-off — zero visual change to existing instances):
  bUseOpacityMap (static switch, default False)
  OpacityMap      (texture object param, default T_None)
  OpacityStrength (scalar param, default 1.0)

Chain: switch ? (OpacityMap sample * OpacityStrength) : Constant(1.0)
  -> MP_OPACITY_MASK (material property; feeds the Substrate Toon BSDF alpha —
     same route M_ToonFoliage uses, confirmed by probe 1 2026-08-17).

Blend reality check from the probe: M_Master_Toon_Universal is BLEND_OPAQUE
with no opacity input on its SubstrateToonBSDF, so the path is built on a
duplicated variant, M_Master_Toon_Universal_Alpha (BLEND_MASKED + two_sided),
and the variant is reported as the parent for opacity sets. Idempotent: an
existing variant is loaded, not duplicated again.

Run inside the live editor via Monolith run_python:
  import wire_atlantis_opacity_master as wo; wo.main()
Manifest: Saved/Audit/atlantis_opacity_master_wire.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROBE = PROJECT_ROOT / "Saved" / "Audit" / "atlantis_material_surface_probe.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "atlantis_opacity_master_wire.json"

MASTER_TOON = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
VARIANT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"

GROUP = "Opacity"

EXPR_PARAM_CLASSES = {
    "scalar": ("MaterialExpressionScalarParameter",),
    "switch": ("MaterialExpressionStaticSwitchParameter", "MaterialExpressionStaticBoolParameter"),
    "texture": ("MaterialExpressionTextureObjectParameter", "MaterialExpressionTextureSampleParameter2D"),
}


def expression_params(mat: unreal.Material, kinds: tuple[str, ...]) -> list[str]:
    names: list[str] = []
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(e).__name__ not in kinds:
            continue
        try:
            names.append(str(e.get_editor_property("parameter_name")))
        except Exception:
            continue
    return sorted(names)


def find_param(mat: unreal.Material, cls, pname: str):
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        try:
            if isinstance(e, cls) and str(e.get_editor_property("parameter_name")) == pname:
                return e
        except Exception:
            continue
    return None


def build_opacity_chain(mat: unreal.Material) -> dict:
    """Create switch + texture + strength + wiring. Returns what was written."""
    written: dict = {"params": [], "wired": []}

    switch = find_param(mat, unreal.MaterialExpressionStaticSwitchParameter, "bUseOpacityMap")
    if not switch:
        switch = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionStaticSwitchParameter, -1600, -300)
        switch.set_editor_property("parameter_name", "bUseOpacityMap")
        switch.set_editor_property("group", GROUP)
        switch.set_editor_property("default_value", False)
        written["params"].append("bUseOpacityMap")

    tex_param = find_param(mat, unreal.MaterialExpressionTextureObjectParameter, "OpacityMap")
    if not tex_param:
        tex_param = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureObjectParameter, -1900, -300)
        tex_param.set_editor_property("parameter_name", "OpacityMap")
        tex_param.set_editor_property("group", GROUP)
        written["params"].append("OpacityMap")

    tex_sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -1700, -250)
    unreal.MaterialEditingLibrary.connect_material_expressions(tex_param, "", tex_sample, "TextureObject")

    strength = find_param(mat, unreal.MaterialExpressionScalarParameter, "OpacityStrength")
    if not strength:
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionScalarParameter, -1700, -100)
        strength.set_editor_property("parameter_name", "OpacityStrength")
        strength.set_editor_property("group", GROUP)
        strength.set_editor_property("default_value", 1.0)
        written["params"].append("OpacityStrength")

    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -1450, -250)
    unreal.MaterialEditingLibrary.connect_material_expressions(tex_sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", mul, "B")

    one = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -1450, -100)
    one.set_editor_property("r", 1.0)

    unreal.MaterialEditingLibrary.connect_material_expressions(one, "", switch, "False")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul, "", switch, "True")

    try:
        unreal.MaterialEditingLibrary.connect_material_property(
            switch, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        written["wired"].append("bUseOpacityMap->MP_OPACITY_MASK")
    except Exception as exc:
        written["wired"].append(f"MP_OPACITY_MASK connect failed: {exc}")
    return written


def main() -> dict:
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    toon = probe["masters"].get("toon_universal", {})
    blend_mode = toon.get("blend_mode", "?")

    target_master = MASTER_TOON
    action = "in_place"

    if "MASKED" in blend_mode.upper():
        mat = unreal.EditorAssetLibrary.load_asset(MASTER_TOON)
    elif unreal.EditorAssetLibrary.does_asset_exist(VARIANT):
        mat = unreal.EditorAssetLibrary.load_asset(VARIANT)
        action = "variant_existing"
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        tools.duplicate_asset(
            VARIANT.split("/")[-1], VARIANT.rsplit("/", 1)[0],
            unreal.EditorAssetLibrary.load_asset(MASTER_TOON))
        mat = unreal.EditorAssetLibrary.load_asset(VARIANT)
        if not mat:
            return {"ok": False, "error": f"variant not created: {VARIANT}"}
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property("two_sided", True)
        action = "variant_created"

    if not mat:
        return {"ok": False, "error": f"target master not loadable: {target_master}"}

    written = build_opacity_chain(mat)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        compile_ok = True
        compile_err = None
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)

    reread = {
        "scalars": expression_params(mat, EXPR_PARAM_CLASSES["scalar"]),
        "switches": expression_params(mat, EXPR_PARAM_CLASSES["switch"]),
        "textures": expression_params(mat, EXPR_PARAM_CLASSES["texture"]),
    }
    ok = (
        compile_ok
        and "OpacityMap" in reread["textures"]
        and "OpacityStrength" in reread["scalars"]
        and "bUseOpacityMap" in reread["switches"]
        and "MP_OPACITY_MASK connect failed" not in written["wired"]
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": target_master,
        "action": action,
        "blend_mode_before": blend_mode,
        "blend_mode_after": str(mat.get_editor_property("blend_mode")),
        "two_sided_after": bool(mat.get_editor_property("two_sided")),
        "written": written,
        "compile_ok": compile_ok,
        "compile_error": compile_err,
        "reread": reread,
        "ok": ok,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)