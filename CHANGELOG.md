# Changelog

All notable changes to **Melodia Melusina** (`BS_GodFile`).

Format follows [Keep a Changelog](https://keepachangelog.com/);
versioning follows [Semantic Versioning](https://semver.org/).

Source of truth: **git** for source/text and authored masters; **Perforce**
(`//Melodia/main`, client `Melodia_ws`) mirrors bulk engine/binaries.

## [Unreleased]

### Added

### Changed

### Fixed

## [0.3.0] - 2026-10-05

First governed-branch closeout since the 2026-09-24 git to Perforce cutover.
Branch `cleanup/scm-closeout-20261005`.

### Added
- Melusina runtime rig + retarget canon
  (`Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md`)
- Foot IK (`FAnimNode_FootPlacement`); retarget infra `IK_Shinbi` +
  `RTG_Shinbi_To_Melusina`
- Copernicus 2K tileable film-preset surfaces + ORM generator; wool variants generator
- Overworld HUD / Storybook (`WBP_Melodia_OverworldHUD`, `WBP_Melodia_CosmicOrrery`)
- Repo-staging-dir guard in `.gitignore` and `.p4ignore`
  (blocks a ~41k-file foreign staging directory from ever entering either VCS)

### Changed
- `M_Master_*` / `SDF/` material masters and material-instance updates
  (git-authoritative authored masters)
- `Config/DefaultEngine.ini` + `Config/DefaultGame.ini` current runtime config
  (protected paths; committed with `SKIP_PROTECTION=1` as a reviewed closeout)
- Locomotion graph repaired: enter locomotion above 3 cm/s, return to idle at or below 3 cm/s

### Fixed
- Idle arm-pose reference-pose interruption corrected to `15.774 | 28.561 | 28.615`
  (was `29.729 | 9.520 | 28.615`)

### Removed
- 110 archived `Saved/Audit/**` outputs pruned from tracking (recoverable from git history)

### Known issues
- Archer (RMB) path still defective at `34.789 | 9.520 | 28.615`; the six
  SparrowArchery clips remain frozen pending an owner decision

### Infrastructure
- Perforce: submitted change **282** (253 files: `L_MelusinaMorning` external
  actors + Content adds/edits + `DefaultGameplayTags.ini`); CL 281/265/264/267
  retained on hold, CL 235 remains shelved by policy

[Unreleased]: https://github.com/fromage3900/MelodiaMelusinaV2/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/fromage3900/MelodiaMelusinaV2/releases/tag/v0.3.0
