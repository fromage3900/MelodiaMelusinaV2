# Melusina Shine — Full Plan (Cozy→Demented, UE 5.8)

**Owner:** Melusina (abyssal mermaid, cute + dread) · **Spine:** `SK_Melusina` + `ABP_Melusina_Current` + `ABP_Melusina_WaterHair (hair_root)` + V2 wardrobe + `M_Master_Toon_Universal`
**Rule:** 0 at rest = byte-identical. No second combat authority. Subagents one task only.

## Delegated Task (Subagent 1): Fabric OIT + BOOTH Hair Pack

**Scope:** Author specs for sheer-fabric master + curate 2 BOOTH hair mods. No editor writes.

| Item | Spec | Evidence |
|---|---|---|
| Fabric master OIT | Create `M_Fabric_Melusina` parent with OIT for sheer shawl/trail (slots Body/Hat/Gloves/Shawl/Trail/HairCharm per MelodiaWardrobeComponent). BaseColor/Normal/ORM + fuzz + wind masks. Reduce variants vs Universal. | `INFINITY_NIKKI_PIPELINES_2026-08-14.md:21`, `UE58_TOON_MATERIAL_INTAKE_2026-08-08.md:188` |
| BOOTH hair | Reika Abyss Empress + Velvet Thorn Drill Twintails (booth.pm 8622261/8546007) + existing 0JPY perches (4561230/5475631) with 5-section PROVENANCE.md + SHA256 per `asset_recommendations.md:159` | `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md:12` |
| Deliver | `research/melusina_shine_fabric_booth.md` + `specs/materials/m_fabric_melusina.v1.json` + `Imports/BOOTH_Hair_*.md` drafts |

## Main Agent — First 2 (Now): Kawaii Limits + Dread Register

### 1) Kawaii limits binding (hair_root)
- **File:** `ABP_Melusina_WaterHair` `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md:13` — 1× `AnimGraphNode_KawaiiPhysics` root `hair_root`
- **Fix:** Bind `DA_Melusina_HairCollisionLimits` + `DA_Melusina_SkirtCollisionLimits` (exist) to node, keep `damping 0.42/stiffness 0.14/limit 46°` `tune_melusina_hair_kawaii.py:28`
- **Probe:** `BP_KawaiiPhysicsPlacementProbe` `KAWAII_PHYSICS_PLACEMENT_AUDIT:59` — map persist, root-body compat, PIE reset
- **Gate:** Kawaii placement audit steps 1-6

### 2) Dread register (presentation only)
- **Signals:** `TensionSustain` (attack 4.0/release 0.35) → `DreadPresence`, `DissonanceAmount=TensionSustain*2` `TENSION_AUDIO_REACTIVITY_2026-08-15.md:22` + OSC `/rhythm/tension`
- **MPC:** `MPC_Melodia_Palette` 47 scalars `TENSION:89` — add if missing `DreadPresence/DissonanceAmount/TemporalJitter`
- **Material:** `MF_Madoka` `MaterialExpressionCollectionParameter` resample `RhythmPulse→Mid` done `TENSION:95`; add `MadokaRealityWarp` gate `TENSION:108` → UV jitter × `TemporalJitter` + baseline lift × `DissonanceAmount` ×0.5 + dim × `DreadPresence` ×0.35 →1-minus. At 0 → `Multiply_52 = Constant_2` byte-identical
- **Duck:** `SM_MelodiaTensionDuck` `TENSION:224` SoundMix Adjuster `SCL_Ambience` vol 1.0, C++ pulls -6dB at max dread (staged `MelodiaRhythmReactivitySubsystem`)
- **Gate:** tension register tests `MelodiaReactivitySignalTests.cpp`

## Remaining 7 (Queued, not this turn)
3 SDF relief + AudioReactiveFX 02 (trail/boots gated), 4 Niagara Water Hair v10 T0-T4, 5 Dataflow panel cloth (outer skirt hybrid), 6 Audio-reactive wardrobe (VJ Master spectrum), 7 VRM4U MToon repoint (3 VRMs staged), 8 Substrate Toon spine polish

