# P0 Convergence — Updated Plan & Work Review

**Date:** 2026-08-28 (session 2)
**Supersedes:** `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md` (retains its evidence, adds the integration-layer work and the remaining BP/echo plan)

---

## 1. Work Done This Session

### A. Hermes Personalization (all live)

| Item | File | Status |
|---|---|---|
| Melodia skin (pink/purple) | `~/.hermes/skins/melodia.yaml` | ACTIVE |
| Bard's Metronome TUI widget | `~/.hermes/tui-widgets/bard-metronome.mjs` | Created — `/bard-metronome` in TUI |
| Melodia Dashboard desktop plugin | `~/.hermes/desktop-plugins/melodia-dashboard/plugin.js` | Created — reload plugins in GUI |
| Melusina TTS persona | `~/.hermes/tts/melusina_persona.txt` | Created — use with `openai`/`elevenlabs` provider |
| Morning digest cron | `3d090c611f5c` | Daily 9am, local save |
| SOUL.md | `~/.hermes/SOUL.md` | Updated with Melusina persona |

### B. C++ Instrumentation (committed to working tree)

| File | Change |
|---|---|
| `MelodiaMusicClockSubsystem.cpp` | +`Stats/Stats.h`, +3 trace scopes (`TickClock`, `GetMusicTime`, `EnsureBattleControllerMusicClock`) |
| `MelodiaWaterGameplaySubsystem.cpp` | +`Stats/Stats.h`, +2 trace scopes (`ApplyOperation`, `RecomputeFlow`) |
| `MelodiaPCGNarrativeChallengeBridgeComponent.cpp` | +`Stats/Stats.h`, +2 trace scopes (`HandleNoteJudged`, `HandlePatternCompleted`) |
| `MelodiaPCGWaterGameplayBridgeComponent.cpp` | +`Stats/Stats.h`, +3 trace scopes (`HandleNoteJudged`, `HandlePatternCompleted`, `SubmitResonance`) |

### C. FGameplayTag Migration (proof of concept)

| File | Change |
|---|---|
| `MelodiaGameplayTags.h` | New — 18 tag categories, 80+ tags registered |
| `MelodiaGameplayTags.cpp` | New — `RegisterMelodiaGameplayTags()` |
| `MelodiaWaterGameplayTypes.h` | `FName` → `FGameplayTag` in all structs |
| `MelodiaWaterGameplaySubsystem.h` | `FName` → `FGameplayTag` in all public/private API |
| `MelodiaWaterGameplaySubsystem.cpp` | Full migration — `.GetTagName()` for map keys, `.IsValid()` for checks |

### D. P0 Content Integration

| File | Change |
|---|---|
| `MelodiaQuillWardrobeEquip.qsc` | Fixed `flags.melusina.sorrow_seam_restored` → `flag.melusina.sorrow_seam_restored` |
| `specs/echo_allowlist.json` | New — all 30+ missing IDs for P0 scripts |
| `Content/Python/Tests/test_p0_content_integration.py` | New — 10-test suite (9/10 pass, .uasset pending editor compile) |

### E. Echo Pipeline Updates

| File | Change |
|---|---|
| `Tools/record_gate.py` | Added 6 P0 gates: rhythm_owner, hud_single_writer, wardrobe_equip_roundtrip, rhythm_grade_to_result, music_world_key, wardrobe_gameplay_hook |
| `qodana.yaml` | Updated from `ide: QDNET` stub → `ide: QDJB` with Unreal C++ inspections |

### F. Codebase Audit

- All `UPROPERTY` UObject pointers already use `TObjectPtr<T>` — no modernization needed
- No raw `AActor*`, `UActorComponent*` in UPROPERTY macros

---

## 2. Current P0 Gate Status

| Gate | Status | Date | Evidence |
|---|---|---|---|
| runtime | PASS | 2026-08-13 | Owner PIE, all 4 outcomes, Quill resumes once |
| save_load | PASS | 2026-08-14 | Canonical save slot across restart |
| repeat_consume | PASS | 2026-08-14 | Flag+reward restore, no duplication |
| package_launch | PASS | 2026-08-14 | Dev package launches |
| battle_integration_map | PASS | 2026-08-28 | Live PIE, all 4 terminal outcomes |
| hud_single_writer | PASS | 2026-08-28 | One writer owns battle HUD |
| rhythm_owner | **OPEN** | — | Needs live battle proving `UseSkillWithRhythm` path |
| wardrobe_equip_roundtrip | **OPEN** | — | Needs equip → save → restart → load |
| rhythm_grade_to_result | **OPEN** | — | Needs real-key grade changing result |
| music_world_key | **OPEN** | — | PCG bridge not wired to level actor |
| wardrobe_gameplay_hook | **OPEN** | — | Needs equipped item → observable capability |

---

## 3. Blueprints Necessary for P0

### Already Exist (verified)

