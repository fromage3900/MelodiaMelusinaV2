"""Test contract verification for Shorewake Questline, Wardrobe Dress, and Sea Above Integration."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
NARRATIVE_DIR = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Narrative"
SPECS_DIR = PROJECT_ROOT / "specs"
TEXTURES_DIR = PROJECT_ROOT / "Content" / "Melodia" / "Characters" / "Melusina" / "Textures" / "Clothes"

NOTIFY_RE = re.compile(
    r"\$ Notify (melodia:(?:battle|quest|questcomplete|flag|travel|reward|stat|item):[^\s\r\n]+)"
)


class TestShorewakeQuestContract(unittest.TestCase):
    def setUp(self):
        self.shorewake_qsc_path = NARRATIVE_DIR / "Shorewake" / "MelodiaQuillShorewake.qsc"
        self.quest_spec_path = SPECS_DIR / "progression" / "melodia_shorewake_quest.v1.json"
        self.wardrobe_manifest_path = SPECS_DIR / "wardrobe" / "wardrobe_shorewake_manifest.v1.json"
        self.allowlist_spec_path = SPECS_DIR / "echo_allowlist.json"

    def _verify_qsc_grammar(self, qsc_path: Path):
        self.assertTrue(qsc_path.is_file(), f"File missing: {qsc_path}")
        text = qsc_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("@ Start"), f"{qsc_path.name} must begin with '@ Start'")
        self.assertTrue(text.strip().endswith("$ End"), f"{qsc_path.name} must end with '$ End'")

        notifications = NOTIFY_RE.findall(text)
        self.assertGreater(len(notifications), 0, f"No valid notifications in {qsc_path.name}")
        for notif in notifications:
            parts = notif.split(":")
            self.assertEqual(parts[0], "melodia", f"Invalid prefix: {notif}")
            verb = parts[1]
            self.assertIn(
                verb,
                ["battle", "quest", "questcomplete", "flag", "travel", "reward", "stat", "item"],
                f"Invalid verb '{verb}' in {notif}",
            )
            if verb == "questcomplete":
                self.assertEqual(len(parts), 7, f"questcomplete verb requires 7 parts: {notif}")
            elif verb == "flag":
                self.assertEqual(len(parts), 4, f"flag verb requires 4 parts: {notif}")
                self.assertIn(parts[3].lower(), ["true", "false"], f"Flag value must be bool: {notif}")
            elif verb == "stat":
                self.assertEqual(len(parts), 5, f"stat verb requires 5 parts: {notif}")
                self.assertTrue(parts[4].lstrip("-").isdigit(), f"Stat delta must be integer: {notif}")
            elif verb == "item":
                self.assertEqual(len(parts), 5, f"item verb requires 5 parts: {notif}")
                self.assertEqual(parts[2].lower(), "give", f"item subverb must be 'give': {notif}")
                self.assertTrue(parts[4].isdigit(), f"Item count must be positive integer: {notif}")

    def test_shorewake_qsc_grammar_and_notifications(self):
        """Shorewake QuillScript adheres to strict 7-verb notification grammar and flow."""
        self._verify_qsc_grammar(self.shorewake_qsc_path)
        text = self.shorewake_qsc_path.read_text(encoding="utf-8")
        self.assertIn("melodia:item:give:item.outfit.shorewake:1", text)
        self.assertIn("melodia:stat:intent.shorewake.resonance:melodia_resonance:5", text)
        self.assertIn("melodia:flag:flag.quest.shorewake_completed:true", text)
        self.assertIn("melodia:flag:flag.sea_above.starskiff_ready:true", text)
        self.assertIn(
            "melodia:questcomplete:quest.shorewake.initiation:"
            "flag.quest.shorewake_completed:reward.shorewake_weave:"
            "intent.shorewake.complete:checkpoint.shorewake.complete",
            text,
        )

    def test_shorewake_progression_spec(self):
        """Shorewake progression spec defines chapter, prerequisite, and quest structure."""
        self.assertTrue(self.quest_spec_path.is_file(), "Shorewake progression spec missing")
        spec = json.loads(self.quest_spec_path.read_text(encoding="utf-8"))
        self.assertEqual(spec["schema"], "melodia.progression_package.v1")
        self.assertEqual(spec["package"]["package_id"], "package.shorewake_quest.progression")
        self.assertEqual(len(spec["quests"]), 1)

        quest = spec["quests"][0]
        self.assertEqual(quest["quest_id"], "quest.shorewake.initiation")
        self.assertEqual(quest["completion_flag"], "flag.quest.shorewake_completed")
        self.assertEqual(quest["reward_id"], "reward.shorewake_weave")
        self.assertEqual(quest["intent_id"], "intent.shorewake.complete")
        self.assertEqual(quest["checkpoint_id"], "checkpoint.shorewake.complete")

        script_path = PROJECT_ROOT / quest["script_path"]
        self.assertTrue(script_path.is_file(), f"Referenced script missing: {quest['script_path']}")

    def test_shorewake_wardrobe_manifest(self):
        """Shorewake wardrobe manifest defines Cos_ShorewakeDress and required textures."""
        self.assertTrue(self.wardrobe_manifest_path.is_file(), "Shorewake wardrobe manifest missing")
        manifest = json.loads(self.wardrobe_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "melodia.wardrobe_shorewake.v1")
        self.assertEqual(manifest["slots"]["Skirt"]["cosmetic_id"], "Cos_ShorewakeDress")
        self.assertTrue(manifest["traversal_impact"]["can_board_starskiff"])

    def test_shorewake_textures_present_on_disk(self):
        """All 4 Shorewake dress texture maps are cooked and present on disk."""
        expected_textures = [
            "T_MelusinaC_DressShorewake_BaseColor.png",
            "T_MelusinaC_DressShorewake_Normal.png",
            "T_MelusinaC_DressShorewake_Roughness.png",
            "T_MelusinaC_DressShorewake_Emission.png",
        ]
        for tex in expected_textures:
            tex_path = TEXTURES_DIR / tex
            self.assertTrue(tex_path.is_file(), f"Expected texture missing on disk: {tex_path}")
            self.assertGreater(tex_path.stat().st_size, 0, f"Texture is empty: {tex_path}")

    def test_allowlist_spec_contains_shorewake_ids(self):
        """Allowlist JSON specification contains all Shorewake identifiers."""
        self.assertTrue(self.allowlist_spec_path.is_file())
        allowlist_data = json.loads(self.allowlist_spec_path.read_text(encoding="utf-8"))["allowlist"]
        self.assertIn("quest.shorewake.initiation", allowlist_data["quests"])
        self.assertIn("flag.quest.shorewake_completed", allowlist_data["flags"])
        self.assertIn("flag.sea_above.starskiff_ready", allowlist_data["flags"])
        self.assertIn("reward.shorewake_weave", allowlist_data["rewards"])


if __name__ == "__main__":
    unittest.main()
