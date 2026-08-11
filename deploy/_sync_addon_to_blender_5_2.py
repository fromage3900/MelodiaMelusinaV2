"""Deploy sync: copies deploy/ changes to Blender 5.2 addons folder.

Run this after editing any files in deploy/surreal_arch/ to keep
the live Blender 5.2 installation in sync.

Usage:
  python deploy/_sync_addon_to_blender_5_2.py
"""
import os
import shutil
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
ADDON_5_2 = os.path.join(
    os.environ.get("APPDATA", ""),
    "Blender Foundation", "Blender", "5.2", "scripts", "addons",
)

PACKAGES = {
    "surreal_arch": os.path.join(DEPLOY, "surreal_arch"),
    "surreal_os": os.path.join(DEPLOY, "surreal_os"),
    "surreal_world": os.path.join(DEPLOY, "surreal_world"),
    "surreal_greybox": os.path.join(DEPLOY, "surreal_greybox"),
}

MONOLITH_SRC = os.path.join(DEPLOY, "surreal_architecture_gen.py")
MONOLITH_DST = os.path.join(ADDON_5_2, "surreal_architecture_gen.py")


def sync():
    errors = []
    for name, src_dir in PACKAGES.items():
        dst_dir = os.path.join(ADDON_5_2, name)
        if not os.path.isdir(src_dir):
            errors.append(f"Source not found: {src_dir}")
            continue
        if os.path.isdir(dst_dir):
            shutil.rmtree(dst_dir, ignore_errors=True)
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"  {name}: synced {len(os.listdir(src_dir))} files")

    if os.path.isfile(MONOLITH_SRC):
        shutil.copy2(MONOLITH_SRC, MONOLITH_DST)
        print(f"  monolith: synced ({os.path.getsize(MONOLITH_SRC)} bytes)")

    # Clear all __pycache__ dirs in the addon
    for root, dirs, files in os.walk(ADDON_5_2):
        if "__pycache__" in dirs:
            pycache = os.path.join(root, "__pycache__")
            shutil.rmtree(pycache, ignore_errors=True)

    if errors:
        print(f"\nERRORS: {errors}")
        return False
    print(f"\nSynced all packages to Blender 5.2 addons: {ADDON_5_2}")
    return True


if __name__ == "__main__":
    sys.exit(0 if sync() else 1)
