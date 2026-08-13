# Backup & GitHub-Sync Audit — 2026-08-12

**Question asked:** what is on the PC's backups that has never reached GitHub, and what is the
most recent true project state?

> **CORRECTED 2026-08-12 (later same day) — read this before the tables below.**
> Two claims in the first version of this report were wrong, and the corrections shrank the
> problem from ~10,250 files to 214:
>
> 1. **`BP_BattleController` and `BP_BattleUI` were already tracked.** `.gitignore:128-134`
>    handles them correctly. The "untracked" reading came from a `git check-ignore` run against
>    `Blueprints/BP_BattleController.uasset` — a path missing the `/Battle/` segment. Git answered
>    about that nonexistent path and the answer was reported as fact.
> 2. **`SK_Melusina` needed nothing.** Per the owner there is one live mesh, and it is the copy at
>    `Content/Characters/Melusina/` — **already tracked**. The `Content/Art/` and
>    `Content/Melodia/Characters/` copies are stale leftovers.
>
> **The genuine gap was the two route levels**, now fixed in `43d0a9ae` (§7).
> The §1 table below is still accurate as a raw tracking-coverage count, but read it as
> "how much bulk art is deliberately untracked", not "how much is at risk".

**Method:** full file-level diff of `Content/` between `C:\EnvironmentPortfolio\BS_GodFile` (the
working project) and `G:\EnvironmentPortfolio\BS_GodFile` (the legacy mirror), cross-referenced
against `git ls-files` and `git check-ignore`. Counts are `.uasset` + `.umap` only.

---

## 1. The headline: the gap is not the backups, it is `.gitignore`

`BS_GodFile/.gitignore:96` is a blanket `Content/*` with a small allowlist under it. The result:

| Tree | On disk (C:) | Tracked by git | Untracked |
|---|---:|---:|---:|
| `Content/EnvSandbox` | 2,588 | **0** | **2,588** |
| `Content/Melodia` | 2,302 | 820 | **1,482** |
| `Content/TurnBasedJRPGTemplate` | 413 | **2** | **411** |
| `Content/Art` | 23 | **0** | **23** |
| `Content/MelodiaIntegration` | 45 | 45 | 0 |
| `Content/Characters` | 71 | 71 | 0 |
| `Content/Experiments` | 6 | 6 | 0 |
| **Project total** | **12,643** | **2,390** | **~10,250** |

**Roughly 81% of the Unreal content on disk has never been pushed to any remote.** Not because a
backup was missed — because it was never eligible to be committed.

### Specifically at risk (verified with `git check-ignore`)

| Asset | Status | Why it matters |
|---|---|---|
| `Content/EnvSandbox/Environments/L_KaleidoNave.umap` | was ignored → **FIXED, tracked in `43d0a9ae`** | Half the playable route, and the only level where a battle has ever started |
| `Content/Melodia/Levels/Opening/L_MelusinaMorning.umap` | was ignored → **FIXED, tracked in `43d0a9ae`** | The other half of the route |
| `Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.uasset` | **already tracked** — no action needed | Earlier "ignored" reading was a bad path check; see the correction banner |
| `Content/Art/Meshes/Skeletal/SK_Melusina.uasset` | ignored, **and that is fine** | Stale copy. Live mesh is tracked at `Content/Characters/Melusina/` |
| Bulk `EnvSandbox` art (meshes, textures, Megascans, ~4.6 GB) | **ignored on purpose** | Re-downloadable. Authored levels + PCG graphs within EnvSandbox are now tracked |

The 2026-08-08 `.gitignore` comment block already caught this class of problem once — it notes that
`Content/Characters/` (the protagonist) was silently untracked until that date and adds an
un-ignore. **The same hole was open for the route levels, and is now closed by `43d0a9ae`.**
`TurnBasedJRPGTemplate/` was never a hole (its two authored Blueprints are tracked); `Art/` is
stale bytes; the rest of `EnvSandbox/` is deliberately-ignored bulk art.

---

## 2. G: mirror diff — what only exists on the backup drive

`G:` holds 27,192 content assets vs C:'s 12,643. **14,563 are G-only** — but almost all of it is
marketplace bulk (Megascans, Asmbly, MagicianLabatory, audio soundscape libraries), not authored
work.

Filtering to project-authored paths leaves **43 files**, and 33 of those are the
`Content_MelodiaIntegration` duplicate mirror that was **deliberately quarantined** on 08-11
(`eb6ff433`, owner-approved). That is expected absence, not loss.

**The genuine G-only remainder is 10 files:**

