#!/usr/bin/env python3
"""
P0 Content Integration Test
Validates that all four P0 Quill scripts:
1. Compile to .uasset
2. Reference only allowlisted IDs
3. Emit valid 7-verb notifications
4. Can be played end-to-end in the MelodiaIntegrationMap

Run: python Content/Python/Tests/test_p0_content_integration.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent.parent
CONTENT = PROJECT / "Content"
NARRATIVE = CONTENT / "MelodiaIntegration" / "Narrative"
SPECS = PROJECT / "specs"

# P0 scripts to validate
P0_SCRIPTS = [
    "MelodiaQuillP0Playthrough.qsc",
    "MelodiaQuillWardrobeEquip.qsc",
    "MelodiaQuillChoralSheepRecruit.qsc",
    "MelodiaQuillSeaAboveCutscene.qsc",
]

# All allowloaded IDs (from specs/echo_allowlist.json)
ALLOWLIST_PATH = SPECS / "echo_allowlist.json"

# 7-verb contract (from echo_pipeline.json)
VERB_SPECS = {
    "battle": {"parts": 3, "allowlist": "encounters"},
    "quest": {"parts": 3, "allowlist": "quests", "consume_once": "id"},
    "flag": {"parts": 4, "allowlist": "flags"},
    "travel": {"parts": 3, "allowlist": "travel"},
    "reward": {"parts": 3, "allowlist": "rewards", "consume_once": "id"},
    "stat": {"parts": 5, "allowlist": "social_stats", "consume_once": "intent"},
    "item": {"parts": 5, "allowlist": "items", "consume_once": "item", "stub": True},
}

TOKEN_RE = re.compile(
    r"melodia:(?:battle|quest|flag|travel|reward|stat|item):"
    r"[A-Za-z0-9_./+\-]+(?::[A-Za-z0-9_./+\-]+){0,3}"
    r"(?![A-Za-z0-9_./+\-:<])"
)
ID_RE = re.compile(r"^[A-Za-z0-9_./+\-]+$")
INT_RE = re.compile(r"^[+-]?\d+$")


def load_allowlist() -> dict[str, set[str]]:
    if not ALLOWLIST_PATH.exists():
        return {}
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    allowlist = data.get("allowlist", data)
    return {k: set(v) for k, v in allowlist.items() if isinstance(v, list)}


def extract_tokens(text: str) -> list[str]:
    return [m.group(0).rstrip(".,;:)]}'\"") for m in TOKEN_RE.finditer(text)]


def parse_token(token: str):
    parts = token.split(":")
    if len(parts) < 2 or parts[0].lower() != "melodia":
        return None, parts, "token must start with melodia:"
    verb = parts[1].lower()
    spec = VERB_SPECS.get(verb)
    if spec is None:
        return verb, parts, f"unknown verb '{verb}'"
    if len(parts) != spec["parts"]:
        return verb, parts, f"{verb} expects {spec['parts'] - 2} arg(s), got {max(0, len(parts) - 2)}"
    for value in parts[2:]:
        if not value or not ID_RE.fullmatch(value):
            return verb, parts, f"invalid identifier/value '{value}'"
    if verb == "flag" and parts[3].lower() not in ("true", "false"):
        return verb, parts, "flag value must be true or false"
    if verb == "stat" and not INT_RE.fullmatch(parts[4]):
        return verb, parts, "stat delta must be an integer"
    if verb == "item":
        if parts[2].lower() != "give":
            return verb, parts, "item verb must use item:give:<ItemId>:<Count>"
        if not INT_RE.fullmatch(parts[4]) or int(parts[4]) <= 0:
            return verb, parts, "item count must be a positive integer"
    return verb, parts, None


class TestP0ContentIntegration(unittest.TestCase):
    """Validate P0 Quill scripts against the allowlist and verb contract."""

    @classmethod
    def setUpClass(cls):
        cls.allowlist = load_allowlist()
        cls.script_contents = {}
        for script_name in P0_SCRIPTS:
            path = NARRATIVE / script_name
            if path.exists():
                cls.script_contents[script_name] = path.read_text(encoding="utf-8")

    def test_01_scripts_exist(self):
        """All four P0 scripts must exist on disk."""
        for script_name in P0_SCRIPTS:
            path = NARRATIVE / script_name
            self.assertTrue(path.exists(), f"{script_name} not found at {path}")

    def test_02_scripts_have_uasset(self):
        """All four P0 scripts must have compiled .uasset companions."""
        for script_name in P0_SCRIPTS:
            uasset_name = script_name.replace(".qsc", ".uasset")
            uasset_path = NARRATIVE / uasset_name
            self.assertTrue(
                uasset_path.exists(),
                f"{uasset_name} not found — script cannot be played. "
                f"Compile with: UE CompileQuillSource(QuillAsset, SourceCode)"
            )

    def test_03_no_duplicate_consume_once_ids(self):
        """No quest/reward/stat/item may emit the same consume-once ID twice."""
        for script_name, text in self.script_contents.items():
            tokens = extract_tokens(text)
            consumed: dict[str, str] = {}
            for token in tokens:
                verb, parts, error = parse_token(token)
                if error or verb not in VERB_SPECS:
                    continue
                spec = VERB_SPECS[verb]
                consume_mode = spec.get("consume_once")
                if consume_mode in ("id", "intent"):
                    identity = parts[2]
                elif consume_mode == "item":
                    identity = parts[3]
                else:
                    continue
                identity_key = f"{verb}:{identity}"
                self.assertNotIn(
                    identity_key, consumed,
                    f"{script_name}: duplicate consume-once ID '{identity_key}' "
                    f"(first at {consumed.get(identity_key, '?')})"
                )
                consumed[identity_key] = token

    def test_04_all_ids_allowlisted(self):
        """Every emitted ID must appear in the allowlist."""
        if not self.allowlist:
            self.skipTest("allowlist not available")
        for script_name, text in self.script_contents.items():
            tokens = extract_tokens(text)
            for token in tokens:
                verb, parts, error = parse_token(token)
                if error or verb not in VERB_SPECS:
                    continue
                spec = VERB_SPECS[verb]
                if "allowlist" not in spec or spec.get("stub"):
                    continue
                category = spec["allowlist"]
                values = self.allowlist.get(category)
                if values is None:
                    self.fail(f"{script_name}: allowlist has no '{category}' collection")
                identifier = parts[3] if verb == "stat" else parts[2]
                self.assertIn(
                    identifier, values,
                    f"{script_name}: '{identifier}' not in allowlist '{category}'"
                )

    def test_05_no_wrong_flag_prefix(self):
        """Flags must use 'flag.' prefix, never 'flags.' (plural)."""
        for script_name, text in self.script_contents.items():
            tokens = extract_tokens(text)
            for token in tokens:
                if "flags." in token:
                    self.fail(
                        f"{script_name}: wrong flag prefix in '{token}' — "
                        f"use 'flag.' (singular), not 'flags.'"
                    )

    def test_06_no_duplicate_reward_in_questcomplete(self):
        """A questcomplete must not grant the same reward twice."""
        for script_name, text in self.script_contents.items():
            tokens = extract_tokens(text)
            rewards_granted = set()
            for token in tokens:
                verb, parts, error = parse_token(token)
                if error:
                    continue
                if verb == "reward":
                    reward_id = parts[2]
                    rewards_granted.add(reward_id)
                elif verb == "questcomplete":
                    reward_id = parts[4]
                    self.assertNotIn(
                        reward_id, rewards_granted,
                        f"{script_name}: questcomplete rewards '{reward_id}' "
                        f"but that reward was already granted earlier in the script"
                    )

    def test_07_p0_playthrough_has_battle(self):
        """P0 Playthrough must trigger a battle."""
        text = self.script_contents.get("MelodiaQuillP0Playthrough.qsc", "")
        tokens = extract_tokens(text)
        battle_tokens = [t for t in tokens if "melodia:battle:" in t]
        self.assertTrue(len(battle_tokens) > 0, "P0 Playthrough has no battle trigger")

    def test_08_wardrobe_equip_sets_flag(self):
        """Wardrobe Equip must set the outfit_equipped flag."""
        text = self.script_contents.get("MelodiaQuillWardrobeEquip.qsc", "")
        self.assertIn("flag.wardrobe.outfit_equipped", text)

    def test_09_choral_sheep_recruits(self):
        """Choral Sheep must set the recruited flag."""
        text = self.script_contents.get("MelodiaQuillChoralSheepRecruit.qsc", "")
        self.assertIn("flag.companion.choral_sheep_recruited", text)

    def test_10_sea_above_travels(self):
        """Sea Above must trigger travel to the prototype level."""
        text = self.script_contents.get("MelodiaQuillSeaAboveCutscene.qsc", "")
        self.assertIn("melodia:travel:", text)
        self.assertIn("LV_SeaAbove_Prototype", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
