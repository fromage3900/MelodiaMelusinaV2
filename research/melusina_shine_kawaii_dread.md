# Melusina Shine — Kawaii Limits + Dread Register (First 2)

**Status:** Spec · **No editor mutation until probe green** · 2026-08-24

## 1) Kawaii limits binding — hair_root

**Asset:** `ABP_Melusina_WaterHair` `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md:13` 1× `AnimGraphNode_KawaiiPhysics` `hair_root`
**Current defect:** `Saved/Audit/melusina_hair_physics_chain.json` audit 2026-07-27 `KAWAII_PHYSICS_PLACEMENT_AUDIT:47` — no `LimitsDataAsset` bound. Exists: `DA_Melusina_HairCollisionLimits` + `DA_Melusina_SkirtCollisionLimits` `KAWAII_PHYSICS_PLACEMENT_AUDIT:17`.
**Baseline:** `Content/Python/tune_melusina_hair_kawaii.py:28` damping 0.42 / stiffness 0.14 / limit 46° — keep as water flow, do not retune until limits bound.
**Fixture:** `BP_KawaiiPhysicsPlacementProbe` `KAWAII_PHYSICS_PLACEMENT_AUDIT:58` — 6 checks `KAWAII_PHYSICS_PLACEMENT_AUDIT:61`: mesh+skeleton+AnimBP+limits+root, placement/readback, probe map, evidence envelope. Generic `BP_PhysicsPlacementSpawner` is pillow test only `KAWAII_PHYSICS_PLACEMENT_AUDIT:26` — do not use.
**Spec:** Bind limits DAs on node, verify compile + PIE spawn, reset/teleport/travel/teardown stable, battle `ABP_Melusina_JRPGPresentation` noted uncovered `KAWAII_PHYSICS_PLACEMENT_AUDIT:50`.

## 2) Dread register — presentation only

**Signal:** `TensionSustain` fast 4.0 attack / 0.35 release → `DreadPresence`, `DissonanceAmount=TensionSustain*2` `Docs/Handoffs/TENSION_AUDIO_REACTIVITY_2026-08-15.md:22` + OSC `/rhythm/tension` `:22`. Owner: `MelodiaRhythmReactivitySubsystem` (plugin) publishes `DreadPresence/DissonanceAmount` `TENSION:27`, game module owns BeatPulse/Phase per single-writer map `TENSION:22`. At 0 → byte-identical.

**MPC:** `MPC_Melodia_Palette` now 47 scalars incl DreadPresence/DissonanceAmount `TENSION:89` — verify via `add_tension_mpc_params.py:13` (add before verify).

**Material:** `MF_Madoka` already resampled `RhythmPulse→Mid` `TENSION:95` saved 15:50. Witch expansion `TENSION:108`: `MadokaRealityWarp` gate 0 + `TemporalJitter`→UV jitter + `DissonanceAmount`×0.5 lift + `DreadPresence`×0.35→OneMinus dim. 11 nodes `TENSION:122`. At 0: `Multiply_52=Constant_2` identical.

**Duck:** `SM_MelodiaTensionDuck` SoundMix `TENSION:224` Adjuster `SCL_Ambience` vol 1.0, C++ ducks -6dB at max dread (staged but not built `TENSION:70`). Created 22:3x `TENSION:237`.

**Gates:** `MelodiaReactivitySignalTests.cpp` TensionRegister + AtRestIncludesTension `TENSION:53`. Needs closed-editor build `TENSION:70` (header changes).

**Next:** re-export `MF_Madoka.t3d` baseline `TENSION:129` after build, then pie crossfade `fx_amb_quad_riverbed_*` + birdsong duck via `SM_MelodiaTensionDuck`.

