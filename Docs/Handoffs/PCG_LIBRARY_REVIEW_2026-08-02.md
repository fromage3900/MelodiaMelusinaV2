# PCG library — full review, 2026-08-02

138 graphs audited programmatically against the failure modes found this session.

## The headline: the meshes are the problem, not the graphs

**67 of 138 graphs (49%) spawn at least one mesh authored at ~1/100 scale.** That is the single
largest defect in the library, and it is *not* a PCG problem at all — it is the Blender-metres →
UE-centimetres import convention.

The good news is how concentrated it is. **29 distinct meshes** account for all 67 graphs, and the
top five account for 39 of them:

| Mesh | Graphs | Actual size (uu) |
|---|---:|---|
| `SM_Block_Cube_1` | 11 | 1 × 1 × 1 |
| `SM_Greybox_Cube_1m` | 10 | 1 × 1 × 1 |
| `SM_Cube_001` | 6 | 1 × 1 × 1 |
| `SM_Greybox_Wall_4x3` | 6 | 4 × 0 × 3 |
| `SM_Greybox_Column_05` | 6 | 0 × 0 × 3 |

`SM_Greybox_Cube_1m` is the proof: the name says one metre, so it should be 100 uu. It is 1.

**A single Build Scale = 100 pass over 29 assets would repair roughly half the library.** That is by
far the highest-leverage action available, and it is *not* done here — changing mesh scale has real
blast radius: any existing hand-placed actor compensating with a ×100 scale would suddenly become
enormous. That check has to happen first, and the call is the owner's.

## Emission health

| Category | Graphs | Meaning |
|---|---:|---|
| generator (works) | 27 | `CreatePoints` / `CreatePointsGrid` — proven to emit |
| sampler + generator | 45 | partially works; the sampler branch contributes nothing |
| **VolumeSampler only** | **40** | **emits zero, project-wide** |
| no spawner | 17 | subgraphs and utilities — expected |
| no source node | 9 | cannot emit; structurally incomplete |

**29% of the library cannot emit at all** because `PCGVolumeSampler` produces nothing here,
regardless of volume size (tested to 5400 uu). Diagnosing that one node would unlock 40 graphs — the
second-highest-leverage item after the mesh scale fix.

## The silent one: coordinate_space

`PCGCreatePointsGrid.coordinate_space` defaults to **WORLD**, which generates at the world origin and
ignores the owning volume. It fails *silently* — the count looks perfectly healthy.

Five graphs still carry it. Three otherwise work and are therefore actively mis-placing:

- `EnvSandbox/PCG/Styles/Grotto/PCG_Grotto_Scatter`
- `EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_DreamStones`
- `EnvSandbox/PCG/Styles/WP/PCG_WP_HumanScaleCorridor` (2 grid nodes)

Also found: **8 graphs have a StaticMeshSpawner with no meshes assigned** — they run and produce
nothing visible.

## Hero graph #2 — `PCG_Hero_PenroseTiling`

A mathematically exact **P3 Penrose aperiodic tiling**, not a decorative approximation.

Built by Robinson-triangle deflation (5 generations from a 10-triangle wheel), extracting the rhomb
edge set, then baking the result into `PCGCreatePoints.points_to_create` as explicit point
transforms. Self-contained: the graph regenerates deterministically with no external dependency.

| | |
|---|---|
| Edges | **780**, every one **631.40 uu** — uniform, as a P3 tiling requires |
| Vertices | 416 (`SM_Greybox_Gem` / `SM_Greybox_GreatDodecahedron`, 208 each) |
| Edge directions | **5, at exactly 18° / 54° / 90° / 126° / 162°** |
| Patch | 6500 uu radius (130 m across), 1196 instances |

The 5-fold direction signature is the correctness proof, and it was **re-measured on the spawned
instances in-engine**, not just in the generator — engine yaws came back `[18, 54, 90, 126, 162]`.

### Two things that made this work

- **The rhomb side is the middle of three lengths.** Deflation yields sides in golden progression
  L, Lφ, Lφ²; the short and long values are the thin- and thick-rhomb *diagonals*. Filtering on the
  middle length is what produces a uniform edge set — filtering wrongly gave 8 distinct lengths and
  15 directions, which is how the first two attempts failed.
- **An edge lattice suits instancing; rhomb faces do not.** All Penrose edges are equal length, so
  one beam mesh with position + yaw covers the whole tiling. Rhomb *faces* would need shear, which a
  point transform cannot express.

Saved in `L_FallenMoon` as `PCG_Hero_PenroseTiling`. Level total is now 1898 instances.

## Recommended order

1. **Audit then fix the 29 broken meshes** (Build Scale 100). Repairs ~half the library. Check for
   compensating ×100 placements first. **Owner's call — not done here.**
2. **Diagnose `PCGVolumeSampler`.** Unlocks 40 graphs.
3. **Fix the 3 WORLD-space graphs** — a one-property change each.
4. **Fill or retire the 8 empty spawners.**
5. Retire the 9 source-less graphs into `_Deprecated`.

Steps 3–5 are small and safe. Step 1 is the big win and the one that needs a human decision.
