"""Versioned offline contract mirroring MelodiaCore stage-recipe generation.

This module has no live run state and never imports Unreal. Its output is used for
fixtures, balance simulation, and cross-language golden-trace verification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = 1
STAGE_IDS = ("Grove", "ResonantBridge", "DissonantClearing", "MemoryCache", "Crescendo")
ENEMY_IDS = ("CrystalShard", "StoneGolem", "VoidWraith", "FireDrake")
BOSS_ENEMY_ID = "CosmicSentinel"
# Real RoomData asset families under /Game/Melodia/Roguelike (each has V1-V3).
# Mirrors UMelodiaRoguelikeRunSubsystem::BuildCurrentStage.
ROOM_FAMILIES = ("MelodiaGrove", "WhisperingGrove", "EverburningClearing", "AbandonedCache", "TokenShrine")
BOSS_ROOM_FAMILY = "BossArena"
THRESHOLD_ROOM_FAMILY = "MelodiaGrove"
SALTS = {
    "stage": 0x53544147,
    "topology": 0x544F504F,
    "room": 0x524F4F4D,
    "enemy": 0x454E454D,
    "reward": 0x52455744,
    "mutator": 0x4D555441,
    "cosmetic": 0x434F534D,
}


def _u32(value: int) -> int:
    return value & 0xFFFFFFFF


def derive_seed(run_seed: int, stage_index: int, salt: int) -> int:
    """Exact uint32 contract implemented by UMelodiaRoguelikeRunSubsystem."""
    value = _u32(run_seed)
    value = _u32(value ^ _u32(stage_index + 0x9E3779B9 + _u32(value << 6) + (value >> 2)))
    value = _u32(value ^ _u32(salt + 0x9E3779B9 + _u32(value << 6) + (value >> 2)))
    value = _u32(value ^ (value >> 16))
    value = _u32(value * 0x7FEB352D)
    value = _u32(value ^ (value >> 15))
    value = _u32(value * 0x846CA68B)
    value = _u32(value ^ (value >> 16))
    return value & 0x7FFFFFFF


@dataclass(frozen=True)
class GoldenStageRecipe:
    schema_version: int
    act_index: int
    stage_index: int
    endless_depth: int
    stage_id: str
    room_definition_id: str
    room_data_id: str
    encounter_id: str
    enemy_id: str
    difficulty_tier: int
    mutator_ids: tuple[str, ...]
    reward_pool_id: str
    dissonance_profile_id: str
    companion_requirement: str
    stage_seed: int
    topology_seed: int
    room_seed: int
    enemy_seed: int
    reward_seed: int
    mutator_seed: int
    cosmetic_seed: int

    def to_dict(self) -> dict:
        value = asdict(self)
        value["mutator_ids"] = list(self.mutator_ids)
        return value


def build_stage_recipe(
    run_seed: int,
    stage_index: int,
    *,
    acts: int = 1,
    stages_per_act: int = 3,
    endless_depth: int = 0,
    dissonance: float = 0.0,
    structured: bool = True,
    endless: bool = False,
) -> GoldenStageRecipe:
    seeds = {name: derive_seed(run_seed, stage_index, salt) for name, salt in SALTS.items()}
    threshold = stage_index == 0 and not endless
    stages_per_dungeon = max(1, acts) * max(1, stages_per_act) if structured else 0
    final_stage = not endless and stages_per_dungeon > 0 and stage_index >= stages_per_dungeon - 1
    stage_id = "SakuraThreshold" if threshold else STAGE_IDS[seeds["room"] % len(STAGE_IDS)]
    if threshold:
        room_family = THRESHOLD_ROOM_FAMILY
    elif final_stage:
        room_family = BOSS_ROOM_FAMILY
    else:
        room_family = ROOM_FAMILIES[seeds["room"] % len(ROOM_FAMILIES)]
    room_variant = 1 + (seeds["room"] >> 8) % 3
    room_data_id = f"RD_{room_family}_V{room_variant}"
    if threshold:
        enemy_id = "SakuraPhantom"
    elif final_stage:
        enemy_id = BOSS_ENEMY_ID
    else:
        enemy_id = ENEMY_IDS[seeds["enemy"] % len(ENEMY_IDS)]
    act_index = stage_index // stages_per_act if structured and stages_per_act > 0 else 0
    difficulty = 1 + endless_depth // 6 if endless else 1 + act_index
    profile = "Critical" if dissonance >= 75.0 else "Medium" if dissonance >= 40.0 else "Low"
    return GoldenStageRecipe(
        schema_version=SCHEMA_VERSION,
        act_index=act_index,
        stage_index=stage_index,
        endless_depth=endless_depth,
        stage_id=stage_id,
        room_definition_id=stage_id,
        room_data_id=room_data_id,
        encounter_id=f"Encounter_{enemy_id}",
        enemy_id=enemy_id,
        difficulty_tier=difficulty,
        mutator_ids=(),
        reward_pool_id="DissonanceHigh" if dissonance >= 50.0 else "CoreMixed",
        dissonance_profile_id=profile,
        companion_requirement="Resonance",
        stage_seed=seeds["stage"],
        topology_seed=seeds["topology"],
        room_seed=seeds["room"],
        enemy_seed=seeds["enemy"],
        reward_seed=seeds["reward"],
        mutator_seed=seeds["mutator"],
        cosmetic_seed=seeds["cosmetic"],
    )


def golden_recipe_trace(run_seed: int, count: int = 100) -> list[dict]:
    if count < 1:
        raise ValueError("count must be positive")
    return [
        build_stage_recipe(
            run_seed,
            stage,
            endless_depth=stage,
            endless=stage > 0,
        ).to_dict()
        for stage in range(count)
    ]
