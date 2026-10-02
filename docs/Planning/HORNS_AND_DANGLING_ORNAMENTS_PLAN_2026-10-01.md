# Horns + Dangling Ornaments — plan (rev 3, 2026-10-01 late session)

**Status: rev 4 — the whole polish queue is implemented, gated, and APPLIED LIVE.**
v1 (0 renderable verts) → v2 (pearl-first row, 13/13) → v3 (spine + hang solve) →
**v4 (row with terminus menu, materials, chain, jitter, music; snapper with
even-spacing + tip drop)**. Supersedes rev 2/3 (rev 2 backup:
scratch `dangler_v2/backup/HORNS_PLAN_rev2_backup.md`).

Applied live this pass (in-memory; **the owner saves** — nothing was written to disk):

| Live object | Result |
|---|---|
| `SheepHornSpine` | 14 stations/horn, evenly spaced by arc length; tip 34/35 stations dropped |
| `SheepHornDanglers` | **35,184 verts** = 24 × (1,322 pearl + 2×72 chain rings); mats `[ME_Sheep_Gold]` |
| `SheepHorns` | **8,664 verts, untouched**, now carrying `ME_Sheep_Horn` (ivory) in slot 0 |
| `MEL_horn_dangler_row` | v4: 61 nodes / 81 links (proof **19/19**) |
| `MEL_horn_dangle_terminus` | 21 nodes / 26 links, per-part material sockets present |

Proof: `Tools/wardrobe_pipeline/horn_dangl_proof.py` → **19/19** gates
(G9 terminus menu, G10 smooth, G11 chain, G12 variation/seed, G13 material,
G14 music passthrough, G15 chain length from the baked `radius`).

Evidence levels: **proven** = measured, number recorded · **source** = builds, not yet rendered
in place · **scaffold** = named, not built · **LIVE** = currently in the open .blend.

Companions: [`GN_BUILDER_AUDIT_2026-10-01.md`](GN_BUILDER_AUDIT_2026-10-01.md),
[`PHYLLOTAXIS_SPIRAL_PLAN_2026-10-01.md`](PHYLLOTAXIS_SPIRAL_PLAN_2026-10-01.md),
[`BIGHORN_LIVE_VERIFICATION_2026-10-01.md`](BIGHORN_LIVE_VERIFICATION_2026-10-01.md).

---

## 1. Where it stands (all numbers measured)

| Item | State | Evidence |
|---|---|---|
| `MEL_horn_dangler_row` (repo) | **proven** | `horn_dangl_proof.py` **13/13**; 17 nodes / 19 links; Count×terminus exact (9→11,898 = 9×1,322) |
| `MEL_horn_dangle_terminus` (house pearl) | **proven** | 1,322 v, 33 mm; reused from `cute_decor.build_pearl_dangl` |
| Spine snapper `horn_spine_snap.py` | **proven** | chord-midpoint snap; inside **1.0** pre/post both horns; 121 stations/horn; local tube radius 32→19.5 mm |
| Hang solve (per-station drop) | **proven** | coil span: sphere clearance **9–17 mm**, loop gap **3–6 mm**; tip stations ~86–120 tight: **2–6 mm** (below the 8 mm bar, not intersecting) |
| End-to-end copy build | **proven** | 20 pearls (10/horn), **26,440 v** = 20×1,322; renders in `Saved/Audit/choral_sheep/dangler_v2_20261001/` |
| Look (vision on the built render) | **proven** | *"they HANG … a thin loop connects the cap to the horn, and the sphere hangs down … not embedded"*; symmetric on both horns |
| `SheepHornDanglers` | **LIVE** | 15,864 v = 12×1,322; wrapper group `SheepHornDanglers`; dials 12 / 0 / 0.03 / 2.0 |
| `SheepHorns` | **LIVE, untouched** | 8,664 v; `MEL_S5_horns`; **no material slot** |
| Materials on the ornament set | **gap** | LIVE read: `SheepHorns`, `SheepHornDanglers`, `SheepMusicBeads`, `SheepPearlDanglers`, `PearlDangl_0/1/2` all read **`mats: []`** |

## 2. Traps paid for in time — read before touching this lane

1. **A legacy Curve datablock has no `attributes` API in 5.2** — `curve.attributes.new(...)` raises
   `AttributeError: 'Curve' object has no attribute 'attributes'`. A direction vector **cannot** ride
   along a curve. Per-point values must be **baked into the point positions** (or the point `radius`,
   which does work).
2. **A −Z drop from a coil's outer rim slides along the tube cross-section.** On a helix the
   cross-section plane contains the coil axis, so "down" from the rim walks *around the tube* and the
   pearl grazes it instead of hanging clear. The anchor must be a **solved** per-station point.
3. **`Curve to Points`' `Normal` twists around a helix** — a large radial offset along it buried
   pearls (vertex-inside fractions up to 0.92 measured). Never use it for the row's push on coil
   hosts; the snapper supplies a baked locus instead.
