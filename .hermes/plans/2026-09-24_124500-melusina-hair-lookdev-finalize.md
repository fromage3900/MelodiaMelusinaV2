# Melusina hair — lookdev and finalize

**Goal:** Melusina's hair is portfolio-final: it reads as luminous pearl-water on the Nikki lane,
frames her face instead of hiding it, moves with her head and flows on its own, and carries a live
water layer (FluidNinja droplets + FLIP drip). Owner approves it on a fixed lookdev sheet.

**Execution SSOT:** `CURRENT_STATE.md`
**Runtime owner:** `BP_MelusinaJRPGCharacter` → `WaterHairMesh` (`SK_MelusinaHair`, `ABP_Melusina_WaterHair`)
**Surface authority:** `M_Master_Nikki` via `MI_Melusina_Nikki_Hair`. The old water material is retired for hair — never reintroduce it.
**Sub-goal:** `.hermes/plans/2026-09-24_121500-melusina-water-hair-fluidninja-goal.md` (water layer detail)

## Fixed — do not touch

- Hair offset `(0, 144.1994, −15.9001)` roll −90 on `head_x` (inverse bind).
- Kawaii root `hair_root`; bangs-lift ModifyBones 0–3. Do not retune Kawaii to fake curvature.
- No new master materials. Nikki master edits are owner-approved only.
- `MelodiaIntegrationMap` untouched. **Owner 2026-09-24: all lookdev and testing is PIE on `L_MelusinaMorning` only — not `L_MelusinaPortfolioCapture`.**

## H0 — stable capture (blocker for everything visual)

- 2026-09-24 crash: `Ensure InRHITexture` in `D3D12RenderTarget.cpp:599` (a texture read-back on a null RHI texture) during FluidNinja + PIE viewport clip captures.
- Isolate it: one PIE run with `WaterHairFluid` disabled + clip capture; one with FluidNinja on + single `HighResShot` only.
- Use whichever capture path does not crash for all later gates.
- **Gate:** two consecutive full captures with FluidNinja on, no crash.
- **PASSED 2026-09-24:** the fatal crash was not the capture — the editor died at 12:37:01 during *autosave* while generating a thumbnail for the retired `MI_Melusina_WaterHair_v10` (the 12:34 `InRHITexture` report was a non-fatal ensure at clip start). Removed the last two references (`SK_MelusinaHair` slot `Cosmos` and `WaterHairFlipCache` override → `MI_Melusina_Nikki_Hair`); referencers now 0. Morning clips `h0_run2` + `h0_run3` back-to-back with FluidNinja on: no crash, 7/7 valid frames.

## H1 — lookdev rig

- PIE on Morning, in-context light. Four views set by a PIE probe (transient camera + view target, framed on `head_x`): front ¾ face, profile, back, full-body gameplay distance. Nothing saved into the level.
- **Gate:** a baseline PIE contact sheet of today's hair from all four views, saved under `Saved/Portfolio/HairLookdev_<date>/`.

## H2 — surface lookdev on the Nikki lane

- Tune `MI_Melusina_Nikki_Hair` only: `BaseTint`, `NikkiPearl_*`, `Iridescence` / `IridescencePower`, `FabricSheen`, `ShadowDreamTint`.
- `MF_NikkiIridescenceSheen` was repaired today — confirm the iridescence now visibly reads on the hair (before/after at 0 vs tuned).
- Every material slot on `SK_MelusinaHair` resolves to the Nikki lane or the outline MI; list the slot map on the sheet.
- Strand outline (`MI_Melusina_Outline_005`) weight checked at gameplay distance.
- **2026-09-24 finding:** the tint was invisible because the master's pastel grade (`NikkiPastelStrength` 0.6, near-white pink pastel ramps) washes it out. With pastel 0.1–0.35 + aqua pastel ramps the tint reads. PIE variants A Pearl Aqua / B Deep Lagoon / C Moon Pearl in `Saved/Audit/melusina_hair_lookdev_20260924/h2_variants_v2/H2_hair_variants.jpg`; probe script `hair_view.py`. Owner: rig and MIs both need work.
- **Gate:** hair reads pearl-aqua, not flat white, under key/fill/rim and in Morning; owner picks from ≤3 variants.

## H3 — face framing

- Open issue: the face reads dark and partly hidden in lit shots.
- Fix within the fixed list: bangs-lift ModifyBone values, face-light / rim in the rig, `ShadowDreamTint` on the hair.
- No hair-offset change unless a Blender-vs-live bind comparison proves a mismatch.
- **Gate:** front ¾ and gameplay views show both eyes clearly; owner approves.

