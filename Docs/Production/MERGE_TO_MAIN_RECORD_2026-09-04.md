# Merge to main — execution record (2026-09-04)

Companion to `MERGE_TO_MAIN_TRIAGE_2026-09-04.md`, which planned this merge.
This records what was **actually done**, including where the plan had to change.

## The planned procedure did not survive contact — and why

The triage doc's procedure was `git checkout main` followed by six `git cherry-pick`
batches. That was attempted and **abandoned**, because two other processes hold this
repository:

1. **The Unreal editor (PID 7760) holds `.uasset` file handles.** `git checkout main`
   reported `unable to unlink old ... Invalid argument` for 13 assets and left them
   carrying merge-branch content while `HEAD` said `main` — a half-applied checkout.
   This is *not* the git-lfs read-only bit; `chmod 666` did not clear it.
2. **The overnight wardrobe daemon drives git itself.** Mid-operation it checked the
   repo out from `main` onto `llm/fromage/BS_GodFile/shorewake-chapter-loop` and
   committed (`b8d3a7c6`). The reflog shows the branch switch happening between two of
   this session's commands.

A cherry-pick sequence interrupted by a concurrent `git checkout` from another process
is genuinely destructive. The plan was changed rather than forced.

## What was done instead

The whole merge was replayed **in the object graph only** — `git merge-tree
--write-tree` to compute each merged tree, `git commit-tree` to build the chain, then a
single `git branch -f main`. This never touches the working tree, the index, or `HEAD`,
so it cannot collide with the editor's file handles or the daemon's checkouts.

18 commits were replayed onto `main`:

| Batch | Commits | Subject |
|---|---|---|
| 1 | `f3949f7e` `53bda2e4` | UI / main menu |
| 2 | `d0471791` `b7e413c5` `db8e0217` | Ocean / water |
| 3 | `0bc95bfb` `5fea50c8` `9b74f333` `d6df96aa` | Audio reactivity |
| 4 | `c08f41f0` | FX — green-ball materials, click sparkle |
| 5 | `8b545ac6` | Build — `LPCTSTR` root cause |
| 6 | `35e18932` `4af6f72e` `4a9ecf34` | Landscape / Gaea |
| 7 | `f52a0fb3` `18625459` `62b80fee` | GPT Sol's convergence, tooling and content |
| 8 | `20d960a2` | The triage doc itself |

Batch 7 was **added beyond the original plan**. Sol's `f52a0fb3` is dated after
`9b74f333` and supersedes it for `M_Master_Nikki_Landscape`; landing batches 1–6
without it would have put a stale landscape master on `main` while the merge branch and
the on-disk asset carried a newer one.

## Conflicts — three, each resolved deliberately

| Where | Kind | Resolution |
|---|---|---|
| `Docs/LookDev/LOOKDEV_PREP_2026-09-03.md` | add/add | **Kept both sides.** `main` held §6–8 (shirt tuning, `SK_MelusinaHair`, Oceanology correction); the incoming commit added §9 (main menu). Concatenated — this is an append-only lookdev log, so a superset is the correct result. Verified §6, §7, §8, §9 all present and in order. |
| `M_Master_Nikki_Landscape.uasset` | content (binary) | **Took the incoming side.** A `.uasset` cannot be text-merged. `main`'s side came from `a528df8a`, *"resave master materials"* — editor churn, not authored change. The incoming side carries the cymatics wiring that is the entire payload of `9b74f333`, and is superseded later in the chain by Sol's converged master anyway. |
| 3× `Docs/References/MelusinasHouse/REF_0*.jpg` | modify/delete | **Kept the files.** Deleted on `main`'s side, modified by Sol in `62b80fee`. Reference images are inert, and Sol touched them deliberately; deleting another agent's referenced material on a merge is the destructive choice. |

No conflict markers exist anywhere in the result — verified by grep on the three
affected paths.

## Verification performed before `main` was moved

