"""Create the physical-surface assets used by terrain painting.

Run only with Unreal Editor closed or from a controlled editor session.  The
surface names are declared in Config/DefaultEngine.ini and must stay stable for
footsteps, landings, VFX, decals, and acoustic traces.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
DEST_DIR = "/Game/Melodia/Art/Materials/Landscape/PhysicalMaterials"

SURFACES = (
    ("PM_Terrain_Grass", "SURFACE_TYPE1"),
    ("PM_Terrain_Soil", "SURFACE_TYPE2"),
    ("PM_Terrain_Stone", "SURFACE_TYPE3"),
    ("PM_Terrain_Path", "SURFACE_TYPE4"),
    ("PM_Terrain_WetGround", "SURFACE_TYPE5"),
)


def build() -> None:
    import unreal

    unreal.EditorAssetLibrary.make_directory(DEST_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for name, enum_name in SURFACES:
        asset_path = f"{DEST_DIR}/{name}"
        physical = unreal.load_asset(f"{asset_path}.{name}")
        if not physical:
            physical = tools.create_asset(
                name, DEST_DIR, unreal.PhysicalMaterial, unreal.PhysicalMaterialFactoryNew()
            )
        if not physical:
            raise RuntimeError(f"Could not create {asset_path}")
        surface = getattr(unreal.PhysicalSurface, enum_name)
        physical.set_editor_property("surface_type", surface)
        unreal.EditorAssetLibrary.save_loaded_asset(physical, only_if_is_dirty=False)
    print(f"LANDSCAPE_PHYSICS_OK count={len(SURFACES)}")


def main() -> int:
    try:
        import unreal  # noqa: F401
        build()
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: UnrealEditor-Cmd not found: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_landscape_surface_physics.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
