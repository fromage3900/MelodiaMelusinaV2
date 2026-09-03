# Session closeout — Niagara, lookdev, and PPV boundaries

**Date:** 2026-08-01  
**Status:** Candidate assets compile cleanly. No candidate was promoted or attached to a live Zen Forest PPV/UDS setup during this session.

## Scope respected

- No environment geometry, landscape, lighting, level map, UDS runtime setting, gameplay authority, or `MPC_PPBlending` asset was changed by this pass.
- `PPV_NikkiDream` remains on the established source materials:
  - `/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline`
  - `/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade`
- Claude owns PPV attachment, `MPC_PPBlending`, and the eventual temporary-PPV A/B. Kiro owns gameplay/UI integration and must only trigger visual FX after authoritative outcomes.

## Verified visual/render state

- The fixed outline master rendered cleanly after its 11:31 save in the supplied post-fix recording: settled frames show readable green grass and sky, no black rectangle, and no ink blowout.
- ~~Motion-only streaking is not evidence of a view-rect/UV error because it disappears once the camera settles.~~
  **SUPERSEDED 2026-08-01 (Claude).** That reasoning was mine and it was wrong — a later capture
  showed the same ~0.70 boundary in a near-settled frame. It is a real buffer-vs-view-rect issue and
  it is **still open**: an editor restart made buffer and view sizes match, which *masks* it, and a
  1920×1080 engine capture from a differently-sized viewport reproduced it in the render. This blocks
  portfolio captures at any non-viewport resolution. Fix identified but not applied — the tap clamp
  bounds the buffer where it must bound the view rect. Full write-up in
  `PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md`.
- ~~Custom Depth requires `r.CustomDepth=3` to be persisted.~~ **DONE 2026-08-01.** `r.CustomDepth=3`
  is committed to `Config/DefaultEngine.ini` with owner approval and verified reading `3` in-editor.
  Kiro's stencil values 1/2/3 are now a live path.

## Niagara: verified candidate assets

- `NS_SakuraPetals_v3_Candidate`: clean diagnostics. CPU source and event receivers are intentional for the death-event landing chain.
- `NS_SakuraPetalPiles_Candidate`: clean GPU diagnostics; bounded burst pile candidate.
- `NS_SurrealSakuraGust_Candidate`: clean GPU diagnostics; `StandardPetalGust` and sparse `HeroNaniteCrossings` are separate emitters.
- All six SDF candidates compile with zero Niagara warnings/errors, GPU simulation, fixed system bounds, and common user controls for intensity, seed, count, size, lifetime, loop duration, wind, reaction, and audio inputs.
- Legacy replacement candidates exist for Fairy Dust, Magic Trail, Rain Ripples, Ember Motes, and Dream Sparkle. They remain unpromoted rollback-safe candidates.

### Niagara work still requiring live sign-off

1. Per-actor Zen Forest candidate placement/swap after identical-camera A/B.
2. Verify one landing event yields one intended ripple or pile, without local-origin output.
3. Verify SDF silhouette alpha and translucent petal readability through the active PPV.
4. Record Standard and Hero GPU cost from a fixed Zen Forest camera.

## Lookdev material reality check

- `M_PP_StorybookOutline_LookdevCandidate` is currently a **straight duplicate of Claude's corrected master**, including the fixed buffer-UV/clamp/max behavior. It is not an eight-direction rewrite; do not describe it as one or judge the A/B as an algorithm comparison.
- Its three profile instances are real parameter-tuning assets. Portfolio Hero currently increases `FalloffEnd` to 9500 and enables vines at `0.18`; this will outline farther foliage more strongly and must be treated as an authored Hero/capture choice, not a gameplay default.
- `M_PP_MeluColorGrade_LookdevCandidate` is a distinct candidate graph/custom grade and compiled successfully. Its Gameplay, Narrative, and Portfolio instances exist.
- `M_Melodia_StarryNight_UDS_Candidate` is currently a candidate duplicate of the authored Starry Night material with three profile instances. It is not attached to UDS and does not yet consume the new sky MPC.
- `MPC_MelodiaSkyLookdev_Candidate` exists as a separate visual-only collection with neutral values for night, cloud, moon, weather, wind, sky intensity, and Hero state. It does not replace UDS or touch `MPC_PPBlending`.
- `BP_MelodiaLookdevDirector_Candidate` compiles cleanly and is an **unplaced profile registry**, not an active runtime director. It has no PPV/UDS write path.

## Existing project scope and ownership

- UDS remains the authority for time, weather, sun/moon, clouds, fog, and skylight.
- JRPG/QuillScript/save/quest/input ownership remains unchanged; all work here is presentation-only.
- Additive/translucent Niagara is outside the depth/normal outline contract. Do not add opaque depth-writing particles without Claude review.
- Stencil guidance for Kiro: values are per-component, clear them to zero on death/pooling/teleport, use only 1/2/3 for styled output, and never read stencil state back as gameplay authority.

## Clean next-session gates

1. Persist Custom Depth-Stencil as Enabled with Stencil.
2. Claude attaches matching source/candidate pairs to a temporary PPV only; do not replace `PPV_NikkiDream` until visual approval.
3. Run same-camera A/B at morning, sunset, clear night, and cloudy night, including moving-camera stability and SDF/petal translucency.
4. If a true edge-algorithm upgrade is still desired, create a new outline candidate from the fixed master, verify exported HLSL and graph fingerprint after each edit, then report only what the asset proves.
5. Build the UDS adapter only after the sky material is deliberately wired to `MPC_MelodiaSkyLookdev_Candidate`; no live UDS or PPV attachment is implied by the existing candidate assets.
