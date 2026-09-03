# Next Polish — MI + Pawn wiring (spec, no editor mutation until heap fixed)

**Editor heap:** `Claireon` `C1076`/`C3859` on `ClaireonWidgetHelpers.cpp` etc. even `-SingleThread -NoUBA` — PCH heap. Game target `BS_GodFile` **Succeeded** 274s, so `MelusinaSorrowSeamComponent` is compile-clean. Editor needs `/Zm200` or `Claireon bEnabled=false` in .uproject for this lane; do not block veil work on it.

## MI spec — Sorrow Seam (to be created via `ClaireonMaterialInstanceTool_Create` when editor responsive)

- **Parent:** `M_Fabric_Melusina` `specs/materials/m_fabric_melusina.v1.json:9` (after `M_Fabric_Melusina` lands) or interim `M_Master_Toon_Universal` `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset:1` (lean fork). Prefer fabric parent.
- **Path:** `/Game/Melodia/Characters/Melusina/Materials/MI_Fabric_Melusina_SorrowSeam`
- **Params:** `SheenIridescence 0.18 default, 0.32 healed`, `MadokaRealityWarp 0 (Gate)`, `DreadPresenceWarp 0`, `BeatBreath 0`, driven by `UMelusinaSorrowSeamComponent` `Source/BS_GodFile/MelodiaIntegration/MelusinaSorrowSeamComponent.cpp:1`. All `0` → byte-identical.
- **Textures:** `T_Fabric_SorrowSeam_BC/N/ORM/Sheen/WindMask` per `m_fabric_melusina.v1.json:81` 5-channel contract; interim reuse `T_Melusina_Trail_BC` etc.
- **Slot:** `Trail` primary `sort 20` + `Shawl 10` share MID; component creates `CreateDynamicMaterialInstance(Idx)` on Trail mesh `SK_Melusina_V2_Trail_SorrowSeam` fallback `SK_Melusina_V2_Trail` `specs/melusina_sorrow_seam.v1.json:8`.

## Pawn wiring spec

- **Pawn:** `BP_MelusinaJRPGCharacter` `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` — alongside `MelodiaWardrobeComponent` (owner per `ORCHESTRA_CONVERGENCE`).
- **Component:** Add `UMelusinaSorrowSeamComponent` with `PaletteMPC = /Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` (47 scalars `TENSION:89`), `MendLerpSpeed 1.5`.
- **Lifetime:** `BeginPlay` finds PaletteMPC + lazily creates MID on Trail material index; `TickComponent PostPhysics` reads `DreadPresence/Dissonance/BeatPulse/TemporalJitter` via `GetParameterCollectionInstance`, `IsWorldHealed()` via `IsWorldChallengeCompleted(first_resonance_echo)` and lerps. No save/combat authority.
- **Validation:** PIE `L_MelusinaMorning` — at rest `Dread 0` → veil pastel identical; `TensionSustain` spike → warp without gameplay effect; piano `first_resonance_echo` → sheen 0.18→0.32 in 1.5s; save/reload persists via narrative flag.

## Niagara U1/U2 live steps (when heap fixed / Claireon disabled)

```bash
python Content/Python/wire_niagara_polish_u1u2.py --live  # Monolith 9316
# U1: validate_system NS_Melusina_Globules non-black, depth 25, soft, BioResponse
# U2: validate_system NS_Melusina_SwingTrail ribbon link-order, curl 120/0.6, width 22->2
# stat Niagara CPU <0.25 GPU <1.0 Tier1 pooled
```

## Build note

- Game `BS_GodFile` build OK proves veil component ships in package even if editor stalls.
- Next editor attempt: `Build.bat BS_GodFileEditor -NoUBA -SingleThread -WaitMutex` already tried → same heap. Fix: add `AdditionalCompilerArguments="/Zm200"` to `BS_GodFile.Target.cs` or set `Plugins/Claireon/Claireon.uplugin` `EnabledByDefault:false` for this lane.

