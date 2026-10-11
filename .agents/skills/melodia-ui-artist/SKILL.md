---
name: melodia-ui-artist
description: Audit, style, and fix Melodia UI widgets in BS_GodFile UE5.8 using the real design-token system — Semantic light/dark palettes, Quill dialogue WBP chain, ui_style_audit inventory, and the editor-driven (Monolith) apply workflow. Use when styling a widget, replacing stock UI, fixing dialogue/selection/background/choice widgets, checking colors against the token set, or running a UI polish pass.
---

# Melodia UI artist

Operational runbook for UI work on the Melodia JRPG surface. Every path and value below was
verified in-session against the repo — this is the SSOT, not a guess. Do the job asked, ship it,
stop; fix ≠ review.

## 0. Scope guard

- **Do not hand-edit `.uasset`/`.umap`.** All widget changes go through the editor (Monolith on
  `http://127.0.0.1:9316/mcp`, `blueprint_query` / `editor_query` / `ui_query`). Hand-editing a
  `.uasset` breaks the registry.
- **One editor, one MCP surface.** `Get-Process UnrealEditor` single instance; one listener on
  9316. Never two graph-mutation MCP servers on the same graph.
- **Never touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python** — fatal enum
  glue crash (`D_DamageType`). Use `blueprint_query` (C++) for skill reads, never `run_python`.
- **Gitignore is intentional.** `Content/Melodia/*` blocks most of `UI/`; only
  `Content/Melodia/UI/Quill/` is allowlisted (tracked). Do not "fix" the gitignore to track ~200
  Figma textures under `Content/Melodia/UI/Textures/` — they are intentionally ignored.

## 1. The token SSOT — read this before choosing any color

Single source of truth: **`melodia-design-system/tokens.json`** (committed). Two semantic themes
referencing primitives:

| family | shades (hex) |
|---|---|
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

**Token audit bar (from the 2026-08-26 audit):** raw `#FFFFFF`/`#000000`/`#FFF2E5` and default-font
widgets are OFF-palette. A value within ~Δ0.05 of a token is a near-miss toward that token; prefer
the real token over a near-match. Fonts should use the token type scale, not the default face.

### The font composite trap — read before touching any font

`F_Melodia_UI`, `Font_KaiseiDecol`, and `Font_KleeOne` are **UFont composites**, not FontFace assets.
Slate **cannot render a FontFace** handed to `FontObject` (recorded in `Saved/Audit/_rebind_f_melodia_ui.py`).
The working shape:
import `.ttf` → FontFace asset → add it to the composite's `DefaultTypeface.Fonts` under **named slots**
→ widgets request the typeface *by name* (`TypefaceFontName`).

**The Invisible Font Invariants:**
1. **Weight Aliases Are Mandatory**: Widgets throughout `WBP_Melodia_OverworldHUD` and `WBP_Melodia_CosmicOrrery` request `"Bold"` on `Font_KleeOne`. Because Klee One only has Regular and SemiBold source files, the composite MUST explicitly alias `Bold` -> `F_KleeOne_SemiBold` alongside `Regular`, `Medium`, and `SemiBold`. A missing slot name causes Slate to draw zero glyphs.
2. **FallbackTypeface Is Mandatory**: Every UFont composite MUST define `FallbackTypeface=(Typeface=(Fonts=((Name="Regular",Font=(FontFaceAsset="/Script/Engine.FontFace'/Engine/EngineFonts/Faces/DroidSansFallback.DroidSansFallback'")),(Name="Roboto",Font=(FontFaceAsset="/Script/Engine.FontFace'/Engine/EngineFonts/Faces/RobotoRegular.RobotoRegular'")))),ScalingFactor=1.000000)`. Without this, unicode glyphs (`·`, `◆`, `✓`, `◇`, `…`) and Japanese characters drop out entirely.
3. **Always Check Alpha**: Verify `ColorAndOpacity.SpecifiedColor.A > 0.0`. `AreaName` defaulted to `(0, 0, 0, 0)` in HUD templates, causing complete invisibility even with valid fonts.
4. **Maintenance Script**: Run `Content/Python/repair_d2_font_stubs.py` inside Unreal Editor via `editor_query.run_python` to repair all composites in one pass.

When splicing `export_text()` to add composite slots, **check paren balance offline first** — the
Fonts array nests two levels deep and an off-by-one paren produces a broken composite that still
imports without error. Validate against the live `export_text()` before writing.

## 2. Inventory before you style

`python Tools/ui_style_audit.py` walks every WBP and clusters the visual properties actually
authored. `--filter <substr>` scopes it, `--json Saved/Dashboards/ui_tokens.json` for an agent
action list. Read-only — it proposes tokens, it does not apply them.

