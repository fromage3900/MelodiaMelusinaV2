"""Small diagnostic for locating authored Landscape output chains before patching."""

import json
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "landscape_graph_roots.json"
PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend.M_Master_Toon_Landscape_HeightBlend"


def describe_expression_input(value):
    result = {"type": type(value).__name__}
    for prop in ("expression", "output_index", "mask", "use_constant", "constant"):
        try:
            raw = value.get_editor_property(prop)
            result[prop] = raw.get_name() if hasattr(raw, "get_name") and raw else str(raw)
        except Exception:
            pass
    return result


material = unreal.load_asset(PATH)
if not material:
    raise RuntimeError(PATH)

editor_data = material.get_editor_property("editor_only_data")
roots = {}
for name in ("base_color", "normal", "roughness", "ambient_occlusion", "emissive_color", "front_material"):
    try:
        roots[name] = describe_expression_input(editor_data.get_editor_property(name))
    except Exception as exc:
        roots[name] = {"error": str(exc)}

expressions = []
toon_inputs = []
for expr in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
    record = {"name": expr.get_name(), "class": type(expr).__name__}
    for prop in ("parameter_name", "material_function"):
        try:
            raw = expr.get_editor_property(prop)
            record[prop] = raw.get_name() if hasattr(raw, "get_name") and raw else str(raw)
        except Exception:
            pass
    expressions.append(record)
    if type(expr).__name__ == "MaterialExpressionSubstrateToonBSDF":
        try:
            names = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expr))
            inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expr))
            toon_inputs.append({
                "name": expr.get_name(),
                "pins": [
                    {
                        "pin": names[index] if index < len(names) else str(index),
                        "source": source.get_name() if source else None,
                        "class": type(source).__name__ if source else None,
                    }
                    for index, source in enumerate(inputs)
                ],
            })
        except Exception as exc:
            toon_inputs.append({"name": expr.get_name(), "error": str(exc)})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"roots": roots, "toon_inputs": toon_inputs, "expressions": expressions}, indent=2), encoding="utf-8")
print(f"LANDSCAPE_ROOTS expressions={len(expressions)}")