| Blueprint | Path | Role |
|---|---|---|
| `BP_MelodiaJRPGGameInstance` | `/Game/MelodiaIntegration/Blueprints/` | Game instance |
| `BP_MelodiaJRPGGameMode` | `/Game/MelodiaIntegration/Blueprints/` | Game mode |
| `BP_MelodiaJRPGPlayerController` | `/Game/MelodiaIntegration/Blueprints/` | Player controller |
| `BP_MelusinaJRPGCharacter` | `/Game/Melodia/Characters/Melusina/` | Live pawn (has wardrobe + traversal components) |
| `BP_BattleController` | `/Game/TurnBasedJRPGTemplate/Blueprints/` | Battle flow |
| `BP_BattleUI` | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | Battle HUD |

### Needed for Remaining P0 Gates

| Gate | Blueprint Needed | Where to Attach | Notes |
|---|---|---|---|
| `music_world_key` | `BP_MelodiaPCGChallengeHost` | MelodiaIntegrationMap (persistent level) | Host actor with `UMelodiaPCGNarrativeChallengeBridgeComponent`. Piano phrase → notification → opens route/door. |
| `wardrobe_equip_roundtrip` | None (code-only) | — | Use existing `BP_MelusinaJRPGCharacter` + `UMelodiaWardrobeSubsystem`. Test via PIE. |
| `wardrobe_gameplay_hook` | `BP_TraversalVolume` (or equivalent) | Test map | Volume that checks `IMelodiaTraversalCapabilityProvider` — confirms Glide/Dash/Swim is active when outfit equipped. |
| `rhythm_owner` | None (code-only) | — | Probe `BP_BattleUI::OnKeyDown` → confirm it calls `UseSkillWithRhythm` not stock `UseSkill`. |
| `rhythm_grade_to_result` | None (code-only) | — | Real-key input during rhythm highway → damage delta observed. |

### BP Creation Priority

1. **`BP_MelodiaPCGChallengeHost`** — required for `music_world_key`. Simple actor with the bridge component, placed in the map.
2. **`BP_TraversalTestVolume`** — optional for `wardrobe_gameplay_hook`. A trigger volume that logs when a character with Glide enters.

---

## 4. Echo Golden Run — Updated Procedure

### Pre-run Checklist

- [ ] Editor open with Monolith MCP on 9316
- [ ] Modal dialog dismissed (check `Saved/Logs/BS_GodFile.log` for `MODAL_OPEN`)
- [ ] `MelodiaIntegrationMap` loaded
- [ ] All 5 `.qsc` files compiled to `.uasset`
- [ ] `DA_MelodiaIntegrationConfig` updated with P0 IDs
- [ ] `RegisterMelodiaGameplayTags()` called at module startup (after FGameplayTag migration)

### Static Gates (offline-capable)

```bash
python Tools/echo_run.py run static_gates
```

Expected: all 5 pass (graph_reachability, bp_live_path, bp_sweep, ui_lint, verify_baseline)

### Runtime Gates (editor-required)

```bash
python Tools/echo_run.py run runtime_gates
```

Expected: pie_smoke, regression, fingerprint all pass

### P0 Content Test

```bash
python Content/Python/Tests/test_p0_content_integration.py
```

Expected: 10/10 pass (after .uasset compilation)

### Manual PIE Gates (owner-performed)

1. **P0 Playthrough** — `Quill.play_script("MelodiaQuillP0Playthrough")` → victory branch → verify atomic commit + Quill resume
2. **Wardrobe Equip** → save → restart → load → verify outfit + materials
3. **Choral Sheep** → script-side proof (companion mesh not skinned)
4. **Sea Above** → travel → membrane pulse → droplets
5. **Rhythm Owner** → confirm `UseSkillWithRhythm` path in live battle
6. **Rhythm Grade** → real-key timing changes result
7. **Music World Key** → `BP_MelodiaPCGChallengeHost` placed, piano phrase opens route
8. **Wardrobe Gameplay Hook** → equipped item → Glide capability observable

### Record Each Gate

```bash
python Tools/record_gate.py <gate-id> pass --note "2026-08-28 <evidence>"
```

---

## 5. Prioritized Action Plan

### Phase 0 — Hygiene (no editor, ~15 min) — DO NOW

1. Delete zero-byte root files: `Checking`, `Installing`, `Set`, `uv`
2. Restore `BS_GodFile.uproject` from HEAD, re-apply only `HoudiniEngine` entry by hand
3. Decide tracked-vs-ignored for `Plugins/HoudiniEngine/` and Choral Sheep FBXs
4. Record 08-27 gate rows into `Saved/gate_ledger.json`, regenerate report

### Phase 1 — Make Content Real (editor, ~1 h) — DO NOW

5. Extend `DA_MelodiaIntegrationConfig` with P0 IDs from `specs/echo_allowlist.json`
6. Compile 5 `.qsc` → `.uasset` (4 new + HarmonyAwakening)
7. Run `test_p0_content_integration.py` → confirm 10/10

