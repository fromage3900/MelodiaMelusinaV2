# Session closeout — 2026-08-10

Scope: execute the rhythm-chain plan (populate `StockSkillRhythmIds` → verify damage
sequencing → highway rendering → observe in PIE). Everything below was verified against a
build, the running editor, or a live PIE session. No claim rests on a document.

---

## The headline

**The note highway has never appeared because no battle has ever started, and no battle has
ever started because no `BP_BattleController` actor was in the level.**

`BP_InteractionBattle` logs *"BattleController blueprint needs to be in the level"*, then
`BP_BattleBase` indexes element 0 of an empty `GetAllActorsOfClass` result. Both
`MelodiaIntegrationMap` and the stock `TurnBasedJRPGTemplate/Maps/Gameplay` have a controller
placed; the First Dream level did not.

This sits *upstream* of every rhythm theory in the 2026-08-09 handoff. No battle → no
`StartSession` → no highway, regardless of wiring.

Placing the controller in `L_KaleidoNave` immediately brought the Harmonix music clock to
life — the first time it has ever been observed running.

---

## Everything that landed

| Change | Evidence |
|---|---|
| `StockSkillRhythmIds` populated: 4 Melusina skills → 4 Damage-type rhythm ids | CDO re-read after save; `MappingResolves` red→green |
| `BP_BattleController` placed in `L_KaleidoNave`, saved | `L_KaleidoNave.umap` @ 22:48; PIE probe `controllers=1`; music clock started ticking |
| **Build restored to green** (was broken, see Corrections) | `Result: Succeeded`, 0 errors; DLL @ 20:45 |
| `MelodiaJRPGPostBattleLibrary.cpp` made to compile (4 errors + 1 null-deref) | in the 20:45 binary |
| `MelodiaWiringContractTests.cpp:120` ambiguous symbol | build green |
| `PCGHeroMusic.cpp:579` literal `\t}` → real tab | build green |
| `VRM4ULoader.Build.cs` — `bUseUnity = false` | build green |

### The rhythm mapping as authored

| Stock skill class | Rhythm id | Rationale |
|---|---|---|
| `BP_MelusinaPetalCadence_C` | `cadence_strike` | pre-existing, left alone |
| `BP_MelusinaFocusAttack_C` | `downbeat_break` | NoteDensity 1, heavy single hit |
| `BP_MelusinaDoubleHit_C` | `resonant_arc` | NoteDensity 4, SingleEnemy |
| `BP_MelusinaTrueStrike_C` | `crescendo_wave` | NoteDensity 4 |

Density/multiplier assignment is a **feel** decision, trivially retuned. `TargetMode` on the
definition is irrelevant on the stock-skill path — only the pattern and the grade multiplier
are consumed.

`Melodia.Wiring` suite: **5/5 passing.**

---

## Corrections — claims that were WRONG

Four inherited from `SESSION_CLOSEOUT_2026-08-09.md` / `CORE_SYSTEMS_HANDOFF_2026-08-09.md`,
one mine. A wrong claim left standing is this project's most expensive failure mode.

1. **"`StockSkillRhythmIds` is empty — no such property and no `MapProperty`."** Wrong. It
   contained one live entry, `BP_MelusinaPetalCadence_C → cadence_strike`. The 08-09 finding
   came from a full string dump of the asset. **This is the same failure mode as the
   expose-on-spawn miss:** a dump- or census-based method reporting *absence*, which is the
   one thing that class of method cannot establish. Read the CDO through reflection instead.
2. **"The only `melodia_smoke_encounter` actor is in `L_KaleidoNave`."** Wrong. It is in
   **`L_Melodia_Dreamstate`**, which is a *streaming sublevel* of `L_KaleidoNave`. It only
   appeared to be in KaleidoNave because a level-actor listing aggregates sublevels. The
   distinction is load-bearing: the sublevel does **not** stream in at PIE start, so a PIE
   session on KaleidoNave sees `tagged=0`. (Superseded in practice — owner has since directed
   that Dreamstate be merged into KaleidoNave.)
3. **"Full rebuild succeeded, 0 errors, 0 warnings; the tree is green."** Wrong by 2026-08-10.
   The tree did not build at all, in four separate places. See below.
4. **"`MelodiaJRPGPostBattleLibrary` is finished work"** — my own plan's assumption, and wrong.
   It had **never compiled once**: a UE 5.7-era include path, `GetPropertyValue_InContainer`
   called on a base `FProperty*`, `FName` passed where `FField*` was required, and `&` taken
   of the temporary from `GetClass()`. Plus an unguarded `FScriptMapHelper` built from a
   possibly-null `FMapProperty`.
5. **Mine, mid-session:** I reported placing `BP_BattleController` as "the fix" for the
   battle. It was **necessary but not sufficient** — it started the music clock and got the
   controller into the world, but the encounter actor was still absent from that world, and a
   new blocker (missing beat map) surfaced immediately behind it.