## Rig fixes 2026-09-24 (owner: rig first; H2 colour = A Pearl Aqua, saved to `MI_Melusina_Nikki_Hair`)

- **Head collision was ineffective:** `DA_Melusina_HairCollisionLimits` held one sphere, radius 8.5 at `hair_root` (the head base / neck), so it never reached the strands. (Its `bEnable=False` is ignored — Kawaii enables limits at runtime when the driving bone is valid.) Now radius 12, `OffsetLocation (0.119, 0.0041, −0.0986)` in `HairExp_Rig` space (bone scale ×100) = head centre at eye level; nose 10.8 cm / ears 16.1 cm from it. Verified with `a.AnimNode.KawaiiPhysics.Debug 1`: sphere sits on the face, strand tips outside it.
- **Fringe:** extended the existing bangs lift (additive Pitch 8.7 / Yaw 23.2 / Roll −2.5, parent-bone space) to `A_DEF_hair_bbone_004` and `_008`, the two remaining strands crossing her eyes (ModifyBone_4/_5, chain 0→5→Kawaii). ABP compiles 0/0, saved.
- **Rings at her cheeks** are material slot `Cosmos` (hair-tie rings on the front side locks). They were near-invisible on the retired water MI; since moving the slot to the Nikki hair MI they read as solid aqua rings. Owner call: keep as hair ties (give them an accessory MI) or hide.
- Open: the front ¾ still shows side strands over her right eye at rest — next pass.
- **Hair ties (owner: keep):** `SK_MelusinaHair` slot `Cosmos` → `MI_Nikki_Show_PearlSheen` (pearl hair ties). Saved.
- **Eyes / blink 2026-09-24:** the blink *timer* works (ABP `BlinkAlpha` 0→1 every ~3.5–4.5 s; `eyeBlinkLeft/Right` curves both reach 1.0). Two faults found:
  1. **Iris seat too shallow** — the `EyeIrises` discs sat 1.46 cm in front of the eyeball centres, proud of the closing lid, so they drew over it. Depth sweep in PIE (0.4 / 0.8 / 1.0 / 1.2 / 1.5 / 1.8 cm back): 1.8 cm hides the iris under the closed right lid (hairline crescent only) with no change to the open look. Saved: `EyeIrises` RelativeLocation `(-0.1019, 133.6346, 43.2741)` (was `(-0.0927, 133.6406, 45.0741)`, −1.8 on `head_x` face-forward). `EyeLashes` unchanged. Clean-PIE proof `Saved/Audit/melusina_hair_lookdev_20260924/eyes_final/eyes_final_sheet.jpg`.
  2. **Left-eye closing morphs don't close her left lid** — forced-morph A/B on `SK_Melusina_V2_Body`: `eyeBlinkRight` and `eyesCloseR` close the right eye; `eyesCloseL` (and the ABP-driven `eyeBlinkLeft` at 1.0) leave the left eye open. The UE curve → morph wiring is fine; the left blink shape keys on the source body mesh need fixing in Blender and re-import. (CURRENT_STATE's "Blink — WORKING" is only true for the right eye.)

## H4 — motion

- Visual confirmation still owed from 2026-09-23: hair rides the head while strands simulate (clip: turn, run, stop, jump).
- Re-read `bBoneSubdivisionCollisionOnly` on the live ABP.
- **Gate:** clip with no scalp gap, no strands through her face or shoulders, settle within ~1 s after stop.

## H5 — water layer

- FluidNinja droplets (`VFX_HairFlow`): bigger sprites, stronger aqua from the Nikki palette, trail length matched to hair length.
- FLIP drip (`WaterHairFlipCache`): still references the retired water MI → move it to a Nikki-lane MI (owner picks the look); finish alignment and visible-drip acceptance.
- **Gate:** isolated + in-context clip: the water reads on motion, settles at rest, and never covers the face.

## H6 — budget

- `stat gpu` / Insights in PIE at 1080p: FluidNinja ≤ 1.0 ms; hair (mesh + Kawaii + FLIP + particles) total recorded.
- **Gate:** numbers recorded; reduce sim resolution / particle count if over.

## H7 — finalize

- Final contact sheet: four PIE views + motion strip on Morning.
- Save every package; record in `CURRENT_STATE.md` (also correct its outdated slot-1 water-material line).
- Commit on owner OK. The 668 MB FluidNinja pack commit is a separate decision.

## Owner decisions

1. Pick the H2 hair look variant.
2. Approve the H3 face framing.
3. The FLIP drip's Nikki-lane look (H5).
4. Commit, and whether `/Game/FluidNinjaLive/` goes into git.
