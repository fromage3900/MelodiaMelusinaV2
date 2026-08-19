# Melodia GN expansion plan — 2026-08-17

**Supersedes for next work:** [GN_EXPANSION_PLAN_2026-08-12.md](GN_EXPANSION_PLAN_2026-08-12.md) (keep as history).  
**Freeze baseline:** 165 / 12. **Live after greybox pass:** 169 / 12. **Live after musical heroes:** **173 / 12** (music +3 SKUs, Structures +1). Set Dressing stays 39.

Owner choice from the 08-12 “stop volume” thesis: **fix stubs first, then greybox/interior; no new `water_them_*` / `music_them_*` clones.**

## What landed (2026-08-17 musical heroes)

Headless factory-startup 5.2: `deploy/_gn_music_heroes_smoke.py` → `Saved/Audit/gn_music_heroes_2026-08-17_1437.json` (7/7). `bl_info` stays `(2, 131, 0)`. AppData sync skipped: hung `blender.exe` (lookdev v23, not responding).

| Tree | Job | Category |
|------|-----|----------|
| `MEL_music_key_unit` | Life-size key: box + front lip, accidental switch, pitch | Musical Notation |
| `MEL_music_piano_roll` | Instance keys on spline; period = key width; PIANO/XYLO/MARIMBA/GLOCK | Musical Notation |
| `MEL_music_sheet_rail` | Rewrite in place: walkable posts + five swept staff lines + notes | Musical Notation |
| `MEL_music_harp` | Pillar, neck curve, strings instance-on-spline, soundboard | Musical Notation |
| `MEL_music_room_shell` | Greybox hollow room + openings + optional dado staff band | Structures |

Named presets: CONCERT_HALL_RAIL, ENDLESS_88, WALKABLE_XYLO_PATH, PEDAL_HARP_C. No `them_*` clones. No Set Dressing volume.

## What landed (2026-08-17)

Headless factory-startup 5.2: `deploy/_stub_rewrite_smoke.py` → `Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json` (14/14). `bl_info` stays `(2, 131, 0)`.

### Wave A — stubs

- Hidden (ids kept): 24 `MEL_water_them_*` / `MEL_music_them_*` factory clones + `MEL_pcg_water_tags`, `MEL_pcg_music_tags`, `MEL_material_crosswalk` (27 hidden). `*_v2` stay visible.
- `Current Speed` / `Density` stored on PCG v2 (`current_speed`, `density`).
- `MEL_greybox_room_kit` — hollow Mesh Boolean DIFFERENCE shell (16 eval verts vs 8-vert solid cube).
- `MEL_polyhedra_dodecahedron` — Dual Mesh of icosahedron (20 verts / 12 faces), not an icosphere.
- `MEL_add_geometry` / `MEL_subtract_geometry` — Mesh Boolean UNION / DIFFERENCE, Mesh 1 minus Mesh 2.
- Mesh Bevel: 5.2 `GeometryNodeMeshBevel` (Offset / Shape). Missing node raises; no silent passthrough. Selection=False no longer wired.
- `MEL_env_reeds_patch` — height jitter + clump (768 eval verts).

### Wave B — greybox spine (Structures)

| Tree | Job | Smoke |
|------|-----|------:|
| `MEL_greybox_room_kit` | Hollow room, wall thick, ceiling switch | 16v / 12f |
| `MEL_greybox_openings` | Door + window boxes cut from Geometry | 24v (hole vs uncut cube) |
| `MEL_greybox_corridor` | Tileable hall, optional end cap | 16v |
| `MEL_greybox_junction` | T or X union of hollow halls | 52v |
| `MEL_greybox_composer` | Join room + corridor + junction | 8v (eval clean, kept) |

Presets SMALL_CELL / HALL / CLOISTER_WALK on room, openings, corridor, junction. `STUDIO_LABELS` for all five greybox ids. Do **not** port `GB_ZEN_*` / `GB_GOTHIC_*`.

### Wave C — addon QOL

- GN Stack **Show hidden / factory clones** (WindowManager, default off).
- Selecting a MEL_* NODES modifier focuses the stack row; **Open GN editor**.
- Stage **Isolate Editable GN** — soft `LayerCollection.hide_viewport` on OrnamentGN_Editable / MusicalGN_Editable / Review_Queue.
- `SURREAL_ARCH_OT_spawn_polyhedron` double-register guarded (`_register_class_once`). Factory-startup overhaul now loads (no “Overhaul package not loaded”).
- User-facing `register_builder` tooltip mojibake (`ΓÇö`) fixed. Comments left alone.

AppData sync skipped this pass: `blender.exe` was running. Run `deploy/sync_surreal_to_live.ps1` after GUIs quit, then one 5.2 restart.

## Counts

| | Freeze | Now |
|--|--:|--:|
| GN builders | 165 | **173** |
| Hidden | 0 (then 27 flagged) | **27** (still in registry) |
| Visible in GN Stack (toggle off) | 165 | **146** |
| Structures | 7 | **12** |
| Set Dressing | 39 | **39** (frozen) |
| Preset builders / looks | 33 / 100 | **42 / 127** |
| Categories | 12 | **12** |

## Still out of scope / leftover

- `FILIGREE_*` monolith rewrites deferred.
- B3 v22 ornament collection eyeball (needs `MELODIA_ALLOW_STAGE_SAVE=1` if writing the stage).
- AppData sync + fresh-install GUI draw while `blender.exe` holds the live addon.
- L4 Figma icons (`icon_loader.py` still a no-op).
- Unreal PCG / LiveLink 9876 conflict — documented, not redesigned.
- Greybox snap / composer placement — later.
- Do not invent a `v2.68.0` tag.
