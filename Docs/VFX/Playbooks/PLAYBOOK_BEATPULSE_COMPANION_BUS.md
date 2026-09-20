# Playbook — BeatPulse companion bus

One writer into Niagara user params on Choral Sheep. Do not add a second audio
or BeatPulse writer.

## Live graph (`BP_ChoralSheep` EventGraph)

Compile **UpToDate**, 0 errors (2026-09-17). Binary is the Blueprint `.uasset`
(not in the docs PR).

```text
Event Tick
  → Get CompanionComponent (Self)
  → Get ResonanceIntensity
  → 6× Set Niagara Variable (Float)
       InVariableName = User.BeatPulse
       InValue        = ResonanceIntensity
```

Order of Set Niagara Variable:

1. `NS_ChoralSheep_BeatBurst`
2. `NS_ChoralSheep_HybridSparkles`
3. `NS_ChoralSheep_PetalCascade`
4. `NS_ChoralSheep_MotionTrails`
5. `NS_ChoralSheep_FluidSplash`
6. `NS_ChoralSheep_WoolMotes`

Each `Get NS_*` feeds that node's `self`. Pin-level receipt:
[`../VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](../VFX_BEATPULSE_BP_WIRE_2026-09-17.md).

## Owner — reparent VFXRoot

If not already: reparent **`VFXRoot` under `SkeletalMesh`** so the six systems
follow the sheep mesh, then Ctrl+S `BP_ChoralSheep`.

## PIE check

Drive music / `ResonanceIntensity` and confirm emitters pulse. Optional: a
SurrealFabric MI on a plane (Lane D lookdev).

## Niagara AAA follow-through

Use the shipped Package B playbooks **without** reintroducing Niagara SubUV:
BeatBurst → HybridSparkles → PetalCascade. MotionTrails / FluidSplash remain outside
that bounded polish pass. See [`../PLAYBOOK_BEATBURST_2026-09-17.md`](../PLAYBOOK_BEATBURST_2026-09-17.md),
[`../PLAYBOOK_HYBRIDSPARKLES_2026-09-17.md`](../PLAYBOOK_HYBRIDSPARKLES_2026-09-17.md), and
[`../PLAYBOOK_PETALCASCADE_LEAFPILLE_2026-09-17.md`](../PLAYBOOK_PETALCASCADE_LEAFPILLE_2026-09-17.md).

## Do not

- Publish `User.BeatPulse` from a second Blueprint, MPC writer, or tick on another actor.
- Confuse this bus with ConstellationDraw **Dream\*** user params (separate).
- `save_packages` from Monolith; owner Ctrl+S.
