# Codex FX / Niagara / PPV handoff — 2026-08-01

## Read first

This is a bounded presentation/lookdev lane. Do not create a second gameplay, rhythm, beat, palette, quest, UI, save, encounter, or combat authority. The allowed flow is one-way:

`gameplay or existing music clock -> existing MPC / Niagara User.* parameter -> FX material -> PPV grade`

No FX, Niagara, or PPV completion event may gate input, dialogue, damage, turns, rewards, quests, saves, or progression.

## Ownership and allowed scope

Codex owns Niagara graph verification and Niagara candidate graph edits only. Allowed work is limited to candidate systems under `/Game/EnvSandbox/VFX/Candidates/`, exposed `User.*` parameters, and directly associated Niagara graph/material assignment verification required to prove the candidate renders as authored.

Do not modify gameplay or C++ source, UMG/UI, maps, actor placement, landscape, lighting, PCG, environment assets, hair code/assets, PPV attachment, `MPC_Melodia_Palette`, or source effects. Do not promote a candidate over a source effect. Do not alter camera or environment composition to make a candidate appear successful.

Claude/environment owner controls PPV attachment, ArtOfShader grade integration, environment/render A/B, fixed-camera approval, and any promotion decision.

## Verify current state directly

First inspect the assets in the editor and record direct evidence rather than relying on prior summaries:

- Sakura candidates remain under `/Game/EnvSandbox/VFX/Candidates/Petals/`.
- SDF candidates remain under `/Game/EnvSandbox/VFX/Candidates/SDF/`.
- SDF systems to verify: `NS_SDF_PulsingGeometry_Candidate`, `NS_SDF_ParallaxFish_Candidate`, `NS_SDF_ParallaxPulse_Candidate`, `NS_SDF_Foliage_Vine_Candidate`, `NS_SDF_Foliage_Grass_Candidate`, and `NS_SDF_Foliage_Bush_Candidate`.
- Confirm the controls are real bindings, not unused metadata: `User.SDFParticleCount`, `User.SDFParticleLifetime`, and `User.SDFLoopDuration`.
- Confirm `NS_SDF_ParallaxFish_Candidate` uses its dedicated `M_SDF_ParallaxFish_Niagara_Candidate` material and that the foliage candidates use `/Game/EnvSandbox/Materials/Niagara/M_SDF_Foliage_Niagara`.
- Verify Sakura candidate compilation and event receivers without changing source systems.

Record compile status, warnings/errors, exposed parameter bindings, material assignments, and asset paths for each changed candidate.

## Outline candidate correction

`M_PP_StorybookOutline_LookdevCandidate` was previously reported as byte-identical to the fixed master, so the claimed eight-direction sampling, brush taper, and local-depth normalization are not evidence of landed work. If the candidate code is being re-landed:

- build on the fixed buffer-UV, tap-clamp, and normal-edge `max()` corrections;
- do not revert to the pre-fix four-tap shape;
- do not treat `MI_StorybookOutline_PortfolioHero` with `FalloffEnd=9500` as an automatic solution to dense foliage;
- preserve the candidate/master distinction and record the exact material expression or HLSL delta.

Use the existing candidate A/B rig only as a visual comparison aid. Do not change map placement or promote the candidate based on static/compile evidence alone.

## PPV and translucency checks

With Claude’s active PPV and a settled fixed camera, recheck:

- SDF silhouette alpha remains readable;
- fish and petal translucency is not crushed into black;
- lilac/blush emissives and soft bloom remain legible;
- UI text, focus, and contrast remain readable because world PPV does not own widget styling;
- strong glitch/CRT/chromatic-aberration/bleach effects remain restricted to intentionally authored moments.

Capture source versus candidate A/B under the same camera, lighting, and render settings. Record whether the result is a visual pass, a targeted fix request, or still open. Do not shader-guess the unresolved approximately `0.70` screen rectangle; hand it back to Claude for diagnosis.

`MPC_PPBlending` and ArtOfShader assets remain Claude-owned. Do not replace `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` or add a second beat/palette controller.

## Performance evidence

Only with Claude/environment-owner approval, record fixed-camera GPU cost for source and candidate using the same scene and settings. Include capture conditions, candidate count, particle count/lifetime/loop values, and the observed delta. A performance number is evidence, not permission to change placement, density, landscape, lighting, or promotion status.

## Stop conditions

Stop and hand back evidence if:

- a requested change touches gameplay/UI/material/PPV attachment/maps/placements/hair/environment/landscape/lighting/PCG;
- a candidate requires a new clock, gameplay callback, completion gate, or authority path;
- visual approval would require changing camera composition or scene density;
- the candidate is only validated by an automated preview and not an editor fixed-camera view;
- SDF/petal alpha or translucency remains unresolved after the narrowest candidate-side check;
- the proposed fix would alter a source effect rather than a candidate.

## Required handback evidence

Return:

- exact assets inspected or changed;
- Niagara compile results and warnings/errors;
- exposed `User.*` binding evidence;
- material assignment evidence;
- exact outline candidate delta, if any;
- fixed-camera source/candidate A/B captures and PPV/translucency observations;
- GPU-cost conditions/results only if approved;
- explicit statement that no gameplay/UI/authority, map/placement, environment, hair, source-effect, or PPV-attachment work was performed;
- explicit promotion status: candidate remains parked unless Claude/environment owner approves it.
