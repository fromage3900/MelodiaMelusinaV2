"""Create demo showcase level for Ornamental Kitbash product.

Places all 15 SM_Orn_* meshes in a grid for beauty renders and store screenshots.

Run in Unreal Editor:
  py Content/Python/setup_ornament_demo_level.py
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal

from ornament_kitbash_catalog import DEMO_LEVEL, MESHES, ORNAMENT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "ornament_demo_level.json"

GRID_COLS = 5
SPACING_CM = 900.0


def _ensure_world() -> unreal.World:
    level_path = f"{DEMO_LEVEL}.{DEMO_LEVEL.split('/')[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_path):
        unreal.EditorLevelLibrary.new_level(level_path)
    unreal.EditorLevelLibrary.load_level(level_path)
    return unreal.EditorLevelLibrary.get_editor_world()


def _spawn_mesh(world: unreal.World, mesh_path: str, location: unreal.Vector, label: str) -> bool:
    mesh = unreal.load_asset(f"{mesh_path}.{mesh_path.split('/')[-1]}")
    if not mesh:
        return False
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        location,
        unreal.Rotator(0, 0, 0),
    )
    if not actor:
        return False
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_static_mesh(mesh)
    actor.set_actor_label(label)
    return True


def main() -> int:
    unreal.log("[OrnamentDemo] Building showcase level...")
    if not unreal.EditorAssetLibrary.does_directory_exist(ORNAMENT_DIR):
        unreal.EditorAssetLibrary.make_directory(ORNAMENT_DIR)

    demo_folder = DEMO_LEVEL.rsplit("/", 1)[0]
    if not unreal.EditorAssetLibrary.does_directory_exist(demo_folder):
        unreal.EditorAssetLibrary.make_directory(demo_folder)

    world = _ensure_world()
    placed: list[dict] = []
    missing: list[str] = []

    for index, spec in enumerate(MESHES):
        row = index // GRID_COLS
        col = index % GRID_COLS
        x = col * SPACING_CM
        y = row * SPACING_CM
        loc = unreal.Vector(x, y, 0.0)
        ok = _spawn_mesh(world, spec.ue_path, loc, spec.asset_name)
        if ok:
            placed.append({"asset": spec.asset_name, "location": [x, y, 0.0]})
        else:
            missing.append(spec.asset_name)

    unreal.EditorLevelLibrary.save_current_level()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": DEMO_LEVEL,
        "placed": len(placed),
        "missing": missing,
        "actors": placed,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[OrnamentDemo] Placed {len(placed)}/{len(MESHES)} -> {DEMO_LEVEL}")
    if missing:
        unreal.log_warning(f"[OrnamentDemo] Missing meshes: {', '.join(missing)}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
