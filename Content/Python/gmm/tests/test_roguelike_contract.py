from __future__ import annotations

from gmm.game.roguelike_contract import (
    SALTS,
    build_stage_recipe,
    derive_seed,
    golden_recipe_trace,
)


def test_seed_streams_are_deterministic_and_independent():
    first = {name: derive_seed(39017, 12, salt) for name, salt in SALTS.items()}
    second = {name: derive_seed(39017, 12, salt) for name, salt in SALTS.items()}
    assert first == second
    assert len(set(first.values())) == len(first)


def test_cosmetic_seed_cannot_change_gameplay_fields():
    recipe = build_stage_recipe(7331, 9, endless=True, endless_depth=9)
    changed_cosmetic = derive_seed(7331, 9, SALTS["cosmetic"] ^ 0x01010101)
    assert changed_cosmetic != recipe.cosmetic_seed
    assert recipe.room_seed == derive_seed(7331, 9, SALTS["room"])
    assert recipe.enemy_seed == derive_seed(7331, 9, SALTS["enemy"])
    assert recipe.reward_seed == derive_seed(7331, 9, SALTS["reward"])


def test_first_100_recipe_trace_is_reproducible():
    assert golden_recipe_trace(1337, 100) == golden_recipe_trace(1337, 100)
    assert golden_recipe_trace(1337, 100) != golden_recipe_trace(7331, 100)
    assert len(golden_recipe_trace(1337, 100)) == 100


def test_structured_and_endless_contract_fields():
    structured = build_stage_recipe(42, 0)
    assert structured.stage_id == "SakuraThreshold"
    assert structured.enemy_id == "SakuraPhantom"
    endless = build_stage_recipe(42, 18, endless=True, endless_depth=18, dissonance=80)
    assert endless.difficulty_tier == 4
    assert endless.dissonance_profile_id == "Critical"
    assert endless.reward_pool_id == "DissonanceHigh"
