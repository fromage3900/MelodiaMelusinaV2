# Melodia Studio 3D Asset Branch — Polish Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Refine `cursor/laptop-3d-asset-convergence-1e72` into a polished, durable
`pipeline/melodia-studio-3d` branch — the dedicated home for Melodia Studio addon work,
Melusina House asset prep, and the Blender→UE intake rail, documented in the house
voice with ledgers, not vibes.

**Architecture:** The branch converges onto `main`, so it becomes a *lane*, not a fork:
docs land in `Docs/MelodiaStudio/`, addon source stays in `Tools/BlenderAddons/melodia_studio/`,
house lineage in `RawArt/MelusinasHouse/`, stage scripts in `deploy/surreal_arch/`.
Every gate gets a dated ledger row with an evidence path. Prose is not a ledger row.

**Tech Stack:** Git (LFS + `git -c http.version=HTTP/1.1` always), Blender 5.2.1 LTS
headless, the melodia_studio addon (268 builders), GitHub PR flow (main merges via PR +
REST, never direct push).

---

## Current state (verified 2026-09-06, not recalled)

- Branch `origin/cursor/laptop-3d-asset-convergence-1e72` is **1 commit ahead, 0 behind**
  `origin/main` (merge-base 15f03403, PR #113). One commit: `5862f539
  recover(laptop): converge Melusina House 3D lineage onto current main`.
- That commit brings: `melusinahouse_v7_plan.md` (repo root), `SESSION_NOTES_2026-09-04.md`
  (repo root), `RawArt/MelusinasHouse/Intermediates/` (25 LFS `.blend` pointers, greybox→v6
  lineage), `deploy/surreal_arch/integration.py` (908 lines, **absent on main**), two
  Splice inventory docs (~1,300 lines, absent on main).
- Main already holds: V7 base blend (`fa6911aa`), the full `melodia_studio` addon tree,
  five `Docs/MelodiaStudio/` files. The addon is NOT ignored by git — it's tracked.
- **The v7 plan's V0 BLOCKED ledger is stale:** PR #96 (`b828e82f`, merged 2026-09-05
  21:07) landed real mh6 shell fixes on main — openings, empty-cutter guard, wall-band
  grid — plus `Tools/verify_full_registry.py` + committed `Tools/registry_baseline.json`
  (289/403 ok, 9 known errors). Task 7 shrinks to *verify-and-reledger*.
- Still open per registry baseline: 16 dead builders, 8 passthrough stubs, rebrand
  decision.
- Laptop is healthy and back; `P:` was only an old drive letter. Docs must stop
  treating P: as a third copy — authority is the repo; AppData is the live deploy copy.
- `Melusina's_Study.blend` (027dce9b, 09-05 14:28) lives **only** on
  `feature/grandmaster-melodia-studio`; its single commit says interior unfurnished.
  No dressing commits exist anywhere in git.

**Owner steer (2026-09-06, evening):** laptop is fine and back; P: = old drive letter,
removed from new docs. User is fetching the decorated Study state now — if uncommitted
dressing exists on the laptop, it lands as a new commit under the Task 5b structure
(RawArt/MelusinasHouse study home, LFS lock before editing).

---

## Proposed branch shape

```
BS_GodFile
├── Docs/MelodiaStudio/
│   ├── PIPELINE_OVERVIEW.md              # NEW — the one-page map of the 3D lane
│   ├── MELUSINA_HOUSE_V7_PLAN.md         # moved from repo root (was melusinahouse_v7_plan.md)
│   ├── SESSION_NOTES_2026-09-04.md       # moved from repo root
│   └── (existing five files stay)
├── RawArt/MelusinasHouse/                # LFS-locked handoff surface (README already good)
│   ├── MelusinasHouse_V7_Base.blend
│   └── Intermediates/                    # recovered lineage, stays
├── Tools/BlenderAddons/melodia_studio/   # addon source, stays as-is
├── deploy/surreal_arch/                  # stage scripts + integration.py (stays)
└── Saved/Audit/melusinashouse/           # evidence drops (renders, verify JSON)
```

Repo root ends up with zero loose 3D-lane docs. Everything under `Docs/MelodiaStudio/`.

---

## Step-by-step plan

### Task 1: Fresh lane branch off the converged tip

**Objective:** Give the polished work a clean, honestly-named branch instead of a
session-slug (`cursor/laptop-3d-...`).

```bash
cd C:/EnvironmentPortfolio/BS_GodFile
git -c http.version=HTTP/1.1 fetch origin
git switch -c pipeline/melodia-studio-3d origin/cursor/laptop-3d-asset-convergence-1e72
```

Verify: `git log --oneline -2` shows `5862f539` at the tip, tree matches main.

### Task 2: Relocate the loose docs

**Objective:** `melusinahouse_v7_plan.md` and `SESSION_NOTES_2026-09-04.md` move into
`Docs/MelodiaStudio/` with capitalization matching its neighbors.

```bash
git mv melusinahouse_v7_plan.md Docs/MelodiaStudio/MELUSINA_HOUSE_V7_PLAN.md
git mv SESSION_NOTES_2026-09-04.md Docs/MelodiaStudio/SESSION_NOTES_2026-09-04.md
git commit -m "docs(studio): move v7 plan and 09-04 session notes into Docs/MelodiaStudio"
```

Verify: `git status --short` clean; `grep -rn "melusinahouse_v7_plan" --include="*.md" .`
— fix any inbound references (RawArt README, cross-doc links) in the same commit.

### Task 3: Restore `integration.py` — main is broken without it (VERIFIED, subagent audit + spot-check 2026-09-06)

**Objective:** The branch copy isn't new work — main *lost* it. Verdict: KEEP and
restore to `origin/main` in the first PR.

Evidence (file:line on `origin/main`):
- `deploy/surreal_arch/bootstrap.py:103` — `from .integration import patch_monolith`
  inside `repatch()`, raises ImportError outright.
- `deploy/surreal_architecture_gen.py:38558/38565/38574` — the monolith's own
  `register()`/`unregister()` import `register_overhaul`/`patch_monolith`/
  `unregister_overhaul` from it; the surrounding `except Exception` swallows the
  ImportError, so the whole overhaul layer silently never loads on main.
- `deploy/surreal_arch/genome_carousel.py:102,135`,
  `deploy/surreal_arch/music_ui.py:590` (`_register_class_once`), 5 probe scripts, and
  `deploy/sync_surreal_to_live.ps1:64` (the deploy sync still lists
  `surreal_arch\integration.py`) — 13+ consumers, one missing module.
- No supersede: `def patch_monolith|register_overhaul|unregister_overhaul|
  _register_class_once` has zero hits on main outside the deleted file.
- Lost in merge `a72e2eee` (PR #98 cross-line reconciliation) — parent 2 lacked the
  file; no dedicated delete commit exists. Branch blob `b7fe7f10` is byte-identical to
  main's last good copy, so restoring is risk-free.
- Session-note claim verified: `integration.py:504-527` is exactly the `**kwargs`
  force-forwarding wrapper that fixed the live-addon break (2026-09-04 notes:20-23).

```bash
git checkout 5862f539 -- deploy/surreal_arch/integration.py
git commit -m "fix(surreal_arch): restore integration.py lost in PR #98 cross-line merge (13 importers on main)"
```

Verify: headless import smoke —
`blender --background --python-expr "import sys; sys.path.insert(0,'deploy'); import surreal_arch.bootstrap"`
(or the repo's existing probe entry) passes; `grep -rn "from .integration" deploy/surreal_arch/`
consumers resolve.

### Task 4: Write `Docs/MelodiaStudio/PIPELINE_OVERVIEW.md`

**Objective:** The one-page map: what the 3D lane is, where every artifact lives, what's
open. In the owner's voice — declarative, gate-driven, facts-not-claims, ledger at the
bottom.

Content requirements:
- **Machine truth (2026-09-06):** the laptop is healthy and back in the fold; `P:` was
  an old drive letter and its name is scrubbed from this lane's docs (leave the
  archived session notes verbatim — they are history; new docs say: authority is the
  repo (`Tools/BlenderAddons/melodia_studio/` + `deploy/surreal_arch/`), AppData is the
  live deploy copy, md5-verify repo → AppData on every addon edit. Cross-machine
  handoff for `.blend` sources = the LFS lock discipline already in
  `RawArt/MelusinasHouse/README.md`).
- **Intake rail diagram (text):** idea → builder (grep registry first) → headless verify
  → stage script nests builder → V7 base blend → FBX/USD export → UE import → lookdev.
- **Ledger of open decisions:** rebrand choice, V0 defects, 16 dead builders, 8 stubs —
  each with file:line pointer into `MELUSINA_HOUSE_V7_PLAN.md`.
- Commit: `docs(studio): pipeline overview — machine truth, intake rail, open ledger`.

Verify: every path named in the doc exists (`git ls-files <path>` per row).

### Task 5: Splice docs to their proper home

**Objective:** `Docs/Tools/SPLICE_SAMPLES_*.md` are a music-kit inventory, not 3D
pipeline. `Docs/Tools/` on main holds only `puzzle-sandbox` and there is no
`Docs/Music/` — create `Docs/Music/` with these two files as its founding rows.
Commit: `docs(music): relocate splice inventories to Docs/Music`.

### Task 5b: Inherit the grandmaster lane (the Study + 14 family kits)

**Objective:** `origin/feature/grandmaster-melodia-studio` is 2 commits ahead of main
and holds work the polished branch must NOT orphan:
- `0b50b42d` — 14 family kit modules under `deploy/surreal_arch/melodia_gn/`
  (aesthetic_fx 4,542 lines, civic_kit, castle_kit, core_forms_kit, euro, zen, asian,
  scifi, walls, buildings, filigree, materials…) + `core.py` string-param accessors +
  C1 `mh6_shell_adapter` + Tools family gates. **None of these modules exist in main's
  tree** — yet main's `Tools/registry_baseline.json` (403 ids) lists their builder ids
  (`MEL_aest_adv_crystals` etc.), so main's own baseline references code it does not
  carry. Reconcile: either merge the kits and re-run
  `python Tools/verify_full_registry.py` (expect the MEL_aest_* empties to resolve),
  or the baseline was generated from a fatter checkout — say so in a doc row.
- `027dce9b` — `Saved/MelusinasHouse/Melusina's_Study.blend` (WIP shell: 30 objects,
  gabled roofs, framed window openings, pill-grid fill; interior unfurnished, camera
  unaimed per its own commit message). `Saved/` is gitignored for UE — this path
  rides only because `.gitattributes` LFS-tracks `*.blend` (note `Saved/MelusinasHouse`
  was added with it deliberately). Move/record the Study where the pipeline can see it:
  candidate home `RawArt/MelusinasHouse/MelusinasStudy/` alongside V7, or a row in
  PIPELINE_OVERVIEW linking the blend where it lives.

**Method:** merge, don't cherry-pick onto the pipeline branch —
```bash
git merge origin/feature/grandmaster-melodia-studio \
  -m "merge(grandmaster): 14 family kits + C1 adapter + Melusina's Study blend onto studio pipeline"
```
Expected conflicts: `core.py`, `__init__.py`, `melodia_house.py` (main carries PR #96
mh6 fixes the branch was cut before). Resolve in favor of main's shell + branch's kits.

Verify: `python -c "import ast; ..."` parse-check of touched modules; registry harness
run; Study blend opens headless (`blender --background -P probe` per
`RawArt` README convention); ledger row added to `MELUSINA_HOUSE_V7_PLAN.md`.

### Task 6: Intermediates README honesty pass

**Objective:** `RawArt/MelusinasHouse/Intermediates/README.md` is 11 lines. Bring it to a
one-table ledger: filename → what it is → dead or alive (v4_FINAL is the LOOKDEV-era
hero; v6_lego/p1 predate convergence; the CHECKPOINT file is a dead branch). Mark the
lineage terminus: everything converges into `MelusinasHouse_V7_Base.blend` at root.
Commit: `docs(rawart): intermediates lineage ledger`.

### Task 7: V0 re-ledger — verify the merged shell fixes, then flip the gate

**Objective:** The V0 BLOCKED forensics in `MELUSINA_HOUSE_V7_PLAN.md` are stale:
PR #96 (commit `b828e82f`, merged 2026-09-05 21:07) already fixed both defects on main
— cutter-scale Combine Y=0 flattening, unconnected cutter grid Size Y, wrong arch
cylinder axis, empty-SDF collapse guard — verified by 20-stage headless bisection
(`v0_final_verify.log`: openings 55158 vs 48200 verts, guard holds 48200 vs 112,
Depth honored). This task confirms and re-legers, it does not re-fix:

1. Re-run the proof headless on main's current tree (mh6 shell vs stock cell bbox at
   same params, openings survive, Depth honored).
2. If PASS: flip the ledger row `BLOCKED` → `PASS 2026-MM-DD` with the log/png path in
   `Saved/Audit/melusinashouse/`, and add a dated note that PR #96 predates the v7
   plan's forensics section.
3. Only if FAIL: open the bisection work described in the old forensics (attribute taps
   bevel → SDF → boolean → fillet → offset).

**Files:** `Docs/MelodiaStudio/MELUSINA_HOUSE_V7_PLAN.md` (ledger), probe script under
`Tools/`, evidence in `Saved/Audit/melusinashouse/`.

Verify: V0 gate rule unchanged — cell rewiring (V0 step 2, nesting `MEL_mh6_room_shell`
into `MEL_city_house_cell` via the C1 adapter from Task 5b) proceeds only after the
ledger row flips with an evidence path. The C1 `mh6_shell_adapter` + identity-proof
harness from `0b50b42d` is exactly the rewiring tool — it arrives with Task 5b's merge.

### Task 8: Verification rail (V4 of the v7 plan, pulled forward)

**Objective:** `Tools/house_v7_verify.py` — builds stock + converged cell, T corridor,
piano walk, organ split, roof param drive; realizes instances before vert counts; writes
JSON verdict to `Saved/Audit/melusinashouse/v7_verify_last.json` + 4-up contact sheet.
This is the harness every later gate cites. Command:
`blender --background --python Tools/house_v7_verify.py` (exit 0 = green).
Commit: `feat(tools): house v7 verify rail`.

### Task 9: Dead-builder and stub quarantine

**Objective:** Land the V5 phases 0–1 against main's addon: harness PASS/FAIL list per
builder, 8 stubs flagged `role='research'`, 16 dead builders either imported+verified
or deleted-and-logged in `ADDON_AUTHORITY`. Registry baseline JSON committed so name
loss is diffable. Two commits: `feat(addon): builder harness`, then `chore(addon): quarantine stubs`.

### Task 10: Ship the branch

**Objective:** Publish and hand off honestly.
```bash
git -c http.version=HTTP/1.1 push -u origin pipeline/melodia-studio-3d
```
- Open PR to main for the docs/structure commits (Tasks 1–6) — small, reviewable.
- Tasks 7–9 stay on the branch as stacked work until each gate's ledger row earns its merge.
- After merge, retire `cursor/laptop-3d-asset-convergence-1e72` per the branch-triage
  routine (confirm no unique commits first: `git log origin/cursor/...1e72 ^main --oneline`
  must be empty).

---

## Files likely to change

- Create: `Docs/MelodiaStudio/PIPELINE_OVERVIEW.md`, `Tools/house_v7_verify.py`,
  `Saved/Audit/melusinashouse/*` (evidence)
- Move: `melusinahouse_v7_plan.md`, `SESSION_NOTES_2026-09-04.md`, Splice docs
- Modify: `RawArt/MelusinasHouse/Intermediates/README.md`, addon mh6 shell module,
  `ADDON_AUTHORITY` doc
- Decide: `deploy/surreal_arch/integration.py` keep/merge

## Risks & open questions

1. **LFS pointer trap:** the 25 Intermediates `.blend`s are pointer files on the branch;
   anyone checking it out needs `git lfs pull` or they get 3-line files. Call it out in
   PIPELINE_OVERVIEW.
2. **Old P: references litter the recovered docs** (v7 plan, session notes name
   `P:/MelodiaMelusinaV2-Laptop/...` paths that no longer resolve). Policy: archived
   docs stay verbatim; PIPELINE_OVERVIEW carries the corrected machine map so nobody
   chases a ghost drive letter.
3. **V0 fixes touch live geometry** — everything after Task 6 is guarded by the harness
   (Task 8) running green before/after each change.
4. **Task 5b merge conflicts** in `core.py` / `melodia_house.py` between PR #96 shell
   fixes and the grandmaster absorb work — resolve toward main's shell, branch's kits;
   registry harness is the arbiter.
5. Rebrand (Melodia Studio vs Surreal Studio vs Forge) stays an owner decision;
   PIPELINE_OVERVIEW presents it as an open ledger row, not a verdict.

## Done means

- Branch `pipeline/melodia-studio-3d` pushed, docs PR open against main, repo root clean
  of loose 3D-lane files, every claim in PIPELINE_OVERVIEW backed by a path that exists,
  and the V0 ledger row either flipped to PASS with a PNG or still honestly BLOCKED.
