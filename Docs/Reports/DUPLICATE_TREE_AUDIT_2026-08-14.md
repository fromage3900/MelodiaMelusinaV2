# Duplicate / Legacy Tree Audit — 2026-08-14

Read-only audit of duplicate and legacy trees that make path resolution
unreliable. No deletions were made and none are recommended here: `Content/`
deletion is Red (Ask First) per `CLAUDE.md:99` and requires the owner.

## Summary table

| Tree | Canonical? | Differs? | Referenced by |
|---|---|---|---|
| `Content/Content/Melodia/` | No — nested mirror of `Content/Melodia/DataStuctures/` | Partial (2/3 identical, 1 differs) | Nothing (only noted as "nested mirror dir" in `Docs/SOURCES_MATRIX.md`) |
| `Content/_PROJECT/` | No — legacy root; canonical moved to `/Game/Melodia/_PROJECT` | Yes — divergent sibling of `Content/Melodia/_PROJECT` (574 A-only, 104 B-only, 964 differ, 0 identical) | Legacy `/Game/_PROJECT/...` paths in ~30 Python scripts + many docs (SDF, materials, PCG); flagged as leakage to rewire |
| `.claude/worktrees/magical-williamson-a3534a/` | No — git worktree, detached HEAD `343d091c`, parallel checkout | Yes — slimmer `Content/Melodia` (no Blueprints/), not shipping tree | Explicitly excluded from audits in `Docs/Reports/DEEP_REVIEW_2026-08-14.md:39` and `WBP_BINDING_MATRIX_2026-08-14.md:120` |
| `../_to_delete_2026-08-14/` (workspace sibling) | No — junk/quarantine holding dir | n/a | Nothing — zero references |
| `Content/Blueprints/WBP_RhythmHUD.uasset` (131115 B) | No — tracked, but not the referenced path | Yes — differs from the Melodia copy (hash `A7D0…` vs `FE18…`) | Not referenced as canonical |
| `Content/Melodia/Blueprints/WBP_RhythmHUD.uasset` (131155 B) | **Yes** — canonical `/Game/Melodia/Blueprints/WBP_RhythmHUD` per `bp_fingerprints.json:147` and `compile_playtest_ui_and_owners.py:22` | Yes — differs from `Content/Blueprints` copy | **Referenced as canonical, but git-ignored** (`Content/Melodia/*`, `.gitignore:102`) |
| `Content/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` (102289 B) | No — legacy `_PROJECT` (this is `BP_`, not `WBP_`) | Yes — differs from `Melodia/_PROJECT` sibling (hash `B20B…` vs `7BD4…`) | Tracked; legacy `/Game/_PROJECT` leakage only |
| `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` (103098 B) | Canonical `_PROJECT` HUD (`bp_fingerprints.json:908`) | Yes — differs from `Content/_PROJECT` copy | Tracked; referenced by fingerprints |
| `Content/IMPERFECTER_-_Post_Process_Toolkit_v1.3.1___40_5.6__5.7_` (A) | No — full plugin source mislocated under `Content/` (UE never loads plugins from `Content/`) | Yes — structurally different from B | Nothing loadable; only self-refs + `SOURCES_MATRIX.md`; 0 git-tracked |
| `Content/IMPERFECTER_-_Post_Process_Toolkit_v1_3_1___40_5_6__5_7_` (B) | No — content-only re-save (Resources `.uasset`, no `.uplugin`) | Yes — differs from A | Nothing; 0 git-tracked |

## Per-tree detail

### 1. `Content/Content/Melodia/`

- Contents: `DataStuctures/` with 3 `.json` only (`DT_MelodySlime_Enemies.json`,
  `DT_MelodySlime_RoomMods.json`, `DT_MelodySlime_Skills.json`).
- `Content/Content` contains nothing else.
- Duplicates `Content/Melodia/DataStuctures/`, which holds the same 3 `.json`
  **plus** 14 `.uasset` files.
- Diffs: `Enemies` and `Skills` identical; `RoomMods` differs (12 line-diffs).
- Git: ignored by `Content/*` (`.gitignore:99`), zero tracked files.
- References: none in code, scripts, or docs. A `/Game/Content/...` package path
  never appears anywhere.

### 2. `Content/_PROJECT/` vs `Content/Melodia/_PROJECT/`

