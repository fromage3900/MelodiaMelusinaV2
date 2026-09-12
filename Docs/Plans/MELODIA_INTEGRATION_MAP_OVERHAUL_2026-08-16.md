# Melodia Integration Map Overhaul + JRPG/Rhythm Polish

**Date:** 2026-08-16
**Owner split:** owner sculpts Cosmic Reaver (boss); this plan covers map, BP kit,
enemies, and the JRPG/rhythm integration loop.
**Test harness:** Echo pipeline, run on a loop; breakages fixed as found.

---

## Ground truth going in

| Fact | Evidence |
|---|---|
| Locomotion repaired | `ABP_Melusina_Current` 7 states, `Locomotion` wired, compile clean, on disk 14:42 |
| Authored idle in place | `A_Melusina_Idle_v22` imported on-contract from the v22 NLA track |
| Puzzle/interaction kit exists | 5 BP children + `WBP_MelodiaInteractionPrompt`, on disk 13:20 |
| Montages wired | 10 assets, 13:34 |
| Water gameplay authority | Native C++, compiled into `UnrealEditor-BS_GodFile.dll` (01:04) |
| Oceanology C++ | **Ports clean on 5.8** — both DLLs build |
| Oceanology shaders | **NOT ported.** Two HLSL errors kill default material → fatal at editor start. Keep `Enabled: false` |
| Atlantis | **NOT imported.** Empty folder, two OOM failures. Not required for this plan |
| Melody Slime | Data-driven already: `DT_MelodySlime_Enemies`, `_Skills`, `_RoomMods` + `BP_MelodySlimeBattle` |
| Cosmic Reaver retarget base | `SK_Mannequin` present (`/Game/TurnBasedJRPGTemplate/Meshes/SK_Mannequin`) |

**Standing constraint:** the editor has been unstable all session — Monolith drops
mid-batch and unsaved graph work is lost. **Every mutation batch must end in
compile → save → disk-mtime check.** `saved: true` is not proof; the `.uasset`
timestamp is. This has bitten three times.

---

## Phase 1 — Map inventory and truth pass (read-only, do first)

`MelodiaIntegrationMap.umap` is the disposable proof map (the player route is
`L_MelusinaMorning → L_KaleidoNave` and is owner-controlled — do not touch it).

1. Enumerate every actor currently placed; classify keep / replace / delete.
2. Confirm exactly one player-pawn authority (`BP_MelusinaJRPGCharacter`) and one
   PlayerController. The 2026-08 bugfix spec warns about duplicate pawn candidates.
3. Record to `Saved/Audit/integration_map_inventory.json`. That file becomes the
   before-state for the overhaul.

## Phase 2 — Core gameplay BP kit placement

The kit already exists from the P0 materialization; the gap is **placement**, not authoring.

Place and configure in the map:

| BP | Role |
|---|---|
| `BP_MelodiaJRPGGameMode` + `BP_MelodiaJRPGPlayerController` | authority — verify map override |
| `BP_MelusinaJRPGCharacter` | single player pawn |
| `BP_MelodiaEncounter_FirstDream` | encounter trigger |
| `BP_MelodiaEnemy_SingleStock` | **repoint to Melody Slime** (Phase 3) |
| `BP_MelodiaTraversalGate_HoverFixture` | traversal gate proof |
| `BP_MelodiaPortal_LockedTraversal` | route lock |
| `BP_MelodiaStateAnchor_FirstDreamProgress` | progress persistence |
| `BP_MelodiaWorldChallenge_FirstResonance` | optional challenge |
| `BP_MelodiaPuzzleRelay_FirstResonance` | spatial puzzle → water route → quest flag |
| `BP_MelodiaInteraction_DreamAnchor` | interaction + prompt |
| `BP_MelodiaMovingPlatform_Base` | platform traversal |

Spacing: keep fixtures far enough apart that trigger volumes cannot chain-fire.

## Phase 3 — Melody Slime as the default enemy

Owner wants slime variants to author from. The data already exists, so **no new
authority** — extend the DataTables and reparent, do not write a new enemy class.

