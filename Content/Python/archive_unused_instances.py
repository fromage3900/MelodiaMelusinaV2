"""Archive legacy MI_Universal_* instances not in the curated starter set.

Moves everything under /Game/EnvSandbox/Materials/Instances/Environment/** that
isn't a starter alias into /Game/EnvSandbox/Materials/Instances/_Archive/** (same
relative subfolder). Does NOT delete uassets. Does NOT touch Instances/Showcase
(starter set) or Instances/Sakura (scene kit).

Run in-editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/archive_unused_instances.py"
"""
from __future__ import annotations

import unreal

from starter_instances import ARCHIVE_ROOT, LEGACY_ALIASES, LEGACY_ENV_DIR, STARTER_NAMES

ROOT = LEGACY_ENV_DIR
SHOWCASE_ROOT = "/Game/EnvSandbox/Materials/Instances/Showcase"

# Legacy names that map to starters — archive these too once Showcase exists
DEPRECATED_LEGACY = set(LEGACY_ALIASES.keys())

eal = unreal.EditorAssetLibrary


def main():
    asset_paths = eal.list_assets(ROOT, recursive=True, include_folder=False)
    moved, kept, skipped = [], [], []

    for asset_path in asset_paths:
        package_path = asset_path.split(".")[0]
        name = package_path.rsplit("/", 1)[-1]

        if not name.startswith("MI_"):
            continue

        # Starters live in Showcase; anything still in Environment is legacy
        if name in STARTER_NAMES:
            kept.append(name)
            continue

        if package_path.startswith(ARCHIVE_ROOT):
            skipped.append(name)
            continue

        rel_dir = package_path[len(ROOT):].rsplit("/", 1)[0]
        dest_dir = ARCHIVE_ROOT + rel_dir
        dest_path = f"{dest_dir}/{name}"

        if eal.does_asset_exist(dest_path):
            unreal.log_warning(f"[Archive] {name}: destination already exists, skipping")
            skipped.append(name)
            continue

        if not eal.does_directory_exist(dest_dir):
            eal.make_directory(dest_dir)

        ok = eal.rename_asset(package_path, dest_path)
        if ok:
            moved.append(name)
        else:
            unreal.log_warning(f"[Archive] failed to move {name}")
            skipped.append(name)

    unreal.log(
        f"[Archive] moved={len(moved)} kept={len(kept)} skipped={len(skipped)} "
        f"(starters={sorted(STARTER_NAMES)})"
    )
    print(f"ARCHIVE_RESULT moved={len(moved)} kept={sorted(kept)} skipped={len(skipped)}")
    if DEPRECATED_LEGACY:
        print(f"Deprecated legacy names (use Showcase starters): {sorted(DEPRECATED_LEGACY)}")
    print(f"MOVED: {sorted(moved)}")


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
        main()
    except ImportError:
        import subprocess
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        ue = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
        if not ue.exists():
            raise SystemExit(1)
        cmd = [
            str(ue),
            str(root / "BS_GodFile.uproject"),
            f"-ExecutePythonScript={(root / 'Content/Python/archive_unused_instances.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        raise SystemExit(subprocess.run(cmd, cwd=str(root)).returncode)
