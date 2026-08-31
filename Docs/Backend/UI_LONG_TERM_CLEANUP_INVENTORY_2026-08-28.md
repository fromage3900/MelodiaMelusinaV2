# UI Long-Term Cleanup Inventory — 2026-08-28

**Status:** planning/draft, offline, no editor
**Author:** Melusina (Hermes agent, no-editor lane)
**Live with:** Junie (Rider, editor lock) — this lane stays offline until she frees it

---

## Purpose

Inventory every UI surface in BS_GodFile Melodia, what token coverage it has, what is off-palette,
and what the long-term cleanup gaps are. This is read-only — no `.uasset` writes. The apply work
stays with the editor lane (`melodia-ui-artist` skill, Monolith-driven).

---

## 1. The token SSOT (from `melodia-ui-artist` skill §1)

Single source of truth: **`melodia-design-system/tokens.json`** (committed). Two semantic themes
referencing primitives:

| family | shades (hex) |
|--------|--------------|
| ivory | 50 `#FCFBF8` · 100 `#F7F4EF` · 200 `#EFEAE1` · 300 `#E3DACE` |
| plum | 500 `#6E6080` · 600 `#463A54` · 700 `#2E2438` · 800 `#241B2E` · 900 `#1C1426` |
| gold | 100 `#F0E6D2` · 300 `#DDC79B` · 500 `#C9A86A` · 700 `#A7884E` |
| lavender | 100 `#E8E4F2` · 300 `#C2BAE0` · 500 `#9F94C6` |
| sakura | 100 `#F5E8EA` · 300 `#E7C9CE` · 500 `#D6A9B0` |
| astral | 100 `#E5EAF5` · 300 `#8AA9D6` · 500 `#3C5C9E` · 700 `#26365E` · 900 `#141A30` |
| slate | 200 `#D5D8DE` · 300 `#AEB4BF` · 400 `#828A98` · 500 `#5A6170` · 700 `#3C414B` |

Semantic roles (light / dark):
- **surface**: light `ivory.100/base, ivory.50/raised, ivory.200/sunken` · dark `astral.900/base,
  astral.700/raised, plum.900/sunken`
- **text.primary/secondary/tertiary**: light `plum.800 / slate.500 / slate.400` · dark
  `ivory.50 / slate.300 / slate.400`; **text.accent** light `gold.700` · dark `gold.300`
- **accent.primary/secondary/tertiary**: light `gold.500 / lavender.500 / sakura.300` · dark
  `gold.500 / lavender.300 / sakura.300`
- **shadows**: sm `rgba(36,27,46,0.06)`, md `rgba(36,27,46,0.10)`; **glows**: gold
  `rgba(201,168,106,0.45)`, astral `rgba(60,92,158,0.50)`

In-editor accessor: `UMelodiaDesignTokens` (`DA_MelodiaDesignTokens.uasset`,
`Source/BS_GodFile/MelodiaIntegration/MelodiaDesignTokens.h`) — `GetColor/GetGameColor/
GetKeybindColor/GetSpacing/GetRadius/GetTypography/GetEffect`.

**Token audit bar:** raw `#FFFFFF`/`#000000`/`#FFF2E5` and default-font widgets are OFF-palette.
A value within ~Δ0.05 of a token is a near-miss toward that token; prefer the real token.

---

## 2. Quill dialogue chain (tracked in git, `Content/Melodia/UI/Quill/`)

Four widgets, assigned to 5 narrative scenes via `Content/Python/assign_melodia_quill_presentation.py`:

| Widget | Path | Parent class | Assigned to |
|--------|------|--------------|-------------|
| `WBP_MelodiaQuillDialog` | `Content/Melodia/UI/Quill/WBP_MelodiaQuillDialog.uasset` | `UMelodiaQuillDialogWidget` | 5 scenes (dialog_box_class) |
| `WBP_MelodiaQuillSelection` | `Content/Melodia/UI/Quill/WBP_MelodiaQuillSelection.uasset` | `UMelodiaQuillSelectionWidget` | 5 scenes (selection_box_class) + selection CDO (choice_entry_class) |
| `WBP_MelodiaQuillBackground` | `Content/Melodia/UI/Quill/WBP_MelodiaQuillBackground.uasset` | `UMelodiaQuillBackgroundWidget` | 5 scenes (background_box_class) |
| `WBP_MelodiaQuillChoiceEntry` | `Content/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry.uasset` | `UMelodiaQuillChoiceEntryWidget` | selection CDO (choice_entry_class) |