```
Content/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto.umap
Content/EnvSandbox/Environments/WP/L_WP_CosmicOrrery.umap
Content/EnvSandbox/Environments/WP/L_WP_SakuraDream.umap
Content/EnvSandbox/Environments/WP/L_WP_SpaceCathedral.umap
Content/EnvSandbox/Textures/VFX/T_Spark_Sparkle4.uasset
Content/EnvSandbox/Textures/VFX/T_Spark_Twinkle8.uasset
Content/EnvSandbox/Textures_Shared/.../Radial_8_-_512x512.uasset
Content/Melodia/Characters/Melusina/BP_Melusina.uasset      <- path move, live copy is Content/Characters/Melusina/
Content/Melodia/Levels/Opening/L_Melodia_Dreamstate.umap    <- deliberately merged out, preserved in Saved/Recovery/
Content/Melodia/_PROJECT/MelusinasHouse/SM_wallhi.uasset
```

**Owner decision needed on the four `WP/` World-Partition portfolio levels** — Baroque Grotto,
Cosmic Orrery, Sakura Dream, Space Cathedral. They exist **only on G:**, they are portfolio track
deliverables, and they are in an ignored path so they were never candidates for a push. Everything
else on this list is explained.

**C-only (14 files)** is small and all accounted for: the recovered foliage MIs, the MeshBlend
activator functions, the three `SK_Melusina` skeletal assets, the water-gameplay proof level, and
the `ZenForestTest_PreRestore` safety copy.

---

## 3. Duplicate-authority hazards found while diffing

**`SK_Melusina.uasset` exists at three paths on disk. Per the owner, only ONE is live** — the other
two are stale copies left by earlier path moves, not competing authorities:

| Path | Size | Modified | Tracked |
|---|---:|---|---|
| `Content/Art/Meshes/Skeletal/` | 41.0 MB | 08-11 14:55 | **no** |
| `Content/Characters/Melusina/` | 38.1 MB | 08-11 14:05 | yes |
| `Content/Melodia/Characters/Melusina/` | 39.6 MB | 08-09 17:44 | yes |

**RESOLVED — no action needed.** The live mesh is `Content/Characters/Melusina/`, and it is already
tracked. Coverage is correct. The `Content/Art/` and `Content/Melodia/Characters/` copies are stale
leftovers from earlier path moves and are cleanup candidates whenever the owner feels like it.

Agents must not delete either path. Cleanup is an owner action.

**`BP_BattleController` was quarantined at 01:25 today** into
`_Quarantine_ThirdPartyFix_20260812/` (2,046,647 bytes, plus a `.bak_fix`), while the live copy in
`Content/TurnBasedJRPGTemplate/Blueprints/Battle/` is 2,147,871 bytes from 08-11 01:54. Different
sizes — these are **not** the same asset. Given this Blueprint is the single reason battles now
start at all, confirm which one the editor is loading before the afternoon's runtime work.

---

## 4. Backup inventory (what exists, and what it is worth)

| Location | Size | Verdict |
|---|---:|---|
| `G:\MelodiaMelusina` | **130 GB** | The real art archive — production/prototype trees, MelusinaFinalRig, bedroom, foliage, tileable textures, `.spp` Substance files. Nothing here is in git. |
| `_MELUSINA_SAFETY_2026-08-08/` | 186 MB | Five dated `SK_Melusina` generations (A_current 08-03 … E_OLD 07-20). Good safety net; keep. |
| `G:\MelusinaRigFinalSeparate` | 56 MB | Separated FBX exports (ARP rig, base, hair, boots, shirt, accessories). |
| `.git.backup.mirror/` (root) | — | Mirror of the pre-rebuild history, incl. `fast_import_crash_19932`. Keep until V2 is proven. |
| `Saved/Recovery/` | — | `DreamstateRemoval_2026-08-10`, `GameplayCoreBeatMap_2026-08-10`. Both deliberate. |
| `_QuarantineAssets_20260730/31/0809`, `_QuarantineSource_*`, `_Quarantine_ThirdPartyFix_20260812` | ~4 MB each | Intentional. Do not delete; do not restore without a reason. |
| `BS_GodFile/BackupBeforeRebuild/` | **0 bytes** | **Empty.** The name promises a pre-rebuild backup and it holds nothing. Do not rely on it. |
| Root `.clean_repo`, `.temp_repo`, `.repo_recovery_20260727` | — | Bare `.git` dirs from the recovery work. Stale. |

**G: has 2.1 GB free of 1 TB.** The backup drive is effectively full — any new mirror pass will
fail partway. That is the most urgent operational fact in this report.

---

## 5. Most recent project state

- **Repo:** `main` @ `62c7920d`, **in sync with `v2/main`** (0 ahead, 0 behind). The 4-commit lead
  and the 3 pending nebula LFS blobs reported on 08-11 evening have since been pushed.
