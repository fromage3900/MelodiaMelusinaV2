# ROOM-SHELL CONVERGENCE PLAN — one healthy shell ecosystem

Written 2026-09-04, after the mh6 defect fix (P: commit 3f1d4460) and a fresh
census of every room-shell-capable system in the addon. Supersedes V7 §V0's
"prove identity, then rewire" step with a fuller scope: the census found FOUR
shell surfaces, not two.

## Census (verified in source, file:line)

| # | Builder | File | Role today | Verdict |
|---|---------|------|-----------|---------|
| 1 | `MEL_mh6_room_shell` | `melodia_gn/melodia_house.py:59` | Genome shell: box → bevel → SDF → boolean openings → fillet → bend. Now WORKS (v0_final_verify PASS). | **PROMOTE: THE exterior shell authority** |
| 2 | `MEL_greybox_room_kit` | `melodia_gn/polyhedra_gn.py:215` | Hollow box (outer cube minus inner void). Builds the EXTERIOR shell of every city house cell (`melodia_city_gen.py:379`) and the §16 interior rooms (`melusina_house.py:169,187`) and `MEL_music_room_shell` (`music_heroes.py:799`). | **DEMOTE: interiors/corridors only** |
| 3 | `MEL_music_room_shell` | `melodia_gn/music_heroes.py:779` | Greybox shell + openings + dado staff band. A third shell that wraps #2. | **FOLD: keep id, re-nest onto mh6** |
| 4 | Monolith `surreal_architecture_gen.py` (v2.131, 38,596 lines) | `apply_geometry_nodes_to_object:18206` dispatches a 209-id `arch_type` enum to ~274 builder functions that author GN nodes into a per-object `SurrealArch_<obj>` tree. Its room shell `_gb_rect_room_shell:4500` (slab walls + cutter boolean) serves GREYBOX_ROOM, GB_ROOM_COMPOSITE, GB_COMBAT_ROOM, GREYBOX_TOWER, GB_ELEVATOR_SHAFT, MODULAR_HOUSE. Roofs: FOUR surfaces (build_roof_tiles GN, _curved_roof GN:11967, _conical_roof_swept bmesh:14518, _build_curved_roof bmesh:36575). Extension seam exists: `kit_registration.py::register_kit` + `catalog_dispatch.py` inject builders into `_KIT_DISPATCH`/`_CATALOG_DISPATCH` without touching the file; `melodia_gn_route.py` routes monolith ids to MEL_ builders. | **CONVERGE VIA SEAMS, NOT EDITS** (see Monolith section) |

## Why mh6 is the authority

- Parametric openings (grid-driven cutter field with real SDF boolean),
  filleted opening edges, curve bend, cornice ring, bbox-driven genome.
  Greybox has none of these — it is a hollow box.
- 27k–55k verts at architectural params: real-time-viable.
- Same MEL schema (register_builder, standard params, presets entry).

## Convergence steps (each with a gate, in order)

### C1 — Param adapter + identity proof (the old V0 gate)
1. New helper `melodia_house.py::mh6_shell_adapter(tree, node, mapping)` —
   thin, maps greybox param names (Room Length/Width/Height, Wall
   Thickness) onto mh6 params (Width/Height/Depth→Wall Thickness). No new
   tree; a wiring helper only.
2. Headless proof script `Tools/house_c1_identity_proof.py`:
   - stock cell `MEL_city_house_cell` (greybox shell) at defaults
   - twin cell tree nesting `MEL_mh6_room_shell` with same W/D/H
   - PASS requires: both realize non-empty, bbox X/Z equal within 1e-3,
     bbox Y (thickness axis) reported — greybox shell Y = wall thickness,
     mh6 Y = Depth. Document the delta rather than fake a match: the cell
     passes Depth = wall thickness so exteriors read identically; opening
     count is mh6-only (greybox has none), noted as a feature gain.
   - Renders 3-up contact sheet → `Saved/Audit/melusinashouse/v0_c1_identity.png`

### C2 — City cell rewiring (kills the exterior duplication)
1. `melodia_city_gen.py:379` — replace `_ensure_group_node("MEL_greybox_room_kit")`
   with `MEL_mh6_room_shell` via the adapter. Params map: W→Width,
   D→Depth, H→Height, T→Wall Thickness (mh6 SDF hollow offset),
   `Roof Rise` stays cell-level. `Show Roof` gate untouched.
2. Gate: same script, stock vs converged cells across 3 param sets
   (default, tall-narrow, wide-flat). T-corridor and piano walk still green.
3. `MEL_greybox_room_kit` keeps: §16 interiors, corridors,
   `MEL_music_room_shell` (until C3), city plan interiors.

