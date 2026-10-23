# Disk reclaim — G: audit — 2026-10-23

**Volume:** `G:` (Hatsune Miku Drive) — 931.5 GB total, **15.2 GB free (1.6%)**.
Measured with `[System.IO.DriveInfo]` (cross-checked against `df`; both agree — this
is not the stale-read trap).

**Method:** bounded native `os.scandir` walk per top-level entry (never unbounded
`du`, which times out on this volume). Script: `%LOCALAPPDATA%\hermes\cache\scratch\g_measure.py`.

## Measured content — every one of the 68 root entries

| Path | GB | Files | Note |
|---|---|---|---|
| `MelodiaMelusina` | 129.83 | 26,274 | game project |
| `_relocated` | 127.67 | 80,141 | relocation target (`.git_EnvironmentPortfolio_Archive_20260908`, `Backups`, `Imports`, `opencode-*`, `patches`) |
| `melodia_models` | 82.40 | 50 | **LLM caches, not models** — `gguf` + `hf-cache` + `ollama` |
| `ueprojects` | 52.03 | 40,522 | |
| `UE_DDC` | **38.40** | 194,147 | regenerable shader cache |
| `melodia_backup` | 27.74 | 18,853 | whole-repo backup |
| `film-304-toon-spine` | 18.82 | 23,552 | live film repo (7.5 GB of it is `.git`) |
| `BS_GodFile_Saved_Audit_20261009` | 17.63 | 20,212 | audit evidence |
| `_Transport_20260930_blend-rescue` | 16.29 | 12 | 8 × ~2.1 GB `.blend` rescues |
| `film-304-toon-spine.zip` | **15.59** | 1 | **verified-redundant snapshot** |
| `melodia_packages` | 8.39 | 330 | |
| `EnvironmentPortfolio` | 5.48+ | 227,360 | PARTIAL — mirror of the C: repo |
| `BlenderArchive` | 3.67 | 5,861 | |
| `Zundamons-kItchen-V2` | 2.65 | 20,318 | |
| `Downloads` | 2.21 | 2,321 | |
| `MelusinaStage_20261009` | 2.05 | 1 | |
| `HUMBER_ANMN301_Shorewake_2026-10-09` | 1.95 | 69 | school copy |
| `BS_GodFile_Snapshot_20260918` | 1.66 | 781 | stale snapshot |
| `_cache_relocated` | 1.35 | 22,423 | |
| `ZUNDYMONSKITCHEN` | 1.29 | 147 | |
| `stylizedcrossprop` | 1.25 | 32 | |
| `ZenTest` | 1.12 | 79 | |
| `Stylized Enchanted Forest Asset Pack` | 0.96 | 41 | |
| `perforce_backup` | 0.91 | 21 | |
| `portfoliowebsite` | 0.69 | 307 | |
| `melusina_assignment1` | 0.59 | 120 | |
| `film-304-dist` | 0.58 | 2 | |
| remaining 38 entries | ~1.4 | — | each < 0.4 GB |
| **Total measured** | **~565** | | |

## The ~345 GB that is not visible

Measured content is ~565 GB but the volume reports **916 GB used**. The gap is
**not** a directory: all 68 root entries are enumerated, there are **no reparse
points** at the root, `$RECYCLE.BIN` is 2.8 MB and `Users`/`SteamLibrary` are
empty stubs.

**Leading hypothesis: VSS shadow storage.** `vssadmin list shadowstorage` requires
elevation and returned *"You don't have the correct permissions"*. One elevated run
would settle it — if shadow copies are large, that dwarfs every item below.

## Candidates, ranked by GB-for-risk

| # | Path | GB | Evidence | Status |
|---|---|---|---|---|
| 1 | `film-304-toon-spine.zip` | **15.59** | HEAD `a78a5c2` is an **ancestor** of live HEAD `a8663ed`; only **145 files / 0.18 GB** absent from the live repo, all regenerable (`Intermediate/CachedAssetRegistry/*.bin` 175.6 MB + `Saved/Logs/*-backup-*.log`). **99.6 % redundant.** | **DEFERRED — owner decision** |
| 2 | `UE_DDC` | **38.40** | 194k files, newest activity **Oct 9**. No project references it: the film repo has **no** DDC override, and the live editor is **BS_GodFile** (`C:\EnvironmentPortfolio\BS_GodFile`), which uses project-local DDC. Regenerable. | **DEFERRED — owner decision** |
| 3 | `_Transport_20260930_blend-rescue` | **16.29** | 8 × ~2.1 GB `.blend` rescues (Sep 29 → Oct 15), incl. `MELUSINABACKUPBECAUSEAIAGENTSARERETARDED.blend`. **Owner's named rescue backups — MOVE, never delete.** | **DEFERRED — owner decision** |
| 4 | `melodia_backup` | 27.74 | whole-repo backup | deferred |
| 5 | `BS_GodFile_Saved_Audit_20261009` | 17.63 | audit evidence — `Saved/` is off-limits by standing rule | deferred |
| 6 | `melodia_models` | 82.40 | LLM caches; standing rule keeps `.ollama` | deferred |
| 7 | stale snapshots (`BS_GodFile_Snapshot_20260918`, `EnvironmentPortfolio_Snapshot_20260918`, `film304-sync-backup-20261003`, `film-304-dist`) | ~2.3 | old copies | deferred |

**Taking #1–#3 frees ~70 GB → G: free would go 15 → ~85 GB.**

## Film repo state (for the next session)

- `film-304-toon-spine` = 18.82 GB, of which **7.5 GB is `.git`**.
- **`git lfs prune` is a no-op here**: dry-run reports *"95 files would be pruned
  (4.4 MB)"*. `.git/lfs` is 3.2 GB but nearly all of it is retained by live refs.
  Do not expect a win from LFS on this repo.
- **G: is the film repo's only copy.** `P:` (the `laptop` remote) is not mounted and
  `origin` is unpushed. The three commits landed 2026-10-23 (`ca7555a`, `c5c2e5b`,
  `a8663ed`) exist **only on G:**.
- ~1.8 GB of `Content/` remains uncommitted — mostly vendored third-party
  (`_ThirdParty`, `UltraDynamicSky`, `ParagonSparrow`).

## Taken without asking

**Nothing was deleted, moved or modified on G:.** This audit is read-only; every
item above is deferred pending owner decision.
