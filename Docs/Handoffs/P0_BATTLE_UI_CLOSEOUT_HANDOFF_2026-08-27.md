# P0 Battle + UI Closeout — Session Handoff 2026-08-27

**Status: two P0 gates closed, Quill dialogue restored, one hard blocker removed.**
Read this before touching battle, UI, or packaging.

---

## 1. The root cause of the multi-week stall: a stale DLL

Bridge source edited 2026-08-26 23:36 added new `UFUNCTION`/`UPROPERTY`/enums. Live Coding **cannot**
hot-patch those (AGENTS.md rule 15), so it reported `patch_applied=true` then failed, and
`UnrealEditor-BS_GodFile.dll` sat at **2026-08-24 23:29**.

**Every PIE result before 2026-08-27 12:28 was testing three-day-old binaries.**

Fix: closed-editor UBT rebuild.
```
"C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" \
  BS_GodFileEditor Win64 Development \
  -Project="C:/EnvironmentPortfolio/BS_GodFile/BS_GodFile.uproject" -WaitMutex
```
332 actions, 377s, `Result: Succeeded`. `UnrealEditor-BS_GodFile.dll` → 12:28,
`UnrealEditor-Quillscript.dll` → 12:27.

---

## 2. `battle_integration_map` → **PASS** (all four terminal outcomes)

**Blocker was one empty array.** `BP_InteractionBattle` (Actor Tag `melodia_smoke_encounter`, in
`MelodiaIntegrationMap`) had `enemyList = []`, so
`MelodiaExternalJRPGBridgeSubsystem.cpp:130` rejected every battle with
*"tagged battle actor has no authored enemy roster."* Every other contract check passed.

Authored: one row, key `BP_WeakEnemy_C`, defaults `spawnChance=1.0 minLevel=1 maxLevel=1`.
Map saved 13:07. Result: `Melodia JRPG bridge started melodia_smoke_encounter on BP_InteractionBattle_2.`

| outcome | how driven | typed result |
|---|---|---|
| `unavailable` | pre-fix abort path | — |
| `victory` | `SetHP(0)` on `BP_WeakEnemy_C` | `result=victory`, `typed=0` |
| `defeat` | `SetHP(0)` on `BP_SirMelodiousPlayerUnit_C` | `result=defeat`, `typed=1` |
| `fled` | `fleeChance=100` + `BP_BattleController.Flee(playerUnit)` | `result=fled`, `typed=2` |

**Quill resumed exactly once on every outcome** (`MELUSINA_LOOP_QUILL_RESTORE` → `_NEXT`, never twice).

**P0-NARR-01 atomic commit proven live** on the victory branch, in order:
```
melodia:quest:melodia_q_echo_01
melodia:reward:melodia_smoke_reward
melodia:flag:melodia_smoke_complete:true
Script 'MelodiaQuillSmoke' ended
```
The fled branch committed **only** the flag — commit is genuinely branch-conditional.

---

## 3. `hud_single_writer` → **PASS pending owner decision**

Direct property reads during a live battle:
```
battleUI                = BP_BattleUI_C_0
widget.battleController = BP_BattleController_2    MATCH=True
melodiaBattleUI = None ; MelodiaUI = None   (properties exist, unused)
```
`melodiaBattleUI`/`MelodiaUI` are **vestigial pre-bridge variables** (category "Melodia"), not a
broken binding. The 2026-08-26 note *"both None, HUD not bound"* measured the wrong properties.
`EnsureStockBattleUIControllerReference` returns true **silently** when already linked, so absence of
`MELODIA_BATTLEUI_LINK` is success.

**Owner decision needed:** retire the two vestigial variables to fully close this gate.

---

## 4. Quill dialogue visibility restored (commit `e1d1b4cd`) — OWNER CONFIRMED ON SCREEN

