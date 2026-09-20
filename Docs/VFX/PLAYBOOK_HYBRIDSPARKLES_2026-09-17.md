# PLAYBOOK — HybridSparkles AAA (Package B) — 2026-09-17

**System:** `/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_HybridSparkles`  
**Emitters:** `FlipSparkles` · `SoftGlints`  
**MIs:** `MI_NS_ChoralSheep_BeatStar` (FlipSparkles, CLEAN_FIXA) · `MI_NS_ChoralSheep_WoolMote` (SoftGlints, CLEAN static 1×1)  
**Bus:** `User.BeatPulse` ← `ResonanceIntensity`  
**Fix A:** FlipSparkles SubUV **off**, SubImageSize **1×1**. SoftGlints stays non-flipbook.  
**Live this pass:** **BLOCKED_LIVE**.

Cross-links: [`PLAYBOOK_FLIPBOOK_FIXA.md`](PLAYBOOK_FLIPBOOK_FIXA.md) · [`Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md`](Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md)

---

## Intent

Near-field sparkle density with far-field calm — flipbook twinkle + soft wool glints. Music raises spawn; slight orbit keeps life around the companion.

## Target shape

| Concern | Guidance |
|---|---|
| LOD near | Higher spawn, SoftGlints visible |
| LOD far | Cull / heavily reduce SoftGlints; FlipSparkles spawn floor low but non-zero |
| Spawn | `spawnRate = baseRate × User.BeatPulse`. Pulse=0 near-idle; Pulse=1 dense but fill-rate safe. |
| Orbit | Slight orbital / curl around sheep / VFXRoot — low angular speed, small radius jitter (companion aura, not vortex). |
| Emitter count | Keep FlipSparkles + SoftGlints; no third emitter without owner look call. |

## LOD sketch

1. Niagara scalability / distance LOD: Near (<~800 uu) both emitters; Far (>~2500 uu) SoftGlints off, FlipSparkles spawn ×0.25–0.4.
2. Or custom float from BP — prefer Niagara LOD if project scalability already covers NS.

## Param wire

Tick → ResonanceIntensity → `User.BeatPulse` on this NS. Multiply spawn (and optional orbit strength) by BeatPulse.

## Live checklist (Monolith up)

1. Read-only: emitters + MI edges.
2. Fix A pin-read on FlipSparkles.
3. Wire spawnRate × BeatPulse; add slight orbit.
4. Tune near/far LOD.
5. Dirty list → owner **Ctrl+S**.

### Intended dirty list

- `NS_ChoralSheep_HybridSparkles`

## Quarantine

Docs-only for Stub/TEMP/Test NS. Do not fold test sparkle systems into HybridSparkles.

## Deferred

MotionTrails, FluidSplash.

## Acceptance

- [ ] Near/far LOD readable on camera pullback
- [ ] Spawn scales with ResonanceIntensity / BeatPulse
- [ ] Slight orbit; no SubUV regression
- [ ] Owner Ctrl+S
