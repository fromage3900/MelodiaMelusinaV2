"""Inject storybook enhancements into the V5 premium outline material.
Run via Monolith: editor_query.run_python with command='exec(open("Content/Python/inject_storybook_v5.py").read())'
"""
from __future__ import annotations
import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")

STORYBOOK = """
    // ---- STORYBOOK ENHANCEMENTS (triple-AAA dreamy ink) -------------------
    float2 paperInt = floor(uvC * 960.0);
    float paperHash = frac(sin(dot(paperInt, float2(12.9898, 78.233))) * 43758.5453);
    paperHash = frac(paperHash + sin(dot(paperInt + float2(39.346, 11.135), float2(12.9898, 78.233))) * 24634.6345);
    float paperGrain = lerp(1.0, paperHash, 0.12 * saturate(1.0 - silEdge * 1.5));
    ink *= paperGrain;
    float inkPool = 1.0 + 0.10 * creaseEdge * (1.0 - silEdge);
    ink *= inkPool;
    float3 paperColor = float3(0.94, 0.89, 0.81);
    float paperShow = 1.0 - saturate(edge * 2.5);
    ink = lerp(ink, paperColor, paperShow * 0.20);
    // -------------------------------------------------------------------------
"""

anchor = "return float4(ink, edge)"
if anchor in code:
    code = code.replace(anchor, STORYBOOK + anchor)
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print("OK - storybook block inserted before return")
else:
    print(f"FAIL - anchor not found in code")
    print(f"Code ends with: ...{code[-300:]}")
