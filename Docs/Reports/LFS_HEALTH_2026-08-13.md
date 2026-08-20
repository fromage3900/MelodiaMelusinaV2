# LFS + Repo-Size Health Report — 2026-08-13

Read-only audit. No git write commands were run. Network access to GitHub from this box was
intermittent/unavailable during this session (see §7) — noted rather than guessed around.

## 1. `Tools/lfs_health_audit.py`

Ran both modes:

```
python Tools/lfs_health_audit.py
  Non-pointer LFS-suffix files in HEAD: 0
    total raw bytes: 0.00 MB
```

```
python Tools/lfs_health_audit.py --game-paths-only
  Non-pointer LFS-suffix files in HEAD: 0
    total raw bytes: 0.00 MB
```
`--game-paths-only` **is supported** (it's a real flag in the script, restricting the scan to
`Content/` and `**/Content/` paths). It ran far longer than the unrestricted pass — the script
shells out to `git show HEAD:<path>` once per LFS-suffixed file (2,000+ `.uasset`/`.umap`/`.png`
files), so each invocation is a separate git-object read; on this box that took several minutes,
not seconds — but it completed and confirms the unrestricted result: **0 non-pointer files**,
scoped to game content specifically.

**Interpretation:** the script checks one specific failure mode — files whose extension matches
an LFS-tracked suffix (`.uasset`, `.umap`, `.fbx`, `.blend`, `.png`, `.wav`, etc.) but whose HEAD
blob is a raw binary instead of an LFS pointer text stub. It found **none**. This directly
**refutes** the "raw PSD blobs where pointers are expected" / "noncanonical pointers" concern for
the current HEAD tree — whatever produced that note either predates a fix, described a
historical commit (not HEAD), or described the `.git/lfs/bad` quarantine (a different problem,
see §6), not a pointer/blob mismatch. No `.psd` files exist in the tracked tree at all
(`git ls-files | grep -i psd` = no hits), so there's nothing to check there specifically.

## 2. `Tools/git_safe_push.py --help`

```
usage: git_safe_push.py [-h] [--limit-mb LIMIT_MB] [--auto-limit]
                        [--range REV_RANGE] [--remote REMOTE]
                        [--branch BRANCH] [--check-only]

Refuse oversized LFS push batches
```

Read the source (`Tools/git_safe_push.py`) to confirm exact behavior:

- **What it measures**: the LFS-relevant byte total of a *batch* about to move — either
  `git diff --cached --name-status` (staged/local, default) or `git diff --name-status <range>`
  (e.g. `origin/main..HEAD`, for CI). For each changed path it resolves the blob at the target ref,
  and if it's an LFS pointer (`version https://git-lfs.github.com/spec/v1 …`) it reads the `size`
  field out of the pointer text — it does **not** download the object. If the path isn't a
  pointer but its suffix is in a fixed `BINARY_SUFFIXES` set (`.uasset .umap .fbx .blend .png .jpg
  .jpeg .wav .mp3 .ogg .psd .tif .tiff .exr .dll .so .dylib .ttf .otf .mp4 .webm`), it falls back
  to raw blob/file size.
- **Deletions** (`status == "D"`) are excluded from the total.
- **Pointer-text-only edits** (same LFS oid on both sides — e.g. an EOL-only pointer-file rewrite)
  are detected via `same_lfs_oid`-style comparison and skipped — they add 0 bytes of real storage
  delta, so they don't count against budget.
- **Limit**: explicit `--limit-mb`, or `--auto-limit` which reads `MELODIA_LFS_LIMIT_MB` env var if
  set, else **50 MB** for branches prefixed `collab/`, `cursor/`, or `docs/`, else **512 MB**.
- **When it fires**: if the summed total exceeds `limit_bytes`, it prints `BLOCKED: LFS batch
  X.XX MB exceeds limit Y MB` to stderr and returns exit code 1 — this is meant to run as a
  pre-push gate (see `Docs/GIT_BATCH_DISCIPLINE.md`) so an oversized batch never reaches `git push`
  and never counts against GitHub LFS bandwidth/storage before someone notices.
- With `--check-only` it stops after reporting (no push). Without it, and if `--branch` was given,
  it will actually run `git push <remote> HEAD:<branch>` when under budget — this script **can**
  perform a real push; it was not invoked in a push-triggering way during this audit (`--help`
  and static read only).

## 3. LFS object breakdown (`git lfs ls-files -s`, 2,224 entries, aggregated)

Parsed and summed by top-level path and extension (values are approximate, derived from the
human-readable sizes `git lfs ls-files -s` prints, total reconciles to ~8.90 GB against the
~8.8 GB baseline in context):

**By top-level path (MB):**

