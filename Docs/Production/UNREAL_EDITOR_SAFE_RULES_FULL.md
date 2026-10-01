# Unreal Editor Safe Working Rules — full text

Moved out of `AGENTS.md` on 2026-10-01 because that file exceeded its 32 KB
agent-context budget and was being served truncated. `AGENTS.md` keeps a numbered
index; this is the authoritative full text. **Nothing was deleted.**

All 26 rules are binding. Read the whole list before editor work.

## Safe working rules

1. Check `list_errored_blueprints` and dirty packages before editing.
2. Do not save existing portfolio/Melodia maps or unrelated materials.
3. Duplicate before changing template assets.
4. Prefer one small, verifiable change per session.
5. Use the filesystem backup at `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26` for rollback — the working tree is ~151 GB of largely-unversioned art and a `git clean -fd` or `checkout -- .` would destroy it permanently; the git object store itself is healthy (verified by `git fsck --full` in 2026-08-28).
6. Static graph inspection is not runtime proof.
7. **One editor instance. Always.** On 2026-08-08 three ran concurrently on this project:
   five crash reports in one hour, assets changing mid-edit, and 39 unsaved packages lost to
   a forced kill. Check `Get-Process UnrealEditor` and that port 9316 has exactly one
   listener before any editor work. Decision 025 forbids two MCP surfaces on one graph; this
   is the same hazard one level up.
8. **`MODAL_OPEN` in the log is not a hang.** A modal dialog blocks the game thread, so
   Monolith goes silent and Windows reports "Not Responding". Grep for it before concluding
   the editor is dead — killing it there costs every unsaved package for nothing. An FBX
   import dialog caused exactly this today.
9. **Verify by re-reading.** `success: true` only means nothing threw. `save_asset` returned
   inconclusive at least once; confirm via `list_dirty_packages`.
10. **Search both name forms.** `UnitHasEnoughMP` vs `Unit Has Enough MP` — node instance
    titles are spaced. A substring search on the identifier form missed a live macro and
    produced a confidently wrong "this macro is never called" conclusion.
11. **`ORPHAN` means prove it, not delete it.** `bp_live_path` cannot see `TSoftObjectPtr`
    (Decision 049) or `.umap` actor references (Decisions 020/029d/037a).
12. **A committed export is an output, not an input.** Verifiers here re-derive from the
    live graph every run; do not add a script that asserts against a stored export. The one
    exception is `bp_regression_checker.py`, whose baseline is therefore tracked at
    `Docs/T3D_Baseline/bp_fingerprints.json` and hard-fails when missing.
13. **A variable-reference census misses expose-on-spawn pins.** `find_variable_references`
    counts `K2Node_VariableSet` nodes only. On 2026-08-09 this produced a confident
    "`BP_BattleUI::battleController` has 4 reads and 0 writes" — false: `K2Node_CreateWidget`
    writes it through an expose-on-spawn input pin. Before declaring a property unwritten,
    check CreateWidget/SpawnActor nodes that construct the object.
14. **Verify the editor lock directly; never trust a report of it.** Attempt a write-open on
    `Binaries/Win64/UnrealEditor-BS_GodFile.dll`. Twice on 2026-08-09 a lane reported the DLL
    locked when it was writable, and the real blocker was a compile error that would have
    failed the build the moment anyone tried. A "blocked on the editor" claim from another
    lane is a hypothesis, not a fact.
15. **Live Coding cannot introduce new imports.** `.cpp`-only edits hot-patch fine
    (`editor_query live_compile`). The moment a change calls a symbol the compiled binary
    never imported, it fails with no useful message in the editor log. Any header change —
    new class, new `UFUNCTION`, new `UPROPERTY` — always needs a full closed-editor build.
16. **Do not hand-build engine data structures.** A runtime `UMidiFile` carrying only a tempo
    change crashed the editor (`EXCEPTION_ACCESS_VIOLATION` reading `0x4` inside HarmonixMidi)
    because a valid song map also needs `Init(ticksPerQuarter)` and a **bar map**. Copy the
    engine's own construction path — `UMusicClockComponent::MakeDefaultSongMap()` — or use a
    properly imported asset. Guarding around a malformed structure is the wrong fix.
17. **Parallelise research, never the editor.** Six read-only explorer agents ran concurrently
    on 2026-08-09 with no incident because none touched the editor. Source/C++ work also
    parallelises — it builds while the editor is closed. All editor work (PIE, CDO edits, T3D,
    graph reads) must serialise through one holder. Another MCP server does not help; Monolith
    runs in-process, so a second surface is a second writer on the same lock.
