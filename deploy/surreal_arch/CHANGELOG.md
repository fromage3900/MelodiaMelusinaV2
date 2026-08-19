# Changelog

## v2.131.0 — 2026-08-17 (musical heroes)

- Registry **173 / 12** (prior 169; music +3 SKUs, Structures +1). `bl_info` still `(2, 131, 0)`.
- New: `MEL_music_key_unit`, `MEL_music_piano_roll` (PIANO/XYLO/MARIMBA/GLOCK), `MEL_music_harp`, `MEL_music_room_shell`.
- Rewrite in place: `MEL_music_sheet_rail` is a walkable staff railing (posts + five swept lines + pitch-height notes). Same tree id.
- Presets include CONCERT_HALL_RAIL, ENDLESS_88, WALKABLE_XYLO_PATH, PEDAL_HARP_C. Library **42 / 127**.
- No `them_*` clones, no Set Dressing volume, no v22 save, no Blender GUI spawn.
- Headless smoke: `deploy/_gn_music_heroes_smoke.py` → `Saved/Audit/gn_music_heroes_2026-08-17_1437.json` (7/7). AppData sync skipped (`blender.exe` PID 92616 hung on lookdev, not responding).

Known / deferred:

- `FILIGREE_*` monolith rewrites stay deferred. Thin-kit GN filigree trees are the SKU.
- B3 editable ornament collections still need a live v22 eyeball (v4.blend absent).
- Do not tag a public store ZIP until B3 + a fresh-install GUI draw pass.
- Do not invent a `v2.68.0` git tag. Live `bl_info` is `(2, 131, 0)`.

## v2.131.0 — 2026-08-17 (stubs, greybox, QOL)

- Registry **169 / 12** (freeze baseline 165; Structures +4). `bl_info` still `(2, 131, 0)`.
- Hidden (ids kept): 24 `them_*` factory clones + 3 PCG v1 aliases. GN Stack **Show hidden / factory clones** defaults off.
- Rewrites: hollow `MEL_greybox_room_kit`, real dodeca dual, Mesh Boolean add/subtract, 5.2 Mesh Bevel (no silent passthrough), PCG v2 Current Speed / Density, reeds jitter/clump.
- New Structures trees: `MEL_greybox_openings`, `MEL_greybox_corridor`, `MEL_greybox_junction`, `MEL_greybox_composer` with SMALL_CELL / HALL / CLOISTER_WALK presets.
- L2 Open GN editor on MEL_* modifiers; L1 Isolate Editable GN (soft viewport); spawn_polyhedron double-register guarded.
- Headless smoke: `deploy/_stub_rewrite_smoke.py` → `Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json` (14/14).

Known / deferred:

- `FILIGREE_*` monolith rewrites stay deferred. Thin-kit GN filigree trees are the SKU.
- B3 editable ornament collections still need a live v22 eyeball (v4.blend absent).
- AppData sync skipped while `blender.exe` is running.
- Do not tag a public store ZIP until B3 + a fresh-install GUI draw pass.
- Do not invent a `v2.68.0` git tag. Live `bl_info` is `(2, 131, 0)`.

## v2.131.0 — 2026-08-17 (Studio final review)

- N-panel hub prints live GN builder / stack-category counts.
- Modifier-tab "Surreal Architecture" drawer is legacy: hidden unless
  Preferences → Melodia Studio → **Show legacy Modifier panel**.
- Addon preferences register on both `surreal_architecture_gen` (enabled module)
  and `melodia_studio` (product alias).
- Live Bridge MCP copy: Agent MCP is N → BlenderMCP → Connect on **9876**.
  Legacy **9317 / 9877** labeled do-not-use. LiveLink Start Server still 9876
  (do not run both).
- Product branding subtitle encoding fixed (`Architecture · Ornament · Genome`).
- Monolith `bl_info` description already 165 builders / 12 categories; module
  docstring now Blender 5.2 / Melodia Team.
- P3 headless bake: `NOTE_HEAD` → `MEL_music_note_head` (122 eval verts) and
  `SHEET_MUSIC_RAIL` → `MEL_music_sheet_rail` (323 eval verts) on factory-startup 5.2.

Known / deferred:

- `FILIGREE_*` monolith rewrites stay deferred. Thin-kit GN filigree trees are the SKU.
- B3 editable ornament collections still need a live v22 eyeball (v4.blend absent).
- Do not tag a public store ZIP until B3 + a fresh-install GUI draw pass.
- Do not invent a `v2.68.0` git tag. Live `bl_info` is `(2, 131, 0)`.

## v2.68.0 — 2026-07-26

- Renamed Blender preferences module id to `melodia_studio`; added one-time settings migration for existing users.
- Updated product branding import fallback for fresh installs.
- Confirmed 39/39 Melodia GN builders.
- Known issue: `FILIGREE_*` monolith builder rewrites are deferred post-v1. Existing filigree meshes in kitbash exports are unaffected.
