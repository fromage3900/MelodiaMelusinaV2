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

## V5 — ADDON CONSOLIDATION (from the 2026-09-04 three-study review)

Sources: overlap inventory + consolidation roadmap + rebrand study (three read-only
subagent audits of the live addon). Key correction they produced: the addon has
**267 registered builders across ~62 modules** (not 173), and 16 of them are dead.

### Study findings (evidence-backed, file:line in subagent reports)

- **Latent load break (fixed 2026-09-04):** `melusina_house.py` was missing from the
  P: SSOT (present in C: + AppData only) while `__init__.py` imports it — fresh P:
  clones could not import the addon. Restored, committed d2b7ce4d.
- **16 dead builders in 9 modules:** `mother_v3.py` (8), `mother_tapestry_wall.py`
  (1), all 7 `p4_*.py` — never imported anywhere, registrations never run.
- **8 passthrough stubs** (7 p4_* + mother_tapestry_wall): geometry-less trees, two
  conflicting `make_group_input`/`link_sockets` signatures held together by
  exception-swallowing.
- **Major parallel-authority clusters:** music/notation (46 MEL_music_* ids across
  11 modules + 4 monolith notation builders), castle (20 MEL_castle_* vs 8 monolith
  bmesh), greybox (THREE surfaces: monolith dispatch, MEL_greybox_*, _KIT_DISPATCH
  kit layer), roofs (THREE inside the monolith alone: _build_curved_roof,
  _curved_roof GN helper, build_roof_tiles), props (4 duplicated), house/city
  (FOUR authorities), Escher (monolith GB_ESCHER_* vs MEL_escher_*).
- **Version-ladder ambiguity:** harp ×4, waveform_wall v1/v2, pcg tags v1/v2
  (v1s hidden but registered, identical bodies), kit_v2/v3/v4 era-named modules
  hiding their contents.
- **Naming chaos:** castle pieces spelled three ways (KEEP / CASTLE_KEEP /
  MEL_castle_keep); zen lantern three ways; `set_dressing.py` registers via f-string
  concat so ids never appear in source (breaks grep inventory); routing-only ids
  invented in melodia_gn_route.py.
- **Backup dir inside the addons tree:** `melodia_gn.bak_180215/` (60 files) —
  import-shadow risk.
- **Rebrand:** one product, three identities today (monolith bl_info, separate
  melodia_studio panel addon with colliding name, MEL_* GN ids). Recommended:
  keep "Melodia Studio" as single umbrella, absorb the panel addon as a "Resonant
  World" section, one preferences entry (bl_idname melodia_studio), one N-panel tab
  (Architecture / Music Geometry / Resonant World / Catalog & Export), operators
  relabeled "Melodia Studio: <Verb Noun>" with legacy surreal_arch.*/mel_gn.* as
  hidden forwarding aliases. Ship merged addon + retired stub in ONE release.

### Consolidation phases (effort S/M/L, each with a gate)

| Phase | Work | Effort | Gate |
|---|---|---|---|
| 0 | Verification harness `Tools/verify_melodia_gn.py` (per-builder eval + realize + PASS/FAIL) + md5 three-copy sync check + registry baseline JSON + contact sheet | M | Harness prints PASS for every live builder; failures = the work queue |
| 1 | Quarantine the 8 stubs behind `role='research'`/hidden; unify call signatures; owner decides promote/keep/delete per p4 builder | S | Stubs out of catalog, harness PASS, decisions recorded |
| 2 | Role separation: declare bmesh-monolith vs GN ownership table in ADDON_AUTHORITY; resolve polyhedra_gn straddle; index monolith greybox functions | M | No subject owned by both paths; doc table complete |
| 3 | Module merges for coherence: instruments→music_kits/, harps→music_harps.py, notation→music_notation.py, escher→escher_extras.py, env+set_dressing merged, terrain package, core.py split (registry vs params) | L | Zero registry-name loss vs baseline; contact sheet reviewed |
| 4 | Deprecation machinery (`deprecated_by=` alias in register_builder); delete dead v1s/stubs after one clean owner session; deletions logged in ADDON_AUTHORITY | M | Zero unreferenced builders; every name live, research-flagged, or deleted-and-logged |
| 5 | Standing ritual: harness + sync check mandatory post-edit; `--changed-only` mode; skill update | S | Green run on fresh checkout of all three copies |

### Rebrand decision needed from owner

Pick one: (1) Melodia Studio umbrella [recommended, cost M], (2) Surreal Studio
[architecture-first, M], (3) Melodia Forge [clean break, L]. Whatever the choice:
no MEL_* id renames in v1, legacy operator aliases mandatory, one release with the
merged addon.

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
| V0 room-shell convergence | **DEFECTS VERIFIED FIXED; identity gate OPEN** 2026-09-06 | `Tools/house_v0_shell_proof.py` → `Saved/Audit/melusinashouse/v0_proof_last.json`: empty-cutter guard holds (0x0 = 87,856 verts, not the old 112-plane), openings survive (3x2 > solid), full Y span honored. NOT yet identity: converged Z overruns stock by 0.085 m (SDF voxel 0.035 quantization + fillet band), and T=2.0 hits the adapter's span clamp (Y bbox 4.096). Rewiring stays gated until tolerance is adjudicated (raise tol to voxel-quantization scale, or refine the shell) — owner call. |
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
