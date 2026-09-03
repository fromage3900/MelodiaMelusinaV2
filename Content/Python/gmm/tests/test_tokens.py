"""Deterministic token contract and reward tests."""
from __future__ import annotations

import unittest

from gmm.game.battle_manager import MelodiaBattleManager
from gmm.game.tokens import get_token_def


class TestTokenDefinitions(unittest.TestCase):
    def test_all_authored_variants_have_their_own_material(self):
        """Every authored variant resolves its own material instance.

        This test previously asserted the opposite - that star/swirl/water had an empty
        `material_path` and fell back to heart - which encoded a known asset gap as an
        invariant. The authored instances were created 2026-08-01 on
        M_Master_Toon_Universal, so the contract now asserts the intended end state:
        each variant points at its own material and nothing silently borrows heart's.
        """
        seen = {}
        for token_id in ("heart", "star", "swirl", "water"):
            token = get_token_def(token_id)
            self.assertIsNotNone(token, token_id)
            self.assertTrue(token.material_path, f"{token_id} has no material_path")
            self.assertFalse(
                token.material_fallback,
                f"{token_id} still declares a fallback but has its own material",
            )
            self.assertNotIn(
                token.material_path, seen,
                f"{token_id} shares a material with {seen.get(token.material_path)}",
            )
            seen[token.material_path] = token_id

    def test_unknown_token_is_none(self):
        self.assertIsNone(get_token_def("not_a_token"))


class TestTokenRewards(unittest.TestCase):
    def test_victory_rewards_are_not_granted_twice(self):
        manager = MelodiaBattleManager()
        manager.start_encounter("CrystalShard")
        manager.enemy_hp = 0.0
        manager.phase = "Victory"
        manager._on_victory()
        first = manager.player.token_wallet.to_dict()
        manager._on_victory()
        self.assertEqual(manager.player.token_wallet.to_dict(), first)

    def test_wallet_spending_is_bounded(self):
        manager = MelodiaBattleManager()
        wallet = manager.player.token_wallet
        self.assertFalse(wallet.spend_mana(wallet.mana_max + 1))
        self.assertFalse(wallet.spend_shard("Tide", 1))
        wallet.add_shard("Tide", 2)
        self.assertTrue(wallet.spend_shard("Tide", 1))
        self.assertEqual(wallet.shards["Tide"], 1)

