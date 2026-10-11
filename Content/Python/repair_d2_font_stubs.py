#!/usr/bin/env python3
"""
repair_d2_font_stubs.py - Populate CompositeFont data for Font_KaiseiDecol and Font_KleeOne.

Resolves the font invisibility regression where WBP_Melodia_OverworldHUD was assigned
Font_KaiseiDecol and Font_KleeOne stubs that lacked CompositeFont typeface bindings.
Configures DefaultTypeface with the imported TrueType FontFace assets:
  - Font_KaiseiDecol -> F_KaiseiDecol (Regular, Medium, Bold)
  - Font_KleeOne     -> F_KleeOne (Regular, SemiBold)
Also verifies F_Melodia_UI composite bindings.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    import unreal
except ImportError:
    print("[repair_d2_font_stubs] Must be run within Unreal Engine context.")
    sys.exit(1)


def configure_font(asset_path: str, typefaces: list[tuple[str, str]], fallback_faces: list[tuple[str, str]] | None = None) -> dict:
    font = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not font:
        return {"asset": asset_path, "ok": False, "error": "Asset not found"}

    fonts_parts = []
    for slot_name, font_face_path in typefaces:
        fonts_parts.append(
            f'(Name="{slot_name}",Font=(FontFaceAsset="/Script/Engine.FontFace\'{font_face_path}.{font_face_path.split("/")[-1]}\'"))'
        )
    fonts_str = ",".join(fonts_parts)

    fb_str = ""
    if fallback_faces:
        fb_parts = []
        for fb_name, fb_path in fallback_faces:
            fb_parts.append(
                f'(Name="{fb_name}",Font=(FontFaceAsset="/Script/Engine.FontFace\'{fb_path}.{fb_path.split("/")[-1]}\'"))'
            )
        fb_str = f"Fonts=({','.join(fb_parts)})"

    cf_text = (
        f'(DefaultTypeface=(Fonts=({fonts_str})),'
        f'FallbackTypeface=(Typeface=({fb_str}),ScalingFactor=1.000000),'
        f'SubTypefaces=(),bEnableAscentDescentOverride=True)'
    )

    new_cf = unreal.CompositeFont()
    new_cf.import_text(cf_text)
    font.set_editor_property("composite_font", new_cf)

    try:
        font.post_edit_change()
    except Exception:
        pass

    saved = unreal.EditorAssetLibrary.save_loaded_asset(font)
    
    # Verify readback
    verify = unreal.EditorAssetLibrary.load_asset(asset_path)
    cf_readback = verify.get_editor_property("composite_font").export_text()
    
    slots_verified = [name for name, _ in typefaces if name in cf_readback]
    all_ok = len(slots_verified) == len(typefaces)

    return {
        "asset": asset_path,
        "saved": saved,
        "ok": all_ok,
        "slots_verified": slots_verified,
        "typefaces_count": len(typefaces)
    }


def main():
    print("=== [repair_d2_font_stubs] Repairing Font Stubs ===")
    
    results = {}

    fallbacks = [
        ("Regular", "/Engine/EngineFonts/Faces/DroidSansFallback"),
        ("Roboto", "/Engine/EngineFonts/Faces/RobotoRegular"),
    ]

    # 1. Font_KaiseiDecol
    kaisei_typefaces = [
        ("Regular", "/Game/Melodia/UI/Fonts/F_KaiseiDecol"),
        ("Medium", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Medium"),
        ("SemiBold", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Bold"),
        ("Bold", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Bold"),
        ("KaiseiDecol", "/Game/Melodia/UI/Fonts/F_KaiseiDecol"),
        ("KaiseiDecolRegular", "/Game/Melodia/UI/Fonts/F_KaiseiDecol"),
        ("KaiseiDecolMedium", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Medium"),
        ("KaiseiDecolBold", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Bold"),
    ]
    results["Font_KaiseiDecol"] = configure_font(
        "/Game/Melodia/UI/Fonts/Font_KaiseiDecol", kaisei_typefaces, fallbacks
    )

    # 2. Font_KleeOne
    klee_typefaces = [
        ("Regular", "/Game/Melodia/UI/Fonts/F_KleeOne"),
        ("SemiBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("Bold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("Medium", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("KleeOne", "/Game/Melodia/UI/Fonts/F_KleeOne"),
        ("KleeOneRegular", "/Game/Melodia/UI/Fonts/F_KleeOne"),
        ("KleeOneSemiBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("KleeOneBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
    ]
    results["Font_KleeOne"] = configure_font(
        "/Game/Melodia/UI/Fonts/Font_KleeOne", klee_typefaces, fallbacks
    )

    # 3. F_Melodia_UI
    melodia_typefaces = [
        ("Regular", "/Game/Melodia/UI/Fonts/F_KleeOne"),
        ("Medium", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Medium"),
        ("SemiBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("Bold", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Bold"),
        ("Syne", "/Game/Melodia/UI/Fonts/F_Syne"),
        ("InstrumentSerif", "/Game/Melodia/UI/Fonts/F_InstrumentSerif"),
        ("InstrumentSerifItalic", "/Game/Melodia/UI/Fonts/F_InstrumentSerifItalic"),
        ("TwinkleStar", "/Game/Melodia/UI/Fonts/F_TwinkleStar1"),
        ("KaiseiDecol", "/Game/Melodia/UI/Fonts/F_KaiseiDecol"),
        ("KaiseiDecolMedium", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Medium"),
        ("KaiseiDecolBold", "/Game/Melodia/UI/Fonts/F_KaiseiDecol_Bold"),
        ("KleeOne", "/Game/Melodia/UI/Fonts/F_KleeOne"),
        ("KleeOneSemiBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
        ("KleeOneBold", "/Game/Melodia/UI/Fonts/F_KleeOne_SemiBold"),
    ]
    results["F_Melodia_UI"] = configure_font(
        "/Game/Melodia/UI/Fonts/F_Melodia_UI", melodia_typefaces, fallbacks
    )

    print(json.dumps(results, indent=2))

    # Save audit report
    out_path = ROOT / "Saved" / "Audit" / "d2_font_stub_repair_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
