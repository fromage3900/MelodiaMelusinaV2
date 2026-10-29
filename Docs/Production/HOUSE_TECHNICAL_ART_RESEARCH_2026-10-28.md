# Game-Ready Procedural Houses — Research Brief (2026-10-28)

How working technical artists ship houses, mapped against `melodia::house`.
Standard first, our state second, gaps as build orders. No new framework.

## 1. The canon stack (what AAA procedural houses all do)

**Modular kit + trim sheet, not bespoke meshes.** Walls/floors/trims share one
material family; variation comes from mesh composition + vertex data, never from
unique textures per room. Our 9-role contract IS this — keep it.

**Two UV channels.** UV0 = tiled material UVs (worldscale, box-projected per
surface is standard for architecture). UV1 = non-overlapping lightmap UVs in
0-1 (UE auto-generates these on import when asked, but authored UV1 beats
auto-unwrap on thin trim/beads). We ship UV0 only (dominant-axis, metre-scale
— correct convention). Gap: no authored UV1; UE auto-generate is the current
answer. Verify on import whether thin trim bleeds; if it does, author UV1.

**Collision in three tiers.** (a) Walkable: simple boxes/slabs
(`collision_geo_*` groups → UCX-style BodySetup, cheapest, what Pawns touch).
(b) Blocker: invisible low-poly hull for walls/props the eye sees but feet
never reach. (c) Complex-as-simple only for hero closeups. Our rooms carry (a)
for floors via `simple_floor_collision`; the HOUSE HDA currently emits arch
with NO collision output — the single biggest runtime gap. Next: emit a
`collision_geo_house` group (floor slabs + stair treads + joint plates as
boxes; walls as a low hull), and prove a capsule sweep in-editor.

**LOD/Nanite discipline.** Opaque rigid architecture: Nanite where tri counts
justify it, else 2LOD (hero + proxy) via screen-size culling — never raw
subdivided fillets at distance. Our bead strings + archivolts are the densest
geometry; measure their screen share in the Salon proof view before optimizing.

**Dressing as data, not geometry.** Scatter points carry (surface, room,
material) and the SET lives in a catalogue keyed by room; physics settles
contact. This is exactly our PCG branch + Codex catalogue split. Keep it.

**Doors as sockets, rooms as sockets.** UE socket workflows (door pivots,
snap points, VFX mounts) want named socket frames on the cooked mesh. Our
frames are JSON only. Verify the installed plugin's socket attribute name
against `Plugins/HoudiniEngine/Source/*/Houdini*.h` (grep `socket`, case-insensitive)
BEFORE building — the team has asserted `mesh_socketX_*` twice without a
citation. If supported, emit them from `rep['sockets']`; if not, keep JSON +
document the miss.

## 2. Our state against the canon

| Canon item | House status |
|---|---|
| Trim-sheet role contract | DONE (9 roles, fail-closed, zero unmapped) |
| Tiled UV0 | DONE (dominant-axis, metre-scale, verified finite) |
| Authored UV1 | OPEN (UE auto-generate assumed) |
| Walkable collision output | OPEN (rooms have slabs; house emits none) |
| Nanite/LOD budget | OPEN (unmeasured) |
| PCG scatter w/ tags | DONE (1,310 pts, 5 surfaces, ch() densities) |
| Room-keyed hero catalogue | DONE by Codex lane (needs DA + build + kit BP) |
| Socket frames on mesh | OPEN (JSON only, plugin support unverified) |
| Artist parms w/ ranges + help | DONE (2.0-vocabulary folders/menus/rows) |
| Drive/restore proof | RUNNING (SalonLive receipt pending) |

## 3. Build orders (in priority)

1. **Collision output + in-editor capsule sweep.** Highest gameplay value; gates P1.
2. **UV1 decision.** Import Salon, enable GenerateLightmapUV, capture closeups of trim/beads; author UV1 only if it bleeds.
3. **Socket verification.** One grep + one test cook. Either real sockets or a documented miss.
4. **Nanite/proxy pass.** Measure first (stat unit + tri counts at Salon proof view), then PolyReduce proxies for bead/archivolt systems only if they dominate.
5. **Corridor + roof rebuild specs** (existing queue) in the assembler vocabulary.
