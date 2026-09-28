# Convergence + dual-drive sync receipt — 2026-09-28

Scope: post-"paradigm shift" convergence of the BS_GodFile repo and the usual G:/D: sync.
All statements below are measured on this machine, not assumed.

## 1. Paradigm-shift disposition (carry-over, unchanged)

The 09-27 "Souls-like/Rhythm-Action paradigm shift" remains **PROPOSED, not canonical**:

- `Docs/Production/MELUSINA_SOULS_ACTION_AGENT_LANES_2026-09-27.md` header was downgraded
  CANONICAL -> PROPOSED in the 09-27 cross-lane audit; no souls BPs/assets/code exist on disk.
- 09-28 ACFU review supersedes the earlier "zero assets" claim: ACFU 4.3.5 loads and
  `BP_MelusinaACFTrial` / `BP_ACFTrialEnemy` exist and compile. It does **not** upgrade the
  track: the enemy's `AutoPossessAI` / `AIControllerClass` edits did not persist, abilities
  are ungranted, and the playable-damage gate is still open.
- Jev-live longterm choice stands: `JRPG_SLICES_PLUS_SANDBOX` (0.98). No conversion without an
  owner pivot plus Issue #51.

## 2. Git convergence performed this pass

| Item | Before | After |
|---|---|---|
| `feature/spout-beauty-2026-09-26` | 4 commits ahead of its origin (tip `8be489cf0`) | pushed; local == `origin` == `979f00d7c` |
| local `main` (worktree `_worktrees/world-compiler-20260927`) | `a520ebbc9`, 2 behind `origin/main` | fast-forwarded to `bdb0acbf2` == `origin/main` |
| `fix/mcp-transport-repair-20260927` | pushed, suspect squash-merged as #362 | confirmed patch-equivalent -> prune candidate, NOT pruned yet |

- Push detail: 4 commits / 68 files / +1934 -330, of which 4 LFS objects
  (`M_Master_Impressionist_Toon`, `..._Toon_Landscape`, `M_Master_Nikki`,
  `MI_Niagara_Melodia_Static_StateB`) went with it.
