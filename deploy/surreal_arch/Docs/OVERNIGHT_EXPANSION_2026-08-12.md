# Melodia GN — Overnight Expansion: Presets + Infrastructure Audit (2026-08-12)

> **STALE COUNTS.** Live registry is **165** (not 119). `geometry_extras` is imported. Preset apply is wired.  
> Use [`GN_EXPANSION_PLAN_2026-08-12.md`](GN_EXPANSION_PLAN_2026-08-12.md) and [`Saved/Audit/gn_library_audit_2026-08-12.md`](../../../Saved/Audit/gn_library_audit_2026-08-12.md). Keep this file for the original preset-layer writeup only.

Lane: INFRASTRUCTURE + PRESETS + QA. Package: `melodia_gn` (subpackage of `surreal_arch`).
Files touched this session: `melodia_gn/presets.py` (new), `melodia_gn/aaa_quality.py`
(BUILDER_PRIORITY snapshot extended), this report. `core.py`, `stack.py`, `bake.py`,
`logging.py` were studied but **not modified** (no provable need — see §3).

---

## 1. What the system is

`melodia_gn` is a pure-Python geometry-nodes builder library for Blender. Every builder
module calls `register_builder(tree_name, fn, label, description, category)` at import
time, which populates `GROUP_BUILDERS` / `GROUP_METADATA` in `core.py`. `__init__.py`
imports all builder modules then calls `core._rebuild_derived_data()` to build
`TREE_TYPES`, `TREE_LABEL_MAP`, `TREE_DESCRIPTIONS`, `TREE_CATEGORY_MAP`,
`TREE_CATEGORIES`. `stack.py` renders the N-panel GN Stack from those lookups;
`bake.py` builds every registered group into `GN_Library/melodia_gn_library.blend`;
`logging.py` provides the `[Melodia GN]` logger; `aaa_quality.py` is the read-only
quality snapshot (gates, naming conventions, roadmap, priority list).

The preset system added tonight is a **pure-Python data + export layer**:

- `BUILDERS_PRESETS`: builder-id → `{label, presets: {name: {param_ui_label: value}}}`.
  Param keys are the exact group-input socket names each builder creates
  (`make_group_input`/`add_*_param`), e.g. `"Wave Count"`, `"Base Frequency"`.
- `export_builder_preset(builder_id, preset_name)` → dict with `schema_version`,
  `source`, builder metadata, preset label/description, and the param map.
- `export_all_presets_json(path)` → writes a schema-versioned JSON file
  (`exported_at`, per-builder label, per-preset param maps) with no bpy dependency.
- `preset_param_sets(builder_id)` → list of `{name, label, description?, params}`.
- `audit_presets()` → report of builders **without** presets. Reads
  `GROUP_METADATA` via a *deferred* import so the module imports cleanly without
  bpy; when the registry is unavailable it reports its own inventory and sets
  `registry_available=False`.
- `python melodia_gn/presets.py` runs the audit as a standalone script (QA use).

This satisfies the `preset_system` gate in `QUALITY_GATES` ("2-3 curated presets per
builder + JSON export") for the covered builders.

## 2. Registry counts (static analysis)

Method: `rg -c "^\s*register_builder\("` per module + an AST pass
(`ast` parse of every module) for exact literal ids, categories, and the loop-driven
set_dressing registration. Counts are call sites in source, not a runtime import.

| Module | `register_builder(` calls | Builders registered |
|---|---|---|
| primitives.py | 9 | 9 |
| profiles.py | 6 | 6 |
| math_ops.py | 6 | 6 |
| operations.py | 2 | 2 |
| effects.py | 6 | 6 |
| ornament.py | 5 | 5 |
| filigree.py | 3 | 3 |
| music.py | 6 | 6 |
| music_instruments.py | 3 | 3 |
| mesh_tools.py | 8 | 8 |
| castle.py | 13 | 13 |
| recursive_castle.py | 3 | 3 |
| polyhedra_gn.py | 3 | 3 |
| structures.py | 3 | 3 |
| nikki_quarter.py | 1 | 1 |
| escher_belvedere.py | 1 | 1 |
| escher_penrose_stairs.py | 1 | 1 |
| escher_waterfall.py | 1 | 1 |
| sky_observatory.py | 1 | 1 |
| water.py | 4 | 4 |
| ribbon.py | 4 | 4 |
| pcg_integration.py | 6 | 6 |
| set_dressing.py | 2 (loop headers) | **24** (12 water_them + 12 music_them factories) |
| geometry_extras.py | 15 | 15 (see risk §7 — NOT imported by `__init__.py`) |
| **Total** | **112 call sites** | **134 builders in source** |

**Live registry today = 119 builders.** `__init__.py` does not import
`geometry_extras`, so its 15 builders never register at runtime. All other 23
builder modules are imported by `__init__.py`.

### Category inventory (all 134 source builders, using the category string each
registration passes; 12 of 12 `CATEGORY_META` categories are used)

