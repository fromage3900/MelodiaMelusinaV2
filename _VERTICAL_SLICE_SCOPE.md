# Active Vertical Slice Scope — First Dream

**Status:** production-foundation closeout before combat expansion  
**Authority:** `Docs/MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md`  
**Playable route:** `L_MelusinaMorning` → `L_Melodia_Dreamstate` → `/Game/EnvSandbox/Environments/L_KaleidoNave`  
**Real paths:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` → `/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate` → `/Game/EnvSandbox/Environments/L_KaleidoNave`  
**KaleidoNave transition:** Travel node retargeted 2026-07-30 from `/Game/ZenForestTest`; `+MapsToCook` added to `DefaultGame.ini`. Open item: KaleidoNave's merged Dreamstate BPs don't function on arrival (`_DECISION_LOG.md` 021b) — diagnose before routing the playtest through it.

> **Corrected 2026-07-31.** This line previously read *"DefaultGame.ini intentionally NOT modified."*
> That is no longer true: `+MapsToCook=(FilePath="/Game/EnvSandbox/Environments/L_KaleidoNave")` **was**
> added to `DefaultGame.ini` (see `_SESSION_HANDOFF.md`, "Route change"). The intent behind the
> original sentence still holds — the Blueprint travel node, not the config, decides the
> *destination*; `MapsToCook` only ensures the cook covers the route however it is sequenced.
> The "Playable route" lines above are now synced (2026-07-31) to the KaleidoNave destination;
> the open item is the arrival-side BP fallout (021b), not the destination itself.

> This document supersedes the historical Phase 2/SakuraDream/MelodiaCore scope. That plan predated the working JRPG/Quill route and is not an active implementation instruction.

## Product goal

Ship a compact Persona-lite loop whose mechanics are readable, intentional, and enjoyable:

```text
sanctuary conversation
  -> authored departure
  -> short dream traversal
  -> one stock JRPG encounter
  -> typed terminal result
  -> narrative consequence
  -> stable checkpoint/save
