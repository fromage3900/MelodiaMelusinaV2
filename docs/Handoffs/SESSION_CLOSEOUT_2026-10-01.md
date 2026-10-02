# Session Closeout — 2026-10-01 (git + Perforce sweep)

Final receipt for the version-control sweep. Every line below was read back from the
destination (git remote / p4 depot), not inferred from a submit or push result.

---

## Verified end state

### Git — `origin/main` @ `159f82eb5`

| Check | Result | How verified |
|---|---|---|
| `L_MelusinaMorning` external actors | **258 / 258** tracked | `git ls-tree -r origin/main -- <path> \| wc -l` |
| AscentCombatFramework **binary** on main | **0** (correct) | `git ls-tree -r origin/main \| grep -c '^Plugins/.../Content/'` |
| AscentCombatFramework **source** on main | 1,153 | same, `Source/` |
| `.p4ignore` on main | 1 | `git ls-tree` |
| Closure plan + capstone plan on main | 1 / 1 | `git ls-tree` |
| `docs/honcho-discord-sync` vs its remote | **in sync**, 0 unpushed | `git rev-parse` equality |
| Working tree | 294 untracked, 1 modified | `git status --porcelain` |

### Perforce — `//Melodia/main`, ticket valid

| Change | Contents | Depot verification |
|---|---|---|
| **271** | 16 `L_MelusinaMorning` external actors that had **no second copy** | `p4 files` answers all 16 at `#1 - add change 271`; `no such file` gone |
| **272** | AscentCombatFramework plugin, **2,712 files** | depot count 2711 + the spaced-name file = 2712; **0** `Binaries/`/`Intermediate/`/`.pdb`/`.dll` |
| **273** | 123 files that had no p4 copy — Sheep audio bank (73), Chladni textures, Kawaii VFX MIs, EdgeDesat post-process, `A_Cascadeur_..._Forge_InPlace`, Sea Above prototype actors | submitted; all 123 read back at `#1 - add change 273` |
| **275** | `Melusina.airi-card.zip` — last true single-copy file; the git pre-commit hook rejects zips, Perforce does not | submitted; resolves at `#1 - add change 275` |
| **276** | Melusina animation archive — 63 files, 13.9 MB: `LegacyRetargets_20261001` (Quaternius/FemaleBard/Mannequin/Source retargets), `Retarget/_Archive` (4 RTG assets), `MelusinaFinal` manifest | submitted; **63/63 on disk == 63/63 in depot, 0 missing** |

`default` holds 94 pre-existing files (Morning external actors from other lanes) — untouched.

### Full-repo single-copy sweep: **zero remaining**

A final pass walked every git-untracked path to concrete files (1,899 files / 221
directories), queried the depot per directory from **stdout only**, and diffed. Everything that
survived as "in neither system" was resolved:

- `Reference/` (247 files) — **false positive**; already in the depot since change 41 (2026-09-25).
  My parse broke on the space in `SC4 Ashlotte Maedel/... (1P Weapon)/...`.
- `.p4ignore`, both plans, this receipt — on git `main` via PRs #393 #394 #395.
- `temp_audit*.ps1` — my own scratch files from this session; deleted.
- 3 animation archive trees — submitted as change 276.
- `Plugins/.../Textures/*`, `Tools/BlenderAddons/tripo-3d-...zip` — already in the depot
  (changes 272 and 53; the zip carries a `binary+F` typemap, which is why `p4 add` refuses it).

### Disk

D: went from **94% / 113 GB free** to **47% / 1,002 GB free** after the owner's cleanup and
the change 272/273 archive. p4d healthy (P4D/NTX64/2026.1), ticket valid.

---

## PRs merged (4, all CI-green)

| PR | Payload |
|---|---|
| #391 | 59 unversioned Morning external actors + `MORNING_PCG_COVERAGE_AUDIT_2026-10-01.md` |
| #392 | `.hermes/plans/2026-10-01_git_p4_closure.md` — the ownership plan |
| #393 | `.p4ignore` restored and versioned + closure outcome recorded |
| #394 | Choral Sheep capstone presentation build plan |

