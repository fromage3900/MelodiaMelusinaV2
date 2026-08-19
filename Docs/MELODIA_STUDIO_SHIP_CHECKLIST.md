# Melodia Studio — Shippable-State Checklist

**Goal:** A polished, installer-free Blender 5.2 addon that a new user can install, enable, and use without reading repo docs.
**Product name:** Melodia Studio
**Blender module id:** melodia_studio
**Operator namespace:** surreal_arch.*
**Live install path:** `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`
**Current proven state (2026-08-17 / deploy GN registry):**
- **173** Melodia GN builders, **12** GN Stack categories (Set Dressing 39 / freeze volume; Structures 12)
- Hidden 27 factory/PCG aliases (ids kept). Visible GN Stack 142 unless Show hidden is on.
- Freeze baseline remains 165/12; greybox pass +4 Structures; musical heroes +4 (key/piano/harp/room; sheet_rail rewrite in place)
- Blender 5.2 AppData sync runs only when `blender.exe` is not running
- Music builders, sheet rail, ornaments, `label_tree`, and `try_apply_melodia_gn` route first
- `ARCH` + registered `CASTLE_*` wired through Melodia GN
- `MEL_arch`, `MEL_portico`, `MEL_gazebo` fixed; greybox room/corridor/openings/junction eval headless
- Solo Object + Ivy (Bagapie) + 5.2 socket rebind confirmed
- P0 smoke: 7/7 hero presets applied (LIQUID live 2026-08-12; remaining 6 headless 2026-08-13)
- P2 fingerprint baseline: 12 heavy trees (`Saved/Audit/gn_fingerprint_baseline_2026-08-13.json`)
- B2 dry-run JSON exists (`Saved/Audit/site_publish_dry_2026-08-13_1258.json`); live Cam_Beauty plate still blocked (user-blender MCP down)
- Preset library: **42** builders / **127** looks (was 37 / 112; +5 music-hero builders × 3 looks)
- Stub rewrite smoke: `Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json` (14/14)
- Musical hero smoke: `Saved/Audit/gn_music_heroes_2026-08-17_1437.json` (7/7)

## Completed hardeners

- B0 GN Stack sections 12/12, 165 trees (`Saved/Audit/melodia_studio_sections_2026-08-12_1948.md`)
- B1 Review Queue parity RQ_MEL_* = 165 (`Saved/Audit/melodia_studio_parity_2026-08-12_1948.md`)
- B1 preferences rename: `melodia_studio` with one-time settings migration from `surreal_architecture_gen`
- B2 first-run N-panel stability: `branding.py` import fallback, N-panel category nesting protected, first-run traceback risk reduced
- B2 website plate **dry-run** (git push OFF) written 2026-08-13; live render still open
- P0 hero presets smoked headless 2026-08-13 (`Saved/Audit/gn_p0_smoke_2026-08-13_1258.md`)
- P2 fingerprint baseline 12/12 (`Saved/Audit/gn_fingerprint_baseline_2026-08-13.json`)
- P1 user README written: `deploy/surreal_arch/README.md`
- P4 addon CHANGELOG written: `deploy/surreal_arch/CHANGELOG.md`
- B5 `_gb_validate_assembly` AttributeError fix: `props.wall_thick` → `getattr(props, 'wall_thickness', 0.3)` and `props.wall_height` → `getattr(props, 'wall_height', 3.5)` in monolith `surreal_architecture_gen.py` lines 34729/34732. Applied 2026-07-28.

---

## Blocking — must fix before any public release

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| B1 | Addon preferences `bl_idname` rename to `melodia_studio` + compat shim for old settings | Sol | 1-2h | **Done** — prefs now register on both `surreal_architecture_gen` (enabled module) and `melodia_studio` (alias) |
| B2 | First-run N-panel draw must not throw Python tracebacks on Blender 5.2 | Sol | 30m | **Mitigated** in code; fresh-install GUI run still open (see Fresh install) |
| B2-live | Live Cam_Beauty website plate render | Sol | 30m | **Done 2026-08-13** — Nikki Cam_Beauty on live v22; live site https://fromage3900.github.io/my-site/ (plate reads bald: Flip cache below scalp) |
| B3 | All intended `_edit_SM_Orn_*` objects present under `OrnamentGN_Editable` / `MusicalGN_Editable` (7 gothic + 10 musical = 17) | Sol | 30m | **Blocked on live stage** — v4.blend absent; contract + headless empty-scene inventory: `Saved/Audit/gn_b3_editable_2026-08-13.json` |
| B4 | FILIGREE_* monolith rewrites remain deferred. Confirm no current SKU/screenshot/portfolio dependency, then lock shippable subset explicitly. | Sol | 15m | **Locked deferred** — spawn/SKU still uses monolith `FILIGREE_PANEL` (gothic ring + musical corners). Melodia GN filigree trees (spiral + 3 extras) are the thin kit; do not rewrite monolith for v1. |

