"""Parameter groups for M_Water_Master_Grand_v6.

Headless:
  python Content/Python/organize_water_groups.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

GROUPS: list[tuple[str, list[str]]] = [
    ("01 | Waves", ["GerstnerScale", "WaveSpeed"]),
    ("02 | Surface", ["WaterRoughness", "Opacity", "RefractionStrength"]),
    ("03 | Caustics", ["CausticIntensity", "CausticTint"]),
    ("04 | Depth", ["WaterColorShallow", "WaterColorDeep", "DepthFadeDistance"]),
    ("05 | Magical", ["MagicalIntensity"]),
    ("06 | Shoreline", ["ShorelineWidth", "ShorelineFoam", "bUseShorelineUV"]),
]

PARAM_META: dict[str, tuple[str, int]] = {}
for gi, (label, names) in enumerate(GROUPS):
    for pi, name in enumerate(names):
        PARAM_META[name] = (label, gi * 100 + pi)


def organize() -> None:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        unreal.log_error("[OrganizeWater] master missing")
        return

    m = unreal.load_asset(f"{MASTER}.M_Water_Master_Grand_v6")
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
            unreal.log_warning(f"[OrganizeWater] {pname}: {exc}")

    unreal.MaterialEditingLibrary.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    print(f"ORGANIZE_WATER_OK grouped={set_count} unmapped={sorted(set(unmapped))}")


def main() -> int:
    try:
        import unreal  # noqa: F401
        organize()
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "organize_water_groups.log"
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/organize_water_groups.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