4. **Ray-parity is not a containment test on an open swept tube** — it reads a confident 1.0 on the
   spine's deep-centre points and garbage near the surface; a normal-signed test failed the same way.
   Use **distance sampling of the pearl sphere** (the hang solve) as the acceptance measure.
5. **`Curve to Points` Count is PER SPLINE** — Count=12 on a 2-spline host gives 24 instances
   (11,568 v measured). Budget `Count × splines`.
6. **`Curve to Points` mode is a menu that defaults to Evaluated and ignores Length** until the mode
   is explicitly set (polish P3 depends on this).
7. **A bare Points cloud is invisible** — no faces, renders nothing, reads **0 through `to_mesh()`**.
   "0 verts" was invisibility, not absence. Always measure after Realize Instances.
8. **Cross-domain links evaluate EMPTY without error** — `Mesh Line.Mesh → Vector Math.Vector`,
   `Vector Math.Vector → Mesh to Curve.Mesh`: accepted, no `link_failures()` entry, evaluates to
   nothing. This is what zeroed v1.
9. **An unlinked Geometry input is a silent no-op, not an error** — v1's live row node was fully
   unlinked and looked healthy.
10. **`GeometryNodeInputNormal` is empty on curve points** — its offset silently no-ops. Use
    `CurveToPoints`' own `Normal` output.

## 3. Architecture (what the row is fed)

```
SheepHorns (mesh, 8,664 v)
  └─ horn_spine_snap.py        chord-midpoint centreline extraction (inside 1.0)
       ├─ per-station local tube radius (BVH ray-pair, 32→19.5 mm)
       ├─ outward direction per station (radial from the horn's own axis)
       └─ hang solve: per-station drop that clears the pearl sphere (≥8 mm bar;
          actual drop 0.040–0.045 on the coil, up to 0.135 near the tip)
  └─ SheepHornSpine (2-spline poly curve = BAKED PEARL ANCHORS)
       └─ MEL_horn_dangler_row      Count x terminus, per spline
            └─ Instance pearl terminus (scale = Terminal Size)
                 └─ Realize -> SheepHornDanglers
```

The row stays generic (Count / Host Offset / Hang Drop / Terminal Size); **for the horns, Host Offset
and Hang Drop stay 0** because the anchors are pre-solved. Re-run the snapper after any change to
Terminal Size (the solve assumes pearl radius 24 mm = scale 2).

## 4. Polish queue (in order)

- **P1 — Materials. The largest visual gap.** LIVE read: horns *and* every dangler object have empty
  slots, while the house gold `ME_Sheep_Gold` already exists (3 users; collar v4 uses
  `ME_Sheep_Gold.002`).
  - P1a: add a **Material socket** to the row (a `Set Material` node on the terminus branch),
    default `ME_Sheep_Gold` → pearls come out gold with no wiring.
  - P1b: give **`SheepHorns` a horn material** (ivory/bone). Today the horns render flat clay grey —
    this is why the test renders read "unfinished". Object slot or `MEL_S5_horns` SetMaterial change;
    owner's call on the datablock.
  - P1c: a loop/cap metal distinct from the pearl (second socket, or one material + contrast).
- **P2 — Tip-region clearance.** Stations ~86–120 (thin curled tip) sit at 2–6 mm — "resting", not
  intersecting. (a) stop the baked spine ~15 stations short so the row never places a pearl there
  (cheapest, keeps the look) — recommended; (b) allow a longer tip drop in the solve.
- **P3 — Spacing rhythm.** Count mode spaces by parameter, so spacing varies with the coil's
  curvature — the "bunching" the vision noticed. Bake the anchors as *evenly spaced* solved stations
  (the snapper already owns the station list) — fixes P2 for free. Recommended.
- **P4 — Pearl read.** The pearls read visibly faceted against the smooth horns. Deliberate style
  (keep) or add a smooth/subdivision pass at the terminus. Owner's taste call.
- **P5 — Chain second pass** (deferred from v1). Build as a sub-branch off the same host points:
  c2m the segment between anchor and loop top. Only after P1–P3 settle.

## 5. Expansion queue (the "xpansion" ask)

| # | Expansion | Reuses | State |
|---|---|---|---|
| E1 | **Terminus variants** — star / lace / bead-tassel danglers | `cute_decor.build_star_dangl` / `build_lace_dangl` / `build_bead_tassel`; add a Terminus enum dial to the row | source |
| E2 | **Blossom rows on the horn base** | `MEL_phyllotaxis_spiral` / `_pave` (proof 18/18) | proven builders |
| E3 | **Neck / collar dangler row** — same row, new host curve | the row + `SheepWreathCollar_v4` (LIVE, has material) | source |
| E4 | **Tail row** — danglers off the tail scroll | the row + `SheepTailScroll` (LIVE, gold) | source |
| E5 | **Herd variation** — a Seed dial so each sheep's row differs | row + per-object seed | scaffold |
| E6 | **Music-reactive ornament** — the house music sockets are already on the row interface (`Music Influence`, `Musical Amplitude`, `Musical Freq A/B`) | the row's existing interface | scaffold |

