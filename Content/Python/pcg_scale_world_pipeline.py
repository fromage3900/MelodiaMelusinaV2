"""Scale-first PCG contracts shared by proof builders and offline audits.

This module deliberately keeps the deterministic world/chunk logic free of
the Unreal Python module so it can be unit-tested while the editor is closed
or another lane owns the live editor. The Unreal helpers are thin adapters for
UE 5.8's PCG/World Partition settings and report unsupported properties rather
than silently pretending they were applied.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping


WP_CELL_SIZE_CM = 25_600
GENERATOR_VERSION = "musical_pcg_scale_v1"
BUILDER_SETTINGS_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings"
SCALE_WORLD_PROOF_LEVEL = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof"
WATER_INTERACTIVE_GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_WaterGameplayInteractive"

HERO_GRAPH_PATHS = (
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_XylophoneTrail",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove",
)

# One authored graph per hero grammar. A chunk references these assets; it
# never clones or rewrites the graph for a new coordinate. The PCGVolume's
# local component transform supplies the chunk origin at build time.
VISUAL_GRAPH_BINDINGS = {
    "ResonanceCathedral": {
        "graph": HERO_GRAPH_PATHS[0],
        "profile": "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_ResonanceCathedralProfile",
        "curve_system": "PCGEx spline -> nearest-spline sample -> classic architecture",
        "hero_role": "nave_landmark",
        "nikki_dressing_recipe": "ResonanceCathedral",
    },
    "ArpeggioBridge": {
        "graph": HERO_GRAPH_PATHS[1],
        "profile": "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_ArpeggioBridgeProfile",
        "curve_system": "PCGEx measured traversal spline -> walkable deck and rails",
        "hero_role": "traversal_landmark",
        "nikki_dressing_recipe": "ArpeggioBridge",
    },
    "BellTreeGarden": {
        "graph": HERO_GRAPH_PATHS[2],
        "profile": "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_BellTreeGardenProfile",
        "curve_system": "PCGEx measured branch spline -> grounded support landmarks",
        "hero_role": "branch_landmark",
        "nikki_dressing_recipe": "BellTreeGarden",
    },
    "XylophoneTrail": {
        "graph": HERO_GRAPH_PATHS[3],
        "profile": "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_XylophoneTrailProfile",
        "curve_system": "PCGEx measured xylophone guide spline -> low authored rail",
        "hero_role": "walkable_instrument_landmark",
        "nikki_dressing_recipe": "XylophoneTrail",
    },
    "CrystalHarpGrove": {
        "graph": HERO_GRAPH_PATHS[4],
        "profile": "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_CrystalHarpGroveProfile",
        "curve_system": "paired PCGEx harp-frame splines -> walkable corridor and station landmarks",
        "hero_role": "pitched_string_landmark",
        "nikki_dressing_recipe": "CrystalHarpGrove",
    },
}

BIOME_BANDS = (
    "stone_court",
    "moss_rim",
    "blue_void",
    "crystal_meadow",
    "wind_shelf",
)


def chunk_origin_cm(chunk_x: int, chunk_y: int) -> tuple[int, int, int]:
    """Return the integer World Partition origin for a chunk coordinate."""
    return (int(chunk_x) * WP_CELL_SIZE_CM, int(chunk_y) * WP_CELL_SIZE_CM, 0)


def biome_band_for_chunk(world_seed: int, chunk_x: int, chunk_y: int) -> str:
    """Choose a stable macro biome band, with the proof center kept readable."""
    if (int(chunk_x), int(chunk_y)) == (0, 0):
        return "stone_court"
    return BIOME_BANDS[stable_chunk_seed(world_seed, chunk_x, chunk_y) % len(BIOME_BANDS)]


def hero_slots_for_chunk(world_seed: int, chunk_x: int, chunk_y: int) -> tuple[str, ...]:
    """Place sparse landmarks deterministically, preserving the proof triad."""
    coord = (int(chunk_x), int(chunk_y))
    if coord == (0, 0):
        return ("ResonanceCathedral",)
    if coord == (1, 0):
        return ("ArpeggioBridge",)
    if coord == (-1, 0):
        return ("BellTreeGarden",)
    if coord == (0, 1):
        return ("XylophoneTrail",)
    if coord == (1, 1):
        return ("CrystalHarpGrove",)
    # Sparse landmark cadence for an endless grid. Most chunks are biome-only;
    # landmark chunks remain far enough apart to preserve a readable vista.
    token = stable_chunk_seed(world_seed, chunk_x, chunk_y) % 23
    if token == 0:
        return ("ResonanceCathedral",)
    if token == 7:
        return ("ArpeggioBridge",)
    if token == 13:
        return ("BellTreeGarden",)
    return ()


def border_anchor_layout(world_seed: int, chunk_x: int, chunk_y: int) -> dict[str, dict[str, int | str]]:
    """Describe deterministic walkable curve anchors at all four chunk edges."""
    half = WP_CELL_SIZE_CM // 2
    def edge_jitter(ax: int, ay: int, bx: int, by: int) -> int:
        # The shared edge, rather than either owning chunk, owns the offset.
        # This is what makes the curve guide terminate at the same place from
        # either side of a streamed seam.
        signature = shared_border_signature(world_seed, ax, ay, bx, by)
        return int(int(signature[:8], 16) % 1400) - 700

    west_jitter = edge_jitter(chunk_x - 1, chunk_y, chunk_x, chunk_y)
    east_jitter = edge_jitter(chunk_x, chunk_y, chunk_x + 1, chunk_y)
    south_jitter = edge_jitter(chunk_x, chunk_y - 1, chunk_x, chunk_y)
    north_jitter = edge_jitter(chunk_x, chunk_y, chunk_x, chunk_y + 1)
    anchors = {
        "west": (0, half + west_jitter, 0),
        "east": (WP_CELL_SIZE_CM, half + east_jitter, 0),
        "south": (half + south_jitter, 0, 0),
        "north": (half + north_jitter, WP_CELL_SIZE_CM, 0),
    }
    result: dict[str, dict[str, int | str]] = {}
    for side, location in anchors.items():
        neighbor_x = chunk_x + (1 if side == "east" else -1 if side == "west" else 0)
        neighbor_y = chunk_y + (1 if side == "north" else -1 if side == "south" else 0)
        result[side] = {
            "signature": shared_border_signature(world_seed, chunk_x, chunk_y, neighbor_x, neighbor_y),
            "x_cm": int(location[0]),
            "y_cm": int(location[1]),
            "z_cm": int(location[2]),
            "clearance_cm": 2400,
        }
    return result


def reusable_graph_binding(slot: str) -> dict[str, str]:
    binding = VISUAL_GRAPH_BINDINGS.get(str(slot))
    if not binding:
        raise KeyError(f"unknown visual hero slot: {slot}")
    return dict(binding)


@dataclass(frozen=True)
class PCGInteractivePlacementSpec:
    """Stable runtime placement contract for a PCG-spawned gameplay actor.

    This is intentionally separate from visual graph points. Visual dressing
    may be regenerated or HLOD-merged; interactive actors are owned by one
    chunk, live in the gameplay Data Layer, and are never HLOD inputs.
    """

    stable_actor_id: str
    world_seed: int
    chunk_x: int
    chunk_y: int
    hero_slot: str
    local_index: int
    gameplay_role: str
    water_network_id: str
    water_node_id: str
    motion_mode: str
    route_id: str
    owning_chunk: str
    gameplay_data_layer: str = "DL_Musical_HeroGameplay"
    exclude_from_hlod: bool = True
    no_merging: bool = True
    border_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_interactive_actor_id(
    world_seed: int,
    chunk_x: int,
    chunk_y: int,
    hero_slot: str,
    local_index: int,
    gameplay_role: str,
    generator_version: str = GENERATOR_VERSION,
) -> str:
    """Derive identity from deterministic point/chunk data, never labels/order."""
    payload = (
        f"{int(world_seed)}|{int(chunk_x)}|{int(chunk_y)}|{generator_version}|"
        f"{hero_slot}|{int(local_index)}|{gameplay_role}"
    ).encode("utf-8")
    return f"PCGIA_{hashlib.sha256(payload).hexdigest()[:20]}"


def make_interactive_placement_spec(
    world_seed: int,
    chunk_x: int,
    chunk_y: int,
    hero_slot: str,
    local_index: int,
    gameplay_role: str,
    water_network_id: str,
    water_node_id: str,
    motion_mode: str = "None",
    route_id: str = "",
    border_signature: str = "",
) -> PCGInteractivePlacementSpec:
    if motion_mode not in {"None", "KinematicRoute", "PhysicsBuoyant"}:
        raise ValueError(f"unsupported interactive motion mode: {motion_mode}")
    if int(local_index) < 0:
        raise ValueError("interactive local_index must be non-negative")
    owning_chunk = f"{int(chunk_x)},{int(chunk_y)}"
    return PCGInteractivePlacementSpec(
        stable_actor_id=stable_interactive_actor_id(
            world_seed, chunk_x, chunk_y, hero_slot, local_index, gameplay_role
        ),
        world_seed=int(world_seed),
        chunk_x=int(chunk_x),
        chunk_y=int(chunk_y),
        hero_slot=str(hero_slot),
        local_index=int(local_index),
        gameplay_role=str(gameplay_role),
        water_network_id=str(water_network_id),
        water_node_id=str(water_node_id),
        motion_mode=str(motion_mode),
        route_id=str(route_id),
        owning_chunk=owning_chunk,
        border_signature=str(border_signature),
    )


def interactive_placements_for_chunk(
    world_seed: int,
    chunk_x: int,
    chunk_y: int,
    hero_slot_assignments: Iterable[str],
) -> tuple[PCGInteractivePlacementSpec, ...]:
    """Return the deterministic water proof placements for a Crystal Harp chunk.

    The five existing hero graphs keep their authored interactive counts. This
    separate placement stream owns water devices/platforms only.
    """
    slots = tuple(str(slot) for slot in hero_slot_assignments)
    if "CrystalHarpGrove" not in slots:
        return ()
    network = "WaterNetwork_CrystalHarpGrove"
    edge = shared_border_signature(world_seed, chunk_x, chunk_y, chunk_x + 1, chunk_y)
    specs = (
        ("resonance_station", "HarpResonance", "None", ""),
        ("valve_anchor", "HarpValve", "None", ""),
        ("pump_anchor", "HarpPump", "None", ""),
        ("drain_anchor", "HarpDrain", "None", ""),
        ("water_gate_anchor", "HarpGate", "None", "Route_HarpCrossing"),
        ("moving_platform", "HarpPlatformRoute", "KinematicRoute", "Route_HarpCrossing"),
        ("buoyant_platform", "HarpBuoyantFlow", "PhysicsBuoyant", ""),
        ("current_volume_anchor", "HarpCurrent", "None", ""),
    )
    return tuple(
        make_interactive_placement_spec(
            world_seed,
            chunk_x,
            chunk_y,
            "CrystalHarpGrove",
            index,
            role,
            network,
            node,
            motion,
            route,
            edge if role in {"moving_platform", "water_gate_anchor"} else "",
        )
        for index, (role, node, motion, route) in enumerate(specs)
    )


@dataclass(frozen=True)
class ChunkManifest:
    world_seed: int
    chunk_x: int
    chunk_y: int
    generator_version: str = GENERATOR_VERSION
    chunk_size_cm: int = WP_CELL_SIZE_CM
    biome_id: str = "musical_classic"
    pcg_graph_paths: tuple[str, ...] = HERO_GRAPH_PATHS
    data_layer_assignments: tuple[str, ...] = (
        "DL_Musical_HeroGameplay",
        "DL_Musical_StaticArchitecture",
        "DL_Musical_BiomeDressing",
    )
    hlod_layer_assignments: tuple[str, ...] = ("HLOD_Musical_Static",)
    hero_slot_assignments: tuple[str, ...] = ()
    border_signatures: tuple[tuple[str, str], ...] = ()
    persistence_revision: int = 0
    generation_quality: int = 2
    stable_seed: int = 0
    world_origin_cm: tuple[int, int, int] = (0, 0, 0)
    biome_band: str = "stone_court"
    curve_seed: int = 0
    walkable_corridor_cm: int = 2400
    seam_buffer_cm: int = 900
    border_anchor_layout: tuple[tuple[str, tuple[tuple[str, int | str], ...]], ...] = ()
    interactive_placement_specs: tuple[PCGInteractivePlacementSpec, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pcg_graph_paths"] = list(self.pcg_graph_paths)
        data["data_layer_assignments"] = list(self.data_layer_assignments)
        data["hlod_layer_assignments"] = list(self.hlod_layer_assignments)
        data["hero_slot_assignments"] = list(self.hero_slot_assignments)
        data["border_signatures"] = {key: value for key, value in self.border_signatures}
        data["world_origin_cm"] = list(self.world_origin_cm)
        data["border_anchor_layout"] = {
            side: {key: value for key, value in values}
            for side, values in self.border_anchor_layout
        }
        data["interactive_placement_specs"] = [
            spec.to_dict() if isinstance(spec, PCGInteractivePlacementSpec) else spec
            for spec in self.interactive_placement_specs
        ]
        return data


def stable_chunk_seed(world_seed: int, chunk_x: int, chunk_y: int, generator_version: str = GENERATOR_VERSION) -> int:
    payload = f"{int(world_seed)}|{int(chunk_x)}|{int(chunk_y)}|{generator_version}".encode("utf-8")
    # UE PCG seeds are signed 32-bit values in several APIs. Keep the
    # deterministic hash positive and away from zero for easier audits.
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "little") & 0x7FFFFFFF or 1


def shared_border_signature(world_seed: int, ax: int, ay: int, bx: int, by: int, generator_version: str = GENERATOR_VERSION) -> str:
    """Return one signature for a shared edge, independent of query order."""
    first = (int(ax), int(ay))
    second = (int(bx), int(by))
    ordered = tuple(sorted((first, second)))
    payload = f"{int(world_seed)}|{ordered[0][0]}|{ordered[0][1]}|{ordered[1][0]}|{ordered[1][1]}|{generator_version}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def make_chunk_manifest(
    world_seed: int,
    chunk_x: int,
    chunk_y: int,
    *,
    biome_id: str = "musical_classic",
    hero_slot_assignments: Iterable[str] = (),
    generation_quality: int = 2,
    persistence_revision: int = 0,
) -> ChunkManifest:
    borders = {
        "west": shared_border_signature(world_seed, chunk_x - 1, chunk_y, chunk_x, chunk_y),
        "east": shared_border_signature(world_seed, chunk_x, chunk_y, chunk_x + 1, chunk_y),
        "south": shared_border_signature(world_seed, chunk_x, chunk_y - 1, chunk_x, chunk_y),
        "north": shared_border_signature(world_seed, chunk_x, chunk_y, chunk_x, chunk_y + 1),
    }
    anchors = border_anchor_layout(world_seed, chunk_x, chunk_y)
    hero_slots = tuple(str(value) for value in hero_slot_assignments)
    return ChunkManifest(
        world_seed=int(world_seed),
        chunk_x=int(chunk_x),
        chunk_y=int(chunk_y),
        biome_id=str(biome_id),
        hero_slot_assignments=hero_slots,
        border_signatures=tuple(sorted(borders.items())),
        persistence_revision=max(0, int(persistence_revision)),
        generation_quality=max(0, min(4, int(generation_quality))),
        stable_seed=stable_chunk_seed(world_seed, chunk_x, chunk_y),
        world_origin_cm=chunk_origin_cm(chunk_x, chunk_y),
        biome_band=biome_band_for_chunk(world_seed, chunk_x, chunk_y),
        curve_seed=stable_chunk_seed(world_seed, chunk_x, chunk_y, GENERATOR_VERSION + ":curve"),
        walkable_corridor_cm=2400,
        seam_buffer_cm=900,
        border_anchor_layout=tuple(
            (side, tuple(sorted(values.items())))
            for side, values in sorted(anchors.items())
        ),
        interactive_placement_specs=interactive_placements_for_chunk(
            world_seed, chunk_x, chunk_y, hero_slots
        ),
    )


def build_chunk_grid(world_seed: int, radius: int = 1) -> tuple[ChunkManifest, ...]:
    radius = max(0, int(radius))
    manifests = []
    for chunk_y in range(-radius, radius + 1):
        for chunk_x in range(-radius, radius + 1):
            manifests.append(
                make_chunk_manifest(
                    world_seed,
                    chunk_x,
                    chunk_y,
                    hero_slot_assignments=hero_slots_for_chunk(world_seed, chunk_x, chunk_y),
                )
            )
    return tuple(manifests)


def validate_chunk_manifest(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "world_seed", "chunk_x", "chunk_y", "generator_version", "chunk_size_cm",
        "biome_id", "pcg_graph_paths", "data_layer_assignments",
        "hlod_layer_assignments", "hero_slot_assignments", "border_signatures",
        "persistence_revision", "generation_quality", "stable_seed",
    )
    for field in required:
        if field not in manifest:
            errors.append(f"missing {field}")
    if errors:
        return errors
    if int(manifest["chunk_size_cm"]) != WP_CELL_SIZE_CM:
        errors.append(f"chunk_size_cm must be {WP_CELL_SIZE_CM}")
    expected_seed = stable_chunk_seed(
        int(manifest["world_seed"]),
        int(manifest["chunk_x"]),
        int(manifest["chunk_y"]),
        str(manifest["generator_version"]),
    )
    if int(manifest["stable_seed"]) != expected_seed:
        errors.append("stable_seed does not match world/chunk identity")
    if not str(manifest["generator_version"]):
        errors.append("generator_version must be non-empty")
    if not isinstance(manifest["pcg_graph_paths"], list) or not all(
        isinstance(path, str) and path.startswith("/Game/") for path in manifest["pcg_graph_paths"]
    ):
        errors.append("pcg_graph_paths must contain /Game/ asset paths")
    borders = manifest["border_signatures"]
    if not isinstance(borders, dict) or set(borders) != {"west", "east", "south", "north"}:
        errors.append("border_signatures must contain west/east/south/north")
    if not 0 <= int(manifest["generation_quality"]) <= 4:
        errors.append("generation_quality must be 0..4")
    expected_origin = list(chunk_origin_cm(int(manifest["chunk_x"]), int(manifest["chunk_y"])))
    if "world_origin_cm" in manifest and list(manifest["world_origin_cm"]) != expected_origin:
        errors.append("world_origin_cm does not match chunk coordinate")
    if "biome_band" in manifest and str(manifest["biome_band"]) not in BIOME_BANDS:
        errors.append("biome_band is not a registered macro band")
    if "curve_seed" in manifest:
        expected_curve_seed = stable_chunk_seed(
            int(manifest["world_seed"]),
            int(manifest["chunk_x"]),
            int(manifest["chunk_y"]),
            str(manifest["generator_version"]) + ":curve",
        )
        if int(manifest["curve_seed"]) != expected_curve_seed:
            errors.append("curve_seed does not match chunk identity")
    if "border_anchor_layout" in manifest and not isinstance(manifest["border_anchor_layout"], dict):
        errors.append("border_anchor_layout must be an object keyed by side")
    placements = manifest.get("interactive_placement_specs", [])
    if not isinstance(placements, list):
        errors.append("interactive_placement_specs must be a list")
        placements = []
    placement_ids: set[str] = set()
    for placement in placements:
        if not isinstance(placement, dict):
            errors.append("interactive placement must be an object")
            continue
        for field in (
            "stable_actor_id", "world_seed", "chunk_x", "chunk_y", "hero_slot",
            "local_index", "gameplay_role", "water_network_id", "water_node_id",
            "motion_mode", "route_id", "owning_chunk", "gameplay_data_layer",
            "exclude_from_hlod",
        ):
            if field not in placement:
                errors.append(f"interactive placement missing {field}")
        actor_id = str(placement.get("stable_actor_id", ""))
        if actor_id in placement_ids:
            errors.append(f"duplicate interactive actor ID {actor_id}")
        placement_ids.add(actor_id)
        if actor_id and actor_id != stable_interactive_actor_id(
            int(placement.get("world_seed", 0)),
            int(placement.get("chunk_x", 0)),
            int(placement.get("chunk_y", 0)),
            str(placement.get("hero_slot", "")),
            int(placement.get("local_index", 0)),
            str(placement.get("gameplay_role", "")),
            str(manifest.get("generator_version", GENERATOR_VERSION)),
        ):
            errors.append(f"interactive actor ID is not deterministic: {actor_id}")
        if str(placement.get("owning_chunk")) != f"{int(manifest['chunk_x'])},{int(manifest['chunk_y'])}":
            errors.append(f"interactive placement {actor_id} is owned by another chunk")
        if str(placement.get("gameplay_data_layer")) != "DL_Musical_HeroGameplay":
            errors.append(f"interactive placement {actor_id} is outside gameplay Data Layer")
        if not bool(placement.get("exclude_from_hlod")):
            errors.append(f"interactive placement {actor_id} participates in HLOD")
        if str(placement.get("motion_mode")) not in {"None", "KinematicRoute", "PhysicsBuoyant"}:
            errors.append(f"interactive placement {actor_id} has invalid motion mode")
    anchors = manifest.get("border_anchor_layout")
    if isinstance(anchors, dict):
        expected_sides = {"west", "east", "south", "north"}
        if set(anchors) != expected_sides:
            errors.append("border_anchor_layout must contain west/east/south/north")
        borders = manifest.get("border_signatures", {})
        half = WP_CELL_SIZE_CM // 2
        expected_positions = {
            "west": (0, None),
            "east": (WP_CELL_SIZE_CM, None),
            "south": (None, 0),
            "north": (None, WP_CELL_SIZE_CM),
        }
        for side, anchor in anchors.items():
            if not isinstance(anchor, dict):
                errors.append(f"border anchor {side} must be an object")
                continue
            if not all(key in anchor for key in ("signature", "x_cm", "y_cm", "z_cm", "clearance_cm")):
                errors.append(f"border anchor {side} is missing required fields")
                continue
            if isinstance(borders, dict) and anchor.get("signature") != borders.get(side):
                errors.append(f"border anchor signature mismatch on {side}")
            expected_x, expected_y = expected_positions.get(side, (None, None))
            if expected_x is not None and int(anchor["x_cm"]) != expected_x:
                errors.append(f"border anchor {side} x coordinate is not on the chunk edge")
            if expected_y is not None and int(anchor["y_cm"]) != expected_y:
                errors.append(f"border anchor {side} y coordinate is not on the chunk edge")
            transverse = int(anchor["y_cm"] if expected_x is not None else anchor["x_cm"])
            if not 0 <= transverse <= WP_CELL_SIZE_CM:
                errors.append(f"border anchor {side} transverse coordinate is out of bounds")
            if int(anchor["clearance_cm"]) < int(manifest.get("walkable_corridor_cm", 0)):
                errors.append(f"border anchor {side} clearance is narrower than the walkable corridor")
    return errors


def validate_grid(manifests: Iterable[ChunkManifest]) -> list[str]:
    entries = list(manifests)
    errors: list[str] = []
    if not entries:
        return ["chunk grid is empty"]
    seen: set[tuple[int, int]] = set()
    by_coord = {(entry.chunk_x, entry.chunk_y): entry for entry in entries}
    for entry in entries:
        coord = (entry.chunk_x, entry.chunk_y)
        if coord in seen:
            errors.append(f"duplicate chunk {coord}")
        seen.add(coord)
        errors.extend(validate_chunk_manifest(entry.to_dict()))
        for direction, dx, dy, opposite in (
            ("east", 1, 0, "west"),
            ("north", 0, 1, "south"),
        ):
            neighbor = by_coord.get((entry.chunk_x + dx, entry.chunk_y + dy))
            if neighbor:
                own_border = dict(entry.border_signatures).get(direction)
                neighbor_border = dict(neighbor.border_signatures).get(opposite)
                if own_border != neighbor_border:
                    errors.append(f"seam mismatch {coord} {direction}")
                own_anchors = dict(entry.border_anchor_layout).get(direction)
                neighbor_anchors = dict(neighbor.border_anchor_layout).get(opposite)
                if own_anchors and neighbor_anchors:
                    own_anchor = dict(own_anchors)
                    neighbor_anchor = dict(neighbor_anchors)
                    transverse_key = "y_cm" if direction == "east" else "x_cm"
                    if own_anchor.get(transverse_key) != neighbor_anchor.get(transverse_key):
                        errors.append(f"curve anchor mismatch {coord} {direction}")
                    if own_anchor.get("z_cm") != neighbor_anchor.get("z_cm"):
                        errors.append(f"curve anchor height mismatch {coord} {direction}")
    return errors


def write_grid_report(path: str | Path, world_seed: int = 3900, radius: int = 1) -> dict[str, Any]:
    manifests = build_chunk_grid(world_seed, radius)
    report = {
        "generator_version": GENERATOR_VERSION,
        "world_seed": int(world_seed),
        "radius": int(radius),
        "chunk_size_cm": WP_CELL_SIZE_CM,
        "chunks": [entry.to_dict() for entry in manifests],
        "errors": validate_grid(manifests),
    }
    report["ok"] = not report["errors"]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _set_first(obj: Any, names: Iterable[str], value: Any) -> str | None:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            return name
        except Exception:
            continue
    return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    try:
        return str(value.get_path_name())
    except Exception:
        return str(value)


def ensure_builder_settings_asset(unreal: Any, asset_path: str = BUILDER_SETTINGS_PATH) -> dict[str, Any]:
    """Create/configure the UE 5.8 PCGBuilderSettings asset if available."""
    folder = asset_path.rsplit("/", 1)[0]
    name = asset_path.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    settings = unreal.EditorAssetLibrary.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    if settings is None:
        settings_class = getattr(unreal, "PCGBuilderSettings", None)
        if settings_class is None:
            settings_class = getattr(unreal, "PCGWorldPartitionBuilderSettings", None)
        if settings_class is None:
            settings_class = unreal.load_class(None, "/Script/PCGEditor.PCGBuilderSettings")
        if settings_class is None:
            return {"asset": asset_path, "available": False, "error": "PCGBuilderSettings class unavailable"}
        factory_class = getattr(unreal, "PCGBuilderSettingsFactory", None)
        if factory_class is None:
            factory_class = getattr(unreal, "DataAssetFactory", None)
        if factory_class is None:
            factory_class = unreal.load_class(None, "/Script/PCGEditor.PCGBuilderSettingsFactory")
        if factory_class is None:
            return {"asset": asset_path, "available": False, "error": "PCGBuilderSettingsFactory unavailable"}
        settings = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, settings_class, factory_class()
        )
    if not settings:
        return {"asset": asset_path, "available": False, "error": "asset creation failed"}

    applied: dict[str, Any] = {}
    graph_assets = [unreal.EditorAssetLibrary.load_asset(path) for path in HERO_GRAPH_PATHS]
    graph_assets = [graph for graph in graph_assets if graph]
    for names, value in (
        (("b_iterative_cell_loading", "bIterativeCellLoading"), True),
        (("iterative_cell_size", "IterativeCellSize"), WP_CELL_SIZE_CM),
        (("b_one_component_at_a_time", "bOneComponentAtATime"), True),
        (("b_load_editor_only_data_layers", "bLoadEditorOnlyDataLayers"), True),
        (("b_load_activated_runtime_data_layers", "bLoadActivatedRuntimeDataLayers"), True),
        (("graphs",), graph_assets),
    ):
        prop = _set_first(settings, names, value)
        if prop:
            applied[prop] = _json_safe(value)
    settings.modify()
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return {
        "asset": asset_path,
        "available": True,
        "applied": applied,
        "missing_expected_properties": [
            name for name, aliases in (
                ("iterative_cell_loading", ("b_iterative_cell_loading", "bIterativeCellLoading")),
                ("iterative_cell_size", ("iterative_cell_size", "IterativeCellSize")),
                ("graphs", ("graphs",)),
            )
            if not any(alias in applied for alias in aliases)
        ],
    }


def scale_contract() -> dict[str, Any]:
    return {
        "world_partition_cell_size_cm": WP_CELL_SIZE_CM,
        "chunk_identity": ["WorldSeed", "ChunkX", "ChunkY", "GeneratorVersion"],
        "graph_reuse": {
            "mode": "one-authored-graph-per-hero-slot",
            "bindings": VISUAL_GRAPH_BINDINGS,
            "chunk_origin_source": "PCGVolume local component transform",
            "graph_cloning": False,
        },
        "curve_spine": {
            "system": "PCGEx measured spline and nearest-spline sampling",
            "seam_contract": "border anchors + shared signatures",
            "finite_transform_guard": True,
            "walkable_corridor_cm": 2400,
        },
        "pcg_generation_tiers": {
            "hero_interactive": {"execution": "CPU", "partitioned": False, "hlod": False},
            "classic_architecture": {"execution": "CPU", "partitioned": True, "hierarchical": True, "hlod": True},
            "biome_dressing": {"execution": "CPU_or_GPU_after_profile", "partitioned": True, "hierarchical": True, "hlod": True},
        },
        "control_preview": {
            "component": "/Script/BS_GodFile.PCGControlLivePreviewComponent",
            "default_enabled": False,
            "editor_preview_tick": True,
            "debounce_seconds": 0.20,
            "scope": "explicit PCG component targets or finite discovery radius",
            "discrete_layout_note": "count/spacing changes use the normal builder or authored graph rebuild; continuous data-driven branches regenerate immediately",
        },
        "runtime_dependencies": [
            {
				"class": "APCGHeroMusicNode",
				"role": "generated interactive note actor; BeginPlay registers reactive mesh",
				"source": "Source/BS_GodFile/Piano/PCGHeroMusic.cpp",
            },
            {
				"class": "APCGHeroMusicGraphHost",
				"role": "authoritative note judgement/completion event source",
				"source": "Source/BS_GodFile/Piano/PCGHeroMusic.h",
            },
            {
				"class": "UMelodiaMusicClockSubsystem",
				"role": "single canonical beat clock used by hero host timing",
				"source": "Source/BS_GodFile/Piano/PCGHeroMusic.cpp",
			},
			{
				"class": "UMelodiaRhythmReactivitySubsystem",
				"role": "single reactivity/MPC owner; receives existing hero runtime notifications",
				"source": "Source/BS_GodFile/Piano/PCGHeroMusic.cpp",
			},
			{
				"class": "UMelodiaAudioComponent",
				"role": "existing PlayMusicalNote audio path",
				"source": "Source/BS_GodFile/Piano/PCGHeroMusic.cpp",
			},
			{
				"class": "UMelodiaWaterGameplaySubsystem",
				"role": "logical reservoir/pressure/flow/route/puzzle authority",
				"source": "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplaySubsystem.h",
			},
			{
				"class": "UMelodiaWaterInteractionSubsystem",
				"role": "native Water Body query and presentation impulse bus",
				"source": "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterInteractionSubsystem.h",
			},
			{
				"class": "AMelodiaWaterPlatform",
				"role": "stable gameplay-layer moving/buoyant actor; no HLOD or merging",
				"source": "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterPlatform.h",
			},
        ],
        "music_framework": {
            "clock": "UMelodiaMusicClockSubsystem",
            "reactivity": "UMelodiaRhythmReactivitySubsystem",
            "audio": "UMelodiaAudioComponent::PlayMusicalNote",
            "mpc": "MPC_Melodia_Palette",
            "dedupe_contract": "no second clock, MPC writer, or reactivity subsystem",
        },
        "interactive_placement_contract": {
			"schema": "PCGInteractivePlacementSpec",
			"graph": WATER_INTERACTIVE_GRAPH_PATH,
			"identity": ["WorldSeed", "ChunkX", "ChunkY", "GeneratorVersion", "HeroSlot", "LocalIndex", "GameplayRole"],
			"roles": ["resonance_station", "valve_anchor", "pump_anchor", "drain_anchor", "water_gate_anchor", "moving_platform", "buoyant_platform", "current_volume_anchor"],
			"gameplay_data_layer": "DL_Musical_HeroGameplay",
			"exclude_from_hlod": True,
			"seam_ownership": "one chunk owns the gameplay actor; neighbors own visual continuation geometry only",
			"border_route_identity": "shared_border_signature",
		},
		"proof_runtime": {
			"first_graph": "CrystalHarpGrove",
			"proof_sequence": "generated node press -> PlayMusicalNote -> shared clock -> reactivity -> water resonance -> route -> platforms -> gate",
			"production_maps_touched": False,
		},
        "production_maps_touched": False,
    }