- **Working tree, uncommitted:** 13 new + 3 modified `deploy/surreal_arch/melodia_gn/` Python
  modules (assigned to Muse, task M5), `Docs/Reports/WORKDAY_REVIEW_2026-08-12.md`, the new
  quarantine dir, and ~15 root scratch scripts (`check_bp*.py`, `fix_rhythm*.py`, `pie_*.py`).
- **ZenForest map repaired:** C: copy was a stale 4,207,052-byte version corrupted by a save made
  while the working directory was the V2 checkout but the open editor was the C: project. Restored
  from G: and **verified by SHA-256** — `073C9A1B8B92A5AD955411C17154B73FF6F138770C32C3B5BD9487072A84A22D`,
  41,126,742 bytes. Pre-repair copy preserved as `ZenForestTest_PreRestore_20260811_204055.umap`.
- **The local V2 checkout was deleted** at the owner's direction; the remote V2 branch was not.
  `C:\EnvironmentPortfolio\BS_GodFile` is the one working project.
- **Gates:** `runtime` **fail** (honest), `static_gates` **fail**, `save_load` / `repeat_consume` /
  `package_launch` **open**. 13 earlier gates pass. `release_tag.yml` is correctly blocked from
  cutting a release until the four completion gates have rows.
- **Known unresolved:** two exact Quaternius animation dependencies are absent from every C: and G:
  copy searched *and* from the tracked tree — these appear to be genuinely lost, not misfiled.
  Several malformed/empty assets remain (`Content/BigBush*`, `GenericFlower1.uasset` —
  "Invalid value for PACKAGE_FILE_TAG", pre-existing, quarantine rather than delete).

---

## 6. Recommended owner decisions (not taken by this audit)

1. **Rotate the Figma API key.** It was public on v2; the doc was redacted in `87b2938d` but the
   live key is still valid. Carried over from 08-11 and still open.
2. **Un-ignore the route levels and `BP_BattleController`** — or accept explicitly that the
   playable route is not recoverable from GitHub. Right now it is not.
3. ~~Confirm which `SK_Melusina` path is the live one~~ — **RESOLVED.** Owner confirms one live
   mesh; it is `Content/Characters/Melusina/`, already tracked. The other two paths are stale.
4. **Free space on G:** — 2.1 GB left of 1 TB.
5. **Decide on the four `WP/` portfolio levels** (§2) — G:-only, and in an ignored path.

---

## 7. Resolution — what was actually done (2026-08-12)

**Commit `43d0a9ae` — "content: track the playable route levels + authored PCG graphs"**

214 files, ~48 MB, all real LFS pointers. The `.gitignore` gained a documented block explaining
both what was added and what was deliberately left out, so the next cleanup pass does not undo it.

| Now tracked | Contents |
|---|---|
| `Content/Melodia/Levels/**` | `L_MelusinaMorning`, `L_MelodiaMainMenu`, DistanceFieldBlendLab |
| `Content/Melodia/PCG/**` | authored PCG graphs |
| `Content/EnvSandbox/Environments/**` | `L_KaleidoNave`, `L_SakuraPath`, CelestialPond, EscherAscent, FallenMoon, InfiniteScore, VinylGalaxy |
| `Content/EnvSandbox/PCG/**` | 7 musical hero levels incl. `L_PCG_Hero_WaterGameplayProof`, + graphs |

**Still ignored on purpose:** ~4.6 GB of bulk EnvSandbox art. Re-downloadable, no protective
value. The LFS budget is now funded (~$10 ≈ 50 GB as of 2026-08-12), so this is a signal-to-noise
decision rather than a cost one — but the reasoning stands: history is for authored work.

**Not done, still open:** the four `WP/` World-Partition portfolio levels remain **G:-only**
(§2). They are portfolio-track deliverables with no version history and no C: copy. Now that the
budget is funded, promoting them is cheap — it needs an owner call on whether they are current or
superseded.

## 8. Concurrent-writer notice

During this audit, commit `0e34eaed` ("gates: accept 12 material drifts + scope
graph_reachability/bp_sweep to shipped defects — static chain ALL OK") landed from the **Muse
lane** mid-operation, causing a `cannot lock ref 'HEAD'` failure on the first commit attempt.

Two consequences worth carrying forward:

1. **`static_gates` has moved from `fail` to passing.** Any doc written earlier on 2026-08-12
   that calls the static chain failing is already stale — including the first version of the
   Muse and DeepSeek handoffs.
2. **This repo has more than one active writer.** Agents must re-check `git log -1` before
   committing and expect to re-stage. Do not `git reset` to recover from a lock failure; re-add
   and commit on top.
