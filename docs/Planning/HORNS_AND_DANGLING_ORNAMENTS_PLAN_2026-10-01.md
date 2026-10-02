# Horns + Dangling Ornaments — updated plan (2026-10-01)

**Status:** plan only. Nothing built. Companion to
[`GN_BUILDER_AUDIT_2026-10-01.md`](GN_BUILDER_AUDIT_2026-10-01.md) and
[`PHYLLOTAXIS_SPIRAL_PLAN_2026-10-01.md`](PHYLLOTAXIS_SPIRAL_PLAN_2026-10-01.md).

---

## Read this first: step 0 is ALREADY DONE (corrected 2026-10-01, verified live)

**`s5_bighorn_horns.py` is not a pending promotion — it is already live.** Verified through
MCP 9876 in the working session: all 15 dial names match the runner exactly, `has_lissajous:
false`, one curve family, and the belly measures present on both radius and thickness.

Full evidence: [`BIGHORN_LIVE_VERIFICATION_2026-10-01.md`](BIGHORN_LIVE_VERIFICATION_2026-10-01.md).

**An earlier version of this plan said the rebuild "was authored but not promoted." That was
wrong** — 45 nodes is the *rebuilt* tree's size, not the rejected one's, and I read it backwards.
Note also that the live `Curl Radius` (0.105) and `Turns` (1.25) differ from the runner's
docstring (0.085 / 1.35): **that is owner tuning, not drift. Do not "correct" it.**

So the horn spine is done. What remains is **§2 — danglers on the existing horn** — and it
still needs `phyllotaxis.py` first.

### The measured baseline, for reference

Horn world bbox span **0.444 × 0.193 × 0.217 m** on a 1.18 m body, 8,664 evaluated verts,
`scale [1,1,1]`, raw mesh 0 (pure GN — correct, not a defect).

**`s5_bighorn_horns.py` (27,592 bytes) already exists and already fixes the horn.** Written
2026-09-25, it is a rebuild of `MEL_S5_horns` authored specifically to replace the spiral tree
**the owner rejected**. Its own docstring records the measured defects it exists to fix:

| Rejected tree | Bighorn rebuild |
|---|---|
| 3 coils at 0.07 m curl radius — "a cinnamon roll, not a ram horn" | 1.35 turns, curl radius 85 mm |
| Root 0.028 → tip 0.006, a 4.7:1 cone with **no belly** | base 62 mm · **belly 58 mm** · tip 8 mm |
| Wobble 0.008 vs curl 0.07 = 11% noise, **visually inert** | 14 growth ridges, 3.5 mm deep |
| **TWO competing curve families in one tree** (Spherical Spiral AND Lissajous A/B/Delta/Coils) driving one output — 13 dials, no decision | **ONE curve family**, radius authored as an explicit radius-at-t curve, cross-section flattening to a 0.35 oval at the tip |
| `s5_horns_live.json` recorded **2.63 × 2.15 × 2.37 m on a 1.19 m sheep**, measured pre-Align-To-Surface in the wrong frame, never reconciled | targets the 1.19 m body explicitly |

**The live `MEL_S5_Horns` is still the rejected one.** The prep file's 22-tree census shows
`SheepHorns::S5_Horns` at 45 nodes / 60 links — the *old* count. The rebuild was authored and
never promoted.

**So: promote it before writing anything new.** That is a file swap, not a build.

---

## 1. Step 0 — promote the bighorn rebuild (do this first, ~30 min)

```bash
blender.exe -b Saved/Audit/choral_sheep/capstone_prep_20261001/choral_sheep_CAPSTONE_PREP_20261001.blend \
  --factory-startup --python Saved/Audit/choral_sheep/gn_v2_20260919/s5_bighorn_horns.py
```

Then, before believing it:

- **Re-measure the horn extent against the body.** The old tree's failure was a 2.63 m horn on
  a 1.19 m sheep. The gate is: horn span is plausible against a 1.19 m body, measured on the
  *evaluated world bbox*, not from the script's own JSON.
