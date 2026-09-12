# Merge to main — triage and batch plan (2026-09-04)

## The "570 unpushed commits" figure is misleading

`git log --all --not --remotes` returns 570, but that is the **union across ~34 branches**
with heavy overlap, not 570 distinct pieces of work. Twelve branches each report 341–400
unpushed commits because they share almost the same base:

```
400  cursor/git-health-checkpoint-c2b1
362  feat/2026-09-02-github-pages-atmosphere
362  codex/weapon-gallery-20260902
360  integration/2026-09-02-front-door-cymatic-sanctuary
...  (eight more in the 341-356 range)
 16  merge/unify-histories   <- the working branch
```

## What actually needs to reach main

`main` and `merge/unify-histories` have genuinely diverged:

```
main ahead of HEAD : 704
HEAD ahead of main : 641
```

Of the 641, only **16 are from today** (after 2026-09-03 12:00). The other 625 are older
history the working branch carries — Melusina house documentation packets, GN phase plans
and similar — whose provenance has not been audited in this session.

**Do not merge 641 commits to get 16.** Cherry-pick the 16.

## The 16, in chronological order, grouped into batches

Cherry-pick oldest first; the order below minimises conflicts.

### Batch 1 — UI / main menu
```
f3949f7e  docs(ui): computed main-menu orrery fix values
53bda2e4  fix(ui): main menu layout - orrery on screen, text collisions resolved
```

### Batch 2 — Ocean / water
```
d0471791  fix(ocean): repair corrupted P0 SeaAbove water instance
b7e413c5  fix(fx): align runtime ocean base with repaired asset; audio-reactivity handoff
db8e0217  feat(ocean): route bioluminescence through MF_NikkiSparkle
```

### Batch 3 — Audio reactivity
```
0bc95bfb  docs(audio): root cause - route leg 0 has no music clock
5fea50c8  fix(audio+ui): clock on GameMode so every level reacts; revert starfield regression
9b74f333  feat(audio): Electric Dreams ambience + landscape reacts to the beat
d6df96aa  verify(audio): reactivity confirmed live in PIE with measured values
```

### Batch 4 — FX
```
c08f41f0  fix(fx): replace DefaultSpriteMaterial green balls; wire click sparkle
```

### Batch 5 — Build
```
8b545ac6  fix(build): editor builds green - LPCTSTR was the real root cause
```

### Batch 6 — Landscape / Gaea
```
35e18932  lookdev(landscape): real rock/mud normals + restore audio reactivity on SeaAbove
4af6f72e  feat(landscape): import Gaea weightmaps and enable mask-driven layer blending
4a9ecf34  docs(landscape): close Gaea intake question; plan PCG volume layout and dressing
```

### Batch 7 — Wardrobe (authored by GPT Sol, not by this session)
```
47f2b8dd  chore(wardrobe): verify ButterflyWingMembrane 9/9 2048 PASS
a9f1578b  chore(wardrobe): restore+verify MEL_garment_tension_folds loom v2 - GN52 PASS
```
These are committed, not in-flight, so they are safe to carry — but they are another
agent's work. Confirm with the owner before including them.

## BLOCKER — do not start while the tree is dirty

At time of writing the working tree has **92 modified files** from GPT Sol, concentrated in
`Content/Python` (15), `EnvSandbox/Materials/Instances/Landscape` (14), `Docs/Plans` (13),
`EnvSandbox/Materials/Masters` (10) and `Tools/PCG` (5).

Switching to `main` would rewrite every file that differs across a 641/704-commit
divergence and would disturb that in-flight work. **Wait until those changes are committed
or stashed by their author.**

A `git worktree` would normally sidestep this, but `Content/` is ~88 GB, so a second
checkout is not practical here.

## Procedure once the tree is clean

```bash
git checkout main
git cherry-pick f3949f7e 53bda2e4                     # batch 1
git cherry-pick d0471791 b7e413c5 db8e0217            # batch 2
git cherry-pick 0bc95bfb 5fea50c8 9b74f333 d6df96aa   # batch 3
git cherry-pick c08f41f0                              # batch 4
git cherry-pick 8b545ac6                              # batch 5
git cherry-pick 35e18932 4af6f72e 4a9ecf34            # batch 6
```

Verify after each batch, not at the end. `.uasset` conflicts cannot be merged by text —
on any conflict, take one side deliberately (`git checkout --ours|--theirs <path>`) and
re-verify the asset in the editor before continuing.

**Do not push main.** The pre-push hook forbids it and that constraint stands.

## Backup status

- Network to origin is **down** (`curl 28`, port 443) — two snapshot pushes failed today.
- Offline bundle written and verified:
  `G:/melodia_bundles/today-16-20260904-0249.bundle` (69 MB, "records a complete history").
- **Caveat:** a git bundle carries objects and LFS *pointers*, not LFS *blobs*. Text and
  history are protected; `.uasset` binary content is not. A full off-machine copy still
  needs either a successful `git push` or an LFS-aware mirror.

## Recommended order of operations

1. GPT Sol commits or stashes its 92 files.
2. Cherry-pick batches 1–6 onto main, verifying between batches.
3. Decide on batch 7 with the owner.
4. Retry the origin push when the network returns; that is the only thing that gets LFS
   blobs off this machine.