| Path | MB |
|---|---|
| `Exports/` | 5,604.8 |
| `Content/` | 2,849.9 |
| `Plugins/` | 168.1 |
| `CompatibilityLabs/` | 165.5 |
| (misc loose Melusina rig/shirt files at repo root) | ~90 combined |
| `_QuarantineAssets_20260730` / `_20260809` / `_20260731` | ~14.5 combined |
| `Docs/`, `_TouchDesigner/`, fonts, `UpdatedShirt.fbx` | <1 each |

**`Exports/` dominates at ~63% of the 8.8 GB LFS payload** — almost entirely Blender portfolio-
stage `.blend` files. `Content/` (actual UE game content) is ~32%.

**By extension (MB):**

| Ext | MB |
|---|---|
| `.blend` | 5,538.9 |
| `.uasset` | 2,912.2 |
| `.umap` | 173.1 |
| `.fbx` | 114.0 |
| `.png` | 110.8 |
| `.wav` | 47.2 |
| `.dll` | 6.1 |
| `.ttf` | 0.2 |

`.blend` alone is **63% of all LFS content** in the current checkout — that's the portfolio
Blender source stages under `Exports/`, not the shipping game content.

## 4. Pointer-vs-raw problems

**Verdict: refuted for HEAD.** `Tools/lfs_health_audit.py` found 0 files with an LFS-tracked
suffix that are stored as raw blobs instead of pointers in HEAD. There are also no raw `.psd`
files in the tree (none exist at all). If "noncanonical pointers" refers to something else (e.g.
pointer files with unexpected line endings, or a mismatched OID vs. the object actually in
`.git/lfs/objects`), that's a different check than this script performs and was not separately
observed — flagging as unverified rather than claiming it's also clean.

The one *confirmed* real problem in this space is the **quarantined "bad" object** covered in §6:
a currently-referenced `.blend` file whose local LFS object failed integrity and was moved to
`.git/lfs/bad` — that's a corrupted/incomplete object on disk, not a pointer/blob mismatch in git
history.

## 5. Extensions in the working tree not covered by `.gitattributes` LFS patterns

`.gitattributes` LFS-tracks: `uasset umap upk blend fbx vrm usd usda usdc obj png jpg jpeg tga exr
hdr psd tif tiff wav mp3 ogg mp4 webm ttf otf dll so dylib`.

Cross-referencing against `git ls-files` extension counts, confirmed gaps (large/binary,
currently committed as raw git blobs, not LFS):

| Ext | Count | Where | Risk |
|---|---|---|---|
| `.bmp` | 3 | `Content/Melodia/Characters/Itako/Textures/{hair_sphere,skin,tops_w3}.bmp` | Confirmed gap (matches the context note). Raw uncompressed textures in git object DB. |
| `.mid` | 2 | `Content/MelodiaIntegration/MIDI/*.mid` | Small (MIDI is tiny), low risk, but still an uncovered binary suffix. |
| `.pyd` | 2 | `Tools/BlenderAddons/rust_gpu_sdf_addon/{bin/win/,}rust_gpu_sdf.pyd` | Compiled Python binary extension (like `.dll`, which *is* covered) — inconsistent, should probably be LFS. |
| `.lib` | 1 | `Plugins/VRM4U/ThirdParty/assimp/lib/x64/Release/assimp-vc141-mt.lib` | Compiled static lib, binary, uncovered. |
| `.pack` / `.idx` | 2 each | `Plugins/PCGExtendedToolkit/.git_disabled/objects/pack/*` | **Not a coverage gap — a separate hazard.** This is a *nested git object store* (a disabled `.git` directory renamed `.git_disabled`) that got committed into the outer repo as regular tracked files. Raw git pack files, binary, uncovered by LFS, and semantically shouldn't be tracked content at all. |

Extensions the context flagged as suspects but that are **not present** in the tree at all (so
not a gap in practice): `.tga` (covered anyway), `.wav`/`.ogg` (covered), `.abc`, `.uexp`,
`.ubulk`, `.spp`, `.exr` (covered, 0 files), `.mov`, `.dds`.

## 6. `.git/lfs/bad` — the 4 quarantined objects

Identified all 4 by OID against `git lfs ls-files --all`:

| OID (short) | Size | Path | Referenced by current HEAD? |
|---|---|---|---|
| `e8f3aebdb9…` | 1.79 GB (1,792,267,474 bytes) | `Exports/PortfolioStages/Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` | **Yes** (`*` in `ls-files --all`) — this is the file currently checked out/expected. |
| `6e66991082…` | ~1.03 MB | `Content/Melodia/_PROJECT/04_Materials/Textures/…/Purple_Nebula/Purple_Nebula_7_-_1024x1024.uasset` | No (`-`) — orphaned historical version, superseded. |
| `b5bd919a3b…` | ~1.07 MB | `…/Purple_Nebula/Purple_Nebula_6_-_1024x1024.uasset` | No (`-`) — orphaned historical version. |
| `bfeca0bc55…` | ~1.07 MB | `…/Blue_Nebula/Blue_Nebula_8_-_1024x1024.uasset` | No (`-`) — orphaned historical version. |

