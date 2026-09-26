"""Glassgarden WP recreate - Melodia new_level(is_partitioned_world=True)."""
import unreal, json, time, shutil
from pathlib import Path

LEVEL = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/LV_Glassgarden_Shoals"
LEVEL_DIR = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype"
SCRATCH = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/_GG_WP_Scratch"
SEAABOVE = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
out = {"steps": {}}

def editor_world():
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            w = ues.get_editor_world()
            if w:
                return w
    except Exception:
        pass
    return unreal.EditorLevelLibrary.get_editor_world()

def disk_paths(level_path):
    rel = level_path.removeprefix("/Game/")
    base = PROJECT_ROOT / "Content" / rel.replace("/", "\\")
    return [base.with_suffix(ext) for ext in (".umap", ".uasset")]

def external_actors_dir(level_path):
    rel = level_path.removeprefix("/Game/").replace("/", "\\")
    return PROJECT_ROOT / "Content" / "__ExternalActors__" / rel

def is_wp(world, level_path=None):
    if not world:
        return False
    if level_path:
        ext = external_actors_dir(level_path)
        if ext.is_dir() and any(ext.rglob("*.uasset")):
            return True
    try:
        bounds = unreal.WorldPartitionBlueprintLibrary.get_editor_world_bounds()
        if bounds and bounds.is_valid:
            return True
    except Exception:
        pass
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for a in (eas.get_all_level_actors() or []):
            if a.get_class().get_name() in ("WorldDataLayers", "WorldPartitionMiniMap", "WorldPartitionReplay"):
                return True
    except Exception:
        pass
    return False

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = editor_world()
cur = w.get_path_name().split(".")[0] if w else None
out["open_before"] = cur
if cur == SEAABOVE:
    out["error"] = "Refusing recreate while SeaAbove open"
    print(json.dumps(out))
else:
    if not unreal.EditorAssetLibrary.does_directory_exist(LEVEL_DIR):
        unreal.EditorAssetLibrary.make_directory(LEVEL_DIR)
    scratch_on_disk = any(p.is_file() for p in disk_paths(SCRATCH))
    if scratch_on_disk and unreal.EditorAssetLibrary.does_asset_exist(SCRATCH):
        les.load_level(SCRATCH)
        out["steps"]["park"] = {"action": "load_scratch"}
    else:
        ok = les.new_level(SCRATCH, is_partitioned_world=False)
        out["steps"]["park"] = {"action": "new_scratch", "ok": bool(ok)}
        try:
            unreal.EditorLevelLibrary.save_current_level()
        except Exception:
            pass
    w = editor_world()
    out["steps"]["park"]["open"] = w.get_path_name().split(".")[0] if w else None

    purge = {"delete_asset": False, "disk_removed": [], "external_actors_removed": False}
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        purge["delete_asset"] = bool(unreal.EditorAssetLibrary.delete_asset(LEVEL))
    for path in disk_paths(LEVEL):
        if path.is_file():
            path.unlink()
            purge["disk_removed"].append(str(path))
    ext_dir = external_actors_dir(LEVEL)
    if ext_dir.is_dir():
        shutil.rmtree(ext_dir, ignore_errors=True)
        purge["external_actors_removed"] = True
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, False)
    except Exception as e:
        purge["save_dirty_note"] = str(e)[:200]
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([LEVEL_DIR], True)
    except Exception:
        pass
    time.sleep(0.35)
    out["steps"]["purge"] = purge

    on_disk = any(p.is_file() for p in disk_paths(LEVEL))
    in_reg = unreal.EditorAssetLibrary.does_asset_exist(LEVEL)
    if on_disk or in_reg:
        out["steps"]["create"] = {"error": "still present", "on_disk": on_disk, "in_reg": in_reg}
    else:
        ok = les.new_level(LEVEL, is_partitioned_world=True)
        w = editor_world()
        create = {
            "new_level_ok": bool(ok),
            "method": "new_level(is_partitioned_world=True)",
            "world_partition": is_wp(w, LEVEL),
            "open": w.get_path_name().split(".")[0] if w else None,
        }
        try:
            create["save_current"] = bool(unreal.EditorLevelLibrary.save_current_level())
        except Exception as e:
            create["save_current_error"] = str(e)[:200]
        try:
            create["save_asset"] = bool(unreal.EditorAssetLibrary.save_asset(LEVEL, only_if_is_dirty=False))
        except Exception as e:
            create["save_asset_error"] = str(e)[:200]
        create["world_partition_after_save"] = is_wp(editor_world(), LEVEL)
        create["external_actors_dir_exists"] = external_actors_dir(LEVEL).is_dir()
        ext_files = list(external_actors_dir(LEVEL).rglob("*.uasset")) if external_actors_dir(LEVEL).is_dir() else []
        create["external_actor_uasset_count"] = len(ext_files)
        actors = [{"label": a.get_actor_label(), "class": a.get_class().get_name()} for a in (eas.get_all_level_actors() or [])]
        create["actors_after_create"] = actors
        create["actor_count_after_create"] = len(actors)
        out["steps"]["create"] = create
    print(json.dumps(out, default=str))
