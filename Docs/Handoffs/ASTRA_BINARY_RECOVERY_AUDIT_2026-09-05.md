# Astra binary recovery audit — 2026-09-05

This document classifies the remaining GPT-6 Astra checkpoint delta after the source-safe PPV contract and audio-presentation source were reconstructed onto current `main` in PR #94.

Historical source branch: `codex/game-state-2026-09-04-checkpoint`

Relevant checkpoint commits:

- `94624ff7e984c1a57b493098079c7a595a354959` — lookdev/material/Starskiff saved-state checkpoint
- `c5efaba392bd03305b06203d416198790bceac3d` — Sea Above terrain/authored-dependency checkpoint
- `df9ca6a8a460e9ba848be9b4938ba418462efafd` — PPV contract + ocean presentation checkpoint
- `eb0db91d7e2a6d0687c9d576f093c3497ac9fa81` — evidence / explicit merge-conflict checkpoint

The detached Astra branch must not be merged wholesale.

## GREEN — source-safe reconstruction

The following work has been reconstructed on the fresh current-main branch `integration/astra-game-state-transplant-2026-09-05`:

- centralized PPV/shipping/lookdev contract (`Content/Python/ppv_contract.py`);
- gameplay PPV application and audio audit scripts routed through that contract;
- StarryNight hero stack confined to lookdev/regression maps;
- Sea Above explicitly included in gameplay PPV certification;
- `MelodiaAudioReactivePresentationSubsystem.cpp` Astra delta accepted after an isolated one-file tree test.

The C++ delta contains two bounded changes:

1. Oceanology `DeepScatteringColor` baseline is aligned to the repaired light-blue water instance (`0.205079, 0.715693, 0.630757, A 0.65`) instead of the stale dark-teal baseline (`0.05, 0.25, 0.30, A 0.15`).
2. The sole audio MPC writer publishes the consumer-facing aliases `BassIntensity`, `MidIntensity`, and `BeatTracker`. Current-main consumers already read `BassIntensity`/`MidIntensity`, so leaving these lanes unpublished creates silent-zero behavior.

This is source-safe but still requires a current UE 5.8 compile/runtime smoke before it is called runtime-proven.

## YELLOW — inspect in Unreal before accepting

### Lookdev/material/Starskiff packet (`94624ff7...`)

Binary LFS changes include:

- `Content/EnvSandbox/Materials/Instances/BlingVol3/MI_BlingVol3_06.uasset`
- `Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FrostBloom.uasset`
- `Content/EnvSandbox/Materials/Instances/Environment/MI_Env_Gold_Trim.uasset`
- `Content/EnvSandbox/Materials/Masters/M_LF_StainedGlass.uasset`
- `Content/EnvSandbox/Materials/Masters/M_Master_Nikki.uasset`
- `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset`
- `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha.uasset`
- `Content/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v7.uasset`
- `Content/EnvSandbox/Materials/Masters/SDF/M_SDF_MandelbulbSlice.uasset`
- `Content/EnvSandbox/Materials/Masters/SDF/M_SDF_Mandelbulb_Master.uasset`
- `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_BaseColor.uasset`
- `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_Normal.uasset`
- `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_Roughness.uasset`

Do not replace current-main copies from Git alone. Open the current asset and the Astra candidate in UE or compare editor-readable metadata/parameters first. Master materials receive the highest caution because later work may depend on them.

### PPV/ocean binary packet (`df9ca6a8...`)

Review individually in-editor before accepting:

- Oceanology project-owned material assets/instances changed in the checkpoint;
- `MPC_Cymatics_Driver.uasset`;
- `MPC_Melodia_Palette.uasset`;
- any companion PPV/material instance assets from the same checkpoint.

The source contract now exposes the intended ownership and parameter names, but the binary contents cannot be safely inferred from LFS pointers.

## RED — no automatic transplant

### Sea Above world / external-actor packet (`c5efaba3...`)

This commit is a large authored-world snapshot, not a normal source patch. It includes:

- `LV_SeaAbove_Prototype.umap`;
- a very large `Content/__ExternalActors__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype/...` set;
- Atlantis material instances;
- landscape/triplanar material assets;
- Sea Above PCG assets;
- pivot-fixed mesh derivatives;
- Gaea landscape/material state;
- world dressing and authored dependencies.

At least one external actor object is ~12.6 MB and many hundreds of actor packages are involved. A blanket transplant can silently replace later level authoring, actor transforms, data-layer membership, PCG state, landscape work, or world-partition ownership. Never cherry-pick or overwrite this packet as one unit.

The same checkpoint also contains useful Python utilities (grounding, phyllotaxis, triplanar/RNM, terrain-alignment and Gaea helpers). Those are source files and may be recovered later as a separate reviewed batch; they should not be used as justification to import the associated world binaries.

## Current UE workstation acceptance gate

Before PR #94 is merged as runtime-proven:

1. sync the workstation to the PR #94 head;
2. run a current UE 5.8 editor build;
3. run the PPV/audio read-only audits;
4. load Sea Above and confirm the gameplay PPV contract applies without StarryNight gameplay authority;
5. verify the ocean does not darken when the presentation subsystem ticks;
6. verify `BassIntensity` / `MidIntensity` are non-zero when their upstream signal is active;
7. inspect only the YELLOW binary candidates you actually need;
8. save and push approved binaries in small semantic commits with screenshots/read-back evidence.

## Recovery rule

> Source can be reconstructed. Binary world state must be re-proven.

Do not merge the detached Astra checkpoint wholesale, and do not use Git history cleanliness as a substitute for UE runtime evidence.
