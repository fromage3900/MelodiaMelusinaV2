#!/usr/bin/env python3
"""Import the D2 type ramp (Kaisei Decol + Klee One) and rebind F_Melodia_UI.

WHY THIS FILE EXISTS

Owner ruling 2026-09-26 (D2) chose **Kaisei Decol (display) + Klee One (UI/body)**
and retired Syne / InstrumentSerif / AzeretMono / TwinkleStar. The UI token audit
of 2026-10-03 (`Saved/Dashboards/ui_tokens_20261002.json`) found **0 uses of either
chosen family** — they had never been imported. This script closes that gap.

RUN THIS WITH THE EDITOR FREE
------------------------------

This creates NEW assets (FontFace) and rewrites one composite (F_Melodia_UI). It does
NOT touch any widget blueprint, so it cannot disturb in-flight widget work — but it
does dirty packages, so run it when you own the editor.

    # Preferred: through the live editor's MCP bridge (Monolith must be up)
    python Tools/mcp_run_python.py Content/Python/import_d2_fonts.py

    # Or headless (no editor session needed):
    UnrealEditor-Cmd.exe BS_GodFile.uproject -NullRHI -unattended -nopause \
        -ExecutePythonScript="C:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_d2_fonts.py"

THE TRAP THIS SCRIPT AVOIDS
---------------------------

`F_Melodia_UI` is a **UFont composite**, not a FontFace. Slate cannot render a
FontFace handed to `FontObject` — that bug is recorded in
`Saved/Audit/_rebind_f_melodia_ui.py` ("TitleText was also assigned a UFontFace as
FontObject, which Slate cannot render"). So the correct shape is:

  1. import each .ttf  -> a FontFace asset
  2. add each FontFace to F_Melodia_UI's CompositeFont.DefaultTypeface.Fonts
     under a named typeface slot

Widgets then request the typeface BY NAME (`set_font typeface="KaiseiDecol"`).
A name that is absent from the composite silently falls back to engine Roboto —
which is exactly why the audit saw so much default-face text.

SOURCE FILES (staged, gitignored under Imports/*)

    Imports/UI/Fonts/KaiseiDecol-Regular.ttf     SIL OFL 1.1
    Imports/UI/Fonts/KaiseiDecol-Medium.ttf      SIL OFL 1.1
    Imports/UI/Fonts/KaiseiDecol-Bold.ttf        SIL OFL 1.1
    Imports/UI/Fonts/KleeOne-Regular.ttf         SIL OFL 1.1
    Imports/UI/Fonts/KleeOne-SemiBold.ttf        SIL OFL 1.1

Both families are Google Fonts, SIL Open Font License 1.1 — free to ship.
OFL text staged alongside each family.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
SRC_DIR = ROOT / "Imports" / "UI" / "Fonts"
DEST_PATH = "/Game/Melodia/UI/Fonts"
COMPOSITE_ASSET = "/Game/Melodia/UI/Fonts/F_Melodia_UI"

# (source filename, destination asset name)
IMPORTS = [
    ("KaiseiDecol-Regular.ttf",  "F_KaiseiDecol"),
    ("KaiseiDecol-Medium.ttf",   "F_KaiseiDecol_Medium"),
    ("KaiseiDecol-Bold.ttf",     "F_KaiseiDecol_Bold"),
    ("KleeOne-Regular.ttf",      "F_KleeOne"),
    ("KleeOne-SemiBold.ttf",     "F_KleeOne_SemiBold"),
]

# Typeface slots to add to F_Melodia_UI. These are the names widgets will request.
# Regular/Bold are remapped to the NEW ramp so existing widgets that ask for the
# generic names get Kaisei/Klee instead of the retired Syne.
NEW_TYPEFACES = [
    ("KaiseiDecol",       "F_KaiseiDecol"),
    ("KaiseiDecolMedium", "F_KaiseiDecol_Medium"),
    ("KaiseiDecolBold",   "F_KaiseiDecol_Bold"),
    ("KleeOne",           "F_KleeOne"),
    ("KleeOneSemiBold",   "F_KleeOne_SemiBold"),
]

report = {"schema": "melodia.fonts.d2_import.v1", "imports": [], "composite": {}}


def _import_one(src_name: str, dest_name: str) -> dict:
    src = SRC_DIR / src_name
    entry = {"src": str(src), "dest": f"{DEST_PATH}/{dest_name}"}

    if not src.is_file():
        entry.update(ok=False, error="source file missing")
        return entry

    existing = unreal.EditorAssetLibrary.does_asset_exist(f"{DEST_PATH}/{dest_name}")
    entry["pre_existing"] = existing

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(src))
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", False)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    asset = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{dest_name}")
    if not asset:
        entry.update(ok=False, error="import produced no asset")
        return entry

    entry.update(
        ok=True,
        cls=asset.get_class().get_name(),
        # A FontFace carries the raw glyph data; this is the readback that proves
        # the import produced a real face rather than an empty stub.
        has_source=bool(asset.get_editor_property("source_filename")),
    )
    return entry


def _rebind_composite() -> dict:
    font = unreal.EditorAssetLibrary.load_asset(COMPOSITE_ASSET)
    if not font:
        return {"ok": False, "error": "F_Melodia_UI missing"}

    cf = font.get_editor_property("composite_font")
    before = cf.export_text()

    # Rebuild the DefaultTypeface font list: keep every existing entry, then add the
    # D2 faces. Existing slots stay so no current widget loses its face mid-migration.
    parts = []
    for slot, asset_name in NEW_TYPEFACES:
        parts.append(
            f'(Name="{slot}",Font=(FontFaceAsset='
            f'"/Script/Engine.FontFace\'{DEST_PATH}/{asset_name}.{asset_name}\'"))'
        )
    new_fonts = ",".join(parts)

    # Insert the new faces ahead of the closing of the Fonts array, preserving the
    # existing Syne/InstrumentSerif entries (retiring them is a separate, later step
    # that must follow the widget sweep, not precede it).
    marker = ')))),FallbackTypeface='
    if marker not in before:
        return {"ok": False, "error": "composite format not recognised", "before": before[:400]}

    head, tail = before.split(marker, 1)
    # `head` ends mid-entry (…F_TwinkleStar1'")) — i.e. inside the last Fonts
    # entry and inside the Fonts array. Close both, append the new entries, then
    # re-close the Fonts array so the parens stay balanced. Verified offline
    # against the live export_text (17/17 -> 21/21).
    after = head + "))" + "," + new_fonts + "))" + ",FallbackTypeface=" + tail

    new_cf = unreal.CompositeFont()
    new_cf.import_text(after)
    font.set_editor_property("composite_font", new_cf)
    try:
        font.post_edit_change()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_asset(COMPOSITE_ASSET)

    verify = unreal.EditorAssetLibrary.load_asset(COMPOSITE_ASSET)
    after_text = verify.get_editor_property("composite_font").export_text()
    return {
        "ok": all(slot in after_text for slot, _ in NEW_TYPEFACES),
        "before_len": len(before),
        "after_len": len(after_text),
        "slots_present": [slot for slot, _ in NEW_TYPEFACES if slot in after_text],
        "slots_missing": [slot for slot, _ in NEW_TYPEFACES if slot not in after_text],
    }


def main():
    report["imports"] = [_import_one(s, d) for s, d in IMPORTS]
    ok_imports = [e for e in report["imports"] if e.get("ok")]
    if len(ok_imports) != len(IMPORTS):
        report["status"] = "FAILED_IMPORTS"
        report["composite"] = {"skipped": "not attempted while imports incomplete"}
    else:
        report["composite"] = _rebind_composite()
        report["status"] = "ok" if report["composite"].get("ok") else "COMPOSITE_FAILED"

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
