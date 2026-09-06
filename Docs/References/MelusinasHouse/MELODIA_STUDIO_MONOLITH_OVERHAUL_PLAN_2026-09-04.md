# MELODIA STUDIO + SURREAL ARCHITECTURE — MONOLITH OVERHAUL PLAN

**Date:** 2026-09-04 (evening, after git re-sync)
**Supersedes:** ROOM_SHELL_CONVERGENCE_PLAN_2026-09-04.md as the master ladder
(same C1–C7 shell ladder, now nested inside a full monolith breakdown).
**Read with:** MELUSINA_HOUSE_GN_START_HERE.md, AGENT_START_HERE.md,
Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md,
Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md,
deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md (docs branch).

---

## 0. State of the world (verified tonight)

### The two codebases

| Surface | Size | Nature |
|---|---|---|
| `surreal_architecture_gen.py` (monolith) | 38,596 lines, v2.131 | Scene-workflow addon: 209-id arch_type enum → ~274 builders that AUTHOR GN nodes into per-object `SurrealArch_<obj>` trees. 246 category entries / 224 unique piece ids / ~52 categories. 53 ARCH_PRESETS, 16 styles, 9 materials, ~89 bmesh specials. Extension seams BUILT IN: `kit_registration.py::register_kit`, `catalog_dispatch.py`, `melodia_gn_route.py`. |
| `deploy/surreal_arch/melodia_gn/` (package) | ~62 modules | 268+ registered GN builders via `register_builder`; Melodia Studio N-panel catalog; house/city/music kits; presets.py. |

These are NOT duplicates of each other. The monolith is the interactive
scene/props/controls layer; the package is the curated GN builder catalog.
The unhealthy part is not coexistence — it is the three parallel room-shell
constructions, four roof paths, and the fact that neither side knows what the
other owns. Breakdown = make ownership explicit and route, not rewrite.

### Git reality (new tonight)

- `origin/main` @ c154efd9: Melusina House GN discoverability landed —
  `melusina_house_foundation.py` (4 MEL_mh_foundation_* builders), dedicated
  `melusina_house` GN category, presets, `Tools/verify_melusina_house_gn_catalog.py`,
  front-door docs, two-workstation sync contract.
- **The mh6 V0 defect fix (3f1d4460) is ONLY on `docs/2026-09-02-grand-master-plan`.**
  origin/main's melodia_house.py has the new categories but NOT the guard,
  grid wiring, or osc.Y fix. This is the single most important promotion.
- 95 remote branches; PRs #79/#81 superseded; V7 baseline promoted via PR #82
  to `RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend`. Recovery branches
  are history-only; promotion is narrow named-file batches.
- `ADDON_AUTHORITY_2026-09-03.md` exists only on the docs branch — promote it.
- Sync discipline is now codified: `deploy/sync_workstation.ps1` +
  `install_melodia_studio.ps1` (installer sources its own checkout). The
  manual three-copy md5 rule remains the local fallback.

---

## 1. Target end-state (what "healthy" means)

```text
ONE scene workflow (monolith dispatch + props + panels)
ONE curated GN catalog (melodia_gn package)
ONE room-shell authority (mh6) for every exterior
ONE interior-shell authority (greybox_room_kit) for rooms/corridors
ONE roof authority per role (object-level = _build_curved_roof)
Every cross-system use goes through a registered seam (register_kit /
register_builder / melodia_gn_route) — zero copy-paste geometry code
Every builder discoverable: category + verifier + front-door doc
Every change: harness PASS + three-copy sync + narrow git promotion
```

Non-goals: no big-bang rewrite of the monolith; no deletion of greybox;
no bmesh-special rewrites; no param renames; no new shell builders.

---

## 2. G-workstream — git reconciliation (do FIRST, unblocks everything)

