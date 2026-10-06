# Hybrid Combat Trial Web — what it is and how it hangs together

**Status:** confirmed 2026-10-05 (disk sweeps with `--no-ignore` over all of `Content` + sequential single-asset editor reads; no parallel loads after the 2026-10-05 OOM). Companion to `MELUSINA_RUNTIME_CANON_2026-10-05.md`, which remains the rig/retarget authority — this doc owns **combat-trial organization only**.

**One-line version:** the trial web is **harness around the converged path, not a fork of it**. The converged runtime is `BP_MelusinaJRPGCharacter` (`runtime_unit` per `Docs/P1_TASK_LEDGER.json:17`) with its native components. Everything under `Content/Melodia/CombatTrial/` stages, probes, or playtests that path. The two ACF pawns carry a genuinely different parent class (see §5) and stay off the boot path; everything else in the trial web inherits canonical-family classes.

## 1. The converged path (the thing the harness exercises)

On the canonical pawn, in PIE:

1. `MelodiaTraversalComponent` guarantees a `UMelodiaWaveHarpCombatComponent` exists on the owner character (auto-created if missing — `MelodiaTraversalComponent.cpp:56`).
2. LMB = caster basic attack, RMB = charged Sparrow draw/hold/fire through the WaveHarp component (chord semitones 0/4/7/11/12, fifth-shot reset; floating astrolabe vs bow morphs).
3. Aim finds the nearest actor carrying `UMelodiaHybridEncounterComponent`; projectiles (`AMelodiaWaveArrow`) resolve hits against it.
4. `HybridEncounterComponent` owns **presentation/input transition only** (FLOW ↔ SEQUENCE). Damage arrives only as already-resolved stock numbers via `ApplyResolvedFlowDamage` / `ApplyResolvedSequenceDamage`.
5. `AMelodiaWorldSlimeNode` owns the single HP value and stays in the world across mode changes; `UMelodiaExternalJRPGBridgeSubsystem` binds the stock resolver (`BindWorldDamageResolver` / `ResolveWorldFlowAttack`) and closes the loop to the typed narrative result.
6. Boot: project `GlobalDefaultGameMode` (`Config/DefaultEngine.ini`) = `BP_MelodiaJRPGGameMode`, whose pawn is the canonical character; `P0PlayerClass` in `MelodiaIntegrationConfig.cpp` agrees.

No trial asset re-implements any of this. That is the convergence claim, and it is why the trial web is documentation debt, not architecture debt.

## 2. Trial-web inventory (editor-confirmed parents)

| Asset | Parent (editor read 2026-10-05) | Role | Wired to / by |
|---|---|---|---|
| `BP_MelusinaWaveHarpFlurry` | `BP_MelusinaJRPGCharacter_C` — **the canonical pawn**, compiles `UpToDate`, 8 vars / 1 func | WaveHarp shot/caster proof unit | References canonical pawn + ProofBow + ProofArrowItem; referenced by both trial GameModes + PlayerUnit |
| `BP_MelusinaWaveHarpPlayerUnit` | `BP_MelusinaSwordsman_Presentation_C` — **the battle presenter**, data-only, 0 SCS comps, compiles `UpToDate` | Possessable wrapper for the Flurry in trial maps | Referenced by `BP_ZenForestWaveHarpPlayerController`; references Flurry + Swordsman |
| `BP_WaveHarpProofBow` / `ProofArrowItem` | — | Instrument + projectile proof props | Referenced by Flurry |
| `BP_WaveHarpProofArrowActor` | — | Dead proof prop | **No referencers and no dependencies in the project index; self-only on disk.** Delete when the proof trio is retired |
| `BP_WaveHarpTestAttackerStats` / `DefenderStats` | stat views | Stock resolver inputs for the playtest | Placed in `L_HybridWaveHarpPlaytest`; staged by `Content/Python/stage_hybrid_waveharp_playtest.py` |
| `BP_ACFTrialGameMode` | (not read — harness) | GameMode of `L_ZenForestACFTrial`; references Flurry | Tools: `acf_trial_preflight`, `acf_trial_host_probe`, `acf_hybrid_p1/p2`, `build_acf_trial_level` |
| `BP_ACFTrialGameState` | — | Trial match state | Tool refs only |
| `BP_ACFTrialEnemy` | — | Trial opponent | Tool refs only |
| `BP_ZenForestWaveHarpGameMode` | references `BP_MelodiaJRPGGameMode` (disk) + Flurry | WaveHarp-flavored trial GameMode — **extends the canonical GameMode, not a fork** | Trial web |
| `BP_ZenForestWaveHarpPlayerController` | — | Trial PC | References PlayerUnit + Swordsman |
| `BP_MelusinaACFHybrid` | `ACFPlayerCharacterBP_C` (disk + editor) | ACF-hierarchy experiment pawn | `Tools/acf_hybrid_*`; carries a live `CharacterMesh0` pin warning. Package contains a `BP_MelusinaJRPGCharacter` class-path string but **no graph node by that name** (title search, both name forms) — pin default or saved import, non-load-bearing |
| `BP_MelusinaACFTrial` | `ACFPlayerCharacterBP_C` (disk) | Sibling experiment pawn | Tool refs only |
| `BP_HybridSlimeNode` | — | Unused slime-side harness node | **No referencers and no dependencies in the project index; self-only on disk.** Only mention is `Tools/acf_hybrid_p1_character_probe.py`. Delete with the ArrowActor unless a probe script is shown to stage it |
| `L_HybridWaveHarpPlaytest` / `L_ZenForestACFTrial` | — | The two playtest maps | Playtest hosts HybridStats; ZenForest hosts ACFTrialGameMode + `BP_EnemyUnit_MelodySlime` + RoomExit + DungeonGenerator |

