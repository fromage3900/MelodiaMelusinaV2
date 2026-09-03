# Kiro + Claude + Cline evening core-loop handoff

**Date:** 2026-08-01 evening  
**Goal:** close one complete First Dream loop without adding a second gameplay authority:

`New Game → Morning Quill choice → Harmony → quest/marker → Dreamstate → stock JRPG encounter → result → Quill resume → KaleidoNave → save → full process restart → load`

Use `Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md` as the acceptance script. This handoff assigns execution; it does not replace that test.

## Start-of-session truth

Already proven:

- Closed-editor `BS_GodFileEditor Win64 Development` build is green.
- The four project Quill WBPs exist, have the correct native parents/bindings, and freshly compile with 0 errors and 0 warnings.
- Petal Priestess `FScriptSettings` and Selection `ChoiceEntryClass` read back to the expected generated classes.
- Priestess Quill compiles to 26 statements and contains exactly one stable Harmony intent:
  `melodia:stat:priestess_first_echo:melodia_harmony:1`.
- Persisted quest 2 requires both `melodia_q_echo_01` and `melodia_harmony >= 1`.
- Authored Blueprint travel legs use `UMelodiaTravelSubsystem::TravelTo`; the two stock `currentMap` save/restore legs deliberately retain `OpenLevel` per Decision 028.
- Exactly 49 `Melodia` automation tests are registered. Historical baseline is 46 pass / 3 known failures.
- A staged packaged build exists, but its executable has not been walked outside the editor.

Not yet proven:

- NPC interaction reaches the intended Quill scene in the runtime route.
- Harmony/quest/reward/consumed-intent state survives a full process restart.
- The actual instantiated battle widget package and mouse/keyboard/controller parity.
- Victory, defeat, fled, and unavailable result branches each resolve exactly once.
- Portal/death travel fixes and arrival input restoration in PIE.
- The complete timed 20-minute route.

## Non-negotiable safety and authority rules

1. **Do not inspect or edit `MelodiaHairComponent.cpp`.** It is correct and PIE-verified.
2. **Do not save `/Game/ZenForestTest` without the owner's explicit in-session approval.** At preparation time it was the editor's sole dirty package.
3. Do not edit Codex-owned Niagara, locked live look assets, or owner-approved PPV/material instances. Claude has one narrow, isolated exception: create new sibling PPV profile instances, new Universal-master portfolio/token instances, and update the GMM token registry/tests described in Lane D. Masters and locked instances remain read-only.
4. Quill alone advances dialogue and choices. Widgets never advance the interpreter independently.
5. Stock JRPG owns command submission, damage, turns, terminal outcomes, rewards, and result dismissal.
6. `FMelodiaNarrativeRecord` v2 is the sole persistent Persona store. No transient or parallel stat/save store.
7. `UMelodiaTravelSubsystem` owns authored travel. Preserve the Decision 028 save/restore exception.
8. Rhythm, stencil, sparkle, audio, and camera feedback are presentation-only; disabling them must not change outcomes.
9. One Unreal mutation surface per asset/graph per session. Prefer Monolith; never run Monolith and another MCP against the same graph concurrently.
10. For graph edits: `export → fingerprint → mutate → compile → assert → fingerprint → save`, one asset per transaction. Failure is a hard stop.
11. Never commit through `BS_GodFile\.git`. Healthy Git metadata is `C:\EnvironmentPortfolio\.repo_recovery_20260727\.git`. No commit unless the owner explicitly requests one.

## Collision locks