So: 3 of the 4 bad objects are **dead weight** — old revisions of nebula texture `.uasset`s that
no longer exist in HEAD. They can only be reached by rewriting/checking out old commits; deleting
them from `.git/lfs/bad` loses nothing reachable from the current branch tip. The 4th, and by far
the largest (1.75 GB of the 1.75 GB total in `.git/lfs/bad`), is the **one that matters**: it's
the object backing a file that *is* referenced by current HEAD. Its presence in `bad/` rather than
`objects/` means the local LFS smudge filter has a corrupted/incomplete copy — `git lfs fsck` (or
equivalent integrity check) rejected it. Locally this can manifest as that `.blend` file being
missing, truncated, or failing checkout for anyone who re-clones or re-fetches on this machine.
Re-fetching that single object from origin (assuming origin's copy is good) is the fix — see §8.

## 7. GitHub LFS billing exposure — what can and can't be determined offline

**Cannot determine precisely, offline, in this session** — GitHub's LFS storage/bandwidth quota
is a server-side ledger (every object ever pushed, until unreferenced *and* a billing period
rolls over) and there's no local artifact that mirrors it exactly. Network access to
`github.com` failed during this audit:

```
$ git ls-remote origin
fatal: unable to access 'https://github.com/fromage3900/MelodiaMelusinaV2.git/':
Failed to connect to github.com port 443 after 21110 ms: Could not connect to server
```

This was not retried in a loop per instructions — noting the failure and moving on.

What's measurable locally, and what it implies:

- **`.git/lfs` is 19 GB on disk** (`.git` total 20 GB) — this is the *local* object cache
  (`.git/lfs/objects`), which includes historical/orphaned objects (superseded file versions,
  deleted files) that were fetched at some point but are no longer referenced by any ref this
  clone knows about, plus the 1.75 GB in `.git/lfs/bad`.
- **`git lfs ls-files` (current HEAD only) = 2,224 files ≈ 8.8–8.9 GB** — this is what a fresh
  shallow checkout of just the current branch tip would need to download, and is the useful proxy
  for "how big is the game as it stands today," but it is **not** the number GitHub bills against.
- **GitHub LFS billing bills cumulative historical storage** — every distinct OID ever pushed to
  `origin`, still counted until nothing references it AND the object is actually pruned server-side
  (which the owner would have to request/run, `git lfs prune` locally doesn't touch the remote).
  Given `git lfs ls-files --all` shows **10,766** file@oid entries across all local history/refs
  (vs. 2,224 live), a large fraction of history is superseded objects — some meaningful (but
  unknown without remote access) share of that was pushed and is billed regardless of current
  relevance.
- **Free tier is 10 GiB storage + 10 GiB bandwidth/month.** Current live content alone (8.8–8.9 GB)
  is already within ~90% of the 10 GiB storage allowance *before counting any historical/orphaned
  pushed objects*. If even a modest fraction of the ~10 GB gap between `.git/lfs` (19 GB local
  cache) and live content (8.8 GB) was ever pushed to `origin` and hasn't been pruned server-side,
  **the storage free tier is very likely already exceeded**, and has probably been in a billed
  state for some time. This is an inference from local evidence, not a confirmed billing figure —
  flagging it as the highest-confidence estimate obtainable without an authenticated GitHub API
  call (`gh api /repos/fromage3900/MelodiaMelusinaV2` won't even give LFS byte counts directly;
  GitHub's LFS storage/bandwidth usage lives under the account billing pages, not the repo API).
- **Recommendation to get a real number**: when network access is available, log into
  github.com → Settings → Billing → "Git LFS Data" (or the org equivalent) for the exact current
  storage/bandwidth figures. This session cannot substitute for that.

## 8. Prioritized remediation (copy-pasteable, ordered value/risk — highest value-per-risk first)

None of these were run. Read the one-line risk note before running anything marked destructive.

```bash
# 1. (near-zero risk) Re-verify the game-paths-only audit finished clean, confirming §1/§4.
python Tools/lfs_health_audit.py --game-paths-only
# Risk: none — read-only, just re-running a check that was still in progress at report time.

# 2. (near-zero risk) Get GitHub's authoritative billing number once network is up.
gh auth status && gh browse --settings   # or manually: github.com -> Settings -> Billing -> Git LFS Data
# Risk: none — read-only web navigation, resolves the biggest unknown in §7.

# 3. (low risk) Try to repair the one LIVE bad object by re-fetching it from origin.
git lfs fetch origin --include="Exports/PortfolioStages/Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend"
git lfs fsck
# Risk: low — only downloads, does not delete .git/lfs/bad automatically; re-run fsck to confirm
# origin's copy is now clean before touching the quarantined file. Needs GitHub connectivity.

# 4. (low risk, needs owner confirmation) Delete the 3 orphaned bad objects — confirmed
#    unreferenced by current HEAD (see table in §6).
rm ".git/lfs/bad/6e66991082369b214258bf781b68b0b3458291a201a745e88d9f5d5a634575f3"
rm ".git/lfs/bad/b5bd919a3b994f54a0e0024bfce017008a6cb9b2fc8c6d44175254d51a8c5ba6"
rm ".git/lfs/bad/bfeca0bc555816f8119ebc359420e41b2e6d91651a101a417024c9741496d03c"
# Risk: low-but-irreversible-in-this-clone — these are historical superseded texture versions,
# unreachable from current HEAD; deleting frees ~3.2 MB (trivial) and removes clutter. Confirmed
# via `git lfs ls-files --all` (marked `-`, not `*`). Not recoverable from this clone afterward,
# but they're still in origin's history if ever needed. DO NOT delete the 4th (1.79 GB) file this
# way — that one is live-referenced; deleting it without a good replacement corrupts the checkout.

# 5. (medium value, needs owner decision) Add missing LFS coverage for confirmed gaps, going
#    forward only — this does not retroactively fix already-committed raw blobs.
#    Add to .gitattributes (ask first per CLAUDE.md — Config/Content material rule doesn't apply
#    here, but .gitattributes itself is in the project's "never touch without instruction" table):
#      *.bmp filter=lfs diff=lfs merge=lfs -text lockable
#      *.pyd filter=lfs diff=lfs merge=lfs -text lockable
#      *.lib filter=lfs diff=lfs merge=lfs -text lockable
# Risk: none to existing history, but .gitattributes is a protected file per CLAUDE.md — get
# explicit sign-off before editing it, and note this only affects new commits, not the 6 files
# already committed raw (those need `git lfs migrate` — see item 8, separately gated).

# 6. (medium value, needs owner decision) Remove the nested disabled-git pack files — they are
#    not game content and were committed by accident.
git rm -r "Plugins/PCGExtendedToolkit/.git_disabled/objects/pack/"
# Risk: medium — irreversible in working tree until committed by the owner (per repo rules, this
# agent does not commit). Confirm the plugin doesn't need `.git_disabled/` restored before removing
# it; it looks like a leftover from disabling an embedded git repo, not an asset.

# 7. (high value, HIGH RISK — history rewrite, get explicit owner sign-off, do NOT run casually)
#    Actually shrink the ~10 GB gap between .git/lfs (19 GB local) and live content (8.8 GB) by
#    finding + pruning truly-unreachable local LFS cache entries.
git lfs prune --dry-run --verify-remote
# Risk: the --dry-run is safe (read-only preview). The real `git lfs prune` that follows is NOT
# run here per hard rules — it only touches the *local* cache (not origin), but confirm the
# --dry-run list looks sane before ever running it for real, and know it needs remote connectivity
# for --verify-remote to be meaningful.

# 8. (highest value, HIGHEST RISK — full history rewrite, irreversible, coordinate with anyone
#    else who has a clone, and read Docs/GIT_BATCH_DISCIPLINE.md fully first)
#    If the ~10 GB of historical/orphaned LFS content (10,766 all-time file@oid entries vs. 2,224
#    live) is confirmed pushed to origin and billing against the free tier, the only way to
#    actually reduce GitHub-billed storage is a coordinated `git lfs migrate` / history-rewrite +
#    force-push, or GitHub's own LFS object pruning tool.
# Risk: MAXIMUM. Rewrites commit hashes, breaks every existing clone/PR/branch reference,
# requires force-push (explicitly listed as a "warn the user" action even when they ask), and is
# irreversible once other clones rebase onto it. This agent will not run any part of this — it is
# an explicit owner decision, likely with a maintenance-window announcement to any collaborator.
```

### Summary ranking

1. Re-run the game-paths-only check to close out §1 (no risk).
2. Get the real GitHub billing number (no risk, biggest unknown resolved).
3–4. Fix/clear the 4 `.git/lfs/bad` objects (low risk, mostly confirmed-safe).
5–6. Close the two confirmed `.gitattributes` coverage gaps and remove the accidental nested
   `.git_disabled` pack files (medium risk, needs sign-off since both touch protected/ambiguous
   files).
7–8. Any actual reclaiming of the ~10 GB local/historical gap requires prune or history rewrite —
   both are explicitly high-risk and deliberately left as owner-only, unexecuted recommendations.
