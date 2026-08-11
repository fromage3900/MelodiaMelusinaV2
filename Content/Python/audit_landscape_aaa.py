"""AAA audit for M_Master_Toon_Landscape_HeightBlend — CC0 layers, Nikki switches, instances.

Headless:
  python Content/Python/audit_landscape_aaa.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_aaa_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
INST_DIR = "/Game/EnvSandbox/Materials/Instances/Landscape"
LAYER_DIR = "/Game/EnvSandbox/Materials/Landscape"
PHYSICAL_DIR = "/Game/Melodia/Art/Materials/Landscape/PhysicalMaterials"

EXPECTED_PHYSICAL = (
    ("PM_Terrain_Grass", "SURFACE_TYPE1"),
    ("PM_Terrain_Soil", "SURFACE_TYPE2"),
    ("PM_Terrain_Stone", "SURFACE_TYPE3"),
    ("PM_Terrain_Path", "SURFACE_TYPE4"),
    ("PM_Terrain_WetGround", "SURFACE_TYPE5"),
)
EXPECTED_LAYER_PHYSICAL = {
    "Rock": "PM_Terrain_Stone",
    "Grass": "PM_Terrain_Grass",
    "Mud": "PM_Terrain_Soil",
    "Path": "PM_Terrain_Path",
    "Wonder": "PM_Terrain_Grass",
}

REQUIRED_SWITCHES = (
    "bNikkiFast", "bNikkiHero", "bUsePaintedLayers",
    "bLandscapeHeroTier", "bLandscapeFastTier",
    "bLandscapeDebugMasks", "bLandscapeDebugHeight", "bLandscapeDebugPath",
    "bLandscapeDebugSlope", "bLandscapeDebugDistance", "bLandscapeDebugWonder",
)
REQUIRED_LAYERS = ("Rock", "Grass", "Mud", "Path")
REQUIRED_TEX = tuple(f"{layer}_{kind}" for layer in ("Rock", "Grass", "Mud") for kind in ("Albedo", "Normal", "Height"))
REQUIRED_TEX += tuple(f"{layer}_ORM" for layer in ("Rock", "Grass", "Mud", "Path"))
REQUIRED_TEX += ("PathMask", "Path_Albedo", "Path_Normal", "Path_Height")


def _audit_in_ue() -> dict:
    import unreal
    import material_lib as lib
    import portfolio_landscape_textures as lt
    from setup_landscape_height_blend import INSTANCES

    checks: list[dict] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": label, "ok": ok, "detail": detail})

    check("master exists", unreal.EditorAssetLibrary.does_asset_exist(MASTER), MASTER)
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        passed = 0
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "passed": passed,
            "total": len(checks),
            "all_ok": False,
        }

    mat = unreal.load_asset(f"{MASTER}.{MASTER.split('/')[-1]}")
    params: set[str] = set()
    switches: set[str] = set()
    functions: set[str] = set()
    has_audio_reactivity = False
    has_sakura_sparkle = False
    collection_bindings: list[dict[str, str]] = []
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if not expr:
            continue
        tname = type(expr).__name__
        if "StaticSwitch" in tname or "StaticBool" in tname:
            for prop in ("parameter_name", "ParameterName"):
                try:
                    switches.add(str(expr.get_editor_property(prop)))
                except Exception:
                    pass
        if "Parameter" in tname and "Function" not in tname:
            for prop in ("parameter_name", "ParameterName"):
                try:
                    params.add(str(expr.get_editor_property(prop)))
                except Exception:
                    pass
        if "MaterialFunctionCall" in tname:
            try:
                mf = expr.get_editor_property("material_function")
                if mf:
                    functions.add(mf.get_name())
            except Exception:
                pass
        if "CollectionParameter" in tname:
            try:
                collection = expr.get_editor_property("collection")
                parameter = str(expr.get_editor_property("parameter_name"))
                collection_name = collection.get_name() if collection else ""
                collection_bindings.append({"collection": collection_name, "parameter": parameter})
has_audio_reactivity = bool(
                    collection
                    and collection_name == "MPC_Melodia_Palette"
                    and parameter == "GlobalReactivity"
                ) or has_audio_reactivity
                has_sakura_sparkle = bool(
                    collection
                    and collection_name == "MPC_SakuraDream"
                    and parameter == "SparklePulse"
                ) or has_sakura_sparkle
            except Exception:
                pass

    for sw in REQUIRED_SWITCHES:
        check(f"switch {sw}", sw in switches, "present" if sw in switches else "missing")
    for tex in REQUIRED_TEX:
        check(f"texture param {tex}", tex in params, tex)
    check("PathMask param", "PathMask" in params)
    check("MF_LandscapeHeightCompete", any("LandscapeHeightCompete" in f for f in functions))
    check("MF_NikkiDreamGrade", any("NikkiDream" in f for f in functions))
    check("switch bUseLayerORM", "bUseLayerORM" in switches)
    check("audio reactivity collection", has_audio_reactivity, "MPC_Melodia_Palette.GlobalReactivity")
    check("Sakura sparkle collection", has_sakura_sparkle, "MPC_SakuraDream.SparklePulse")
    for param in (
        "TriplanarBlend", "TriplanarSlopeStart", "TriplanarSlopeEnd",
        "NearDetailStrength", "NearDetailStart", "NearDetailEnd",
        "FarAtmosphereStrength", "FarAtmosphereStart", "FarAtmosphereEnd",
        "WonderStrength", "WonderPalette", "WonderSparkleBoost", "PathEdgeStrength",
    ):
        check(f"storybook param {param}", param in params, param)

    for layer in REQUIRED_LAYERS:
        tex = lt.resolve_layer_textures(layer)
        for kind in ("Albedo", "Normal", "Height"):
            resolved = lib.resolve_texture_path(tex.get(kind, []))
            check(f"cc0 {layer}.{kind}", bool(resolved), resolved or "")

    for name, enum_name in EXPECTED_PHYSICAL:
        path = f"{PHYSICAL_DIR}/{name}.{name}"
        physical = unreal.load_asset(path)
        check(f"physical material {name}", bool(physical), path)
        if physical:
            expected_surface = getattr(unreal.PhysicalSurface, enum_name)
            actual_surface = physical.get_editor_property("surface_type")
            check(
                f"physical surface {name}",
                actual_surface == expected_surface,
                f"expected={expected_surface} actual={actual_surface}",
            )

    for layer, physical_name in EXPECTED_LAYER_PHYSICAL.items():
        path = f"{LAYER_DIR}/{layer}.{layer}"
        layer_info = unreal.load_asset(path)
        check(f"layer info {layer}", bool(layer_info), path)
        if layer_info:
            assigned = layer_info.get_editor_property("phys_material")
            assigned_name = assigned.get_name() if assigned else ""
            check(
                f"layer physical {layer}",
                assigned_name == physical_name,
                f"expected={physical_name} actual={assigned_name or 'None'}",
            )

    for spec in INSTANCES:
        name = spec["name"]
        path = f"{INST_DIR}/{name}.{name}"
        check(f"instance {name}", unreal.EditorAssetLibrary.does_asset_exist(path), path)

    passed = sum(1 for c in checks if c["ok"])
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "instance_count": len(INSTANCES),
        "collection_bindings": collection_bindings,
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
        print(f"LANDSCAPE_AAA passed={report['passed']}/{report['total']} all_ok={report['all_ok']}")
        return 0 if report.get("all_ok") else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_landscape_aaa.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
