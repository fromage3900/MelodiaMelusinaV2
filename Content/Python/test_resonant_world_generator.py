from __future__ import annotations

import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_generator import (  # noqa: E402
    GENERATOR_VERSION,
    ResonantEdit,
    WorldConfig,
    WORLD_MOVEMENT_LIBRARY,
    arrangement_score,
    build_world_manifest,
    edge_anchor,
    iter_chunk_voxels,
    shared_border_signature,
    voxel_at,
)


def test_seed_is_reproducible_and_changes_the_world_profile() -> None:
    first = build_world_manifest(3900, radius=1)
    second = build_world_manifest(3900, radius=1)
    other = build_world_manifest(3901, radius=1)

    assert first == second
    assert first["ok"] is True
    assert first["world"] != other["world"]
    assert len(first["chunks"]) == 9


def test_streamed_chunk_edges_share_the_same_anchor() -> None:
    config = WorldConfig.from_seed(3900)
    east = edge_anchor(config, 0, 0, "east")
    west = edge_anchor(config, 1, 0, "west")
    north = edge_anchor(config, 0, 0, "north")
    south = edge_anchor(config, 0, 1, "south")

    assert east["signature"] == west["signature"] == shared_border_signature(3900, 0, 0, 1, 0)
    assert east["local_y"] == west["local_y"]
    assert north["signature"] == south["signature"]
    assert north["local_x"] == south["local_x"]


def test_voxels_have_stable_ids_and_pitch_from_the_world_mode() -> None:
    config = WorldConfig.from_seed(3900)
    voxel = voxel_at(config, 0, 0, 4, 5, 2)
    repeat = voxel_at(config, 0, 0, 4, 5, 2)
    generated = list(iter_chunk_voxels(config, 0, 0))
    allowed_pitch_classes = {(config.root_pitch_class + interval) % 12 for interval in config.mode.intervals}

    assert voxel == repeat
    assert voxel.cell_id.startswith(f"{GENERATOR_VERSION}:")
    assert voxel.pitch_class in allowed_pitch_classes
    assert generated
    assert all(item.material_id != "air" for item in generated)


def test_arrangement_scoring_is_supportive_and_mode_aware() -> None:
    config = WorldConfig.from_seed(3900, root_pitch_class=0, mode_id="ionian")
    stable = [
        ResonantEdit(0, 0, 0, 0, 2, "note_block", 0, "harp", "a"),
        ResonantEdit(0, 0, 1, 0, 2, "note_block", 4, "harp", "b"),
        ResonantEdit(0, 0, 2, 0, 2, "note_block", 7, "harp", "c"),
    ]
    dissonant = [
        ResonantEdit(0, 0, 0, 0, 2, "note_block", 0, "harp", "a"),
        ResonantEdit(0, 0, 1, 0, 2, "note_block", 1, "harp", "b"),
    ]

    stable_result = arrangement_score(stable, config)
    dissonant_result = arrangement_score(dissonant, config)
    assert stable_result["score"] > dissonant_result["score"]
    assert stable_result["interpretation"] == "a stable refrain"
    assert dissonant_result["interpretation"] in {"a searching phrase", "a beautiful dissonance"}


def test_movements_bind_chunks_to_authored_asset_grammars() -> None:
    manifest = build_world_manifest(3900, radius=1)
    config = WorldConfig.from_seed(3900)
    center = next(chunk for chunk in manifest["chunks"] if (chunk["chunk_x"], chunk["chunk_y"]) == (0, 0))

    assert config.movement_id in WORLD_MOVEMENT_LIBRARY
    assert config.mode_id in WORLD_MOVEMENT_LIBRARY[config.movement_id].mode_affinities
    assert center["movement_id"] == config.movement_id
    assert center["pcg_binding"]["movement_id"] == config.movement_id
    assert center["movement"]["resonant_form_id"].startswith("ResonantForm_")
