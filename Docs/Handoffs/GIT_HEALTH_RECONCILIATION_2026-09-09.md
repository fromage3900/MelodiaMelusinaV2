# Git Health Reconciliation — 2026-09-09

**Operator:** build agent (pre-UE-hour prep)
**Request:** Lane A + "complete and documented git health merged in isolated batches to main with no loose ends"
**Outcome: merged via PR, not direct push.** Pre-push hook blocks direct `main` pushes (reviewed branch/PR only).
Unification is staged as **PR #133** (`integration/main-unify-20260909` → `main`).

## 1. What was found

- Local `main` was 77 commits ahead of `origin/main` (`c2add6cd..743fe548`), believed 0 behind.
- `git fetch` revealed **remote had advanced 64 commits** (`c2add6cd..f1ed4d89`): capstone/TD
  cross-repo docs, reference boards, PR #121 (studio F2/F3b), PR #122 (Convergence Mode).
- True state at discovery: **local 77 ahead / remote 64 behind → diverged, 141-commit unification.**
- Working tree was dirty (18 modified/staged `.uasset` + C++ + untracked scratch/actors/docs).

Because the remote moved mid-operation, per-batch pushes to `origin/main` were impossible
(non-fast-forward). The plan adapted: **isolated commits locally → single verified merge → PR.**

## 2. Isolated triage batches (committed on `feat/choral-sheep-root-c-material-proof-2026-09-08`)

| # | SHA | Batch | Contents |
|---|-----|-------|----------|
| B1 | `0c55a900` | docs(mocap) | 3 handoffs (benchmark take, Cascadeur LiveLink studio, Meet2 corner) + `Companions/Melusina/README_CASCADEUR_STUDIO.md` |
| B2 | `2d1f8b49` | feat(choralsheep) C++ | Harmonize reactivity: Tick ramp, reactive tag + explicit subsystem registration, null-safe interaction entry. **UNBUILT — header change needs closed-editor build** |
| B3 | `f6076362` | feat(choralsheep) content | BP/DA/MI_Body/Coat_PCC/SK + `T_Chladni_C_ROOT` + fixture PNG + generator script as provenance. Scratch excluded |
| B4 | `36663933` | style(lookdev) | 4 Melusina MIs + `M_Master_Nikki_Landscape` + `M_Master_Toon_Character` |

Published (policy-compliant name) as `feature/choral-sheep-root-c-material-proof-2026-09-08` —
local `feat/` prefix violates the pre-push branch policy, so the remote name uses `feature/`.
LFS budget gate: 1.71 MB / 512 MB OK.

## 3. Merge construction (zero worktree contact)

Editor was running (holds `.uasset` handles; cf. 2026-09-04 merge record), so no checkout/merge
touched the worktree or HEAD:

1. `git merge-tree <base> HEAD origin/main` → informational format, **zero conflict markers**.
2. Definitive check: `diff(base..HEAD) ∩ diff(base..origin/main)` = **exactly 2 files**, both
   text docs, both auto-merged with both banners preserved:
   - `Docs/TD_GRANDMASTER_MELODIA_PLAN.md`
   - `Docs/TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md`
3. All binaries one-sided (no binary conflicts). Spot-verified in result tree `555c1ecf`:
   local `SK_ChoralSheep` blob `eda9bdd` preserved; remote `convergence_mode.py` + ChoralSheep
   reference boards present.
4. `update-ref refs/heads/main 36663933` (ff, verified ancestor) →
   `commit-tree <tree> -p <local> -p <remote>` → **`4689d74f`** → `update-ref refs/heads/main`.
5. Pushed as `integration/main-unify-20260909` (direct main push blocked by hook) → **PR #133**.

Local `main` now sits at `4689d74f` (82 ahead / 0 behind). It converges with `origin/main`
the moment PR #133 merges.

## 4. Deliberately NOT merged (deferred with reason, still worktree-only)

- **2 modified Sea Above external actors** (`2/UX/EZRR…`, `4/YK/GGB4…`): live editor session owns
  them. Commit after the UE hour with a clean editor close.
- **New Sea Above actor files** (`7/C9`, `D/T1`, 6 files in `E/M9`) + empty editor-created dirs
  (`2/PG`, `5/EL`, `9/S3`, `B/KJ`, `D/V1` — empty dirs, untracked by git by nature): same reason.
- **`M_Scratch_Test.uasset`** (untracked, unreferenced anywhere in Content): scratch.
  Delete in a closed-editor cleanup pass; do not promote.
- **B2 C++ unbuilt**: `Tick` override + new UPROPERTYs = header change → closed-editor `Build.bat`
  before any PIE trust. Live Coding cannot register these.

## 5. Adjacent findings for the owner

- ~25 `wardrobe watch runNN heartbeat` commits are permanent main-line noise. History was NOT
  rewritten (shared across workstations/daemons). Recommendation: heartbeat lane commits to a
  non-main branch going forward, squashed on promotion.
- `recovery/laptop-main-20260904` was not touched; wholesale merge remains forbidden per standing rule.
- TODO.md "Refresh persistence closure from current main; do not merge stale PR #54 wholesale"
  is still open and now unblocked on the unified line once PR #133 lands.

## 6. After PR #133 merges

1. `git fetch origin` + verify `main...origin/main` = 0 0.
2. UE hour (see `LANE_A_PERSISTENCE_RUN_SHEET_2026-09-09.md`), then commit deferred Sea Above
   actors from a clean editor close.
3. This doc + the Lane A sheet ride on the feature branch until the next promotion (see §7).

## 7. Loose-end ledger (everything has an owner)

| Item | State | Owner/next step |
|------|-------|-----------------|
| PR #133 | open, merge commit `4689d74f` | owner review → merge |
| This doc + Lane A sheet | committed on feature branch (next commit) | next promotion after #133 |
| 2 Sea Above actors + new actor files | dirty/untracked, documented §4 | UE hour → clean close → commit |
| `M_Scratch_Test.uasset` | untracked, documented §4 | closed-editor delete |
| B2 C++ build | committed, unbuilt | closed-editor `Build.bat` |
| Watch-heartbeat noise policy | documented §5 | owner decision |
