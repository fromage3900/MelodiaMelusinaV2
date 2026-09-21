# Melusina's House — GN Final Plan (Paris → Nikki bar)

Date: 2026-09-18. Lens: professional Geometry Nodes expert. Scope: the remaining house build-out
after the Paris phase (GN_PARIS_WallDetail / SlabTrim / CurvedWall + turret skins, saved at
`pre_paris_v2`). Research basis: official Blender 5.2 GN release notes (developer.blender.org),
verified local Higgsas v13 inventory (279 groups) + live-session probe, Infold's Infinity Nikki
UE5 technical interview.

## 1. Research verdicts

### Blender 5.2 GN — what actually changes this plan
- **Mesh Bevel node (new in 5.2).** The long-missing fillet primitive now exists inside GN.
  Fillets stop being a modifier appended outside the group and become authored, per-selection
  group geometry. This is the "proper fillets" answer for the greybox builders.
- **Lists** (Field to List, Get List Item, Filter List, Sort List) + **Collection Children** —
  per-floor / per-bay parameter variation without Repeat-zone accumulation gymnastics.
- **Transfer Attributes** — arbitrary (or all) attributes across geometry-to-geometry, index- or
  ID-mapped. Cleaner multi-attribute carries (band_id + panel_seed together) for wall→shell and
  curve→mesh assembly than hand-rolled Store chains.
- **Atomic merge building blocks** — Merge Points / Cluster by Distance / Cluster by Connected
  give exact control over which points weld. Fits the kit chain Join → Merge(0.02) → Boolean →
  Bevel where a global weld is too blunt.
- **GN modifiers on Empties** (official) — legit effector hosts for fully generated objects and
  collection instances. Watch-list: a house-wide "bay rhythm" controller empty driving wall
  modifiers. Not day-one work; Object Info (RELATIVE) placement already covers current needs.
- Capture Attribute selection, Get Attribute Names, Rename Attribute — hygiene, adopt casually.
- Field dedup + corner-domain avoidance — free performance on the band math (MapRange chains
  evaluated per corner).
- **Experimental procedural hair/cloth physics — NOT adopted.** No consumer in the house; do not
  enable experimental settings in the production .blend. Watch lane for Melusina wardrobe later
  (Wardrobe owns outfit state, per project authority).
- 5.2 modifier-property Python API changed; the `mod.properties.inputs[<identifier>]["value"]`
  truth table already in use matches 5.2. Keep interface identifiers as the key.

### Higgsas v13 — adopt, with the bridge as the only door
Ground truth (live probe 2026-09-18): bridge `deploy/surreal_arch/higgsas_bridge.py` + library
`RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` both on disk;
asset library `Higgsas_Geometry_Nodes_Toolset_v1.3` registered in Preferences. The open session
already carries 4 appended families: `Cairo Tile Grid` (×2 — `.001` duplicate, remove), `Dynamic
Catenary Splines`, `Lissajous Curve`.

Rules (from the verified inventory + bridge):
- Append ONLY via `higgsas_bridge.load_node("NT<Name>")` — on demand, never bulk-load 279. Each
  appended group is a SUBTREE and counts against the node budget.
- Run the Higgsas gate after any bridge-touching edit.
- v1.3 dropped the `NT` prefix in group names; the bridge resolves it. Call with NT names.

ADOPT for the house:
| Higgsas group | Use |
|---|---|
| NTCairo Tile Grid, NTHexagon Grid | Gothic tracery: rose window, porte-cochère fanlights |
| NTBricks Grid | Masonry course variation on plinth + quoin fields |
| NTDynamic Catenary Splines | Garland swags over the porte-cochère and eaves |
| NTRounded Cube | Dormer shells, balusters, newels |
| NTInset Face, NTMesh Offset, NTSolidify | The moulding language where the Extrude-based inset falls short (stepped gothic reveals) |
| NTRounded Cone, NTSpin | Turret caps + finials |
| NTScales Texture | Fish-scale roof relief |
| NTLoft Splines, NTEven Curve to Mesh | Mansard profile loft along the roof ring |
| NTTriplanar UV Mapping | UV hygiene for props only — trim-band surfaces keep the band mapping |

DEFER: solver groups (Ripples — bake-only rule, never in a live tree), Mesh Points Fracture /
Voxel Remesh (destructive, no consumer), Forward/Inverse Kinematics (no chains on a house).

### Infinity Nikki — the bar, made concrete
From Infold's UE5 interview: the series' strength is "small-yet-refined" studio quality — that is
exactly our case (one house, not their open world). Do not chase their open-world scale systems.
- Their look = Disney-PBR lighting under cartoon forms. Geometry levers first, then the
  material/lighting lane (per the established lever order: per-system semantic materials, ground,
  sky/key/fill/rim, emissive windows, set dressing).
- Detail density order for the house: silhouette (roofline) → trim (done) → microrelief
  (tracery/scales/garlands) → color story (pearl-pink / blue-lavender / gold accents per the
  Melodia gem taxonomy).
