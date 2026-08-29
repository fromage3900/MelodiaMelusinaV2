# P0 Integration Map Six-Pass Playtest — 2026-08-29

## Scope and result

Requested: six separate PIE reviews on `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`, with each pass reviewed for play feel, fun, and animation quality.

Completed: 2/6. Passes 3–6 are **BLOCKED**, not passed: after Pass 2 the editor entered a reproducible game-thread crash loop while loading material expressions.

Authoritative crash:

```text
Assertion failed: Outputs.Num() == AttributeGetTypes.Num() + 1
[File: Engine/Source/Runtime/Engine/Private/Materials/MaterialExpressions.cpp]
[Line: 6633]
```

Fresh crash evidence:

- `Saved/Crashes/UECC-Windows-DFC743D64A6A52344CC4A9BCA7B64408_0000/`
- `Saved/Crashes/UECC-Windows-43BF993A4651DBB61486BA85A41658FD_0000/`
- `Saved/Crashes/UECC-Windows-43BF993A4651DBB61486BA85A41658FD_0001/`
- `Saved/Crashes/UECC-Windows-43BF993A4651DBB61486BA85A41658FD_0002/`

No gameplay or material asset was edited to bypass the failure.

## Pass 1 — Idle baseline

Evidence: `Saved/Evidence/P0_SixPass_2026-08-29/Pass01_Idle/`

- PIE launched on the integration map.
- Runtime pawn: `BP_MelusinaJRPGCharacter_C`.
- Runtime animation class remained `ABP_Melusina_Current`; no identity drift.
- 4 frames captured; 3 post-warmup frames valid.
- No Blueprint runtime error or `Accessed None`.
- The capture path logged two D3D12 render-target ensures at `D3D12RenderTarget.cpp:599`; therefore the pass result is **FAIL**, not certification.

### Feel and fun

The idle spawn is stable but not fun on its own. There is no immediately readable objective, interaction prompt, encounter pressure, or rewarding response. It feels like a presentation/test room rather than the opening beat of the intended Quill → battle → result loop.

### Animation and visual review

- The character silhouette is readable and the idle pose remains stable.
- Hair covers most of the face, weakening expression and character connection.
- The dark sleeve/arm surfaces sparkle/noise heavily.
- Skirt and body layers intersect or collapse visually around the hips and legs.
- The nearby red mannequin dominates the composition and reads as test content.
- Lighting is bright enough to inspect the character, but the environment has no authored route framing.

## Pass 2 — Forward locomotion

Evidence: `Saved/Evidence/P0_SixPass_2026-08-29/Pass02_Forward/`

- Forward movement was driven through live PIE on `BP_MelusinaJRPGCharacter_C`.
- `AddMovementInput` executed successfully against the live pawn.
- Runtime animation class remained `ABP_Melusina_Current`; no identity drift.
- 7 frames captured; 5 valid and 1 invalid after warmup, so capture validity failed.
- No Blueprint runtime error or `Accessed None`.
- Two D3D12 render-target ensures recurred; pass result is **FAIL**.

### Feel and fun

Movement response makes the scene more engaging than idle, but it still is not genuinely fun: the room provides no goal, obstacle, music-key payoff, battle transition, or meaningful choice. The input has a response, but no game loop follows it.

### Animation and visual review

- The locomotion pose changes and carries visible weight.
- The torso remains noticeably hunched during movement.
- Skirt deformation is the largest animation-readability defect: it pinches, folds sharply, and exposes inconsistent layer intersections around the legs.
- Hair continues to hide the face during motion.
- Camera framing drifts and does not consistently preserve a hero-readable profile.
- `Sky Light waiting on Shaders for final capture` is visibly overlaid, so these are diagnostic frames, not presentation-ready captures.

## Passes 3–6 — blocked

Planned passes:

3. Strafe and rapid direction reversal.
4. Jump/traversal transition and landing.
5. Rhythm-key/input responsiveness in the integration surface.
6. Longer mixed-input stability and overall fun/animation review.

None can be certified. The editor repeatedly crashed before a clean PIE session could begin, with the material-expression assertion above. Continuing to restart would risk unrelated dirty packages and would violate the P0 fail-and-stop rule.

## Closeout judgment

- **How did it feel?** Responsive at the basic movement layer, but unfinished and test-room-like.
- **Was it fun?** Not yet. The two completed passes expose movement but not the intended integrated gameplay loop, feedback cadence, or payoff.
- **How did the animations look?** Stable animation-class ownership and a readable broad silhouette, but weak hero presentation due to face-obscuring hair, hunched locomotion, severe skirt/layer deformation, noisy arm materials, and drifting camera framing.
- **Shipping status:** HOLD. Only 2/6 passes ran, both failed evidence criteria, and the editor crash blocks further live certification.