1. Point `BP_MelodiaEnemy_SingleStock` (or a `BP_MelodiaEnemy_MelodySlime` child) at the
   Melody Slime rows in `DT_MelodySlime_Enemies`.
2. Confirm `BP_MelodySlimeBattle` is the battle-side presentation and that the encounter
   references it rather than a stock JRPG enemy.
3. Author **3 variant rows** as the pattern proof (e.g. Tonic / Third / Fifth), differing
   only in data — stats, skill list from `DT_MelodySlime_Skills`, room mods.
4. Acceptance: adding a fourth variant is a DataTable row plus nothing else.

## Phase 4 — Cosmic Reaver retarget lane (owner sculpting in parallel)

Owner confirms the boss uses the **default UE ThirdPerson skeleton**, so this is the easy
path — but it is still a *foreign* skeleton relative to Melusina's 465-bone ARP rig.

1. Source rig: `SK_Mannequin`. A `RTG_UE4Mannequin_To_Melusina` and
   `IK_UE4Mannequin_Source` already exist — reuse, do not create a second retargeter.
2. **Align the retarget pose before baking anything.** The Quaternius retargeter had
   `bone_delta_count: 0` and produced arms-overhead garbage; `align_retarget_pose` fixed it
   (32 deltas). Assume any new retargeter needs the same and verify the delta count is
   non-zero before trusting output.
3. Boss animations stay on the Mannequin skeleton; only retarget if they must play on
   Melusina. Enemies keep their own skeleton.

## Phase 5 — JRPG + rhythm integration polish

1. **Rhythm HUD** — `PaintNoteHighway` lane fix is already compiled in (DLL 08-16 01:04;
   `_TASK_QUEUE.md`'s "BUILD OWED" is stale). Verify four lanes render as columns in PIE.
2. **Skill → rhythm id** — currently a central map keyed by generated class name
   (`StockSkillRhythmIds`). Long-term gap: skills are not self-describing. Note it; do not
   restructure during the overhaul.
3. **Battle ↔ encounter ↔ quest** — encounter completion must route through
   `UMelodiaNarrativeSubsystem` (`CompleteQuest`, `SetNarrativeFlag`), which is
   allowlist-validated and exactly-once. Never write a parallel flag path.
4. **Puzzle → water → quest** chain (in progress): `OnPuzzleActivated` →
   `SetRouteOpen(first_resonance_route)` → `SetNarrativeFlag(first_resonance_solved)`.
   Nodes and connections were authored; pin defaults + save still outstanding.

## Phase 6 — Echo pipeline on a loop

`Tools/echo_run.py` is the harness. Stage order is
`author → spec_validate → inject → compile → static_gates → runtime_gates → record → promote`.

Loop each iteration:

```bash
python Tools/echo_run.py status
```
```bash
python Tools/echo_run.py validate-spec <spec>
```

- `status` works offline and self-labels stale rows — trust it.
- `static_gates` needs Monolith: reachability, live-path, UI lint, sweep, baseline.
- **`static_gates` was failing 2026-08-14** on two material baseline drifts. Expect it red;
  fix or re-baseline rather than ignoring.
- Record every gate result — a claim without a ledger row is not a claim.

## Phase 7 — Verification

1. Map inventory before/after diff.
2. Compile clean on every touched BP; `.uasset` mtime confirms each save.
3. PIE in `MelodiaIntegrationMap`: walk/run/idle → interact prompt → puzzle solves →
   water route opens → quest flag set → encounter starts → slime battle → rhythm lanes
   render → result returns to exploration.
4. Echo gates recorded.

---

## Known hazards

- **Do not enable Oceanology.** Shaders unported; fatal at editor startup.
- **Editor instability** — save and verify after every batch.
- **`add_transition` / `create_blueprint` are not idempotent** — read existing state first.
- **A JSON body can report failure while the transport succeeds** — check `success`/`ok`.
- **Monolith param names differ per action** — read `describe_query action_schema`
  (`target_action`, not `target`) rather than guessing.
