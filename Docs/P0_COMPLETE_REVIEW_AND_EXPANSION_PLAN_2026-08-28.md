# P0 Convergence — Complete Review & Expansion Plan

**Date:** 2026-08-28 (session 3)
**Supersedes:** `Docs/P0_CONVERGENCE_UPDATED_PLAN_2026-08-28.md`

---

## 1. Loose Ends Audit

### Critical (Block P0 Closure)

| # | Loose End | Status | Fix Required |
|---|---|---|---|
| 1 | `.qsc` files not compiled to `.uasset` | BLOCKING | Compile 5 scripts via `CompileQuillSource` |
| 2 | `DA_MelodiaIntegrationConfig` missing P0 IDs | BLOCKING | Add 30+ IDs from `specs/echo_allowlist.json` |
| 3 | `BP_MelodiaPCGChallengeHost` not created | BLOCKING | Create actor + place in map for `music_world_key` |
| 4 | `LiveResultsWidgetPath` empty | OPEN | C++ `Initialize()` backfill + rebuild |
| 5 | Player death crash (`AnimMontage.h:781`) | OPEN | Fix death montage on player unit |
| 6 | Quill background panel not rendering | OPEN | Fix `ShowBackgroundBox` double-call |
| 7 | Choral Sheep mesh not skinned | OPEN | Owner-side skinning |
| 8 | Slime/Cosmic Reaver meshes missing | OPEN | Owner-side mesh import |
| 9 | `BS_GodFile.uproject` BOM + reindent | OPEN | Revert, re-apply only HoudiniEngine |
| 10 | Zero-byte root files (`Checking`, `Installing`, `Set`, `uv`) | OPEN | Delete |

### Important (Post-P0)

| # | Loose End | Status |
|---|---|---|
| 11 | FGameplayTag migration incomplete | 6 subsystems remaining |
| 12 | `static_gates` frozen baseline drift | Material re-freeze needed |
| 13 | `package_launch` stale (08-14 baseline) | Re-run against current content |
| 14 | Oceanology/ACFU vendor plugins | HOLD_VENDOR_INPUTS_MISSING |
| 15 | `wardrobe_equip_roundtrip` not proven live | Needs PIE |
| 16 | `wardrobe_gameplay_hook` not proven live | Needs PIE |
| 17 | `rhythm_owner` not proven live | Needs PIE |
| 18 | `rhythm_grade_to_result` not proven live | Needs PIE |
| 19 | `music_world_key` not proven live | Needs PIE |

---

## 2. Blueprints Necessary for P0

### Already Exist (verified)

| Blueprint | Path | Role |
|---|---|---|
| `BP_MelodiaJRPGGameInstance` | `/Game/MelodiaIntegration/Blueprints/` | Game instance |
| `BP_MelodiaJRPGGameMode` | `/Game/MelodiaIntegration/Blueprints/` | Game mode |
| `BP_MelodiaJRPGPlayerController` | `/Game/MelodiaIntegration/Blueprints/` | Player controller |
| `BP_MelusinaJRPGCharacter` | `/Game/Melodia/Characters/Melusina/` | Live pawn (has wardrobe + traversal + sorrow seam components) |
| `BP_BattleController` | `/Game/TurnBasedJRPGTemplate/Blueprints/` | Battle flow |
| `BP_BattleUI` | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | Battle HUD |
| `BP_InteractionBattle` | `/Game/MelodiaIntegration/Blueprints/` | Battle trigger (tag: melodia_smoke_encounter) |

### Needed for Remaining P0 Gates

| Gate | Blueprint Needed | Where to Attach | Notes |
|---|---|---|---|
| `music_world_key` | `BP_MelodiaPCGChallengeHost` | MelodiaIntegrationMap (persistent level) | Actor with `UMelodiaPCGNarrativeChallengeBridgeComponent`. Piano phrase → notification → opens route/door. |
| `wardrobe_equip_roundtrip` | None (code-only) | — | Use existing `BP_MelusinaJRPGCharacter` + `UMelodiaWardrobeSubsystem`. Test via PIE. |
| `wardrobe_gameplay_hook` | `BP_TraversalTestVolume` (optional) | Test map | Trigger volume that logs when a character with Glide enters. |
| `rhythm_owner` | None (code-only) | — | Probe `BP_BattleUI::OnKeyDown` → confirm it calls `UseSkillWithRhythm` not stock `UseSkill`. |
| `rhythm_grade_to_result` | None (code-only) | — | Real-key input during rhythm highway → damage delta observed. |

