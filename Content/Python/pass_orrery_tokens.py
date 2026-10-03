#!/usr/bin/env python3
"""WBP_ComicOrrery token pass — colors to Melodia tokens, fonts to the D2 ramp.

Generated 2026-10-03 from the UI token audit (`Saved/Dashboards/ui_tokens_20261002.json`).
Target: `/Game/Melodia/UI/WBP_ComicOrrery` — the storybook Orrery hub (W3 in
`.hermes/plans/2026-09-26_storybook-ui-work-plan.md`).

BEFORE (live read, 2026-10-03)
-----------------------------
Every label was engine **Roboto** and every label color was off-palette cyan/teal:

    TXT_SPH_Sakura/Stage/Celestial/Village   #00EBFF  Roboto Regular 18
    TXT_Menu_QuestJournal/SkillCodex/Settings #00D69E  Roboto Regular 16
    OrreryKicker                             #00D69E  Roboto Regular 17
    OrreryTitle                              #00D69E  Roboto Regular 46
    OrreryInstruction                        #00D69E  Roboto Regular 19

Two independent defects, and the second is why the first was invisible:
  1. off-palette colors (cyan #00EBFF / teal #00D69E are not in tokens.json)
  2. FontObject pointed at `/Engine/EngineFonts/Roboto.Roboto` — the engine default

THE FONT RECIPE (this is the part that is easy to get wrong)
------------------------------------------------------------
`ui_query set_font` resolves **UFont composites, not FontFace assets**. Passing
`/Game/Melodia/UI/Fonts/F_KaiseiDecol` fails with "Font asset not found" — that asset
is a *FontFace*. The working call is:

    font_family = "/Game/Melodia/UI/Fonts/F_Melodia_UI"   # the UFont composite
    typeface    = "KaiseiDecol"                            # the named slot

The named slots were added by `Content/Python/import_d2_fonts.py`. A typeface name
that is absent from the composite silently falls back to Roboto.

TOKEN MAPPING (dark theme — the Orrery is a night surface)
----------------------------------------------------------
The Orrery is the Night-themed storybook cover, so the dark semantic roles apply:

    text.primary   dark = ivory.50  #FCFBF8
    text.secondary dark = slate.300 #AEB4BF
    text.accent    dark = gold.300  #DDC79B
    accent.primary      = gold.500  #C9A86A

Sphere labels and menu labels are the primary interactive text -> ivory.50.
Kicker/instruction are supporting copy -> slate.300.
Title is the storybook display line -> gold.300 (display emphasis).
Cyan/teal are removed entirely; they are not in the token set.

SAFETY
------
* Backup written before any mutation:
  `…/scratch/orrery_backup_20261003/WBP_ComicOrrery_BEFORE.uasset` (md5 eb665fce…).
* Colors are authored as `#RRGGBB` (Slate FSlateColor accepts hex in this pipeline).
* `compile=False` on every write, one compile at the end (compile wipes CDO overrides
  set before it — the melodia-ui-artist §4 ordering trap).

RUN IT FROM AN OS PROCESS — NOT via run_python
----------------------------------------------
This script calls `mcp_client.monolith(...)`, i.e. HTTP into the live editor. If it is
launched with `Tools/mcp_run_python.py`, it exec()s *inside* the editor's Python and then
tries to HTTP back into the same Monolith server from the same thread — a self-call that
fails with `WinError 10061 connection refused` on every step while still reporting
`MCP_RUN_PYTHON_STATUS=OK`. Correct invocation is a plain OS python process:

    python Content/Python/pass_orrery_tokens.py
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Tools")
from mcp_client import monolith  # noqa: E402

ASSET = "/Game/Melodia/UI/WBP_ComicOrrery"
COMPOSITE = "/Game/Melodia/UI/Fonts/F_Melodia_UI"

# Tokens (melodia-design-system/tokens.json)
IVORY_50 = "#FCFBF8"    # text.primary (dark)
SLATE_300 = "#AEB4BF"   # text.secondary (dark)
GOLD_300 = "#DDC79B"    # text.accent (dark)
GOLD_500 = "#C9A86A"    # accent.primary

# (widget, typeface slot, size, color)
# Kaisei Decol = display; Klee One = UI/body (owner D2 ruling 2026-09-26).
TEXT = [
    # Sphere labels — primary interactive text
    ("TXT_SPH_Sakura",        "KleeOne",       18, IVORY_50),
    ("TXT_SPH_Stage",         "KleeOne",       18, IVORY_50),
    ("TXT_SPH_Celestial",     "KleeOne",       18, IVORY_50),
    ("TXT_SPH_Village",       "KleeOne",       18, IVORY_50),
    # Menu labels — primary interactive text
    ("TXT_Menu_QuestJournal", "KleeOne",       16, IVORY_50),
    ("TXT_Menu_SkillCodex",   "KleeOne",       16, IVORY_50),
    ("TXT_Menu_Settings",     "KleeOne",       16, IVORY_50),
    # Storybook display + supporting copy
    ("OrreryTitle",           "KaiseiDecolBold", 46, GOLD_300),
    ("OrreryKicker",          "KleeOne",       17, SLATE_300),
    ("OrreryInstruction",     "KleeOne",       19, SLATE_300),
]


def ui(action, **kw):
    payload = {"action": action, "asset_path": ASSET}
    payload.update(kw)
    raw = monolith("ui_query", payload, timeout=90)
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": str(raw)[:200]}


def main():
    report = {"schema": "melodia.ui.orrery_token_pass.v1", "asset": ASSET,
              "fingerprint_before": "50ee265f554909f500bc7d2826462f591e5f395c", "steps": []}

    for name, typeface, size, color in TEXT:
        rf = ui("set_font", widget_name=name, font_family=COMPOSITE,
                typeface=typeface, font_size=size, compile=False)
        rc = ui("set_widget_property", widget_name=name, property_name="ColorAndOpacity",
                value=color, raw_mode=True, compile=False)
        report["steps"].append({"widget": name, "typeface": typeface, "size": size,
                                "color": color, "font_result": rf, "color_result": rc})
        ok_f = "properties_set" in str(rf)
        ok_c = "properties_set" in str(rc) or "success" in str(rc)
        print(f"  {name:24} {typeface:16} {size:>3} {color}  "
              f"font={'ok' if ok_f else rf}  color={'ok' if ok_c else rc}", flush=True)

    # One compile at the end — compile wipes CDO overrides, so nothing may be set after it.
    report["compile"] = ui("compile_widget")
    raw = monolith("blueprint_query", {"action": "save_asset", "asset_path": ASSET}, timeout=90)
    try:
        report["save"] = json.loads(raw)
    except Exception:
        report["save"] = {"raw": str(raw)[:200]}

    out = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\orrery_token_pass_20261003.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    print("\ncompile:", report["compile"])
    print("save:", report["save"])
    print("report:", out)


if __name__ == "__main__":
    main()