`WBP_MelodiaQuillDialog`'s `Event Play` override shadowed native
`UMelodiaQuillDialogWidget::Play_Implementation`, so `AddToViewportAtLayer()`, `SpeakerText`/`BodyText`
and `AdvanceButton` focus never ran — the box was constructed but never added to the viewport. An
unfinished typewriter feature had replaced the working override with no parent call (its downstream
nodes still have disconnected exec pins).

Fixed by injecting `K2Node_CallParentFunction` ("Parent: Play") as the first link, via
`validate_nodes_t3d` → `inject_nodes_t3d` → `connect_pins_bulk`:
```
Event Play.then -> Parent: Play -> SetPortrait -> (existing chain)
Speaker/Text/Tags fan out to Parent: Play   (SetPortrait keeps Speaker, portrait preserved)
```
Compile 0/0; fingerprint `d956ebd6` → `d8eae2b3` (26→27 nodes, 11→15 connections).

**`WBP_MelodiaQuillSelection` / `WBP_MelodiaQuillBackground` were never affected** — their `Event Play`
nodes are **disabled**, so they already fell through to native. Only Dialog had the override.

---

## 5. How to drive a battle in PIE (non-obvious — cost many cycles)

`StartBattle` refuses with `MissingRuntime` (enum 5) unless a **Quill interpreter is live**. Battles are
script-driven by design. **An idle PIE smoke can NEVER start a battle** — so every historical
"idle smoke passed, no battle started" note proved nothing about the battle gates.

Working procedure via `editor_query run_pie_smoke` + `probe_scripts`:
1. `unreal.Quill.play_script(world, unreal.load_asset('/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke'))`
2. `i = unreal.Quill.get_interpreters(world)[0]`; `o = i.get_options_set(-1)`; `i.option_selected(o[0])`
3. `i.next()` repeatedly → fires `$ Notify melodia:battle:melodia_smoke_encounter`
4. Kill a side: `actor.call_method('SetHP', args=(0,))`
5. **Post-battle dialogue does not advance itself** — call `i.next()` again at ~+10s and ~+22s or the
   quest/reward/flag notifies never fire.

Gotchas:
- `unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(world)` is the accessor.
  **`unreal.SubsystemBlueprintLibrary` does not exist in this build.**
- `BP_BattleController.currentTargetUnit` is `DisableEditOnInstance` — cannot be set from Python, so
  `DealDamage` is unusable that way. Use `SetHP`.
- Rejections log `"Melodia intent rejected: <intent> (<enum>)"` — **not** `MELODIA_INTENT_REJECTED`.

---

## 6. Open items for next session

### Blocked on assets (owner)
- **No slime or Cosmic Reaver meshes exist in UE Content.** Searched `SK_*slime*`, `SKM_*slime*`,
  `*slime*`, `*reaver*`, `*cosmic*` — `BP_MelodySlime*` exist but no mesh backs them; "Reaver" matches
  only cosmic *materials*. Owner decision: **import from Blender first, then build variants.**
- **Plan agreed:** 3 MelodySlime variants — Small/Medium/Large — varying scale, stats, shader values.
  Recipe below is ready to execute the moment meshes land.

### MelodySlime variant recipe (ready, unblocked once meshes import)
Duplicate `/Game/TurnBasedJRPGTemplate/Blueprints/Units/EnemyUnits/BP_WeakEnemy` (a **valid**
`BP_EnemyUnitBase` subclass). Per-variant fields on the CDO:
| knob | field |
|---|---|
| name | `title` (FText) |
| difficulty | `firstLevelStats` / `lastLevelStats` (`maxHP`, `min/maxAttack`, `defense`, `speed`, `hit`, `actionTime`) |
| rewards | `expReward` (25), `goldReward` (1) |
| size | inherited `SkeletalMesh` component `RelativeScale3D` |
| mesh/shader | that component's mesh + material overrides |

Animations inherit free from `BP_UnitBase_C` (`AM_Intro/Idle/Attack/GetHit/Die/Stun`).

