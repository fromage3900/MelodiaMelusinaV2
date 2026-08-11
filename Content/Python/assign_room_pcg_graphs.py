"""PCG M1 — assign existing PCG graphs to the 22 already-placed, empty
{level_name}_PCGVolume actors in the roguelike room maps.

These volumes were placed by setup_roguelike_dungeon.py::_create_room_level
(see that file, ~line 425) but never given a graph, so every roguelike room
has stood visually bare. This script does NOT create new PCG graphs or new
gameplay systems - it wires the 8 room archetypes (from the level_configs in
setup_roguelike_dungeon.py::create_all_room_levels) onto real, existing graphs
under Content/EnvSandbox/PCG/, and does the same for any _V2/_V3 variant map
sharing a base name.

Idempotent: safe to re-run. GenerationTrigger is set to OnDemand (non-blocking
at level load); the dungeon coordinator's existing PCG-generating wait
(MelodiaDungeonRunCoordinator.cpp) already handles waiting for it before
validating a streamed room.

Run inside the Unreal Editor Python console, or headless:
    UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/assign_room_pcg_graphs.py"
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOM_LEVEL_DIR = "/Game/Melodia/Roguelike/Rooms"
# Absolute, project-root-relative - -ExecutePythonScript's CWD is the engine
# binaries folder, not the project, so a bare relative Path() writes outside
# the project entirely.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Melodia" / "pcg_room_graph_assignment.json"

# Base level_name -> PCG graph asset path. Keyed by room identity (matches
# setup_roguelike_dungeon.py's level_configs), not raw nikki_archetype, so the
# mapping stays legible even though several rooms share an archetype tag.
ROOM_GRAPH_MAP: dict[str, str] = {
    # Start / Standard grove rooms (SakuraDreamer) - lantern-lit grove scatter.
    "MelodiaGrove": "/Game/EnvSandbox/PCG/Universal/PCG_LanternGrove",
    "WhisperingGrove": "/Game/EnvSandbox/PCG/Universal/PCG_LanternGrove",
    # Elite fire fight (CosmicWeaver) - dramatic rock/grotto dressing.
    "EverburningClearing": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_BaroqueGrotto_RockScatter",
    # Boss arena (MirageDancer) - clean, legible, low-clutter greybox standard
    # so the fight itself stays readable (matches the arena-legibility intent
    # already agreed for boss rooms).
    "BossArena": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_SpaceCathedral_Greybox_Standard",
    # Shop (SakuraDreamer, calmer variant) - soft meadow bloom.
    "TokenShrine": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_SakuraDream_MeadowBloom",
    # Treasure / abandoned ruins (CosmicWeaver) - overgrown ruin scatter.
    "AbandonedCache": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_BaroqueGrotto_GardenRuins",
    # Event room, marked as a photo spot (MirageDancer) - the most striking
    # graph on the roster, deliberately: this room is meant to be screenshotted.
    "StarlightReverie": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_SpaceCathedral_FloatingStairways",
    # Blessing altar (CosmicWeaver) - ceremonial ruin + cosmic dressing.
    "BlessingAltar": "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_CosmicOrrery_GardenRuins",
}

# Density/perf safety net for any room whose base name isn't recognized
# (e.g. a future room archetype added without updating this map).
FALLBACK_GRAPH = "/Game/EnvSandbox/PCG/Greybox/PCG_Greybox_Minimal"


def _base_room_name(level_asset_name: str) -> str:
    """'L_WhisperingGrove_V2' -> 'WhisperingGrove'. Strips the L_ prefix and
    any trailing _V<n> variant suffix."""
    name = level_asset_name[2:] if level_asset_name.startswith("L_") else level_asset_name
    parts = name.split("_")
    if len(parts) > 1 and parts[-1].startswith("V") and parts[-1][1:].isdigit():
        parts = parts[:-1]
    return "_".join(parts)


def _find_pcg_volume() -> unreal.Actor | None:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        if actor.get_actor_label().endswith("_PCGVolume"):
            return actor
    return None


def assign_graph_to_level(level_path: str) -> dict:
    level_name = level_path.rsplit("/", 1)[-1]
    base_name = _base_room_name(level_name)
    graph_path = ROOM_GRAPH_MAP.get(base_name, FALLBACK_GRAPH)

    result = {"level": level_path, "base_name": base_name, "graph": graph_path, "status": ""}

    graph_asset = unreal.load_asset(graph_path)
    if not graph_asset:
        result["status"] = f"MISSING GRAPH ASSET: {graph_path}"
        unreal.log_error(f"  [FAIL] {level_name}: {result['status']}")
        return result

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(level_path):
        result["status"] = "FAILED TO LOAD LEVEL"
        unreal.log_error(f"  [FAIL] {level_name}: could not load level")
        return result

    pcg_actor = _find_pcg_volume()
    if not pcg_actor:
        result["status"] = f"NO {level_name}_PCGVolume ACTOR FOUND"
        unreal.log_warning(f"  [SKIP] {level_name}: no *_PCGVolume actor in this level")
        return result

    pcg_comp = pcg_actor.get_component_by_class(unreal.PCGComponent)
    if not pcg_comp:
        result["status"] = "PCGVolume ACTOR HAS NO PCGComponent"
        unreal.log_error(f"  [FAIL] {level_name}: {pcg_actor.get_actor_label()} has no PCGComponent")
        return result

    # PCGComponent.Graph is reflection-protected; SetGraph is the real API
    # (mirrors what the details-panel graph picker calls under the hood).
    pcg_comp.set_graph(graph_asset)
    try:
        pcg_comp.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    except Exception as exc:  # noqa: BLE001 - non-fatal, graph assignment is what matters
        unreal.log_warning(f"  [WARN] {level_name}: could not set generation_trigger ({exc})")

    les.save_current_level()
    result["status"] = "OK"
    unreal.log(f"  [assigned] {level_name} ({pcg_actor.get_actor_label()}) -> {graph_path}")
    return result


def main() -> None:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    room_assets = registry.get_assets_by_path(ROOM_LEVEL_DIR, recursive=True)
    level_paths = sorted(
        f"{a.package_name}"
        for a in room_assets
        if str(a.asset_class_path.asset_name) == "World"
    )

    unreal.log(f"Found {len(level_paths)} room level(s) under {ROOM_LEVEL_DIR}")

    results = []
    for p in level_paths:
        try:
            results.append(assign_graph_to_level(p))
        except Exception as exc:  # noqa: BLE001 - one bad room must not abort the batch
            unreal.log_error(f"  [FAIL] {p}: unhandled exception: {exc}")
            results.append({"level": p, "status": f"EXCEPTION: {exc}"})

    ok = sum(1 for r in results if r["status"] == "OK")
    unreal.log(f"PCG M1: {ok}/{len(results)} room volumes assigned a graph.")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"Report written: {REPORT}")


if __name__ == "__main__":
    main()