- Canonical moved: `Content/Python/paths.py:48` —
  `MELODIA_PROJECT = f"{MELODIA}/_PROJECT"  # was /Game/_PROJECT`;
  `_QuarantineSource_20260731/BrokenReconstructions_20260731/rewrite_content_paths.py:32`
  rewrites `"/Game/_PROJECT"` → `"/Game/Melodia/_PROJECT"`.
- Both trees have the same 13 top-level dirs; `Melodia/_PROJECT` additionally
  holds `BP_MelodiaGameMode.uasset` at its root.
- Full hash comparison: 574 files only in `Content/_PROJECT`, 104 only in
  `Melodia/_PROJECT`, 964 common but differing, **0 identical** → divergent
  siblings, not copies.
- Git: `Content/_PROJECT` has 108 tracked of 1538 on disk; `Melodia/_PROJECT`
  has 153 tracked of 1068 on disk.
- References: heavy legacy usage of `/Game/_PROJECT/...` in Python tooling and
  docs (SDF manifests `Docs/Gumroad/FAB_SDF_PACK_MANIFEST.md`, material audit
  `Docs/MATERIAL_LIBRARY_AUDIT.md`, `M_PP_MeluColorGrade` in
  `check_grade_v3.py`/`inspect_grade.py`, PCG roots in
  `pcg_portfolio_standards.py`). Several docs call this out as leakage to
  rewire to `/Game/EnvSandbox/...` or `/Game/Melodia/_PROJECT`.

### 3. `.claude/worktrees/magical-williamson-a3534a/`

- Git worktree, detached HEAD `343d091c` ("Update PIE_RUNTIME_NOTES_2026-08-12.md").
  Listed by `git worktree list`; `_pr_wt/pr5` is another (prunable).
- `Content/Melodia` is a slim subset: Characters, DataStuctures, Levels, PCG,
  UI, `_PROJECT` — no `Blueprints/`, no `WBP_RhythmHUD`.
- The worktree also carries its own copy of `Plugins/MelodiaCore/Source/`
  noted in `WBP_BINDING_MATRIX_2026-08-14.md:120` as a possibly-diverged
  duplicate that was not audited.
- References: only the two audit docs above, both treating it as excluded.

### 4. `../_to_delete_2026-08-14/`

- Workspace-level (sibling of `BS_GodFile/`) holding dir containing:
  `.clean_repo`, `.repo_recovery_20260727`, `.temp_repo`,
  `BS_GodFile_pr4_merge` (empty), `BT_GodFile`, `my-site-deploy`,
  `_MELUSINA_SAFETY_2026-08-08`, `_pr_wt`, plus cleanup scripts
  (`big_cleanup.ps1`, `recycle_*.ps1`, etc.).
- No references to it anywhere in the repo.

### 5. RhythmHUD copies — four assets, three paths

The "three WBP copies" framing is slightly off: `Content/_PROJECT/Blueprints/`
holds `BP_RhythmHUD` (a `BP_` widget, not `WBP_`). There are four assets:

| Path | Kind | Size | Git | Canonical? |
|---|---|---|---|---|
| `Content/Blueprints/WBP_RhythmHUD.uasset` | WBP | 131115 | tracked | no |
| `Content/Melodia/Blueprints/WBP_RhythmHUD.uasset` | WBP | 131155 | **ignored** | **yes** |
| `Content/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` | BP | 102289 | tracked | no (legacy) |
| `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` | BP | 103098 | tracked | yes (`_PROJECT`) |

- The canonical WBP (`/Game/Melodia/Blueprints/WBP_RhythmHUD`) is the one
  referenced by `compile_playtest_ui_and_owners.py:22` (with parent class
  `/Script/MelodiaCore.MelodiaRhythmHUDWidget`) and `bp_fingerprints.json:147` —
  and it is the git-ignored copy. A divergent duplicate in
  `Content/Blueprints/` is the tracked one.
- Note also `Content/Python/setup_rhythm_ui.py:18` targets a third path,
  `/Game/UI/Rhythm/WBP_RhythmHUD`, which does not exist on disk
  (`Content/UI/` contains only `WidgetStyleSheet.json`).
- Live anchors per `Config/DefaultEngine.ini`: `EditorStartupMap` /
  `GameDefaultMap` = `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu`,
  `GlobalDefaultGameMode` = `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode`.
  Nothing on the `/Game/_PROJECT` or `/Game/Content` roots is on the live path.

