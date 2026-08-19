# Melusina V2 finalization plan — 2026-08-15

Supersedes the earlier draft of this file. Written after the rig defect was closed, the
export went green, and the Infinity Nikki / Wuthering Waves research landed.

**Companion:** `Docs/Research/AAA_ANIME_UE_CHARACTER_PIPELINE_2026-08-15.md` (Infold, Kuro
Games, SDF face shadows, garment layering, skeleton/LOD standards) and
`Docs/Research/BLENDER_ADDON_INTAKE_2026-08-15.md` (77 addons + 37 extensions).

---

## 1. Closed today

| | Evidence |
|---|---|
| **Rig defect root-caused and fixed** | Cornea section was skinned to `eyes → MCH-eyes_parent → root`, a sibling of the spine. `MCH-eyes_parent` carries a `COPY_TRANSFORMS` constraint to `ORG-face` that FBX export discards. Same shape orphaned 20 finger controllers. |
| **Fixed at the source, not the symptom** | The orphaning was baked into `melusina_contract_hierarchy.json` (69 bones parented to `root`), which `apply_canonical_hierarchy` stamps into every export. Repointed the 20 finger controllers to their real parents. Stage weights stay on the `c_*` bones ARP drives. |
| **Export green** | `ok:true`, `promotion_allowed:true`, no blockers, approved ARP exporter, **0 hierarchy mismatches**, **0 orphan-skinned bones** across all five pieces. |
| **Weight-paint base applied** | 20,026 vertices were over 4 influences (peak 19). All 11 meshes now peak at exactly 4, normalized, zero unweighted. |
| **ARKit shapes populated** | 35 of the 52 empty ARKit keys filled from their FACS twins. UE goes from 68 → 103 morph targets. |
| **Gate added** | `Tools/test_melusina_skin_topology_contract.py` — every skinned bone must descend from `root_x`. Baseline empty. Suite 19/19. |

Stage lineage: `ZenRebuild_WIP` → `EYEFIX` → `EYEFIX_ONLY` → `PAINTBASE` → **`FINAL_2026-08-15`**.

---

## 2. Immediately remaining — V2 as canonical pawn

1. **Dismiss the `Content Browser 2` modal** in the editor. Monolith cannot answer through
   a blocking modal loop; this is the only thing gating import.
2. **Reimport** — `import_melusina_wardrobe_contract.py -- --all-v2 --replace-existing`.
   Verify already passed on Body/Shirt/Skirt/Boots. Accessories flags **material slot
   order only** (all ten materials correct, permuted by merge order) — resolves on
   replace, or is a two-minute reassign.
3. **Verify the corneas numerically**, not by eye: `get_animated_bone_transform` on an eye
   bone composed against `head_x` must hold constant across frames.
4. **Closed-editor build** for the seven wardrobe C++ fixes — still compiled-pending after
   a full day of editor contention.
5. **`DA_MelodiaCosmeticCatalog`** still does not exist. The wardrobe C++ fails closed
   without it and logs once, loudly.

---

## 3. Female base for long-term use — the Nikki/WUWA adoption order

Taken from the research brief's adopt table, reordered by cost-to-value for a solo dev.
Every item below is **stock UE or Blender** — no engine fork, which both studies say is
the trap.

**Do first — hours to days, transformative:**

1. **Smoothed / spherical normals on face and hair.** Kuro Games do exactly this
   (documented, Unreal Fest Tokyo 2025). Hours in Blender, and it fixes the ugliest
   stylization failures on its own. *Do this before the SDF work.*
2. **SDF face shadow map.** The genre's visual signature. Bakers exist; the UE material
   math is ~10 lines. This is the single biggest look-uplift available.
3. **Per-outfit body hiding via mask texture** in the master material — avoids seams and
   extra draw calls versus cutting the body.

**Do next — the thing that makes it a *base* rather than one character:**

4. **Precompute the non-clipping garment rest state** (Blender Shrinkwrap bake per
   outfit). This is Infold's actual architectural insight: anti-clipping is solved in
   *preprocessing*, not at runtime. `wrapper_addon` and `simply_cloth_studio` are both
   installed and do this.