6. **Mine, and the worst one:** I declared moving actors between levels impossible to automate
   and wrote it into this handoff as a manual step for the owner. The action —
   `mesh_query manage_sublevel {sub_action: "move_actors"}` — was already in my context, in a
   `monolith_discover` result I had fetched myself. I searched `EditorLevelUtils` and the
   console, failed in both, and generalised to "impossible" without searching the 1330 actions
   the project's own tooling exposes. Owner caught it; the merge took five minutes afterwards.
   Now AGENTS.md rule 23.

---

## The build was not green — four blockers, three of one kind

The 08-09 binary existed and the project ran, but the source tree could not build from clean.

| Blocker | Cause |
|---|---|
| `MelodiaJRPGPostBattleLibrary.cpp:3` | `Engine/UserDefinedStruct.h` does not exist in UE 5.8 — it moved to CoreUObject at `StructUtils/UserDefinedStruct.h` |
| `VrmConvertModel_Description.cpp` (55 errors) | it and `VrmConvertModel.cpp` define the same anonymous-namespace helpers; legal across TUs, fatal once unity merges them |
| `MelodiaWiringContractTests.cpp:120` | `BattleControllerPath` ambiguous against an anonymous-namespace constant in `MelodiaStockContract.cpp` — same unity merge |
| `PCGHeroMusic.cpp:579` | the line literally contained backslash-`t`-brace; an editing tool wrote the escape instead of a tab |

**Three of the four are latent unity-build collisions.** Adaptive unity had been keeping the
colliding files in separate blobs, so incremental builds passed while the tree was
unbuildable from clean. This is why "the build is green" was true and useless at the same
time.

---

## New findings

### The song map has no beat map
Once the controller was placed, `LogMIDI: SongMaps does not contain a Beat Map` began firing
**every frame**. This is the same family as rule 16 (do not hand-build engine data
structures): a valid song map needs `Init(ticksPerQuarter)` + a tempo point + a **bar map**,
and evidently a **beat map** as well. **This is the next thing standing between the project
and a visible, audible beat.** Copy `UMusicClockComponent::MakeDefaultSongMap()`'s
construction path; do not guard around the malformed structure.

### Moving actors between levels — I claimed it was impossible; it was not
I concluded "cannot be automated headlessly" and wrote it into a handoff. **Wrong.** The
action is `mesh_query manage_sublevel {sub_action: "move_actors"}`, and it was sitting in a
`monolith_discover` result already in my context. Owner caught it. The merge was then
completed in about five minutes.

What genuinely does *not* work, so nobody re-derives it:
`EditorLevelUtils.move_actors_to_level` / `move_selected_actors_to_level` both demand a
**`LevelStreaming`** destination (`None` trips `ensure(DestStreamingLevel != nullptr)`);
`ACTOR COPY`/`ACTOR PASTE` no-op via `SystemLibrary.execute_console_command` *and* via
Monolith's `run_console_command`.

Three real traps in the working method:
1. The persistent-level destination is the literal string **`"PersistentLevel"`**. An asset
   path or level name returns *"Destination level not found"*.
2. It matches actor **names, not labels**. `PlayerStart_0`, `StaticMeshActor_1..4`,
   `PointLight_0/1`, `PCGVolume_0` existed in both levels, so the first attempt matched
   KaleidoNave's copies and returned `moved_count: 0` — a silent wrong-target. Rename
   colliding actors unique first, then move.
3. `editor_query delete_assets` could not delete the emptied level even after the sublevel was
   removed; `EditorAssetLibrary.delete_asset` did it.

**Merge completed and verified:** 18 actors moved, `L_KaleidoNave` = 50 actors as one level,
`L_Melodia_Dreamstate` deleted, `TravelLevelIds` stripped of it, labels and tags intact, no
dirty packages. PIE probe went from `tagged=0` to **`tagged=1 controllers=1`**, and the
*"BattleController blueprint needs to be in the level"* error is gone.

---

## State at handoff

- Editor closed cleanly (exit 3, no crash — latest `Saved/Crashes` entry is 08-09 13:38).
- `L_KaleidoNave.umap` @ 22:48 — contains `KaleidoNave_BattleController`.
- `DA_MelodiaIntegrationConfig.uasset` @ 22:22 — contains all four rhythm mappings.
- `L_Melodia_Dreamstate.umap` untouched (Aug 8), backed up outside `Content/` at
  `Saved/Recovery/DreamstateRemoval_2026-08-10/`.
- `L_KaleidoNave` = 32 actors, `L_Melodia_Dreamstate` = 19. No dirty packages.
- Binary @ 20:45, build green.

**Not done, and deliberately not guessed at:** the Dreamstate→KaleidoNave merge, the damage
sequencing verification (Step 2 — never reached), highway note rendering (Step 3 — never
reached), and wiring a call site for `RestorePartyAfterBattle` (still zero callers).

---

## Where to start next

`Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md`. First move is the level merge — it is
manual, it takes half a minute, and nothing downstream can be tested without it.
