# Branch cleanup — verified 2026-08-25

Every branch other than `main`, classified by whether its content is actually present in `main`.

**Method matters here.** `git rev-list --left-right --count main...<branch>` is misleading after a
squash merge — the merge base never advances, so a fully-merged branch still reports commits "ahead".
Every verdict below comes from checking each changed file with `git cat-file -e main:<path>`, and
from `git check-ignore` on anything absent (a file can be absent because `main` correctly ignores it,
which is not unmerged work).

Nothing here has been deleted. This is the list to act on.

---

## SAFE TO DELETE — 15 branches, zero unmerged content

### Ancestors of `main` (contained by definition)

| Branch | Evidence |
|---|---|
| `claireon-test` | `git merge-base --is-ancestor` passes |
| `claude/magical-williamson-a3534a` | ancestor |
| `feature/claireon-test-20260819` | ancestor |
| `safety/pre-g-sync-20260821` | ancestor |

### Squash-merged into `main` on 2026-08-20 — every changed file present

| Branch | Files checked | Absent from main |
|---|---|---|
| `feature/credits-20260813` (+ `origin/`) | 8 | 0 |
| `feature/echo-topo-chapter2` | 9 | 0 |
| `cursor/model-lanes-agents-slim-f425` (+ `origin/`) | 10 | 0 |
| `origin/cursor/phone-artist-bridge-handoff-0f00` | 2 | 0 |
| `origin/cursor/twinmotion-realityscan-handoff-1a53` | 3 | 0 |
| `origin/cursor/pie-rhythm-highway-notes-1a53` | 6 | 0 |
| `origin/cursor/v2-game-foundation-098b` | 39 | 0 |
| `origin/cursor/toronto-ai-startup-research-ca02` | 14 | 0 |

### Deliberately not merged — superseded, but content is present anyway

| Branch | Files | Absent | Why it was skipped |
|---|---|---|---|
| `origin/cursor/restore-party-callsite-0f00` | 1 | 0 | Superseded by PR #6 (2026-08-12). Its version passes `ActiveBattleActor`; main's comment states *"ActiveBattleActor is the tagged encounter, not the controller."* Merging it would **double-call `RestorePartyAfterBattle`** in `HandleBattleOver`. |
| `origin/cursor/restore-party-controller-e6ac` | 7 | 0 | Same C++ fix, already on main. Its only unique content was 08-12 docs saying PRs #4 and #6 still needed approval — both merged. |

### Merged despite an "absent" count that looks alarming

| Branch | Files | Absent | Verdict |
|---|---|---|---|
| `origin/cursor/git-health-batches-e6ac` | 159 | 148 | **Merged.** 147 of the 148 are gitignored, and the 148th is a mojibake-named tutorial `.txt` in the same tree. They are all the ZBrush Orb Brushes pack that this branch's own commit *"chore: gitignore + untrack brush pack"* deliberately removed. Their absence is the branch working as intended, not unmerged work. |

---

## KEEP — real unmerged content

### `origin/feature/repo-lockin-20260813` — **164 files still unmerged**

The 2026-08-20 session merged this in two parts (`309a575d` assets, `caee6389` text/code), but 164
files never landed. Only 1 of them is gitignored; the rest are genuine.

| Area | Count |
|---|---|
| `Content/Python/` | 97 |
| `Content/Melodia/` (mostly `Melusina/V2Test/Animations/`) | 33 |
| `Tools/BlenderAddons/` | 17 |
| `deploy/` one-off scripts | ~10 |

**Includes `Content/EnvSandbox/Environments/Sakura/L_SakuraPath.umap`** — human-owned art per
CLAUDE.md. Do not auto-merge that file; it needs an explicit owner decision.

### `pr/melusina-v22-sync` — **all 11 files unmerged**, dated 2026-08-24

The newest unmerged work in the repo. Melusina v22 body textures (`T_Melusina_Body_BC/Emission/H/
Mask/N/ORM.uasset`), two locomotion animations (`A_Melusina_GlidePose`, `A_Melusina_RunLoop_Trim`),
`Tools/import_body_textures_live.py`, `Tools/import_body_v22.py`, and
`research/melusina_v22_sync_fix_2026-08-24.md`. Nothing here exists on `main`.

### `origin/cursor/nemotron-research-docs-2d2d` — 4 files unmerged

`Docs/Handoffs/TODAY_2026-08-19_PARALLEL_PLAN.md`,
`Docs/Handoffs/claireon_ue58_build_report_TEMPLATE.md`,
`Docs/PhoneOps/OPENCODE_MOBILE_CLIENT_2026-08-19.md`,
`specs/nemotron_ground_truth/T3_handle_quill_notification.json`.

### `origin/cursor/recruiter-sendoffs-no-nvidia-ca02` — 1 file unmerged, dated **today**

`Docs/Career/RECRUITER_SENDOFFS_2026-08-25.md`. Note `origin/main` is 1 commit ahead of local `main`
with the matching subject *"docs(career): OpenCode-first sendoffs; NVIDIA withdrawn"* — pull before
assuming this is unmerged.

### `recovery/melodia-main-sync-20260811` — 369 commits ahead

Tracks `legacy-melodia/main`, a different repo. Those commits exist only there. Cherry-pick or
abandon deliberately; do not push as-is. Unchanged guidance from `_TASK_QUEUE.md`.

---

## Suggested order

1. **Pull first** — `origin/main` is 1 ahead of local `main`.
2. Delete the 15 safe branches (local + remote).
3. Land the 4 keeps, smallest first: recruiter sendoff → nemotron docs → `pr/melusina-v22-sync` →
   `repo-lockin`'s 164, with `L_SakuraPath.umap` held out for owner review.
4. `git gc --prune=now` after the deletions.

Deleting merged branches matters beyond tidiness: per `Docs/GIT_BATCH_DISCIPLINE.md` rule 5, LFS
objects reachable only from pushed dead branches are billed indefinitely.
