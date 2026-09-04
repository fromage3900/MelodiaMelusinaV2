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
| 4 | Monolith greybox dispatch | `surreal_architecture_gen.py` `_KIT_DISPATCH` | Fourth surface, bmesh. | **LEAVE: different job (scene ops), not a GN shell** — documented, not merged |

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

### C4 — mesh-boolean shell parity check
Greybox shell uses mesh DIFFERENCE boolean; mh6 uses SDF. After C2/C3,
grep confirms `MEL_greybox_room_kit` is nested ONLY by interior/corridor
builders. `grep -rn "MEL_greybox_room_kit" melodia_gn/ | grep -v polyhedra_gn`
must show only: `melusina_house.py` (interiors), `melodia_city_gen.py`
(plan interiors/corridors), `music_heroes.py` — none of them as exterior.

### C5 — Presets, docs, ledger
1. `presets.py` entries for `MEL_city_house_cell` / `MEL_music_room_shell`
   updated if param names shifted (they do not — adapter hides it).
2. `Docs/ADDON_AUTHORITY_2026-09-03.md` — new row: "Room shell (exterior):
   MEL_mh6_room_shell. Room shell (interior): MEL_greybox_room_kit."
3. `melusinahouse_v7_plan.md` ledger: V0 gate row updated with C1–C4 PASS
   lines (dated, evidence paths). Prose is not a ledger row.

## Non-goals (explicit)

- No deletion of greybox — it stays healthy for interiors/corridors.
- No new builders. The adapter is a wiring helper, not a fifth shell.
- No monolith surgery — the `_KIT_DISPATCH` surface gets a doc note only.
- No param renames — the adapter absorbs name differences; downstream
  presets and stage scripts keep working.

## Verification contract (all steps)

Headless (Blender 5.2.1, `--background --python`), realize-instances before
vert counts, judge by print lines, evidence JSON/PNG in
`Saved/Audit/melusinashouse/`. After any addon edit: three-copy sync P: → C:
→ AppData, md5 `3 <hash>` whole-file, then commit P: with the gate evidence.
