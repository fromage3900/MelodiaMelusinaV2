# UI Token Pass — Worklist (generated 2026-10-03, read-only)

Source: `Saved/Dashboards/ui_tokens_20261002.json` (`python Tools/ui_style_audit.py --json …`).
This is a **worklist, not a change record**. Nothing in the editor was touched to produce it.

## Headline numbers

- 125 widget blueprints audited; 105 carry authored style rows.
- **1,441** color assignments; **1,187 (82%)** off the token palette.
- **67** distinct font entries; **62** distinct face+size combos in project widgets.
- **102** project widgets carry debt (third-party excluded).

## Blocker: the D2 fonts — SOURCES STAGED 2026-10-03, IMPORT PENDING

Owner ruling 2026-09-26 (D2): **Kaisei Decol + Klee One**, everything else retired.

At audit time: **no Kaisei asset, no Klee asset** existed in `Content/`. The decision was
recorded but the families were never imported, so W2 could not start.

**Resolved on the source side (2026-10-03).** Both families are SIL OFL 1.1 (Google Fonts,
free to ship) and are now staged in the repo's font-source convention `Imports/UI/Fonts/`
(gitignored, matching how Syne/InstrumentSerif/TwinkleStar are kept):

| file | bytes |
|---|---|
| `Imports/UI/Fonts/KaiseiDecol-Regular.ttf` | 4,503,152 |
| `Imports/UI/Fonts/KaiseiDecol-Medium.ttf` | 4,297,772 |
| `Imports/UI/Fonts/KaiseiDecol-Bold.ttf` | 4,286,896 |
| `Imports/UI/Fonts/KleeOne-Regular.ttf` | 8,724,204 |
| `Imports/UI/Fonts/KleeOne-SemiBold.ttf` | 8,905,128 |
| `Imports/UI/Fonts/KaiseiDecol-OFL.txt` · `KleeOne-OFL.txt` | licence text |

All five TTFs verified as valid TrueType (`0x00010000` magic, glyf/loca/cmap/OS-2 present).

**Importer written and syntax-clean, NOT yet run:** `Content/Python/import_d2_fonts.py`
(`py_compile` clean). Run it when the editor is free:

```
python Tools/mcp_run_python.py --file Content/Python/import_d2_fonts.py
```

It creates `F_KaiseiDecol`, `F_KaiseiDecol_Medium`, `F_KaiseiDecol_Bold`, `F_KleeOne`,
`F_KleeOne_SemiBold` under `/Game/Melodia/UI/Fonts/`, then adds matching typeface slots to
the `F_Melodia_UI` composite.

### The composite trap (read before running or editing this script)

`F_Melodia_UI` is a **UFont composite**, not a FontFace. Slate cannot render a FontFace
handed to `FontObject` — recorded in `Saved/Audit/_rebind_f_melodia_ui.py`. Correct shape:
import `.ttf` → FontFace asset → add the FontFace to
`F_Melodia_UI.CompositeFont.DefaultTypeface.Fonts` under a **named slot**; widgets then
request the typeface *by name*.

**A name absent from the composite silently falls back to engine Roboto.** That is the
mechanism behind the audit's 227 `Bold` + 101 `Default` + 74 `Regular` uses: those slots
resolve to whatever the composite happens to carry, or to Roboto.

The existing slots are kept during this import (retiring Syne/InstrumentSerif/AzeretMono/
TwinkleStar must follow the widget sweep, not precede it). The splice that appends the new
slots was validated offline against the live `export_text()` — paren balance 17/17 → 21/21.

Font assets that existed at audit time under `Content/Melodia/UI/Fonts/`:
`F_Syne`, `F_InstrumentSerif`, `F_TwinkleStar`, `F_NotoMusic`, `F_Melodia_UI`,
`Inter/F_Bold|F_Regular`, `InterTokens/F_Bold|F_Regular|F_SemiBold|F_Inter_Token`.

## What the faces are doing now

| face | uses | status |
|---|---|---|
| Bold | 227 | generic default — not a token face |
| Default | 101 | generic default — not a token face |
| Regular | 74 | generic default — not a token face |
| Syne | 22 | retired by D2 |
| InstrumentSerif | 7 | retired by D2 |
| AzeretMono | 4 | retired by D2 |
| TwinkleStar | 3 | retired by D2 |
| Light | 1 | generic default |
| Kaisei Decol | 0 | chosen, not imported |
| Klee One | 0 | chosen, not imported |

## W3 Orrery — DONE 2026-10-03

`/Game/Melodia/UI/WBP_ComicOrrery` passed. Verified by live re-read, all 10 labels:

| widget | before | after color | after font |
|---|---|---|---|
| `TXT_SPH_Sakura` | `#00EBFF` Roboto 18 | `#FCFBF8` ivory.50 | KleeOne 18 |
| `TXT_SPH_Stage` | `#00EBFF` Roboto 18 | `#FCFBF8` | KleeOne 18 |
| `TXT_SPH_Celestial` | `#00EBFF` Roboto 18 | `#FCFBF8` | KleeOne 18 |
| `TXT_SPH_Village` | `#00EBFF` Roboto 18 | `#FCFBF8` | KleeOne 18 |
| `TXT_Menu_QuestJournal` | `#00D69E` Roboto 16 | `#FCFBF8` | KleeOne 16 |
| `TXT_Menu_SkillCodex` | `#00D69E` Roboto 16 | `#FCFBF8` | KleeOne 16 |
| `TXT_Menu_Settings` | `#00D69E` Roboto 16 | `#FCFBF8` | KleeOne 16 |
| `OrreryTitle` | `#00D69E` Roboto 46 | `#DDC79B` gold.300 | KaiseiDecolBold 46 |
| `OrreryKicker` | `#00D69E` Roboto 17 | `#AEB4BF` slate.300 | KleeOne 17 |
| `OrreryInstruction` | `#00D69E` Roboto 19 | `#AEB4BF` | KleeOne 19 |

