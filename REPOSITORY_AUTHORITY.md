# Melodia Repository Authority Map

**Status:** CANONICAL — 2026-09-08  
**Purpose:** Prevent duplicate project authority across historical workspace repositories.

## Active repositories

| Domain | Canonical repository | Authority |
|---|---|---|
| Game / Unreal / runtime / capstone | `fromage3900/MelodiaMelusinaV2` | gameplay, assets, runtime contracts, semester/capstone truth |
| Portfolio website | `fromage3900/my-site` | public web presentation, Three.js/editorial site work |
| TouchDesigner / AE visual-performance lane | separate `MelodiaTouchDesigner` Git; canonical local checkout `C:/MelodiaTouchDesigner/td/grandmaster_melodia/` | TD networks, TDN/TOE, concert/live visuals, presentation passes |

## Deprecated repository

`fromage3900/EnvironmentPortfolio`

is a **historical umbrella/archive Git repository only**.

Important distinction: the local filesystem folder `C:/EnvironmentPortfolio/` remains a valid workspace container. The deprecated thing is the **root Git repository attached to that container**, not the folder itself.

`C:/EnvironmentPortfolio/BS_GodFile/` may continue to be the local checkout path for the canonical game repo, and sibling project folders may also live under `C:/EnvironmentPortfolio/`.

It is not:
- the game repo;
- the website repo;
- the active TouchDesigner repo;
- a current project root;
- a source of current Melodia status.

Do not implement new work there.

## Discovery rule

A local folder name does not define Git authority.

Paths such as:

```text
C:/EnvironmentPortfolio/BS_GodFile
C:/EnvironmentPortfolio/my-site-clean
C:/EnvironmentPortfolio/<other-project>
```

may be perfectly valid local checkout locations. A filesystem path does not determine Git authority.

What is deprecated is using the **root `C:/EnvironmentPortfolio/.git` / `fromage3900/EnvironmentPortfolio` repo** as Melodia authority.

Current repository identity is determined by:
1. the actual Git remote;
2. this authority map;
3. current front-door docs;
4. current source/evidence.

## Agent rule

Before cross-repo work:

1. identify the requested domain;
2. work in exactly one canonical repo;
3. read other repos only for contracts/reference;
4. never copy a whole project tree between repos;
5. migrate historical unique files deliberately, with provenance.

### Game → TD

The game repo publishes semantic/runtime truth.

TD consumes that truth for visual presentation.

TD does not become gameplay authority.

### Game → website

The site publishes curated downstream evidence/renders.

Website copy or browser prototypes do not become runtime authority.

## Archive migration rule

If useful content is found only in `EnvironmentPortfolio`:

- do not revive that repo;
- compare against the active destination;
- migrate only the unique file/idea;
- record provenance;
- leave the historical original in the archive.

## Current cleanup status

As of 2026-09-08:
- `EnvironmentPortfolio` root authority files have been replaced with deprecation notices;
- its legacy authority files were preserved under `Docs/Archive/`;
- the recent frozen TD snapshot is retained for uniqueness comparison;
- final GitHub rename/archive metadata is pending owner-side repository settings;
- the public `MelodiaTouchDesigner` remote is still to be recorded once exposed.

**One domain, one repo, one authority.**
