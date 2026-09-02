"""Repair M_PP_MelodiaInk custom node under-wiring (defect #2, 2026-08-29 audit).

Audit finding: the Custom node declares 42 inputs, 38 connected. The gap names
cited: "SceneColor, cR, cB, smeared" — SceneColor was later confirmed present,
so the live missing set is cR, cB, smeared (+1 unknown found at runtime).

Strategy (defensive, because the live graph is the only truth):
  1. DIAGNOSE — enumerate every Custom node in the master, list its declared
     inputs and per-input connection state, write the full map to the audit.
  2. RECONNECT — for each unconnected input, prefer an existing node whose
     desc/parameter_name matches; otherwise create a sane default:
       float-ish inputs -> Constant (0.0)
       float3/color     -> Constant3Vector (neutral 0.5 grey)
       float4           -> Constant4Vector (0,0,0,0)
     Defaults are tagged "InkFix:" and recorded.
  3. VERIFY — recount connections, recompile, save, report compile stats delta.

Idempotent: InkFix:-tagged nodes are cleaned before reconnecting.

Run in the UE editor (Monolith run_python): repair_melodia_ink.main()
Writes: Saved/Audit/melodia_ink_repair_2026-08-29.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

CANDIDATE_MASTERS = [
    # registry-verified canonical location (2026-08-29)
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk",
    "/Game/Melodia/_PROJECT/04_Materials/M_PP_MelodiaInk",
    "/Game/EnvSandbox/Materials/Masters/M_PP_MelodiaInk",
]
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "melodia_ink_repair_2026-08-29.json"
TAG = "InkFix:"

MEL = unreal.MaterialEditingLibrary


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[InkFix] {message}")


def _load_master():
    for path in CANDIDATE_MASTERS:
        m = unreal.EditorAssetLibrary.load_asset(path)
        if m is not None:
            return m, path
    raise RuntimeError(f"M_PP_MelodiaInk not found at any candidate path: {CANDIDATE_MASTERS}")


def _input_map(material, node):
    """{input_name: source_expr_or_None} for a material expression node."""
    result = {}
    try:
        names = MEL.get_material_expression_input_names(node)
        inputs = MEL.get_inputs_for_material_expression(material, node)
        for i, n in enumerate(names):
            result[n] = inputs[i] if i < len(inputs) else None
    except Exception as exc:
        _log(f"input map failed for {node.get_name()}: {exc}")
    return result


def _declared_inputs(node):
    """Declared Custom-input names (the pins the HLSL expects)."""
    names = []
    try:
        for ci in (_get(node, "inputs", None) or []):
            names.append(str(_get(ci, "input_name", "")))
    except Exception as exc:
        _log(f"declared inputs read failed: {exc}")
    return names


def _default_expression(material, input_name, x, y):
    """Create the sane default expression for a missing input."""
    cls = unreal.MaterialExpressionConstant
    node = MEL.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + input_name)
    lowered = input_name.lower()
    try:
        if any(k in lowered for k in ("color", "cr", "cb", "tint", "hue")):
            cls3 = unreal.MaterialExpressionConstant3Vector
            node = MEL.create_material_expression(material, cls3, x, y)
            _set(node, "desc", TAG + input_name)
            _set(node, "constant", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
        elif "smeared" in lowered or "scene" in lowered:
            cls4 = unreal.MaterialExpressionConstant4Vector
            node = MEL.create_material_expression(material, cls4, x, y)
            _set(node, "desc", TAG + input_name)
            _set(node, "constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
        else:
            _set(node, "constant", 0.0)
    except Exception as exc:
        _log(f"default creation fallback for {input_name}: {exc}")
    return node


def _find_existing_match(material, input_name):
    lowered = input_name.lower()
    for e in MEL.get_material_expressions(material) or []:
        desc = str(_get(e, "desc", "")).lower()
        pname = str(_get(e, "parameter_name", "")).lower()
        if not desc and not pname:
            continue
        if input_name.lower() in (desc, pname) or \
           (lowered == "smeared" and "smear" in (desc + pname)):
            return e
    return None


def repair_master(material, master_path):
    exprs = list(MEL.get_material_expressions(material) or [])
    customs = [e for e in exprs if type(e).__name__ == "MaterialExpressionCustom"]
    if not customs:
        raise RuntimeError("no Custom node found in M_PP_MelodiaInk")

    report = {"master": master_path, "custom_nodes": []}
    for node in customs:
        declared = _declared_inputs(node)
        connected = _input_map(material, node)
        before = {n: (connected.get(n) is not None) for n in declared}
        missing = [n for n in declared if not before.get(n, False)]

        entry = {
            "node": node.get_name(),
            "declared_count": len(declared),
            "before_connected": sum(1 for v in before.values() if v),
            "missing_before": missing,
            "fixed": [],
            "defaults_created": [],
        }
        _log(f"{node.get_name()}: {len(declared)} declared, "
             f"{entry['before_connected']} connected, missing={missing}")

        # clean prior InkFix defaults
        for e in list(exprs):
            if str(_get(e, "desc", "")).startswith(TAG):
                try:
                    MEL.delete_material_expression(material, e)
                except Exception:
                    pass

        y = 3000
        for n in missing:
            src = _find_existing_match(material, n)
            origin = "existing"
            if src is None:
                src = _default_expression(material, n, 3000, y)
                y += 180
                origin = "default"
                entry["defaults_created"].append(n)
            try:
                if not MEL.connect_material_expressions(src, "", node, n):
                    raise RuntimeError(f"connect returned False for {n}")
                entry["fixed"].append({"input": n, "source": origin})
                _log(f"connected {n} <- {origin} ({src.get_name()})")
            except Exception as exc:
                _log(f"FAILED to connect {n}: {exc}")
                entry["fixed"].append({"input": n, "error": str(exc)})

        # verify + recompile
        after = _input_map(material, node)
        entry["after_connected"] = sum(1 for n in declared if after.get(n) is not None)
        entry["missing_after"] = [n for n in declared if after.get(n) is None]
        try:
            MEL.recompile_material(material)
            entry["recompiled"] = True
        except Exception as exc:
            entry["recompiled"] = False
            entry["recompile_error"] = str(exc)
        report["custom_nodes"].append(entry)

    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report["ok"] = all(not c.get("missing_after") for c in report["custom_nodes"])
    return report


def main():
    material, path = _load_master()
    report = repair_master(material, path)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _log(f"audit -> {OUT}")
    return report


if __name__ == "__main__":
    main()