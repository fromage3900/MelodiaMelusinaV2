"""Parameter groups for M_Master_Toon_Landscape_HeightBlend.

Headless:
  python Content/Python/organize_landscape_groups.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

GROUPS: list[tuple[str, list[str]]] = [
    ("01 | Palette", ["RockTint", "GrassTint", "MudTint", "SnowTint", "PathTint", "WaterAlignTint"]),
    ("02 | Blend", [
        "HeightBlendStrength", "GrassAmount", "MudAmount", "SlopeSharpness",
        "bUsePaintedLayers", "bUseLandscapeUV", "LandscapeUVScale",
    ]),
    ("03 | Triplanar", ["TriplanarTiling", "TriplanarBlend", "TriplanarSlopeStart", "TriplanarSlopeEnd"]),
    ("04 | Textures", [
        "Rock_Albedo", "Rock_Normal", "Rock_Height",
        "Rock_ORM",
        "Grass_Albedo", "Grass_Normal", "Grass_Height",
        "Grass_ORM",
        "Mud_Albedo", "Mud_Normal", "Mud_Height",
        "Mud_ORM", "Path_Albedo", "Path_Normal", "Path_Height", "Path_ORM",
        "PathMask", "SparkleMask",
    ]),
    ("05 | Surface", [
        "Roughness", "RockRoughness", "GrassRoughness", "MudRoughness",
        "NormalStrength", "Wetness", "WetRoughness", "bUseLayerORM",
    ]),
    ("06 | Macro", ["MacroStrength", "MacroScale", "RockMacroStrength", "GrassMacroStrength", "MudMacroStrength", "PathMacroStrength"]),
    ("07 | Snow", ["SnowStrength", "SnowUpBias"]),
    ("08 | Path", ["PathWearStrength", "PathEdgeStrength"]),
    ("09 | Shore", ["ShoreWetnessBoost", "ShoreColorDarken", "WaterPaletteAlign"]),
    ("10 | Nikki Rim & Glow", [
        "bNikkiFast", "bNikkiHero", "RimColor", "RimWidth", "RimIntensity",
        "GlowIntensity", "BloomBoost",
    ]),
    ("11 | Nikki Sparkle", [
        "SparkleIntensity", "SparkleThreshold", "SparkleColor",
    ]),
    ("12 | Nikki Iridescence & Sheen", [
        "PastelLift", "DreamTint", "DreamSaturation", "DreamContrast", "DreamShadowLift",
        "Iridescence", "IridescenceTint", "IridescencePower", "FabricSheen", "SheenTint",
    ]),
    ("13 | Audio Reactive", ["AudioReactiveStrength"]),
    ("14 | Distance Detail", ["DetailNormal", "NearDetailStrength", "NearDetailStart", "NearDetailEnd"]),
    ("15 | Distance Atmosphere", ["FarAtmosphereStrength", "FarAtmosphereStart", "FarAtmosphereEnd", "FarAtmosphereColor"]),
    ("16 | Wonder Mask", ["WonderStrength", "WonderPalette", "WonderSparkleBoost"]),
    ("17 | Quality Tier", ["bLandscapeHeroTier", "bLandscapeFastTier"]),
    ("18 | Debug", ["bLandscapeDebugMasks", "bLandscapeDebugHeight", "bLandscapeDebugPath", "bLandscapeDebugSlope", "bLandscapeDebugDistance", "bLandscapeDebugWonder"]),
]

PARAM_META: dict[str, tuple[str, int]] = {}
for gi, (label, names) in enumerate(GROUPS):
    for pi, name in enumerate(names):
        PARAM_META[name] = (label, gi * 100 + pi)


def organize() -> None:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        unreal.log_error("[OrganizeLandscape] master missing")
        return

    m = unreal.load_asset(f"{MASTER}.M_Master_Toon_Landscape_HeightBlend")
    set_count, unmapped = 0, []
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        pname = None
        for prop in ("parameter_name", "ParameterName"):
            try:
                raw = expr.get_editor_property(prop)
                if raw:
                    pname = str(raw)
                    break
            except Exception:
                continue
        if not pname:
            continue
        meta = PARAM_META.get(pname)
        if not meta:
            unmapped.append(pname)
            continue
        group, prio = meta
        try:
            expr.set_editor_property("group", group)
            expr.set_editor_property("sort_priority", prio)
            set_count += 1
        except Exception as exc:
            unreal.log_warning(f"[OrganizeLandscape] {pname}: {exc}")

    unreal.MaterialEditingLibrary.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    print(f"ORGANIZE_LANDSCAPE_OK grouped={set_count} unmapped={sorted(set(unmapped))}")


def main() -> int:
    try:
        import unreal  # noqa: F401
        organize()
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "organize_landscape_groups.log"
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/organize_landscape_groups.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
