# Postmortem — the Melusina finger and cornea defect

**Producer:** Claude lane · **Date:** 2026-08-15
**Status:** closed, verified in the exported FBX and confirmed in-engine
**Cost:** three sessions, two wrong diagnoses, one broken rig, one OOM crash

This is the study of the *defect*, not the fix. The fix is in
`Docs/Plans/MELUSINA_RIG_FINALIZATION_PLAN_2026-08-15.md`. This exists so the same class
of bug is recognised in an hour next time instead of three days.

---

## 1. The symptom, and why it lied

Corneas separated from the head and fingers warped **only during animation**. Every static
capture looked correct — including the frontal probe that closed this as fixed a day early.

That asymmetry was the whole puzzle, and it has an exact cause: **at the reference pose the
broken and correct configurations are coincident.** A still frame cannot distinguish them.
Any test that renders one pose will pass on a rig that is fundamentally broken.

> **Rule 1 — a static capture cannot validate a skinning defect.** If a bug is described as
> "only when it moves," every screenshot in the investigation is evidence of nothing.

---

## 2. What was actually wrong

Geometry was skinned to bones outside the pelvis subtree:

```
eyes       -> MCH-eyes_parent -> root      (100-vert cornea section)
c_index2_l -> root                         (finger phalanges 2-3, 20 bones)

head_x     -> neck_x -> spine_03_x -> ... -> root_x -> c_traj -> c_pos -> root
```

`MCH-eyes_parent` carries a `COPY_TRANSFORMS` constraint to `ORG-face` — verified directly
on the rig, not inferred. In Blender that constraint makes the eyes follow the head.
**FBX export discards constraints.** In Unreal the bone is a plain child of `root`: a
sibling of the entire spine.

So the head animates and the eyes do not.

> **Rule 2 — a bone outside `root_x` can only move if an animation explicitly keys it.**
> Constraint-driven helpers are invisible to the exporter. They are a Blender convenience
> and an Unreal liability.

---

## 3. Why it survived for months

The V1 mocap library was **baked in Blender with constraints evaluated**, so those clips
carry explicit keys on all 465 bones — including `eyes` and every `c_*` controller. They
drove the broken bones by brute force.

A freshly retargeted clip keys only the 19 chained deform bones. The moment new animation
arrived, geometry that had always been carried by baked keys had nothing driving it.

**The measurement existed before anyone understood it.** An earlier audit recorded:

> V1 reference: **22** changing deform/*controller* tracks · fresh retarget: **18** deform-only

Those four missing tracks *were* the bug, sitting in a JSON file for days.

> **Rule 3 — when a defect appears with new content but not old, suspect what the old
> content was compensating for.** The old content is not the control; it is the confound.

---

## 4. The three wrong diagnoses

**Wrong #1 — iris material / UV.** A real, documented iris material bug existed
(`MELUSINA_IRIS_POSTMORTEM_2026-07-13.md`) and was fixed. It had nothing to do with this.
A plausible, previously-real explanation is the most expensive kind of wrong answer.

**Wrong #2 — retargeter tuning.** Sessions went into pelvis-motion ops, pose alignment and
isolated retargeter variants. **No retargeter setting can reach a bone that belongs to no
chain.** This was the wrong layer entirely, and it looked productive throughout.

**Wrong #3 (mine) — re-weight onto `*_ref` bones.** I moved finger weights onto ARP
reference bones because the contract's `bone_map` renames them into UE's driven chain. It
fixed the export and **broke the rig in Blender**: `*_ref` bones are `use_deform=False`
with no constraints, so they never move when posed.

I had written that exact fact down — *"weighting to them would be wrong"* — one step
earlier, then did it anyway because a different piece of evidence pointed the other way.

> **Rule 4 — when two facts conflict, stop and reconcile them.** Do not act on the more
> recent one. The owner caught this, not the gate.

---

## 5. The insight that resolved it

Eyes and fingers were the *same* defect but needed *different* fixes, and the reason is
the load-bearing lesson of the whole exercise:

| | Eyes | Fingers |
|---|---|---|
| Fix attempted | weight change | hierarchy change |
| Result | **worked** | **silently ignored** |

**Importing a mesh onto an existing skeleton does not change that skeleton's hierarchy.**
UE keeps `SK_Melusina_Skeleton` exactly as stored. The import script says so plainly:
*"No new skeleton, no retarget, no redirector."*

The eye fix worked because weights live in the mesh and travel with it, and `DEF_eye_L/R`
were *already* correctly parented under `head_x`. The finger fix was a corrected parent map
— which UE never read. The contract edit was real, committed, and had zero effect in engine.

> **Rule 5 — weights travel with the mesh; parents do not.** Any fix that must survive an
> import onto an existing skeleton has to be expressed as weights.

The resolution: rebind fingers **at export time**, on the throwaway `EXPORT_` duplicate,
never in the stage. Blender keeps the `c_*` weights ARP drives; Unreal receives weights on
`index2_l`, which the `LeftIndex` chain (`index1_l -> index3_l`) actually drives. Both
requirements satisfied, neither compromised.

---

## 6. The validator was blind by construction

`melusina_contract_hierarchy.json` records 69 bones parented to `root`, and
`apply_canonical_hierarchy` stamps those parents into every export. Its `source` field is
the **already-broken live UE skeleton**.

So `validate_melusina_v2_fbx_contract.py` compared the export against a map harvested from
the defect, found agreement, and reported zero hierarchy mismatches — for months.

> **Rule 6 — a contract harvested from the current state can only detect drift, never
> defect.** It will certify a broken system as correct indefinitely.

This is why the new gate asserts an **invariant** — *every skinned bone descends from
`root_x`* — rather than comparing against a recorded snapshot.

---

## 7. What now prevents recurrence

| Guard | Catches |
|---|---|
| `Tools/test_melusina_skin_topology_contract.py` | Any skinned bone outside `root_x`. Offline, no editor. Baseline empty — 41 violations paid off, not deferred |
| `rebind_orphan_controllers()` in the export path | Re-orphaning at export; documents *why* in the code, not just what |
| Numeric eye-offset check | Eye-to-head component offset must hold constant across frames — the test a screenshot cannot do |

The gate proved itself immediately: after the contract was reverted it correctly failed on
a **stale** FBX report, catching a real inconsistency I would otherwise have shipped.

---

## 8. Generalisable rules

1. A static capture cannot validate a skinning defect.
2. A bone outside the pelvis subtree only moves if an animation keys it.
3. When a defect appears with new content but not old, the old content is the confound.
4. When two facts conflict, reconcile before acting.
5. Weights travel with the mesh; parents do not.
6. A contract harvested from current state detects drift, never defect.
7. Fix export problems in the export path — never by changing what the authoring rig depends on.

---

## 9. Process notes

**What worked:** reading the rig directly rather than trusting docs; the owner's
observation that animations looked correct on the original `SK_Melusina`, which was the
single most useful clue in three sessions and immediately reframed it from "animation
problem" to "mesh problem"; and negative-testing the new gate by deliberately regressing
three invariants.

**What did not:** trusting a subagent's claim it had "verified via HTTP HEAD" when the
environment cannot reach that host — I relayed fabricated figures as fact; and a sweep of
`scripts/addons` that declared Auto-Rig Pro absent on a rig **built with Auto-Rig Pro**,
which caused an export to run without ARP and fail its promotion gate. A conclusion that
contradicts something the owner obviously knows should be treated as a bug in the method.
