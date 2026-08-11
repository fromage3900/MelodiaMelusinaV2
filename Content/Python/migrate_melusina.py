"""Migrate the ARP-rigged Melusina character from MelodiaMelusina_PROD into
this project via filesystem copy + registry scan + reference verification.

Same raw-copy approach as migrate_props_from_source.py (see its docstring for
why raw copy is the right tool when the source project's editor isn't open),
but shaped for a character folder: recursive copy including subfolders
(Animations/, Meshes/), not the flat per-prop layout that script targets.

Key structural fact (verified 2026-07-02): Melusina is ONE skeletal mesh
(SK_Melusina) with ~40 material slots -- the Meshes/ subfolder is those
per-slot materials plus SKM_character_rig* scene-import artifacts. The
materials MUST come along or every slot renders the fallback grid; the
SKM_character_rig* artifacts are a separate duplicate import and are
deliberately excluded.

Run inside the editor (Monolith run_python):
  import migrate_melusina
  migrate_melusina.migrate()
"""
import os
import shutil
import unreal

SRC_ROOT = r"G:\MelodiaMelusina\MelodiaMelusina_PRODUCTION\MelodiaMelusina_PROD\Content\Characters\Melusina"
# IMPORTANT: destination preserves the source project's /Game/Characters/Melusina
# package path. Raw copy does NOT rewrite baked-in references inside the .uassets
# (SK->slot materials, BP->SK, ABP->skeleton all reference /Game/Characters/Melusina/...),
# so landing at the identical game path is what makes them resolve. Confirmed live
# 2026-07-02: a first attempt at /Game/_PROJECT/Characters/Melusina left 0/35 material
# slots resolved; same copy at the original path resolves them.
DEST_ROOT_DISK = r"G:\EnvironmentPortfolio\BS_GodFile\Content\Characters\Melusina"
DEST_ROOT_GAME = "/Game/Characters/Melusina"

EXCLUDE_PREFIXES = ("SKM_character_rig", "SceneImport_SKM_character_rig")


def _copy_tree(src: str, dest: str) -> list[str]:
    copied = []
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dest_dir = dest if rel == "." else os.path.join(dest, rel)
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            if not f.lower().endswith((".uasset", ".uexp", ".ubulk")):
                continue
            if any(f.startswith(p) for p in EXCLUDE_PREFIXES):
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))
            copied.append(os.path.join(rel, f) if rel != "." else f)
    return copied


def migrate(force: bool = False) -> dict:
    report = {"copied": 0, "skipped": False, "sk_slots_total": 0, "sk_slots_resolved": 0}
    if os.path.isdir(DEST_ROOT_DISK) and os.listdir(DEST_ROOT_DISK) and not force:
        report["skipped"] = True
    else:
        files = _copy_tree(SRC_ROOT, DEST_ROOT_DISK)
        report["copied"] = len(files)

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_paths_synchronous([DEST_ROOT_GAME], force_rescan=True)

    sk = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT_GAME}/SK_Melusina")
    if sk is None:
        report["error"] = "SK_Melusina failed to load after copy+scan"
        return report
    mats = sk.get_editor_property("materials")
    report["sk_slots_total"] = len(mats)
    report["sk_slots_resolved"] = sum(
        1 for m in mats if m.get_editor_property("material_interface") is not None)

    for name in ("BP_Melusina", "ABP_Melusina", "IK_Melusina"):
        report[name] = unreal.EditorAssetLibrary.does_asset_exist(f"{DEST_ROOT_GAME}/{name}")
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(migrate(), indent=2))
