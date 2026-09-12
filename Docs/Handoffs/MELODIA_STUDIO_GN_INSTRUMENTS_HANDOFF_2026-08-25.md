# Melodia Studio + Surreal GN — Session Handoff (2026-08-25)

All work verified in Blender 5.2 headless (`--factory-startup`, 6/6 PASS) and
53/53 offline unit tests OK. The Surreal monolith `deploy/surreal_architecture_gen.py`
(38,564 lines, v2.131.0) was **never edited** — all builders use the
`melodia_gn` registry pattern.

## 1. What shipped

### A. Tandem Bridge — terrain <-> city (v1.4)
- `Tools/BlenderAddons/melodia_studio/tandem_bridge.py`
  - Pairing table melodia preset -> surreal COMPOSE_STYLE/plan/dressing (34 pairs).
  - `snap_plan_to_field()` / `pad_and_level()`: surreal plans sit on the musical
    heightfield via `surface_height_at()` (floor-fix); gates/corners get 1-cell pads.
  - Operators: `melodia_studio.tandem_compose` (COLLECTION mode), `.tandem_export`.
  - Subpanel under the Studio panel; worlds tagged `melodia_tandem_*`.

### B. Dressing instancing + budget fix (v1.4)
- Linked-instance dressing (`MS_Dressing` collection, `MS_TPL_*` templates,
  `MS_Dress_*` instances) reusing the resonant_world_studio pattern.
- `terrain_dressing.plan_dressing()` now strictly respects `budget`.
- `cleanup_scene` clears dressing + tandem worlds; added missing
  `setup_script_directory` operator.

### C. Gold-ivory / pink / rose-gold chrome (v1.5)
- `melodia_chrome/*.png` generated from `wix/melodia-tokens.css` by
  `tools/generate_chrome_icons.py` (gold_rule, header_void strip,
  6 preset cards, 4 pillar dots, starlight_gold -> melodia_icons/starlight.png).
- `melodia_studio/melodia_chrome.py`: `chrome_header/kicker/status/preset_grid`
  with pillar accents (cathedral=cosmic blue, grotto=gold, zen=sakura,
  plaza=lavender). Panels: studio=cathedral, gaea=grotto, tandem=zen.
- `addon_utils._load_icons()` ingests `melodia_chrome/`; graceful fallback when PNGs absent.
- Autosync: `tools/figma_sync.py --chrome` regenerates chrome locally without
  FIGMA_TOKEN and re-runs the GN triage; post-kit/motion hook auto-refreshes chrome.

### D. Ancient Cultures instrument presets (12)
- `ancient_cultures.py`: Ur lyre, Hurrian hymn, Egypt harp, Greek aulos,
  guqin, sho gagaku, Andes siku, Mande kora, Welsh crwth, Nordic lur,
  Vedic saman, Roman hydraulis. Meter -> chunk_beats; drone/percussion ->
  beatgrid layer; aura = ritual intensity.
- 5 new dressing kinds (sun_disc, oracle_stone, papyrus_reed,
  processional_mark, lotus_bloom) + 12 styles merged into terrain_dressing;
  `full_bloom` recomputed to include everything.
- 12 tandem pairings merged into tandem_bridge (total 34).

### E. Surreal GN instruments + reactive geometry (this session's close-out)
New files in `deploy/surreal_arch/`:
- `morph_baker.py` — bakes GN param variants as shape keys on a duplicated
  object (live GN untouched), FBX export adapts to Blender <=4.x vs 5.x API,
  sidecar schema v2 adds `morph_targets[]` with `reaction_channel`
  (`beat|bass|grade|pluck:<id>`). Verified end-to-end:
  SM_Mus_Harp_Concert_Real.fbx (26 KB) + .snap.json with MOR_pluck_01..03.
- `melodia_gn/chimes_gn.py` (5 builders) — ET tuning ported from chime_row:
  f=root*2^((semi-9)/12), L=Lmax*sqrt(f_ref/f). tube / field_scatter /
  mark_tree / carillon_tier / aeolian_wall (wind-phase strings).
- `melodia_gn/music_harps_real.py` (4) — concert harp anatomy (arc neck,
  pillar, soundboard, graduated strings, semitone_mod12 for C/F color coding),
  Ur lyre, kora, siku. Pluck params are morph-ready.
- `melodia_gn/music_terrain.py` (2) — `MEL_roll_walkable`,
  `MEL_staff_bridge` consuming roll-field data.
- `melodia_gn/__init__.py` imports the three modules (registry auto-rebuilds).

### F. Roll field single source of truth
- `Tools/BlenderAddons/melodia_studio/roll_field.py` — MIDI ->
  `melodia_roll_field_v1` JSON (222 cells, walk=1.0, per-cell pitch/
  velocity/is_accidental). Same cells for Blender GN and UE PCG.
  Verified output at Saved/Audit/roll_field_128BPMarpeggiomelody.json path
  convention (temp verify used %TEMP%).

### G. Docs / audit
- `Docs/GN_TAXONOMY_20260825.md` + `Saved/Audit/gn_triage_20260825.json`
  (165 builders / 12 cats / 19 families / 42 genomes / 33-of-165 presets),
  organization recommendations, autosync wiring diagram.

## 2. Verification evidence (Blender 5.2 headless)
```
PASS: registry: 12 new builders registered
PASS: build 11 trees w/ Geometry I/O
PASS: evaluate chime field scatter (verts > 100)
PASS: evaluate concert harp (verts > 200)
PASS: morph bake: 3 pluck shape keys + schema v2 sidecar
PASS: roll field exporter (222-cell walkable)
==== 6/6 passed ====
python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
-> Ran 53 tests, OK (expected failures=1)
```
Bugs found & fixed during verification: installed-addon vs repo split
(files mirrored to AppData), Blender 5.2 NODES `node_group` rename +
interface-identifier params, dependency-rebuild orphaned Group refs
(`_refresh_group_refs` self-heal), FBX exporter flag changes, mesh-lifecycle
bug in baker cleanup.

## 3. Known cosmetic warnings (non-blocking)
- Harp soundboard tilt uses rotation default instead of linked float.
- One Store Named Attribute Value default not linked (float literal).

## 4. Live install note
Blender loads `surreal_arch` from
`%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`.
The four new/changed files were mirrored there manually. If you reinstall or
re-link the addon from the repo, re-copy: morph_baker.py,
melodia_gn/{chimes_gn,music_harps_real,music_terrain,__init__}.py.

## 5. Next up (not started)
- UE side of WS-D: VAT materials on waveform walls/staff rails, HISM reaction
  via MPC_Melodia_Palette channels, snap-sidecar importer.
- Batch bake `regenerate_musical_instruments_v3.py` (SM_Mus_* naming).
- Chrome preset cards for the 12 ancient presets (dropdown works today).
