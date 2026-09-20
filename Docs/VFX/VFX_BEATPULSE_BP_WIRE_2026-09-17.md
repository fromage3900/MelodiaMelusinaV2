# BeatPulse BP wire — BP_ChoralSheep — 2026-09-17

Graph contract only. The nodes live in `BP_ChoralSheep` (`.uasset`, not in this
docs PR). Compile **UpToDate**, **0 errors**. Owner Ctrl+S; dirty packages = 0.

## Graph (EventGraph)

`Event Tick` → 6× `Set Niagara Variable (Float)` chain, in order:

1. `NS_ChoralSheep_BeatBurst`
2. `NS_ChoralSheep_HybridSparkles`
3. `NS_ChoralSheep_PetalCascade`
4. `NS_ChoralSheep_MotionTrails`
5. `NS_ChoralSheep_FluidSplash`
6. `NS_ChoralSheep_WoolMotes`

Data:

- `Self` → `Get CompanionComponent` (`MelodiaChoralSheepActor.CompanionComponent`)
  → `Get ResonanceIntensity` (`MelodiaCompanionComponent`)
- `ResonanceIntensity` → all six `InValue`
- Each `Get NS_*` → matching SetFloat `self`
- `InVariableName` = `User.BeatPulse` on all six

## Not in this PR

No Blueprint binary is committed here. PIE confirmation (drive music /
ResonanceIntensity and watch emitters pulse) and any `VFXRoot` reparent under
`SkeletalMesh` remain owner look calls.
