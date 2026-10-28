# Melusina Housing HDA Stack — Technical Breakdown (Hero System 1/3)

**Date:** 2026-10-28 · **Author lane:** build (CAD Architect / Houdini Engine)
**Machine-readable pin:** `specs/housing/melodia_housing_stack.v1.json`
**Live level (read-only audit, untouched):** `/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0` — 243 actors
**Status authority:** `CURRENT_STATE.md`. This doc is the lasting technical record, not status.

## 0. What this system is

One interior-geometry owner (`melodia::room_shell` family) plus its companion producers —
stained glass, exterior kit, terrain/caves — driving Unreal through Houdini Engine with a
closed material contract and named dressing surfaces. No second owner, no new framework:
every capability below extends the existing shell owner.

Grid law: **0.6 m module, 2.4 m bays** (= 1 bar of 4/4 at 128 BPM). Standard portal
**2.4 × 3.2 m at floor level**. Portal height is 5.33 beats (a 3:4 fourth) — recorded, not rewritten.

## 1. Live stack as found (editor-query readback, 2026-10-28)

| Live actor | Transform (cm) | Sections / material |
|---|---|---|
| `HDA_House_Salon` | (360,-330,0) | 1 × `houdini_default_material` (GREY — defect) |
| `HDA_House_Bedroom` | (-1152,-96,0) | 1 × `houdini_default_material` (GREY — defect) |
| `HDA_Corridor_Garden_Live` | (1586,-396,0) | 1 × `MI_Poitou_LimeWash` |
| `HDA_Gallery_Upper_Live` | (285,0,440) | 1 × default (grey) |
| `HDA_Porch_Live` | (2306,-396,0) | 1 × `MI_Poitou_Quoin_Limestone` |
| `HDA_Roof_Salon_Live` / `Bedroom` / `Corridor` | — | 1 × `MI_Poitou_Tile` each |
| `HDA_RoofTrim_*` | — | trim actors, single-section |
| `HDA_Stair_Gallery_Live` | (1020,-590,0) | present, single-section |
| `HDA_MelusinaHouse_Landscape` | (18909,18900,0) | **0 components — emits nothing** |
| `STAGE_HouseExteriorKit_v1` | (120,0,100) | **5 sections, all resolved** (PearlPlaster, Lavender/BlueScaleRoof, GiltTrim, LanternGlow) |
| `STAGE_Salon_ExplicitShell_*` (×2) | staged aside | 1 × default each |

Root cause of the grey Salon/Bedroom: every live interior cooks through
`Content/HDA/MelodiaRoomShell_1.0.hda` (`96958AB6…`, 47,247 B), whose embedded
PythonModule **predates** `openings_json`, `simple_floor_collision`, and the entire
`unreal_material` contract. Single-section output is the signature of that stale bake —
the converged modules emit 6–9 role sections.

## 2. The converged stack (pinned, Hython-proven)

**Rect rooms** — `hda/MelodiaRoomShell_ContactFloor_1.0.hda` (`078775C0…`, 61,517 B).
Gate **20/20**. Additive delta over shipped is proven byte-exact on rendered geometry
(74,540 pts / 20,035 prims identical; +24 pts / +6 prims = the invisible collision slab
`collision_geo_simple_box_main_geo` paired with `rendered_main_geo`). Adds
`openings_json` (named floor-level portals), `material_map_json` per-actor override,
`unreal_material` prim attribute, `surfaces_json`, 7 prim groups.

**Rounded salon** — `hda/MelodiaRoomShell_Rounded_1.0.hda` (`05A1071B…`, 59,733 B).
Gate **29/29** on 18,240 prims / 72,416 pts. Ellipse/superellipse/polygon plan, theta-
or bay-parametrised portals cut as exact plan vertices, `tiers_json` setback massing that
steps the wall band **without moving interior volume** (tier change ⇒ different geometry
hash, same footprint). No windows, no collision slab yet; sockets diagnostic-only.

**HDA graph anatomy** (both modules, `Tools/Houdini/room_shell/`): interlocking half-lap
wall panels → floor medallion + skirting + chair rail + bead swags + acoustic tuning +
Chladni dawn puzzle + streamer-ribbon lib → Paris wall detail
(`CORNICE_STYLE` flat/Haussmann/Gothic) + Nikki bead/star/heart/crystal decor, cord
strands, parabolic bead strings → portal cutter (plan-projection, header-exact) →
role/material classifier → dressing-surface classifier (role **and** face geometry;
`wall_plaster` splits wall-body vs ceiling slab; `surface_wall` is interior-only so
exterior faces never scatter props) → `Mesh.poly` emission (Houdini clockwise-front
winding; `Mesh.F` stores reverse right-hand order — readers must un-reverse before
Newell tests; pinned by assertion, do not "fix").

**Stained glass** — `Content/HDA/MelodiaStainedGlassWindow_1.0.hda` (`D3B86A18…`),
Gate 2 GREEN: frame + pane + panel/geometric/intersecting tracery + Chladni lead came,
per-note hue via `NOTE_HUE_TABLE`. Zero placements in House P0 — first glass belongs
to the Salon proof.

**Exterior kit** — `Saved/Staging/HouseExterior_20261023/MelodiaHouseExteriorKit_1.0.hda`
(`70A38CB2…`): the only multi-section resolve on the map (5/5). Palette carrier —
pearl plaster / lavender + blue scale roofs / gilt trim / lantern glow — matching
REF_01 (pearl-pink / blue-lavender / gold).

**Terrain + caves** — `Saved/Staging/HouseTerrain_20261023/` (`27B8EBF6…` / `50882540…`):
house-measured pad, horizon ridges, paths, caves. Candidates only; registry promotion
untaken; live landscape actor is empty.