| Category id | Label | Builders |
|---|---|---|
| primitives | Primitives | 14 |
| profiles | Profiles | 8 |
| math_attrs | Math & Attributes | 9 |
| structures | Structures | 6 |
| effects | Magic Effects | 15 |
| ornament | Ornament | 6 |
| filigree | Filigree & Crests | 1 |
| music | Musical Notation | 11 |
| castle | Castle Kit | 19 |
| operations | Operations | 3 |
| mesh_tools | Mesh Tools | 12 |
| set_dressing | Set Dressing | 30 |
| **Total** | | **134** |

## 3. Core / AAA changes

- **core.py — none.** A "pipeline" category entry was considered and rejected:
  no builder registers under any unknown category (all 134 use the existing 12),
  and `CATEGORY_META` keys are only consumed by `_rebuild_derived_data()` for
  builders that reference them. No provable consumer exists → core.py untouched.
- **aaa_quality.py — BUILDER_PRIORITY extended** with builder ids that already
  exist in the registry (verified against the static scan): `high` +=
  `MEL_nikki_quarter`, `MEL_sky_observatory`, `MEL_recursive_castle_spire`;
  `medium` += `MEL_escher_belvedere`, `MEL_escher_penrose_stairs`,
  `MEL_castle_assembler`, `MEL_harmonic_orb`, `MEL_water_them_gazebo`,
  `MEL_music_them_gazebo`; `low` += `MEL_water_them_fountain`,
  `MEL_water_them_bridge`, `MEL_music_them_bandstand`, `MEL_pcg_water_tags_v2`,
  `MEL_music_staff`, `MEL_column`. Data-only change; no behavior touched.
- Nothing else modified. `stack.py`, `bake.py`, `logging.py` left as-is.

## 4. Preset coverage

17 builders covered with 52 curated presets (names are exact input-socket keys):

| Builder | Presets |
|---|---|
| MEL_water_gerstner | CALM_POND, RIVER_FLOW, OCEAN_SURF, WATERFALL, RIPPLE_ZONE (5) |
| MEL_gazebo | GARDEN_GAZEBO, MARKET_PAVILION, BANDSTAND_PARK |
| MEL_castle_tower | WATCHTOWER, KEEP_BASTION, MINARET_SLIM |
| MEL_ribbon_curve | GENTLE_BORDER, PENDANT_SWAG, HELIX_GUARD |
| MEL_water_them_gazebo | MOAT_RING, HARBOR_CAFE, CANAL_PARK |
| MEL_music_them_gazebo | CONCERT_PAVILION, QUIET_RECITAL, GARDEN_FETE |
| MEL_recursive_castle_spire | GOLDEN_SPIRE, SLIM_MINARET, FORTRESS_MAIN |
| MEL_nikki_quarter | TOWNHOUSE_SWEET, TEA_PAVILION, RUINED_SHRINE |
| MEL_sky_observatory | CELESTIAL_DREAM, MINIMAL_ISLE, RING_TEMPLE |
| MEL_escher_waterfall | IMPOSSIBLE_TRIBAR, QUIET_LOOP, CHAOS_CASCADE |
| MEL_music_staff | LESSON_LINE, CONCERT_SYSTEM, RAIL_CLEF |
| MEL_column | DORIC_SOBER, FLUTED_IONIC, PILASTER_SLIM |
| MEL_pcg_water_tags_v2 | RIVER_TAGS, LAKE_TAGS, WHITEWATER_TAGS |
| MEL_effect_wave | FAIRY_RIPPLE, EARTHQUAKE_SURGE, MIDNIGHT_SWELL |
| MEL_harmonic_orb | SOOTHING_ORB, DREAM_CHANDELIER, SOLO_DESK_ORB |
| MEL_brass_pipe | TRUMPET_STOP, HUNTING_HORN (2) |
| MEL_music_note_head | QUARTER_BEAT, TREMBLE_EIGHTH, HOLDING_HALF |

Coverage vs the 119-builder live registry: 14.3% of builders have presets. The
remaining 102 live builders are reported by `audit_presets()["builders_without_presets"]`
(plus the 15 dormant geometry_extras builders when wiring that import in).

## 5. Verification

