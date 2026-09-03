# Melodia Studio — Pie / Room-Shell / Window Review & Orchestration Roadmap

> **Incident addendum (2026-08-23, later session):** between sessions a `git checkout -- .`-class
> revert wiped **all tracked-file modifications** in this repo (AGENTS.md documents this as the
> 2026-08-08 catastrophic pattern). Recovered in full from the `Melodia_ClaireonTest/deploy`
> mirror (which post-dated the edits): monolith room/window enums, `shells.py`, `pie_menu.py`,
> `integration.py`, `ui.py`, `bootstrap.py`. Untracked new files (`music_ui.py`, `music_aaa.py`,
> reconstructed glue) were immune. Three untracked glue files that only ever lived in the old
> live install were destroyed by an earlier `/MIR` and were **reconstructed from surviving
> `.pyc` bytecode**: `surreal_greybox/__init__.py`, `surreal_os/_io.py` (variadic
> `load_data(*parts)`, None-on-missing), `melusina_portrait/__init__.py` (MPR_* operators +
> Living Portrait panel). Also repaired corruption-era casualties `expression_mixer.py`
> (missing `dataclass` import). **Lesson:** run `_sync_addon_to_blender_5_2.py` (now SSOT-pinned
> to `BS_GodFile/deploy`) after every edit batch; never `/MIR` without first diffing both trees.
> Note: the same revert also consumed another lane's uncommitted `MelodiaCore/*.cpp` changes —
> not recoverable here; owner should check those files.

