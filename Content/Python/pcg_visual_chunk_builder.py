"""Reusable visual PCG chunk planning for an endless World Partition grid.

The planner is deliberately independent from Unreal. It emits the exact
inputs an editor or unattended World Partition builder needs: one existing
hero graph/profile binding, a chunk-local origin, data/HLOD ownership, curve
seam anchors, and a quality tier. The same graph asset can therefore be
instantiated in any number of chunks without graph duplication.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pcg_scale_world_pipeline as scale


CLASSIC_LIBRARY_MESHES = {
    "floor": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
    "rail": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
    "column": "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
    "arch": "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
}

BIOME_DRESSING_RULES = {
    "stone_court": {"accent": "column", "accent_period": 5, "rotation_band": "orthogonal"},
    "moss_rim": {"accent": "rail", "accent_period": 4, "rotation_band": "edge_biased"},
    "blue_void": {"accent": "arch", "accent_period": 6, "rotation_band": "vista_facing"},
    "crystal_meadow": {"accent": "column", "accent_period": 3, "rotation_band": "radial"},
    "wind_shelf": {"accent": "rail", "accent_period": 5, "rotation_band": "crosswind"},
}

STATIC_SUBGRAPH_CONTRACT = {
    "control_snapshot": "shared tagged PCG_Control snapshot",
    "seed_identity": "WorldSeed|ChunkX|ChunkY|GeneratorVersion|local_point_seed",
    "curve_sampling": "PCGEx spline sampling with nearest-spline PathDist",
    "walkable_corridor": "authored floor/rail corridor with border anchor clearance",
    "architecture_library": "classic authored mesh descriptors via PCG mesh spawners",
    "biome_dressing": "hierarchical macro dressing; optional GPU only after profile",
    "render_contract": "custom depth/stencil and culling aliases",
    "level_to_pcg_data_asset": "authored classic library export is an input, not a graph clone",
    "seam_connector_ownership": "east and north edge owner emits each shared connector once",
    "nikki_scene_dressing": "proof-only material palette recipe; water instances are read-only inputs",
}

GENERATION_TIER_CONTRACT = {
    "tier_0_manifest": "deterministic chunk identity, persistence revision, and seam signatures",
    "tier_1_corridor": "CPU-authored walkable curve spine, floor, rails, and clearance buffers",
    "tier_2_landmark": "reused hero graph/profile binding with stable local point seeds",
    "tier_3_biome": "hierarchical macro dressing and authored classic architecture data assets",
    "tier_4_vista": "non-interactive packed/HLOD content only; never merge hero actors",
}


def _manifest_value(manifest: scale.ChunkManifest | Mapping[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(manifest, scale.ChunkManifest):
        return getattr(manifest, key, default)
    return manifest.get(key, default)


def chunk_static_specs(manifest: scale.ChunkManifest | Mapping[str, Any]) -> list[dict[str, Any]]:
    """Plan deterministic non-interactive tile dressing and owned seam connectors.

    The planner emits authored classic-library descriptors rather than cube
    approximations. A future PCG Data Asset import or offline builder can
    consume these descriptors without changing the hero graphs. Only the
    east/north owner emits a seam connector, preventing duplicate geometry when
    both World Partition cells are loaded.
    """
    world_seed = int(_manifest_value(manifest, "world_seed", 0))
    chunk_x = int(_manifest_value(manifest, "chunk_x", 0))
    chunk_y = int(_manifest_value(manifest, "chunk_y", 0))
    origin = tuple(int(value) for value in _manifest_value(manifest, "world_origin_cm", scale.chunk_origin_cm(chunk_x, chunk_y)))
    biome = str(_manifest_value(manifest, "biome_band", "stone_court"))
    quality = max(0, min(4, int(_manifest_value(manifest, "generation_quality", 2))))
    rule = BIOME_DRESSING_RULES.get(biome, BIOME_DRESSING_RULES["stone_court"])
    # Four-by-four authored tiles keep macro generation cheap while leaving a
    # full 900 cm seam buffer around the PCGEx curve anchors.
    tile_span = scale.WP_CELL_SIZE_CM // 4
    specs: list[dict[str, Any]] = []
    for grid_y in range(4):
        for grid_x in range(4):
            tile_seed = scale.stable_chunk_seed(
                world_seed,
                chunk_x * 4 + grid_x,
                chunk_y * 4 + grid_y,
                scale.GENERATOR_VERSION + ":biome-tile",
            )
            local_x = grid_x * tile_span + tile_span // 2
            local_y = grid_y * tile_span + tile_span // 2
            specs.append(
                {
                    "tier": "biome_dressing",
                    "chunk_x": chunk_x,
                    "chunk_y": chunk_y,
                    "grid_index": [grid_x, grid_y],
                    "seed": tile_seed,
                    "mesh": CLASSIC_LIBRARY_MESHES["floor"],
                    "local_position_cm": [local_x, local_y, 0],
                    "world_position_cm": [origin[0] + local_x, origin[1] + local_y, origin[2]],
                    "biome_band": biome,
                    "data_layer": "DL_Musical_BiomeDressing",
                    "hlod_layer": "HLOD_Musical_Static",
                    "interactive": False,
                    "quality_min": 0,
                    "generation_quality": quality,
                    "variation": {
                        "accent_mesh": CLASSIC_LIBRARY_MESHES[rule["accent"]],
                        "accent_period": int(rule["accent_period"]),
                        "rotation_band": rule["rotation_band"],
                        "place_accent": tile_seed % int(rule["accent_period"]) == 0,
                    },
                }
            )

    anchors = _manifest_value(manifest, "border_anchor_layout", {})
    if isinstance(anchors, tuple):
        anchors = {side: dict(values) for side, values in anchors}
    # Shared edges have a canonical owner: current chunk owns east/north,
    # neighbor owns west/south by virtue of its own east/north emission.
    for side in ("east", "north"):
        anchor = dict(anchors.get(side, {}))
        if not anchor:
            continue
        specs.append(
            {
                "tier": "seam_corridor",
                "chunk_x": chunk_x,
                "chunk_y": chunk_y,
                "side": side,
                "edge_signature": str(anchor.get("signature", "")),
                "seed": scale.stable_chunk_seed(
                    world_seed,
                    chunk_x,
                    chunk_y,
                    scale.GENERATOR_VERSION + ":seam:" + side,
                ),
                "mesh": CLASSIC_LIBRARY_MESHES["floor"],
                "local_position_cm": [int(anchor.get("x_cm", 0)), int(anchor.get("y_cm", 0)), int(anchor.get("z_cm", 0))],
                "clearance_cm": int(anchor.get("clearance_cm", 0)),
                "data_layer": "DL_Musical_StaticArchitecture",
                "hlod_layer": "HLOD_Musical_Static",
                "interactive": False,
                "ownership": "east_north_chunk_owner",
            }
        )
    return specs


def chunk_volume_specs(manifest: scale.ChunkManifest | Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return idempotent PCGVolume specs for the hero slots in one chunk."""
    world_seed = int(_manifest_value(manifest, "world_seed", 0))
    chunk_x = int(_manifest_value(manifest, "chunk_x", 0))
    chunk_y = int(_manifest_value(manifest, "chunk_y", 0))
    origin = list(_manifest_value(manifest, "world_origin_cm", scale.chunk_origin_cm(chunk_x, chunk_y)))
    slots = tuple(str(slot) for slot in _manifest_value(manifest, "hero_slot_assignments", ()))
    data_layers = list(_manifest_value(manifest, "data_layer_assignments", ()))
    hlod_layers = list(_manifest_value(manifest, "hlod_layer_assignments", ()))
    quality = int(_manifest_value(manifest, "generation_quality", 2))
    biome = str(_manifest_value(manifest, "biome_band", "stone_court"))
    anchors = _manifest_value(manifest, "border_anchor_layout", {})
    if isinstance(anchors, tuple):
        anchors = {side: dict(values) for side, values in anchors}

    specs = []
    for slot in slots:
        binding = scale.reusable_graph_binding(slot)
        specs.append(
            {
                "label": f"PCG Chunk {chunk_x}_{chunk_y} {slot}",
                "world_seed": world_seed,
                "chunk_x": chunk_x,
                "chunk_y": chunk_y,
                "generator_version": str(_manifest_value(manifest, "generator_version", scale.GENERATOR_VERSION)),
                "origin_cm": origin,
                "identity_namespace": {
                    "chunk_seed": int(_manifest_value(manifest, "stable_seed", 0)),
                    "local_point_seed_formula": "chunk stable seed + PCGPoint.Seed",
                    "global_identity": "WorldSeed|ChunkX|ChunkY|GeneratorVersion|PCGPoint.Seed",
                },
                "graph": binding["graph"],
                "profile": binding["profile"],
                "curve_system": binding["curve_system"],
                "hero_role": binding["hero_role"],
                "nikki_dressing_recipe": binding["nikki_dressing_recipe"],
                "biome_band": biome,
                "generation_quality": quality,
                "data_layers": data_layers,
                "hlod_layers": hlod_layers,
                "pcg_component": {
                    "coordinate_space": "LocalComponent",
                    "partitioned": True,
                    "generation_trigger": "GenerateOnDemand",
                    "actor_spawning": "NoMerging",
                },
                "border_anchors": anchors,
            }
        )
    return specs


