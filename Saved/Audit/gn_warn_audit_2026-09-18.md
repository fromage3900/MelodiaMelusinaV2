# GN builder WARN audit — 2026-09-18

Read-only audit of the socket-link warnings emitted by the Melodia GN builder registry
under Blender 5.2.1 LTS (hash `9e2066aef7ef`). Complements `Tools/verify_addon.py`
(the pass/fail gate) by cataloguing the **latent defects the gate passes over**: every
warning below is a link that `link_sockets` / `link_float_to_vector`
(`deploy/surreal_arch/melodia_gn/core.py`) caught, logged, and then dropped. Trees still
produce geometry, so the gate stays green while the affected sub-effect is miswired.

## Evidence

| Artifact | What it is |
|---|---|
| `Saved/Audit/verify_addon_2026-09-18_post_sync.log` | gate vs live synced addon (A PASS, B `new=2`, C PASS, D `137>136`, E PASS, F PASS); 117 raw WARN lines |
| `Saved/Audit/verify_addon_2026-09-18_postconvergence.log` | re-run after baseline/RECORDED_EMPTIES convergence (A/B/C PASS, then a mid-gate-D exit); 53 WARN lines |
| `Saved/Audit/probe_mesh_line_2026-09-18.log` | live 5.2.1 Mesh Line socket probe (class C) |
| `deploy/_probe_mesh_line.py`, `deploy/_melodia_health_gn_builders.py` | probe + registry health scripts |

Raw WARN lines counted across the run: 117 (a builder is invoked in the gate-A build
phase and again in the gate-D eval phase, so each warning prints ~2–3×).
**Distinct (tree, class) pairs: 19 across 18 named trees.**

## Class A — None socket link (socket absent) — 10 trees, HIGHEST

`link_sockets: one or both sockets are None`. A socket arg resolved to `None`, so
`NodeLinks.new()` was never called — the link does not exist. On a Geometry input the
downstream sub-graph receives **no geometry** (silent no-op).

| Tree | Dropped sockets |
|---|---|
| `MEL_garment_vertex_ao` | Attribute / Value / Vector |
| `MEL_gb_corridor_arc` | Geometry (in) |
| `MEL_gb_corridor_arc_cross` | Geometry (in) |
| `MEL_gb_escher_gravity_shift` | Geometry (in) |
| `MEL_gb_escher_recursive_room` | Geometry (in) |
| `MEL_gb_escher_waterfall` | Geometry (in) |
| `MEL_gb_room_rotunda` | Geometry (in) |
| `MEL_legacy_cascading_beams` | Spacing / Thickness / Z Cascade / X Cascade / Twist |
| `MEL_legacy_lancet` | Width / Height / Point Rise |
| `MEL_musical_pulse_variant` | Vector (in) + one `None→None` |

Mechanism: the socket name changed in 5.2 (same family as `NODE_REMAP_52` node renames)
and the builder still asks for the old name — or passes a node where a socket is expected.

## Class B — scalar / ShaderNodeMath → Value mismatch — 7 trees, HIGH

`link_sockets: cannot link <?|Math.00x> → Value … expected a NodeSocket, not <float|ShaderNodeMath>`.
The caller passed a **node** (or a float) instead of a **socket**, so `NodeLinks.new()`
rejected argument 1 and no link formed.

| Tree | Offending link |
|---|---|
| `MEL_chime_field_scatter` | `? → Value` (float) |
| `MEL_harp_concert_real` | `? → Value` (float) |
| `MEL_harp_kora` | `? → Value` (float) |
| `MEL_harp_ur_lyre` | `? → Value` (float) |
| `MEL_musical_harmonic_variant` | `Math.002/004/006 → Value` |
| `MEL_roll_walkable` | `? → Value` (float) ×2 |
| `MEL_wind_siku` | `? → Value` (float) |

Same root cause as AGENTS.md rule 13 (node-vs-socket confusion); only the live link
attempt catches it.

## Class C — 'End Location' missing on Mesh Line (5.2 socket absence) — MEDIUM

`link_float_to_vector: 'End Location' input not found on node 'Mesh Line'` (also
`Mesh Line.001`). Live probe on this exact build:

```
GeometryNodeMeshLine inputs: ['Count', 'Resolution', 'Start Location', 'Offset']
mode: OFFSET
after OFFSET:     ['Count', 'Resolution', 'Start Location', 'Offset']
after END_POINTS: ['Count', 'Resolution', 'Start Location', 'Offset']
```

**No `End Location` input exists in either mode on 5.2.1.** The span end silently
no-ops. A *socket* absence that `NODE_REMAP_52` cannot cover (it remaps node ids).

## Class D — `link_float_to_vector` component link error — 1 site, LOW

`cannot link component 1` / `component 2` inside `link_float_to_vector`.

## Root cause

`core.link_sockets` / `core.link_float_to_vector` wrap `NodeLinks.new()` in a
`try/except` that logs `[WARN]` and continues. A dropped link is invisible to every gate
(gate A only checks the factory returns a tree; gate D only checks verts are produced).
This is the "silent no-op" defect class named in AGENTS.md.

## Prioritized fix list (audit only — no fix applied)

1. **P0 — make link failures loud.** In `core.py`, **raise** (or set a tree error flag the
   gate reads) when a socket is `None` or a node is passed where a socket is expected.
   One change turns all four classes into gate-A FAILs.
2. **P1 — Mesh Line span.** Use the probe's real socket list; if 5.2.1 has no
   `End Location`, drive the span with `Offset`/distance maths. Files: `chimes_gn.py`,
   `musical_mesh_variants.py`, any builder creating `GeometryNodeMeshLine`.
3. **P1 — Class A Geometry-in None.** Fix the 7 `gb_*` builders so their `Geometry` input
   is actually wired.
4. **P2 — Class B socket-vs-node.** Pass the socket, not the node, in the 7 trees above.
5. **P2 — legacy_* None sockets.** `legacy_cascading_beams` (5), `legacy_lancet` (3):
   fix names or retire.
6. **P3 — `garment_vertex_ao` (3)**, **`musical_pulse_variant` (2)**.

## Clean / not in scope

- **Gate F PASS (offenders=none)** — no `BoundBox` over an unrealized instance cloud.
- **Gate E PASS** — the 6 converged files are byte-identical repo↔live.
- No NaN-propagation scan added (`safe_math` FIX-4 remains a P2).

Owner review required before any fix lands (StairStep Oversight Agreement).