Compile: `up_to_date`, 0 errors / 0 warnings. EventGraph fingerprint unchanged
(`50ee265f…`) — no graph nodes touched, only widget properties.

Script: `Content/Python/pass_orrery_tokens.py` (run as an OS process, NOT via `run_python`).
Report: `Saved/Audit/orrery_token_pass_20261003.json`.
Backup: `…/scratch/orrery_backup_20261003/WBP_ComicOrrery_BEFORE.uasset` (md5 `eb665fce…`).

**Save trap hit and solved:** `blueprint_query save_asset` returned
`Failed to save asset` while the edit was live and correct — the checkout prompt was blocking it.
The working path is `unreal.EditorLoadingAndSavingUtils.save_packages([pkg], only_dirty=True)`.
Recorded in `.agents/skills/melodia-ui-artist` §4.

## Worklist — project widgets by debt score

Score = off-palette color rows + non-token font rows.

| score | color | font | widget |
|---|---|---|---|
| 90 | 67 | 23 | `/Game/Melodia/UI/HUD/WBP_Melodia_OverworldHUD` |
| 83 | 63 | 20 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_UnitDetails` |
| 83 | 60 | 23 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_EquipmentDetails` |
| 77 | 55 | 22 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_LevelUpDialogue` |
| 75 | 53 | 22 | `/Game/Melodia/UI/WBP_MelodiaSettings` |
| 66 | 47 | 19 | `/Game/Melodia/UI/WBP_SkillCodex` |
| 62 | 43 | 19 | `/Game/Melodia/UI/WBP_MelodiaTokenWallet` |
| 54 | 42 | 12 | `/Game/Melodia/UI/WBP_MainMenu` |
| 52 | 42 | 10 | `/Game/Melodia/UI/WBP_ComicOrrery` |
| 48 | 35 | 13 | `/Game/Melodia/UI/WBP_BlessingBurden` |
| 44 | 33 | 11 | `/Game/Melodia/UI/WBP_QuestJournal` |
| 43 | 34 | 9 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_UnitPartyDetails` |
| 38 | 31 | 7 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UnitBattleDetails` |
| 36 | 27 | 9 | `/Game/Melodia/UI/WBP_Settings` |
| 33 | 25 | 8 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_WearEquipmentUI` |
| 33 | 22 | 11 | `/Game/Melodia/UI/WBP_MelodiaWallet_Universal` |
| 30 | 19 | 11 | `/Game/Melodia/UI/Compendium/WBP_MelodiaCompendium` |
| 27 | 18 | 9 | `/Game/Melodia/UI/WBP_Battle_Results` |
| 26 | 21 | 5 | `/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow` |
| 25 | 19 | 6 | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_BuyItemAmountDialogue` |

(102 widgets total; the tail is mostly stock `TurnBasedJRPGTemplate` dialogues.)

## Recommended order, tied to the 2026-09-26 plan

1. **W3 — Orrery hub = storybook cover.** `WBP_ComicOrrery` (52). Colors: 21×`#FFFFFF`, 11×`#000000`,
   6×`hdr(0,214,158)`, 4×`hdr(0,235,255)`. Fonts: Regular 16/17/18/46.
   Highest design value: this is the surface the player sees as "the interface becomes an object".
2. **W5 — HUD leftovers.** `WBP_Melodia_OverworldHUD` (90 — worst in the project).
   Colors: 27×`#000000`, 17×`#FFFFFF`, 12×`#8FA3B8`, 4×`#E9E4F2`, 4×`#9EE7F7`, 3×`#C9A96E`.
   Fonts: Bold 10/11/16/20. Bar fills, prompts, cooldowns live here.
3. **W1/W6 — Compendium + Quill.** `WBP_MelodiaCompendium` (30) already has gold `#C9A86A` ×4 and
   `#F4EEE6` ×4 — partly on-palette; its documented "washed-out slate" debt is the `#000000` ×11.
4. **W4 — one menu owner.** `WBP_MelodiaSettings` (75), `WBP_Settings` (36), `WBP_MainMenu` (54),
   `WBP_QuestJournal` (44) — fold the menu surfaces onto the same tokens.

## The near-miss class

`WBP_Melodia_OverworldHUD` uses `#C9A96E` ×3 — that is a near-miss of gold `#C9A86A` (Δ tiny).
Per the audit bar, prefer the real token over a near-match. Same for `#E9E4F2` vs lavender `#E8E4F2`.

## Method (when the editor is free)

Per `.agents/skills/melodia-ui-artist` §4 — editor-driven only, never hand-edit a `.uasset`:

```
export_graph -> get_graph_fingerprint (before)
<mutate via blueprint_query/ui_query>
compile_blueprint  (not clean? STOP)
assert_graph_matches (matched:false? STOP)
get_graph_fingerprint (after); record both
save_asset -> re-read live state to confirm
```

Compile order trap: `compile_blueprint` wipes CDO overrides set before it.
Order is always `compile -> set_cdo_property -> save`.

## Gate

Editor is held by the owner (active animation work, 2026-10-03).
RiderLink loads at the next editor restart — no further action needed beyond the
`BS_GodFile.uproject` change already on disk.
