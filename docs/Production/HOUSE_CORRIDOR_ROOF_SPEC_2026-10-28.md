# House Corridor + Roof Rebuild Spec (2026-10-28)

Follows the assembler vocabulary (roles, sockets, surfaces, bays). Pure-Python
first, HDA after. Salon-first plan exercises joints only; these cover runs.

## 1. Corridor runs (separated rooms)

Status: `link_corridor` builds single-sided quads (visible from inside only).
Exterior invisibility accepted v1 because SALON_FIRST snaps every joint
(dist = 0, joint mode). A two-room-apart plan would expose it.

Rebuild: closed slabs via `slab_quad` (already in house.py, used by nothing
yet — wire it in): floor slab (top = surface_floor), ceiling slab (underside
= surface_ceiling), two wall slabs (inner = surface_wall, outer = structure
via `_faces_room` against the run midpoint). Ends stay open. Reuse the
existing width/height/portal-facing gates; add a max-length gate (runs over
12 m want a jointed midpoint portal instead of a tunnel).

Proof: a two-room test plan (rooms 6 m apart), gate green, capsule sweep
(34 cm radius / 88 cm half-height) down the run axis in pure Python
(sampled disc-vs-wall check, no editor needed).

## 2. Mansard + conical roofs (closed solids)

Status: rect mansard = 4 single-sided slope quads + trim beams; round cap =
2 sloped bands + finial sphere. From below/inside they are invisible; the
gable triangles rely on wall heads.

Rebuild: every slope becomes a closed slab (outer face panel, inner face
panel, eave + ridge edges trim_gold), eave overhang as a real parameter
(default 0.6 m, already exposed), ridge beam kept, gable ends closed with
wall_plaster triangles keyed off the room footprint. Pitch gate stays
15-60 deg. Round cap: bands become slabs + eave ring trim + finial kept.

Proof: closed-solid check per roof (signed volume > 0 on the slab set),
no new roles, determinism + footprint gates unchanged.

## 3. Order

Corridor slabs first (unlocks multi-room plans), roofs second (visible in
every exterior view), both before the UE stage so P1 cooks the closed build.