**Final headless verification (Blender 5.2.0 LTS, `--factory-startup`): 32/32 PASS**
- Overhaul loads; 5 pies registered; keymaps=5 (Shift+Q/Alt+Q/Ctrl+Shift+Q/Shift+Alt+Q/**Shift+M score**)
- `melodia_score` prop + Score panel + `apply_bpm_genome` / `generate_scale_room` ops live
- greybox `attach_all` OK; SurrealOS genomes=33
- 8 AAA builders eval: waveform 128v · vinyl 52267v · harp 240v · **piano 192v (=14W+10B keys)** · ribcage 2142v · fork 226v · metronome 162v · rosette 2016v
- Rooms: RECT/L/T/U/CIRCULAR/OCTAGON/APSIDAL/SUPERELLIPSE/ELLIPSE × GOTHIC windows all generate (>50v each)
- IMM export: 8 base-pivoted OBJs (5.7 MB) + `_IMM_README.txt`

Blender-5.2 API traps hit & fixed (documented for future builders): no `MeshTorus`/`Solidify`;
MeshLine = Count/Start/**Offset** (OFFSET mode); `FunctionNodeBooleanMath`; circle fill `'NONE'`;
Math node has 3 Value sockets factory-defaulting to **0.5** (never b_val-then-link same slot);
`Realize Instances` gained `Realize All` (set True); CurveToMesh `Fill Caps=True` for IMM-closed tubes;
always link result → Group Output (`new_geometry_tree` leaves passthrough otherwise).

---

**Date:** 2026-08-23  
**Scope:** Changes shipped in working tree `BS_GodFile/deploy` (not yet committed), how to make it faster, friendlier, and feel orchestrated.  
**Live install:** `C:/Users/froma/AppData/Roaming/Blender Foundation/Blender/5.2/scripts/addons` (synced via `_sync_addon_to_blender_5_2.py`).

---

## 1. What changed (verified)

| File | Change | Verification |
|---|---|---|
| `deploy/surreal_architecture_gen.py:2293` | `gb_room_shape` 4→11 (`CIRCULAR/APSIDAL/OCTAGON/HEX/ELLIPSE/SUPERELLIPSE/FREEFORM`) + 7 new props (`gb_room_sides`, `gb_room_radius`, `gb_room_ellipse_ratio`, `gb_room_super_n`, `gb_window_shape` 8-way, `gb_window_arch_height`, `gb_window_has_mullion/transom`, `gb_window_glazing`) | headless `p.gb_room_shape="CIRCULAR"` / `p.gb_window_shape="GOTHIC"` → `True`; 7 `GREYBOX_ROOM` variants `PASS` (eval 463–2606 verts) |
| `deploy/surreal_greybox/shells.py` | New `_window_cutter_geometry` (shape-aware GN cutter: box / cylinder-through-wall / box+half-cylinder arch / pointed GOTHIC/OGEE), `_window_frame_extra_parts` (mullion/transom/glazing tagged `SURREAL_TRIM:window_glass=5.0`), rewrite of `collect_window_cutters_for_rect` + `rect_room_shell` frame append, new `_ngon_wall_ring` (CurveCircle→Fill→Extrude floor, segmented wall ring with tangent `Transform`, angular window distribution, apse stem), `build_greybox_room` dispatch | `L_SHAPE/T_SHAPE/U_SHAPE` + `CIRCULAR/ELLIPSE/SUPERELLIPSE/APSIDAL` + corridor still `PASS`; cylinder depth `t*4` |
| `deploy/surreal_arch/pie_menu.py` | 1 pie → 4 pies: `pie_main` (Shift+Q), `pie_room` (Alt+Q), `pie_window` (Ctrl+Shift+Q), `pie_genome` (Shift+Alt+Q) + operators `set_room_shape/set_window_shape/nudge_genome` + keymaps + `VIEW3D_MT_object_context_menu` | `SURREAL_ARCH_MT_pie_*` all `ok`, `keymaps count=4`, `unregister→re-register` ok |
| `deploy/surreal_arch/integration.py:15,678,844` | Import + `register_pie_menu_with_keymaps` / `unregister_pie_menu_with_keymaps` | headless register ok; second `register_overhaul` fails on prefs `ValueError: already registered` (pre-existing `bootstrap.py:79` only catches `RuntimeError`) — not hit on normal start |
| `deploy/surreal_arch/ui.py:204` | `draw_level_design` adds **Room Shell — shape & math** + **Window Cutouts — detailed** boxes (counts, arch, frame, mullion/transom/glazing, placement) | visual in `N→Melodia Studio→Level Design`; pi-hint labels |
| `Melodia_ClaireonTest/deploy/*` | Copied from `BS_GodFile/deploy` then synced to live `5.2/scripts/addons` (1912202 bytes) | sync log 60+13+9+8 files |

Git status (`BS_GodFile`): `M deploy/surreal_arch/{integration,pie_menu,ui}.py`, `M deploy/surreal_architecture_gen.py`, `M deploy/surreal_greybox/shells.py` (+ unrelated `Plugins/MelodiaCore` token wallet moves, `Docs/*`). No commit yet.

---

## 2. Critical review

### Good

- **No regression** on legacy `RECTANGLE` + `gb_windows_enabled` old path (both legacy `gb_window_n/e/w` + new `gb_window_count_ns/ew` work).
- **Pies are discoverable**: 4 Q-family hotkeys (Shift+Q safe vs `MACHIN3tools` Q), context menu, `N` panel hints.
- **Window glazing tag** (`trim_value=5.0`) reuses existing `SURREAL_TRIM` vertex-color pipeline (`trim_color_bake.py`, `build_trim_groups`) — exports to UE snap JSON without new channel.
- **Headless verification** is now easy (`--background --factory-startup --python`); prior corridor/room coverage was manual.

### Issues / risks

1. **Node count explosion** — `CIRCULAR` with `n=32` creates ~64 wall nodes + per-window `JoinGeometry`/`Transform`/`Cylinder` (12 windows → +36). `ARCH_ROUND` cutter does `box + cylinder + Join` per window. Room with 4 walls × 6 windows = 24 `Join`s; depsgraph eval still < 3k verts but node graph is hard to read and bevel/trim downstream walks every node (`_wire_trim_box_wrapper`).  
   Root: `rect_room_shell` joins then bool-diffs per-wall; `_ngon_wall_ring` duplicates wall segment + cutter + transform per segment.
2. **Pies over-allocated** — `pie_genome` packs 6 axes × 2 buttons (12) + 2 picks into an 8-slot pie; Blender clips to 8, so 6 slots overflow into a column that is cramped. `pie_room` buries `SUPERELLIPSE/FREEFORM` off-pie; `pie_window` already at 8, no room for count nudges.
3. **Keymap is hardcoded Q-family** — 4 bindings on `Q` with `Shift/Alt/Ctrl` are fat-finger prone; no `AddonPreferences` to remap; `bootstrap.py:79` migrates Higgsas only, not hotkeys. Second `register_overhaul` (hot-reload) crashes on prefs before pie dedup can run.
4. **`_ngon_wall_ring` transform hack** — `_gb_box` is axis-aligned; we bolt a `Transform(Rotation=(0,0,tang))` after. The box was already placed at `(x,y)` world then rotated around origin, so wall center drifts. Needs `Transform` with `Translation` undo/redo or use `InstanceOnPoints` on a curve.
5. **Apse stem reuses `rect_room_shell` with `with_windows=False`** — loses window reveals on the rectangular stem; no doorway continuity at the seam.
6. **`ui.py` mega-panel** — `draw_level_design` is now ~520 lines; `Room Shell` box shows even when `arch_type` is `TREFOIL_KNOT` etc. (shows for any greybox, poll is too loose). No search/filter for 11 shapes × 8 window shapes.
7. **Sync drift** — `BS_GodFile/deploy` is source of truth but `Melodia_ClaireonTest/deploy` is a manual copy; no CI check that they stay identical (`git diff` shows only BS_GodFile dirty, ClaireonTest is opaque `%APPDATA`).

---

## 3. How to make it more orchestrated (not just more knobs)

Think **preset = Room footprint × Window language × Genome × Kit → one click**, not 4 pies + 14 sliders.

### 3.1 Orchestration primitives (next)

- **Room Preset (orchestrated object):** `OrchestratedRoom { room_shape, room_radius/sides/ellipse/super_n, window_shape+arch/mullion/transom/glazing+counts, genome_id, corridor_profile/ceiling/rib/wainscot, trim_mode }` → one `surreal_arch.orchestrated_room_apply` operator that sets all props then `generate`. Store as JSON in `surreal_os/orchestrated_presets/*.json` (like `orchestrated_presets/gothic_apse_rosette.json`). Pies and `N` panel become **pickers over presets**, not raw prop editors.
- **Guided flow in N panel:** collapse `Room Shell` + `Window` + `Genome` + `Corridor kit` into a single **Orchestrated Room** stepper with `← Back / Next →` and live preview count (`eval_verts`, `trim_groups`). Raw props stay in an `Advanced` disclosure.
- **One Graph, not N wall segments:** replace `_ngon_wall_ring` segment loop with a single `CurvePrimitiveCircle → ResampleCurve → InstanceOnPoints (wall segment)` → `RealizeInstances` → single `MeshBoolean` with grouped cutters. Cuts node count from `O(n)` to `O(1)` plus one `StoreNamedAttribute` for per-wall window tag. Same for `ARCH_ROUND` cutter: pre-build one arch cutter template then `InstanceOnPoints` at window positions.

### 3.2 Builder performance (do first)

1. **Batch cutters** — collect all window cutters for a wall into one `JoinGeometry` then one `_gb_bool_diff` (today: per-wall diff already batches, but ngon ring does per-segment diff). Change ngon ring to one diff after wall join.
2. **Cache arch cutter** — build one `ARCH_ROUND` cutter mesh (box+cylinder+join) once at `(0,0,0)` then `Transform(Translation=(cx,cy,cz), Rotation=…)` per instance via `InstanceOnPoints` — avoids `n` cylinder nodes.
3. **Don’t create `Transform` per wall if not needed** — `OCTAGON/HEX` walls are axis-snappable (multiples of 30°/45°); skip rotation for those exact angles.
4. **Measure** — add `surreal_arch.studio_health` metric: `node_count`, `bool_count`, `eval_ms` (via `time.monotonic()` around `generate`); log to `Saved/Logs/MonolithCalls.jsonl` already, add `orchestrated_preset_id`.
5. **Lazy genome** — `SURREAL_ARCH_MT_pie_genome` currently enumerates all `genome_*.py` on every draw; cache `genome_groups` in `integration:486` and invalidate only on `sync_reload`.

### 3.3 Friendliness (do second)

- **Pie redesign:** `Main` stays 8 (Generate, Room ▶, Window ▶, Genome ▶, Trim/Bake, Snap, Export, Graph). `Room` → 8 *common* shapes, move `SUPERELLIPSE/FREEFORM` to long-press or `N` panel only. `Window` → 6 shapes + `Mullion` toggle + `Glazing` toggle (8 total, drop `LINTEL/SEGMENTAL` to long-press). `Genome` → 4 axes (Vertical/Symmetry/Ornament/Cosmic) + 4 favorite genomes; expose all 6 axes in `N` panel sliders (today hidden).
- **Preferences for hotkeys:** add `pie_hotkey_main/room/window/genome: StringProperty` to `MelodiaStudioAddonPreferences` (`bootstrap.py:50`), build keymaps from prefs, show in `Preferences → Melodia Studio` with `KeyMap` UI; duplicate Q-family becomes user-fixable.
- **Search + favorites:** extend `ui.draw_arch_picker_filtered` search index to include `gb_room_shape` + `gb_window_shape` presets; add `★ Favorite` toggle per orchestrated preset (store in `bpy.types.Scene.melodia_fav_presets`).
- **Live preview:** after `set_room_shape`/`set_window_shape` with `do_generate=False`, show ghost wire preview via `gpu` overlay or `depsgraph` eval vert count label (already `eval_verts` in tests) before user hits Generate.
- **Fix `bootstrap.py:79`:** catch `ValueError` as well as `RuntimeError` so `sync_reload` (which calls `register_overhaul` again) doesn’t abort before pies re-register.

---

## 4. Documentation of current usage

**New workflow:**
1. Select mesh → `N → Melodia Studio → Level Design` or **Shift+Q** (main) / **Alt+Q** (room) / **Ctrl+Shift+Q** (window) / **Shift+Alt+Q** (genome).
2. Room Shell box: pick `CIRCULAR/APSIDAL/OCTAGON/HEX/ELLIPSE/SUPERELLIPSE`; adjust `Radius / Sides / Ellipse Ratio / Super N` as it appears. Pie `Alt+Q` does same without opening `N`.
3. Window Cutouts box: enable, pick `RECT/ARCH_ROUND/GOTHIC/OGEE/CIRCLE/ROSETTE/LINTEL/SEGMENTAL`, set `Arch Height, W/H/Sill, Frame Thick, Mullion/Transom/Glazing`, then `N/S, E/W` counts. Pie `Ctrl+Shift+Q` cycles shape.
4. `Generate` (pie or `N` panel). Glass planes from `glazing` carry `SURREAL_TRIM=5.0` → `Bake Trim Attributes` → `Export UE5` / `Export Snap JSON`.

**Not yet orchestrated:** user still sets 5–7 props by hand per room; next step is one-click orchestrated presets.

---

## 5. Recommended order

1. **Perf** — batch cutters + instance cutter templates (one session, no UX).  
2. **Prefs hotkeys + bootstrap `ValueError` fix** (30 min).  
3. **Orchestrated preset JSON + one `Apply` operator + pie as preset picker** (design doc first: schema in `surreal_os/orchestrated_presets/schema.json`).  
4. **Single-curve ring wall** (replace segment loop) — requires GN `InstanceOnPoints` spike, behind feature flag `gb_orchestrated_ring_v2`.

No new `Content/` assets touched; all `BS_GodFile/deploy` changes are `--factory-startup` safe (headless verify passed).
