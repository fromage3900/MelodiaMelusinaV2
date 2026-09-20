"""Build MF_MelodiaWindHueReveal — the reusable directional wind hue-reveal function.

Muse brief 2026-09-16 (commit 09316fa9), stage P3.

Contract, straight from the brief's field math:

    D      = normalize(WindDirection.xy)          <- guarded, see below
    phase  = dot(AbsoluteWorldPosition.xy, D) * SpatialFrequency
    phase += Time * WindStrength * TravelSpeed
    phase += PerInstanceHueSeed
    Wave   = sin(phase) * 0.5 + 0.5

Ownership: the function is a pure consumer. It reads no collection itself — the
caller wires the palette's `WindDirX`/`WindDirY`/`WindStrength` lanes (source) or
`MPC_Cymatics_Driver`'s `Cymatic_Wind*` lanes (derived). Nothing here writes a
collection, so the Cymatics writer keeps its authority.

Zero-delta: `Color` equals `BaseColor` when either gate is zero. Two independent
multiplicative gates do that -- the artist's ResponseAmount and WindStrength
itself -- so an undriven meadow is the natural flower albedo, not a tinted one.
The wave is applied at 0.5 weight inside the lerp; the brief asks for a
restrained directional reveal, not a full-spectrum rainbow cycle.

Per-family response without unique MIs: ResponseAmount and PerInstanceHueSeed are
inputs, so they come from instance custom data on the shared material.

Run: Monolith editor.run_python (execute_file), or
     import build_mf_melodia_wind_hue_reveal as b; b.main()
Receipt: Saved/Audit/mf_melodia_wind_hue_reveal_build.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MF_DIR = "/Game/Melodia/_PROJECT/04_Materials/Functions"
MF_NAME = "MF_MelodiaWindHueReveal"
MF_PATH = f"{MF_DIR}/{MF_NAME}"


def _report_path() -> Path:
    try:
        return Path(unreal.Paths.project_dir()) / "Saved" / "Audit" \
            / "mf_melodia_wind_hue_reveal_build.json"
    except Exception:
        return (Path(__file__).resolve().parents[2] / "Saved" / "Audit"
                / "mf_melodia_wind_hue_reveal_build.json")


REPORT = _report_path()
MEL = unreal.MaterialEditingLibrary


def ensure_function():
    """Load the function, creating it if this is the first run."""
    existing = unreal.EditorAssetLibrary.load_asset(MF_PATH)
    if existing:
        return existing, False
    if not unreal.EditorAssetLibrary.does_directory_exist(MF_DIR):
        unreal.EditorAssetLibrary.make_directory(MF_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFunctionFactoryNew()
    mf = tools.create_asset(MF_NAME, MF_DIR, unreal.MaterialFunction, factory)
    if mf is None:
        raise RuntimeError(f"could not create {MF_PATH}")
    return mf, True


def expr(mf, cls, x, y):
    return MEL.create_material_expression_in_function(mf, cls, x, y)


def fn_input(mf, name, x, y, input_type, sort):
    inp = expr(mf, unreal.MaterialExpressionFunctionInput, x, y)
    inp.set_editor_property("input_name", name)
    inp.set_editor_property("sort_priority", sort)
    try:
        inp.set_editor_property("input_type", input_type)
    except Exception as exc:
        print(f"  [warn] input_type on {name}: {exc}")
    return inp


def fn_output(mf, name, x, y):
    out = expr(mf, unreal.MaterialExpressionFunctionOutput, x, y)
    out.set_editor_property("output_name", name)
    return out


def custom_node(mf, code, description, names, x, y, output_type):
    node = expr(mf, unreal.MaterialExpressionCustom, x, y)
    node.set_editor_property("code", code)
    node.set_editor_property("description", description)
    try:
        node.set_editor_property("output_type", output_type)
    except Exception as exc:
        print(f"  [warn] output_type on {description}: {exc}")
    # Every identifier the HLSL uses must be a declared input pin; an undeclared
    # one is the 'Custom node reads an identifier it never declared' defect that
    # compiles to a broken/default material rather than an error.
    ins = list(node.get_editor_property("inputs"))
    while len(ins) < len(names):
        ins.append(unreal.CustomInput())
    for idx, nm in enumerate(names):
        ins[idx].set_editor_property("input_name", nm)
    node.set_editor_property("inputs", ins)
    return node


# Shared preamble. rsqrt + a length-squared compare is the guard: a degenerate
# wind vector falls back to +X instead of feeding NaN through normalize().
WIND_PREAMBLE = """float2 raw = WindDirection;
float len2 = dot(raw, raw);
float2 D = (len2 > 1e-8) ? raw * rsqrt(len2) : float2(1.0, 0.0);

float phase = dot(WorldPos.xy, D) * SpatialFrequency;
phase += Time * WindStrength * TravelSpeed;
phase += HueSeed;

