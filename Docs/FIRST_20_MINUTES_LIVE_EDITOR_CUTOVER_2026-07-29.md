# Melodia — First 20 Minutes Live-Editor Cutover

**Updated:** 2026-07-29  
**Purpose:** a small, testable fixed-loop slice for the afternoon editor session. This is the current execution authority; the older `MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md` remains an authored north star, not a prerequisite list.

## The playable promise to finish

```text
Main Menu
  -> New Game creates MelusinaSlot0
  -> Morning room / Sir interaction
  -> Dreamstate traversal
  -> Zen Forest guided walkway
  -> one Quill-requested stock JRPG battle
  -> one typed result resumes Quill
  -> post-battle world change + save
  -> fully restart and Continue proves the result persisted
```

The route must feel intentional for roughly twenty minutes, but it does not require procedural expeditions, a second combat controller, direct companion flight, or a new persistence schema.

## Static evidence already in place

- Startup and game default maps are both `L_MelodiaMainMenu`; the configured GameInstance is `BP_MelodiaJRPGGameInstance`.
- Packaging includes Main Menu, Morning, Dreamstate, ZenForestTest, MelodiaIntegrationMap, and the narrative directory.
- New Game is live-proven by the project owner and uses the canonical stock `BP_JRPGSaveGame` slot `MelusinaSlot0`.
- The live character Blueprint contains `MelodiaTraversalComponent`; Space is mapped to `MelodiaTraversalJump` and tilde is the configured `OpenMenu` key.
- The UMG recovery gate and the active menu/battle route audit both passed after the current native build. See `Saved/Audit/critical_ui_recovery.json` and `Saved/Audit/active_frontend_and_battle_routes.json`.
- The active landscape master is the restored authored master with the additive Living Storybook lane; its integrity audit passes 91/91. This does not substitute for in-level visual and frame-cost sign-off.

## What is still required before calling the slice working

### P0 — route and reliability

1. **UMG recovery in a real session.** Open ZenForestTest and start play without the former UMG assertion.
2. **One complete terminal battle.** Confirm one stock Battle UI, one active Melusina mesh, one attack animation, one 4.5-second stock impact, one damage/target result, and one turn release.
3. **Narrative exit.** In the Quill-backed encounter, capture exactly one `MELUSINA_LOOP_BATTLE_COMPLETED`, `MELUSINA_LOOP_QUILL_RESTORE`, and `MELUSINA_LOOP_QUILL_NEXT`; the post-battle dialogue/world state must appear once.
4. **Canonical restart proof.** Save outside battle, fully stop play, launch again, Continue, and prove the completion flag/reward is present exactly once. Do not claim persistence from a same-session load alone.
5. **Walkable authored route.** The Morning-to-Zen Forest route needs a player-readable main path, recoverable collision, no fall-through/softlock locations, and a clear destination before the encounter.

### P1 — high-value polish immediately after the route is stable

- **True double-tap glide:** current code is a second press *after descent begins*; it has no configurable double-tap window. It will not read like Infinity Nikki if the player taps twice immediately. This is a contained native input fix, pending a closed-editor rebuild.
- **Battle command legibility:** the native keyboard legend is safe and compiled, but it must be seen in the actual Quill/JRPG battle host. Confirm whether legacy controller glyphs remain confusing before changing any stock widget again.
- **Duplicate-player cleanup:** the repair compiles, but a real battle must prove the old grey JRPG mesh is hidden and only Melusina presents.
- **Menu completion:** New Game and Continue are the only verified controls. Add a lightweight Settings/Options surface after persistence is proven; keep it presentation-only and do not move save ownership.
- **Opening readability:** add the short VN/dream beat between New Game and the controllable room only after the stable route works end to end.

### P2 — capture and finish work

- Import only complete authored PBR sets (base color, normal, ORM, height) into the documented landscape contract, then sign off close/traversal/distant views.
- Tune Melusina's new rig, cloth physics, and authored attack montage after the one-mesh routing proof; retain the stock 4.5-second impact timing.
- Add final contextual interaction, collectible, quest, and SFX feedback only once each along the finished walkway.

## Live-editor lane for level authoring

While this document is active, the environment lane may safely author geometry, collision, route markers, and local set dressing. Keep these boundaries:

- Build one unmistakable **primary walkway** from the player spawn toward the next story/battle landmark; use a strong distant silhouette, a near interaction cue, and one recovery route at any drop/fork.
- Put the first meaningful interaction on the natural forward path, not behind a blind turn. A player should receive a visual or sound confirmation within 10–15 seconds of entering each new area.
- Use collision volumes deliberately: block accidental sequence breaks, allow a forgiving edge near traversal jumps, and provide a visible return path rather than a kill/fall reset where possible.
- Do not edit World Settings, GameMode, GameInstance, stock Battle UI, map travel, or the active landscape master while building the route. Report any needed change as a handoff instead.
- Preserve a small, clean 16:9 capture sightline at the room, the first Zen Forest reveal, and the battle approach.

## Recommended afternoon test order

1. **Stability (2 minutes):** open the project, compile only prompted assets, start ZenForestTest once, and record whether the prior UMG assertion returns.
2. **Core route (5 minutes):** New Game -> Morning/Sir -> Dreamstate -> Zen Forest. Record any map transition, collision, or input failure immediately rather than working around it.
3. **Battle proof (5 minutes):** trigger the single encounter. Check mesh count, attack readability, keyboard hints, impact timing, terminal result, and Quill resumption.
4. **Persistence proof (3 minutes):** save after battle, stop play completely, Continue, and check the result/reward once.
5. **Authoring (remaining time):** assemble the primary walkway and its sightlines. Retest only the portion touched.

## Evidence to hand back after testing

- A screenshot or short note for the first frame that fails, with map name and action.
- Output Log lines beginning `MELUSINA_LOOP_` for the completed encounter.
- Whether Space twice behaves as expected, and whether the player can see both a grey default mesh and Melusina in battle.
- One before/after Zen Forest route frame when the walkways are in place.

## Next closed-editor implementation queue

1. Add a configurable double-tap interval to `UMelodiaTraversalComponent` while preserving one authoritative exploration input path.
2. Address only the confirmed active battle-host UI issue (keyboard cue or legacy glyph suppression) with a presentation overlay, never a structural stock Battle UI rewrite.
3. Add Settings/Options as a separate main-menu presentation route; retain `AOrreryMainMenuGameMode` as the New Game/Continue and canonical-save boundary.
4. After the PBR maps arrive, run the documented material integrity/capture pass and record Standard-tier shader/GPU numbers.
