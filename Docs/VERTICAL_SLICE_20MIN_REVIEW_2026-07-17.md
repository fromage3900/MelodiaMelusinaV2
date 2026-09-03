# 20-Minute Vertical Slice — Deep Review (2026-07-17)

Companion to `AI_ORCHESTRATION_HANDOFFS_2026-07-17.md`. Sources: full C++ trace of the roguelike loop, map/flow inventory, `MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md` milestone audit.

## Beat map vs. readiness

| # | Slice beat (~time) | Assets/systems | Verdict |
|---|---|---|---|
| 1 | Wake in bedroom, bed = save (0–2 min) | `L_MelusinaMorning` exists; `MelodiaBedActor` (save-on-overlap, placeholder mesh); `OpeningFlowSubsystem` Morning phase | **GO** — needs bed art + BP presentation hooks only |
| 2 | Sir Melodious reunion → departure (2–4 min) | `MelodiaSirMelodiousIntroActor` (reunion trigger + window departure → travels to `L_Melodia_Dreamstate`) | **GO** — presentation-only polish |
| 3 | Dreamstate interlude (4–6 min) | `L_Melodia_Dreamstate` exists; flow phase wired | **GO** (content pass unknown — verify visually) |
| 4 | ZenForest explore: jump/glide/Ctrl-swap (6–10 min) | `Content\ZenForestTest.umap` (root, not in Melodia/Levels); traversal C++ verified in PIE today; tutorial encounter → `NotifyZenEncounterVictory` unlocks dungeon | **GO w/ fixes** — map should be moved/renamed into `Content\Melodia\Levels\`; glide ABP state not yet authored; tutorial-enemy id must match `OpeningTutorialEnemyId` |
| 5 | Dungeon run: 3 stages, encounter→reward→exit (10–17 min) | Coordinator/RunSubsystem/Triggers/Exit **fully wired + PIE-proven** (fixed 3-stage); 22 room maps + 22 RoomData; staged-turn feel layer landed today | **GO** — the strongest part of the project |
| 6 | Boss + run end (17–19 min) | BossArena rooms V1–V3; generic final-stage victory → `OnRunCompleted` → spawns Sir intro actor | **GO** — no dedicated boss logic, acceptable for slice |
| 7 | Results + return (19–20 min) | Victory rank banner exists in HUD; `WBP_Battle_Results` NOT authored; defeat path NOT handled | **GAP** |

## Ranked gaps (slice-blocking first)

1. **Default map is an engine template** (`OpenWorld.OpenWorld` in DefaultEngine.ini for both editor+game). One-line config fix → `L_MelusinaMorning`. Without it the "game" boots into nothing.
2. **No end-to-end map chain**: nothing travels bedroom→(Dreamstate exists)→ZenForest→dungeon. Dreamstate→Zen and Zen→dungeon-entry travel points need wiring (flow subsystem has the travel events; the level-side triggers are missing).
3. **Defeat path unwired**: `EndRun`/Defeated phase exists in RunSubsystem but coordinator has no handler → death mid-run soft-locks the slice. Needs defeat→summary→return-to-bedroom.
4. **Persistence never called**: `RoguelikePersistenceSubsystem` is complete but zero callers — no checkpoint on stage boundary, no run history, so quitting mid-run loses everything. Minimum slice fix: checkpoint at stage transition + clear on run end.
5. **Glide anim state** missing in `ABP_Melusina_Current` (C++ flag `bRuntimeIsGliding` ships already) — glide currently plays airborne pose.
6. **Results screen** (`WBP_Battle_Results`) unauthored — rank/score currently only a text banner.
7. **BP_RoguelikeDungeonGenerator must implement `IMelodiaDungeonRecipeConsumer`** — if it doesn't and `bRequireRecipeConsumer=true`, generation hard-fails. VERIFY FIRST in editor before anything else dungeon-side.
8. **Enemy content is 13 code-hardcoded defs, 0 data assets, ~3 with art BPs** — fine for slice mechanics; ollama lane's JSON batches + `UMelodiaEnemyDataAsset` instances close it later (RGL-009).
9. Quartz beat clock (plan Phase 1.4) — feel upgrade, not slice-blocking; wall-clock judgment works.
10. Seeded room pools (RGL-003) — replayability, explicitly post-slice per completion plan.

## Recommended execution order (slice assembly)
1. Config default map → L_MelusinaMorning (instant).
2. Verify generator implements the recipe-consumer interface (editor check).
3. Wire the travel chain: Dreamstate-exit trigger → ZenForest; ZenForest dungeon gate (`MelodiaFirstDungeonGate` exists in C++!) → dungeon map w/ coordinator `bStartRunOnBeginPlay`.
4. Defeat handler on coordinator (+ persistence checkpoint calls — both are ≤50-line additions to existing classes).
5. Glide ABP state (Sonnet lane task #4, already queued).
6. Playtest the full 20 minutes; log timing per beat; tune staged-turn pacing + traversal en route.
7. Results WBP + bed art + presentation polish (Cursor specs feeding Sonnet).

## Delegation mapping
- **Sonnet editor lane**: items 1, 2, 3, 5, 6 verification + UI imports.
- **Fable (coordinator)**: item 4 (defeat/persistence C++ — judgment-heavy, touches run authority), slice playtest arbitration.
- **Cursor**: Results/UltCutIn/SaveLoad specs (already in handoff).
- **Ollama**: enemy/chart/room-modifier JSON batches (already in handoff).
- **DeepSeek/Cline**: validation report + quarantine list (already in handoff).