- Fur spline editing and wardrobe systems: Wardrobe lane owns these; out of house scope.

## 2. Build phases (each: backup stamp → one test object → evaluated-depsgraph measures →
contact sheet to Saved/Audit/melusinashouse/ → save)

P0 — Scene hygiene (small, first): remove duplicate `Cairo Tile Grid.001` (clear fake-user
first); decide WALL_CURVED_TEST fate (proposal: keep, reposition as the south garden wall — it
verified clean; delete only on owner say-so). Backup stamp `pre_nikki_v1`.

P1 — WallDetail v2: fillets and gothic mode IN the kit (the original ask).
- Fold the object-level Bevel (0.04 / 3 segments) into the group with the new **Mesh Bevel
  node**, per-selection, so every wall/slab is self-contained and the modifier stack shrinks.
- Add **Menu Switch CORNICE_STYLE** = FLAT / HAUSSMANN / GOTHIC (5.2: menu socket takes item
  NAME strings; set after naming items). GOTHIC mode: pointed-arch lintel heads (reuse
  `build_gothic_arch` from surreal_architecture_gen — delegation, no reimplementation), stepped
  reveals via NTInset Face + NTMesh Offset, NTBricks Grid quoins along corners.
- Keep the normal-aware inset extrude; upgrade only where it reads wrong.
- Gate: WALL_W001 first (poly delta, band-UV check, closeup), then house-wide rollout.

P2 — Mansard roof + dormers: NTEven Curve to Mesh / NTLoft Splines profile loft around the roof
ring; dormers as Instance on Points with Rounded Cube shells + gothic arch cuts; visible-window
emissive material (Nikki night read). Gate: front + 3/4 silhouette renders.

P3 — Gothic tracery + garlands + turret caps: Hexagon/Cairo tracery fanlight over the
porte-cochère; catenary garlands bound to the curved cornice (Align Curve to Surface — no
floating geometry); Rounded Cone + Spin finials on T042/T043 turret shells. Gate: closeups of
each surface + node-budget count.

P4 — Surface contrast: the stone sheet art is extremely low contrast (root-caused, not a GN/UV
bug). GN-lane answer: the inset shadows already bought most depth; optional microrelief bump.
The art itself is the trim pipeline's artifact — flag a contrast pass to the trim lane (owner
decision), do not re-author here.

P5 — Tail (optional): parterre/hedge scatter — DistributePointsOnFaces + Collection Children
lists for variation; Lissajous hedge motif as the signature (already appended in-session).

## 3. Ownership + pipeline law (binding)
- Builders extend `deploy/surreal_arch` + the Melodia Studio addon (`register_builder`, explicit
  side-effect import in `__init__`). Never hand-rolled standalone blends.
- New GN groups named GN_PARIS_* / GN_MH_*; named groups with exposed interface parameters —
  never baked-flat meshes. Trims enter only via `trim_sheet_lab`.
- One editor instance, one bridge. `Saved/MelusinasHouse/*.blend` are local-only (gitignored);
  scripts are the tracked artifact. Backups before every mutation; `paris_wrap.py` + target file
  for all bridge runs; cleanup DIAG_ objects same-session.
- No experimental physics in the production file. No git operations without explicit owner
  approval — this plan doc is a file creation only.

## 4. Honest limits of this research
Read the official 5.2 GN release notes (not every 5.2 manual page) and the UE Nikki interview;
Higgsas review is grounded in the verified v13 inventory and the live probe, not every group
re-tested. Node names still get probed before wiring (throwaway node pattern) — 5.2 already
renamed several things once (SplineParameter, FunctionNodeCompare).

---

## Floating-geometry sweep — results (2026-09-19, session 20260918_214925_b2872e)

ROOT CAUSES FOUND AND FIXED (all in `deploy/surreal_arch/melodia_gn/paris_wall_detail.py`):

1. Quoin "monster" staircase (32.18m): MeshLine nodes silently stuck in OFFSET
   mode (END_POINTS enum swallowed by try/except in 5.2) → 0.06 + 11x2.92 stack.
   Fixed with explicit per-step offset wiring (0.2655m x 12). Z max now 4.31.
2. World-vs-local trim placement (THE REAL FLOAT): the group read trim positions
   from the world-space BBox Min/Max modifier inputs and applied them to the
   mesh's LOCAL coordinates — correct only for identity-matrix objects. Every
   wall's trim was floating 3-5m off its wall. Fixed by deriving bbox from the
   input geometry itself (GeometryNodeBoundBox node) in WallDetail + SlabTrim;
   the BBox input sockets are now ignored (kept for API compatibility).
3. End-of-chain bevel spikes + vert bomb: beveling the whole stream multiplied
   verts ~14x and spiked degenerate panel edges (10 verts to z 6.0). Bevel is
   now applied ONLY to the band cubes (clean boxes) at their join.
4. Medallion overhang: the 1.392m arch instances were placed at panel-face
   centers regardless of fit — arches near wall ends poked ~0.5m out. Added a
   point fit filter (|x - center| <= W/2 - 0.716) before Instance on Points.

