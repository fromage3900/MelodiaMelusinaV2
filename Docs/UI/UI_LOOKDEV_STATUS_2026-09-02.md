# UI Lookdev + Integration Status — 2026-09-02

Tight, honest status for P0 UI surfaces, lookdev, and Figma token alignment. Real numbers only — no claim without evidence.

## 1. Token SSOT (committed, complete)

`melodia-design-system/tokens.json` — HoYoverse celestial × luxury editorial, 217 lines.

| family | shades |
|---|---|
| ivory | 50 `#FCFBF8` · 100 `#F7F4EF` · 200 `#EFEAE1` · 300 `#E3DACE` |
| plum | 500 `#6E6080` · 700 `#2E2438` · 800 `#241B2E` · 900 `#1C1426` |
| gold | 100 `#F0E6D2` · 300 `#DDC79B` · 500 `#C9A86A` · 700 `#A7884E` |
| lavender/sakura/astral/iris/slate/status | all defined |

Semantic roles: surface/text/border/accent/feedback for both **light** (Ivory editorial) and **dark** (Astral Night) themes. Global: space 4-128, radius none/pill, fonts Fraunces/Cinzel/Inter/IBM Plex Mono, typography display-xl → metadata, shadows sm/md, glows gold/astral.

In-editor accessor: `UMelodiaDesignTokens` (`DA_MelodiaDesignTokens.uasset`, `MelodiaDesignTokens.h`).

**Status: token file is complete. Token-to-WBP audit is NOT yet run.**

## 2. Quill Dialogue WBPs (tracked, partially fixed)

Four widgets at `Content/Melodia/UI/Quill/`, assigned to 5 scenes:

| Widget | Status |
|---|---|
| `WBP_MelodiaQuillDialog` | Event Play override **fixed** 2026-08-27 (e1d1b4cd) — injected Parent: Play |
| `WBP_MelodiaQuillSelection` | Event Play **DISABLED** — falls through to native |
| `WBP_MelodiaQuillBackground` | Event Play **DISABLED** — falls through to native |
| `WBP_MelodiaQuillChoiceEntry` | selection CDO choice_entry_class |

**Wired:** dialog_box_class, selection_box_class, background_box_class → 5 narrative scenes via `Content/Python/assign_melodia_quill_presentation.py`.

**Unpolished / misaligned:**
- Background panel still not rendering — no `.qsc` calls `Background()`/`Bg()` at all; separately the plugin calls `ShowBackgroundBox()` twice at `QuillscriptInterpreter.cpp:438-439` (second almost certainly meant to be `ShowSelectionBox()`)
- Empty-event stubs and dead exec islands (Dialog worst at ~3 empty / 5 dead) — cosmetic, editor-only cleanup
- Selection/Background fall through to native — intentional? unclear

## 3. Battle HUD (converged, two defects remain)

Single writer converged: `UMelodiaUIBridgeSubsystem` (old `UMelodiaJRPGBattleOverlaySubsystem` retired).

**Wired + verified:**
- `BP_BattleUI` (667KB — 210KB authored rhythm-HUD work over stock)
- `WBP_Battle_Rhythm_C` spawned by UIBridgeSubsystem
- `BP_BattleController` ↔ `BP_BattleUI` bidirectional link MATCH=True (owner-verified 2026-08-27)
- Runtime widget identity proven; real-key input verified 2026-08-13

**Unpolished / misaligned:**
- `LiveResultsWidgetPath` empty — logs "cannot load live-results widget class from ''" twice per session (source backfill landed in MelodiaUIBridgeSubsystem.cpp:131-133 but path still unset at runtime)
- `JudgmentText`/`ComboText` need widget-graph binding functions calling `MelodiaBattleSession` BlueprintPure getters (currency via `UMelodiaTokenWalletSubsystem`)
- Rhythm highway rendering/feel "clunky" (owner PIE 2026-08-13) — T3D target for note presentation
- Two `BP_BattleUI` paths + 33-asset mirror at `Content_MelodiaIntegration/` (quarantined 2026-08-11; confirm no short-name collisions before delete)

## 4. Vestigial vars (owner decision awaited)

`melodiaBattleUI` / `MelodiaUI` — both None, pre-bridge Blueprint vars in category 'Melodia'. `hud_single_writer` is **pass pending owner decision** to retire/keep. Cleanup, not a gate blocker.

## 5. Figma token alignment

- tokens.json committed and complete ✓
- **Token-to-WBP audit NOT run** — `Tools/ui_style_audit.py` has not been executed against Quill or Battle widgets
- Token coverage report does not exist yet
- raw `#FFFFFF`/`#000000`/`#FFF2E5` and default-font widgets would be flagged as OFF-palette if audit were run (per inventory §1 audit bar)
- `melodia-ui-artist` skill is the SSOT for the apply workflow

## 6. Orphan / partial MIs on disk

- 38 `MI_Orphan_*` at `Content/EnvSandbox/Materials/Instances/Environment/PBR_Auto/` — partial from crashed bulk-creation; **texture binding unverified**
- 144 orphaned PBR stems total per pbr_full_scan_2026-08-30.json
- Safe small-batch creator authored: `Content/Python/bulk_create_orphan_mis_safe.py` (one MI at a time, resumable, verified-binding) — **not yet run**

## 7. Recommended next 3 UI/lookdev actions

1. **Run token audit**: `python Tools/ui_style_audit.py --filter Quill` and `--filter Battle` — produce the actual token coverage report for the 4 Quill WBPs + battle HUD, flag off-palette values. This is the single most honest "what's the UI state" deliverable.
2. **Fix LiveResultsWidgetPath**: verify the backfilled source at MelodiaUIBridgeSubsystem.cpp:131-133 is actually hitting the load path at runtime; wire `JudgmentText`/`ComboText` to `MelodiaBattleSession` getters.
3. **Resolve the background panel**: confirm whether Selection/Background Event Play DISABLED is intentional; fix `ShowBackgroundBox` double-call at QuillscriptInterpreter.cpp:438-439.

All three are editor-bound. No further offline UI inventory will change the grade — the gap is apply, not documentation.