def build_visual_world_plan(world_seed: int = 3900, radius: int = 2) -> dict[str, Any]:
    manifests = scale.build_chunk_grid(world_seed, radius=radius)
    chunks = []
    hero_specs = []
    static_specs = []
    for manifest in manifests:
        chunk = manifest.to_dict()
        chunk["graph_profile_bindings"] = {
            slot: scale.reusable_graph_binding(slot)
            for slot in manifest.hero_slot_assignments
        }
        chunks.append(chunk)
        hero_specs.extend(chunk_volume_specs(manifest))
        static_specs.extend(chunk_static_specs(manifest))
    return {
        "ok": not scale.validate_grid(manifests),
        "world_seed": int(world_seed),
        "radius": int(radius),
        "chunk_size_cm": scale.WP_CELL_SIZE_CM,
        "generator_version": scale.GENERATOR_VERSION,
        "graph_reuse": True,
        "static_subgraph_contract": STATIC_SUBGRAPH_CONTRACT,
        "generation_tier_contract": GENERATION_TIER_CONTRACT,
        "world_partition_contract": {
            "cell_size_cm": scale.WP_CELL_SIZE_CM,
            "chunk_origin_source": "PCGVolume local component transform",
            "runtime_generation": "nearby detail only; offline builder owns authored chunk generation",
            "interactive_actor_policy": "CPU actor spawning with NoMerging; excluded from HLOD",
        },
        "chunk_count": len(chunks),
        "hero_volume_count": len(hero_specs),
        "static_spec_count": len(static_specs),
        "chunks": chunks,
        "hero_volume_specs": hero_specs,
        "static_specs": static_specs,
    }


