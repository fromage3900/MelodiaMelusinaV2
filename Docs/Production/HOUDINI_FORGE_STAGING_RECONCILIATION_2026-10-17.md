# Houdini Forge staging reconciliation — 2026-10-17

Status: **audit only; do not merge assets yet**.

Source: `feature/houdini-forge-staging`; target: `main` at `0c8c714e`.
Comparison: 45 ahead / 37 behind; 300 paths returned (GitHub comparison result may be capped).
Related merged work: PR #488 and earlier Houdini Forge integrations. Related open hybrid work: PR #494.

## Candidate-only assets requiring owner/editor validation

| Path | Main | Staging | Decision |
| --- | --- | --- | --- |
| `Content/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow.uasset` | Absent at path | LFS sha256 `f72fad5f3b0362b4008ef7551d6251872d543c5eef161d816506dd9e1f7fdb86`, 209201 bytes | Candidate: verify dependencies, world placement and ownership |
| `Content/EnvSandbox/Environments/WP/L_WP_CosmicOrrery.umap` | Absent at path | LFS sha256 `2624e00b5ba1857adaf7b2dc7012bfb8d6308494710d70d0fc3aed42554343ca`, 13449 bytes | Candidate: check newer Cosmic Orrery world and map references before moving |
| `Content/EnvSandbox/PCG/Styles/SeaAbove/OceanCathedral_20261014/PCG_SeaAbove_OceanCathedral.uasset` | LFS sha256 `4488ae4b512a0738c13a94fa1372ddaeaad714bc9f764c30da53f28140511a22`, 755071 bytes | LFS sha256 `62ad50b14331b7006b4f5e158e24792522dfe852bb8aa0b32ab92d8a2b8204c7`, 766218 bytes | **Hold:** conflicting binary versions, not safe to overwrite |

## Exclusions and release gates

- Do **not** merge `feature/houdini-forge-staging` wholesale or overwrite `CURRENT_STATE.md`, `AGENTS.md`, `CLAUDE.md` or skill guidance.
- Do not assume paths absent on main are functionally absent: check redirects, equivalent assets and merged PR #488 before extraction.
- Never transplant LFS pointer text alone and claim hydration. Verify `git lfs pull` and `.\\deploy\\validate_setup.ps1 -CheckLfsHydration` on the Windows workspace.
- For any selected asset: confirm dependency closure, reference paths, ownership and in-editor UE5.8 load/PIE; then stage in a separate **small asset-only PR** with Echo Static Gates.
- PR #494 is an active separate gameplay integration lane; preserve its hybrid canon and avoid importing staging docs.
- No binary files were copied in this audit. This document is a decision log, not proof that candidates are integration-ready.