### BP Creation Priority

1. **`BP_MelodiaPCGChallengeHost`** — required for `music_world_key`. Simple actor with the bridge component, placed in the map.
2. **`BP_TraversalTestVolume`** — optional for `wardrobe_gameplay_hook`. A trigger volume that logs when a character with Glide enters.

---

## 3. Wardrobe Functionality Test Plan

### Test Files Created

| File | Purpose |
|---|---|
| `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeAutomationTests.cpp` | 4 automation tests for wardrobe |
| `Content/Python/Tests/test_p0_content_integration.py` | 10 offline tests for P0 content |

### Automation Tests (C++)

| Test | Class | What It Proves |
|---|---|---|
| `FMelodiaWardrobeEquipRoundtripTest` | `Melodia.Wardrobe.EquipRoundtrip` | Grant → Equip → Unequip → Idempotency |
| `FMelodiaWardrobeGameplayHookTest` | `Melodia.Wardrobe.GameplayHook` | Equip → Glide active → Unequip → Glide inactive |
| `FMelodiaWardrobeSaveLoadRoundtripTest` | `Melodia.Wardrobe.SaveLoadRoundtrip` | Save → Restore → State matches |
| `FMelodiaWardrobeTraversalIntegrationTest` | `Melodia.Wardrobe.TraversalIntegration` | QueryTraversalCapability through interface |

### Python Tests (Offline)

| Test | What It Proves |
|---|---|
| `test_01_scripts_exist` | All 4 P0 scripts on disk |
| `test_02_scripts_have_uasset` | All 4 compiled to .uasset |
| `test_03_no_duplicate_consume_once_ids` | No duplicate quest/reward/stat/item IDs |
| `test_04_all_ids_allowlisted` | Every emitted ID in allowlist |
| `test_05_no_wrong_flag_prefix` | No `flags.` (plural) prefix |
| `test_06_no_duplicate_reward_in_questcomplete` | No double-grant in questcomplete |
| `test_07_p0_playthrough_has_battle` | P0 Playthrough triggers battle |
| `test_08_wardrobe_equip_sets_flag` | Wardrobe Equip sets outfit_equipped flag |
| `test_09_choral_sheep_recruits` | Choral Sheep sets recruited flag |
| `test_10_sea_above_travels` | Sea Above triggers travel |

### Live PIE Tests (Owner-Performed)

| Test | Steps | Expected |
|---|---|---|
| Wardrobe Equip Roundtrip | 1. PIE → Open wardrobe UI → Equip Resonant Weave → Save → Quit → Reload → Check outfit | Outfit persists |
| Wardrobe Gameplay Hook | 1. PIE → Equip Resonant Weep → Jump → Glide activates | Glide works |
| Rhythm Owner | 1. PIE → Start battle → Press Q/W/O/P → Highway lights up | Single path to damage |
| Rhythm Grade | 1. PIE → Start battle → Hit notes with timing → Damage changes | Grade affects result |
| Music World Key | 1. PIE → Play piano phrase → Route opens | Phrase → world change |

---

## 4. Rider Tool Skill Expansion

### Current Rider Capabilities (Verified)

| Capability | How to Access | Use for P0 |
|---|---|---|
| Blueprint Usages / Derived Classes | Code Vision lenses above UCLASS | Find all BPs using a class |
| Blueprint Default Values in C++ | Inlay Hints | See CDO overrides without editor |
| 1-Click Navigation | Click lens → opens node in editor | Fast BP debugging |
| Unreal Editor Log | Structured, color-coded output | Debug compilation issues |
| PIE Toolbar | Pause, step frame, inspect | Debug gameplay |
| Unreal Insights | `.utrace` profiling | Profile CPU, memory |
| Clang-Tidy Modernization | Code Cleanup (Ctrl+E, C) | Enforce `TObjectPtr<T>` |
| IWYU Analyzer | Strip redundant includes | Faster compilation |
| Qodana Static Analysis | Headless pre-commit checks | Catch memory leaks, missing reflection |

### RiderLink Plugin (Not Yet Installed)

| Feature | Benefit | Status |
|---|---|---|
| In-Editor Test Execution | Run IMPLEMENT_SIMPLE_AUTOMATION_TEST from gutter | Need to install |
| Interactive Unreal Editor Log | Color-coded engine output in Rider | Need to install |
| PIE Toolbar Controls | Pause, step frame from Rider | Need to install |