def write_visual_world_plan(path: str | Path, world_seed: int = 3900, radius: int = 2) -> dict[str, Any]:
    result = build_visual_world_plan(world_seed=world_seed, radius=radius)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def validate_visual_world_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    chunks = list(plan.get("chunks", []))
    if not plan.get("graph_reuse"):
        errors.append("graph_reuse must be true")
    if int(plan.get("chunk_size_cm", 0)) != scale.WP_CELL_SIZE_CM:
        errors.append("plan chunk size does not match World Partition cell")
    if int(plan.get("chunk_count", -1)) != len(chunks):
        errors.append("chunk_count does not match serialized chunks")
    if set(plan.get("static_subgraph_contract", {})) != set(STATIC_SUBGRAPH_CONTRACT):
        errors.append("static subgraph contract is incomplete")
    if set(plan.get("generation_tier_contract", {})) != set(GENERATION_TIER_CONTRACT):
        errors.append("generation tier contract is incomplete")
    seen_origins: set[tuple[int, int, int]] = set()
    expected_specs = 0
    expected_bindings: dict[tuple[int, int], dict[str, dict[str, str]]] = {}
    for chunk in chunks:
        origin = tuple(int(value) for value in chunk.get("world_origin_cm", ()))
        if origin in seen_origins:
            errors.append(f"duplicate chunk origin {origin}")
        seen_origins.add(origin)
        errors.extend(scale.validate_chunk_manifest(chunk))
        coords = (int(chunk.get("chunk_x", 0)), int(chunk.get("chunk_y", 0)))
        bindings = chunk.get("graph_profile_bindings", {})
        expected_slots = set(str(slot) for slot in chunk.get("hero_slot_assignments", []))
        if set(bindings) != expected_slots:
            errors.append(f"graph/profile slot drift for chunk {coords}")
        expected_bindings[coords] = bindings
        expected_specs += len(expected_slots)
        for slot, binding in chunk.get("graph_profile_bindings", {}).items():
            expected = scale.reusable_graph_binding(slot)
            if binding != expected:
                errors.append(f"graph binding drift for {slot}")
    for spec in plan.get("hero_volume_specs", []):
        if spec.get("pcg_component", {}).get("actor_spawning") != "NoMerging":
            errors.append(f"interactive volume is mergeable: {spec.get('label')}")
        coords = (int(spec.get("chunk_x", 0)), int(spec.get("chunk_y", 0)))
        slot = next((name for name, binding in scale.VISUAL_GRAPH_BINDINGS.items() if binding["graph"] == spec.get("graph")), None)
        if slot is None:
            errors.append(f"hero spec references an unknown graph: {spec.get('graph')}")
            continue
        binding = expected_bindings.get(coords, {}).get(slot)
        if not binding or spec.get("graph") != binding.get("graph") or spec.get("profile") != binding.get("profile"):
            errors.append(f"hero spec binding drift for chunk {coords} {slot}")
        expected_origin = list(scale.chunk_origin_cm(*coords))
        if list(spec.get("origin_cm", [])) != expected_origin:
            errors.append(f"hero spec origin drift for chunk {coords} {slot}")
        if spec.get("identity_namespace", {}).get("global_identity") != "WorldSeed|ChunkX|ChunkY|GeneratorVersion|PCGPoint.Seed":
            errors.append(f"hero spec identity contract missing for chunk {coords} {slot}")
    if int(plan.get("hero_volume_count", -1)) != len(plan.get("hero_volume_specs", [])):
        errors.append("hero_volume_count does not match serialized specs")
    if expected_specs != len(plan.get("hero_volume_specs", [])):
        errors.append("hero volume specs do not match chunk hero slots")
    static_specs = list(plan.get("static_specs", []))
    if int(plan.get("static_spec_count", -1)) != len(static_specs):
        errors.append("static_spec_count does not match serialized specs")
    edge_signatures: set[str] = set()
    for spec in static_specs:
        if spec.get("mesh") not in CLASSIC_LIBRARY_MESHES.values():
            errors.append(f"static spec is outside the classic mesh library: {spec.get('mesh')}")
        if spec.get("interactive"):
            errors.append(f"static spec is marked interactive: {spec.get('tier')}")
        if spec.get("tier") == "seam_corridor":
            signature = str(spec.get("edge_signature", ""))
            if signature in edge_signatures:
                errors.append(f"duplicate owned seam connector {signature}")
            edge_signatures.add(signature)
            if spec.get("ownership") != "east_north_chunk_owner":
                errors.append(f"seam connector ownership drift for {signature}")
    return errors
