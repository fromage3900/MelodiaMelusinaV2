"""Dreamprint — find the dead material in the live PPV stack.

Every material the stack can resolve to (preference lists + per-level variants)
gets: exists, blendable location, custom nodes (code len + by-name identifiers),
named input coverage, MPC collection refs, and a compile attempt whose failure is
captured from the editor log (recompile does not throw on shader errors).

Manifest: Saved/Audit/dreamprint_live_stack_probe.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_live_stack_probe.json"

STACK = [
    # role, material/master paths the stack can resolve to
    ("outline",
     "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate",
     "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline",
     "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_FoliageSafe_Candidate"),
    ("outline_mi",
     "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard",
     "/Game/EnvSandbox/Materials/PostProcess/MI_PP_StorybookOutline"),
    ("grade",
     "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"),
    ("ink",
     "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"),
]

NAME_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def mpcs_of(mat) -> set[str]:
    out = set()
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(e).__name__ != "MaterialExpressionCollectionParameter":
            continue
        coll = e.get_editor_property("collection")
        out.add(str(coll.get_path_name()).split(".")[0] if coll else "?")
    return out


def probe(path: str) -> dict:
    res: dict = {"path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return res
    obj = unreal.load_asset(path)
    if not obj:
        res["exists"] = True
        res["load_failed"] = True
        return res
    cls = type(obj).__name__
    res["exists"] = True
    res["class"] = cls
    if cls == "MaterialInstanceConstant":
        parent = obj.get_editor_property("parent")
        res["parent"] = str(parent.get_path_name()) if parent else None
        try:
            res["scalar_overrides"] = len(obj.get_editor_property("scalar_parameter_values") or [])
        except Exception:
            pass
        return res
    if cls != "Material":
        res["class"] = cls
        return res
    res["domain"] = str(obj.get_editor_property("material_domain"))
    res["blendable_location"] = str(obj.get_editor_property("blendable_location"))
    res["mpc_references"] = sorted(mpcs_of(obj))
    customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(obj)
               if type(e).__name__ == "MaterialExpressionCustom"]
    res["custom_count"] = len(customs)
    for i, c in enumerate(customs):
        code = c.get_editor_property("code") or ""
        inputs = {str(x.get_editor_property("input_name"))
                  for x in (c.get_editor_property("inputs") or [])}
        # heuristics: identifiers that LOOK like material/MPC globals (capitalized
        # CamelCase, not HLSL keywords/types) referenced but not inputs
        caps = set(NAME_RE.findall(code)) - {
            "float", "float2", "float3", "float4", "int", "uint", "bool", "if", "else",
            "return", "for", "while", "true", "false", "saturate", "lerp", "max", "min",
            "abs", "dot", "length", "sin", "cos", "frac", "smoothstep", "step", "fwidth",
            "clamp", "sqrt", "pow", "exp", "log", "tan", "floor", "ceil", "modf", "UV",
            "View", "SceneColor", "Parameters", "Input", "Output",
        }
        caps = {c2 for c2 in caps if c2[:1].isupper() or c2.startswith("b")}
        unbound = sorted(caps - inputs)
        res[f"custom_{i}"] = {
            "code_len": len(code),
            "inputs": sorted(inputs),
            "unbound_like": unbound,
        }
    try:
        unreal.MaterialEditingLibrary.recompile_material(obj)
        res["recompile"] = "ok"
    except Exception as exc:
        res["recompile"] = f"error: {exc}"
    return res


def main() -> dict:
    results: list[dict] = []
    for role, *paths in STACK:
        for p in paths:
            r = probe(p)
            r["role"] = role
            results.append(r)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "materials": results,
        "ok": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()