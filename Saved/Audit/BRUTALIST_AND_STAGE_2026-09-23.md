# Brutalist pair + Track A builders 4-6 + GN showcase stage — 2026-09-23

Laptop session record. All numbers from the runs on this tree, Blender 5.2.1
headless, factory-startup.

## What shipped

| Builder | Nodes | Verts (default) | Params | Presets | Health |
|---|---|---|---|---|---|
| `GN_PARIS_Mansard` | 272 | 1,192 | 17 | 3 | PASS problems=0 |
| `GN_PARIS_PenroseArch` | 185 | 144 | 19 | 4 | PASS problems=0 |
| `GN_PARIS_MetamorphosisFrieze` | 156 | 11,152 (seam preset) | 15 | 4 | PASS problems=0 |
| `GN_BRUTALIST_OfficeBlock` | 254 | 904 | 17 | 4 | PASS problems=0 |
| `GN_BRUTALIST_CubicleFarm` | 321 | 2,098 | 18 | 4 | PASS problems=0 |

- **Mansard**: two-slope Haussmann roof band; roof height is DERIVED from the
  slopes (eaves cannot float); zinc seam ribs, gabled/oculus dormers, chimney
  stacks with pots, iron cresting.
- **PenroseArch**: the tribar join as a doorway. `Impossibility` slides the two
  join blocks in opposite Y directions - 0 is an honest arch, +/-1 is the
  paradox, and the bbox y-span grows with it (probe: 0.615 -> 0.916).
- **MetamorphosisFrieze**: bird->fish morph band. The seam STRADDLES the
  species boundary (floor(seamN/2) either side) and instancing both species in
  those cells IS the interlock (probe: seam 0->3 = +120 verts).
- **OfficeBlock**: beton brut slab - full-height piers at every bay line on all
  four faces, flush board-marked spandrels, glass sunk a full reveal behind
  both, pilotis lobby (columns + glass + ground beam, all deleted when off),
  stair tower with slot windows, parapet, roof plant + stacks.
- **CubicleFarm**: shared-partition cubicle grid - left wall per cell plus one
  closing wall per row (no doubled panels), pedestal desks, monitors, chairs,
  overhead bins, waffle ceiling with lights, plants. Rows are guarded
  instances (slots pattern): Rows 1/3/8 = 1106/2098/4578 verts. `Drift` shears
  each row sideways without rebuilding (same verts, moved bbox: xmax
  5.12 -> 9.65 at Drift 1.0).

## New shared infrastructure

`melodia_gn/paris_common.py` - the family outgrew copy-and-patch preamble.
Now also carries:
- `_sock()` - resolves a NODE to its output socket in `mathn` / `combine` /
  `xform` / `inst_realize` / `gn_line` / `cube_s` / `cyl` / `cone` / `sphere` /
  `booln`. Kills the silent-dropped-link bug class below.
- `gn_line()` - the house MeshLine-in-OFFSET-mode pattern (count may be int,
  math node, param name, or bare socket; start/offset always CombineXYZ).

## Defects the harnesses caught (a green build would have shipped all of these)

1. **Node-vs-socket dropped links.** Passing a CombineXYZ NODE where a socket
   was expected made `NodeLinks.new` fail; `link_sockets` records the failure
   and the build stays green with silently-wrong positions. Caught on the
   first smoke of both brutalist builders (11 + 10 dropped links). Fixed
   centrally with `_sock()`.
2. **Left/right piers doubled their X** - position was applied in BOTH the
   line start and the instance translate, putting side piers at +/-18.9 instead
   of +/-8.7. Found by the per-part bbox probe.
3. **Stair tower floated 0.35 off the block** - attachment formula now
   overlaps the block by 0.35.
4. **Frieze seam was asymmetric** - the fish zone leaked 3 cells left of the
   boundary; the seam now straddles it.
5. Probe calibration (not product defects): math-op census minima, the
   overhead-bin delta (single box per cell ~24 verts), and the parapet probe
   being masked by the taller roof plant box (isolate first, then measure).

## Pipeline (all on the final tree)

- `_melodia_preset_audit.py` -> **exit 0**: 157 builders with presets, 492
  presets, 0 shadowed, 0 orphans; packs MI_SALON_IMPOSSIBLE / MI_COUR_D_HONNEUR
  / MI_MAISON_NUIT all 5/5.
- Live addon sync: **293/293 byte match**.
- `Tools/verify_addon.py` gate: **PASS 6/6** (registry 599 -> 601; baseline
  re-cut, pre-cut preserved at `Saved/Audit/registry_baseline_pre_brutalist_20260923.json`).
- `Tools/melodia_studio_census.py`: **PASS**, 601 builders, 0 real errors.

## Staging deliverable

`Saved/Blend/MELODIA_GN_SHOWCASE_2026-09-23.blend` (staged by
`deploy/_melodia_stage_gn_showcase.py`):

```
MELODIA_GN_SHOWCASE
  01_MAISON_IMPOSSIBLE
    MI_EscherLadder, MI_FountainLoop, MI_DayNightFacade,
    MI_Mansard, MI_PenroseArch, MI_MetamorphosisFrieze
  02_BRUTALIST
    BR_OfficeBlock, BR_CubicleFarm
```

Every object carries a LIVE geometry-nodes modifier (dials stay editable in
the file); presets applied: facade MI_CREPUSCULE, arch MI_ARCH_TRIBAR, frieze
MI_MORPH_SEAM, office BR_OFFICE_CIVIC, cubicle BR_CUBICLE_CANON. Reopen-verified:
11 collections, 8 builder objects each in its own collection, trees live
(office nodes=254/params=25, cubicle nodes=321).

Companion outputs: `Saved/Audit/gn_showcase_manifest.json`,
`Saved/Audit/gn_showcase_overview.png`, and per-builder previews in
`Saved/Audit/paris_trackA_previews/` (fountain, facade x3, mansard, arch,
frieze, office x3, cubicle x3) - all vision-checked.

## Not done / open

- Track A remaining: **MobiusBalcony, HyperbolicRose**.
- Brand-pack apply operator: still needs a live Blender session to validate.
- Work is uncommitted on purpose (git pipeline law: no commits without
  explicit owner permission).
