"""AAA audit for Zen (15) + Trimsheet (4) material instances — masks and layer textures.

Headless:
  python Content/Python/audit_zen_trimsheet.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zen_trimsheet_aaa_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

ZEN_TEXTURE_PARAMS = ("MotifMask", "FairyGlyphMask", "SparkleMask", "Albedo", "NormalMap")
TRIMSHEET_TEXTURE_PARAMS = (
    "Albedo",
    "NormalMap",
    "ORM",
    "HeightMap",
    "LayerB_Albedo",
    "LayerB_NormalMap",
    "LayerB_ORM",
    "LayerB_HeightMap",
    "DetailNormal",
)


def _audit_in_ue() -> dict:
    import unreal
    import material_lib as lib
    from zen_instances import ZEN_INSTANCES

    try:
        from setup_trimsheet_instances import all_trimsheet_specs

        TRIMSHEET_INSTANCES = all_trimsheet_specs()
    except ImportError:
        TRIMSHEET_INSTANCES = []

    checks: list[dict] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": label, "ok": ok, "detail": detail})

    for spec in ZEN_INSTANCES:
        name = spec["name"]
        folder = spec.get("folder", "/Game/EnvSandbox/Materials/Instances/Environment/Zen")
        path = f"{folder}/{name}.{name}"
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        check(f"zen asset {name}", exists, path)
        if not exists:
            continue
        mi = unreal.load_asset(path)
        parent = mi.get_editor_property("parent") if mi else None
        parent_ok = parent and str(parent.get_path_name()).startswith(MASTER)
        check(f"zen parent {name}", bool(parent_ok), str(parent) if parent else "")
        tex_spec = spec.get("textures") or {}
        scalars = spec.get("scalars") or {}
        for pname in ZEN_TEXTURE_PARAMS:
            if pname == "SparkleMask" and float(scalars.get("SparkleIntensity", 0)) <= 0:
                continue
            if pname in ("Albedo", "NormalMap") and float(scalars.get("TextureWeight", 1)) < 0.35:
                continue
            if pname not in tex_spec and pname not in ("Albedo", "NormalMap"):
                continue
            import portfolio_texture_catalog as catalog

            spec_map = catalog.resolve_instance_texture_map(name)
            candidates = spec_map.get(pname)
            if not candidates and pname in tex_spec:
                try:
                    import portfolio_alpha_paths as alphas
                    from apply_theme_instances import _resolve_texture_keys

                    wires = _resolve_texture_keys(spec, alphas)
                    candidates = wires.get(pname)
                except Exception:
                    candidates = None
            if candidates:
                resolved = lib.resolve_texture_path(
                    candidates if isinstance(candidates, list) else [candidates]
                )
                check(f"zen {name}.{pname}", bool(resolved), resolved or str(candidates))
            elif pname in ("MotifMask", "FairyGlyphMask", "SparkleMask"):
                try:
                    import portfolio_alpha_paths as alphas
                    from apply_theme_instances import _resolve_texture_keys

                    wires = _resolve_texture_keys(spec, alphas)
                    key_candidates = wires.get(pname)
                    if key_candidates:
                        resolved = lib.resolve_texture_path(key_candidates)
                        check(f"zen {name}.{pname}", bool(resolved), resolved or str(key_candidates))
                    else:
                        check(f"zen {name}.{pname}", False, "no key rule")
                except Exception as exc:
                    check(f"zen {name}.{pname}", False, str(exc))

    for spec in TRIMSHEET_INSTANCES:
        name = spec["name"]
        trim_folder = spec.get(
            "folder",
            "/Game/EnvSandbox/Materials/Instances/Environment/Stylized",
        )
        path = f"{trim_folder}/{name}.{name}"
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        check(f"trimsheet asset {name}", exists, path)
        if not exists:
            continue
        mi = unreal.load_asset(path)
        parent = mi.get_editor_property("parent") if mi else None
        check(f"trimsheet parent {name}", bool(parent), str(parent) if parent else "")

        layer_a = spec.get("layer_a", "Base4K")
        layer_b = spec.get("layer_b", "CrackedToHell")
        if spec.get("trim_family") == "cloth":
            import cloth_trim_textures as trim_tex

            tex_maps = {**trim_tex.variant_maps(layer_a), **trim_tex.layer_b_maps(layer_b)}
        else:
            import zen_trim_textures as trim_tex

            tex_maps = {**trim_tex.variant_maps(layer_a), **trim_tex.layer_b_maps(layer_b)}

        for pname, tex_path in tex_maps.items():
            if pname in ("RoughnessMap", "MetallicMap", "MotifMask", "DetailNormal"):
                continue
            resolved = lib.resolve_texture_path([tex_path])
            check(f"trimsheet {name}.{pname}", bool(resolved), resolved or tex_path)

        blend_mode = 0.0
        try:
            if hasattr(unreal.MaterialEditingLibrary, "get_material_instance_scalar_parameter_value"):
                blend_mode = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
                    mi, "LayerBlendMode"
                )
        except Exception:
            pass
        check(
            f"trimsheet height lerp {name}",
            float(blend_mode) >= 1.0,
            f"LayerBlendMode={blend_mode}",
        )

    passed = sum(1 for c in checks if c["ok"])
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zen_count": len(ZEN_INSTANCES),
        "trimsheet_count": len(TRIMSHEET_INSTANCES),
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "all_ok": passed == len(checks) and len(checks) > 0,
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"ZEN_TRIMSHEET_AUDIT passed={report['passed']}/{report['total']} all_ok={report['all_ok']}")
        return 0 if report.get("all_ok") else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_zen_trimsheet.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
