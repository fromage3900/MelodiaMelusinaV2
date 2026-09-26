# GOAL — PCG loss check · 24 h review · Sir Melodious switch + perch · stable P0 dungeon loop (2026-09-26)

Owner ask: "verify any PCG work we may have lost, final check and review on all gameplay and work done in
the past 24h, and next necessary steps for: Sir Melodious party member switch and his model as a perchable
explorable unit (cockatoo, flies), and a stable core P0 loop with the established procedural dungeon
mechanisms and melody slime enemies and variants."

**Bound:** verify, review, and land the smallest content-first steps on EXISTING systems. No new dungeon
generator, no new party system, no new enemy framework. Routing per `.jcode/swarm-prompt.md` lanes;
editor work = Hermes-in-Claireon one at a time; Claude verifies artifacts.

## G1 — PCG: nothing is lost (verified 2026-09-26, read-only)
- `Content/Melodia/PCG/MassiveBiome` 7/7 and `Content/Massive` 206/206 assets on disk **and** in p4;
  `PCG_Biome_{MorningMeadow,RockScatter,CrystalGarden}` + `DA_Melodia_{MorningBiome,RockScatter,CrystalGarden}`
  present; `p4 diff -sd` on `Content/EnvSandbox/PCG` = nothing missing.
- Universe Foundry crystals (`SM_FloatingCrystal_*`, `MI_FloatingCrystal_Iridescent`, static-field
  textures) on disk and in p4. **Git-only leftovers** on unmerged `feature/universe-foundry-ue-staging-20260922`
  (4 commits): `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md` additions, `…hython_canon_20260922.json`,
  `faraway_alignment_diagnostic.py` → **G1a** small PR (docs/tools only; binaries already in p4).
- **At risk = owner's unsubmitted Morning edits in the p4 default CL:** `BP_Morning_GoldenSpiral`
  (PCG-driven) edited, `MassiveSandstoneCliff_01` actor deleted, 2 actors added → **G1b owner:** submit or
  shelve (`p4 shelve`) so a revert can't eat them.
- **G1c (Hermes, editor):** open `L_MelusinaMorning`, regenerate `Massive_Biome_Meadow`, screenshot vs
  `Saved/Audit/massive_morning_20260924/` (expect ≈992–996 instances, 0 floaters). Artifact = PNG + count.

## G2 — Review of the last 24 h (29 commits on `main`, PRs #328–#336, p4 CL 225–229)
| Landed | Proof level | Still owed |
|---|---|---|
| Overworld HUD, minimap/compass, orrery chassis | live PIE | — |
| Compendium W1, Motion Grammar | live PIE (3 entries) | kit art, thread-clear bug |
| Rhythm windows 45/80/120, calibration, highway HL1–5 | gate PASS 01:06 | owner calibration tap-run |
| #51 fixes + tests | main 104/106 headless | rung 3 restart (owner), rung 4 package (re-run, OOM fixed) |
| Jump/glide arm-at-press (main), ABP JumpWindup removed | build + compile | PIE feel check |
| Agent lanes / jcode fleet / Hermes rules | router live PASS | Ollama chat endpoint hangs (restart app) |
- **G2a (fleet, `deep` lane = `moonshotai.kimi-k2-thinking`):** read-only review of
  `git diff 2cb5eb9a4..origin/main -- Source Plugins/MelodiaCore/Source` → findings JSON; Claude verifies each
  finding against the code before anything is filed. Stale Echo rows (runtime 08-13 …) stay owed to the ladder.

## G3 — Sir Melodious: party switch, then perchable flight (content-first)
**Exists:** `UMelodiaJRPGPartyBootstrapSubsystem::RecruitSirMelodiousThroughStockParty` (idempotent, unlocks
flight after the stock party accepts him); `UMelodiaPartySubsystem` `SwitchToNext`/`SetActiveIndex`/
`IsSirMelodiousExplorationUnlocked` (Ctrl); `AMelodiousFlightCharacter` (always `MOVE_Flying`, WASD+pitch,
Space ascend, Shift boost, Ctrl back); `BP_SirMelodious_Flight`, `ABP_SirMelodious`, `SK_SirMelodious_Rigged`,
one retargeted clip `Animations/FreeCameraTrackingframeupdate_Anim_RT`. Recruit is gated: `NotifySirRescued()`
only in phase `FirstDungeonUnlocked`, and its dungeon caller `MelodiaDungeonRunCoordinator` is placed in no map.
- **S1 Prove the switch (Hermes, editor, `MelodiaIntegrationMap`):** PIE → `RecruitSirMelodiousThroughStockParty`
  → unlocked → Ctrl → flight pawn possessed → fly → Ctrl back. Artifact: log lines + 2 screenshots. Fixes
  only if it fails.
