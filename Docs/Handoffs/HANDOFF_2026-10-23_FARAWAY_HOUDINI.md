# Handoff — Faraway Mother Houdini staging (2026-10-23) — FINAL

Written at the owner's explicit request (this overrides the "no handoff files" line in CLAUDE.md for this one file).
Status authority is still `CURRENT_STATE.md`; nothing here has been added to it. Governing plan: commit `90bfa88`.

## Where things are
- **C: repo, branch `lane-poitou-sanctuary-convergence`:** everything below, committed locally (not pushed). Pull with
  `git pull C:/EnvironmentPortfolio/BS_GodFile lane-poitou-sanctuary-convergence` (use a clean worktree: the old `G:` tree is on
  `wip/main-local-20261013` with ~1,460 uncommitted changes).
- **G: (unplugged before the final merge):** has only the early set — Heart Gate (earlier build, 1266/1170 pins), Silk Peak,
  their builders, the doc as of ~06:30, the earlier registry, the interim handoff, the 7 synced C++ files
  (`Source/BS_GodFile/MelodiaIntegration/`, backups in `_pre_sync_backup_20261023/`), and 2 Poitou docs. The five fan-out
  HDAs, the Frill Arch, the G1 proof and the review fixes are **not on G:** — they arrive with the git pull.
- **G: C++ was never compiled.** `G:` build failed with "Unable to build while Live Coding is active" (a C: editor process was
  running). Close editors, then `Build.bat BS_GodFileEditor Win64 Development -Project=...` (UHT already ran clean on G:).

## HDAs (all in `hda/` + `Content/HDA/`, builders in `Tools/Houdini/faraway/`)
| HDA | Repo gate | Notes |
|---|---|---|
| HeartGate | PASS (pins 1246/1156) | review pass skipped 2 cusps that pierced the heart frame; heart reads small; stretchers sparse |
| SilkPeak | PASS | **visible defects, not fixed:** pleat aliasing (phase = dot(p,dir(p)) multiplies frequency), near-vertical pleat walls, pinch point at world origin |
| FrillArch | PASS | scalloped flounces + brocade rosette; rosette faceted |
| LaceBridge | PASS | optional curve input |
| TerracedIsland | PASS | waterfall ribbons + emitter points + collision hull |
| MotherfoldBasin | PASS | shared-edge proof, shoreline + water outputs |
| ListeningOrchardTree | PASS | blossom cards + canopy proxy |
| SilkRibbon | **WARN / owed** | builder verify passes but gate restore-after-drive returns the guide curve (121 pts) not the ribbon; **not committed** |

## G1 stitched-tile proof (`Saved/Audit/faraway_g1/acceptance.json`) — overall **FAIL**
Border positions PASS (worst 0.0 m over 4 edges x 129 samples; global lattice exact). **Border normals FAIL** (limit 0.98, not tuned) —
traced to the Silk Peak pleat aliasing above, not the stitch. Visual review gate still pending. Next real step: fix the Silk Peak phase
construction (needs a globally continuous, unit-gradient phase), re-run `Tools/Houdini/faraway/g1_stitch_proof.py`.

## Houdini layout
Melodia Houdini Studio installed on the C: PC via `deploy/houdini/install_melodia_studio.ps1 -Verify` (24/24 headless; pointer
`Documents/houdini22.0/packages/melodia_studio_local.json`; undo with `-Remove`). GUI look is owner-unchecked. Repeat on the college PC.

## Rules and traps
- `Tools/*` is gitignored: builders were force-added. Houdini winding is clockwise-front: gate closed meshes by signed volume with `prim.normal()`.
- VEX: `PI` is reserved; array initialisers cannot call functions; Grid `orient=2` is the ZX plane; a VEX error leaves `geometry()` None silently.
- `hda/backup/*_bakN.hda` stubs appear on every rebuild and fail Gate 0: delete your own after building.
- Nothing is imported into UE; materials are existing MI paths only. Education licence output is non-commercial.
- College figures (128 GB RAM, extreme crowd sims, 4K Copernicus bakes) are owner-stated, unmeasured. G1 proof peaked at ~0.9 GB.
- Observed, not touched: repo gate `arpeggio_stair` FAIL, stale `hda/backup/*` stubs from other builders, an unrelated uncommitted
  `context: Object->Sop` change in `hda_registry.v1.json` (included in this commit because it shares the file).
