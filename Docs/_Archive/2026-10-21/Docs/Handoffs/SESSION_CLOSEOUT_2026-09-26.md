# SESSION CLOSEOUT — 2026-09-26

**This is a session record, not project status.** `CURRENT_STATE.md` remains the
only authority on what is proven or open. This file records what happened in one
Blender/Geometry-Nodes session and what a next session should know before
touching the same files.

---

## 1. What was worked on

Melusina's magical-surreal regalia, in `Saved/Audit/regalia/`, plus a house
Geometry-Nodes toolkit audit and one real bug fix in the house toolkit.

**Completed and staged (4 of 9 pieces):**

| piece | gate | verts | size (m) |
|---|---|---|---|
| Circlet | `PASS_BAROQUE 22/22` | 37,186 | 0.5114 × 0.5120 × 0.0963 |
| Tiara (5-spire fan) | `PASS_BAROQUE 22/22` | 38,598 | 0.2849 × 0.2853 × 0.1412 |
| Earrings | `PASS_EARRING 10/10` | 4,544 | 0.2938 × 0.0126 × 0.1051 |
| Necklace | `PASS_NECKLACE 11/11` | 8,716 | 0.1877 × 0.1922 × 0.1319 |

**Not started:** brooch, hair pins, pauldrons, arm bands, waist chain.

**House toolkit:** 207 add-ons installed. `MESHmachine` and `MACHIN3tools` are
installed but disabled; enabling them works and registers **94 `machin3`
operators**. `CURVEmachine` is genuinely dead (`enable()` returns `None`).
Enabling MESHmachine **segfaults Blender at exit** — save before quitting.

---

## 2. The one real bug found and fixed

**File:** `deploy/surreal_arch/melodia_gn/mesh_tools.py`, function
`_wire_mesh_bevel`. Converged to the installed addon, SHA-verified identical.

Blender 5.2's `GeometryNodeMeshBevel` has four sockets the house never wired or
reset, all defaulting to **0.1**:

```
Start Left Offset   Start Right Offset   End Left Offset   End Right Offset
```

Each expresses how much of an edge the bevel may consume. They are **not
cosmetic and are independent of `Offset`.** Measured on the baroque circlet
(6,252 v / 6,189 faces, after a 1.6 mm thicken):

```
four offsets at their 0.1 defaults  ->  590,664 v, 1267.9 × 1093.7 × 548.4 mm
four offsets set to 0.0             ->   37,186 v,  511.4 ×  512.0 ×  96.3 mm
```

Width made no difference across 0.0002/0.0004/0.0006/0.001, which is what makes
it read as a broken link rather than a default. Because `_wire_mesh_bevel` is the
shared path, this also fixes `build_weighted_bevel`, `build_multi_bevel` and
`build_curvature_bevel`.

**This is the only tracked source change from the session.**

---

## 3. What I learned

### Tooling

- **`mesh_tools.py` is a full house finish suite in pure Geometry Nodes** —
  auto/weighted/curvature/multi bevel, profile, inset, poke, subdivision, remesh,
  laplacian. FBX-safe, no MESHmachine needed. It was there the whole time; I
  hand-rolled node graphs before finding it.
- `build_auto_bevel`'s own docstring says *"Mirrors Infinity Nikki soft bevel
  look."* That is the house's stated target, not mine.
- Verify a bevel actually worked with a unit cube: **8 v / 6 f → 96 v / 98 f** at
  Width 0.02, Segments 3, Profile 0.5, Angle Threshold 30.
- **Thicken first, then bevel.** Once `build_shell_thicken` seals every face
  there are no raw edges left, so the bevel becomes a no-op (`Offset=0` and
  `Offset=0.0006` both give 37,186 v). Bevel earns its keep on open-edged
  pieces. `regalia_finish.build_thicken_only` exists for closed curved surfaces.
- **Isolate stages by rewiring the group output.** Two-stage blow-ups look
  identical from the outside; the link dump is what finds them.

### House builders, measured

Ornament/filigree builders are **architectural scale and good shapes** —
rescale, never rebuild:

```
build_ornament_rosette_sixpetal  x0.040  ->  100.0 × 86.6 × 32.0 mm  brooch flower
build_ornament_scallop_band      x0.040  ->  154.9 × 10.8 ×  1.6 mm  brooch band
build_ornament_keyhole_frame     x0.030  ->   25.2 × 40.2 ×  1.2 mm  brooch frame
build_filigree_wreath_ring       x0.090  ->   86.4 × 86.4 ×  6.5 mm  circlet band
build_filigree_finial_cross      x0.020  ->   48.0 × 54.0 × 40.0 mm  tiara spire
build_decorative_rosette         x0.035  ->   86.1 × 86.1 × 21.0 mm  hair-pin rose
```

Dangle builders blow up in **one axis only** — `build_star_dangl` 54 × 57 ×
**1003** mm, `build_lace_dangl` 60 × 80 × **1005** mm. Same family as
`build_tassel_dangl` at 1.67 m. Fix is a Z-only transform, pending.

Usable at default, correct jewellery scale: `build_star_charm` (148 v, 57 mm),
`build_heart_dangl`, `build_bow_dangl`, `build_pearl_dangl`,
`build_flower_pendant`. `build_crystal_chain` is 234 × 231 × 225 mm at 96 v —
a clean low-poly band, possibly a better circlet base than the hand-built egg
band.

### Corrections to earlier claims in this session