- **S2 Anim (Jev 0.9 "wire the existing clip first"):** flight clip into `ABP_SirMelodious` locomotion; perch
  idle clip is **owed** (no Sir source blend — Jev's riskiest item) → Blender/Rokoko lane, not today.
- **S3 Perch (smallest new capability, on the existing pawn):** in `AMelodiousFlightCharacter`, a downward trace
  on landing input finds a surface tagged `Perch` → `MOVE_Walking` + perch state (ABP bool) → Space takes off.
  Content-first: tag 3–5 perch actors in Morning (fence, bell tree, house roof). **Owner decision D1:** any
  walkable surface vs authored `Perch`-tagged surfaces only (recommend authored — readable, testable).
- **S4 Tests:** `Melodia.Party.SirSwitchRoundTrip` + `Melodia.Flight.PerchLandTakeoff` (headless where possible).

## G4 — Stable P0 core loop: procedural dungeon + melody slimes
**Exists:** `UMelodiaRoguelikeRunSubsystem`, `MelodiaDungeonRunCoordinator`, `MelodiaFirstDungeonGate`,
`MelodiaDungeonRecipeConsumer`, `RoguelikeRoomCustomData`, persistence + reward widget, `MelodiaEnemyBase`/
`EnemyDefinition`; `DT_MelodySlime_{Enemies,Skills,RoomMods}` (row structs in `MelodiaSlimeDataRows.h`);
slime tutorial authored 09-18 (`MelodiaQuillSlimeTutorial`, `DA_MelodySlimeTutorialSongs`) — **PIE proof owed**;
`RD_MelodiaGrove_V1`; `Melodia.Roguelike.*` tests (2 known headless-only failures).
Loop: Morning → FirstDungeonGate → procedural run (rooms + slime encounters/variants from the DTs) → rhythm
battle → reward → `NotifySirRescued` → return home → save.
- **L1** Place `MelodiaDungeonRunCoordinator` (+ gate) in the dungeon map so Sir's rescue has its real caller
  (remove the MorningIntro stand-in only after L3 passes). **Owner D2:** which map is the P0 dungeon.
- **L2** Slime variants: verify the three DT `.uasset`s import non-empty against their row structs; each room
  mod resolves an enemy definition (fleet `code` lane: offline check script over the `.json` twins + a
  headless test). Stray duplicate `Content/Content/Melodia/DataStuctures/*.json` → owner to delete.
- **L3** One real-key golden run (owner): gate → 3 rooms → 2 slime battles (1 variant) → reward → Sir
  rescued → home → save → restart proof (#51 rung 3 doubles as this). Artifacts → fresh Echo rows.
- **L4** Run `Roguelike.Functional.ThreeStagePhysicalRoute` + `TwentyFiveGenerationSoak` **with a viewport**
  (in-editor, not headless); triage the `BP_SkillUseDialogue` Accessed None if it recurs.

## Frontier models on this Bedrock account (live 2026-09-26, Mantle)
Answering: `moonshotai.kimi-k2-thinking` (best long reasoning/review), `zai.glm-5`, `moonshotai.kimi-k2.5`,
`deepseek.v3.2`, `mistral.mistral-large-3-675b-instruct`, `qwen.qwen3-235b-a22b-2507`, `qwen.qwen3-coder-480b`.
`access_denied`: `openai.gpt-6-sol/-luna`, `gpt-5.6-sol` (request access). Claude: not cleared. `xai.grok-4.3`:
chat route unsupported, Responses route timed out — unproven.

## Order
G1b (owner, now) → G1a + G2a + L2 (fleet, parallel) → S1 → L1 → S2/S3 → L3 golden run → L4.
**Done =** G1 closed, G2 findings verified, S1 + L2 proven, D1/D2 answered, L3 scheduled.

## Execution log — 2026-09-26 afternoon (Claude session; editor on `MelodiaIntegrationMap`)
- **S1 DONE + bug fixed.** Recruit → switch → fly worked, but **Sir → Melusina silently did nothing**: index 0
  (game-mode-spawned `BP_MelusinaJRPGCharacter`, stock `BP_JRPGCharacterBase` child) never self-registers and
  roster slot 0 has no class, so `EnsurePawn(0)` returned null. Fix in `UMelodiaPartySubsystem::SetActiveIndex`:
  register the pawn being left at `ActiveIndex` when that slot is empty. Live Coding patch OK; PIE round-trip
  Melusina→Sir→Melusina→Sir→Melusina: possession + view target follow every hop, `MOVE_FLYING` on Sir,
  no Accessed None / BP runtime errors. Camera boom (520 uu) makes the cockatoo read small → tune in S3.
- **L2 verified (and the real G4 gap found).** `DT_MelodySlime_Enemies` 48 rows (`MelodiaSlimeEnemyRow`),
  `_Skills` 31, `_RoomMods` 21 — import fine, **but zero referencers**: no `UMelodiaRoguelikeEncounterDefinition`
  asset exists, room `EnemyPool`s are empty (`RD_BossArena_V1` custom data = bare `RoguelikeRoomCustomData`,
  `RD_MelodiaGrove_V1` none). Only enemy asset: `/Game/Melodia/Enemies/CrystalShard/BP_CrystalShard_SlimePlaceholder`.
  24 `RD_*` rooms + `BP_RoguelikeDungeonGenerator` + `BP_DungeonFloorManager` + `BP_MelodiaDungeonRunCoordinator` exist.
- Pre-existing, not P0: CDO warnings — `MelodiaTokenPickup` can't find `MI_MelodyToken_Heart`,
  `MelodiaSmokeCharacter` can't find `/Game/Melodia/Characters/Melusina/SK_Melusina`.

## Jev ruling for the next sessions (live `jev-1.13.0`)
| Question | Ruling | Conf |
|---|---|---|
| Re-run the packaged cook | **after slime wiring**, so the package proves the loop | **0.91** |
| First Hermes-in-Claireon task | author slime encounter defs + room pools | 0.56 |
| Sir perch vs dungeon wiring | perch first | 0.45 (conflicts with row 2 — row 2 wins) |
| Slime wiring method | hand-author ~6 representative encounters first | 0.29 (weak — owner may override) |

## HERMES RUNBOOK — follow in order, one task per session, stop on any red flag
Start every session: `git fetch && git status` (must be `main` == `origin/main`), read `AGENTS.md` BINDING RULES,
confirm exactly one `UnrealEditor` process and that the open level is `MelodiaIntegrationMap` (closed-editor
tasks: `Tools\issue51_ladder.ps1 preflight` instead). Access GI subsystems in PIE Python via
`unreal.find_object(None, gi.get_path_name()+'.<SubsystemClass>_0')` (`gi.get_subsystem` is not exposed).
1. **H-1 Slime encounters — PART A DONE 2026-09-26 (Claude, saved):** `/Game/Melodia/Roguelike/Encounters/ENC_Slime{Fortissimo,
   TideCurrent,GaleTroupe,SorcererSweep,RadianceWaltz,Stalagmite}` (lowest-HP row of 6 elements; Umbral later) +
   `/Game/Melodia/Roguelike/Archetypes/DA_RunArchetype_SlimeCore` (`Encounters` = those 6, `Rooms` empty → the run
   falls back to the physically validated Grove rooms). **Real runtime chain (read from source — room `EnemyPool`
   is NOT on it):** `AMelodiaDungeonRunCoordinator.RunArchetype` → `ApplyArchetype` → archetype `Encounters` →
   `EnemyIds` → stage `EnemyId` → every `AMelodiaEncounterTrigger` in the room → bridge
   `StartTaggedJRPGBattle("Encounter_<EnemyId>")` → a level actor **tagged `Encounter_<EnemyId>`** (stock
   `BP_InteractionBattle` carrying its own `offLevelBattleData` + `enemyList`; same contract as the highway gate's
   `melodia_smoke_encounter`). Unknown tag ⇒ "Stock JRPG bridge refused encounter" and no battle.
   **PART B (needs owner D2 = dungeon map):** in that map, 6 `BP_InteractionBattle` actors tagged
   `Encounter_Slime<Row>`, enemy list = the template slime unit(s) under `Content/_PROJECT/Characters/Enemies`
   (tint/scale per element later); set the placed coordinator's `RunArchetype` = `DA_RunArchetype_SlimeCore`.
   **Done when:** PIE run log shows `EnemyId=Slime…` for stage 1 and "Encounter routed to tagged stock JRPG battle (Slime…)".
2. **H-2 Coordinator in the dungeon map (editor, owner D2 names the map).** Place
   `BP_MelodiaDungeonRunCoordinator` (+ `MelodiaFirstDungeonGate`). PIE: complete a run → `NotifySirRescued`
   returns true → Sir recruited without the MorningIntro stand-in. Artifact = log lines + screenshot.
3. **H-3 Packaged proof (closed editor).** `ollama stop <all>` → `Tools\issue51_ladder.ps1 preflight` →
   `package` → `launch`. Artifact = `Saved/Audit/issue51_ladder_<date>/launch.json`.
4. **H-4 Sir perch — owner D1 = authored perch BPs (2026-09-26).** One content class `BP_SirPerch` (`/Game/Melodia/Characters/SirMelodious/Perch/`): a `PerchPoint` scene component (landing spot + facing), actor tag `Perch`, optional glint VFX. `AMelodiousFlightCharacter` gains a land input: nearest `Perch`-tagged actor within ~300 uu → snap to its `PerchPoint`, `MOVE_Walking`, ABP perch bool; Space takes off. Place 3–5 in Morning (fence, bell tree, roof) — ask first, Morning is Red. `AMelodiousFlightCharacter`: land on `Perch`-tagged surfaces
   (owner D1), `MOVE_Walking` + ABP perch bool, Space takes off; shorten the boom for a cockatoo. Test
   `Melodia.Flight.PerchLandTakeoff`. Flight clip into `ABP_SirMelodious` (Jev 0.9).
5. **Owner-only:** restart proof (#51 rung 3, real keys), calibration tap-run, Morning p4 default-CL edits.
**Red flags → stop and report:** a second editor/agent on the editor; any `.uasset` outside the task's paths
dirtied; `Accessed None`/BP runtime errors after a change; a need to touch `Config/`, masters, `L_SakuraPath`
or `L_MelusinaMorning` layout; any git/p4 push/submit (owner approves).
