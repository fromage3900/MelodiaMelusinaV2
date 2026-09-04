# Melusina House V7 — Grand Plan

Written 2026-09-04, after the v6 convergence session (C: commit 7900f950, P: e17ec030).
Authority doc: `P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md`.
Canonical references: image boards in `P:/MelodiaMelusinaV2-Laptop/Docs/References/MelusinasHouse/`,
house plan in `melusinashouseplan.md` (this repo).

## North star for V7

**One genome, zero parallel authorities.** Every room, wing, and roof in the mansion
stages through the Melodia Studio addon's registered builders. No stage script builds
mesh or node trees inline. If a feature is missing, it becomes an addon builder first
(P: SSOT → sync → md5-verify), then the stage script nests it.

Blender target: **5.2.1 LTS** (current install is already newest — verified 2026-09-04
against download.blender.org and blender.org; nothing to update).

## Where V6 ended (facts, not claims)

- Roofing converged: cells stage `Show Roof=False`, roofs are `SurrealRoof_HIP_*`
  objects from the monolith `_build_curved_roof`. Floating-roof defect dead.
- Organ split: `MEL_music_organ_pipes` standalone; facade nests it.
- T corridor: `Corridor Type 4` via `MEL_greybox_junction`.
- Piano walk parameterized (was a dead-param stub).
- Copy discipline: P: SSOT → C: → AppData, md5 `3 <hash>` after every edit.

## V0 — ROOM SHELL CONVERGENCE (the gate; everything else waits)

Two room-shell systems exist and both are alive:

| System | Owner file | Nature |
|---|---|---|
| `MEL_greybox_room_kit` | `polyhedra_gn.py` | Boolean hollow box + openings; the shell inside `MEL_city_house_cell` |
| `MEL_mh6_room_shell` | `melusina_house_v6.py` | Genome shell: SDF grid boolean + fillet openings, curve bend, cornice ring, bbox-driven |

They are parallel authorities for the same job (a wall/room shell with openings).
V7 kills the duplication:

1. **Promote `MEL_mh6_room_shell` to THE shell authority.** It is strictly more
   capable (SDF-filleted rounded openings, curve bend, cornice, bbox-genome params).
2. **Rewire `MEL_city_house_cell`** to nest `MEL_mh6_room_shell` instead of
   `MEL_greybox_room_kit` for its outer shell (params map: W/D/H → Width/Height,
   Depth = wall segment thickness, Wall Thickness passes through, Opening
   Columns/Rows/Scale from cell-level knobs). `MEL_greybox_room_kit` remains for
   interior rooms/corridors (simple hollow boxes) but no longer builds the
   exterior shell of any house cell.
3. **Prove identity before switching:** side-by-side headless render, stock cell vs
   converged cell; openings must survive, bbox must stay W×D×H exact.
4. **Then** `MEL_city_plan_*` interiors, avenues, and blocks inherit automatically —
   no edits below the cell.
5. Delete nothing yet; `MEL_greybox_room_kit` keeps its corridor/interior role.
   After V7 ships and a full city smoke passes, re-evaluate demoting it.

**Gate:** headless eval — converged cell vert count within expected band, bbox
exact, T-corridor still green, piano walk still green. Ledger row in this file.

## V1 — ROOF AS A FIRST-CLASS BUILDABLE (not just staged)

Current state: roofs are per-object bmesh pieces placed by the stage script.
V7 moves roof authority into the cell while keeping the monolith as the generator:

1. New thin builder `MEL_city_roof_hip` — a GN wrapper that emits only the
   parameter carrier: it does NOT mesh a roof. Instead `MEL_city_house_cell` grows
   `Roof Span/Depth/Rise/Overhang/Eave Curve` params, and the stage script reads
   them off the cell object to drive `SurrealRoof_*` creation. Cell = single source
   of roof numbers; monolith = the only roof mesh generator.
2. Optional `Roof Style` int on the cell (0 none, 1 hip, 2 gabled, 3 pagoda) —
   mapped 1:1 onto `surreal_arch_props.roof_type` strings by the stage script.
3. Tower roofs: `Tower=True` cells get a second `SurrealRoof_ONION` from the same
   params (no new builder).