| Surface | Exclusive owner while claimed | Everyone else |
|---|---|---|
| Quill WBP trees/native presentation adapters | Kiro | Read-only |
| Priestess source, Persona content, narrative record/save transaction | Claude | Read-only |
| Stock battle controller/UI/result graphs | Cline | Read-only |
| `BP_MelodiaJRPGGameInstance` travel graph | Cline | Read-only; currently verified, avoid needless edits |
| `ZenForestTest` NPC/Quill bindings | Owner-approved single agent only | No save, no opportunistic cleanup |
| `WBP_Battle_Rhythm` | Unclaimed by default | Do not repair/use; stale references are known |
| Locked live PPV/grade, `MI_StorybookOutline_Premium_Hero`, Codex Niagara/material work | Locked outside this session | Observe only |
| New PPV profile siblings, Universal portfolio/token MIs, `tokens.py` + token tests | Claude, Lane D | Kiro/Cline read-only until released |
| Live landscape master/forks and `ZenForestTest` landscape actor | Read-only verification by Claude | No instance/master/map mutation |

Before changing a shared asset, post: `CLAIM <asset> <agent> <purpose>`. After validation, post `RELEASE <asset> <evidence>`. If another claim exists, stop.

## Lane A — Kiro: player-facing Quill, UI, input, and focus

**Own:** runtime presentation verification and narrow fixes in project-owned UI only.

Order:

1. Verify the runtime uses the four Melodia Quill classes already assigned.
2. Test Dialog Advance and Selection with mouse, Enter/Space, and controller separately.
3. Prove one physical action emits one `OnAdvance` or one `OnSelected`; test rapid/double input.
4. Verify first-valid-choice focus, disabled-choice behavior, text population, background insertion, and focus return after results.
5. Verify dialogue/menu input contexts: movement blocked only while required, cursor/focus restored, no leaked context after travel.
6. Identify the actual instantiated stock battle widgets in PIE before polishing anything else.
7. Verify primary `BP_ActionButton` focus/centering changes appear at runtime and do not submit duplicate commands.

Acceptance evidence:

- Runtime widget class names or screenshots for Dialog, Selection, battle command UI, and results.
- Input matrix: mouse / keyboard / controller, one action each, duplicate count zero.
- Log counts for Quill advance/selection and any `MELODIA_INPUT_LEAK` lines.
- Compile result for every changed widget: 0 errors, 0 warnings.

Do not:

- Repair `WBP_Battle_Rhythm` unless the owner explicitly assigns it after runtime package identity is known.
- Change Quill intent text, quest data, save schema, battle commands, PPV, or materials.

## Lane B — Claude: Quill/Persona transaction and persistence

**Own:** authoritative narrative and economy transactions plus full-process persistence evidence, including Melody Token wallet state and idempotent victory grants.

Order:

1. Verify the eligible runtime NPC interaction resolves the Petal Priestess Quill asset. If this requires changing `ZenForestTest`, stop for explicit owner approval and a safe save window.
2. Run the choice on a fresh slot and prove:
   - exactly one selected original `FStatement`;
   - exactly one stable intent consumption;
   - Harmony becomes exactly `1/5`;
   - quest 1 accepts exactly once;
   - quest 2 is unavailable before both prerequisites and available afterward.
3. Save through canonical UI/authority after the battle/travel boundary.
4. Fully exit Unreal, relaunch, load through the normal menu, and prove Harmony, consumed intent, quest, reward, encounter completion, map, and spawn context survive.
5. Replay/restore the authored Priestess beat and prove Harmony and rewards do not duplicate.
6. Prove Melody Token economy persistence in the same canonical save/restart pass: victory grants once per battle instance; seven-element shard balances, mana, golden tokens, and `total_collected` survive; replaying/restoring the terminal result cannot grant twice.
7. Exercise missing/unknown Quill recovery only after the clean path passes; valid current state must not be erased.

Acceptance evidence:

- Before-save and after-restart values for `SocialStats`, quest state, narrative flags, rewards, `ConsumedIntentIds`, token wallet (`shards`, `mana_current`, `mana_max`, `golden_tokens`, `total_collected`), map, and spawn context.
- One victory grants its token reward exactly once; a repeated victory callback, result restore, or reload leaves the wallet unchanged.
- Harmony remains 1 after replay.
- Quest 2 eligibility matrix: locked with neither prerequisite; locked with only one; available with both.
- Save slot name and timestamps showing an actual process restart, not same-session reload.

Do not:

- Add a second save/stat/quest store.
- Award Harmony from battle, pickup, or travel.
- Mutate battle/result graphs or player-facing UI styling.

## Lane C — Cline: stock encounter/result/travel and regression evidence

**Own:** runtime orchestration around the stock JRPG authority, travel proof, automation, and packaged launch.

Order:

1. PIE-walk fixed-but-unverified P0s before graph changes:
   - Dreamstate/portal arrival at `L_KaleidoNave`;
   - party defeat → confirm → `L_MelodiaMainMenu`;
   - input restoration and intended tagged arrival.
2. Identify the actual runtime battle controller and overlay package; share paths with Kiro.
3. Run Victory, Defeat, Fled, and unavailable outcomes on isolated slots where possible.
4. For each branch count:
   - `MELUSINA_LOOP_BATTLE_COMPLETED`
   - `MELUSINA_LOOP_QUILL_RESTORE`
   - `MELUSINA_LOOP_QUILL_NEXT`
5. Verify reward/completion only occur on authored branches, result dismisses once, Quill resumes once, and the encounter does not immediately retrigger.
6. Once `ZenForestTest` is no longer dirty/at risk, run the full live-editor automation suite.
7. Launch the staged packaged executable and walk the shortest representative route outside the editor.

Acceptance evidence:

- Outcome matrix with result, reward, completion flag, and marker counts per branch.
- `MELODIA_TRAVEL_START` and `MELODIA_TRAVEL_ARRIVED ... placed=1` for authored travel.
- Full automation result: 49 total; baseline expectation 46 pass / 3 known failures. Any fourth failure is a regression.
- Packaged executable launch, map reached, input functional, and save/menu smoke result.

Do not:

- Fork stock battle authority.
- Repair stale `WBP_Battle_Rhythm` as a substitute for identifying the instantiated package.
- Modify Persona record/schema, Quill source, or UI styling.

## Lane D — Claude: isolated portfolio materials and Melody Token asset contract

**Own:** new material-instance assets and the matching GMM token-definition/registry tests. Token-wallet runtime persistence and victory-transaction integrity remain Lane B. This lane may run in parallel with gameplay only when it does not load/save protected maps or claim assets from Lanes A–C.

### D1. PPV profile siblings — six new instances

Create fresh Hero and Gameplay profiles under the existing `Candidates/Profiles/` convention for:

| Parent material | Hero intent | Gameplay intent |
|---|---|---|
| `M_PP_StorybookOutline_Premium_Candidate` | Capture-grade contour | Restrained/cheaper dials |
| `M_PP_StarryNightOverlay_Candidate` | Full painted sky | Reduced impasto/value push |
| Active `/Game/_PROJECT/.../M_PP_MeluColorGrade` root | Hero grade | Quiet defaults |

Rules:

- Never copy from or modify owner-locked `MI_StorybookOutline_Premium_Hero`; the new outline Hero is a sibling.
- Sky Hero may start from the current loud structural tuning, but must set `UseUDSTimeOfDay=1` before capture. Gameplay lowers `ValueStructure` and `ImpastoRelief`.
- Do not attach these profiles to a live PPV or save a map during authoring. Promotion is a separate owner decision.

### D2. Universal-master portfolio/parallax instances

- Use existing `M_Master_Toon_Universal` parameters and `setup_master_universal.py` conventions; do not build another parallax function.
- Drive parallax only where a real height/displacement map exists. Relevant controls include `ParallaxScale`, `ParallaxHeight`, `ParallaxStrength`, per-layer scales, `bUseHeightToNormal`, `HeightToNormalStrength`, and the existing simple/steep/stepped-POM mode/step controls.
- A connected height texture with `ParallaxStrength=0` is a failed visual proof; verify a close shot.
- Keep every material within Unreal's two-MaterialParameterCollection limit.

### D3. Landscape verification — read-only first