**Naming trap:** `BP_MelodySlimeBattle`'s parent is `BP_BattleBase_C` — it is an **encounter**, not an
enemy unit, which is why it cannot be a roster key. It also derives from the `_ThirdParty` template
copy, not `/Game/TurnBasedJRPGTemplate/` — mixed lineage, watch for it.
`BP_MelodiaEnemy_SingleStock` / `BP_MelodiaEnemy_Base` are likewise **not** `BP_EnemyUnitBase`
subclasses and are rejected as roster keys.

### Choral Sheep — it is NOT a quest
No Quill script, no quest ID, no flag, no reward, no allowlist entry. It is a **non-combat companion**
(`combat: false`, Graze/Harmonize/Guide), classified `PRESENTATION_ONLY`.
`BP_ChoralSheep.uasset` + `DA_ChoralSheepDefinition.uasset` exist (2026-08-25).
**Hard blocker:** source mesh `Skin_Sheep_ZSpheres2` (5,918 verts) has **0 vertex groups** — unskinned,
so no `SK_ChoralSheep`, no rig, no ABP, no coat MIs. Variants JSON status:
`coat_pipeline_ready_weight_paint_blocked_pending_blend_transfer`.
**Owner's blendshape-driven approach is the unblock** — it sidesteps weight painting entirely.
Unresolved: map conflict `L_ChoralSheep_Prototype` vs `MelodiaIntegrationMap`.

### Known defects (none block P0 gates)
- **Player death crashes the editor**: `Assertion failed: false [AnimMontage.h] [Line: 781]` ~10s after
  `SetHP(0)` on `BP_SirMelodiousPlayerUnit_C`. The defeat result lands correctly first. Prefer the flee
  path when a non-crashing terminal outcome is needed.
- **`LiveResultsWidgetPath` is empty.** `UCLASS()` has no `config` specifier and the property has no
  `Config` flag, so **ini cannot set it**. `Initialize()` backfills `MelodiaBattleWidgetPath` (~L99) but
  not this one. Fix = mirror that backfill using
  `/Game/Melodia/UI/WBP_Battle_Results.WBP_Battle_Results_C` (verified to derive from
  `MelodiaBattleResultsWidget`). **Requires a rebuild.**
- **Quill background panel never renders**: no `.qsc` in the project uses a background command at all.
  `Background(UTexture*, Transition, Duration)` / alias `Bg(...)` is the API; nothing calls it.
  Separately, `WBP_MelodiaQuillDialog`'s `ParchmentPanel` Image is Visible at z-order 10 — if it shows
  nothing its brush texture is likely unassigned.
- Plugin bug: `AQuillscriptInterpreter::Wakeup_Implementation` calls `ShowBackgroundBox()` **twice**
  (L438-439); the second is almost certainly meant to be `ShowSelectionBox()`.

---

## 7. Shipping to itch — reality check

- **No itch tooling exists in this repo.** No `butler`, no `.itch.toml`, no upload script. First upload
  will be manual. `deploy/package_game.ps1` even says "upload to GitHub Releases", contradicting
  `_DECISION_LOG.md` Decision 004 (itch.io).
- Working pipeline: `deploy/BuildGraph/Invoke-MelodiaBuildGraph.ps1 -Target MelodiaBuild`
  (`ValidateContracts → CookPackage → Gauntlet → PublishArtifact`).
- **Disk was the hard blocker.** C: was at 6.8 GB free / 100%. Moved ~12 GB to
  `G:/BS_GodFile_Archive/20260827/` — an 11 GB `OceanologyLegacy-UE5.8-package-20260825` staged archive
  (Oceanology is `"Enabled": false` in the .uproject and the installed
  `Plugins/Oceanology_Plugin` has no `.uplugin`), plus Gaea staged dirs. **C: now 19 GB free.**
  `Products/Builds/BuildGraph` (2.7 GB, Aug-14 package, 156 commits stale) did **not** move — still there.
- `ProceduralModelingToolkit` is **editor-only** (no runtime module) — verify nothing shipped depends on
  its classes before cooking.