- `python -m py_compile presets.py aaa_quality.py` → OK (Python 3.14).
  `core.py` untouched, so not compiled.
- Standalone logic test (no bpy on the machine; executed with system python):
  - fake `melodia_gn` package with a stub `core.GROUP_METADATA` (4 builders),
    real `presets.py` copied in:
    - `builders_with_presets()` → 17; total presets → 52.
    - `export_builder_preset("MEL_water_gerstner","OCEAN_SURF")` → correct
      metadata + `params["Wave Count"] == 8`, `Animated is True`.
    - The full 5-preset water set requested in the job brief is present.
    - `preset_param_sets` / JSON export round-trip: 17 builders / 52 presets
      written and re-read, `TEA_PAVILION["Mode"] == 1`.
    - `audit_presets()` with registry: `registered_builders=4`,
      `builders_without_presets=["MEL_does_not_exist"]`, coverage 0.75.
    - `audit_presets()` without bpy (package without core.py): falls back with
      `registry_available=False` + `registry_error`, no crash.
    - KeyError paths for unknown builder / unknown preset.
  - `python presets.py` standalone → prints the audit table.
  - All assertions passed ("ALL STANDALONE TESTS PASSED").
- Full-package import (`import surreal_arch.melodia_gn`) intentionally **not** run
  (other lanes editing concurrently; bpy not installed here).

## 6. Integration needed

In `melodia_gn/__init__.py`, add one line to the import block (anywhere after the
core import; `presets.py` has no import-time dependency on bpy or core). Exact line:

```python
from .presets import (
    BUILDERS_PRESETS, builders_with_presets, preset_names, preset_param_sets,
    export_builder_preset, export_all_presets_json, audit_presets,
)
```

No `core.py` diff is required (decision: no "pipeline" category — no consumer
exists). If other lanes add new builder modules, their `from .<module> import ...`
lines must be added to `__init__.py` before `_rebuild_derived_data()` — including
the currently-dormant `geometry_extras` (15 builders), which nothing imports today.

Optional wiring for the GN Stack / asset browser (see §7 ideas): expose
`preset_param_sets(tree_name)` next to the `mel_gn.stack_add` flow, and feed
`export_all_presets_json()` output into the parent `surreal_arch` preset catalog
(`catalog.py` / `preset_catalog.py` currently cover architecture presets, not GN
builder presets).

## 7. Risks / notes

- **`geometry_extras.py` (15 builders) is not imported by `__init__.py`** — those
  builders never register, never appear in the GN Stack, and never get baked.
  Static grep says 134 builders; the live registry is 119. Importing it is a
  one-line `__init__.py` change but is the other lanes' / next session's call.
- `audit_presets()` on a naked Python reports the library inventory, not the live
  registry (`registry_available=False`); this is deliberate to keep `presets.py`
  bpy-free.
- Param keys are the **UI socket names** (spaces, e.g. `"Wall Thick"`), matching
  `make_group_input` names verbatim; consumers must not snake_case them.
  Note `MEL_castle_tower` uses `add_float_param` for `Segments` and names its wall
  param `Wall Thick` — naming-convention drift candidates for the P0 audit.
- `MEL_nikki_quarter` presets rely on `Mode` (0 townhouse / 1 pavilion / 2 spire /
  3 ruin); the spire preset was omitted because its params share names with the
  townhouse block — mode-2 preset is a future P1 item.
- Presets are curated art-direction values; a builder whose input names change
  will silently drop keys on apply (apply is not yet wired — export only tonight).
- No `register_builder` calls, no bpy import, no writes outside
  `melodia_gn/presets.py`, `aaa_quality.py`, and this doc.

## 8. Prioritized next expansion ideas

1. **Wire `geometry_extras` into `__init__.py`** (15 builders go live; registry 119 → 134).
2. **Preset apply operator** (`mel_gn.stack_add` preset enum → set modifier
   `id_properties_ui`/interface defaults from `preset_param_sets()`).
3. **Preset coverage push to all 134 builders** — the P0 roadmap item
   ("2-3 preset JSON configs for the most-used builders"); `audit_presets()`
   gives the exact missing list.
4. **Schema v2: per-param descriptions + min/max from `make_group_input` ranges**
   and an optional "seed" transform for variation presets.
5. **Catalog bridge**: register GN presets into parent `catalog.py` /
   `preset_catalog.py` so the asset browser sees them (`_presets` bucket).
6. **Fingerprint-based regression gate** (P2 roadmap): bake all trees, hash, and
   compare against a committed baseline; `presets` export JSON doubles as a
   stable contract input for it.
