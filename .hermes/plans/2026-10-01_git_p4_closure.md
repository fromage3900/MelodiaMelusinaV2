# Git + Perforce Closure Plan — 2026-10-01

**Goal:** finish the version-control sweep. Correct the ACF architecture error, land the
remaining work in the system that owns it, and leave both depots verified.

**Status:** PR #391 (Morning OFPA fix) is **merged to main** and CI-green. Everything below
is what remains.

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
