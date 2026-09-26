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
  (remove the MorningIntro stand-in only after L3 passes). **Owner D2 ANSWERED 2026-09-26 evening:** ZenForestTest
  stays an exploration map; the P0 dungeon = the procedural room levels (`RD_*` RoomData → `L_*` levels under
  `Content/Melodia/Roguelike/`), to be expanded with PCG. Retarget H-1B/H-2 to the run world accordingly.
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
   **PART B — DONE 2026-09-26 evening (Hermes, in `ZenForestTest`, p4-opened + saved, unsubmitted).**
   Dungeon map per D2 = the procedural run world. Coordinator `RunArchetype` = `DA_RunArchetype_SlimeCore`.
   **8** anchors, one `Encounter_<id>` tag each, roster cloned from the working `Encounter_CrystalShard` anchor:
   6 × `BP_EnemyUnit_MelodySlime_C`, plus `Encounter_SakuraPhantom` (stage-0 threshold, stock `BP_WeakEnemy_C`)
   and `Encounter_CosmicSentinel` (final stage, stock `BP_BossEnemy_C`) — both were hardcoded by the run and had no
   anchor, so real play would have been refused at stage 0.
   **Archetype was rejected until its missing fields were authored** (`Melodia archetype validation error: Run
   archetype requires rooms / a difficulty definition`) — there were no `UMelodiaRoomDefinition` or
   `UMelodiaDifficultyDefinition` assets in the project at all. Added
   `Content/Melodia/Roguelike/Definitions/{DR_Grove_Threshold, DR_Grove_ResonantBridge, DD_SlimeCore}`; the rooms
   point at `RD_MelodiaGrove_V1/V2` because `MelodiaRoguelikeRunSubsystem.cpp:59` only trusts physically validated
   rooms (the non-Grove rooms still have no exits). Archetype also authored to **1 act × 3 stages**: its unedited
   2×6 default set `StagesPerDungeon=12` (`:443`) and the run no longer completed in 3 stages.
   **Proof:** `Melodia.Roguelike.Functional.ThreeStagePhysicalRoute` (PIE, ZenForestTest) → no validation errors;
   `stage 0 SakuraThreshold/SakuraPhantom → stage 1 Grove/SlimeRadianceWaltz → stage 2 Grove/CosmicSentinel`;
   `Melodia run: dungeon complete - Sir Melodious reunion spawned.`; Complete-phase / endless-offer /
   `bSirMelodiousAvailable` all pass. The only error left was the tests' own stale `AddExpectedError` for a CommonUI
   warning UE 5.8 no longer emits — now asserted absent (count 0) in both cases.
   **Gotcha for the next lane:** a fresh `BP_InteractionBattle` spawns with an EMPTY `enemyList`, so a
   string-replace no-ops and the level saves with unusable anchors. Clone a known-good roster struct instead
   (`import_text` on a donor element), then verify `export_text()` actually contains the intended class before saving.
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

---

## CLOSEOUT — 2026-09-26 night (owner: "close out, test everything, and fix naked Melusina")

### C-1 Naked Melusina in battle — party fix PROVEN; one new defect surfaced

**Symptom:** in the ZenForestTest battle Melusina appears naked.

**It was never an art problem.** The dressed battle unit exists and is fully authored:
`BP_MelusinaSwordsman_Presentation` references `SK_Melusina_V2_Body`, `_Shirt`, `_Skirt_R2`, `_Boots`,
`_Accessories`, `ABP_Melusina_Current`, `ABP_Melusina_WaterHair` and her VFX set.

**Two distinct causes, found in sequence — the first hypothesis was wrong and the live probe corrected it.**

**Cause 1 (C++, fixed):** `UMelodiaJRPGPartyBootstrapSubsystem::TrySeedPresentationUnit` gates its
Swordsman→presentation swap on one hardcoded class name:

```cpp
Controller->GetClass()->GetName().Equals("BP_MelodiaJRPGController_Config_C")   // -> return false, silently
```

`BP_MelodiaJRPGController_Config` and `BP_MelodiaJRPGPlayerController` are **siblings** under the template's
`BP_JRPGPlayerController`, and `BP_MelodiaJRPGGameMode` — the `GlobalDefaultGameMode` — spawns the **latter**
(confirmed live: controller is `BP_MelodiaJRPGPlayerController_C`). Fixed to match the controller's owning
package (`/Game/MelodiaIntegration/`), which survives Blueprint renames, and it now logs instead of declining
in silence.