For reachability / defects: `python Tools/bp_sweep.py --filter <name>` (shadowed events, empty
events, dead exec islands, unreachable assets, dup short names) and
`python Tools/graph_reachability.py --bp <asset>`.

## 3. The Quill dialogue chain (what the player actually sees)

The four widgets live at `Content/Melodia/UI/Quill/` and are **tracked in git**:

- `WBP_MelodiaQuillDialog` — the main dialog box
- `WBP_MelodiaQuillSelection` — choice prompt (its CDO owns `choice_entry_class`)
- `WBP_MelodiaQuillBackground` — backdrop layer
- `WBP_MelodiaQuillChoiceEntry` — a single choice row

They are assigned to 5 narrative scenes under `/Game/MelodiaIntegration/Narrative/`
(`MelodiaMorningIntro`, `MelodiaQuillPetalPriestess`, `MelodiaQuillSmoke`,
`MelodiaQuillStarWeaver`, `MelodiaQuillTwilightDancer`) via
`Content/Python/assign_melodia_quill_presentation.py`. Rendered layers: dialog/selection 5,
background 15.

**Layer/visibility bug class:** `QuillscriptInterpreter.cpp`
`ShowSelectionBox`/`ShowBackgroundBox` must guard with
`!IsInViewport() && !GetParent()` (matching `ShowDialogBox` at L1198) BEFORE `AddToViewport`.
An inverted guard silently keeps selection/background out of the viewport — widgets compile and
save clean but never appear. Verify the guard on all three, not just the dialog.

**Audit note:** the Quill WBPs have empty-event stubs and dead exec islands (Dialog was the worst
at ~3 empty / 5 dead). These are unused handlers, cosmetic — only clean them via the editor.

## 4. Apply workflow (editor-driven, mandatory)

Follow the melodia-p0-loop verification loop for any graph mutation, no exceptions:

```
export_graph            -> save it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate via blueprint_query/ui_query>
compile_blueprint       -> not clean? STOP.
assert_graph_matches    -> matched:false? STOP.
get_graph_fingerprint   -> after; record both
save_asset              -> then re-read live state to confirm (mtime <10min + re-read)
```

Compile order trap: `compile_blueprint` WIPES CDO overrides set before it. Order is always
`compile -> set_cdo_property -> save`. Never compile between set and save.

**mtime is not proof.** Re-read live state (`get_cdo_properties`, `get_level_actors`) after save.
`.uasset` often goes read-only after checkout — `attrib -R <path>` before saving.

### Two traps that make a correct edit look like a failure

**1. `save_asset` can fail while the edit is live and correct.** `blueprint_query save_asset`
returned `ERROR:Failed to save asset: /Game/…` and `ui_query` reported no success, yet
`list_dirty_packages` showed the asset dirty and a re-read showed every new value in place. The
save was being blocked by the source-control checkout prompt, not by the edit. The working path
is a direct package save:

```python
pkg = unreal.load_package("/Game/Melodia/UI/WBP_ComicOrrery")
unreal.EditorLoadingAndSavingUtils.save_packages([pkg], only_dirty=True)   # -> True
```

Confirm by mtime change AND md5 change on disk, then re-read. Do not re-run the whole pass
because the save reported failure — re-read first, you may have nothing to redo.

**2. A Monolith-driving script must NOT be launched with `run_python`.** `run_python` exec()s the
file *inside* the editor; a script that then calls `mcp_client.monolith(...)` is HTTP-ing back into
the same server from the same thread. Every step fails with
`WinError 10061 connection refused` — **while the wrapper still prints `MCP_RUN_PYTHON_STATUS=OK`**,
so it looks like it ran. Run Monolith-driving scripts as a plain OS process:

```
python Content/Python/pass_orrery_tokens.py        # correct
python Tools/mcp_run_python.py --file <same>       # self-call, silently fails
```

Reserve `run_python` for code that only touches `unreal.*` and never calls back into Monolith.

### `set_font` resolves composites, not FontFaces

`ui_query set_font` takes a **UFont composite** path plus a **named typeface slot**:

```
font_family = "/Game/Melodia/UI/Fonts/F_Melodia_UI"   # UFont composite
typeface    = "KaiseiDecol"                            # slot name
```

Passing a FontFace path (`F_KaiseiDecol`) fails `Font asset not found` — FontFace ≠ UFont. A slot
name that is absent from the composite silently falls back to Roboto, which is how a widget reads
a plausible font in the graph yet renders default.

## 5. Evidence / proof

A style change is "done" when: (a) it uses real tokens from `tokens.json`, (b) `compile_blueprint`
is clean AND `assert_graph_matches` matches, (c) the widget re-read shows the new values, and
(d) if it's the dialogue chain, the viewport guards are correct. A live PIE `HighResShot` plus
before/after state reads is the only valid runtime evidence — `capture_scene_preview`/
`capture_anim_frames` produce stale frames and are not proof.