### Phase 2 — BP Creation + Wiring (editor, ~30 min)

8. Create `BP_MelodiaPCGChallengeHost` actor with bridge component
9. Place in `MelodiaIntegrationMap` persistent level
10. Wire piano phrase → notification → route open

### Phase 3 — Live Prove (editor + PIE, ~2 h)

11. P0 Playthrough end-to-end
12. Wardrobe equip roundtrip
13. Choral Sheep script-side
14. Sea Above travel + membrane
15. Rhythm owner (code path proof)
16. Rhythm grade (real-key)
17. Music world key (BP + phrase)
18. Wardrobe gameplay hook (Glide)

### Phase 4 — Echo Golden Run + Closeout (overnight)

19. Run full static chain
20. Run full runtime chain
21. Record all P0 gates
22. 20–30 min golden run
23. Repackage + `package_launch` against current content
24. Final ledger review

### Phase 5 — FGameplayTag Completion (post-P0)

25. Migrate `MelodiaNarrativeSubsystem` (quests, flags, rewards, stats, travel, encounters)
26. Migrate `MelodiaExternalJRPGBridgeSubsystem` (encounters)
27. Migrate `MelodiaExplorationActors` (interaction IDs, puzzle IDs)
28. Migrate `MelodiaPCGWaterGameplayBridgeComponent` (water IDs)
29. Migrate `MelodiaPCGNarrativeChallengeBridgeComponent` (challenge IDs)
30. Migrate `MelodiaBattleMapConfig` (encounter IDs)
31. Update all Blueprints (manual)
32. Update all Data Assets (manual)
33. Test save/load round-trip with `TSet<FGameplayTag>`

---

## 6. Known Blockers

| Blocker | Impact | Resolution |
|---|---|---|
| Editor modal dialog | Monolith MCP unresponsive | Dismiss modal in editor |
| `.qsc` not compiled to `.uasset` | Scripts cannot be played | Compile via `CompileQuillSource` |
| `DA_MelodiaIntegrationConfig` missing P0 IDs | Runtime rejects all P0 notifications | Extend allowlist via editor |
| `music_world_key` needs host actor | PCG bridge not wired to level | Create `BP_MelodiaPCGChallengeHost` |
| Choral Sheep mesh not skinned | Companion stays PRESENTATION_ONLY | Owner-side skinning |
| Slime/Cosmic Reaver meshes missing | Enemies invisible | Owner-side mesh import |
| `LiveResultsWidgetPath` empty | Live results widget not found | C++ `Initialize()` backfill + rebuild |
| Player death crash (`AnimMontage.h:781`) | Defeat path kills editor | Use flee path for repeated testing |

---

## 7. File Manifest (all work this session)

```
BS_GodFile/
├── qodana.yaml                                    # Updated: Unreal C++ inspections
├── specs/
│   ├── echo_pipeline.json                         # Unchanged (already had P0 gates)
│   └── echo_allowlist.json                         # New: P0 allowlist IDs
├── Source/BS_GodFile/MelodiaIntegration/
│   ├── MelodiaGameplayTags.h                       # New: 18 tag categories, 80+ tags
│   ├── MelodiaGameplayTags.cpp                     # New: RegisterMelodiaGameplayTags()
│   ├── MelodiaMusicClockSubsystem.cpp              # +3 trace scopes
│   ├── MelodiaWaterGameplaySubsystem.h/.cpp        # FName → FGameplayTag migration
│   ├── MelodiaWaterGameplayTypes.h                 # FName → FGameplayTag in structs
│   ├── MelodiaPCGNarrativeChallengeBridgeComponent.cpp  # +2 trace scopes
│   └── MelodiaPCGWaterGameplayBridgeComponent.cpp  # +3 trace scopes
├── Content/MelodiaIntegration/Narrative/
│   ├── MelodiaQuillWardrobeEquip.qsc               # Fixed: flags. → flag.
│   ├── MelodiaQuillP0Playthrough.qsc               # Unchanged
│   ├── MelodiaQuillChoralSheepRecruit.qsc          # Unchanged
│   └── MelodiaQuillSeaAboveCutscene.qsc            # Unchanged
├── Content/Python/Tests/
│   └── test_p0_content_integration.py              # New: 10-test P0 suite
├── Tools/
│   ├── echo_run.py                                 # Unchanged
│   └── record_gate.py                              # +6 P0 gates
├── Docs/
│   ├── P0_CLOSEOUT_PLAN_2026-08-28.md              # Unchanged (still authoritative)
│   ├── MELODIA_PERSONALIZATION_INSTALLATION_2026-08-28.md  # New
│   └── RIDER_UE58_INTEGRATION_ROADMAP_2026-08-28.md # New
└── Saved/
    ├── gate_ledger.json                            # +2 rows (battle_integration_map, hud_single_writer)
    └── Echo/state.txt                              # Unchanged
```
