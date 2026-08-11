"""Post-rebuild integrity gate for the safe landscape master.

Run in the same closed-editor commandlet session after
rebuild_landscape_safe_fallback.py.  It rejects the exact graph conditions
that caused the current default-material fallback: empty TextureSample nodes,
material-function dependencies, and missing paint layers.  UE shader compiler
messages remain authoritative and are emitted to the commandlet log.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_safe_compile_gate.json"
LAYERS = {"Rock", "Grass", "Mud", "Path"}


def _object_path(path: str) -> str:
    package = path.split(".", 1)[0]
    return f"{package}.{package.rsplit('/', 1)[-1]}"


def main() -> int:
    import unreal

    material = unreal.load_asset(_object_path(MASTER))
    checks: list[dict[str, object]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    check("master loads", bool(material), MASTER)
    if not material:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps({"checks": checks}, indent=2), encoding="utf-8")
        return 1

    expressions = unreal.MaterialEditingLibrary.get_material_expressions(material) or []
    function_calls = []
    texture_samples = []
    blend_layers: set[str] = set()
    for expression in expressions:
        type_name = type(expression).__name__
        if "MaterialFunctionCall" in type_name:
            function_calls.append(expression.get_name())
        if "TextureSample" in type_name:
            texture = None
            try:
                texture = expression.get_editor_property("texture")
            except Exception:
                pass
            texture_samples.append({"node": expression.get_name(), "texture": texture.get_path_name() if texture else ""})
        if type_name == "MaterialExpressionLandscapeLayerBlend":
            for layer in expression.get_editor_property("layers") or []:
                try:
                    blend_layers.add(str(layer.get_editor_property("layer_name")))
                except Exception:
                    pass

    check("no material function calls", not function_calls, ", ".join(function_calls))
    check("all texture samples have defaults", all(item["texture"] for item in texture_samples), json.dumps(texture_samples))
    check("paint layers intact", LAYERS.issubset(blend_layers), f"found={sorted(blend_layers)}")
    check("three layer blends", sum(type(expr).__name__ == "MaterialExpressionLandscapeLayerBlend" for expr in expressions) == 3)

    # Force shader compilation after structural validation.  Any compiler error
    # is printed by UE to this commandlet's log and fails the external log gate.
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "checks": checks,
        "passed": sum(1 for item in checks if item["ok"]),
        "total": len(checks),
    }
    result["all_ok"] = result["passed"] == result["total"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"LANDSCAPE_SAFE_COMPILE_GATE passed={result['passed']}/{result['total']} all_ok={result['all_ok']}")
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