VERIFICATION (nikki_gate2.py — authoritative gate, base = kit-only evaluation,
ParisDetail muted, world-space, per-axis tolerances): 15 walls + 5 slabs PASS,
0 failures. W001: 61,180 -> 1,217 verts (X +3.16 -> +0.04, Z +0.33 medallion
crowns, within 1.35). W002: 3,264 -> 760 verts, 0 strays. W015: trim follows
rotation flush. Slabs: all within 0.10.

VISUAL: 3 wall verification renders + 6 final decor renders
(Saved/Audit/nikki_decor/renders/), vision-checked: no floating geometry, no
staircase, no spikes; trim flush on straight, curved, and rotated walls.

W002 note: earlier "kit modifier vanished" was a measurement artifact — the
base mesh (o.data) IS a raw 8-vert cube by design; the SurrealArch kit modifier
(SurrealArch_Cube.002) builds the wall and was present all along.

Deferred (deliberate): per-face-normal medallion rotation (currently global
W>D heuristic + fit filter, passes gate); scalar-into-Translation band wiring
(evaluates correctly, style only); NTInset Face swap (needs library append).

## Post-review correction (2026-09-20)

The disc-state review found the saved blend WRECKED at 00:32 (post-dated the
verified 15:59 state): a rebuild crashed inside the medallion fit filter —
5.2's GeometryNodeDeleteGeometry has NO Domain/Mode input sockets (they are
node properties, defaults POINT/ALL) — leaving a 99-node unwired WallDetail
partial, no SlabTrim, all ParisDetail modifiers orphaned (node_group=None).
Fixed by dropping the two input assignments; rebuilt 177/33 nodes, both groups
out_wired, all modifiers assigned, gate ALL PASS (14 walls + 15 slabs), saved.
The overnight GUI session / cron fleet likely triggered the crashed rebuild;
the module now builds clean, but any scheduled job that rebuilds paris groups
should re-run the gate + introspection after saving.

SlabTrim bevel clarification: the "no end-of-chain bevel" fix applies to
WallDetail. SlabTrim retains its end-of-chain bevel (ap2 -> bvl -> gout2,
0.04/3) — its stream is a single clean slab mesh (no degenerate duplicates),
gate-verified within 0.10 on every slab.

## Doorway regression — investigated 2026-09-20, verdict: NOT a regression

Report: "you cant enter the house anymore, the doorways have been removed
seemingly." Six checks against disc, all clean:

1. Inventory diff vs pre-polish backup (Sep 18): zero objects removed,
   added, or visibility-changed.
2. Positions: all 51 WALL_/MISC_/FLOOR_/SLAB_ objects byte-identical except
   WALL_CURVED_TEST (moved away from the house to 12,-4 by a session snap test).
3. Every kit wall is a solid closed box (zero boundary edges) with evaluated
   vertex counts matching the Sep 19 gate exactly (W002 760 / W007 632 /
   W013 692); kit groups and modifier inputs unchanged.
4. W001's archway — the only real opening in any wall — renders open from
   front, back, and 3/4; clear passage.
5. Trim overshoot max 0.12m, symmetric; nothing reaches the gaps between
   wall segments.
6. The user viewport faces the decor installation; the overnight fleet's
   changes are additive decor (fish group 57->96 nodes), not walls.

What the user saw was almost certainly the 00:32 wreck window: walls stripped
to bare kit cubes with every ParisDetail modifier orphaned. Repaired 00:36,
gate ALL PASS. If missing doorways are still observed live, the report needs
a wall name or file name — the compound on disc contains none.

## Close-out 2026-09-20 — UE staging

Payload for git: deploy/surreal_arch/melodia_gn/paris_wall_detail.py (md5
9a6ae693, deploy = live addon), this plan doc, and a close-out evidence note
under Saved/Audit/. Study blends stay local per standing convention.

Desktop-side staging checklist (canonical machine):
1. Pull the task branch; review module diff (501+/611- vs f0c760f6).
2. Re-run census: blender --background --factory-startup --python
   Tools/melodia_studio_census.py (expect PASS, 0 lost / 0 new).
3. installer re-stamp + install_melodia_studio.ps1 -CheckOnly (LIVE ADDON
   SYNC: OK).
4. UE side: GN module is Blender-authoritative; UE consumes staged geometry
   via the existing pipeline. No UE Content changes in this payload.

Open items carried forward (not blockers for staging):
- Gate count discrepancy: 2026-09-19 report said "15 walls + 5 slabs",
  2026-09-20 re-run says "14 walls + 15 slabs". Recorded verbatim, unexplained.
- Any scheduled job that rebuilds paris groups must re-run the gate +
  group introspection after saving (the 00:32 crash-save shipped unnoticed).
- Deferred: per-face-normal medallion rotation; scalar-into-Translation band
  wiring (evaluates correctly, style only); NTInset Face swap (needs library
  blend appended first).
- WALL_CURVED_TEST parked at (12,-4), off the compound.

