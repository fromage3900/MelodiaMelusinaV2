# Portfolio Renders — Handoff, 2026-09-21

**Status in one line:** the canonical Melusina render state landed at 13:44 (`13dbc182e`), but **no
frame has been captured from it yet**. Every still on disk from today predates it and is a proof frame,
not a portfolio frame.

Reference state (do not re-derive): `CURRENT_STATE.md` §3, *CANONICAL Melusina presentation state —
2026-09-21*.

---

## 1. What exists on disk

`Saved/Screenshots/MelusinaPortfolio_20260921/` holds 340 PNGs, all captured between 00:00 and 02:07.

| Pass | Time | What it is | Verdict |
|---|---|---|---|
| `V1`–`V13` | → 01:19 | Bow-draw stills, 20 frames each | Proof only. The rear three-quarter camera, blown-out white hair, flat black ground plane, figure centred |
| `WaveHarpTransform_V1`–`V3` | 02:03–02:06 | Harp → bow transform sequence | Proof only. Same camera and lighting problems. The transform itself reads |
| `BowOrientationSweep`, `BowRelativeSolve` | 02:04–02:07 | Bow attach-rotation solve | Diagnostics. Settled the `hand_l` / scale 0.9 / world `(0,90,0)` attach |

Why they fail: they use the old `(260,-240,115)` yaw-137 camera, which is her **rear** three-quarter
(her front is **-X/+Y**). The directional light was at 10 and auto-exposure was on, so she blew out to
white against the dark ground. Both are fixed in the canonical state; nothing has been rendered since.

## 2. The next capture (one sitting)

1. Open `/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture`. After any rebuild,
   re-apply Standalone PIE first (command in `CURRENT_STATE.md` §3).
2. Camera `CAM_Melusina_BeautyFront34`: `(-383, 351, 250)`, pitch −17.1, yaw −48.5, FOV 40,
   exposure locked (min = max brightness 0.25). Leave the lights at directional 3.0 / skylight 0.45.
3. Pose: play `A_Melusina_BowAttackV2_PortfolioShoulders` as a **dynamic montage on `DefaultSlot`**,
   rate ~0.08, so the 0.50 s draw notify holds. **Not** `AM_Melusina_BowAttack_Bound`, which carries
   the hiked shoulders.
4. Bow: `Portfolio_WaveHarp_Bow` on `hand_l`, scale 0.9, world rotation `(0,90,0)`. Hide the harp.
5. Wardrobe: Shirt / Boots / Accessories come from the presenter's `DefaultGarmentMeshes` (fixed in C++
   today). The R2 skirt is the standalone `Portfolio_R2_Skirt` actor, because the wardrobe correctly
   refuses its separate skeleton.
6. Composition: keep her in the right third and the left clear for HSR-style UI.
7. Capture into a new `Saved/Screenshots/MelusinaPortfolio_20260922/Beauty_V1/`, not into `V14`, so the
   proof passes stay separate.

**Acceptance for a portfolio frame:** you can read her face; the hair has its hue and is not clipped
white; the horizon sits above her head; the bow reads as held; no black void fills the lower half. The
last one probably needs a ground material or a backdrop in the capture level, and nothing is there yet.

## 3. Known blockers for other shots

- **Battle shots:** both enemies are unusable. `BP_WeakEnemy` (`SK_Zundamon`) collapses above the hips
  (Hips 68.40 → Upper_Chest 68.59), and 5 of its 6 material slots are `WorldGridMaterial`.
  `BP_EnemyUnit_MelodySlime` has no mesh, and `SM_MelodySlime` is ~6 uu with a placeholder material.
  Source files and the CosmicReaver `.usdz` are catalogued in `CURRENT_STATE.md` §3.
- **Hair:** `bBoneSubdivisionCollisionOnly=False` in `ABP_Melusina_WaterHair` gives the 220 dummy bones
  real simulation. It is stable in PIE, but no still shows the new motion yet. Capture a short
  sequence rather than a single frame.
- **Shorewake outfit:** the whole-outfit swap and Sail boarding landed in C++ today (build passed
  15:06). Outfit stills wait until the catalog pass and PIE proof in `CURRENT_STATE.md` §3 *C++ rebuild pass 1*.

## 4. Do not

- Render from the old `(260,-240,115)` camera again.
- Use `AM_Melusina_BowAttack_Bound` for stills.
- Re-open "hair needs a re-rig". That claim was superseded today.
- Chase the `melodia_animation_validate_bindings` "NO POSE OUTPUT PINS" result for the battle ABPs.
  It is a false positive.
