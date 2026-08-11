# Melodia Foundation Lock — 2026-07-29

## Purpose

This is the current safe handoff for narrow content work. It permits new
experimental **content** while protecting the proven foundation. It does not
claim that runtime-only gates have been tested; those gates are listed below.

## Locked baseline evidence

| Gate | Evidence | Status |
| --- | --- | --- |
| Native Editor build | `Saved/Logs/CodexNativeBuild_20260729_coreloop_r3.out.log` | Passed, 2026-07-29 |
| Python contract suite | `python -m unittest discover -s Content/Python/gmm/tests -p test_*.py` | Passed, 285 tests, 2026-07-29 |
| Rule parity | `Plugins/MelodiaCore/Rules/melodia_rules.json` matches `Content/Python/gmm/game/rules_generated.py` | Passed, 2026-07-29 |
| Menu New Game | Project-owner live confirmation | Verified |
| Stock battle completion / no duplicate Melusina | Project-owner live confirmation | Verified |
| Landscape authored baseline | Project-owner live confirmation; separate landscape contract | Verified, not part of gameplay edits |

The build is a **content-lock baseline**, not a release certificate. Never
describe it as packaged-ready until the runtime gate below is complete.

## Sole authorities — never replace them

| Concern | Authority | Allowed extension |
| --- | --- | --- |
| Turns, damage, target resolution, results | `/Game/TurnBasedJRPGTemplate` | Add stock-skill data/presentation only |
| Party, equipment, inventory, quest state | stock JRPG controller/data | Use stable IDs through `UMelodiaPersonaSubsystem` |
| Save/load | canonical JRPG GameInstance and `BP_JRPGSaveGame` | Embed the existing versioned Melodia narrative record only |
| Dialogue | QuillScript | Add `.qsc` scripts and allowlisted notifications |
| Narrative validation | `UMelodiaNarrativeSubsystem` | Add explicitly approved allowlist IDs |
| Exploration HUD | active `BP_ExploreUI` | Add contextual children to the existing panel only |
| Battle UI / keyboard guidance | stock Battle UI + presentation overlay | Overlay only; do not restructure the stock root |

Never create a second battle manager, save class, inventory, quest manager,
HUD root, dialogue system, player controller, or map-travel authority.

## Safe lower-tier work lanes

### Rhythm / MIDI

- Harmonix and MIDI Device Support are project-enabled. Use the contract in
  `Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md` before authoring any
  imported MIDI, Music Clock, MetaSound, or external-device route.
- MIDI may time UI, animation, VFX, and audio only. It must never become an
  alternate battle, save, quest, inventory, or party authority.
- The first proof is one profile for a stock skill, not a global rhythm system.

### Experimental skills

- Start from an existing stock skill class/data entry.
- Give it one stable ID, one animation/montage route, one VFX/SFX route, and
  one presentation-only rhythm cue.
- Preserve stock cost, target, damage, impact, and turn-release execution.
- Acceptance: one command, one visible montage, one stock impact, one result.

### Quests and NPC dialogue

- Add Quill source under `Content/MelodiaIntegration/Narrative/`.
- Use only `melodia:quest:<approved-id>` and other documented notifications.
- Add the ID to `DA_MelodiaIntegrationConfig` before use.
- Keep quest progression inside the Persona/JRPG adapter; do not store it in
  a new actor, widget, or Quill variable as canonical gameplay state.
- Acceptance: dialogue starts once, intent is accepted once, journal updates,
  reload does not duplicate completion or reward.

### Equipment

- Add a stable Melodia item ID and map it to a real stock JRPG equipment
  class in `DA_MelodiaPersonaContent` / `UMelodiaPersonaSubsystem`.
- Never create a parallel equipment list or save serializer.
- Acceptance: item reaches stock inventory, equips to canonical Melusina, and
  survives the canonical restart test.

### Sir Melodious companion

- Stock battle-party child:
  `/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit`.
- It was duplicated from the active stock player-unit parent and compiles
  cleanly. Author Sir's display, battle mesh, portrait, and skills in that
  child only; never edit its stock parent.
- `UMelodiaJRPGPartyBootstrapSubsystem` is the sole recruitment adapter. After
  the `SirRescued` opening phase it calls the stock controller's
  `AddPlayerUnit` API. Only a successful stock-party presence opens the
  presentation-only Ctrl flight handoff.
- `UMelodiaPartySubsystem` may possess the existing Sir flight pawn for
  exploration, but it must never add/remove combat units, write the canonical
  save, or bypass the stock party controller.

### Gatherable materials and interaction props

- Use the existing interaction/presentation actor seam in
  `MelodiaExplorationActors` or a content Blueprint that delegates its reward
  through the approved narrative/JRPG route.
- The actor may own meshes, VFX, SFX, collision, respawn presentation, and a
  one-shot visual state. It may not own permanent inventory or quest state.
- Acceptance: pickup fires once, stock authority acknowledges the reward,
  saving/reloading does not duplicate it.