- Prune evidence: `git cherry -v origin/main fix/mcp-transport-repair-20260927` prints
  `- b4bec4ddc` (minus = patch-equivalent to what #362 already landed). The 51-file
  three-dot diff is the branch's own contribution measured from its merge-base, i.e. main's
  work, not unique branch content. No gc run; SHA stays recoverable.
- Working tree deliberately left as-is: 69 modified / 473 untracked. Per the 09-21 rule the
  parked set (Frozen PPV, MPCs, `DefaultEngine.ini`, EnvSandbox texture dumps, Oceanology,
  Humber) is **not** dumped, and main moves by PR only.

## 3. Open item that must not be lost — `BP_Melusina.uasset`

Both the main checkout and `_worktrees/mcp-transport-repair` hold an **identical uncommitted
delta** to the LFS-tracked asset:

- on disk: 82,635 bytes, `sha256 d1a5102a3c4cff1496c481e3e34702731a12679d89e230e1493dc15444f5e5a2`
- committed pointer: `sha256 f5c16292920bcc2c6888052d2efe42d3f2be7f017330b2627044eb8b54ff3867` (same size)

Same bytes in both worktrees, so this is one real save, not two divergent edits. It is **not**
committed here: UnrealEditor PID 49724 is live and could rewrite the file mid-commit. Land it
as a single isolated art commit from one worktree only, after the editor is saved and closed.

## 4. Dual-drive sync — space verdict first

Runbook rule (from `G:\BS_GodFile_School_20260925\MIRROR_MANIFEST.md` step 1): a full mirror
needs tree + 20% headroom.

- measured tree: **248 G** (09-25 measurement, unchanged in kind; Content 69.6 G, Saved 61.4 G,
  .git 46.3 G, Intermediate 7.8 G)
- 248 x 1.2 = **297.6 G** required
- free now: **D: 177.5 G**, **G: 87.0 G**, C: 10.6 G

=> A **new** full mirror is **space-blocked on both drives**. No fresh date folder was created,
and nothing on G:/D: was deleted. Instead, per the 09-24 manifest's update procedure, the sync
is a **catch-up `/MIR` into the existing dated folders** (delta-only, always fits) plus the
**108 M G: school kit**.

- `Tools/mirror_sync_20260928.ps1` (new) drives `-Phase DryRun|Apply|Verify`:
  - G: school-kit pairs, `/E` scoped: `Tools/Houdini`, `Docs`, `Content/EnvSandbox/PCG`,
    `Source/MelodiaShader`, `Chapters`, `specs`, `Houdini`, `Saved/Daemon/proposals`
  - D: full-tree `/MIR` catch-up into `D:\BS_GodFile_Mirror\20260924`
  - `/XJ` mandatory (6 junctions, incl. `Exports/PortfolioStages` -> `D:/_relocated`)
  - `Apply`/`Verify` **refuse to run while UnrealEditor is up or :9316 is listening** —
    at dry-run time PID 49724 was up and 9316 was open, so only the read-only `/L` pass ran.
  - logs + `*-run.json` land in `%TEMP%\bsg-mirror-20260928\`

### Measured dry run (`-Phase DryRun`, read-only, 2026-09-28 03:20)

D: full-tree catch-up into `D:\BS_GodFile_Mirror\20260924`:

```
               Total    Copied   Skipped  Mismatch    FAILED    Extras
    Dirs :     58557     58206     57696         0         3        39
   Files :    148775      7627    141148         0         0      1582
   Bytes :  213.815 g   5.990 g  207.824 g         0         0  300.55 m
```

- **7,627 files / 5.990 GB** to copy, 207.8 GB already in sync, **0 failed files**.
- The 3 failed dirs are the documented `Saved/TmpTests/pytest_mesh_terrain{,_2,_final}/`
  process-held pytest scratch — the script now *tolerates* rc=11 only when failed files = 0
  and failed dirs <= 3, and warns instead of aborting.
- 5.99 GB fits D: free 177.5 GB with large headroom. A full fresh mirror still does not
  (248 G + 20% = 297.6 G needed), so the catch-up route stands.
- The 1,582 extras / 300.55 MB are the cache copies the 09-24 run made
  (Intermediate/DerivedDataCache/Binaries/`__pycache__`) which are now excluded. **`-Purge` is
  opt-in for exactly this reason** — a blind `/MIR` would delete them, and a `/L` pass cannot
  enumerate them, so the default Apply is copy-only `/E`.

G: school kit (`G:\BS_GodFile_School_20260925`): 4 of 8 pairs already current (rc=0 —
`Source/MelodiaShader`, `Chapters`, `Houdini`, `Saved/Daemon/proposals`); 4 have small deltas
(rc=1 — `Docs` incl. the new audits/handoffs, `Content/EnvSandbox/PCG` incl. 7 new PCG test
assets, `specs`, `Tools/Houdini`). Total remains ~108 MB, so it always fits G:.

### Running the Apply (blocked only on the editor)

UnrealEditor PID 49724 is up and :9316 is listening, and the script refuses `Apply`/`Verify`
in that state by design (the game DLL is locked and a half-written asset would be mirrored).
Once the editor is saved and closed:

```powershell
# copy-only catch-up (recommended; deletes nothing in either mirror)
powershell -NoProfile -ExecutionPolicy Bypass -File C:\EnvironmentPortfolio\BS_GodFile\Tools\mirror_sync_20260928.ps1 -Phase Apply

# confirmation pass afterwards
powershell -NoProfile -ExecutionPolicy Bypass -File C:\EnvironmentPortfolio\BS_GodFile\Tools\mirror_sync_20260928.ps1 -Phase Verify

# only after reviewing the extras: add -Purge to make the D: pass a true /MIR
```

`Tools/mirror_sync_20260928.ps1` is **gitignored by project policy** (`.gitignore:255
Tools/*`) and was deliberately not force-added; it reaches the mirrors through the D: catch-up
and G: school kit like every other untracked runner script.

## 5. Still blocked on the owner

- `p4 login` — Perforce session expired; `BP_SirPerch` and the Sir work sit in pending CLs.
  Nothing p4-side was submitted or reverted here.
- Editor close — required before the `Apply` phase.
- Free space — pruning C: worktrees or reclaiming `D:/perforce` after migration validation is
  the owner's call, never the agent's.
- `harp_bow_pipeline` is never robocopied, junctioned or overwritten; D: remains master there.