**Gate:** one param edit on the cell changes the staged roof on rebuild.

## V2 — INTERIOR CONVERGENCE (REF_03 board)

1. Round/salon/courtyard plans stay as-is; audit that plan interiors reference
   `MEL_greybox_room_kit` only where a simple box is wanted.
2. Add `MEL_mh6_room_shell`-based curved interior partitions where the board shows
   rounded flow (reuse the same genome shell with `Curve=1`).
3. Furniture dressing stays in `house_dress.py` family — extend, never inline.

## V3 — MUSIC-WORLD KEYS (the project's reason to exist)

1. The piano walk (parameterized), organ facade, and sheet rail become the
   "musical lock" set: each dressing piece gains a `Melodia Key Id` string param
   (stored as a custom prop on the object), matching the game's
   `melodia:travel:`/puzzle naming — no gameplay logic in Blender, naming only.
2. Chime row / instrument builders stay in the music kit; no new instruments.

## V4 — EXPORT & VERIFICATION RAIL

1. One verify script to rule them all: `Tools/house_v7_verify.py` — builds
   stock + converged cells, T corridor, piano walk, organ split, roof params,
   renders a 4-up contact sheet, writes JSON verdict to
   `Saved/Audit/melusinashouse/v7_verify_last.json`.
2. FBX export profile: per-cell realize+export with materials, matching the
   UE-side import already used for V4 assets.
3. Optional overnight cron: rerun verify + hero render on the C: repo; morning
   report only (no mid-run messages).

## Discipline (unchanged, restated because it is the plan's spine)

- P: SSOT → C: → AppData sync + md5 `3 <hash>` on every addon edit.
- Discovery checklist before any new builder (grep both trees + GROUP_BUILDERS +
  monolith props).
- Headless verify with realize-instances before vert counts; judge by print lines.
- Commit targets: C: → melodiamelusinav2.git, P: → MelodiaMelusinaV2.git; confirm
  with owner before pushing either.
- Prose is not a ledger row: every V# gate gets a dated PASS line here.

## Ledger

| Gate | Status | Evidence |
|---|---|---|
| V0 room-shell convergence | **BLOCKED — mh6 builder defects found 2026-09-04** | `Saved/Audit/melusinashouse/v0_shell_convergence_proof.png`; forensics in session log |
| V1 roof params on cell | OPEN | — |
| V2 interior convergence | OPEN | — |
| V3 music keys | OPEN | — |
| V4 verify rail | OPEN | — |

### V0 forensics (2026-09-04) — do NOT rewire the cell until these are fixed

The V0 proof exposed two real defects in `MEL_mh6_room_shell`
(`melodia_gn/melusina_house_v6.py`), confirmed by differential repro against a
hand-built identical chain (which evaluates correctly):

1. **Empty-cutter collapse.** With `Opening Columns=0` (or any config yielding zero
   cutter instances), the realized cutter field is empty, `MeshToSDFGrid` of it feeds
   `SDFGridBoolean.Grid 2`, and the boolean destroys the wall field — output is a
   112-vert flat plane. Fix: gate the boolean on cutter-count > 0 (Switch on the
   boolean output vs the fillet-direct path).
2. **Thin-wall collapse.** With cutters present the wall evaluates 3D but ~0.3 m
   thick in Y regardless of `Depth` (e.g. Depth 2.0 → Y span ≈ 0.32). A
   node-identical scratch chain keeps full volume, so the cause is inside the tree
   (bend `SetPosition` was already fixed 2026-09-04: it used `Position` (replace
   mode) instead of `Offset`, flattening all vertices — fixed and synced, but the
   thin-wall issue remains). Next step: node-by-node bisection with a Stored Named
   Attribute tap between bevel → SDF → boolean → fillet → offset.

Also verified during forensics: plain `Mesh→SDF→GridToMesh` roundtrip, boolean with
real cutters, fillet, and `SDFGridOffset` at Distance 0 all preserve volume in
isolation on 5.2.1. The combination inside mh6 does not — it is a wiring bug, not an
SDF-node behavior bug.

**V0 gate rule stands:** no cell rewiring until a converged mh6 shell matches the
stock cell's bbox exactly at the same params.