## 3. Salon proof of concept — `salon_bay`

Selection: **bay-aligned 16.8 × 12.0 × 7.2 m** (28/20/12 beats), tiers `[1.0, 0.92, 0.84]`,
portals `salon_entry` θ=0.25 / `salon_front` θ=0.75 (2.4 × 3.2 m, floor level),
21,450 prims. Rejects the measured 15.84 m variant as the documented off-grid exception
(it stays valid, it just doesn't join the kit). Step massing reads from the canal as
the ziggurat that marks the big room; interior volume never moves.

Staged file `Saved/Staging/PoitouInteriors_20261025/MelodiaRoomShell_Poitou_salon_bay_1.0.hda`
disks at `D7915DCA…` — **all six staged variant hashes differ from their
`interior_manifest.json` pins** (material-contract rebuild without a manifest update).
Variant re-verification is owed before any admission; family-base gates do not cover it.

Salon dressing contract (already authored, `specs/p0/melusina_house_p0_dressing.v1.json`):
37 salon placements on the measured 60..1350 × -1780..0 plan; fill contract
(`melusina_house_p0_fill.v1.json`) reserves density scatter to tolerance-loose species
only — contact pieces stay hand-placed. PCG samples `surface_floor/wall/sill/ledge`,
never material roles.

## 4. Room plans reviewed

- REF_01 exterior (pearl-pink/blue-lavender/gold, tower counterweight, shell crests) —
  canonical committed board; exterior kit matches it.
- REF_02 build sheet (foundation/wall/roof/tower split, reusable window/door family,
  trim/shell/pearl/railing repeaters) — the stack's module split follows it.
- REF_03 cutaway (rounded lower-floor flow, centre sitting room, music/prayer nook,
  curved stair, sleeping/writing loft) — dressing spec notes the committed JPEG is
  corrupt; treat text citations of it as provisional.
- `OriginalDesign/melusinahouseplan_2026-09-02.md` + `MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md`
  (9-room constellation, acoustic gather/guide/release): **referenced by three specs but
  absent from `main` and from the pre-collapse tag — REFERENCED BUT UNCOMMITTED.**
  No plan content was inferred; only the specs' explicit citations (portal sizes, room
  tags, nook program) were used. Genuine GN dressing rules (e.g. `MEL_mh6` placement
  frames) do not transfer 1:1 — live shells are Houdini bakes, not Blender wrappers.
- Floral sigils: 6 families / 45 PNGs (`RawArt/…/SalonFloralSigils_20261022/`), contract
  maps BaseColor/ORM/Normal/Height/Emissive onto `Toon_Universal`, staged through
  existing MIs only — none imported to UE yet. Salon floor/ceiling dressing lane.

## 5. Missing systems (the convergence backlog — M1…M10 in the stack pin)

In priority order for the Salon proof: (1) variant re-verify + rounded collision slab +
real `mesh_socketX` outputs; (2) Salon live recook through the converged rounded
definition with `STAGE_` aside-compare first; (3) stained-glass placement; (4) pearl_shell
hero MI decision (61% of bedroom faces ride a provisional borrow); (5) roof/trim/porch/
stair source-HDA identification; (6) terrain/caves promotion; (7) sigil import; (8) fill
volumes. Promotion in-place vs sibling type is an **owner decision** (recorded, not taken).

## 6. How to demo this (portfolio lane)

1. Native: `hython` drive/restore on `salon_bay_radius`-class controls (family pattern:
   bay-radius/tiers/portal-theta), fresh-process reopen, hash compare.
2. Contract: `unmapped_roles` sweep (9 roles → 0 unmapped), `roles_mapped` gate,
   `promotion_delta` proof (rendered-identical + slab-only delta).
3. Live: staged Salon aside-compare vs grey live Salon; 5-section exterior kit vs
   1-section live interiors; `surfaces_json` areas feeding one PCG fill volume.
4. Breakdown renders: wall-band section showing tiers, portal cutter plan projection,
   medallion/skirting/chair-rail stack, glass tracery + came.

## 7. Evidence ledger (this change set)

- Live audit: editor-query readback, 243 actors, mats/transforms — structural, not PIE.
- Hashes: 8 SHA256 disk verifications (family 3/3 match registry; staged variants 6/6
  drift from manifest — flagged, not hidden).
- No map mutation: zero dirty packages added by this lane; level untouched per the
  hand-arranged rule. `scene_context_cycle.begin()` could not run — the snapshot tool
  calls a removed API (`get_editor_world`) under UE 5.8 and raises; preflight was the
  readback above instead. Tool fix is separate work, not claimed here.
- Not claimed: PIE, traversal, visual acceptance, promotion, packaging.


## 8. Assembler green + Jev verdict (2026-10-28 batch A)

`Tools/Houdini/room_shell/house.py` assembles SALON_FIRST (rounded salon +
rect landing, snapped portal joint, porch stair run, both mansard roofs,
foundation pad) in one gate: **all_pass, 23,117 prims / 91,844 points, zero
unmapped roles, all five dressing surfaces non-zero, 4 sockets, 7 named prim
groups, deterministic.** Per-face `surface` + `room` tags ride every prim for
the PCG branch; meta/face counts asserted equal.

Jev plan-audit via beam (`reflection/beam-1.0-501b-a23b:free`,
`response_format: json_object`, criteria text transmitted, authored-only
enforced, receipts in `Prototypes/JevHouseAudit/`): run 1 (red state) ordered
ASSEMBLER_GREEN (0.75), riskiest socket math (0.5); run 2 (green state) ordered
PACKAGER (0.78), riskiest UE cook scale (0.52). Agreement across the state
change; needs_human false both runs; readiness 1 -> 2. Next: packager subnet.
