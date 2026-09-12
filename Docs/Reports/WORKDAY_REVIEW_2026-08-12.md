# Workday Review — Project State, Pipelines, and Recovery Friction

**Period:** 2026-08-11 through 2026-08-12  
**Purpose:** Historical review of the day’s repository, environment, map,
runtime, LFS, and synchronization work. This is a postmortem, not a new
source-of-truth layer.

## Executive status

The existing C: Unreal project remains the working project:

```text
C:\EnvironmentPortfolio\BS_GodFile
```

Its `main` branch and the `v2/main` remote-tracking ref advanced through the
day to `62c7920d` after several independently-created commits were pushed. The
current C/G ZenForest map is synchronized by hash:

```text
073C9A1B8B92A5AD955411C17154B73FF6F138770C32C3B5BD9487072A84A22D
```

The project is not fully clean or fully reproducible yet. The remaining
problems are identifiable:

- four foliage material instances were recovered from the G: recovery tree;
- tracked MeshBlend LFS pointer files were hydrated locally;
- two exact Quaternius animation dependencies are absent from all searched C:/G:
  copies and the tracked tree;
- several pre-existing malformed/empty assets remain;
- LFS history contains noncanonical/raw blobs that need separate hygiene work;
- the live editor has historically reported stale load errors until restart and
  asset rescan.

No full rebuild or gameplay gate pass was made as part of this review.

## Timeline

### Repository and study activity

The day began with an exhaustive workspace intake. The workspace contained
separate C:, G:, V2, compatibility, website, and worktree surfaces. The main
failure mode was treating those surfaces as one synchronized project when Git
only tracked a narrow subset of the Unreal content.

The environment/ECHO work added portable setup, path resolution, ledger and
validation improvements, website validation fixes, and historical reports. The
main relevant commits include:

- `c6d932f1` — environment/ECHO/source-map documentation and tooling
- `c868ece6` — corrected MCP-count handoff
- `17ac26ca` — moved portfolio stage blends
- `c0454177` — corrected collaboration kit size
- `533352d8` — resolved the `curentMP` source verdict
- `fb3b8297` — mobile renderer, nebula, and cathedral handoff
- `eb6ff433` — quarantined the duplicate 33-asset integration mirror
- `f1948852` — MUSE lane completion and pointer normalization
- `69f76813` — input-node/live-path/reachability tooling
- `f77421c4` — folded cloud/Linux research and Git reconciliation
- `62c7920d` — Kiro locomotion loose-end resolution

Some commits were created by other concurrent agents/processes while the
workspace was being audited. They must be treated as existing history, not
as one atomic change authored by this session.

### V2 detour and correction

An attempted RT-001 operation used the separate `MelodiaMelusinaV2` checkout
after its requested branch was temporarily unavailable. That was the wrong
fallback. The open editor was actually the C: `BS_GodFile` project, while the
working directory was V2. The operation loaded `/Game/ZenForestTest` through
the editor and saved a one-off NPC binding in the wrong context.

The V2 local checkout was subsequently removed at the user’s direction. The
remote V2 branch was not deleted. The existing C: project remained the recovery
target.

### Map provenance and repair

The map discrepancy was not a changed `EditorStartupMap`. Configuration still
selects `L_MelodiaMainMenu`. The actual issue was two ignored local map copies:

| Copy | Size | Hash | Meaning |
|---|---:|---|---|
| `C:\EnvironmentPortfolio\BS_GodFile\Content\ZenForestTest.umap` before repair | 4,207,052 | `73B9E268...` | stale local copy, modified by the mistaken save |
| `G:\EnvironmentPortfolio\BS_GodFile\Content\ZenForestTest.umap` | 41,126,742 | `073C9A1B...` | current August map |
| `C:\EnvironmentPortfolio\BS_GodFile\Content\ZenForestTest.umap` after repair | 41,126,742 | `073C9A1B...` | matches G: |
| `C:\EnvironmentPortfolio\BS_GodFile\Content\ZenForestTest_PreRestore_20260811_204055.umap` | 4,207,052 | `73B9E268...` | preserved pre-repair copy |

`BS_GodFile/.gitignore` contains `Content/*`, so these maps were never
reliably synchronized by Git. The current map was copied from G: to C: and
verified by SHA-256. No project defaults or gameplay source were changed.

## Workflows and pipelines added or exercised

### ECHO evidence pipeline

The active pipeline was formalized as:

```text
author
  -> spec_validate
  -> inject
  -> compile
  -> static_gates
  -> runtime_gates
  -> record
  -> promote
```

Changes included:

- strict JSON/QSC/T3D verb and arity validation;
- live `DA_MelodiaIntegrationConfig` allowlist inspection;
- duplicate consume-once detection;
- explicit editor HOLD behavior;
- live-path, graph, sweep, UI, and baseline gate orchestration;
- atomic ledger writes;
- shared playtest-to-ledger recording;
- ECHO contract tests.

