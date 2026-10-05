# Git + Perforce Closure Plan — 2026-10-01

**Goal:** finish the version-control sweep. Correct the ACF architecture error, land the
remaining work in the system that owns it, and leave both depots verified.

**Status: COMPLETE for the two approved submissions.** Both changelists submitted and verified
in the depot. See "Outcome" at the bottom for the receipts and what remains open.

---

## Principle being applied

`Content/*` and bulk binary are **Perforce's** responsibility on this repo. Git carries
native/runtime systems, code, docs, and specs. This is not a preference — it is enforced:
the `docs/` branch prefix caps git LFS at 50 MB, and the repo has a 512 MB normal cap.
Committing the 458 MB AscentCombatFramework binary payload to git was a category error and
CI blocked it correctly.

---

## Phase 1 — Git: land what legitimately belongs in git

**1.1 Drop the ACF binary commits from the working branch.**
`docs/honcho-discord-sync` carries 20 commits of ACF `Content/` binary that must not merge.
The branch is 22 ahead / 5 behind main. Plan:

- Reset the branch to `origin/main` (the ACF source + Resources already landed via PR #387;
  the binary `Content/` never will).
- Keep the branch for the 2 legitimate commits it still owns, or retire it. The Morning fix
  is **already on main** via #391, so nothing is lost by resetting.

**1.2 Remaining untracked, non-binary, worth committing to git:**

| Path | Files | Verdict |
|---|---|---|
| `.hermes/plans/2026-10-01_1700-choral-sheep-capstone-build.md` | 1 | commit — a plan is documentation |
| `Docs/AIRI/MelusinaCard/` | 1 | commit the card, **exclude the `.zip`** (pre-commit rejects zip) |
| 1 modified tracked file | 1 | inspect, then commit |

**1.3 The 283 untracked `Content/` files** — do **not** blanket-add. Classify first; they
are p4 territory. See Phase 2.

---

## Phase 2 — Perforce: put the binary where it belongs

**2.1 Restore `.p4ignore`.** It is **missing from the repo root** and `P4IGNORE` points at
it. Without it `reconcile` sweeps build junk, `Saved/`, and `.git/`. This is a
prerequisite for every step below and it is currently a live hazard.

**2.2 `p4 add` the AscentCombatFramework plugin (2,712 files, ~1.4 GB).**
It is in **neither** system right now — 0 files in the depot, binary unlanded in git, so it
exists only on this disk. This is the single largest exposure on the machine.

- Must exclude `Binaries/`, `Intermediate/`, `*.pdb`, `*.dll` (build output).
- Open into a **new dedicated changelist**, not `default` — `default` already holds 182 files.
- `p4 add` is safe and reversible (`p4 revert`); it does not submit.

**2.3 Submit decision — owner call, three CLs:**

| CL | Contents | Recommendation |
|---|---|---|
| new | ACF plugin (2,712 files) | **submit** — single-copy exposure |
| new | 16 at-risk Morning external actors | **submit** — these are the audit finding |
| existing 182 in `default` | mixed lanes incl. Morning + VFX | review before submit; do not bulk-submit |

Existing pending CLs 224/227/235/264/265/267 are all still **HOLD / REVIEW / SHELVE-ONLY**
and must not be submitted without explicit approval.

**2.4 `Content/Massive` (206 files).** Already fully in the depot, 4/206 in git. This is the
intended split — confirm, then no action.

**2.5 Classify the 283 untracked `Content/` files.** Reconcile will propose them; review the
list before opening. They are Melodia/EnvSandbox/UltraDynamicSky textures and materials —
bulk art, p4's job.

---

## Phase 3 — Verify (no prose-as-evidence)

```
# git
git log --oneline origin/main -3
git ls-tree -r origin/main --name-only | grep -c '^Plugins/AscentCombatFramework/Content/'   # expect 0
git ls-tree -r origin/main --name-only -- Content/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning   # expect 258

# p4
p4 info                                                   # ticket valid, client/stream correct
p4 files //Melodia/main/Plugins/AscentCombatFramework/... | wc -l   # expect 2712-ish
p4 opened -c default | wc -l
p4 changes -s pending -u froma
df -h /d                                                  # depot disk headroom
```

---

## Risks and blockers

- **D: is at 94% (114 GB free).** Adding 1.4 GB of plugin to the depot is fine, but the
  depot has no headroom to spare. Check before submitting large CLs.
