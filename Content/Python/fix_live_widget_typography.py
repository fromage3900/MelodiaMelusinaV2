"""Fix live widget typography: slideshow -> F_Melodia_UI composite, MainMenu buttons -> styled chrome.

Why:
- polish_melodia_opening_slideshow.py never passed font_family (its FontFace comment is
  stale since the 2026-08-13 composite fix), so all slideshow text stayed on engine Roboto.
- WBP_MainMenu button labels already carry F_Melodia_UI/Syne, but every Button has
  WidgetStyle null + default content padding, so labels render blank/greyed (and
  Continue/LoadGame are intentionally disabled until a save slot passes PIE).

Idempotent. Run through Monolith with the editor open.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Tools")
sys.path.insert(0, str(HERE))
from mcp_client import monolith

FAMILY = "/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI"
PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"

SLIDESHOW = "/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow"
MAINMENU = "/Game/Melodia/UI/WBP_MainMenu"


def call(action, params, timeout=120):
    raw = monolith("ui_query", {"action": action, "params": params}, timeout=timeout)
    if isinstance(raw, str) and raw.startswith("ERROR"):
        return {"error": raw}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return {"raw": str(raw)[:600]}


def set_font(asset, widget, typeface, size, tracking=0, outline=None):
    p = {
        "asset_path": asset,
        "widget_name": widget,
        "font_family": FAMILY,
        "typeface": typeface,
        "font_size": size,
        "compile": False,
    }
    if tracking:
        p["letter_spacing"] = tracking
    if outline:
        p["outline_size"] = outline["size"]
        p["outline_color"] = outline["color"]
    return call("set_font", p)


print("=== SLIDESHOW: migrate Roboto -> F_Melodia_UI composite ===")
slide_results = []
# Title -> Syne; kicker/body -> InstrumentSerif (SSOT roles); buttons -> Syne.
for name, face, size, tracking in (
    ("KickerText", "InstrumentSerif", 18, 180),
    ("TitleText", "Syne", 48, 20),
    ("BodyText", "InstrumentSerif", 25, 0),
    ("AdvanceLabel", "Syne", 20, 60),
    ("SkipLabel", "Syne", 17, 80),
):
    r = set_font(SLIDESHOW, name, face, size, tracking)
    slide_results.append({"widget": name, "face": face, "set": r})

print("=== MAIN MENU: give buttons Melodia chrome (parchment pill + gold) ===")
menu_results = []
for name in ("Btn_Continue", "Btn_NewGame", "Btn_LoadGame", "Btn_Settings"):
    for state, tint in (
        ("Normal", "#745A83F2"),
        ("Hovered", "#9975A7FF"),
        ("Pressed", "#5B4668FF"),
        ("Disabled", "#3A335099"),
    ):
        r = call("set_brush", {
            "asset_path": MAINMENU,
            "widget_name": name,
            "property_name": f"WidgetStyle.{state}",
            "texture_path": PARCHMENT,
            "draw_type": "Box",
            "margin": {"left": 0.28, "top": 0.28, "right": 0.28, "bottom": 0.28},
            "tint_color": tint,
            "compile": False,
        })
    # Label color must be readable on the pill in every state.
    for name_lbl, color in (
        ("BtnLabel_Continue", "#FFF9F3FF"),
        ("BtnLabel_NewGame", "#FFF9F3FF"),
        ("BtnLabel_LoadGame", "#FFF9F3FF"),
        ("BtnLabel_Settings", "#FFF9F3FF"),
    ):
        pass  # labels already carry ColorAndOpacity gold; keep.
    menu_results.append({"widget": name, "styled": True})

# Re-assert button label font (F_Melodia_UI/Syne) explicitly so nothing regressed.
for name in ("BtnLabel_Continue", "BtnLabel_NewGame", "BtnLabel_LoadGame", "BtnLabel_Settings"):
    menu_results.append({"widget": name, "font": set_font(MAINMENU, name, "Syne", 19, 70)})

print("=== compile + save ===")
for asset in (SLIDESHOW, MAINMENU):
    comp = call("compile_widget", {"asset_path": asset})
    errs = (comp.get("error_count") if isinstance(comp, dict) else "?") or (
        len(comp.get("errors", [])) if isinstance(comp, dict) else "?"
    )
    saved = monolith("blueprint_query", {"action": "save_asset", "asset_path": asset}, timeout=120)
    print(f"{asset} -> compile_error_count={errs} save={str(saved)[:120]}")

print(json.dumps({"slideshow": slide_results, "mainmenu": menu_results}, indent=2, default=str)[:6000])