- Read the material reference from the live landscape actor in `ZenForestTest` without saving the map.
- Report which of the approximately eight master forks is actually live.
- Instance only the proven live master if the owner separately authorizes it; otherwise stop at the report. Delete or edit none of the forks.
- Use `MacroWorldSizeCm` in physical centimeters; do not restore or reinterpret reciprocal `MacroScale`.

### D4. Melody Token materials and registry

Canonical proposed MI family under the existing Heart location:

- `/Game/EnvSandbox/Textures/melodsytoken/Materials/MI_MelodyToken_Heart`
- `/Game/EnvSandbox/Textures/melodsytoken/Materials/MI_MelodyToken_Star`
- `/Game/EnvSandbox/Textures/melodsytoken/Materials/MI_MelodyToken_Swirl`
- `/Game/EnvSandbox/Textures/melodsytoken/Materials/MI_MelodyToken_Water`

All four parent `M_Master_Toon_Universal`; Heart must be rebuilt because the current orphan has no parent and importer-only parameters. Map each variant's authored BaseColor/Emission/Metallic/Normal/Roughness textures. Star/Swirl/Water additionally map Alpha and Displacement into the existing height/parallax controls. Heart has no displacement and keeps parallax disabled. Differentiate Forte/Radiant/Arcane/Tide using existing rim/glow/iridescence/sparkle controls and approved palette swatches; do not add a third MPC.

Update `Content/Python/gmm/game/tokens.py` in the same transaction:

- Correct Heart texture path to `/Game/EnvSandbox/Textures/melodsytoken/Textures/T_MelodyToken_Heart_BaseColor`.
- Populate direct Star/Swirl/Water `material_path` values and remove their `material_fallback` entries.
- Treat `/Game/EnvSandbox/Textures/melodsytoken/Materials/` as the proposed canonical family; report the duplicate Heart under `melodsytoken_material/`, delete neither.
- Update `gmm/tests/test_tokens.py`: the current test intentionally asserts empty paths plus Heart fallback and must change to assert each direct path resolves conceptually and each fallback is empty. Without this test update, the required green contract suite is impossible.

### D5. Material/token acceptance

1. Every new instance reports the intended parent and `validate_material` returns 0 issues.
2. Every texture reference resolves; no Star/Swirl/Water asset silently uses Heart.
3. Close-shot evidence proves nonzero parallax for each displacement-bearing token.
4. `python -m unittest discover -s gmm -p "test_*.py" -q` passes from `Content/Python`.
5. No material exceeds two MPC references.
6. No live PPV, locked instance, landscape master/fork, duplicate token MI, or map is modified/deleted.
7. Publish `Docs/Handoffs/KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md` with released asset paths before Kiro begins pickup/HUD implementation.

## Shared execution phases

### Phase 0 — preserve work and establish evidence

- Confirm dirty packages. If `ZenForestTest` is dirty, no automation, map switch, restart, or package launch until the owner establishes a safe checkpoint.
- Record editor build timestamp, current map, input device, viewport resolution, and test slots.
- Each agent posts its claims before mutation.

### Phase 1 — read-only runtime reconnaissance

Run one short PIE route with no mutations. Kiro records UI classes/focus, Claude records Quill/Persona events, Cline records encounter/travel/result actors and loop markers. Stop at the first broken authority seam and assign it to the owning lane.

### Phase 2 — close the narrative transaction

Claude closes NPC → Quill → Harmony → quest/marker. Kiro validates choice fidelity/focus in parallel only if no shared asset is being edited. Cline remains read-only on this seam.

**Gate:** Harmony exactly 1, quest 1 once, quest 2 data gate correct, replay does not double-pay.

### Phase 3 — close encounter and result

Cline closes the four result branches. Kiro validates runtime command/results UI and input parity. Claude observes persistence events without editing battle graphs.

**Gate:** one battle session, one result, one Quill restore/next transition, branch-correct reward.

### Phase 4 — close travel and persistence

Cline proves authored travel and spawn placement. Claude performs canonical save → full process exit → relaunch → load, including both narrative state and the Melody Token wallet/idempotent victory grant. Kiro checks focus/input restoration after dialogue, result, menu, and travel.