**Known issues (from `melodia-ui-artist` skill §3 and the 2026-08-27 ledger):**
- `WBP_MelodiaQuillDialog` Event Play override shadowed native `Play_Implementation` — fixed 2026-08-27
  (`e1d1b4cd`: injected `K2Node_CallParentFunction('Parent: Play')` as first link in Event Play chain).
  Owner reports background panel still not rendering — not investigated, out of scope of that fix.
- `WBP_MelodiaQuillSelection` / `WBP_MelodiaQuillBackground` have Event Play **DISABLED** — they fall
  through to native. Only the Dialog widget had the override.
- Quill background panel never renders — no `.qsc` calls `Background()`/`Bg()` at all; separately the
  plugin calls `ShowBackgroundBox()` twice at `QuillscriptInterpreter.cpp:438-439`, where the second
  is almost certainly meant to be `ShowSelectionBox()`.
- The Quill WBPs have empty-event stubs and dead exec islands (Dialog was the worst at ~3 empty / 5 dead).
  These are unused handlers, cosmetic — only clean them via the editor.

**Token coverage (to audit via `ui_style_audit.py`):**
- Run `python Tools/ui_style_audit.py --filter Quill` (offline if editor is down; `--live` only if
  editor is up) and report the smallest token set covering the 4 Quill WBPs' actual authored
  fonts/colours/paddings.
- Flag any hardcoded (non-token) colors that deviate from a Universal palette.

---

## 3. Battle HUD surface (from `AGENTS.md` § current phase + P0 ledger)

The battle HUD is the most loaded UI surface — it carries the rhythm highway, the damage numbers,
the skill prompts, and the Quill resume indicators. The source has converged on one writer:
`UMelodiaUIBridgeSubsystem` (the old `UMelodiaJRPGBattleOverlaySubsystem` is a retired compatibility
observer that creates no widgets).

**What exists (from `AGENTS.md` + P0 ledger):**
- `BP_BattleUI` — the battle UI widget blueprint (667KB vs 457KB stock — the difference is authored
  rhythm-HUD work). There are currently two `BP_BattleUI` paths and a 33-asset mirror at
  `Content/MelodiaIntegration/Content_MelodiaIntegration/` (mirror quarantined 2026-08-11).