float wave = sin(phase) * 0.5 + 0.5;
"""

MASK_CODE = WIND_PREAMBLE + """
// Two multiplicative gates: artist amount, then wind itself. Either at zero
// holds the reveal off completely, which is the zero-delta state.
float amount = saturate(ResponseAmount) * saturate(WindStrength);
return wave * amount;"""

COLOR_CODE = """// 0.5 keeps the reveal restrained -- a directional tint travelling through the
// meadow, not a rainbow cycle. Mask already carries both gates.
float k = saturate(Mask) * 0.5;
float3 Color = lerp(BaseColor, RevealTint, k);
return Color;"""


def clear_function(mf) -> int:
    """Empty the function graph and prove it is empty before rebuilding.

    A partially-built first attempt leaves expressions behind, and a
    `delete_all_material_expressions_in_function` that does not actually empty
    the graph produces a function with two inputs of the same name -- which
    reads as a working build in any count-only check. So this counts, falls back
    to per-expression deletion, and returns what is left for the report.
    """
    MEL.delete_all_material_expressions_in_function(mf)
    remaining = MEL.get_num_material_expressions_in_function(mf)
    if remaining:
        for e in list(MEL.get_material_function_expressions(mf)):
            try:
                MEL.delete_material_expression_in_function(mf, e)
            except Exception as exc:
                print(f"  [warn] delete {e}: {exc}")
        remaining = MEL.get_num_material_expressions_in_function(mf)
    return remaining


def build(mf):
    leftover = clear_function(mf)
    if leftover:
        raise RuntimeError(
            f"function graph not empty before build: {leftover} expressions remain")

    i_base = fn_input(mf, "BaseColor", -2000, 0,
                      unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 0)
    i_tint = fn_input(mf, "RevealTint", -2000, 180,
                      unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 1)
    i_wdir = fn_input(mf, "WindDirection", -2000, 360,
                      unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2, 2)
    i_wstr = fn_input(mf, "WindStrength", -2000, 540,
                      unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 3)
    i_freq = fn_input(mf, "SpatialFrequency", -2000, 700,
                      unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 4)
    i_speed = fn_input(mf, "TravelSpeed", -2000, 860,
                       unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 5)
    i_seed = fn_input(mf, "PerInstanceHueSeed", -2000, 1020,
                      unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 6)
    i_amt = fn_input(mf, "ResponseAmount", -2000, 1180,
                     unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 7)

    world_pos = expr(mf, unreal.MaterialExpressionWorldPosition, -2000, 1360)
    time = expr(mf, unreal.MaterialExpressionTime, -2000, 1520)

    names = ["WorldPos", "Time", "WindDirection", "WindStrength", "SpatialFrequency",
             "TravelSpeed", "HueSeed", "ResponseAmount"]

    mask = custom_node(mf, MASK_CODE, "MF_MelodiaWindHueReveal mask",
                       names, -1500, 0, unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    MEL.connect_material_expressions(world_pos, "", mask, "WorldPos")
    MEL.connect_material_expressions(i_wdir, "", mask, "WindDirection")
    MEL.connect_material_expressions(i_wstr, "", mask, "WindStrength")
    MEL.connect_material_expressions(i_freq, "", mask, "SpatialFrequency")
    MEL.connect_material_expressions(i_speed, "", mask, "TravelSpeed")
    MEL.connect_material_expressions(i_seed, "", mask, "HueSeed")
    MEL.connect_material_expressions(i_amt, "", mask, "ResponseAmount")
    MEL.connect_material_expressions(time, "", mask, "Time")

    color = custom_node(mf, COLOR_CODE, "MF_MelodiaWindHueReveal color",
                        ["BaseColor", "RevealTint", "Mask"],
                        -1100, 300, unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    MEL.connect_material_expressions(i_base, "", color, "BaseColor")
    MEL.connect_material_expressions(i_tint, "", color, "RevealTint")
    MEL.connect_material_expressions(mask, "", color, "Mask")

    o_color = fn_output(mf, "Color", -700, 300)
    MEL.connect_material_expressions(color, "", o_color, "")

    # The mask is published too: Niagara petals/motes and the sparkle ceiling
    # ride the same wave rather than computing a second, drifting one.
    o_mask = fn_output(mf, "RevealMask", -700, 560)
    MEL.connect_material_expressions(mask, "", o_mask, "")

    return {"mask": str(mask.get_name()), "color": str(color.get_name())}


def main() -> dict:
    mf, created = ensure_function()
    nodes = build(mf)
    try:
        MEL.recompile_material(mf) if hasattr(MEL, "recompile_material") else None
    except Exception:
        pass
    saved = False
    try:
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mf, False))
    except TypeError:
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mf))

    # Verify by re-reading the asset, not by trusting the build's own returns.
    reread = unreal.EditorAssetLibrary.load_asset(MF_PATH)
    exprs = list(MEL.get_material_function_expressions(reread)) \
        if hasattr(MEL, "get_material_function_expressions") else []
    inputs = sorted(str(e.get_editor_property("input_name")) for e in exprs
                    if isinstance(e, unreal.MaterialExpressionFunctionInput))
    outputs = sorted(str(e.get_editor_property("output_name")) for e in exprs
                     if isinstance(e, unreal.MaterialExpressionFunctionOutput))
    customs = [e for e in exprs if isinstance(e, unreal.MaterialExpressionCustom)]

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "brief": "MUSE_LIVING_FLOWER_FIELD_TECHNICAL_BRIEF_2026-09-16 P3",
        "asset": MF_PATH,
        "created": created,
        "saved": saved,
        "nodes": nodes,
        "expression_count": len(exprs),
        "inputs": inputs,
        "outputs": outputs,
        "custom_nodes": len(customs),
        "duplicate_inputs": sorted({n for n in inputs if inputs.count(n) > 1}),
        "expect_inputs": ["BaseColor", "PerInstanceHueSeed", "ResponseAmount",
                          "RevealTint", "SpatialFrequency", "TravelSpeed",
                          "WindDirection", "WindStrength"],
        "expect_outputs": ["Color", "RevealMask"],
    }
    report["ok"] = (inputs == report["expect_inputs"]
                    and outputs == report["expect_outputs"]
                    and len(customs) == 2
                    and not report["duplicate_inputs"]
                    and saved)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