## 3. Boot paths (which GameMode runs where)

- **Production:** project default → `BP_MelodiaJRPGGameMode` → canonical pawn. `L_MelusinaMorning` (World-Partition external actors — the `.umap` itself is nearly empty; always sweep `Content/__ExternalActors__/...`) carries no GameMode override found on disk.
- **Trial:** `L_ZenForestACFTrial` → `BP_ACFTrialGameMode`; `L_HybridWaveHarpPlaytest` → references `BP_MelodiaJRPGGameMode` (canonical GM with trial content placed in-map).
- **Rule (already satisfied, keep it):** no production map boots an ACF or ZenForest GameMode. That single invariant is what makes the ACF parent divergence safe.

## 4. Harness tooling (probe/build scripts, not runtime)

`Tools/acf_trial_preflight.py`, `acf_trial_host_probe.py`, `acf_hybrid_p1_character_probe.py`, `acf_hybrid_p2_build.py`, `acf_hybrid_input_probe.py`, `build_acf_trial_level.py`, `Tools/acf_hybrid_p2_build.py`, `Content/Python/stage_hybrid_waveharp_playtest.py`. These stage maps, preflight the trial GameMode/pawns, and probe input/character state. They are the reason the trial BPs look "referenced but homeless" — their referencers are scripts, not maps.

## 5. The one real divergence (kept, guarded, not merged)

Both ACF pawns inherit `ACFPlayerCharacterBP`, a separate character hierarchy from `BP_JRPGCharacterBase`. Consequences that follow from the parent, not from anyone's intent: different native component set (Hybrid: 17 native comps vs canonical's 4; 40 SCS comps vs 44), different movement/combat ownership, and the `CharacterMesh0` pin warning on Hybrid. Policy: **trial-only, never the boot path, never reparented casually** (a reparent would silently rewire movement + mesh slots). If a future pass wants ACF behaviors on the canonical pawn, the move is component-level porting into the existing owners, not pawn replacement. (PR #367 remains reference/provenance only, per the owner-directed migration boundary.)

## 6. Slime-tree ruling (disk-proven 2026-10-05)

The live slime unit is **`/Game/Melodia/_PROJECT/Characters/Enemies/BP_EnemyUnit_MelodySlime`** — referenced by full package path from the Morning external actor, both ZenForest maps, and six Roguelike `ENC_Slime*` assets. The `Content/_PROJECT/...` twins (same base names) are referenced by none of these. `BP_MelodySlimeEncounter_Test` (IntegrationMap-adjacent, placed in Morning) is the live tutorial encounter shell. Still open: plain `BP_MelodySlime`, `BP_MelodySlimeBattle`, `BP_MelodySlimeExplorePawn` (no referencers found — an earlier "referenced by Encounter_Test" read was a substring self-hit, retracted here), and the root `_PROJECT` twins. None of them may be deleted on this doc alone — each needs its 30-second editor confirm.

## 7. Method note (so future sweeps don't repeat two traps)

1. Morning actors live in `Content/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning/...`, not in the `.umap`. Any grep that only reads `.umap` files reports "Morning references nothing" — false.
2. `rg` without `--no-ignore` skips some `Content` paths (bulk `Content/` is git-ignored); an early pass without the flag produced a flip-flopping result. All zero-claims above were re-verified with `rg -a --no-ignore -F`.
3. Substring self-hits: a search for `BP_MelodySlime` matches `BP_MelodySlimeEncounter_Test`'s own name strings. Confirm every "referenced by" with a full-path read before acting.
4. After the 2026-10-05 parallel-query OOM (`AvailableVirtual 0.01 GiB` → Foreground Worker crash), editor reads for this lane stay **sequential, single-asset, spaced**. The six reads behind §2 were done that way against the restarted editor.
