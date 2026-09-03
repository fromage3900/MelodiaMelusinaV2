"""Export scene metadata from the currently loaded editor level.

Run in-editor:
  py Content/Python/scene_metadata_exporter.py

Output:
  Saved/Portfolio/Metadata/scene_metadata.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import portfolio_output_layout as portfolio_fs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = portfolio_fs.SCENE_METADATA_PATH


def _asset_path(obj) -> str | None:
    if not obj:
        return None
    try:
        return obj.get_path_name().split(".", 1)[0]
    except Exception:
        return None


def _get_engine_version() -> str | None:
    import unreal

    try:
        ver = unreal.SystemLibrary.get_engine_version()
        return f"{ver.major}.{ver.minor}.{ver.patch}"
    except Exception:
        pass
    try:
        ver = unreal.SystemLibrary.get_engine_version_string()
        return str(ver) if ver else None
    except Exception:
        return None


def _get_editor_world():
    """Return the editor world, preferring the UE 5.8 subsystem API."""
    import unreal

    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            world = ues.get_editor_world()
            if world:
                return world
    except Exception:
        pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _get_level_info() -> tuple[str | None, str | None]:
    import unreal

    level_name: str | None = None
    level_path: str | None = None
    try:
        world = _get_editor_world()
        unreal.log(f"[SceneMetadata] DIAG world={world!r}")
        if world:
            level = world.get_current_level()
            unreal.log(f"[SceneMetadata] DIAG current_level={level!r}")
            if level:
                outer = level.get_outer()
                unreal.log(f"[SceneMetadata] DIAG outer={outer!r}")
                if outer:
                    level_path = _asset_path(outer) or str(outer.get_path_name()).split(".", 1)[0]
                    level_name = outer.get_name()
    except Exception:
        import traceback
        unreal.log_warning(f"[SceneMetadata] level info unavailable:\n{traceback.format_exc()}")
    return level_name, level_path


def _classify_material(mat) -> str:
    import unreal

    try:
        if mat.is_a(unreal.MaterialInstance.static_class()):
            return "instance"
        if mat.is_a(unreal.Material.static_class()):
            return "material"
    except Exception:
        pass
    return "other"


def export_scene_metadata(map_path: str | None = None) -> dict:
    import unreal

    # Use hardcoded level path from generate_portfolio.py as fallback
    DEFAULT_LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
    DEFAULT_LEVEL_NAME = "L_SakuraPath"

    if map_path:
        try:
            unreal.EditorLoadingAndSavingUtils.load_map(map_path)
            unreal.log(f"[SceneMetadata] loaded map: {map_path}")
        except Exception as exc:
            unreal.log_warning(f"[SceneMetadata] failed to load map {map_path}: {exc}")

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not eas:
        raise RuntimeError("EditorActorSubsystem unavailable — run inside Unreal Editor")

    level_name, level_path = _get_level_info()
    
    # Fallback to known values if extraction fails
    if not level_name:
        level_name = DEFAULT_LEVEL_NAME
        unreal.log_warning(f"[SceneMetadata] Using fallback level_name: {level_name}")
    if not level_path:
        level_path = DEFAULT_LEVEL
        unreal.log_warning(f"[SceneMetadata] Using fallback level_path: {level_path}")
    static_mesh_actors: list[dict] = []
    materials_used: set[str] = set()
    material_instances: set[str] = set()

    all_actors = eas.get_all_level_actors() or []
    unreal.log(f"[SceneMetadata] DIAG total actors={len(all_actors)}")
    for actor in all_actors:
        try:
            if not actor.is_a(unreal.StaticMeshActor.static_class()):
                continue
        except Exception:
            continue

        comp = actor.static_mesh_component
        mesh_path = _asset_path(comp.get_static_mesh()) if comp else None
        slot_materials: list[str] = []

        if comp:
            try:
                slot_count = comp.get_num_materials()
            except Exception:
                slot_count = 0
            for slot in range(slot_count):
                mat = comp.get_material(slot)
                mat_path = _asset_path(mat)
                if not mat_path:
                    continue
                slot_materials.append(mat_path)
                materials_used.add(mat_path)
                if _classify_material(mat) == "instance":
                    material_instances.add(mat_path)

        static_mesh_actors.append(
            {
                "label": actor.get_actor_label(),
                "mesh": mesh_path,
                "materials": slot_materials,
            }
        )

    static_mesh_actors.sort(key=lambda entry: entry.get("label") or "")

    report = {
        "level_name": level_name,
        "level_path": level_path,
        "engine_version": _get_engine_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "static_mesh_actors": static_mesh_actors,
        "materials": sorted(materials_used),
        "material_instances": sorted(material_instances),
        "counts": {
            "static_mesh_actors": len(static_mesh_actors),
            "materials": len(materials_used),
            "material_instances": len(material_instances),
        },
    }
    return report


def write_scene_metadata(*, output_path: Path | None = None, map_path: str | None = None) -> Path:
    import unreal

    portfolio_fs.ensure_portfolio_layout()
    portfolio_fs.organize_portfolio_outputs()
    out = output_path or OUTPUT_PATH
    report = export_scene_metadata(map_path=map_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SceneMetadata] wrote {out}")
    return out


def main() -> None:
    import sys

    map_path = None
    for idx, arg in enumerate(sys.argv):
        if arg in ("--map", "--level") and idx + 1 < len(sys.argv):
            map_path = sys.argv[idx + 1]

    path = write_scene_metadata(map_path=map_path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