- **Re-read the receipt's `src`/`opened` fields** — that is the provenance chain, written by the
  run rather than inferred after.
- **Re-open the saved file and re-measure.** Append+save is where unlinked grafts die; the
  post-save read is the only evidence that matters.
- Confirm the tree count for `SheepHorns::S5_Horns` has *changed* from 45 nodes. If it is still
  45, nothing happened.

⚠️ **The prep `.blend` exists on one disk only — copy it before any run that saves in place.**
Verified 2026-10-01: `choral_sheep_CAPSTONE_PREP_20261001.blend` is in **neither** git nor
Perforce (`p4 files` → *no such file*). It carries the wool parent-inverse fix, the
`SW_SculptCage` shrinkwrap, and the hidden 1.2M-poly ghosts — all unrecoverable if lost.

- `s5_bighorn_horns.py` **is** already in Perforce (change 222), so the script itself is safe.
- Of 45 sheep `.blend` files on disk, 35 are in the depot. The prep file is one of the 10 that
  are not.

---

## 2. The new builder: dangle-along-a-host-curve

**This is the genuine gap.** The 13 danglers in `cute_decor.py` are all standalone shapes, and
the sheep's `SheepPearlDanglers` (39 nodes) and `PearlDangl_0..2` (17 nodes each) were placed
by hand. Nothing attaches a dangler to a host curve at a point along it.

**Closest prior art:** `ornament_strip.py::build_gold_ornament_strip` — beads along a curve.
Extend that idea; do not start from nothing.

### `MEL_horn_dangler_row` (wrapper) + `_dangle_row` (sub-builder)

Same composition contract as `filigree_kit.py`: sub-builder takes `(tree, props, …)`, returns a
**geometry socket**; wrapper owns the interface. Return `tree`, never a triple.

| Dial | Default | Note |
|---|---|---|
| `Count` | 7 | int, wide range |
| `Host Offset` | 0.0 | **along `CurveToPoints.Normal`, never `InputNormal`** |
| `Drop Length` | 0.06 | scaled per §4 below |
| `Terminal` | — | terminator selector |
| `Terminal Size` | 0.015 | |
| `Chain Links` | 3 | 0 = single drop |
| `Link Radius` / `Link Thick` | 0.011 / 0.0028 | brooch-genome values |
| `Phase Offset` | 0.0 | de-correlates the two horns |
| `Jitter` | 0.0 | **0 default** — see neutrality gate |
| `Even` | false | the phyllotaxis bool, shared with the spiral plan |

### Terminators — reuse, do not rebuild

`MEL_pearl_dangl` (**already on this sheep**), `MEL_star_dangl`, `MEL_crystal_drop`,
`MEL_lace_dangl`, `MEL_bead_tassel`, `MEL_star_finial`.

⚠️ **Scale.** The dangl family is jewellery scale and already correct: `build_star_dangl`
measured 54 × 57 × **1003 mm** long, `build_lace_dangl` 60 × 80 × **1005 mm**. A horn drop wants
60–120 mm. **Rescale via `Scale Elements` or the `Terminal Size` dial — do not re-author the
shape.**

### Two non-negotiable construction rules

1. **`GeometryNodeInputNormal` is EMPTY on curve points and its offset silently no-ops.**
   Measured: offsetting 180 curve points by 0.10 along `InputNormal` left every coordinate
   bit-identical. **Use `CurveToPoints.Normal`** — with a 0.21 radius arc, a 0.10 offset along
   it put every point at r = 0.310, exactly radial. This is the single most important rule in
   this builder; get it wrong and the danglers sit buried inside the horn.
2. **`DeleteGeometry`'s unlinked `Selection` defaults TRUE** — no link deletes everything. A
   96-point resampled curve went to 0 verts, the tree still built, still passed every size and
   seat gate, with the ornament simply absent. **Link Selection explicitly and assert the
   branch produces geometry.**