- **LFS completeness.** All 259 `main`-side LFS blobs for differing binaries confirmed
  present in `.git/lfs/objects` *before* the checkout was attempted. The network to
  origin is down, so a missing blob would have silently produced pointer-file corruption
  in the working tree.
- **Path-level equivalence.** Of the 135 paths touched by the replayed commits, 132 are
  byte-identical to the merge-branch tip. The three that differ are the two deliberate
  resolutions above plus `OVERNIGHT_STATE.md` (auto-merged daemon state).
- **`main`'s own work preserved.** `MelodiaAudioReactivePresentationSubsystem.cpp` in the
  result retains the *consumer-facing alias lanes* block (`BassIntensity` / `MidIntensity`
  / `BeatTracker`, reconciliation 2026-09-02) that exists on `main` but **not** on the
  merge branch. The replay added today's work on top of it rather than reverting it.
- **Payload spot-checks, all passing:** ocean base `0.205079`; `const TCHAR* MaterialToken`;
  `ExportRenderTarget2DAsPNG`; `FindMorphTarget`; `import_gaea_glacier_weightmaps.py`;
  `WBP_MainMenu`, `M_Water_Oceanology_Melodia` and `MI_Glacier_Landscape_Layered` present.

## Still outstanding

- **`main` has not been pushed, and must not be** — the pre-push hook forbids it and that
  constraint stands. The merge is local.
- **Origin is still unreachable** (`curl 28`); four push attempts have now failed. Nothing
  is off-machine except `G:/melodia_bundles/today-16-20260904-0249.bundle`, which carries
  LFS *pointers*, not blobs. A successful push or an LFS-aware mirror is still the only
  real backup.
- **The working tree is not on `main`.** The daemon left `HEAD` on
  `llm/fromage/BS_GodFile/shorewake-chapter-loop` with 13 editor-locked files dirty.
  Reconciling the working tree requires the editor to be closed; the merge itself does
  not.
- Rollback refs: `backup/unify-histories-20260904` and tag
  `premerge/unify-histories-20260904`, both at `62b80fee`. `main`'s pre-merge tip was
  `3d3b6644`.

---

## Addendum — backup completed, and a divergence worth knowing about

Written after the section above; it supersedes that section's "Still outstanding" claim
that nothing had been pushed.

### The push succeeded

Connectivity returned (intermittently — roughly two of every three probes connect), and
two branches reached origin:

| Branch on origin | Commit | What it protects |
|---|---|---|
| `recovery/unify-histories-20260904` | `62b80fee` | the source branch — today's work as originally committed |
| `recovery/main-merged-20260904` | `53216f24` | the merge result, i.e. what local `main` now points at |

**68 LFS objects / 67 MB uploaded.** This is the first genuine off-machine backup of this
work: the `G:` bundle carried LFS *pointers* only, so the binary content of every
`.uasset` touched today existed in exactly one place until now.

Note on the branch names: the pre-push hook rejects any branch not prefixed
`feature/ fix/ docs/ cleanup/ collab/ codex/ recovery/ cursor/`, so the original
`backup/…` name was refused. `recovery/` is the hook-sanctioned prefix for this.
**`main` itself was not pushed** — `refs/heads/main` on origin is untouched.

### Local `main` and `origin/main` are unrelated lineages

This predates today's merge and is not a consequence of it:

```
origin/main   8c6b204d      628 commits not in local main
local main    3d3b6644      704 commits not in origin/main   (tip before today's merge)
```

They are **diverged, not ahead/behind** — neither is an ancestor of the other. So
"merged to main" in this document means **local `main` only**. Anyone reading
`origin/main` will not see today's work; they should read
`recovery/main-merged-20260904` instead.

Reconciling those two lineages is a separate decision with real consequences and is
deliberately **not** attempted here. It is not a merge conflict to grind through — it is
a question about which history is authoritative, and that is the owner's call.
