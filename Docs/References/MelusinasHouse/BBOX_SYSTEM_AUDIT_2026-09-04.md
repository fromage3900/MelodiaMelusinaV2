# BBOX SYSTEM AUDIT + FIX PLAN — 2026-09-04 (night)

**Trigger:** owner suspicion "I do not believe the bounding box systems work."
**Method:** headless probes against Blender 5.2.1 (Tools/bbox_system_audit.py,
bbox_system_audit2.py). Every claim below is measured, not inferred.

## Measured findings

| # | Finding | Verdict |
|---|---|---|
| 1 | `GeometryNodeBoundBox` Min/Max/Bounding Box correct on real meshes (cube at +5x → bbox x[4,6] exact) | **works** |
| 2 | `BoundBox` **ignores unrealized instances**. join(cube, 3 instances spanning x=0..20) → bbox reads only the solid cube (x −0.5..0.5) | **real defect, engine-level behavior** |
| 3 | Monolith `add_auto_align_pass` (GROUND/CENTER, line 11461) runs bbox on the FINAL composed geometry — which for instance-based pieces contains unrealized instances. 64 `InstanceOnPoints` sites exist in the monolith. GROUND alignment therefore silently mis-aligns every instance-based piece (fences, railings, towers, radial arrays) | **confirmed system defect** |
| 4 | GROUND z-snap math itself is exact for solid meshes (zmin → 0.0) | works |
| 5 | Empty-geometry bbox returns degenerate box at origin (Min=Max=0), silently wrong downstream | guarded in mh6; latent elsewhere |
| 6 | mh6 fixed shell: bbox sane, grounded; cornice caps the wall at top edge (by design, top-100 z ≈ 3.45 vs Height 3.42) | OK |
| 7 | Package builders: ~30 modules emit instances; 88 RealizeInstances sites exist but are not systematically placed BEFORE bbox-consuming nodes | **audit needed per builder** |

Root cause of #2 is Blender's documented GN behavior: BoundBox operates on the
geometry socket's LOCAL content; instance clouds are descriptors, not meshes.
Any bbox-driven feature (align, center, fit, scale-to-bounds, UV normalization,
cornice ride, cutter-grid sizing) must run AFTER `RealizeInstances` — or the
instances must be counted via `Domain Size`/`Instance Rotate`-aware patterns.

## Fix plan (two layers)

### F1 — Engine-facing utility (the durable fix)
New package builder `MEL_realize_and_bounds` in
`melodia_gn/operations.py`:
```text
Geometry IN → Realize Instances → BoundBox → outputs:
  Geometry (realized), Min, Max, Size, Center, Instance Count
```
All bbox-consuming logic across the ecosystem switches to this node group.
It makes "bounds of what will actually render" impossible to get wrong,
because realizing is INSIDE the group — you cannot feed it instances without
getting correct bounds back.

### F2 — Call-site repairs (gated per site)
1. **Monolith generate pipeline** (one site, fixes 64 builders at once):
   in `apply_geometry_nodes_to_object`, insert `Realize Instances` before
   `add_auto_align_pass` and `add_procedural_uv_pass` when the builder
   emitted instances (detect via Domain Size > 0 → Switch, preserving
   pass-through for solid geometry so non-instance pieces keep their node
   graphs instance-native for UE Nanite-style workflows).
2. **Package audit sweep**: for each of the ~30 instance-emitting modules,
   check whether any bbox-consuming node sits upstream of a
   RealizeInstances. The verifier (P0 harness, absorption plan) gains a
   static check: no `GeometryNodeBoundBox` may receive a socket that traces
   back to `InstanceOnPoints` without an intervening `RealizeInstances` —
   grep + node-graph level, automated in `verify_full_registry.py`.
3. **UV pass** (line 11565): same realize-first gate — normalized UVs on
   instanced pieces currently normalize against the wrong box.

## Sequencing

- F1 + the monolith pipeline gate (F2.1) go into the FIRST absorption batch
  (P0/P1 window of ONE_ECOSYSTEM_ABSORPTION_PLAN) — they are exactly the
  kind of shared-infrastructure fix the single ecosystem exists to carry.
- F2.2 is folded into each family port: while porting a family's builders,
  every bbox consumer gets rewired to `MEL_realize_and_bounds` and the
  verifier's static check enforces it permanently.
- Add a regression case to the baseline harness: one instance-heavy piece
  (e.g. RAILING or FENCE), assert post-GROUND-align zmin == 0 and x-center
  == 0. This test FAILS on today's code and PASSES after F2.1 — it is the
  receipt.

## Ledger

| Gate | Status | Evidence |
|---|---|---|
| BBox probe audit | **DONE 2026-09-04** | Tools/bbox_system_audit*.py console logs |
| F1 MEL_realize_and_bounds builder | OPEN | — |
| F2.1 monolith pipeline realize-gate | OPEN | — |
| F2.2 per-family bbox rewire | OPEN | rides P2 family ports |
| Instance-align regression case (red→green) | OPEN | — |