**Gate:** loaded state is equivalent to pre-exit state and stable intents remain consumed.

### Phase 5 — regression, package, timed slice

Only after protected dirty work is safe:

1. Run all 49 `Melodia` tests.
2. Launch-test the staged package.
3. Execute the canonical 20-minute playtest once without developer shortcuts.
4. Repeat only failed segments, then perform one final clean route.

## Commands and tools

### Build, editor closed

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -WaitMutex -NoHotReloadFromIDE -NoUBA
```

### Preferred automation route in the running editor

Monolith JSON-RPC at `http://localhost:9316/mcp`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "editor_query",
    "arguments": {
      "action": "run_automation_tests",
      "prefix": "Melodia",
      "max_tests": 49
    }
  }
}
```

This route runs in the existing editor without PIE or a separate process and bypasses the UE 5.8 commandlet `ValidatePlatforms` failure. Do not invoke it while protected dirty map work is at risk.

### Commandlet fallback

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -ExecCmds="Automation RunTests Melodia; Quit" -unattended -nopause -nullrhi -NoSplash -NoSound
```

Known blocker: UE 5.8 `ValidatePlatforms` rejects missing LinuxArm64/VisionOS SDK `MainVersion` metadata before tests start. Do not modify installed SDK/security configuration merely to force this path.

### Log evidence

Current log:

`C:\EnvironmentPortfolio\BS_GodFile\Saved\Logs\BS_GodFile.log`

Useful filters:

```powershell
Select-String -Path "Saved\Logs\BS_GodFile.log" -Pattern "MELUSINA_LOOP|MELODIA_TRAVEL|MELODIA_INPUT_LEAK|Harmony|Quill|Error|Warning"
```

## Evidence ledger

Every lane reports compactly in this format:

```text
AGENT:
CLAIMED ASSETS:
CHANGED:
COMPILE/VALIDATION:
PIE OR PROCESS-RESTART EVIDENCE:
COUNTS/VALUES:
FILES MODIFIED:
DEFERRED/BLOCKED:
RELEASED ASSETS:
```

A green compile is not runtime proof. A same-session reload is not process-restart proof. Static references are not instantiated-widget proof. Screenshots prove presentation, not authority; logs/state readback prove authority.

## Stop conditions

Stop and coordinate immediately if any of these occurs:

- A prompt would save `ZenForestTest` without explicit owner approval.
- Two agents claim the same asset or graph.
- Quill advances twice, a choice emits the wrong statement, or Harmony changes by anything other than exactly +1 once.
- A presentation event changes damage, turns, rewards, travel, save state, or command submission.
- An expected compile/assert fails; do not retry blind.
- A fourth automation failure appears beyond the known three.
- A result branch duplicates completion/reward or resumes Quill more than once.
- Save/load changes schema version, loses consumed intents, or differs after full restart.
- Travel arrives with `placed=0`, wrong map, world origin, or leaked input context.

## Definition of done for the evening

The session is complete only when evidence shows:

1. The runtime NPC opens the intended Melodia Quill UI.
2. Either Priestess choice produces the selected statement and converges on one stable Harmony intent.
3. Harmony is 1/5, quest 1 changes once, and quest 2 requires quest 1 plus Harmony ≥1.
4. Stock battle starts once; commands work across required input methods; terminal result resolves once.
5. Quill resumes at the correct post-result statement and rewards do not duplicate.
6. Authored travel reaches KaleidoNave at the intended spawn with input restored.
7. Full process restart preserves stat, consumed intent, quest, reward, encounter, token wallet, map, and spawn state; restoring the same battle result cannot grant tokens twice.
8. Automation has no regression beyond the documented three known failures.
9. The packaged executable launches and completes the agreed smoke route.
10. The timed 20-minute route completes without developer shortcuts or saving protected world-building work.

If all runtime gates cannot close, the acceptable fallback is an evidence-backed blocker list naming the exact first broken seam, owning asset/system, reproduction, and next action—never a broad claim that the loop is "mostly done."
