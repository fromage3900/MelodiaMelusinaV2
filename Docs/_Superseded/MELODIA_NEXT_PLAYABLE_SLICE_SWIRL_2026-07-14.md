# Melodia — Next Playable Slice: Swirl Token

Date: 2026-07-14

## Proven in PIE

- The roguelike run now targets three stages.
- Stage 0 offers the Heart Melody Token. With persistent party HP at 40, selecting it consumed the token and restored HP to 70.
- Stage 1 offers the Swirl Melody Token as the middle reward candidate.
- During the stage-1 encounter, a basic action raised SP from 1 to 2. Selecting Swirl consumed one token and restored 2 SP, producing 4 persistent SP.
- A stage-2 encounter then hydrated its combat state with 4 SP. This proves the reward persists across encounters.
- The native module built successfully for `BS_GodFileEditor Win64 Development` with UE 5.8.

## Not Yet Proven / Remaining P0

1. **Physical three-stage traversal**
   - Repeat the full test using the placed room-exit volume for both transitions.
   - Confirm the procedural generator reports completion for each generated room set.
   - Confirm there are no overlapping encounter triggers or stale battle controllers after unload/reload.
   - Current direct subsystem advancement enters `Generating`; it does not itself drive the coordinator. This is expected for the test shortcut but needs an automated authoritative traversal test.

2. **Player-facing encounter interaction**
   - Replace test-only function calls with the intended overlap/interact/input route.
   - Add a clear encounter prompt, lockout while battle is active, and completion feedback.

3. **Reward presentation and controls**
   - Give Heart and Swirl distinct icon, color, description, and selection animation.
   - Verify keyboard, mouse, and controller focus; prevent double selection.
   - Surface the immediate stat delta (`SP +2`) and current/max SP.

4. **World token presentation**
   - Use the existing Melody Token mesh and Swirl texture/material for a brief 3D reward reveal.
   - Add pickup audio, musical particle spiral, and a short HUD fly-to-SP animation.

5. **Room anchors and transition safety**
   - Add explicit entrance, encounter, reward, and exit anchors to every room.
   - Spawn the player at the entrance anchor after generation.
   - Keep the exit disabled until reward commitment and generation readiness.

## P1 — Make the Loop Sellable

- Author three visually and mechanically distinct room recipes instead of repeating the Grove layout.
- Give each stage a distinct enemy or modifier package and readable escalation.
- Turn dissonance into a combat modifier: rhythm-window pressure, audiovisual corruption, and meaningful risk/reward—not global color grading alone.
- Author the Sir Melodious reunion beat after the final victory, then enable companion state for the next run.
- Add deterministic seed display, run summary, restart, defeat, and abandon-run paths.
- Add a functional automation test covering: start run → three encounters → two rewards → two exits → reunion → complete.

## Acceptance Gate for the Next Review

The next slice is reviewable only when a player can complete all three rooms without editor/test calls, see Heart and Swirl feedback, carry HP/SP into subsequent encounters, cross both physical exits, and reach Sir Melodious without a crash, stuck phase, duplicate encounter, or null battle controller.
