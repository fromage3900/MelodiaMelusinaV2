# Melusina water hair — FluidNinja LIVE goal

**Goal:** Melusina's water hair visibly *flows*. A live FluidNinja sim rides her head, is stirred by
her own hair/head/hand bones, and drives a water-droplet/mist layer that trails and swirls as she
moves — layered on top of the existing hair, not replacing it.

**Execution SSOT:** `CURRENT_STATE.md`
**Runtime owner:** `BP_MelusinaJRPGCharacter` (canonical; `WaterHairMesh` on `CharacterMesh0` socket `head_x`)
**Installed pack:** `/Game/FluidNinjaLive/` (FluidNinja LIVE 5.8, content-only, copied 2026-09-24, not committed)

## Keep as-is (existing hair contract)

- `SK_MelusinaHair` + `ABP_Melusina_WaterHair` (Kawaii root `hair_root`, bangs-lift ModifyBones).
- Hair surface is on `M_Master_Nikki` (`MI_Melusina_Nikki_Hair`). Do not touch or reintroduce the old water material.
- `WaterHairFlipCache` (FLIP drip) stays (geometry only). Hair offset `(0, 144.1994, -15.9001)` roll −90 is inverse-bind — do not touch.
- No new master materials. FluidNinja output materials are MIs of the pack's own shipped masters.

## Ordered goal

### W0 — pack health
- FluidNinja core BPs (`NinjaLive`, `NinjaLiveComponent`, `NinjaLiveCore`) compile clean in this project.
- **Gate:** 0 errored FluidNinja blueprints.

### W1 — sim on Melusina
- DONE 2026-09-24: `WaterHairFluid` (`NinjaLiveComponent`) on `BP_MelusinaJRPGCharacter`, attached at the head.
- `CameraFacing` on; `InteractionWithOwnerActor` on; `InteractionBoneNamesExact` = hair strand tip bones + `head_x` + both hands.
- Sim area ~2 m around the head, resolution 256 (drop to 128 if W3 fails).
- **Gate:** PIE log/debug shows tracked bones > 0 and the velocity/density render target changes while she moves.
- **PASSED 2026-09-24 (PIE, L_MelusinaMorning):** NinjaLiveCore active, 17 tracked positions, 2 overlapping components (body + hair), BP compiles 0/0 and is saved.

### W2 — water layer output
- Drive a FluidNinja surface-aligned Niagara system (droplets + fine mist) from the component.
- Particle MI tinted from `MI_Melusina_Nikki_Hair`: BaseTint `(0.62,0.88,1.0)`, pearl `(1.0,0.92,0.96)`, shadow dream `(0.48,0.42,0.62)`.
- Additive/translucent, subtle — the hair silhouette stays the hero.
- **Gate:** PIE capture, running and idle: water visibly trails behind the hair on motion and settles at rest. No white quads (see white-square causes).
- **PARTIAL 2026-09-24:** `NS_Melusina_HairFlow` (copy of pack `NS_Area_Small_Moving_ZaxisDerivedFromVelocity`, Scale RGB = Nikki BaseTint) + `MI_Melusina_HairFlow_Sprite` (DefaultSpriteMaterial, Hardness −4) on `VFX_HairFlow` under `WaterHairFluid`; pack debug plane hidden (`ForceHideVisualizationMesh`). Isolated PIE (all other 54 Niagara hidden): droplets appear on motion and drift off behind her, none at rest — but they read small and near-white. Tune size/tint next. Frames: `Saved/Audit/melusina_hairflow_20260924/clip3_isolated/`.

### W3 — budget
- **Gate:** FluidNinja GPU cost ≤ 1.0 ms at 1080p in PIE (`stat gpu`); otherwise reduce resolution / particle count.

### W4 — lock in
- Save the BP and every new asset; record in `CURRENT_STATE.md`.
- Commit only with owner OK. The 668 MB FluidNinja content commit is a separate owner decision.

## Owner decisions (not in scope unless approved)

1. Feeding the sim render target into the hair's *surface* — would need a texture input on `M_Master_Nikki` (master edit, red tier).
2. Committing `/Game/FluidNinjaLive/` (668 MB, LFS).