- Do **not** re-add `DirectoriesToNeverCook=(Path="/PCGExtendedToolkit")` — it was tried and reverted
  (cook exit 25 class).

---

## 8. Tooling notes

- **Text injection pipeline is CORE, not deprecated** (owner: "like half our game pipeline"). Primary
  path for wiring. `add_node` **cannot** create `K2Node_CallParentFunction` — T3D injection is the only
  way. Always `validate_nodes_t3d` (or `dry_run:true`) first.
  Narrow caveat: `Docs/T3D_Patterns/t3d.py` imports `safe_wire` from `Tools/t3d_safe_wire.py`, flagged
  STALED in the 2026-08-14 postmortem — call the MCP actions directly instead.
- `AGENTS.md`'s T3D tool table is **stale**: points at `Tools/t3d_blueprint_injector.py`, archived to
  `Tools/_Archive/T3D_20260818/`.
- **`melodia_config_get_allowlist` (MCP) returns STALE FIXTURE DATA** that matches nothing live. Use
  `blueprint_query get_cdo_properties` on `DA_MelodiaIntegrationConfig` for config truth.
- **Log rotation trap:** a second editor instance writes `Saved/Logs/BS_GodFile_2.log`, not
  `BS_GodFile.log`. Check `ls -lt Saved/Logs/` before concluding "the run produced nothing".
- **Parallelism ceiling:** PIE / graph mutation / editor Python is ONE serialized lane (one editor, one
  MCP surface on 9316). Subagents are useful for offline analysis and authoring only — three Sonnet
  Explore agents this session found the Quill defect, the disk blocker, and the packaging path.
- Editor crashed twice (water-PBR DDC build; AnimMontage assert). Engine init ~150-250s.

---

## 9. Current gate state

| gate | status |
|---|---|
| `battle_integration_map` | **pass** |
| `hud_single_writer` | **pass** pending owner decision on vestigial vars |
| `rhythm_owner` | open |
| `rhythm_grade_to_result` | open |
| `wardrobe_equip_roundtrip` | open |
| `wardrobe_gameplay_hook` | open |
| `music_world_key` | open |
| `static_gates` | fail |

Full evidence in `Docs/P0_TASK_LEDGER.json` → `agent_work_log_2026-08-27`.
Backup of the pre-session ledger: `Docs/P0_TASK_LEDGER.json.bak-20260827`.

---

## 10. Amendment — incomplete sweep (read before planning enemy work)

**The Melodia battle-enemy inventory was NOT completed.** A background sweep of every Melodia enemy
asset (parent classes, backing meshes/materials, `DA_MelodiaEnemyCatalog` / `DT_MelodySlime_*` wiring,
and the minimum change to make a real Melodia enemy fight) was launched but **terminated early on an
API session limit**. No findings were produced. Treat enemy-asset knowledge in this handoff as
partial — only these facts are verified:

- `BP_WeakEnemy` / `BP_AverageEnemy` / `BP_BossEnemy` ARE valid `BP_EnemyUnitBase` subclasses and are
  accepted as `enemyList` roster keys.
- `BP_MelodiaEnemy_SingleStock` and `BP_MelodiaEnemy_Base` are NOT — rejected at the key
  (`ClassProperty` MetaClass mismatch).
- `BP_MelodySlimeBattle` parents to `BP_BattleBase_C` (an encounter, not a unit) and derives from the
  `_ThirdParty` template copy.
- No slime / Cosmic Reaver **meshes** were found in Content by name search.

**Not yet checked:** `/Game/Melodia/Enemies/*` parent classes (`BP_Enemy_CrystalShard`,
`BP_Enemy_SakuraPhantom`, `BP_Enemy_StoneGolem`, `BP_MelodiaEnemyBase`,
`CrystalShard/BP_CrystalShard_SlimePlaceholder`), what `DA_MelodiaEnemyCatalog` and the
`DT_MelodySlime_*` tables define, whether anything consumes them, and whether MelodiaCore holds enemy
classes. Re-run that sweep first next session.
