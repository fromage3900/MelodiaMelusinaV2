# HANDOFF — Melodia Studio P2/Shell + Two-Repo Organization (2026-09-05)

Written at session close. Both repos clean, everything committed and pushed.
Read this before touching either repo or the addon. Companion docs (all
current, don't re-derive):

- Plan SSOT: `Docs/References/MelusinasHouse/ONE_ECOSYSTEM_ABSORPTION_PLAN_2026-09-04.md`
  (§8 ledger reconciled 2026-09-05, commit b8d2330d — every row cites its commit)
- Shell plan: `Docs/References/MelusinasHouse/ROOM_SHELL_CONVERGENCE_PLAN_2026-09-04.md`
- Sync contract: `Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`

---

## 1. Where the work stands

### Melodia Studio one-ecosystem absorption (P: docs/2026-09-02-grand-master-plan)

- P0 safety net: DONE (f980df0a harness, 50cddcbf baseline refresh — zero
  regressions in the pre-existing 268).
- P1 kernel param-schema: DONE (4a2113b5).
- P2 absorption: 210/276 builders across 14 family modules in
  `deploy/surreal_arch/melodia_gn/` — aesthetic 70, scifi 7, zen/castle/asian
  22, civic 19, experimental 17, euro 11, core_forms 14, walls 15,
  buildings+misc 22, filigree 3, materials 10. Ten gate-verified commits,
  fcef35a1 → 7e5304d2. Music-notation dupes (4) routed via melodia_gn_route.
- Shell convergence ladder: **C1 PASS 2026-09-05** (e0328da7).
  `melodia_house.py::mh6_shell_adapter` maps greybox param names onto
  MEL_mh6_room_shell with measured SDF compensation. Key measured facts that
  future sessions must not re-litigate:
  - mh6's SDF hollow offset dilates the exterior by Wall Thickness T on every
    face (spans exceed declared extents by 2T). The adapter subtracts 2T and
    lifts +T in the CALLER's tree; mh6 itself is untouched.
  - 1e-3 bbox equality is unattainable across an SDF grid: voxel quantization
    is ~±0.05 at Voxel Size 0.035. The gate asserts voxel tolerance + a
    documented cornice allowance (mh6-only feature, same class as openings).
  - Proof: `melodiamelusinav2/Tools/house_c1_identity_proof.py`, evidence
    `melodiamelusinav2/Saved/Audit/melusinashouse/v0_c1_identity.{json,png}`.
- Gate discipline that held all session: three-copy sync P: → C: → AppData
  with md5 BEFORE every headless run; grep the marker lines, never trust exit
  codes; headless runs start `cd /c` then absolute blender path.

### Next steps, in order (the ladder)

1. **C2 — city cell rewire**: `melodia_city_gen.py:379` replaces
   `_ensure_group_node("MEL_greybox_room_kit")` with the mh6 shell via
   `mh6_shell_adapter`. Cell params map W→Room Length, D→Room Width, H→Room
   Height, T→Wall Thickness; Roof Rise and Show Roof untouched. Gate: same 3
   param sets as C1 + T-corridor and piano walk still green.
2. **C3 — music room shell fold**: `music_heroes.py::build_music_room_shell`
   swaps its nested greybox for mh6 via the same adapter. Gate: dado band
   present, door/window cuts in slice probe, vert count same order.
3. **C4 — monolith room-shell routes**: GREYBOX_ROOM / GB_ROOM_COMPOSITE /
   GB_COMBAT_ROOM / GREYBOX_TOWER / GB_ELEVATOR_SHAFT / MODULAR_HOUSE routed
   onto mh6 via melodia_gn_route / register_kit seams. NO edits inside
   surreal_architecture_gen.py. Gate: spawn through the monolith's own picker.
4. **C6 parity grep**: `MEL_greybox_room_kit` nested only by
   interior/corridor builders (melusina_house.py interiors, city plan
   interiors/corridors, music_heroes until C3).
5. **C5 roof authority declaration** (grep-gate only, no mesh changes) and
   **C7 presets/docs/ledger** close the ladder. Then core_forms remainder
   (73) and the P3 dispatch rework.

### Melusina's Study blend (owner-authored, C: repo)

- `Saved/MelusinasHouse/Melusina's_Study.blend` committed LFS (027dce9b).
- WIP state documented in the commit message: detached partition panels right
  of the main block, unfurnished interiors, pill-grid floor fill leaves zero
  circulation, authored camera aims at empty sky (renders verified from
  computed bounds instead: `Saved/Audit/melusinashouse/study2_{hero,top,interior}.png`).
- Not defects: geometry is intact — no collapsed sheets, z-fighting, or
  floating pieces. Owner to continue staging.

---

## 2. Repo organization — findings

Both repos: working trees CLEAN, 0 unpushed commits at handoff time.

### P: MelodiaMelusinaV2 (branch docs/2026-09-02-grand-master-plan, HEAD b8d2330d)

- Branch is 48 ahead / 21 behind local `main`. The 21 behind are git-hygiene
  commits on main (branch prune docs, LFS renormalizes) — low conflict risk,
  but the branch needs a main sync before any narrow-promotion to main.
- Local `main` is ahead 13 / behind 39 vs origin/main — do not push main
  without reconciling first.
- Stale local branch: `collab/laptop/integration-batch-2026-09-02` — its
  upstream is GONE (remote-deleted). Its content (deep intake report) also
  lives on `collab/laptop/main-reconciliation-2026-09-04` (same c0c4148c
  parent, still has an upstream). Safe to delete the local dead one after
  confirming c0c4148c is reachable from the reconciliation branch.
- This repo's hook only accepts feature/ fix/ docs/ cleanup/ collab/
  integration/ codex/ recovery/ cursor/ prefixes (integration/* added
  2026-09-05, 9aef3a15).

### C: melodiamelusinav2 (branch fix/mh6-fix-promotion-20260904, HEAD 027dce9b)

- Grandmaster branch `feature/grandmaster-melodia-studio` exists at the same
  HEAD and is pushed. It is a POINTER at the latest verified state, NOT a
  merge of every branch — deliberate, per the narrow-promotion rule.
- Branch is 63 ahead / 13 behind local main. The 13 behind on main include
  owner-requested house-version commits (bd870dd6) — check them before
  rebasing anything.
- This repo's hook has NO integration/ lane (the 9aef3a15 hook change was
  P:-side only). Allowed prefixes: feature/ fix/ docs/ cleanup/ collab/
  codex/ recovery/ cursor/. `feat/` and bare names are REJECTED — the
  grandmaster branch had to be named feature/grandmaster-melodia-studio.
- Remote branches not merged into grandmaster (18+): mostly stale cursor/
  codex/ copilot/ checkpoints. Do not bulk-delete; the P: side has a standing
  rule about "not on main ≠ not committed" and a prior prune needed a
  guard commit (957f80c9). Reconcile via the reconciliation branch, not
  wholesale.

### AppData live addon: VERIFIED in sync

All 77 melodia_gn .py files md5-identical across P: SSOT, C: deploy, and
AppData live copy (checked at handoff). After ANY future addon edit, re-sync
all three and md5-verify before running gates — a stale AppData copy gates
nothing.

---

## 3. Unfinished tasks ledger (owner-visible)

### Owner actions only you can do

1. **G1 PR to main**: `fix/mh6-shell-promotion-20260904` → main (P:). The mh6
   fix is done-on-branch and gate-proven; the PR is the only thing between it
   and main. Ledger marks G1 "DONE on branch, PR pending owner."
2. **Study blend continuation**: furnish interiors, place the detached
   partition panels, re-aim the authored camera, decide circulation aisles in
   the pill-grid fill.
3. **Rebrand decision** (from the V7 intake): "Melodia Studio" umbrella
   naming — still parked, blocks P4 UI unification detail work.

### Studio lane (next session picks up at C2)

- C2 → C3 → C4 → C5 → C6 → C7 as ordered in §1. Each has its gate defined in
  ROOM_SHELL_CONVERGENCE_PLAN_2026-09-04.md. Prose is not a ledger row: every
  gate needs a dated PASS line + evidence path in the plan §8.
- Then: core_forms remainder (73 builders — closure-based extraction handles
  them in 2–3 batches), prototype trio (3, rides P3 dispatch), P3 single
  dispatch, P4 single UI, P5 monolith retirement (<500 lines).
- Known monolith defects surfaced by ports (do not "fix" the monolith; they
  die with it): zen_pagoda reads outputs['Geometry'] on CurveToMesh (correct
  output 'Mesh'); 9 known socket-drift registry errors documented in
  registry_baseline refresh (50cddcbf).

### Game lane (separate from studio — tracked in TODO.md, 57 open items)

- Nearest open: transplant runtime-persistence from stale PR #54 onto fresh
  main; RestoreNarrativeRecord idempotency audit; full process restart proof;
  packaged-build proof. TODO.md §NOW is the authority — this handoff does not
  duplicate it.
- AGENTS.md discovery rules remain binding: dated docs saying "blocked" are
  historical until checked against source; recovery/laptop-main-20260904
  still must not be merged wholesale.

---

## 4. Environment facts that cost time this session (inherit, don't rediscover)

- Registered builders: MOST return a bare tree; city_gen builders return
  (tree, gin, gout). Normalize with a `_norm()` helper — `[0]` on a tree
  raises `TypeError: bpy_struct[key]: only strings are allowed`.
- `all()` over an empty/errored result set is True — the verdict expression
  must require non-empty results (a previous session's "PASS" was exactly
  this bug).
- Blender headless: run `cd /c && "C:/Program Files/.../blender.exe"
  --background --python <abs path>`; piping through grep eats buffered output
  on crash, redirect to a log file and grep after. The `NameError: name 'bpy'
  is not defined` traceback in every log is addon-teardown noise, not a
  failure. GN modifiers need base geometry — evaluate on a small bmesh cube
  host.
- `bpy.ops.wm.read_factory_settings(use_empty=True)` unregisters addon
  classes: delete `surreal_arch*` from sys.modules and re-import after the
  reset.
- C: repo hook rejects branch names without the allowed prefixes — name
  lanes `fix/…` or `feature/…` from the start.

— End of handoff. Nothing else is left uncommitted in either repo.
