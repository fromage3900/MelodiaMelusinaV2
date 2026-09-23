# Stage-and-push plan — 2026-09-23 (GN lane → origin, for PC pull)

Written per the GIT PIPELINE LAW: no branch creation, no commits, no push
without this plan stated first and explicit owner approval per operation.

## Goal

Get tonight's GN-lane work (Track A builders 4–6, the BRUTALIST pair, the
shared family helpers, the showcase stage and its evidence) onto `origin` so
the desktop PC can pull it.

## Verified state (read-only checks, run 2026-09-23)

- Branch: `collab/laptop/brooch-sky-20260917` (already published; local tip ==
  `origin/…` tip, 0/0 — the push is a clean fast-forward, no force needed).
- Branch is 23 commits ahead of `origin/main` — that is the existing laptop
  line. **`main` is not touched by this plan.**
- Working tree: 124 changed entries. Only the GN lane is in scope (below);
  the other entries are listed under "explicitly NOT included" with reasons.
- Hooks that will run:
  - `pre-commit`: blocks >50 MB non-LFS files, `.blend1/.zip/.7z`, zero-byte
    files, and anything under `Saved/` except `Saved/Audit/*.(json|md)`,
    `Saved/AnimationReference/*.md`, `Saved/MelusinasHouse/*.blend`,
    `Saved/Accessories/*`.
  - `pre-push`: branch-prefix allowlist (`collab/*` passes), `main` push
    blocked, LFS budget gate — **50 MB for `collab/*`** (payload here ≈ 6 MB).
- `Saved/` is gitignored → the audit artifacts need `git add -f` (precedent:
  268 files already tracked there).
- Precedents followed: `913531ab` (GN state → PC = deploy/ + Docs text),
  `7df713fb` (renders → tracked non-Saved path, LFS).

## Commit A — GN lane source + docs + evidence (text, no friction)

Staged paths (exact):

```
deploy/surreal_arch/melodia_gn/paris_common.py            (new)
deploy/surreal_arch/melodia_gn/paris_fountain_loop.py     (new)
deploy/surreal_arch/melodia_gn/paris_daynight_facade.py   (new)
deploy/surreal_arch/melodia_gn/paris_mansard.py           (new)
deploy/surreal_arch/melodia_gn/paris_penrose_arch.py      (new)
deploy/surreal_arch/melodia_gn/paris_metamorphosis_frieze.py (new)
deploy/surreal_arch/melodia_gn/brutalist_office.py        (new)
deploy/surreal_arch/melodia_gn/brutalist_cubicles.py      (new)
deploy/surreal_arch/melodia_gn/__init__.py                (M — imports)
deploy/surreal_arch/melodia_gn/presets.py                 (M — +11 presets)
deploy/_melodia_health_paris_mansard.py                   (new)
deploy/_melodia_health_paris_penrose_arch.py              (new)
deploy/_melodia_health_paris_metamorphosis_frieze.py      (new)
deploy/_melodia_health_paris_fountain_loop.py             (new)
deploy/_melodia_health_paris_daynight_facade.py           (new)
deploy/_melodia_health_brutalist_office.py                (new)
deploy/_melodia_health_brutalist_cubicles.py              (new)
deploy/_melodia_render_paris_previews.py                  (new)
deploy/_melodia_stage_gn_showcase.py                      (new)
Docs/Production/CLOSEOUT_PLAN_2026-09-23.md               (new)
Docs/Production/MAISON_IMPOSSIBLE_2026-09-20.md           (M — Next section)
Docs/Production/MELODIA_STUDIO_CLOSEOUT_2026-09-21.md     (M — known-open)
Tools/registry_baseline.json                              (M — re-cut, 601 ids)
Tools/verify_addon.py                                     (M — RECORDED_EMPTIES
                                                            137→138, so Gate D
                                                            stays green on the PC)
```

Force-added (gitignored, hook-allowlisted `Saved/Audit/*.md|json`):

