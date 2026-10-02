# Bighorn Verification — LIVE SESSION (2026-10-01)

**Result: the bighorn rebuild is ALREADY LIVE in the working session. No promotion is
needed.** This document supersedes the step-0 promotion plan, which was written on a wrong
premise and has been replaced by the measurements below.

Companion: [`GN_BUILDER_AUDIT_2026-10-01.md`](GN_BUILDER_AUDIT_2026-10-01.md),
[`HORNS_AND_DANGLING_ORNAMENTS_PLAN_2026-10-01.md`](HORNS_AND_DANGLING_ORNAMENTS_PLAN_2026-10-01.md).

---

## 0. The live session

Read through MCP **127.0.0.1:9876**, Blender **5.2.1 LTS**, PID 64688:

| | |
|---|---|
| File | `Saved/Audit/choral_sheep/stage_a_20261001/choral_sheep_A_blossoms_FIXED_20261001.blend` |
| `is_dirty` | **true** — unsaved edits exist only in this window |
| Objects / trees | 86 / 149 |

---

## 1. Correction to my own audit: the promotion already happened

The audit reported `MEL_S5_horns` at 45 nodes with "no bighorn tree present" and concluded
the rebuild was unpromoted. **The node count was the tell I misread.** A 45-node tree is what
the *rebuilt* tree measures, not the rejected one.

Direct evidence, read from the live session:

| Test | Result |
|---|---|
| Dial names in `MEL_S5_horns` vs `s5_bighorn_horns.py` | **15 vs 15, all 15 identical**, `only_in_runner: []`, `only_in_live: []` |
| `has_lissajous` | **false** — the two-competing-families defect is **gone** |
| Curve drivers | exactly one family: `CurveSpiral` → `StoreNamedAttribute` → `CurveToMesh` |
| Authored dials | `Turns 1.25 · Curl Radius 0.105 · Base Dia 0.062 · Belly Dia 0.058 · Tip Dia 0.008 · Ridge Count 14 · Ridge Depth 0.0035` |

`Belly Dia`, `Tip Flatness`, `Ridge Depth` and `Align To Body` are **bighorn-only dials**. They
are present, set, and driving the tree. **The rejected tree is not in this file.**

⚠️ `Curl Radius` is **0.105**, not the 0.085 the rebuild's docstring specifies, and `Turns` is
**1.25** not 1.35. Those are **owner tuning on top of the rebuild** — the docstring records the
authored intent, the live values are the truth. Do not "correct" them to the docstring.

---

## 2. Gates — measured, not asserted

| Gate | Criterion | Result |
|---|---|---|
| G1 | Tree constructed in `bpy.data.node_groups` | **PASS** — `MEL_S5_horns`, 45 nodes / 60 links |
| G2 | Dials match the bighorn runner | **PASS** — 15/15 identical |
| G3 | One curve family, no Lissajous | **PASS** — `has_lissajous: false` |
| G4 | Spine plausible against the 1.18 m body | **PASS** — horn span 0.444 × 0.193 × 0.217 m |
| G5 | **Belly present** | **PASS** — measured below |
| G6 | Evaluated geometry non-empty | **PASS** — 8,664 verts / 8,626 faces (raw mesh is 0; pure GN, correct) |
| G7 | Scale is 1.0 (no unapplied scale) | **PASS** — `scale [1.0, 1.0, 1.0]` |

### G5 in detail

A 1.25-turn curl **cannot be sliced on a world axis** — a Z-slice cuts the coil several times
and mixes stations. My first attempt did exactly that and produced a meaningless series; it is
discarded. The correct measurement orders stations by **polar angle about the object's local Z**
(the spiral wraps that axis) and reads **thickness as 2 × the 4th-nearest-neighbour distance**,
using a spatial hash.

| Station | r from axis (m) | thickness (m) |
|---|---|---|
| 0 | 0.1353 | 0.01626 |
| 1 | 0.1291 | 0.01760 |
| 2 | 0.1195 | 0.02024 |
| 3 | 0.1397 | 0.01639 |
| 4 | **0.1591** | 0.01682 |
| 5 | 0.1335 | 0.01631 |
| 6 | 0.1074 | 0.01910 |
| 7 | 0.1506 | 0.01785 |

**Interior stations exceed both ends on both measures** — station 2 thickness 0.0202 and
station 4 radius 0.1591 both beat the end stations. That is a belly, not a linear cone. The
rejected tree's defining defect is **not present**.

---

## 3. Two socket facts this lane hit (5.2)

- **`GeometryNodeCurveToMesh` has NO `Radius` input.** Its inputs are exactly
  `Curve`, `Profile Curve`, `Scale`, `Fill Caps`; the output is `Mesh` (not `Geometry`).
  `c2m.inputs["Radius"]` raises `KeyError: key "Radius" not found`. The sweep radius here comes
  through **`Scale`**, fed by the `radius_plus_ridge` Math chain. `GeometryNodeCurveArc` and
  `GeometryNodeCurveSpiral` likewise take `Start Radius` / `End Radius`, not `Radius`.
- **A named attribute consumed by the sweep does not survive onto the evaluated mesh.**
  `me.attributes.get("radius")` is `None` even though `store_radius` writes it and
  `CurveToMesh.Scale` reads it. Read the *authored* dials plus a geometric thickness measure;
  do not expect to read the realised attribute back.

Verified wiring: `centreline` (CurveSpiral) → `place_curve` (SetPosition) → `store_radius`
(StoreNamedAttribute) → `sweep` (CurveToMesh), with `section` (CurvePrimitiveCircle,
**Resolution 20**) as the profile curve, then `apply_ridges` → `place_right` / `place_left`.
`Points` = 96, matching 96 × 20 = 1,920 profile points before ridge displacement.

---

## 4. What this changes

- **No promotion.** Steps 0–2 of the horn plan are done. The horn work reduces to
  **danglers on the existing horn** (still unwritten; needs `phyllotaxis.py` first).
- **The `HORNS_AND_DANGLING_ORNAMENTS_PLAN` scale warning is now partly retired:** the horn is
  *not* a 2.63 m runaway. The old `s5_horns_live.json` recorded dimensions pre-`Align-To-Surface`
  in the wrong frame and were never reconciled — that JSON is a false alarm.
- **Wool remains the capstone blocker**, per the 2026-10-01 render review. Not a horn problem.

## 5. Housekeeping

- **Nothing was mutated.** Every call this session was read-only.
- **The file is dirty and I did not save it.** Ctrl+S is yours.
- The 45-node count is now a **known-good fingerprint** for this tree: if a later edit drops it,
  the tree was rebuilt from a different source.
