# Melodia Studio — Shippable-State Checklist

**Goal:** A polished, installer-free Blender 5.2 addon that a new user can install, enable, and use without reading repo docs.
**Product name:** Melodia Studio
**Blender module id:** melodia_studio
**Operator namespace:** surreal_arch.*
**Live install path:** `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`
**Current proven state (2026-07-16 / 2026-07-26 hardening):**
- 39/39 Melodia GN builders: `gold/works`
- Blender 5.2 sync confirmed via `deploy/sync_surreal_to_live.ps1`
- Music builders, sheet rail, ornaments, `label_tree`, and `try_apply_melodia_gn` route first
- `ARCH` + registered `CASTLE_*` wired through Melodia GN
- `MEL_arch`, `MEL_portico`, `MEL_gazebo` fixed
- Solo Object + Ivy (Bagapie) + 5.2 socket rebind confirmed

## Completed hardeners

- B1 preferences rename: `melodia_studio` with one-time settings migration from `surreal_architecture_gen`
- B2 first-run N-panel stability: `branding.py` import fallback, N-panel category nesting protected, first-run traceback risk reduced
- P1 user README written: `deploy/surreal_arch/README.md`
- P4 addon CHANGELOG written: `deploy/surreal_arch/CHANGELOG.md`
- B5 `_gb_validate_assembly` AttributeError fix: `props.wall_thick` → `getattr(props, 'wall_thickness', 0.3)` and `props.wall_height` → `getattr(props, 'wall_height', 3.5)` in monolith `surreal_architecture_gen.py` lines 34729/34732. Applied 2026-07-28.

---

## Blocking — must fix before any public release

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| B1 | Addon preferences `bl_idname` rename to `melodia_studio` + compat shim for old settings | Sol | 1-2h | Done |
| B2 | First-run N-panel draw must not throw Python tracebacks on Blender 5.2 | Sol | 30m | Mitigated; needs fresh-install run |
| B3 | All intended `_edit_SM_Orn_*` objects present under `OrnamentGN_Editable` / `MusicalGN_Editable`. Current status: 7 gothic + 10 musical = 17 intended editable objects. Must verify live in Blender 5.2. | Sol | 30m | Pending Blender verification |
| B4 | FILIGREE_* monolith rewrites remain deferred. Confirm no current SKU/screenshot/portfolio dependency, then lock shippable subset explicitly. | Sol | 15m | Pending dependency check |

## High-priority polish — before store listing, not necessarily before portfolio

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| B2 | Confirm B2 in a fresh Blender 5.2 install: copy `deploy/surreal_arch/` to live addons, enable, and verify no red tracebacks on first draw | Sol | 30m | Not started |
| P2 | Verify `try_apply_melodia_gn` route-first behavior: selecting a new arch object should prefer Melodia GN over SurrealArch automatically; document if manual cleanup is still required | Sol | 30m | Not started |
| P3 | Confirm Melodia GN bake works for `NOTE_HEAD` / `SHEET_MUSIC_RAIL` under Blender 5.2 | Sol | 30m | Not started |
| L3 | Demote leftover PROPERTIES drawers that compete with Melodia Studio panels | Sol | 30m | Not started |

## Low-priority polish — after first release

| # | Item | Owner | Effort | Status |
|---|---|---|---|---|
| L1 | In-addon collection visibility operator — currently requires Outliner or external Tools scripts | Sol | 2-4h | Not started |
| L2 | Unify edit UX: selecting an editable ornament should show arch-specific props + “Open GN Stack” in the N-panel | Sol | 1-2h | Not started |
| L4 | Figma icon integration via `icon_loader.py` for Stage/Wardrobe/Photo headers | Sol | 1h | Not started |

## Verification protocol — run before tagging a release

1. Fresh Blender 5.2 install with no other addons.
2. Copy `deploy/surreal_arch/` to `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`.
3. Enable addon in Preferences → confirm no red tracebacks in the N-panel.
4. Open `Melodia_Portfolio_Stage_v4.blend`.
5. In Melodia Studio tab: verify genome carousel loads, at least one preset generates without error.
6. Route-check: `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, one ornament builder, `ARCH`, one `CASTLE_*`.
7. Confirm Review Queue Prev / Solo / Next, Solo Object, Ivy (Bagapie) all use soft visibility only.
8. Save a test screenshot or package ZIP to confirm exports work end-to-end.

## Rename scope reality

The shippable Blender module id is `melodia_studio`, backed by live install folder `surreal_arch/`. Some deploy tooling still references `surreal_architecture_gen.py` filenames/paths; these do not block a first public release, but should be cleaned up in a follow-on pass once the addon is live.

## Git release readiness

For a Git-only release, the shippable artifact is the `deploy/surreal_arch/` folder plus:
- `deploy/sync_surreal_to_live.ps1`
- `deploy/surreal_greybox/`
- `deploy/surreal_world/`
- `deploy/surreal_os/`

Tag `v2.68.0` after the verification protocol passes.

---

> **Updated 2026-08-07:** All Blender 5.1 references corrected to 5.2 per the live install path, CI config, and `.mcp.json` Blender 5.2 entry. This was tracked as contradiction C7 in `_ROADBLOCKS_2026-07-31.md`.