18. **The allowlist does NOT fail closed in editor builds.** `bRelaxedAllowlistInEditor = true`
    on `DA_MelodiaIntegrationConfig` lets unregistered narrative ids pass with a warning in
    every non-shipping build; it fails closed only in `UE_BUILD_SHIPPING`. An authored typo
    therefore works in PIE and breaks in a packaged demo. Run a verification pass with it off.
19. **`Content/_ThirdParty/TurnBasedJRPGTemplate/` is not a pristine copy** — 156 Blueprints vs
    205/206, missing whole subsystems, and its `BP_BattleController` was edited after copying.
    The trustworthy stock reference is the standalone project at
    `CompatibilityLabs/TurnBasedJRPGUE58`. Copy **node clusters, never whole files**: live
    `BP_BattleUI` is 667KB vs 457KB stock, and that difference is authored rhythm-HUD work.
20. **A dump cannot prove absence.** On 2026-08-09 a full string dump of
    `DA_MelodiaIntegrationConfig` concluded `StockSkillRhythmIds` had "no such property and no
    `MapProperty`", and the whole rhythm investigation was built on that. It had an entry the
    entire time. This is rule 13 generalised: **census and dump methods can confirm presence,
    never absence.** To establish that something is missing, read it through reflection —
    `get_cdo_properties`, not a text search of the asset.
21. **"The build is green" decays into a lie.** Adaptive unity keeps recently-changed files in
    separate translation units, so a tree can build incrementally for days while being
    unbuildable from clean. On 2026-08-10 three of four blockers were unity-build symbol
    collisions (two anonymous-namespace constants, one third-party plugin pair) that only
    appeared on a full rebuild. **Do a full closed-editor build before trusting a green claim,
    and before starting editor work** — discovering it after an hour in the editor wastes the
    session. Fix collisions by qualifying the name or, for vendored plugins, `bUseUnity =
    false` on that module only.
22. **A file existing is not a file compiling.** `MelodiaJRPGPostBattleLibrary.cpp` sat in the
    tree for a day looking like finished work; it had never once compiled — a UE 5.7 include
    path, a typed accessor called on a base `FProperty*`, and `&` of a temporary. Before
    planning around code another lane left behind, **build it**. Note UE 5.8 moved
    `UserDefinedStruct.h` from `Engine/` to CoreUObject's `StructUtils/`.
23. **Check Monolith's own namespace before declaring something impossible.** Moving actors
    between levels is `mesh_query manage_sublevel {sub_action: "move_actors"}`. On 2026-08-10 an
    agent burned an hour on `EditorLevelUtils` (both variants demand a `LevelStreaming`
    destination, so neither can target the persistent level) and `ACTOR COPY`/`ACTOR PASTE`
    (no-ops headlessly, via both the Python console and `run_console_command`), then wrote
    "cannot be automated" into a handoff — with the correct action sitting in a `monolith_discover`
    result already in context. **1330 actions across 24 namespaces: search the list before
    concluding a capability is absent.** Related trap: `manage_sublevel` takes actor *names*,
    not labels, and names repeat across levels (`StaticMeshActor_1`, `PointLight_0`, `PCGVolume_0`
    all exist in more than one). Move unambiguous actors first and verify per-level counts after
    every batch — a silent no-op and a silent wrong-actor move look identical from the return value.
24. **A level actor listing aggregates sublevels.** `get_level_actors` reports actors from
    streaming sublevels alongside the persistent level, which is how "the encounter actor is in
    `L_KaleidoNave`" survived a session — it is in `L_Melodia_Dreamstate`, streamed in. The
    distinction is load-bearing: a sublevel that is not set to load at startup is **absent from
    the PIE world**. Read the `sublevel` field, and confirm at runtime with a tag probe.

25. **Cron jobs sharing the same `workdir` lock each other out.** Two daemons with `workdir: C:\EnvironmentPortfolio\BS_GodFile` will deadlock on the TERMINAL_CWD write lock — the second job times out after 660s with `TimeoutError`. Fix: remove `workdir` from the job config (use absolute paths in prompts) or stagger schedules so they never overlap.

26. **`Saved/Audit/*.json` commits are allowed.** Daemon-produced specs and audit reports in `Saved/Audit/` are explicitly allowlisted in `.githooks/pre-commit` (line 68: `grep -Ev '^Saved/Audit/.*\.(json|md)\$'`). They do not need owner sign-off to commit.