| Step | Action | Gate |
|---|---|---|
| G1 | Promote mh6 V0 fix (3f1d4460, one file) from docs branch onto `main` as a narrow batch; run `v0_final_verify.py` against post-merge AppData install | verifier PASS + builder count stable |
| G2 | Promote `ADDON_AUTHORITY_2026-09-03.md` + convergence/overhaul docs from docs branch to main docs tree | files on main |
| G3 | Docs branch (23+ commits of session docs/handoffs) reviewed file-by-file; promote named docs, leave branch as history | discovery doc updated |
| G4 | Adopt sync_workstation contract on this laptop: after every addon session, run sync + installer; retire manual-copy as primary | report clean |
| G5 | After G1–G4, archive recovery/* and collab/laptop/* per LAPTOP_WORK_DISCOVERY policy | branches marked history in doc |

---

## 3. M-workstream — monolith breakdown (strangler via existing seams)

The monolith already knows how to be extended from outside
(register_kit → _KIT_DISPATCH/_CATALOG_DISPATCH + param-spec stubs;
melodia_gn_route → MEL_ builders). Use ONLY those seams. Never edit inside
the 38k-line file except version bumps forced by register() ordering.

### M0 — Baseline health lock (before touching anything)
1. Headless harness `Tools/verify_monolith_dispatch.py`: iterate the
   arch_type enum, generate each of the 209 ids on a scratch object
   (force=True), realize, record vert count + errors to JSON.
2. Baseline JSON committed; any later monolith work re-runs and diffs.
   Gate: every id generates without exceptions (research/fallback ids
   allowed to produce fallback geometry — recorded, not failed).

### M1 — Shell convergence inside the package (C1–C3 of the shell plan)
- C1 param adapter + stock-cell vs mh6 identity proof (3 param sets).
- C2 city cell rewired onto mh6; T-corridor + piano walk stay green.
- C3 music_room_shell re-nested onto mh6; dado band survives.
- Gate per step: headless eval + slice probe + contact sheet.

### M2 — Monolith shell family routed (C4)
1. Route GREYBOX_ROOM / GB_ROOM_COMPOSITE / GB_COMBAT_ROOM /
   GREYBOX_TOWER / GB_ELEVATOR_SHAFT (+ MODULAR_HOUSE wall faces) to the
   converged shell via melodia_gn_route / register_kit.
2. Gate: spawn each through the monolith's OWN picker/operator path;
   realize; bbox tolerance vs pre-routing baseline (M0 JSON); slice probe
   shows door/window cuts; greybox_graph.py room-graph presets still
   spawn + snap. M0 diff must show zero regression on all other ids.

### M3 — Roof authority (C5)
Declare roles in ADDON_AUTHORITY and enforce by grep:
- object-level roof: `_build_curved_roof` + `_add_roof_modifier_stack`
  (SurrealRoof_* staging) — THE roof;
- GN in-tree roof: exactly ONE of `build_roof_tiles` / `_curved_roof`;
  the other demoted/aliased (owner picks which);
- `_conical_roof_swept`: only where pagodas/towers call it.
Gate: grep census + M0 diff.

### M4 — Kit extraction (continuous, low-risk)
Move monolith builder functions into cohesive package modules ONLY when a
builder needs a fix or a feature — never bulk:
```text
greybox kit family   → melodia_gn/greybox_kit.py   (via register_kit)
zen kit family       → melodia_gn/zen_kit.py
scifi effects        → melodia_gn/scifi_fx.py
aesthetic passes     → melodia_gn/aesthetic_fx.py
```
Each extraction: register_kit with arch_id parity, param-spec stubs
generated, M0 diff clean, monolith keeps its enum entry (delegation, not
deletion). The 38k file shrinks only at the speed of real need.

### M5 — Dead-weight triage (owner-decided)
From the 2026-09-04 subagent audits: 16 dead builders in 9 modules, 8
passthrough stubs (p4_*, mother_tapestry_wall), version-ladder v1s, backup
dir inside the addons tree. Quarantine behind role='research'/hidden first;
delete only in a clean owner session with a logged decision. Never as a
side effect of other work.

### M6 — Naming + discovery (continuous)
- New/edited builders register to the right category (house →
  `melusina_house`, shared primitives stay generic) per the integration doc.
- `MELUSINA_HOUSE_GN_START_HERE.md` manifest updated when any
  builder id/status changes.
- Catalog verifier (`verify_melusina_house_gn_catalog.py`) extended to
  cover the extracted monolith kits as they land.

---

## 4. Order of execution (dependency-honest)

```text
G1 (mh6 fix → main)          ← everything depends on the fixed shell
C1 identity proof            ← needs G1 on both machines
C2 city cell rewire
C3 music shell fold
M0 monolith baseline         ← needs stable main; parallel-safe with C1
C4 monolith shell routing    ← needs C2 + M0
M3 roof authority            ← anytime after M0
C5 (old C5→C7) presets/docs/ledger
M4 kit extraction            ← continuous, opportunity-driven
M5 dead-weight triage        ← owner session only
G2–G5 git housekeeping       ← parallel with C/M steps
```

## 5. Verification contract (unchanged, now repo-codified)

- Headless Blender 5.2.1 `--background --python`; realize before counts;
  judge print lines; JSON/PNG evidence in `Saved/Audit/melusinashouse/`.
- Three-copy addon sync + md5 `3 <hash>` after every edit; then
  `sync_workstation.ps1` + installer per the two-workstation contract.
- Narrow git promotion: named files, compared to main, relevant test run,
  discovery doc updated. Branch = discovery surface, not SSOT.
- Prose is not a ledger row: every gate gets a dated PASS line in
  `melusinahouse_v7_plan.md` §Ledger and this file's §6.

## 6. Ledger

| Gate | Status | Evidence |
|---|---|---|
| G1 mh6 fix promoted to main | OPEN | — |
| C1 shell identity proof | OPEN | — |
| C2 city cell rewire | OPEN | — |
| C3 music shell fold | OPEN | — |
| M0 monolith dispatch baseline | OPEN | — |
| C4 monolith shell routing | OPEN | — |
| M3 roof authority declared | OPEN | — |
| C6/C7 parity grep + docs | OPEN | — |
| mh6 shell defects fixed | **DONE 2026-09-04** | v0_final_verify.log PASS; P: 3f1d4460 |
