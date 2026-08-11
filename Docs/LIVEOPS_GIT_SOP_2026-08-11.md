# Live Ops Git SOP — MelodiaMelusinaV2
**Date:** 2026-08-11  
**Authority:** [`specs/echo_pipeline.json`](../specs/echo_pipeline.json) + [`Docs/GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md)  
**Lens:** Infinity Nikki–style live-ops (trunk sacred, lockable content, batched patches)

## Echo first (most recent pipeline)

Nothing gameplay-shaped is “done” without a ledger row. Manifest stages:

```text
author → spec_validate → inject → compile → static_gates → runtime_gates → record → promote
```

| Stage | Tooling | Live-ops / collab note |
|-------|---------|------------------------|
| author | specs / T3D / `.qsc` | Prefer **text** PRs under 50 MB slices |
| spec_validate | `echo_run.py validate-spec` | Allowlist + 7-verb contract |
| inject / compile | T3D + Monolith | Editor; one asset per txn |
| static_gates | live-path, reachability, sweep, baseline | HOLD if 9316 down — never fake pass |
| runtime_gates | PIE, campaigns 01–04 | Real input for `runtime`; probe ≠ play |
| record | `record_gate.py` / `echo_run.py record` | Only ledger rows certify gates |
| promote | commit + baselines | LFS budget gate runs here |

Completion gates (all OPEN until ledger says otherwise): `runtime`, `save_load`, `repeat_consume`, `package_launch`.

Repo hygiene (LFS audit, 50 MB share packs) is **promote-adjacent**. It does not replace Echo runtime evidence.

## Nikki rules → Melodia

| Nikki practice | Melodia rule |
|---|---|
| Trunk shippable | `main` = text + proven; binaries only intentional |
| Outfit drop = one patch | One LFS concern per commit |
| Asset locks | `git lfs lock` on `.uasset`/`.umap` (already `lockable`) |
| Parallel craft | Lane A editor ≠ Lane C cloud; CODEOWNERS paths |
| Metered content | 50 MB collab / 512 MB full push budgets |

## 50 MB version sharing

```bash
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git config core.hooksPath .githooks
bash deploy/collaborator_onboarding.sh docs50      # or slice50 / placement50
```

| Tier | Manifest | Intent |
|------|----------|--------|
| `docs50` | `specs/collab_slices/docs50.json` | Source/docs/Python review |
| `slice50` | `specs/collab_slices/slice50.json` | MelodiaIntegration BPs (~10 MB) |
| `placement50` | `specs/collab_slices/placement50.json` | Universal PCG + physics placement (EnvSandbox required on workstation) |
| `gameplay` | (inline) | ~2 GB Melodia+EnvSandbox+JRPG — **not** 50 MB |
| `full` | all LFS | Build/PIE/cook |

Measure: `python Tools/lfs_health_audit.py --manifest specs/collab_slices/slice50.json`  
Push budget: collab/cursor/docs → 50 MB; else 512 MB (`MELODIA_LFS_LIMIT_MB` overrides).

## Universal BP physics placement

Text builders live under `Content/Python/setup_*universal*.py`. Binary authority is EnvSandbox:

- `BP_MelodiaPCGControl`, `PCG_Melodia_Universal_Scatter`, `BP_InstanceOnSpline`
- `M_Master_Toon_Universal`
- Integration travel/physics: `BP_MelodiaTravelVolume`, exploration actors in C++

Use `placement50` on a machine that can `git lfs pull` EnvSandbox. Cloud checkouts may have **zero** EnvSandbox files — treat missing required paths as HOLD, not as “system absent from the project.”

Grok Universal research (2026-08-11, no branch): text builders under `Content/Python/setup_*universal*.py` are **not** binary proof; EnvSandbox PCG/Universal + `M_Master_Toon_Universal` must exist on disk after LFS pull. Digest: [`Reports/GROK_RESEARCH_FOLDIN_2026-08-11.md`](Reports/GROK_RESEARCH_FOLDIN_2026-08-11.md).

## Sculpt drops (parallel with play-proof)

While sculpting: export to `Imports/Sculpt/Inbox/`, run `python Tools/sculpt_intake_check.py`, then one UE import + one LFS commit.  
Full SOP: [`Docs/SCULPT_ASSET_INTAKE_2026-08-11.md`](SCULPT_ASSET_INTAKE_2026-08-11.md). Phone scan → ZBrush → Rokoko: [`Docs/MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`](MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md). Never FBX-import onto an existing `.uasset` path.

## Forbidden

`git clean -fd`, `git checkout -- .`, skill-Blueprint Python loads, probe-only `runtime` pass, mixing BP rewire + texture dumps in one push.

## Recommended GitHub branch protection (Settings — owner)

Document only; cloud agents cannot flip these:

1. Protect `main`: require PR, linear history (no direct pushes).
2. Require status checks when self-hosted runners are green: `Echo Static Gates` / `Unreal Build + Tests`.
3. Do not require admin bypass for LFS-heavy merges without a human looking at `git_safe_push` output.
4. Keep Releases on-demand via `Release Tag` workflow (ledger-gated).