5. **Hybrid cloth** — bone chains for structure, Chaos Cloth only for genuinely soft
   material. UE ships `AnimDynamics`/`RigidBody` natively; biggest perf win available.
6. **LOD bone/morph stripping** — strip face bones and morphs at LOD1/2 via Bones to
   Remove and Morph Target Position Error Tolerance.

**Decide early, expensive to reverse:**

7. **Leader Pose vs Copy Pose From Mesh.** Leader Pose children **cannot simulate
   physics**. The wardrobe component currently uses Leader Pose. If garments need cloth
   sim (item 5), this must change. *Owner decision.*
8. **The 465-bone skeleton.** AAA norm is 150–200 deform bones; UE5 stock is 67. 465
   should be a Blender-side authoring number, not the in-engine one. The contract fix
   makes 465 *correct*, not *right*. *Owner decision, not urgent.*

**Explicitly do not:** fork the engine, write a custom constraint cloth solver, or
back-port Lumen. All three are documented real practice at Kuro/Infold and all three are
specialist programmes inside 800-person teams.

---

## 4. Facial — what is left

35 ARKit shapes now carry real deltas. **17 remain genuinely unauthored** and no copy can
fabricate them:

```
eyeLookDown/In/Out/Up (L+R)   eyeSquintLeft/Right   eyeWideLeft/Right
mouthClose   mouthRollLower   mouthRollUpper   mouthShrugLower   tongueOut
```

The eight `eyeLook*` directions are the important ones — they are what makes a face track
a target. **Faceit 2.3.56 is installed** and can generate these from the rig, which is the
right route rather than sculpting. `live_link_unreal` is installed if iPhone capture is
wanted.

*Owner decision: is Live Link Face capture in scope?* If not, 103 morphs is already
generous and this thread closes.

---

## 5. Animation — retarget and BlendSpace

The retarget path is proven; the library is not. Three blockers, in order:

1. **Retarget with root motion preserved.** Currently root-locked, which is precisely why
   clip speed is unknowable.
2. **BlendSpace samples are guesses.** `BS_Melusina_Locomotion_Hybrid` holds 7 samples but
   only 4 unique clips — Walk at both 150 and 180, Run at 300 and 420, Sprint at 540 and
   630. Every X derives from `root_motion_speed_known: false`. Positions must come from
   `get_root_motion_speed`. The axis also caps at **650** while the sprint gate records
   **714 uu/s**, so sprint clamps today.
3. **The IK rig has zero solvers and zero goals** — "Run IK Rig" is inert, so there is no
   foot planting. That is the difference between "retargeted" and "not sliding".

Only locomotion belongs in a BlendSpace. Jump/land are state-machine one-shots;
dodge/bard/combat are montages. **Swim has no valid source** — the only swim clips are the
rejected Quaternius ones. Sourcing is now safe to do, since the rig no longer tears.

---

## 6. Division of labour

**Autonomous:** reimport, numeric verification, closed-editor build, root-motion retarget,
BlendSpace measurement and placement, shrinkwrap bakes, LOD stripping setup, gates.

**Human-authored:** hand weight paint on hands and cloth boundaries, lookdev, the SDF face
shadow authoring, and the three owner decisions above (ARKit scope, Leader vs Copy Pose,
465-bone skeleton).

---

## 7. Standing rules learned the hard way today

- **`--factory-startup` for all headless Blender work.** The `rockform` addon raises
  `KeyError` on every depsgraph update and killed two export runs. It also cuts stage load
  from 1:06 to 12.9s.
- **Enable ARP explicitly** as `bl_ext.user_default.auto_rig_pro` — it is an *extension*,
  not under `scripts/addons`.
- **Never touch the active object** on a loaded interactive stage; it rebuilds the
  depsgraph on 879 objects and OOM'd Blender at 35 GB.
- **Use the direct data API, not `bpy.ops`,** for per-vertex work — the operator path
  OOM'd at exit 137.
- **Never save over the master stage**; sidecar only.
- **`Melusina.001` is untouchable** — the known-good animation reference.
- Weights that satisfy the exporter can break the authoring rig. Fix export problems in
  the export contract, not in the weights.