The runtime gate remains unproven. No `runtime`, `save_load`,
`repeat_consume`, or `package_launch` pass was claimed.

### Environment/bootstrap workflow

Added or aligned:

- `Config/paths.json` portable environment contract;
- `deploy/validate_setup.ps1`;
- `deploy/bootstrap_environment.ps1`;
- corrected collaborator onboarding and validation;
- environment and ECHO runbooks;
- path resolution through environment variables rather than fixed G: paths.

The setup contract detects Unreal 5.8, Blender, Python, Node, Git LFS,
plugins, website lockfiles, and optional service ports.

### Portfolio and website workflow

The portfolio launcher now fails when pipeline steps fail even if an old
package exists. Website tooling now:

- resolves the selected website root instead of a fixed G: path;
- recognizes the canonical underscore deployment manifest;
- uses explicit local ESLint plugin resolution;
- fixes broken deprecated-page links;
- validates assets, facts, JSON, and local links.

The website JavaScript, assets, facts, and link checks passed. Existing CSS
duplicate-selector debt and raw-token debt remain.

### Map and asset synchronization workflow

The safe selective-sync pattern is now established:

1. Compare C:/G:/revert/worktree files by hash and timestamp.
2. Keep C: project descriptors, configuration, source, and plugin authority.
3. Promote only a verified newer map or asset.
4. Preserve the previous C: file under a recovery name.
5. Hydrate tracked LFS pointers locally.
6. Do not bulk-copy a dirty G: tree.
7. Do not use `git clean -fdx` or broad reset operations.

## Current missing/invalid asset inventory

### Recovered locally

- `MI_ToonBush`
- `MI_Toon_GenericFlower1`
- `MI_Toon_GenericFlowerTall`
- `MI_Toon_GrassSimple`
- 31 MeshBlend LFS assets were materialized with `git lfs checkout`.

### Still absent or unresolved

- `CAS_Q_Armature_Spell_Simple_Shoot.uasset`
- `CAS_Q_Armature_Sword_Attack.uasset`

These exact animation assets were not found on C:, G:, the recovery tree, the
Sakura worktree, or the tracked current tree. Available `ZUN_CAS_Q_*` assets
are not equivalent substitutes and were not silently wired in.

### Pre-existing malformed assets

- `Content/CustomAudio/SubFolder/C_Test_Target_2.uasset` is identically
  malformed on C: and G:.
- Several Marble texture files are malformed in the ignored local content.
- LFS audit reports raw PSD blobs where pointer files are expected.
- Three stage blend pointers are noncanonical.
- Four LFS objects remain quarantined under `.git/lfs/bad`.

The current editor’s 22-error report included stale MeshBlend pointer failures
from before hydration. A closed-editor restart/rescan is required to determine
which of those messages remain current.

## Git/LFS and remote state

- C: `main` is ahead of cached `v2/main` by three commits at the time of this
  review; several of those commits were pushed by concurrent processes during
  the day.
- Five gate-tool files were observed as unstaged during the audit; they were
  not included in synchronization actions.
- Current-head Git object integrity passed earlier; dangling commits were
  preserved and not pruned.
- LFS is not fully hygienic: current objects exist, but pointer canonicality
  and raw-blob issues remain.
- Remote pushes were intermittently blocked by GitHub edge selection and were
  only possible with command-local DNS pinning; no Git configuration was
  changed.

## Friction and failure modes

1. Multiple complete-looking workspaces made project identity ambiguous.
2. The open editor and shell working directory pointed at different projects.
3. `Content/*` ignored the most important map and environment binaries.
4. Git LFS pointer files were mistaken for real assets until the editor loaded
   them and reported invalid package tags.
5. A failed LFS checkout exhausted C: space and left a partial working tree
   during recovery.
6. GitHub DNS returned a reachable browser edge and an unreachable Git edge.
7. MCP schemas did not match runtime bridge parameter names.
8. Screenshot/log tools were partially unavailable or returned stale session
   data.
9. Concurrent agent commits changed C: history during the audit, preventing
   one atomic “today” snapshot.
10. Old recovery/worktree maps were easy to confuse with the current August
    map without hashing them.

## Final recommendations

- Keep `C:\EnvironmentPortfolio\BS_GodFile` as the working project.
- Treat the matching 41 MB C/G ZenForest map as the current map.
- Never bulk-merge G:, revert, or Sakura worktrees.
- Hydrate LFS pointers before diagnosing package corruption.
- Keep missing exact animations unresolved until their original source is found.
- Freeze concurrent writers before any future Git/LFS synchronization.
- Use a clean auxiliary worktree for remote pushes; do not push from a dirty
  editor checkout.
- Treat this file as a historical workday record, not a new authority document.