- **`build_crystal_drop` is not broken.** Measured default: 24.0 × 20.8 ×
  90.0 mm, 1036 v — a proper long earring. I had passed `Crystal Length=0.153`
  where ~0.015 was right. The earring and necklace stones were flat because of my
  parameters, not the builder. **The stones on both pieces still need redoing.**
- **"MACHIN3tools and MESHmachine FAIL TO REGISTER under 5.2"** in
  `BOAT_MASTER_PLAN_v09.md` is **stale**. They were patched (see
  `MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`) and now enable cleanly.

### Traps that cost real time

- A **Curve Arc generates in the XY plane; she faces −Y.** Her front is 270°,
  not 0°. A gap meant for her throat was landing on her shoulder.
- **Use a house builder's RETURN VALUE, never a name lookup.**
  `build_star_finial("X")` returned a tree it never registered under `X`, so
  `bpy.data.node_groups.get("X")` was `None`, `node_tree` was `None`, `outputs`
  was `[]`, and every `outputs["Geometry"]` raised `KeyError`.
- **A node can be built and orphaned with every gate still green.** The link dump
  showed `Transform Geometry.007`–`.012` with `out=[]` while the tiara measured
  *unchanged* at 6450 v and six star trees sat unused. No size/seating/material
  gate can see this. **Dump `from_node → to_node` for everything you create
  whenever a measurement refuses to move.**
- **Two ways a list silently loses everything appended to it:**
  `parts = [_transform(..., parts[0], ...)]` rebuilds the list with one element
  (assign `parts[0] = ...`); and appending to `parts` *before* the branches that
  fill a sibling list orphans every later part. Append **last**.
- `to_mesh()` returns **local** space — object scale appears to do nothing.
  Measure with `matrix_world @ v.co` or the numbers lie.
- `_dial(tree, name, default, lo, hi, loc)` — the name comes **second**.
- Import the house **package**: `from surreal_arch.melodia_gn import ...` with
  the *addons* dir on `sys.path`. Importing `melodia_gn` directly raises
  "attempted relative import beyond top-level package" (`stack.py` does
  `from ..branding import N_PANEL_CATEGORY`).

---

## 4. What remains, in order

1. **Re-sweep the dangl family on Z only** — recover `build_star_dangl`,
   `build_lace_dangl`, `build_bow_dangl` for hair pins and dangly earrings.
2. **Redo the crystal stones** with `Crystal Length` ≈ 0.012–0.02, not 0.153.
   The stones are on *every* piece, so this is the highest-leverage fix left.
3. **Clean the necklace** — cord and drop weld awkwardly; the cord shell reads
   as a stray 128 v island. MeshCleanerPro on the realized mesh.
4. **Build the remaining five** (brooch, hair pins, pauldrons, arm bands, waist
   chain) with the rescaled ornament builders and the thicken+bevel finish
   applied as authored, not retrofitted.
5. **Enable MESHmachine / MACHIN3tools** for boolean union and stash — the
   things GN cannot do. Verified working; expect the exit segfault.
6. **Re-measure the earring stones** once step 2 lands, then get eyes on them.
   The "flat disc" problem was invisible to both the gates and one vision read.

---

## 5. Blockers and cautions

- **Nothing is committed.** All regalia work is in `Saved/`, which
  `.gitignore:5` excludes. The only committable artefact from this session is
  `mesh_tools.py`.
- **No live save.** The Blender session is an unsaved factory scene, 21 objects,
  `Regalia_Baroque` collection. It is **not** the harp WIP and nothing was
  written into it. The harp (2,392 MB) was untouched throughout.
- **No independent sheep backup exists.** S3c / bighorn / crown / decor
  generations are separate and must be preserved individually.
- **Nested crystal materials still do not propagate reliably** to object slots in
  the live assembly. Proof renderers currently assign materials by connected
  shell after realization. The tiara stone rendered lavender live despite
  `Aquamarine Dream` being authored.
- **Technical PASS ≠ well-made object.** `PASS_BAROQUE 22/22` passed on flat
  zero-thickness wire. Cleaner geometry needs its own receipt: thickness in mm,
  chamfer present, non-manifold count zero, close-up render.
- **Separate UE/P0 lane, untouched this session.** The owner's note referenced
  `.hermes/plans/2026-09-26_p0-loop-sir-pcg-review-goal.md` (PR #337), Perforce
  change 230, the unsubmitted Morning edits in the default changelist, the three
  unmerged foundry files, G1–G4, and two open decisions (D1 authored Perch spots
  vs any walkable surface; D2 which map is the P0 dungeon). **None of it was
  touched.** Ollama restart also not done.

---

## 6. Artefacts

All in `Saved/Audit/regalia/` (gitignored):

```
BAROQUE_REBUILD_2026-09-25.md      479 lines — circlet, tiara, fan, finish stage
NIKKI_ORNAMENT_REVIEW_2026-09-26.md   measured sweep of 18 ornament builders
TOOLCHAIN_AUDIT_2026-09-26.md      add-on state, Mesh Machine finding
MELUSINA_REGALIA_PLAN_2026-09-25.md  the nine-piece plan
CIRCLET_AUDIT_2026-09-25.md         why the flat graph was rejected

regalia_baroque_build.py            circlet + tiara, now with the finish stage
regalia_earring_build.py            earrings
regalia_necklace_build.py           necklace
regalia_finish.py                   NEW — shared thicken + bevel stage
regalia_stone.py                    magical-surreal gem materials

baroque/, earring/, necklace/      proof renders
```

Skills updated: `melodia-gn-builder-workflow` (bevel-socket bug, finish-suite
discovery, house-builder scale traps, orphan-node detection, list-accumulation
traps).
