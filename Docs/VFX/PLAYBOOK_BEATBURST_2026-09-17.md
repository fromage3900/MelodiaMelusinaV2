# PLAYBOOK ΓÇö BeatBurst AAA (Package B) ΓÇö 2026-09-17

**System:** `/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_BeatBurst`  
**Primary emitter:** `BeatStars`  
**MI:** `MI_NS_ChoralSheep_BeatStar` (parent `M_Niagara_MelodiaFlipbook`)  
**Bus:** `User.BeatPulse` ΓåÉ `CompanionComponent.ResonanceIntensity` (`BP_ChoralSheep` Event Tick)  
**Fix A:** CLEAN_FIXA ΓÇö SubUVAnimation **off**, SubImageSize **1├ù1** (material owns scrub).  
**Live this pass:** **BLOCKED_LIVE** (no Monolith/MCP on executor). Apply when editor bridge is up; **no save_packages**.

Cross-links: [`PLAYBOOK_FLIPBOOK_FIXA.md`](PLAYBOOK_FLIPBOOK_FIXA.md) ┬╖ [`Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md`](Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md) ┬╖ [`VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](VFX_BEATPULSE_BP_WIRE_2026-09-17.md)

---

## Intent (Infinity Nikki soft)

Beat hits bloom as soft fleece-adjacent star pulses ΓÇö readable at silhouette distance, gentle nose-close, never hard collision sparks.

## Target shape

| Slot | Guidance |
|---|---|
| Primary | `BeatStars` ΓÇö sprite, camera-facing, BeatStar MI |
| Secondary | **Γëñ2** extra emitters (e.g. soft wool mote puff + optional tiny glint). Prefer reuse `MI_NS_ChoralSheep_WoolMote`. Do not exceed 3 total enabled emitters. |
| Collision | **Soft fleece** ΓÇö settle against sheep fleece (dampen / soft stick), not hard world bounce. Prefer collision vs skeletal mesh / fleece channel with low restitution; kill or sleep on fleece contact. |
| Size curve | Scale driven by `User.BeatPulse` (0ΓåÆ1): rest ΓåÆ pulse peak ΓåÆ soft decay. |
| Emissive / glow | Intensity / emissive ├ù BeatPulse. Keep material FlipFPS ownership; **do not** enable Niagara SubUV. |

## Param wire (documented)

```text
BP_ChoralSheep Event Tick
  ΓåÆ Get CompanionComponent ΓåÆ Get ResonanceIntensity
  ΓåÆ Set Niagara Variable (Float) User.BeatPulse on NS_ChoralSheep_BeatBurst
```

Inside NS: bind spawn rate / size / emissive curves to `User.BeatPulse`. Prefer single bus name.

## Live checklist (Monolith up ΓÇö read-only first)

1. Confirm emitter list; renderer MI = BeatStar (not WoolMote).
2. Pin-read: SubUVAnimation enabled=false; SubImageSize 1├ù1.
3. Confirm `User.BeatPulse` (float) exists.
4. Apply soft collision + size/emissive curves + Γëñ2 secondaries **without** SubUV.
5. List dirty packages for owner ΓÇö **Ctrl+S** only.

### Intended dirty list (after live apply)

- `NS_ChoralSheep_BeatBurst`
- Secondary MIs only if newly created (prefer existing WoolMote)

## Quarantine (docs only)

Do not promote Stub/TEMP/Test NS into BeatBurst. Docs label only unless already owner-labeled on disk.

## Deferred

`NS_ChoralSheep_MotionTrails`, `NS_ChoralSheep_FluidSplash` ΓÇö out of Package B scope.

## Acceptance

- [ ] Soft fleece collision in PIE (no hard ping-pong)
- [ ] Size + emissive answer BeatPulse / ResonanceIntensity
- [ ] Γëñ2 secondary emitters
- [ ] Fix A intact (SubUV off, 1├ù1)
- [ ] Owner Ctrl+S; no Monolith save