### How to Expand Rider for P0

1. **Install RiderLink** — Clone into `Plugins/Developer/RiderLink/`, add to `.uproject`, rebuild
2. **Configure Code Vision** → Settings → Editor → Code Vision → Enable "Blueprint Usages"
3. **Run Automation Tests** → Right-click test → "Run" (requires RiderLink)
4. **Profile with Unreal Insights** → Session Frontend → Profiler → Live Capture
5. **Qodana Headless** → `qodana scan --ide QDJB` in CI

---

## 5. Melodia MCP Expansion

### Current MCP Tools (51 tools across 24 namespaces)

| Namespace | Tools | Use for P0 |
|---|---|---|
| `blueprint_query` | 134 actions | Graph inspection, node search, fingerprint |
| `material_query` | 20+ actions | Material validation |
| `animation_query` | 10+ actions | State machine validation |
| `editor_query` | 30+ actions | Level actors, compilation, Python execution |
| `config_query` | 5 actions | Read config assets |
| `project_query` | 10+ actions | Asset listing, stats |
| `source_query` | 10+ actions | C++ reflection |
| `mesh_query` | 15+ actions | Mesh analysis |
| `audio_query` | 10+ actions | Audio validation |
| `level_sequence_query` | 10+ actions | Sequencer validation |
| `reflect_query` | 15+ actions | Runtime reflection |
| `monolith_discover` | 1 action | Enumerate all tools |

### MCP Tools to Add for P0 Closure

| Tool | Namespace | Purpose | Priority |
|---|---|---|---|
| `wardrobe_query` | `wardrobe` | Read wardrobe state, equipped map, owned set | HIGH |
| `traversal_query` | `traversal` | Read traversal mode, capability state | HIGH |
| `narrative_query` | `narrative` | Read narrative record, consumed intents | HIGH |
| `quest_query` | `quest` | Read quest states, completion status | MEDIUM |
| `echo_record` | `echo` | Record gate results directly from PIE | MEDIUM |
| `pie_command` | `pie` | Execute commands in PIE session | LOW |

### How to Add MCP Tools

1. Add to `deploy/melodia_mcp_server.py` → `handle_tool_call()` dispatch table
2. Add JSON-RPC method handler
3. Test with `python -c "import json, urllib.request; ..."`

---

## 6. Updated P0 Action Plan

### Phase 0 — Hygiene (no editor, ~15 min)

1. Delete zero-byte root files: `Checking`, `Installing`, `Set`, `uv`
2. Restore `BS_GodFile.uproject` from HEAD, re-apply only `HoudiniEngine` entry
3. Decide tracked-vs-ignored for `Plugins/HoudiniEngine/` and Choral Sheep FBXs

### Phase 1 — Make Content Real (editor, ~1 h)

4. Extend `DA_MelodiaIntegrationConfig` with P0 IDs from `specs/echo_allowlist.json`
5. Compile 5 `.qsc` → `.uasset` (4 new + HarmonyAwakening)
6. Run `test_p0_content_integration.py` → confirm 10/10

### Phase 2 — BP Creation + Wiring (editor, ~30 min)

7. Create `BP_MelodiaPCGChallengeHost` actor with bridge component
8. Place in `MelodiaIntegrationMap` persistent level
9. Wire piano phrase → notification → route open

### Phase 3 — Live Prove (editor + PIE, ~2 h)

10. P0 Playthrough end-to-end
11. Wardrobe equip roundtrip
12. Choral Sheep script-side
13. Sea Above travel + membrane
14. Rhythm owner (code path proof)
15. Rhythm grade (real-key)
16. Music world key (BP + phrase)
17. Wardrobe gameplay hook (Glide)

### Phase 4 — Echo Golden Run + Closeout (overnight)

18. Run full static chain
19. Run full runtime chain
20. Record all P0 gates
21. 20–30 min golden run
22. Repackage + `package_launch` against current content
23. Final ledger review

### Phase 5 — FGameplayTag Completion (post-P0)

24. Migrate `MelodiaNarrativeSubsystem` (quests, flags, rewards, stats, travel, encounters)
25. Migrate `MelodiaExternalJRPGBridgeSubsystem` (encounters)
26. Migrate `MelodiaExplorationActors` (interaction IDs, puzzle IDs)
27. Migrate `MelodiaPCGWaterGameplayBridgeComponent` (water IDs)
28. Migrate `MelodiaPCGNarrativeChallengeBridgeComponent` (challenge IDs)
29. Migrate `MelodiaBattleMapConfig` (encounter IDs)
30. Update all Blueprints (manual)
31. Update all Data Assets (manual)
32. Test save/load round-trip with `TSet<FGameplayTag>`