- **`.p4ignore` missing** makes any `reconcile` unsafe until restored. Do Phase 2.1 first.
- **p4 ticket expires in 12 h.** A long `add` job may need a re-login mid-flight.
- **`p4 reconcile -I` disables ignore-checking** — the opposite of intuition. Use plain
  `reconcile`.
- **Binary `.uasset` diffs are invisible to `p4 diff`** — verify adds by count, not diff.
- **Editor is running on :9316.** `p4 add` on plugin content is safe (it does not load
  packages), but do not `p4 edit` files the editor has open.

---

## Explicitly out of scope

- No `git gc --prune`, no history rewrite, no force-push, no branch deletion without approval.
- No new landscape for `L_MelusinaMorning` (contract: no landscape floor; `ground_probe`
  runs against `SM_PM3D_Sphere3D*` islands).
- No submit of any HOLD/REVIEW/SHELVE-ONLY changelist.

---

## Outcome — 2026-10-01 (owner approved both submissions)

### Submitted and verified in the depot

| Change | Was | Contents | Verified |
|---|---|---|---|
| **271** | CL 271 | 16 `L_MelusinaMorning` external actors that had **no second copy** | `p4 files` answers all 16 at `#1 - add change 271`; the `no such file` condition is gone |
| **272** | CL 270 | AscentCombatFramework plugin, **2,712 files** (Source 1154 / Content 1446 / Config 11 / Resources 98, plus `ACF Discord Tutorial.txt` whose space-in-name made `p4 files` word-split and report a phantom 2,711) | `p4 files //Melodia/main/Plugins/AscentCombatFramework/...` = 2711 + the spaced-name file = **2712**; **0** `Binaries/`/`Intermediate/`/`.pdb`/`.dll` in the depot |
| **273** | submitted | 123 `Content/` files that had no p4 copy — Choral Sheep audio bank (73), Chladni textures, Kawaii VFX MIs, EdgeDesat post-process, the forged `A_Cascadeur_Melusina_BowDraw_v2_Forge_InPlace`, Sea Above prototype actors | all 123 read back at `#1 - add change 273`; 18.2 MB; pure adds |
| **275** | submitted | `Melusina.airi-card.zip` — the last true single-copy file. The git pre-commit hook rejects zips, Perforce does not | resolves at `#1 - add change 275` |
| **276** | submitted | Melusina animation archive — 63 files / 13.9 MB: `LegacyRetargets_20261001`, `Retarget/_Archive`, `MelusinaFinal` manifest | **63/63 on disk == 63/63 in depot, 0 missing** |

**The Perforce server root is `D:\perforce\root` on this machine.** A submit is history-tracked,
not off-machine; GitHub is the only offsite copy. See
[`STORAGE_ARCHITECTURE_2026-10-01.md`](../../docs/Production/STORAGE_ARCHITECTURE_2026-10-01.md).

Perforce renumbered CL 270 → **change 272** on submit. That is normal `p4 submit` behaviour,
not a second submission — `p4 changes -s submitted -m 3` shows 272 and 271 only.

Both were pure `add` operations (no `edit`, so nothing could clobber a depot revision), and
both files are read-only (`-r--r--r--`) again post-submit, per the `binary+l` typemap.
`p4 opened` is back to 166 in `default` — CLs 270 and 271 are empty.

### Git side

| | |
|---|---|
| main tip | `12ad9b2a2` (PR #392 merged, CI green) |
| Morning actors on main | **258 / 258** |
| ACF **binary** on main | **0** (correctly refused; now lives in p4 change 272) |
| ACF **source** on main | 1,153 — landed earlier via PR #387, left alone (no history rewrite) |

The 18 ACF-binary commits remain on `docs/honcho-discord-sync`, unpushed to main and
recoverable by SHA. They are now redundant with p4 change 272 and can be dropped whenever the
owner retires that branch.

### Still open

1. **166 files in `default` + CLs 224/227/235/264/265/267** — untouched, all still
   HOLD / REVIEW / SHELVE-ONLY. Not submitted.
2. **283 untracked `Content/` files** — Melodia/EnvSandbox/UltraDynamicSky bulk art. Belong
   in p4; not yet reconciled. Classify before opening.
3. **`Reference/`** (247 files, 106 MB) and the remaining ACF texture dirs — untracked, no VCS
   home yet.
4. **`.p4ignore` restored but untracked in git.** It should be committed so the next machine
   and any other agent inherit the ignore rules; `P4IGNORE` already points at that exact path.
5. **ACF source on main** — owner's call whether it stays in git or moves wholesale to p4.