### 6. `Content/IMPERFECTER_*` — two name-mangled copies

- Copy A (`v1.3.1___40_5.6__5.7_`, literal dots): a full plugin **source** tree —
  `Imperfecter.uplugin`, `Source/` (runtime + editor), `Binaries/Win64`,
  `Shaders/`, `Config/`, `Intermediate/`, `Resources/*.png`. Double-nested:
  `Content/A/A/IMPERFECTER - Post Process Toolkit v1.3.1 (5.6-5.7)/Imperfecter/`.
- Copy B (`v1_3_1___40_5_6__5_7_`, dots→underscores): content-only re-save —
  `Resources/*.uasset` icons only, no `.uplugin`, no Source, no Binaries.
- The two trees are structurally different (not a name-only duplicate).
- Neither is loadable: Unreal does not load plugins from `Content/`, and no
  `IMPERFECTER` plugin is registered in `.uproject`.
- Git: both fully ignored; 0 tracked files.

### 7. `Plugins/MelodiaTokenWallet/` — inert (4/4 claims confirmed)

1. **No `Modules` array in `.uplugin`** — confirmed. Has FileVersion, Version,
   Name, Description, Category, VersionId, SupportedEngineVersions,
   InstalledPlugins — but no `Modules`. (Contrast `MelodiaCore.uplugin`.)
2. **`Build.cs` in wrong directory** — confirmed.
   `Build/MelodiaTokenWallet.Build.cs` (also git-ignored, `.gitignore:8`),
   not the required `Source/MelodiaTokenWallet/MelodiaTokenWallet.Build.cs`
   (cf. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.Build.cs`).
3. **Header has `GENERATED_BODY()` but no `UCLASS()`** — confirmed.
   `UMelodiaTokenWalletSubsystem.h` declares
   `class MELODIATOKENWALLET_API UMelodiaTokenWalletSubsystem : public USubsystem`
   with `GENERATED_BODY()` and no `UCLASS()`. It also references
   `FMelodiaWalletSnapshot`, which is defined nowhere → would not compile.
4. **Absent from `.uproject`** — confirmed. Not in the `Plugins` array, unlike
   MelodiaCore / MelodiaWardrobe / MelodiaNPR.

## Tooling: `Tools/bp_live_path.py`

Step-0 role: pre-authoring reachability gate. Where `graph_reachability.py`
checks whether nodes inside a graph are wired, `bp_live_path.py` checks whether
the graph's **owner is instantiated by anything that actually runs** (walking
UP the reference graph toward configured anchors with soft+hard refs, max 8
hops, `World` counts as anchor-grade).

Unreachable-duplicate detection: `find_by_short_name()` lists every package
sharing an asset short name → multiple hits = AMBIGUOUS. For explicit
`/Game/...` paths it reports that copy's verdict and lists the others. Anchors
are read from disk (`Config/DefaultEngine.ini` → `GameMapsSettings`), so the
verdict stays honest if the editor session differs from config.

Exit codes:
- `0` LIVE — reaches a configured anchor.
- `1` ORPHAN — exists but no anchor route within 8 hops / nothing references
  it; or, for a native class, `UNKNOWN_NATIVE` (no `/Game` asset, no
  Blueprint subclass) also returns 1. ORPHAN ≠ "safe to delete" (blind to
  TSoftObjectPtrs, `.umap` actor refs, C++-by-name construction).
- `2` AMBIGUOUS — bare short name matched >1 copy.
- `3` tool/transport error — incl. missing anchors (fails closed).

## Key takeaways

- `Content/Content/Melodia/` and both `IMPERFECTER_*` trees are dead, untracked,
  unreferenced mirrors (with `RoomMods` and full plugin source as the only
  content of note).
- The canonical WBP_RhythmHUD lives at `/Game/Melodia/Blueprints/` but is
  git-ignored; the tracked duplicate at `/Game/Blueprints/` is the risk — an
  agent editing the tracked copy authors into a non-canonical island.
- `/_PROJECT` remains a live source of path ambiguity: docs and tooling still
  reference the legacy `/Game/_PROJECT` root while the canonical tree moved to
  `/Game/Melodia/_PROJECT`.
- All deletion decisions for `Content/` trees are Red (Ask First) per
  `CLAUDE.md` and require the owner.