```
Saved/Audit/BRUTALIST_AND_STAGE_2026-09-23.md
Saved/Audit/PARIS_TRACKA_BUILDERS_2_3_2026-09-22.md
Saved/Audit/gn_showcase_manifest.json
Saved/Audit/census_20260922.json / b / c .json, census_20260923.json
Saved/Audit/registry_baseline_pre_trackA_20260922.json
Saved/Audit/registry_baseline_pre_trackA6_20260922.json
Saved/Audit/registry_baseline_pre_brutalist_20260923.json
```

Command:

```
git add <the paths above>
git add -f <the Saved/Audit paths above>
git commit -m "feat(melodia-gn): Track A builders 4-6, BRUTALIST office pair, shared family helpers - for PC pull"
```

## Commit B — showcase binaries (RECOMMENDED, optional)

The stage `.blend` and the 14 preview PNGs cannot be committed from `Saved/`
(gitignore + pre-commit hook both block that path family). To give the PC the
literal files with **zero infrastructure edits**, publish copies under a
tracked path (precedent: `RawArt/MelusinasHouse/Intermediates/*.blend`,
`Website/**` for renders; `*.blend`/`*.png` are LFS-tracked):

```
mkdir -p RawArt/GNShowcase/previews
cp Saved/Blend/MELODIA_GN_SHOWCASE_2026-09-23.blend RawArt/GNShowcase/
cp Saved/Audit/paris_trackA_previews/*.png           RawArt/GNShowcase/previews/
git add RawArt/GNShowcase
git commit -m "chore(melodia-gn): showcase stage blend + 14 previews (LFS) - for PC pull"
```

Payload ≈ 6 MB (0.44 MB blend + 5.4 MB previews) — well under the 50 MB
`collab/*` LFS budget. If you would rather keep the repo lean, **skip B**:
the stage file regenerates on the PC in one command (below).

Long-term alternative (owner call, not tonight): add `!Saved/Blend/` to
`.gitignore` plus one exception line in `.githooks/pre-commit`, so stage
blends can be committed in place.

## Push

```
git push origin collab/laptop/brooch-sky-20260917
git ls-remote origin refs/heads/collab/laptop/brooch-sky-20260917   # verify tip
```

Fast-forward only; no `--force`, no merge, no rebase, no new branch.

## Desktop PC steps (after the push)

```
git fetch origin
git checkout collab/laptop/brooch-sky-20260917      # or, on an existing checkout:
git pull --ff-only
git lfs pull
```

Then, to see the staged scene on the PC (either open
`RawArt/GNShowcase/MELODIA_GN_SHOWCASE_2026-09-23.blend`, or regenerate):

```
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python deploy/_melodia_stage_gn_showcase.py
```

Gate re-check on the PC after pull:
`blender --background --factory-startup --python Tools/verify_addon.py`
(expect `GATE RESULT: PASS (6/6)` against the new 601-id baseline).

## Explicitly NOT included (and why)

- `Content/**/*.uasset` (61 files) — **LFS pointer churn**, not content
  changes; the desktop's Content is canonical. Never commit these from the
  laptop.
- `.github/`, `.claude/`, `.opencode/`, `.jcode/`, `Chapters/`, `AGENTS.md`,
  `AGENT_START_HERE.md`, `CURRENT_STATE.md`, `MELUSINA_HOUSE_GN_START_HERE.md`
  — pre-existing edits from earlier sessions/other lanes, not reviewed by this
  session. Separate call.
- `Tools/brooch_*.py`, `Tools/BlenderAddons/*`, `Saved/Accessories/brooch_lab/*`,
  `Saved/Audit/v114_sbs/*`, `RawArt/BlenderLibraries/Higgas/` (untracked) —
  brooch/Higgsas lane strays. Separate call.
- `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`,
  `Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md` — earlier-session doc
  edits, unreviewed.

## Rollback

Nothing is published until the push. If a commit is wrong before pushing:
`git reset --soft HEAD~1` (explicit approval) then re-stage. After the push,
the branch is additive on `collab/*` — correcting means a follow-up commit,
never a rewrite.