**Cause 2 (data, fixed — this was the actual naked-Melusina):** a live PIE probe showed the party was
**`[Sir]` only** — `partyMembers=[BP_SirMelodiousPlayerUnit_C]`, `playerUnits={Sir}`, and both come from the
**controller Blueprint's CDO defaults**. Melusina was in no roster at all, and the stock Swordsman was gone too,
so the presentation swap had nothing to swap. `BP_MelodiaJRPGPlayerController` is now p4-opened and its default
`playerUnits` carries `BP_MelusinaSwordsman_Presentation` alongside Sir. Verified on disk: the package grew
98675→98883 bytes and contains both unit references. **Do not trust a same-session `load_asset` read-back of a
CDO you just wrote — it reported empty while the file on disk was correct.**

**Proof:** `Melodia.Integration.Functional.PartyPresentationUnit` now clears both of its own assertions —
Melusina's dressed unit is fielded, the stock mannequin is not. (It failed those assertions before the data fix,
so the test does pin the defect.)

**Cause 3 (NEW, open):** with a second unit actually fielded, the stock battle pawn's possess graph now runs and
dereferences a null AI controller:

```
Accessed None trying to read (real) property AIController in
/Game/TurnBasedJRPGTemplate/Blueprints/PlayerPawns/BP_JRPGCharacterBase.BP_JRPGCharacterBase_C
Node: Possess  Graph: EventGraph
```

This is stock-template content shared by the whole battle system, so it is **not** being edited unattended.
Two candidate fixes, owner's call: (a) null-guard that Possess node in `BP_JRPGCharacterBase`, or (b) give
`BP_MelusinaSwordsman_Presentation`'s pawn an AI controller / `AutoPossessAI` so the read is valid.

**Also unexplained, worth one probe:** `TrySeedPresentationUnit` still logs nothing at runtime even with the gate
fixed — the subsystem appears never to be invoked on this path, so the C++ swap remains dormant and the data fix
is what is actually carrying the party. Worth confirming whether that subsystem is registered at all.

### C-0 Jev plan-audit of this closeout (2026-09-26 night, `source=jev-live`)

One `system_one` call, closed option sets, full distributions. State assembled from the proven facts above plus
live probes. Script: `%LOCALAPPDATA%\hermes\cache\scratch\jev_closeout_audit.py` (read-only; mutates nothing).

| Question | Choice | Confidence | Distribution |
|---|---|---|---|
| AIController fix | **`DEFER_TO_OWNER`** | 0.56 | DEFER 0.70 · GIVE_UNIT_AICONTROLLER 0.27 · GUARD_STOCK_BP 0.03 |
| Next block | **`FIX_AICONTROLLER_THEN_SUITE`** | 0.32 | FIX_AICONTROLLER 0.49 · COOK_FIRST 0.41 · SUITE_THEN_FIX 0.05 · HOLD 0.05 |
| Riskiest | **`ROOM_LEVELS_NOT_COOKED`** | 0.40 | ROOM_LEVELS 0.55 · AIMED_TEMPLATE_REGRESSION 0.24 · COOK_MEMORY 0.21 · SILENT_SUBSYSTEM 0.00 |
| Owner gate? | **yes — noul 0.93** | — | gated |
| Readiness | **1 = "risky"** | — | 1.0 on that level |

**What the audit changes.** (1) The AIController block is owner-gated (0.93), so it is *not* executed
unattended — it is handed over with evidence. (2) Between the two candidate fixes Jev puts the unit-scoped
`GIVE_UNIT_AICONTROLLER` (0.27) far above the stock-template edit `GUARD_STOCK_BP` (0.03), independently
matching the read that shared template content should not be edited to accommodate one unit. (3) The
dominant risk is **not** the template regression (0.24) but the **cook** (0.55): room levels absent from
`MapsToCook` while streamed by soft path. That risk is retired by *running* the cook and inspecting the
package, which needs no owner approval — so it is the block being executed. (4) Jev rates the whole closeout
"risky" (readiness 1), which is honest: the packaged build has never passed on this machine.

### C-2 PLAN OF RECORD — supersedes the earlier C-2 ordering (written 2026-09-26 ~21:5x)

**Source-control reality check first, because the owner's question assumed a state that does not hold.**
Verified this session, not assumed:

| Claim | Truth |
|---|---|
| Prior lanes' last-24 h work committed and merged | **YES** — 34 commits, 9 merges, `main == origin/main` at `77b7d40f9` |
| **This session's** work committed | **NO** — 11 files are **staged only**, never committed |
| This session's content submitted to p4 | **NO / unverifiable** — p4 session expired; nothing submitted |
| 12 task assets present on disk | **YES — 12/12** |
| …of those, holding a second copy (git or p4) | **NO — 0.** `Content/*` is gitignored (`.gitignore:113`), so **the working tree is the ONLY copy** |
| Editor unsaved packages | 0 — closed clean, no dirty packages, so no in-memory loss vector |

**So the honest answer to "is everything from the last 24 h committed and merged with no lost work": the prior
lanes' work is; this session's is not, and 12 assets are single-copy on one disk.** That is the real exposure —
and note it is *not* a git problem. Git holds the 11 staged files in the index and the working tree. The
12 content assets are the ones with no second copy anywhere.

**Order of work.** Step 1 is the only thing that is genuinely urgent, and it is not the suite:

1. **`p4 login` (owner) — then immediately reconcile + submit the 12 task assets.** This is the single action
   that converts the only single-copy work in the project into work with a server-side copy. Do it *before* any
   further authoring. List: `Content/ZenForestTest.umap`; `Content/Melodia/Roguelike/Archetypes/
   DA_RunArchetype_SlimeCore.uasset`; `Definitions/{DD_SlimeCore, DR_Grove_ResonantBridge, DR_Grove_Threshold}`;
   `Encounters/ENC_Slime{Fortissimo,GaleTroupe,RadianceWaltz,SorcererSweep,Stalagmite,TideCurrent}`;
   `Content/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController.uasset`.
   **Do not** reconcile the owner's Morning work in the same pass — it is a separate change with a live deleted
   external actor.
2. **The two p4-blocked edits, then closed-editor build, then the suite.** (a) `Config/DefaultGame.ini`:
   `+DirectoriesToAlwaysCook=(Path="/Game/Melodia/Roguelike")`. (b) `BP_JRPGCharacterBase.uasset`: the Possess
   null-guard — safe because `K2Node_CallFunction_21` is terminal. Then build, then `Automation RunTests
   Melodia.`, expecting **107–108/108**.
3. **Full packaged cook** to settle the open room-level question, which only a green `-stage -pak` package can
   answer. Expect it to still fail on the owner's `L_MelusinaMorning` (editor-only `MeshPartition` import from
   the deleted external actor) until that is resolved — that is the owner's call, not a silent fix.
4. **Git commit last, not first.** Jev scores holding the staged set at 0.65 versus 0.34 for committing
   source+docs only and 0.01 for committing all eleven now, because a commit that leaves the suite red on a
   known single root cause misrepresents the state. So the commit lands *after* step 2 turns the suite green —
   and it should carry a message that names the stock defect rather than implying the P0 is closed.
5. Docs: `CURRENT_STATE.md` is the only status document; this file is the runbook. No new status files.

**What was deliberately NOT done, and why.** No `git add -A` (it would have staged the owner's deleted
external actor). No `chmod`/`attrib` around Perforce (writes p4-controlled content outside p4). No commit or
push (owner approves; Jev's guidance is to hold). No claim that the room-cook question is answered — two
attempts to prove it were invalid and the decisive artifact does not exist.

### Carried-forward defects (do not silently absorb)
- **Single-copy exposure:** 12 content assets exist only in this working tree until step 1 lands. This is the
  highest-consequence open item in the project right now, and it outranks the red suite.
- `TwentyFiveGenerationSoak` trips its own 240 s budget at 3–5 FPS after generating all 25 rooms. Machine-speed
  dependent; raising it is the owner's call, not a quiet gate edit.
- Cause 3 above: stock `BP_JRPGCharacterBase` possess graph null-derefs `AIController`. One root cause behind
  all three suite failures.
- `git status` carries the owner's unsubmitted Morning work, including a **deleted** `L_MelusinaMorning`
  external actor — which is also the sole cook blocker. Untouched.
- 5 git stashes exist from earlier deliberate parks (2026-09-19 → 09-23). Intentionally parked, not lost work.
- `UMelodiaJRPGPartyBootstrapSubsystem` still logs nothing at runtime even with its gate fixed, so its swap
  path may be dead code and the CDO data fix may be the only thing carrying the party.
- Claireon proxy still reports `active_editor: null` even with `-EnableMCPProxy`; Monolith on :9316 works.
- Non-Grove rooms have no exits, which is why the runtime only trusts `RD_MelodiaGrove_V1/V2`.
- `Source/BS_GodFile/MelodiaMultiWorldGameViewportClient.cpp/.h` are untracked and belong to an earlier lane,
  not this task. Review before anyone commits.