Also: `parts = [_transform(..., parts[0], ...)]` **rebuilds** the list and discards the rest.
Assign `parts[0] = ...`. And a `_feed` helper that swallows exceptions makes a missing link
indistinguishable from a correct one — record and print every failure.

---

## 3. Seating — measure, never iterate

The sheep crown is the precedent for getting this wrong. Per the skill:

> **DO NOT "clean up" a local transform that evaluates correctly.** The earlier version of this
> skill said to reset `scale`/`rotation_euler` and re-solve `.location` when adopting a legacy
> object. Doing that to the crown **DESTROYED a correctly-seated piece four times over.**

The correct procedure:

1. **Measure the evaluated world bbox first. If it is right, do nothing.**
2. Only if wrong, measure the tree's **local** vertex centre by hand (`evaluated.to_mesh()`),
   and note the parent's real world transform.
3. **Solve ONCE in closed form:** `world_centre = parent_t + loc + local_centre`.
   **Never iterate** — the map is affine and a mis-signed parent term becomes positive
   feedback, not convergence.
4. Reset inherited `scale`/`rotation_euler` only when you have **measured** that they are the
   defect. Opaque ≠ broken: one legacy lane left `scale 2.0065` and `rot 73.74°` on a wreath
   object; a different object legitimately carries a large local rotation the parent chain
   cancels.

---

## 4. Per-object variation needs per-object tree copies

**NODES modifier idprops are DEAD in 5.2.1** — both `mod["Name"]` and `mod[identifier]` raise
`id properties not supported`, headless *and* live. And modifiers **capture** interface
defaults at creation, so changing a tree default afterwards does not recapture: a re-point at a
different tree keeps the stale values and the evaluated geometry reads identical.

So for two horns that must differ (left/right, or `Phase Offset`):

- Set the tree interface default **before** `modifiers.new`, or
- remove + re-add the modifier to recapture, or
- use **per-object tree copies** — the established `Sheep_Bloom_A/B/C` pattern, where copies
  share one mesh datablock. **Keep weight sums at 1.0 or the copies deform wrong.**

---

## 5. Proof gate

`Tools/wardrobe_pipeline/horn_dangl_proof.py`:

1. Both trees **construct** in `bpy.data.node_groups`.
2. **Dangler vert count == predicted sum.** A count suspiciously close to one component means
   a socket-domain mismatch — that exact signal exposed a piece whose every ornament branch was
   empty while 18 gates passed.
3. **No dangler is buried in the horn.** Signed containment against the measured horn
   cross-section, allowing the dangler's own thickness. A *proximity* test cannot prove seating:
   counting verts within 12 mm read 56.6% "buried" on a correctly-wrapped piece, because a band
   resting on a surface always has its inner half in contact.
4. **Every node created has a consumer** — the orphan check. No gate catches an orphan otherwise.
5. **Neutrality:** `Jitter 0` and `Host Offset 0` evaluate to no displacement.
6. Horn extent plausible against the 1.19 m body.

---

## 6. Sequence

| # | Work | Gate |
|---|---|---|
| 0 | **Promote `s5_bighorn_horns.py`** (exists) | horn extent re-measured; tree node count changed from 45 |
| 1 | `phyllotaxis.py` per the spiral plan | 6-point proof green |
| 2 | `MEL_horn_dangler_row` using terminal reuse | 6-point proof green |
| 3 | Wire to the promoted horn; left/right tree copies | vert count + seating measured |
| 4 | Stage file for owner visual judgement | **owner decides, not the agent** |

**Two nudge→verify passes max, then stop and ask.** Never loop
screenshot→adjust→screenshot on style. Ship a number plus ONE screenshot, then one question.

---

## 7. Out of scope

Wool/fleece (the real capstone blocker, separate lane — `fluffy_pilot{,2,3,4,5}.py` remain the
open decision), the closed-editor build, UE import, Substance/UVB bake.
