import os
import re
import unittest

class TestQuillPresentationAndCursor(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        self.default_game_ini = os.path.join(self.project_root, "Config", "DefaultGame.ini")
        self.default_engine_ini = os.path.join(self.project_root, "Config", "DefaultEngine.ini")

    def test_default_game_ini_quill_script_settings(self):
        """Verifies that DefaultGame.ini configures QuillscriptSettings ScriptSettings with Melodia UI."""
        self.assertTrue(os.path.exists(self.default_game_ini), f"Missing {self.default_game_ini}")
        with open(self.default_game_ini, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("[/Script/Quillscript.QuillscriptSettings]", content)
        self.assertIn("ScriptSettings=", content)
        self.assertIn("/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog.WBP_MelodiaQuillDialog_C", content)
        self.assertIn("/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection.WBP_MelodiaQuillSelection_C", content)
        self.assertIn("/Game/Melodia/UI/Quill/WBP_MelodiaQuillBackground.WBP_MelodiaQuillBackground_C", content)

    def test_default_engine_ini_software_cursors(self):
        """Verifies that DefaultEngine.ini configures SoftwareCursors map for Default, Hand, and Crosshairs."""
        self.assertTrue(os.path.exists(self.default_engine_ini), f"Missing {self.default_engine_ini}")
        with open(self.default_engine_ini, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("[/Script/Engine.UserInterfaceSettings]", content)
        self.assertIn("SoftwareCursors=", content)
        self.assertIn("WBP_MelodiaCursor", content)
        self.assertIn("WBP_MelodiaCursorInteract", content)

    def test_melodia_quill_wbp_assets_exist(self):
        """Verifies that all 4 Melodia Quill UI WBP assets exist in the Content directory."""
        wbp_files = [
            "Content/Melodia/UI/Quill/WBP_MelodiaQuillDialog.uasset",
            "Content/Melodia/UI/Quill/WBP_MelodiaQuillSelection.uasset",
            "Content/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry.uasset",
            "Content/Melodia/UI/Quill/WBP_MelodiaQuillBackground.uasset",
            "Content/Melodia/UI/Cursor/WBP_MelodiaCursor.uasset",
            "Content/Melodia/UI/Cursor/WBP_MelodiaCursorInteract.uasset",
        ]
        for rel_path in wbp_files:
            full_path = os.path.join(self.project_root, rel_path)
            self.assertTrue(os.path.exists(full_path), f"Required asset missing: {full_path}")

if __name__ == "__main__":
    unittest.main()