E1 and E5 are the best value-per-effort; E2 reuses builders already proven.

## 6. LIVE ornament inventory (read this pass, read-only)

| Object | Verts | Modifier → group | Material |
|---|---|---|---|
| `SheepHorns` | 8,664 | `S5_Horns` → `MEL_S5_horns` | — |
| `SheepHornDanglers` | 15,864 | `Danglers` → `SheepHornDanglers` (wrapper) | — |
| `SheepMusicBeads` | 3,100 | `S5_MusicBeads` → `MEL_S5_music_beads` | — |
| `SheepPearlDanglers` | 3,420 | `S5_Pearls` → `MEL_S5_pearl_string` | — |
| `PearlDangl_0/1/2` | 1,322 ea | `MEL_sheep_pearl_dangl` | — |
| `SheepWreathCollar_v4` | 4,088 | filigree wreath ring | `ME_Sheep_Gold.002` |
| `SheepTailScroll` | 576 | filigree spiral | `ME_Sheep_Gold` |
| `SheepEarBead_L/R` | 86 ea | S5 bead dial | `ME_Sheep_Gold` |
| `MrSheepFinalTHISONELOOK` | 1,000 | S5 body stack | Coat / Skin / Hoof |

Live file: `choral_sheep_A_blossoms_FIXED_20261001.blend` (**dirty — owner saves**).

## 7. Next actions

Done this pass (all verified, live applied but unsaved): P1a, P1b, P2, P3, P4,
P5, E1, E5, E6. Remaining queue, in order:

1. **P1c full split** — the pearl terminus exposes `Pearl Material` / `Trim
   Material` and does the per-part split; the row deliberately stays in SINGLE
   material mode until the star/lace/bead builders carry the same two sockets
   (`all(...)` in `horn_dangl.py` §5 flips it automatically).
2. **E2** blossom ring at the horn base (phyllotaxis builders are proven 18/18).
3. **E3** collar dangler row (host curve fitted to `SheepWreathCollar_v4`).
4. **E4** tail dangler row (host curve fitted to `SheepTailScroll`).
5. **Tuning with the owner's eye** — Count vs the 14 baked stations, Terminal
   Size, Variation/Seed, and whether the chain reads at 2 links.

Owner to note: the pearls span the coil from the base up to where the tip
clearance fails (34 of 121 stations dropped per horn); a 3/4 view can read the
lower run as bunched because the coil's outer curve is nearest the camera.

## 8. Tool / file inventory

- `deploy/surreal_arch/melodia_gn/horn_dangl.py` — the row (synced byte-identical to the AppData copy)
- `deploy/surreal_arch/melodia_gn/cute_decor.py` — `build_pearl_dangl` + the other terminus builders
- `Tools/wardrobe_pipeline/horn_spine_snap.py` — centreline snap + hang solve → `SheepHornSpine`
- `Tools/wardrobe_pipeline/horn_dangl_proof.py` — 13 gates → `horn_dangl_proof_result.json`
- `Tools/wardrobe_pipeline/phyllotaxis_proof.py` — 18 gates (G6g = the row emits geometry)
- scratch `dangler_v2/`: `copy_wire_render.py` (end-to-end copy build + renders),
  `live_state_snapshot.py` (read-only live read), `mcp_exec.py` (live socket runner),
  `study_scene.py`, `fit_study*.py`, `rewire_live_v2.py`

```
blender --background --factory-startup --python Tools/wardrobe_pipeline/horn_dangl_proof.py
blender --background --factory-startup fit_study_base.blend --python copy_wire_render.py
python mcp_exec.py live_state_snapshot.py
```

## 9. Standing rules carried forward (still binding)

- **Seating: measure, never iterate.** Evaluate the world bbox first; if it is right, touch nothing.
  One closed-form solve max (`world = parent_t + loc + local_centre`). The crown precedent (four
  destroyed re-seats) applies; opaque ≠ broken.
- **Per-object variation = per-object tree copies.** NODES modifier idprops are dead in 5.2.1 and
  interface edits do not propagate to existing consumers — write group-node inputs directly, or copy
  the tree (`Sheep_Bloom_A/B/C` pattern; keep weight sums 1.0).
- **Two nudge→verify passes max**, then ship a number + ONE render + one question.
- **Builder/tool sync:** repo copy + byte-identical AppData copy (`cp` then `cmp`); builder code
  carries the defaults, the .blend carries the tuning.
- **Live is read-only unless the owner GOes it.** One live write per authorization; owner saves.

## 10. Out of scope

Wool/fleece (separate lane — the capstone blocker), closed-editor build, UE import,
Substance/UVB bake, rig/mocap work.