---

## Findings, including corrections to my own earlier numbers

1. **The reported "PCG work lost" was never lost.** All 17 `Content/Melodia/PCG` files, all 11
   `Content/Melodia/WorldCompiler` files and all 206 `Content/Massive` files were present. What
   was real: the Morning OFPA mirror was only partly versioned, and because the `.umap` is 14 KB
   with no component data, a clean checkout silently dropped the PCG point-field components.
2. **Correction: I first reported 163 files "at risk."** That number came from `p4 files`
   **stderr**, which drops entries silently. Querying per-subtree showed the true figure was
   **123**; the other 40 were already in the depot since change 79.
3. **Correction: I described the plugin as 2,711 files when 2,712 are on disk.** The delta was
   `p4 files` word-splitting `ACF Discord Tutorial.txt` (space in the name). All 2,712 are in the
   depot.
4. **`.p4ignore` was missing from the repo root** while `P4IGNORE` pointed at that exact path —
   any `reconcile` would have swept `Binaries/`, `Intermediate/`, `Saved/`, `.git/`. Recovered
   from `4709e37f6`, verified p4 loads it, and committed it so the next machine inherits it.
5. **My own architecture error, caught by CI:** I committed 458 MB of plugin binary to a
   `docs/` branch (LFS cap 50 MB). Splitting it into nine sub-50 MB commits made every local
   push green and still failed CI, which measures the whole PR range. Bulk binary is Perforce's
   job; it now lives in change 272.
6. **Another lane's work was sitting unpushed** on the shared branch (`a5a9579af`, cascadeur
   import guards + the post-restart runtime verdict). Pushed and verified.

---

## New skills written

- **`melodia-binary-vcs-ownership`** — the git-vs-Perforce decision, the two-system presence
  test, OFPA partial-coverage audits, and the p4 traps above (stderr drops, `-c` on batch add,
  `#rev` stripping, spaced paths, non-UTF8 decode, missing `.p4ignore`).
- **`melodia-session-closeout`** — the closeout order: re-read reality, push shared-branch work,
  reconcile ownership, themed CI-green PRs, set-equality guards, verify in the destination,
  write the receipt, teach the lesson.

`melodia-git-commit-merge` was also patched with the branch-name LFS gate and the
neither-system-has-it check.

---

## Deliberately NOT done

- **No submit of CL 273.** Staged and asserted, awaiting owner approval.
- **166 → 94 files in `default`** and CLs 224/227/235/264/265/267: untouched, all still
  HOLD / REVIEW / SHELVE-ONLY.
- **No history rewrite, no force-push, no branch deletion, no `git clean`.** The 18 ACF-binary
  commits remain on `docs/honcho-discord-sync`, recoverable by SHA and never merged.
- **ACF source on main (1,153 files)** left in place — it landed via PR #387 before the LFS rule
  was known, and rewriting merged history is an owner decision.

---

## Open for the owner

**Nothing on disk is unversioned any more.** The remaining decisions are architectural, not
exposure:

1. **ACF source on main (1,153 files)** — landed via PR #387 before the LFS rule was known. The
   binary is in Perforce (change 272) and the source is in both systems. Keep the duplication, or
   move source wholesale to Perforce? Removing it from git now means a revert commit.
2. **`.p4ignore` is back in the working tree** (restored from `4709e37f6`) and versioned, so the
   next machine inherits it rather than discovering the gap.
3. **CLs 224 / 227 / 235 / 264 / 265 / 267 and the 94 files in `default`** are other lanes' work,
   all still HOLD / REVIEW / SHELVE-ONLY. Untouched by design.
4. **298 git-untracked paths remain** and are all now confirmed in Perforce — that is the
   intended steady state, not debt.
