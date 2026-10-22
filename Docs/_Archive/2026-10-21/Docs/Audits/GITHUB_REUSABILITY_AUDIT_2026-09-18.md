# GitHub Reusability Audit — 2026-09-18

**Purpose.** A durable, re-runnable audit of what `fromage3900/MelodiaMelusinaV2` actually holds and
whether it can carry this project long-term. This is an audit snapshot, **not** a status document —
current status lives only in [`CURRENT_STATE.md`](../../../../../CURRENT_STATE.md).

**Method.** Read-only against the workstation checkout (`C:/EnvironmentPortfolio/BS_GodFile`, branch
`cleanup/pbr-twin-landing-2026-09-10`; working tree and index untouched) plus the GitHub API (`gh`)
and one throwaway depth-1 clone in `%LOCALAPPDATA%\Temp` (deleted afterwards). The only repository
write is this file, on its own `docs/` branch.

**Disclosed side effect.** Hydration tests pulled **~1.9 GiB of LFS objects** from GitHub. Against the
documented 10 GiB/month free bandwidth allowance, that is about 20% of one month.

---

## 1. GitHub surface (2026-09-18)

| Item | Value |
|---|---|
| Repo | `fromage3900/MelodiaMelusinaV2` — private, created 2026-08-11, 1 collaborator |
| Git store | 88,413 KB on GitHub; local pack 108.5 MiB + 3.2 MiB loose |
| Commits on `main` | 1,988; last push 2026-09-18 21:52 UTC |
| PRs | 159 merged · 40 closed · 1 open (#241, CLEAN, +135/−23, 3 files) |
| Issues | 13 open (221, 51, 42, 40, 39, 38, 36, 34, 33, 31, 30, 29, 27) |
| Branches / tags | 74 remote branches (incl. 8 `backup/*`); 30 tags (mostly `archive/*`); 0 releases; 0 milestones |
| CI | 8 workflows. `Echo Static Gates` runs on every PR and `main` push (green, ~35 s, `ubuntu-latest`); UE build / BuildGraph / publish are **manual** self-hosted jobs using `lfs: false` + targeted `git lfs pull` |
| `main` protection | required linear history; force-push and deletion blocked; required approvals = 0; **no required status checks** |
| Security surface | secret scanning **disabled**; Dependabot **disabled**; no root `LICENSE` |

Push-side policy is enforced locally by `.githooks/pre-push`: branch-name allowlist, direct `main`
pushes blocked, and an LFS budget gate (`Tools/git_safe_push.py`; 50 MB for `collab/|cursor/|docs/`,
otherwise 512 MB).

## 2. Clone-and-hydrate verification (the real reusability test)

Depth-1 clone of `main` into temp, then hydration from GitHub:

| Check | Result |
|---|---|
| Checkout | 285 MB, 15,427 files, 5,264 LFS pointers under `Content/` |
| Live LFS payload on `main` | 6,326 files / **13.05 GiB** |
| `Content/MelodiaIntegration/**` hydration | **109/109 objects** recovered as real bytes |
| Spot objects, mixed trees and sizes | DA_ResonantArc 2,917 B · MI_Landscape_LayerBlend 8,179 B · skirtpanel 24,411 B · RTG_UE4Mannequin 21,755 B · clean_temp16x16 730 B · DT_Burdens 2,198 B · PavingStones070 469,329 B · zun_battle_win_01.wav 170,028 B · T_DressShorewake 899,628 B — **all exact** |

**Verdict: a fresh clone of `main` reconstructs code + curated content, and remote LFS serves real
bytes today.**

*Instrument note.* Raw LFS batch-API probes (`POST /info/lfs/objects/batch`) answer
`404 Object does not exist on the server` for objects that real `git-lfs` clients fetch without
error (Xet-backed storage path). Do not judge remote presence with a raw batch-API probe; use
`git lfs fetch` / `git lfs pull`.

## 3. What the repository is, by design

`.gitignore:113` blankets `Content/*` and re-includes a hand-curated list (`Content/Python`,
`Melodia/{DataStuctures,Companions,Characters,Levels,PCG,UI/Quill}`, `MelodiaIntegration`,
`Melodia/VFX` (:444), reviewed `TurnBasedJRPGTemplate` exceptions,
`__ExternalActors__/EnvSandbox/Monoliths`, protected material masters, …).

- `Content/` measured: **35,210 files on disk → 16,710 in the index → 6,654 in `HEAD`** (working branch).
- Untracked **and not ignored** under `Content/`: **0**. Nothing authored falls silently through `git status`.
- Ignored by policy: marketplace kits (Brushify, Greybox, UltraDynamicSky, Library, `_ThirdParty`),
  bulk `EnvSandbox` art, `Content/Audio` (630 files), `Content/RVTDecals`, `Content/GeneratedScenes`.
  The `.gitignore` comments describe this as "roughly 15 GB that would blow the LFS budget for no
  protective value".
- Authored environment art is delivered out of band: `Docs/Planning/COLLABORATOR_SETUP.md` documents
  the S3 artdrop (`s3://melodia-artdrop-…`, 6,720 objects / 3.06 GiB, read-only IAM user) and states
  plainly that `L_KaleidoNave` opens with missing references on a fresh clone. Documented behaviour,
  not an LFS fault.
- That same guide is numerically stale: it claims tracked `Content/` ≈ 2,700 files / 2.7 GB; measured
  today it is 6,326 LFS files / 13.05 GiB on `main`.

## 4. Findings (ranked)

### F1 — LFS is metered and already past the documented free allowance

Evidence: `main` **13.05 GiB** live; working index 17,697 files / **40.79 GiB**; staged-but-uncommitted
**11,476 files / 27.62 GiB**; local `.git/lfs` cache **54 GB**.
`Docs/GIT_BATCH_DISCIPLINE.md` states the allowance as 10 GiB storage + 10 GiB/month bandwidth, then
metered (≈ $0.07/GiB-month storage, ≈ $0.0875/GiB download).

Consequences:

1. The pending landing would take the live payload to ~41 GiB.
2. The repo's own pre-push gate (512 MB for `cleanup/*`) will refuse that as a single push — split by
   subsystem, or set `MELODIA_LFS_LIMIT_MB` deliberately for one reviewed push.
3. `lfs.allowincompletepush=true` is set locally. A quota-blocked upload can therefore land
   **pointer-only commits** — the same shape as the historical "LFS 404s on fetch" incident
   (`Docs/Production/GIT_STATE_2026-09-03.md`). Set it to `false`.

Mitigation already written but not yet run: `Docs/LFS_COLD_ARCHIVE.md` (archive superseded
`Exports/PortfolioStages` blends + the pre-integration backup = −3.65 GB).

### F2 — Ignore-shadow: authored artifacts that `git status` cannot show

1. **World Compiler UE artifacts.** `Content/Melodia/WorldCompiler/` has no un-ignore, so
   `DT_morning_rainbow_bloom_Points.uasset` (1.8 MB, saved 09-18 03:13),
   `PCG_WorldCompiler_PointField.uasset`, `S_WorldCompilerPoint.uasset`, `EUW_WorldCompiler.uasset`
   and `DA_MorningRainbowBloom.uasset` are ignored. The compiler's own contract
   (`Docs/WorldGen/WORLD_COMPILER_CONTRACT.md` §7) requires "Tracked — DataTable, template graph,
   band MIs, and the level's external actors are on `main`" as evidence-ladder rung 6. **Rung 6 is
   unmet today.**
2. **Compiler tooling.** `Tools/*` is blanket-ignored (`.gitignore:243`) with a per-file allowlist.
   `Tools/world_compiler.py` (44 KB), `Tools/test_world_compiler.py`, `Tools/world_compiler_ue_driver.py`
   and `Tools/triage_working_tree.py` are not on it. **353 `.py` files under `Tools/` are ignored**
   (808 of 3,350 tracked). The compiler CLI is its reusable core; it exists only on this workstation.
3. **`L_MelusinaMorning` OFPA actors.** 192 actor files on disk — 78 tracked, **114 ignored**
   (`.gitignore:224` un-ignores only `EnvSandbox/Monoliths`). **67 of the ignored files contain the
   string `WorldCompiler`** (the compiled field's placed actors) and the newest ignored writes carry
   today's 04:01 timestamp. The Monoliths exception exists precisely because "any actor placed in a
   Monoliths level silently never reaches git"; `L_MelusinaMorning` has the same hazard now.
4. **Evidence JSONs.** `Saved/Audit/world_compiler_*_proof_2026-09-18.json` and
   `…_islands_2026-09-17.json` are ignored under `Saved/` and must be force-added (the pre-commit hook
   explicitly allowlists `^Saved/Audit/.*\.(json|md)$`, so this is a one-line `git add -f`).

Mitigation: one reviewed commit adding `!Content/Melodia/WorldCompiler/`,
`!Content/__ExternalActors__/Melodia/Levels/**`, the four `Tools/*` entries, and the two proof JSONs
by force-add. None of this adds art payload (all small or already-live objects).

### F3 — Newest work is workstation-only

`cleanup/pbr-twin-landing-2026-09-10` is **117 commits ahead of `main`** and **22 behind** (the
landing is a merge, not a fast-forward), and **37 of its commits are not on its own remote**. On top
of that sit **11,757 staged files, uncommitted** (the PBR twin + materials landing).

Other branches with unpushed commits: `feature/eyewear-editorial-20260912` (4),
`codex/game-state-2026-09-04-checkpoint` (4), `collab/desktop/integrate-laptop-2026-09-06` (2),
`codex/snapshot-prep-20260914` (1). Two stashes are parked.

Caution: the staged batch includes `Config/DefaultEngine.ini`, which the pre-commit hook protects.
Commit with `SKIP_PROTECTION=1` inlined in the same command, or the commit is blocked and the index
stays dirty.

### F4 — Advisory-only merge gate, thin security surface

No required status checks and 0 required approvals: `main` is protected against force-push and
deletion and requires linear history, but a bad merge is stopped by discipline alone. Secret scanning
and Dependabot are off (Secret Protection is a paid private-repo feature; Dependabot is free to
enable). No root `LICENSE`.

### F5 — Environment pressure

`C:` free space measured at **6.8 GiB** (100% used) while `.git/lfs` alone is **54 GB**. Any full LFS
hydration (~13 GiB), worktree checkout (a worktree smudges LFS on checkout), or UE build will fail on
space — the failed worktree checkout during this audit died exactly that way.

## 5. Reusability verdict

Usable, and above average for a solo dev + agent workflow: real CI on PRs, policy hooks,
branch-name discipline, an LFS budget gate, workstation sync tooling, an out-of-band art transport,
and ~20 audit docs on `main`. A fresh clone of `main` hydrates and reconstructs the tracked subset.

What limits long-term reusability is not git mechanics but four things: **LFS economics (F1)**,
**authored artifacts in ignore shadows (F2)**, **workstation-only recency (F3)** and **disk (F5)**.
F2 is the quiet one — invisible in `git status`, identical to the failure class this repository
already documented for Monoliths, and it grows every time a session places actors or writes a tool.

## 6. Recommended actions (in order)

1. Before the next landing: `git config lfs.allowincompletepush false`; check
   Settings → Billing → LFS storage/bandwidth; run the `LFS_COLD_ARCHIVE` pass.
2. Land the staged mass in bounded commits by subsystem (materials / meshes+textures / docs), each
   under the 512 MB gate; `SKIP_PROTECTION=1` only for the reviewed `Config/DefaultEngine.ini` change.
3. Close the F2 shadows in one reviewed commit (negations above). That makes the World Compiler's
   evidence-ladder rung 6 true instead of nearly true.
4. Reclaim disk before any large checkout, hydration or build.

## 7. Not checked

Full 13 GiB hydration end-to-end; a UE build/launch from a fresh clone; each of the 74 branches;
history-wide secret scan; the S3 artdrop bucket; the GitHub billing page (requires `user` scope);
pre-Xet LFS behaviour.

## Appendix — re-run commands

```bash
gh repo view fromage3900/MelodiaMelusinaV2 --json name,visibility,diskUsage,pushedAt
gh pr list --state open --limit 20
git rev-list --left-right --count origin/main...HEAD
git lfs ls-files -l | wc -l                                    # LFS pointer files in the index
git ls-files --others --exclude-standard -- Content | wc -l    # must be 0
git check-ignore -v Content/Melodia/WorldCompiler/DT_morning_rainbow_bloom_Points.uasset
python Tools/test_world_compiler.py                            # rung 1 of the compiled-world ladder
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/fromage3900/MelodiaMelusinaV2.git <tmp>
```