## Protected paths

Do not edit these in an experimental-content task without explicit human
approval and a closed-editor native rebuild plan:

- `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.*`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.*`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaBattleAdapter.*`
- `Plugins/MelodiaCore/Source/MelodiaCore/OrreryMainMenuGameMode.*`
- `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI`
- `Config/DefaultEngine.ini`, `Config/DefaultInput.ini`
- active landscape, lighting, World Settings, GameMode, GameInstance, or map
  geometry while the environment lane is authoring.

## Required task closeout

Every lower-tier task ends with:

```text
Task attempted:
Files/assets changed:
Authority preserved:
Validation run:
Observed result:
Unproven or blocked:
Single next action:
Do not touch:
```

## Runtime gates owned by the next live test

1. Settings persist across a restart.
2. Priestess → Crystal Shard victory → Star Weaver updates journal/minimap
   exactly once.
3. One stock battle has one visible Melusina, one animation, one 4.5-second
   impact, one target result, and one turn release.
4. Save outside battle, fully restart, Continue, and verify the completion
   flag/reward exactly once.
5. Verify a stock-controller route can add and equip one mapped equipment
   item, then include it in the restart proof.

Until all five are recorded, experimental work can be authored in isolated
content lanes but must not alter foundation authority or advertise release
readiness.

## 2026-07-29 final foundation closeout

The accepted gameplay baseline received additive closeout scaffolding only:

- `UMelodiaExternalJRPGBridgeSubsystem` now unbinds during `Deinitialize`, clears its active encounter ID, and exposes read-only battle/encounter diagnostics.
- `UMelodiaTraversalComponent::EndPlay` calls `StopGlide` and clears transient references/input bookkeeping so movement overrides cannot leak across teardown.
- `UMelodiaAudioReactivePresentationSubsystem` caches `MPC_Portfolio_Audio` once and clears cached subsystem/object references during shutdown; Harmonix remains presentation-only.
- `UMelodiaPresentationDiagnosticsLibrary::LogGameplayFoundationState` emits `MELODIA_FOUNDATION_STATE` with map, controller, bridge, Harmonic, Persona quest-count, and `MelusinaSlot0` observations. It does not mutate gameplay.

Validation evidence:

- Live Coding: success, patch applied, zero errors.
- Python contracts: `285/285` passed with `PYTHONPATH=Content/Python`.
- Scoped `git diff --check`: passed for the eight native files.
- Source contract checks: bridge teardown unbind present; traversal teardown restores glide; one MPC `LoadObject` remains in initialization; diagnostics marker present.
- Remaining gate: the running editor did not refresh the new reflected `UFUNCTION`. Close Unreal Editor, run a full `BS_GodFileEditor Win64 Development` build, restart, invoke `log_gameplay_foundation_state`, and confirm `MELODIA_FOUNDATION_STATE` in the log.

No hair implementation or environment art was read or edited during this closeout.

## Parallel-agent lane contract

Every agent must claim one lane and list its files before editing. One agent owns a file at a time; shared/native authority files require coordinator approval. Agents must not opportunistically fix another lane.

| Lane | Suitable worker | Allowed scope | Forbidden scope |
| --- | --- | --- | --- |
| Native foundation coordinator | strongest C++/Unreal agent | lifecycle, read-only adapters, diagnostics, build evidence | stock JRPG redesign; hair/environment edits |
| Persona/content data | Claude/Gemini-class analysis agent | stable IDs, mappings, quest/equipment content validation | canonical save, party, inventory ownership |
| Quill narrative | language/content agent | `.qsc`, allowlisted intents, dialogue validation | direct gameplay mutation or parallel quest state |
| Harmonix presentation | audio-specialist agent | MIDI profiles, MetaSound/UI/VFX timing | damage, turns, rewards, save decisions |
| UI authoring | visual/Blueprint agent | children/overlays under approved existing roots | replacing stock Battle UI or Explore HUD root |
| Validation | DeepSeek/Cline or test-focused agent | tests, logs, source audits, diff checks | behavior changes while reporting validation |
| Documentation/portfolio | documentation agent | handoffs, evidence indexes, portfolio copy | source, gameplay assets, environment art |
| Environment art | dedicated artist lane only | landscape/material/lighting work under its own contract | gameplay/native integration files |
| Hair | dedicated owner only | `MelodiaHairComponent` and related hair assets | all other lanes; never inspect incidentally |

Required coordination rules:

1. Read this lock and `Docs/2026-07-29_PROJECT_HANDOFF.md` first.
2. Record `lane`, `files claimed`, `authority preserved`, and `validation command` before edits.
3. Do not modify a file already claimed by another active agent.
4. Binary Unreal assets are exclusive-write; never merge simultaneous Blueprint/package edits.
5. Keep stock JRPG, Persona adapter, Quill, and Harmonix authority boundaries exactly as listed above.
6. End with the required task-closeout template and identify all runtime-only evidence honestly.