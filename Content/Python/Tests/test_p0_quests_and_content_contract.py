"""Test contract verification for P0 Playthrough, Wardrobe Equip, Companion Recruitment, and Sea Above Cutscene."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
NARRATIVE_DIR = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Narrative"
SPECS_DIR = PROJECT_ROOT / "specs"

NOTIFY_RE = re.compile(
    r"\$ Notify (melodia:(?:battle|quest|questcomplete|flag|travel|reward|stat|item):[^\s\r\n]+)"
)


class TestP0QuestsAndContentContract(unittest.TestCase):
    def setUp(self):
        self.p0_playthrough_path = NARRATIVE_DIR / "MelodiaQuillP0Playthrough.qsc"
        self.wardrobe_equip_path = NARRATIVE_DIR / "MelodiaQuillWardrobeEquip.qsc"
        self.companion_recruit_path = NARRATIVE_DIR / "MelodiaQuillChoralSheepRecruit.qsc"
        self.sea_above_cutscene_path = NARRATIVE_DIR / "MelodiaQuillSeaAboveCutscene.qsc"

        self.quests_spec_path = SPECS_DIR / "progression" / "melodia_p0_slice_quests.v1.json"
        self.wardrobe_manifest_path = SPECS_DIR / "wardrobe" / "wardrobe_equip_p0_manifest.v1.json"
        self.companion_manifest_path = SPECS_DIR / "companions" / "choral_sheep_recruit_manifest.v1.json"
        self.cutscene_manifest_path = SPECS_DIR / "cinematics" / "sea_above_cutscene_manifest.v1.json"

    def _verify_qsc_grammar(self, qsc_path: Path):
        self.assertTrue(qsc_path.is_file(), f"File missing: {qsc_path}")
        text = qsc_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("@ Start"), f"{qsc_path.name} must begin with '@ Start'")
        self.assertTrue(text.strip().endswith("$ End"), f"{qsc_path.name} must end with '$ End'")

        # Verify notification grammar
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
                # melodia:questcomplete:QuestId:CompletionFlagId:RewardId:IntentId:CheckpointId
                self.assertEqual(len(parts), 7, f"questcomplete verb requires 7 parts: {notif}")
            elif verb == "flag":
                # melodia:flag:FlagId:true|false
                self.assertEqual(len(parts), 4, f"flag verb requires 4 parts: {notif}")
                self.assertIn(parts[3].lower(), ["true", "false"], f"Flag value must be bool: {notif}")
            elif verb == "stat":
                # melodia:stat:IntentId:StatId:Delta
                self.assertEqual(len(parts), 5, f"stat verb requires 5 parts: {notif}")
                self.assertTrue(parts[4].lstrip("-").isdigit(), f"Stat delta must be integer: {notif}")
            elif verb == "item":
                # melodia:item:give:ItemId:Count
                self.assertEqual(len(parts), 5, f"item verb requires 5 parts: {notif}")
                self.assertEqual(parts[2].lower(), "give", f"item subverb must be 'give': {notif}")
                self.assertTrue(parts[4].isdigit(), f"Item count must be positive integer: {notif}")

    def test_p0_playthrough_qsc(self):
        """P0 Playthrough script adheres to grammar and notification contract."""
        self._verify_qsc_grammar(self.p0_playthrough_path)
        text = self.p0_playthrough_path.read_text(encoding="utf-8")
        self.assertIn("melodia:battle:melodia_smoke_encounter", text)
        self.assertIn("melodia:questcomplete:quest.first_dream:", text)
        self.assertIn("melodia:flag:flag.p0.playthrough.completed:true", text)

    def test_wardrobe_equip_qsc(self):
        """Wardrobe equip script grants item, equips outfit, and sets sorrow seam restoration flag."""
        self._verify_qsc_grammar(self.wardrobe_equip_path)
        text = self.wardrobe_equip_path.read_text(encoding="utf-8")
        self.assertIn("melodia:item:give:item.outfit.melusina_v2:1", text)
        self.assertIn("melodia:flag:flag.wardrobe.outfit_equipped:true", text)
        self.assertIn("melodia:flag:flag.melusina.sorrow_seam_restored:true", text)
        self.assertIn(
            "melodia:questcomplete:quest.wardrobe.equip_outfit:"
            "flag.wardrobe.equip_completed:reward.wardrobe.first_outfit:",
            text,
        )

    def test_companion_recruit_qsc(self):
        """Companion recruit script performs call-and-response and recruits Choral Sheep."""
        self._verify_qsc_grammar(self.companion_recruit_path)
        text = self.companion_recruit_path.read_text(encoding="utf-8")
        self.assertIn("melodia:stat:intent.choral_sheep.call_response:melodia_harmony:2", text)
        self.assertIn("melodia:flag:flag.companion.choral_sheep_recruited:true", text)
        self.assertIn(
            "melodia:questcomplete:quest.companion.choral_sheep:"
            "flag.companion.choral_sheep_completed:reward.companion.choral_sheep:",
            text,
        )

    def test_sea_above_cutscene_qsc(self):
        """Sea Above cutscene script transitions level and activates membrane pulse."""
        self._verify_qsc_grammar(self.sea_above_cutscene_path)
        text = self.sea_above_cutscene_path.read_text(encoding="utf-8")
        self.assertIn("melodia:travel:/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype", text)
        self.assertIn("melodia:stat:intent.sea_above.witness:melodia_resonance:5", text)
        self.assertIn("melodia:flag:flag.cutscene.sea_above_witnessed:true", text)
        self.assertIn("melodia:flag:flag.sea_above.membrane_pulse_active:true", text)
        self.assertIn(
            "melodia:questcomplete:quest.cutscene.sea_above:"
            "flag.cutscene.sea_above_completed:reward.cutscene.sea_above_memory:",
            text,
        )

    def test_progression_package_spec(self):
        """Progression package spec aligns with all 4 authored quests."""
        self.assertTrue(self.quests_spec_path.is_file())
        spec = json.loads(self.quests_spec_path.read_text(encoding="utf-8"))
        self.assertEqual(spec["schema"], "melodia.progression_package.v1")
        self.assertEqual(len(spec["quests"]), 4)

        quest_ids = [q["quest_id"] for q in spec["quests"]]
        self.assertIn("quest.first_dream", quest_ids)
        self.assertIn("quest.wardrobe.equip_outfit", quest_ids)
        self.assertIn("quest.companion.choral_sheep", quest_ids)
        self.assertIn("quest.cutscene.sea_above", quest_ids)

        for q in spec["quests"]:
            script_full = PROJECT_ROOT / q["script_path"]
            self.assertTrue(script_full.is_file(), f"Referenced script missing: {q['script_path']}")

    def test_wardrobe_manifest(self):
        """Wardrobe equip manifest defines slots and Glide capability."""
        self.assertTrue(self.wardrobe_manifest_path.is_file())
        data = json.loads(self.wardrobe_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "melodia.wardrobe_equip_p0.v1")
        self.assertEqual(data["resonant_form"]["capability_unlocked"], "Glide")
        self.assertTrue(data["traversal_impact"]["can_glide"])
        self.assertIn("Body", data["slots"])
        self.assertIn("Shirt", data["slots"])
        self.assertIn("Skirt", data["slots"])
        self.assertIn("Boots", data["slots"])
        self.assertIn("Accessories", data["slots"])

    def test_companion_manifest(self):
        """Companion recruit manifest links Choral Sheep pitch class and assets."""
        self.assertTrue(self.companion_manifest_path.is_file())
        data = json.loads(self.companion_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "melodia.companion_recruit.v1")
        self.assertEqual(data["pitch_class"], "C")
        self.assertEqual(data["semitone_offset"], 0)
        self.assertEqual(data["recruitment_contract"]["quest_id"], "quest.companion.choral_sheep")
        self.assertTrue(data["gameplay_hooks"]["party_follow_enabled"])

    def test_cutscene_manifest(self):
        """Cutscene manifest declares camera tracks and Sea Above pulse parameters."""
        self.assertTrue(self.cutscene_manifest_path.is_file())
        data = json.loads(self.cutscene_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "melodia.cutscene_manifest.v1")
        self.assertEqual(data["quest_binding"], "quest.cutscene.sea_above")
        self.assertEqual(len(data["camera_tracks"]), 3)
        self.assertEqual(data["presentation_effects"]["pulse_cycle_seconds"], 16.0)
        self.assertEqual(data["presentation_effects"]["membrane_sheen_range"], [0.18, 0.32])


if __name__ == "__main__":
    unittest.main()