### C3 — music_room_shell folds onto mh6
1. `music_heroes.py::build_music_room_shell` — swap the nested
   `_ensure_group_node("MEL_greybox_room_kit")` for `MEL_mh6_room_shell`
   (same adapter). Dado band, openings bools, realize-for-export unchanged —
   they consume the shell output, not its internals.
2. Gate: `MEL_music_room_shell` evals with dado band present, door+window
   cuts visible in slice probe, vert count same order as before.

### C4 — Monolith room-shell family convergence (read the file first)
The monolith is NOT a bmesh-only surface — its 274 builders author GN nodes
into per-object `SurrealArch_<obj>` trees (v2.132 preserves user-edited trees).
Its room shell `_gb_rect_room_shell:4500` (floor slab + 4 wall slabs +
cutter boolean) is a third shell construction, used by GREYBOX_ROOM,
GB_ROOM_COMPOSITE, GB_COMBAT_ROOM, GREYBOX_TOWER, GB_ELEVATOR_SHAFT, and
MODULAR_HOUSE's wall faces.
1. Do NOT edit inside the 38k-line file. Converge through the sanctioned
   seams: `kit_registration.py::register_kit` (injects a builder into
   `_KIT_DISPATCH`/`_CATALOG_DISPATCH` with param-spec stubs) and
   `melodia_gn_route.py` (routes monolith ids → MEL_ builders).
2. Route the monolith's shell ids onto `MEL_mh6_room_shell` (or the
   converged cell) via melodia_gn_route; register an mh6-backed kit builder
   under `GREYBOX_ROOM`/`GB_ROOM_COMPOSITE` through register_kit if the
   scene workflow needs a callable attr rather than a route.
3. Gate: spawn GREYBOX_ROOM through the monolith's own picker/operator path,
   realize, bbox within tolerance of the pre-convergence piece; slice probe
   shows door/window cuts; room-graph presets (greybox_graph.py) still spawn
   and snap.
4. Keep the bmesh specials (pagodas, hanok, Escher, Klein bottle — ~89
   bmesh sites) as-is: they are one-off object generators, not shells.

### C5 — Roof authority (four surfaces, pick per role)
Roofs are FOUR, not three: `build_roof_tiles` (GN, 10436), `_curved_roof`
(GN helper, 11967), `_conical_roof_swept` (bmesh, 14518), `_build_curved_roof`
+ `_add_roof_modifier_stack` (bmesh object-level, 36575/36813 — the V6/7
staging authority). Declare roles in ADDON_AUTHORITY: object-level roof =
`_build_curved_roof` (kept, used by SurrealRoof_* staging); GN in-tree roof
= exactly ONE of build_roof_tiles / _curved_roof, the other demoted or
aliased; _conical_roof_swept stays only where pagodas/towers call it.
No mesh changes — an ownership declaration plus grep gate.

### C6 — mesh-boolean shell parity check
Greybox shell uses mesh DIFFERENCE boolean; mh6 uses SDF. After C2/C3,
grep confirms `MEL_greybox_room_kit` is nested ONLY by interior/corridor
builders. `grep -rn "MEL_greybox_room_kit" melodia_gn/ | grep -v polyhedra_gn`
must show only: `melusina_house.py` (interiors), `melodia_city_gen.py`
(plan interiors/corridors), `music_heroes.py` — none of them as exterior.

### C7 — Presets, docs, ledger
1. `presets.py` entries for `MEL_city_house_cell` / `MEL_music_room_shell`
   updated if param names shifted (they do not — adapter hides it).
2. `Docs/ADDON_AUTHORITY_2026-09-03.md` — new row: "Room shell (exterior):
   MEL_mh6_room_shell. Room shell (interior): MEL_greybox_room_kit."
3. `melusinahouse_v7_plan.md` ledger: V0 gate row updated with C1–C4 PASS
   lines (dated, evidence paths). Prose is not a ledger row.

## Non-goals (explicit)

- No deletion of greybox — it stays healthy for interiors/corridors.
- No new builders. The adapter is a wiring helper, not a fifth shell.
- No edits inside surreal_architecture_gen.py — convergence goes through
  kit_registration / catalog_dispatch / melodia_gn_route seams only.
- No bmesh-special rewrites (pagodas, hanok, Escher, Zen kits).
- No param renames — the adapter absorbs name differences; downstream
  presets and stage scripts keep working.

## Verification contract (all steps)

Headless (Blender 5.2.1, `--background --python`), realize-instances before
vert counts, judge by print lines, evidence JSON/PNG in
`Saved/Audit/melusinashouse/`. After any addon edit: three-copy sync P: → C:
→ AppData, md5 `3 <hash>` whole-file, then commit P: with the gate evidence.