---

## 7. File Manifest (all work this session)

```
BS_GodFile/
├── Docs/
│   ├── P0_CONVERGENCE_UPDATED_PLAN_2026-08-28.md
│   ├── MELODIA_PERSONALIZATION_INSTALLATION_2026-08-28.md
│   ├── RIDER_UE58_INTEGRATION_ROADMAP_2026-08-28.md
│   └── Handoffs/
│       └── INTEGRATION_LAYER_HANDOFF_2026-08-28.md
├── Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/
│   ├── MelodiaWardrobeAutomationTests.cpp   # NEW: 4 automation tests
│   └── MelodiaWardrobeCompanionBridgeTests.cpp  # EXISTING: 2 tests
├── Content/Python/Tests/
│   └── test_p0_content_integration.py       # NEW: 10 offline tests
├── specs/
│   └── echo_allowlist.json                  # NEW: P0 allowlist IDs
├── Source/BS_GodFile/MelodiaIntegration/
│   ├── MelodiaGameplayTags.h                # NEW: FGameplayTag infrastructure
│   ├── MelodiaGameplayTags.cpp              # NEW: RegisterMelodiaGameplayTags()
│   ├── MelodiaWaterGameplaySubsystem.h/.cpp  # MOD: FName → FGameplayTag
│   ├── MelodiaWaterGameplayTypes.h           # MOD: FName → FGameplayTag
│   ├── MelodiaMusicClockSubsystem.cpp        # MOD: +3 trace scopes
│   ├── MelodiaPCGNarrativeChallengeBridgeComponent.cpp  # MOD: +2 trace scopes
│   └── MelodiaPCGWaterGameplayBridgeComponent.cpp      # MOD: +3 trace scopes
├── Tools/
│   └── record_gate.py                        # MOD: +6 P0 gates
└── qodana.yaml                               # MOD: Unreal C++ inspections
```

---

## 8. Key Architecture Decisions (for reference)

| Decision | Impact |
|---|---|
| `UMelodiaWardrobeSubsystem` is the wardrobe authority | All equip/grant operations go through here |
| `FMelodiaNarrativeRecord` is the persistence seam | Wardrobe state saved/loaded through narrative record |
| `IMelodiaTraversalCapabilityProvider` is the interface | Wardrobe implements this for Glide/Dash/Swim |
| `UMelodiaTraversalCapabilityRegistry` is the discovery seam | One provider per game instance |
| `BP_MelusinaJRPGCharacter` is the live pawn | Has wardrobe + traversal + sorrow seam components |
| `EMelodiaWardrobeSlot` is the slot vocabulary | Body, Hat, Gloves, Shawl, Trail, HairCharm, Shirt, Skirt, Boots, Accessories |
| `EMelodiaFormCapability` is the capability vocabulary | Glide, Dash, Swim |
| `MelodiaTraversalCapability` namespace | `capability.melodia.glide`, `.dash`, `.swim` |

---

## 9. Test Execution Commands

```bash
# Offline tests (no editor)
cd BS_GodFile
python Content/Python/Tests/test_p0_content_integration.py

# Automation tests (requires editor + RiderLink)
# Right-click test → "Run" in Rider, or:
RunTests Melodia.Wardrobe.EquipRoundtrip
RunTests Melodia.Wardrobe.GameplayHook
RunTests Melodia.Wardrobe.SaveLoadRoundtrip
RunTests Melodia.Wardrobe.TraversalIntegration

# Echo pipeline
python Tools/echo_run.py run static_gates
python Tools/echo_run.py run runtime_gates

# Record gates
python Tools/record_gate.py wardrobe_equip_roundtrip pass --note "2026-08-28 PIE: equip → save → restart → load"
python Tools/record_gate.py wardrobe_gameplay_hook pass --note "2026-08-28 PIE: Glide active after equip"
python Tools/record_gate.py rhythm_owner pass --note "2026-08-28 PIE: UseSkillWithRhythm path confirmed"
python Tools/record_gate.py rhythm_grade_to_result pass --note "2026-08-28 PIE: grade changes damage"
python Tools/record_gate.py music_world_key pass --note "2026-08-28 PIE: piano phrase opens route"
```
