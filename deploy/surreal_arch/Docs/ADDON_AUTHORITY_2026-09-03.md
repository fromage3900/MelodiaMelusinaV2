# Melodia Studio addon — repo authority map (2026-09-03)

**Write this doc before touching the addon or any stage script.** It records the copy
layout that caused the 2026-09-03 convergence incident: builders that existed in one
copy but not another, three diverging `__init__.py` files, and a roof feature
duplicated in two systems.

## The four copies

| Copy | Path | Role |
|---|---|---|
| P: repo | `P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/` (+ `../surreal_architecture_gen.py`) | **SSOT for committed addon source** (remote `MelodiaMelusinaV2.git`). Docs + committed addon live here. |
| C: repo | `C:/Users/brenn/melodiamelusinav2/deploy/surreal_arch/` (+ `../surreal_architecture_gen.py`) | Working copy committed to `melodiamelusinav2.git` (blends/Tools repo). May be on main. |
| Live install | `%APPDATA%/Blender Foundation/Blender/5.2/scripts/addons/surreal_arch/` | What Blender actually loads. |
| melodia_studio | `%APPDATA%/.../addons/melodia_studio/` | Separate panel/MIDI-bridge addon ("Melodia Studio" Blender Integration Panel). NOT a GN copy — do not confuse with surreal_arch. |

The monolith `surreal_architecture_gen.py` was byte-identical across all copies at
this writing; divergence happens in `melodia_gn/`. **Rule: P: is the SSOT.** Edit P:,
then sync C: and AppData immediately (same session), then md5-verify all three.

## Sync procedure (run after EVERY addon edit)

```bash
APPD="C:/Users/brenn/AppData/Roaming/Blender Foundation/Blender/5.2/scripts/addons/surreal_arch/melodia_gn"
# edit P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/<file>.py first
cp P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/<file>.py \
   C:/Users/brenn/melodiamelusinav2/deploy/surreal_arch/melodia_gn/
cp P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/<file>.py "$APPD/"
# verify
md5sum P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn/<file>.py \
       C:/Users/brenn/melodiamelusinav2/deploy/surreal_arch/melodia_gn/<file>.py \
       "$APPD/<file>.py" | awk '{print $1}' | uniq -c   # must print "3 <hash>"
```

Sync the whole `melodia_gn/` dir if `__init__.py` changed. Commit targets: P: repo
commits go to `MelodiaMelusinaV2.git`; C: repo commits go to `melodiamelusinav2.git` —
confirm with the owner which before committing.

## Authority inside the addon — do not build in parallel

| Concern | Owner | Do NOT |
|---|---|---|
| Roofs (all types: hip/gabled/pagoda/mansard/onion/…) | `surreal_architecture_gen.py` `_build_curved_roof` + `SurrealRoof_*` props (`surreal_arch_props`), driven headlessly by setting props on a mesh object then calling `_build_curved_roof(obj, props)` + `_add_roof_modifier_stack(obj, props)` | Write a GN or bmesh roof builder; extend `MEL_city_house_cell`'s inline cone (legacy, gated behind `Show Roof`) |
| House cells / city | `MEL_city_house_cell` (`melodia_gn/melodia_city_gen.py`) — shell + interior plan + foundation | Rebuild shells inline in stage scripts |
| Room shells (genome) | `MEL_mh6_room_shell` (`melusina_house_v6.py`) | — |
| Organ pipe ranks (ET) | `MEL_music_organ_pipes` (`melodia_kit_baroque.py`) — standalone; nested by the facade | Rebuild pipe math inline in another builder |
| Organ facade | `MEL_music_baroque_organ` — case + rosette + nested rank | — |
| GN builders generally | `melodia_gn/core.py` `register_builder` | Bypass the registry |

Pattern for convergence: demote inline code to a parameterized gate (e.g. `Show Roof`)
and stage the authority's objects separately in the script — see
`C:/Users/brenn/melodiamelusinav2/Tools/house_v6_lego_v3.py` (cells staged `Show
Roof=False`, roofs as `SurrealRoof_HIP_*` objects) and `Tools/organ_split_test.py`.

## Before writing ANY new geometry code — discovery checklist

1. `grep -rni "<feature>" deploy/surreal_arch/melodia_gn/ deploy/surreal_architecture_gen.py`
   — both trees, all four copies of the concern (facade/pipes lesson: the organ had
   facade and rank welded in one builder; split, don't re-weld).
2. Check `GROUP_BUILDERS` registry (runtime): `[k for k in GROUP_BUILDERS if '<kw>' in k]`.
3. Check the monolith's prop systems (`surreal_arch_props` categories, Architecture
   Picker arch_types) — features often exist as bmesh generators, not GN.
4. If found: extend/nest it (reuse pattern: nested group node driven by parent params).
5. If truly absent: build it in P:, follow `melodia-studio-gn-builders` skill, sync
   all three copies, verify headless (realize instances before counting verts).

## Incident log (what this doc prevents)

- 2026-09-03: three divergent copies of `melodia_gn/` (city_gen only in C:, house kits
  missing from C:, three different `__init__.py`); `MEL_city_house_cell` had an inline
  cone roof duplicating the addon's `_build_curved_roof` authority; organ facade had
  ET pipe rank welded inline (now split into `MEL_music_organ_pipes`). All converged;
  sync rule + checklist above are the fix.
