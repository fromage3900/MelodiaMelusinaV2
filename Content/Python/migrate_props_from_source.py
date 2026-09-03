"""Batch-migrate self-contained prop folders (mesh + material + textures per
subfolder) from another UE project's raw Content tree into this project via
filesystem copy + material-slot repair.

UE's native Content Browser "Migrate" action requires opening the SOURCE
project's editor. When that isn't available (e.g. scripting from a single
open editor instance), a raw filesystem copy works IF each prop's mesh,
material, and textures live together in one self-contained subfolder with
no external cross-references -- which is the case for both source libraries
this script targets (MagiciansLibraryEnvironm/Props, Melodia/Art/Meshes).

Raw copy does NOT rewrite baked-in package path references inside .uasset
binaries, so a copied StaticMesh's material slot still points at the old
project's package path and fails to resolve (shows as the WorldGridMaterial
fallback). This script repairs that: after copying a subfolder, if it
contains exactly one Material/MaterialInstance asset, every material slot
on every StaticMesh in that subfolder is reassigned to it.

Run: Tools -> Execute Python Script, or Output Log:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/migrate_props_from_source.py"
"""
import os
import shutil
import unreal

SOURCES = [
    (r"G:\ueprojects\MagiciansLibraryEnvironm\Content\MagicianLabatory\Source\Props",
     "MagiciansLibrary"),
    (r"G:\Melodia\Content\_PROJECT\Art\Meshes\Talisman\CablesPipes",
     "Melodia/CablesPipes"),
    (r"G:\Melodia\Content\_PROJECT\Art\Meshes\Talisman\Props",
     "Melodia/Props"),
]

# Flat source folders (loose .uasset files directly in the folder, no
# per-asset subfolder structure, typically simple primitives with no
# material dependency to repair).
FLAT_SOURCES = [
    (r"G:\Melodia\Content\_PROJECT\Art\Meshes\Geometry\Assets",
     "Melodia/Geometry"),
]
DEST_ROOT_DISK = r"G:\EnvironmentPortfolio\BS_GodFile\Content\Library\Migrated"
DEST_ROOT_GAME = "/Game/Library/Migrated"


def _copy_subfolder(src_dir: str, dest_dir: str) -> list[str]:
    os.makedirs(dest_dir, exist_ok=True)
    copied = []
    for f in os.listdir(src_dir):
        if f.lower().endswith(".uasset"):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(dest_dir, f))
            copied.append(f[:-len(".uasset")])
    return copied


def _repair_materials(game_folder: str, asset_names: list[str]) -> dict:
    result = {"meshes": [], "material": None, "repaired": 0}
    loaded = {}
    for name in asset_names:
        a = unreal.EditorAssetLibrary.load_asset(f"{game_folder}/{name}")
        if a is not None:
            loaded[name] = a

    materials = {n: a for n, a in loaded.items()
                 if a.get_class().get_name() in ("Material", "MaterialInstanceConstant")}
    meshes = {n: a for n, a in loaded.items() if a.get_class().get_name() == "StaticMesh"}
    result["meshes"] = list(meshes.keys())

    if len(materials) == 1:
        mat = next(iter(materials.values()))
        result["material"] = mat.get_path_name()
        for name, mesh in meshes.items():
            slots = mesh.get_editor_property("static_materials")
            for slot in slots:
                slot.set_editor_property("material_interface", mat)
            mesh.set_editor_property("static_materials", slots)
            unreal.EditorAssetLibrary.save_asset(f"{game_folder}/{name}")
            result["repaired"] += 1
    return result


def migrate_all(dry_run: bool = False) -> dict:
    report = {"folders": 0, "meshes_repaired": 0, "details": []}
    for src_root, namespace in SOURCES:
        if not os.path.isdir(src_root):
            unreal.log_warning(f"[Migrate] source not found: {src_root}")
            continue
        for entry in sorted(os.listdir(src_root)):
            src_dir = os.path.join(src_root, entry)
            if not os.path.isdir(src_dir):
                continue
            dest_disk = os.path.join(DEST_ROOT_DISK, namespace, entry)
            dest_game = f"{DEST_ROOT_GAME}/{namespace}/{entry}"

            if dry_run:
                n = len([f for f in os.listdir(src_dir) if f.lower().endswith(".uasset")])
                report["details"].append({"folder": entry, "namespace": namespace, "uasset_count": n})
                continue

            if os.path.isdir(dest_disk) and os.listdir(dest_disk):
                report["details"].append({"folder": entry, "namespace": namespace, "skipped": "already migrated"})
                continue

            names = _copy_subfolder(src_dir, dest_disk)
            if not names:
                continue
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            ar.scan_paths_synchronous([dest_game], force_rescan=True)
            fix = _repair_materials(dest_game, names)
            report["folders"] += 1
            report["meshes_repaired"] += fix["repaired"]
            report["details"].append({"folder": entry, "namespace": namespace, **fix})

    for src_root, namespace in FLAT_SOURCES:
        if not os.path.isdir(src_root):
            unreal.log_warning(f"[Migrate] source not found: {src_root}")
            continue
        dest_disk = os.path.join(DEST_ROOT_DISK, *namespace.split("/"))
        dest_game = f"{DEST_ROOT_GAME}/{namespace}"

        if dry_run:
            n = len([f for f in os.listdir(src_root) if f.lower().endswith(".uasset")])
            report["details"].append({"folder": namespace, "namespace": "flat", "uasset_count": n})
            continue

        names = _copy_subfolder(src_root, dest_disk)
        if names:
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            ar.scan_paths_synchronous([dest_game], force_rescan=True)
            report["folders"] += 1
            report["details"].append({"folder": namespace, "namespace": "flat", "meshes": names})
    return report


if __name__ == "__main__":
    import json
    r = migrate_all(dry_run=False)
    print(json.dumps(r, indent=2))