## High-priority polish — before store listing, not necessarily before portfolio

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| B2-fresh | Confirm B2 in a fresh Blender 5.2 install: copy `deploy/surreal_arch/` to live addons, enable, and verify no red tracebacks on first draw | Sol | 30m | **Skipped this session** — live GUI holds AppData; `install_melodia_studio.ps1` now aborts if `blender.exe` is running |
| P0 | Hero preset smoke-apply | Sol | 30m | **Done** — 7/7 (see gn_p0_smoke_2026-08-13_1258.md) |
| P1 | Thin-kit presets (ornament vine/radial/frame, remaining filigree 3, operations 3) | Sol | 1h | **Done** — 33 builders with presets (was 24) |
| P2 | Fingerprint bake for 12 trees with 51+ nodes | Sol | 30m | **Done** — gn_fingerprint_baseline_2026-08-13.json |
| P2-aaa | `aaq_quality_checklist` reads measured construct/preset/label/node/fingerprint | Sol | 30m | **Done** — mesh/export gates stay OPEN |
| P3 | Confirm Melodia GN bake works for `NOTE_HEAD` / `SHEET_MUSIC_RAIL` under Blender 5.2 | Sol | 30m | **Done 2026-08-17** — `deploy/_p3_bake_note_rail.py` factory-startup |
| L3 | Demote leftover PROPERTIES drawers that compete with Melodia Studio panels | Sol | 30m | **Done 2026-08-17** — Modifier drawer hidden unless Preferences → Show legacy Modifier panel |

## Low-priority polish — after first release

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| L1 | In-addon collection visibility operator — currently requires Outliner or external Tools scripts | Sol | 2-4h | **Done 2026-08-17** — `surreal_arch.isolate_editable_gn` soft-isolates OrnamentGN_Editable / MusicalGN_Editable / Review_Queue |
| L2 | Unify edit UX: selecting an editable ornament should show arch-specific props + “Open GN Stack” in the N-panel | Sol | 1-2h | **Partial 2026-08-17** — stack focuses MEL_* NODES modifiers + **Open GN editor**; full ornament-prop unification skipped |
| L4 | Figma icon integration via `icon_loader.py` for Stage/Wardrobe/Photo headers | Sol | 1h | Not started |

## Fresh install / verify (2026-08-13)

Live Blender 5.2 GUI (PID **27644**) is using the AppData addon. **Do not run** `install_melodia_studio.ps1` while that process is up — the script now errors out if `blender.exe` is running.

Headless verify is safe (`--factory-startup` does not copy into AppData):

```powershell
cd deploy
# SKIP while GUI is live:
# .\install_melodia_studio.ps1
.\verify_melodia_studio.ps1 -SkipSmoke   # health only; uses deploy/ sources
python .\test_stage_publish_contract.py  # git push default is False
```

Full `verify_melodia_studio.ps1` (smoke queue) is also factory-startup and does not clobber AppData; it was not re-run this pass because the 165-builder review blender already reconstructs every tree.

## Verification protocol — run before tagging a release

1. Fresh Blender 5.2 install with no other addons.
2. Copy `deploy/surreal_arch/` to `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`.
3. Enable addon in Preferences → confirm no red tracebacks in the N-panel.
4. Open live stage `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` (v4 is historical / currently absent from KitbashExport).
5. In Melodia Studio tab: verify genome carousel loads, at least one preset generates without error. Studio Health: `sections=12/12 section_trees=173`.
6. Route-check: `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, one ornament builder, `ARCH`, one `CASTLE_*`. Click **Circular Array**.
7. Confirm Review Queue Prev / Solo / Next, Solo Object, Ivy (Bagapie) all use soft visibility only.
8. Save a test screenshot or package ZIP to confirm exports work end-to-end.
9. Do **not** tag until live Cam_Beauty plate (B2-live) and B3 editable collections are verified on a stage file.

## Rename scope reality

The shippable Blender module id is `melodia_studio`, backed by live install folder `surreal_arch/`. Some deploy tooling still references `surreal_architecture_gen.py` filenames/paths; these do not block a first public release, but should be cleaned up in a follow-on pass once the addon is live.

## Git release readiness

For a Git-only release, the shippable artifact is the `deploy/surreal_arch/` folder plus:
- `deploy/sync_surreal_to_live.ps1`
- `deploy/surreal_greybox/`
- `deploy/surreal_world/`
- `deploy/surreal_os/`

**Do not invent a `v2.68.0` tag.** Tag only after the verification protocol passes, including live plate + B3 stage collections.

---

> **Updated 2026-08-17 (musical heroes):** Registry **173/12**. New key_unit / piano_roll / harp / room_shell; sheet_rail rewritten in place. Presets 42/127. Smoke `gn_music_heroes_2026-08-17_1437.json` (7/7). AppData sync skipped (hung `blender.exe`). `bl_info` still `(2, 131, 0)`.
>
> **Updated 2026-08-17 (stubs/greybox/QOL):** Registry **169/12**. Hide 27 factory/PCG aliases. Greybox openings/corridor/junction/composer in Structures. Smoke `gn_stub_rewrite_2026-08-17_1335.json`. AppData sync skipped (`blender.exe` running). `bl_info` still `(2, 131, 0)`.
>
> **Updated 2026-08-17:** L3 Modifier drawer demoted. P3 note-head / sheet-rail bake script added. Live Bridge copy corrected (Agent MCP = N-panel Connect :9876). Cam_Beauty plate shipped 2026-08-13. B3 still needs a v22 eyeball. Do not sync AppData while a 5.2 GUI is open.
>
> **Updated 2026-08-13:** Counts 165/12. P0 smoked, P2 baseline on disk, B2 dry-run on disk, live plate still open. P1 thin-kit presets landed (33 builders). Install skipped while GUI PID 27644 holds AppData.
>
> **Updated 2026-08-07:** All Blender 5.1 references corrected to 5.2 per the live install path, CI config, and `.mcp.json` Blender 5.2 entry. This was tracked as contradiction C7 in `_ROADBLOCKS_2026-07-31.md`.