```

The loop is allowed to stay small. If a mechanic does not improve the player’s decisions, feedback, attachment, or flow, remove or defer it.

## Proven now

- Morning Sir interaction presents visible Quill dialogue.
- Dialogue completion gates the single native departure/travel path.
- Dreamstate loads under `BP_MelodiaJRPGGameMode` and is traversable.
- The route reached `/Game/ZenForestTest` in continuous PIE; destination retargeted to `L_KaleidoNave` on 2026-07-30, whose arrival-side BP fallout (`_DECISION_LOG.md` 021b) is the open item.
- Dreamstate has one tagged stock `BP_InteractionBattle` root and its required spawn cluster.
- `BP_MelodiaJRPGGameInstance` is selected by project configuration, and asset export confirms narrative sync/restore nodes exist in its stock-derived graph; runtime call order and persistence are not yet proven.
- `WBP_MainMenu` Kenney/Soft-MG presentation is **in progress, not complete** (checked against the live widget tree via Monolith 2026-07-31: it was a bare `CanvasPanel` with a plain `Image` background and stock `Button`s, no Kenney border, no custom texture, until this session started applying one — `Background` image is now set to `T_Melodia_SoftMG_Parchment`, but buttons are not yet styled). Next step: brush treatment for buttons across all 4 states (Normal/Hover/Pressed/Disabled). Real graph chains exist for New Game, Continue, and opening Save/Load. Continue and Load Game remain disabled until canonical slot and Save/Load-screen PIE gates pass.

> **Corrected 2026-08-06.** Per the project owner's live verification on 2026-08-06, the "Proven now"
> bullets above are **NOT currently reproducible**: Quill dialogue is not visible, battle systems are
> non-functional, and the game is unplayable. The known-good state behind these bullets predates the
> Melodia integration and the UI overhaul. Until PIE proof is recorded, every bullet above is
> re-tagged as **unverified** — treat none of them as current runtime fact. The bullets themselves are
> left unchanged as the historical record; do not rewrite them.

## Foundation gate before combat expansion

All items below are binary gates:

- [ ] Identify the instantiated stock battle widget package at runtime.
- [ ] Prove Attack/Skill/Item/Flee mouse, keyboard, and controller parity without duplicate execution.
- [ ] Pass Victory, Defeat, Fled, and unavailable; each resumes/aborts Quill exactly once.
- [ ] Create and load a canonical `BP_JRPGSaveGame` slot across a full process restart.
- [ ] Prove one narrative flag and one reward restore without duplication.
- [ ] Load the canonical JRPG slot with Quill unavailable and preserve all JRPG-owned state.
- [ ] Route a missing/unknown script or checkpoint to an explicit authored safe location without erasing valid current state.
- [ ] Test interpreter invalidation during terminal-result broadcast; retain a recoverable pending result if Quill resume fails.
- [ ] Keep manual saving disabled or unavailable during an active narrative battle.
- [ ] Wire Main Menu New Game, Continue, and Load to the canonical JRPG GameInstance before making it a startup screen.
- [ ] Repair or intentionally revise the `Morning_RoomShell` validator contract.
- [x] Identify/isolate the overlong or invalid serialized name causing cook exit 25. — `PCGEx_PathTesselate.uasset`, invalid name at index 411; Decision 022, 2026-07-30.
- [x] Package the proven three-map route. — `Saved/StagedBuilds_20260730/`, 2.1 GB, all five maps, `Success - 0 error(s)`.
- [ ] **Launch**-test the packaged route outside the editor. Still open: packaging is not launching.

## Co-op skill gates (2026-07-29)

- [x] `BP_MelusinaPetalCadence` — stock `BP_BattleSkillBase` child, mapped to Melusina at level 1, applies Resonance buff.
- [x] `BP_SirSkyboundRefrain` — stock `BP_FocusAttack` child, mapped to Sir at level 1.
- [x] `BP_Resonance` — stock `BP_BuffBase` child, one-turn duration, referenced in Petal Cadence's `buffs` array.
- [ ] Wire Skybound Refrain's conditional bonus when Resonance is present on target.
- [ ] Author Sir's battle mesh, portrait, and `skillAnimation` entry for Skybound Refrain.
- [ ] PIE-test: Petal Cadence once → Resonance applied → Skybound Refrain once → bonus damage → turn release. Also test Sir without Resonance (normal damage).

## Hair fix gates (2026-07-29) — resolved 2026-07-31, do not re-touch

- [x] Hair bone analysis: body (465 bones) and hair (148 bones) share zero bone names — Copy Pose From Mesh cannot work.
- [x] Native C++ fallback staged in `UMelodiaHairComponent`: attach hair to `head_x`, retain Kawaii Physics below `hair_root`.
- [x] "Hair only" combat body visibility fix staged: defer redirect by one tick so battle Blueprint hides mannequin before visible Melusina mesh becomes montage target.
- [x] Run closed-editor native build to bake both fixes. — build green 2026-07-31.
- [x] Verify hair attaches to `head_x` in PIE. — `MELUSINA_HAIR_SOCKET` verified 2026-07-31 (`_ROADBLOCKS_2026-07-31.md` C6); do not re-apply correction properties.
- [ ] Verify Melusina's full body is visible in combat (not just hair). — still open; folds into the PIE route test.
- [ ] Long-term: re-export hair against body armature with matching bone names for CopyPose-first setup.

## Combat-expansion slice

After the foundation gate passes, expansion is limited to:

1. Make the active stock command UI readable, focusable, and visually consistent.
2. Preserve the stock JRPG controller as turn, target, damage, result, inventory, and save authority.
3. Add one meaningful combat decision at a time and playtest it before adding another.
4. Improve hit, damage, break, result, and companion feedback without making rhythm mandatory.
5. Keep one enemy/encounter until its complete decision loop is fun.
6. Add tests to the result matrix when a new terminal path is introduced.

## Explicitly deferred

- A second combat or save framework
- Procedural roguelike/run authority
- Broad enemy roster or boss pipeline
- Open-world/environment expansion
- Wardrobe platform, crafting, achievements, or multiplayer
- Rhythm as required battle authority
- Broad settings, inventory, quest, or party UI suites
- Front-end map replacement before menu behavior passes

## Flow/QOL priorities

1. Deterministic focus and input-mode transitions.
2. No stale dialogue, battle HUD, cursor, or movement input after transitions.
3. Stable pre-battle and post-result checkpoints; no mid-battle save.
4. Continue is disabled when no canonical slot exists and explains why.
5. Short transitions, skip-safe dialogue, and no duplicated confirmation steps.
6. Clear result/reward feedback before returning control.

## Stop rule

Combat expansion stops whenever a new mechanic fails to make the existing encounter more readable or more enjoyable. Fix, simplify, or remove it before adding scope.