- `WBP_Battle_Rhythm_C` — the rhythm HUD widget, spawned by `UMelodiaUIBridgeSubsystem`.
- `BP_BattleController` — the battle controller, bidirectionally linked to `BP_BattleUI` (verified
  2026-08-27: `BP_BattleController.battleUI = BP_BattleUI_C_0`, that widget's `battleController =
  BP_BattleController_2`, MATCH=True).
- `UMelodiaRhythmHUDWidget` — driven by both the ambient `UMelodiaBattleSession`/execution-component
  sync lane and `UMelodiaRhythmCombatSubsystem::PushHighwayToHUD`.

**Known issues (from `AGENTS.md` § Evidence standard, item 5, and P0 ledger):**
- Two writers on one surface with no ownership was a real defect (ambient lane erased the other
  integration's notes one frame after they were pushed). Fixed — the ambient lane now only clears a
  highway it set (`bExecutionDrivingHighway`).
- `UMelodiaRhythmHUDWidget` rendering/feel was reported "clunky" in owner PIE 2026-08-13 — genuine
  T3D target for note presentation. Re-export baselines and resolve `unresolved_member_parent` first.
- `hud_single_writer` is `pass_pending_owner_decision` — runtime widget identity proven, but two
  vestigial vars (`melodiaBattleUI`, `MelodiaUI` — both None, vestigial pre-bridge Blueprint vars in
  category 'Melodia') await an owner retire/keep call.

**Token coverage (to audit via `ui_style_audit.py`):**
- Run `python Tools/ui_style_audit.py --filter Battle` and report the smallest token set covering the
  battle HUD widgets' actual authored fonts/colours/paddings.
- Flag any hardcoded (non-token) colors — especially `JudgmentText`/`ComboText`, which the 2026-08-24
  session noted still need widget-graph binding functions calling `MelodiaBattleSession` BlueprintPure
  getters (currency via `UMelodiaTokenWalletSubsystem`).

---

## 4. Other UI surfaces (to inventory)

| Surface | Asset path (proposed) | Status |
|---------|----------------------|--------|
| Main menu / HUD | `Content/Melodia/UI/` (TBD) | To inventory |
| Inventory / wardrobe | `Content/Melodia/UI/` (TBD) | To inventory |
| Quest log | `Content/Melodia/UI/` (TBD) | To inventory |
| Rhythm highway | `WBP_Battle_Rhythm_C` (see §3) | Inventoried |
| Quill dialogue | `Content/Melodia/UI/Quill/` (see §2) | Inventoried |

**To do (editor-bound, Junie's lane via `melodia-ui-artist` skill):**
- Run `python Tools/ui_style_audit.py` (full, or `--filter <substr>`) and produce the token coverage
  report for every WBP under `Content/Melodia/UI/`.
- Run `python Tools/bp_sweep.py --filter <name>` for each UI widget — flag shadowed events, empty-bodied
  events, dead exec islands, unreachable assets, duplicate short names.
- Run `python Tools/bp_live_path.py` for each UI widget — flag `ORPHAN` (prove it, don't delete it).

---

## 5. Long-term cleanup gaps (summary)

1. **Token coverage audit** — run `ui_style_audit.py` for Quill + Battle + every other UI WBP, produce
   the token coverage report, flag off-palette values.
2. **Battle HUD binding completion** — `JudgmentText`/`ComboText` need widget-graph binding functions
   calling `MelodiaBattleSession` BlueprintPure getters (currency via `UMelodiaTokenWalletSubsystem`).
   This is part of making `hud_single_writer` pass honestly.
3. **Vestigial var retirement** — owner decision to retire `melodiaBattleUI` / `MelodiaUI` (cleanup,
   not a gate blocker, but it finishes `hud_single_writer`).
4. **Quill background panel** — owner reports it still not rendering; not investigated. Separate from
   the `ShowBackgroundBox` double-call bug.
5. **Dead exec islands / empty events** — cosmetic, clean via the editor only. Don't hand-edit `.uasset`.
6. **Duplicate `BP_BattleUI` paths** — mirror quarantined 2026-08-11; confirm no remaining short-name
   collisions before delete of quarantine tree.
7. **Material baseline drift** — two material baselines drifted against a 2026-08-07 freeze
   (`M_Master_Simple_Universal` 25→26 nodes, `M_Master_Toon_Landscape_HeightBlend` 290→304 nodes).
   Owner call: re-freeze if intended, revert if not. Blocks `static_gates`.

---

## 6. What this lane does (no editor)

- Keep running `python Tools/ui_style_audit.py` (offline form, if it can run without the editor) and
  record the token coverage — but note HOLD if it dies connection-refused.
- Keep the inventory doc current — update it when new UI assets are committed.
- Hand off the apply work to Junie via the `melodia-ui-artist` skill + this inventory.

---

## 7. File map

| File | Purpose |
|------|---------|
| `Docs/Backend/UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md` | **this file** |
| `.claude/skills/melodia-ui-artist/SKILL.md` | UI audit/style/apply runbook (SSOT for token + workflow) |
| `Content/Python/assign_melodia_quill_presentation.py` | Quill WBP assignment script (SSOT for which class goes where) |
| `Tools/ui_style_audit.py` | Token coverage inventory flow |
| `Tools/bp_sweep.py` | Defect-class audit (shadowed events, empty events, dead exec islands, unreachable, dup names) |
| `Tools/bp_live_path.py` | Reachability audit (LIVE/ORPHAN/AMBIGUOUS) |
