# Astra game-state transplant — 2026-09-05

This packet reconstructs the useful **source/text** portion of the GPT-6 Astra game-state checkpoint onto a fresh branch from current `main`.

## Source branch and evidence boundary

Historical Astra branch:

`codex/game-state-2026-09-04-checkpoint`

Relevant Astra checkpoint commits:

- `94624ff7e984c1a57b493098079c7a595a354959` — lookdev/material/Starskiff saved-state checkpoint
- `c5efaba392bd03305b06203d416198790bceac3d` — Sea Above terrain/authored-dependency checkpoint
- `df9ca6a8a460e9ba848be9b4938ba418462efafd` — PPV shipping contract + compiled ocean presentation checkpoint
- `eb0db91d7e2a6d0687c9d576f093c3497ac9fa81` — saved-state evidence + explicit merge conflicts

The historical branch does not share a clean merge ancestry with current `main`, so it must **not** be merged wholesale.

## Reconstructed first slice

Fresh integration branch:

`integration/astra-game-state-transplant-2026-09-05`

This first slice restores only the low-risk PPV contract/source work:

- `Content/Python/ppv_contract.py`
- `Content/Python/apply_dream_candidate_ppv.py`
- `Content/Python/bind_ppv_audio_contract.py`
- `Content/Python/finalize_ppv_hero_stack.py`
- `Content/Python/setup_nikki_render_post_process.py`
- `Content/Python/strip_ppv_color_overrides.py`

The contract separates three surfaces that older scripts conflated:

```text
PACKAGED_SHIPPING_MAPS
GAMEPLAY_PPV_CERTIFICATION_LEVELS
LOOKDEV_REGRESSION_LEVELS
```

The gameplay stack is now explicit and centralized. `StarryNight_Hero` remains cinematic/lookdev-only rather than silently becoming gameplay shipping authority.

## Deliberately deferred

No blanket `.uasset` / LFS transplant is part of this slice.

Deferred for explicit in-editor review:

- Sea Above terrain and authored-dependency asset state from `c5efaba3...`
- lookdev material masters/instances from `94624ff7...`
- Starskiff hull texture state from `94624ff7...`
- Oceanology material assets introduced around `df9ca6a8...`
- `MPC_Cymatics_Driver.uasset`
- `MPC_Melodia_Palette.uasset`

These binary assets may overlap newer current-main authoring and should be accepted individually only after UE inspection.

The Astra-era C++ delta in `MelodiaAudioReactivePresentationSubsystem.cpp` is also deferred until it is compared against the current-main subsystem rather than replaced wholesale.

## Historical proof vs current proof

The Astra checkpoint recorded a successful UE 5.8 editor build (`Result: Succeeded`, 13 build actions, ~46.41 s). That is useful historical evidence, not proof that this reconstructed branch is currently green.

Before merge, current-main validation should include:

1. Python syntax/import check for the PPV scripts.
2. In-editor read-only PPV/audio audit.
3. Verify Sea Above is present in the gameplay certification surface.
4. Confirm StarryNight hero authoring does not target gameplay shipping maps.
5. Current UE editor/build smoke before claiming runtime green.

## Rule

> Recover contracts first. Review binaries separately. Never merge the detached Astra checkpoint wholesale.
