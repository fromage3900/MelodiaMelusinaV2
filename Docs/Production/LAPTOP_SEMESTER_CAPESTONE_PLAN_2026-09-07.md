# Laptop + Blender Longterm Plan — Humber Fall 2026 Semester & Capstone

**Date:** 2026-09-07
**Machine:** ASUS Nitro laptop (P:\MelodiaMelusinaV2-Laptop), Blender 5.2.1 LTS, GTX 1050 Ti 4GB
**Authority:** GIT PIPELINE LAW — origin/main is canonical (desktop-maintained). Laptop = Blender/asset-prep + mobile hub. Long-lived laptop line = collab/laptop/longterm (additive). No branch/commit/merge/push without explicit owner approval per operation.
**Read with:** Docs/Production/HUMBER_LAB_PRIMARY_WORKSTATION_2026.md, Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md, Docs/Semester/FALL_2026_ACADEMIC_MATRIX.md, Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md

---

## 0. Verified state (2026-09-07)

| Surface | State |
|---|---|
| P: main | 025ae175 = origin/main, 0/0, clean ff of 21 desktop commits (CI workstation validation, sync fixes, Humber docs) |
| collab/laptop/longterm | 0/0 with origin, 825fb91c |
| C: repo checkout | fast-forwarded to 025ae175 (its branch tip was an ancestor — non-destructive) |
| P:↔C: surreal_arch trees | 152 files each, content-identical (16 files differ EOL-only), monolith byte-identical |
| P: addon headless census | import OK, 466 GROUP_BUILDERS, all 53 P2 family-kit ids present |
| LIVE AppData addon | **OUT OF DATE** — 15 missing (P2 kits never installed live) + 4 stale (core, __init__, melodia_house, presets). GUI currently runs pre-P2 code |
| sdf_kit_workshop.blend | on disk, gates pass headless: SDF_WallPanel 5440v/5438p, Dentil_Run 96v/72p; Repeat_Scaffold 0v headless (known Repeat-zone headless limitation — GUI-evaluated) |
| LFS | 5217/5243 hydrated; 26 missing are all _QuarantineAssets_20260809 + one old portfolio blend — not pipeline-relevant |
| Verify tooling gap | deploy/blender_smoke_queue.json references 6 scripts (_health_check_gn_builders.py, _health_check_full.py, _mcp_verify_overhaul.py, _mcp_verify_os.py, _preset_audit_job.py, _site_publish_dry_job.py) that exist in NO tree — verify_melodia_studio.ps1 will fail |

**Workshop review conclusion:** the SDF experiments already graduated. melodia_house.py (converged addon, on origin/main) uses MeshToSDFGrid → SDFGridBoolean → SDFGridFillet → SDFGridOffset for the room shell and a RepeatInput zone internally. The workshop blend is the provenance record, not pending work. What remains un-graduated: the two reusable *kit-level* patterns (parameterized dentil/moulding run; fillet-boolean wall panel as a standalone detail kit) are not registered MEL_* builders yet.

---

## S0 — Make Melodia Studio a working ecosystem (BLOCKING, do first)

The imperative. Nothing else matters while the GUI runs stale addon code.

1. Close Blender (PID holding AppData modules; installer refuses while open).
2. `powershell -File deploy\install_melodia_studio.ps1` — byte-verifies + stamps live addon from P: checkout @ HEAD.
3. `deploy\install_melodia_studio.ps1 -CheckOnly` → must report all-match + provenance stamp.
4. Headless register + census against the LIVE install (not just sys.path repo copy): confirm 466 builders, panel categories present.
5. GUI smoke: open Blender, N-panel → Melodia Studio catalog, spawn one builder per family kit (zen, scifi, filigree, materials, walls), screenshot-verify.
6. Fix or trim the smoke-queue gap: author the 6 missing verify scripts OR trim blender_smoke_queue.json to what exists, so `verify_melodia_studio.ps1` is runnable. (Needs owner approval to commit the fix to main-side; can land via collab/laptop/longterm PR.)

**Gate S0:** -CheckOnly clean + GUI spawn smoke + verify runner exits 0.

## S1 — Semester operating rhythm (laptop role)

Per HUMBER_LAB_PRIMARY_WORKSTATION_2026.md the topology is: Humber lab = primary interactive, home PC = render/bake worker, **laptop = auxiliary: docs, Blender batches, Rider, validation, spare render chunks**. This plan makes the laptop the *asset-prep hub* within that role — Melodia Studio builds happen here, get promoted, and lab/home machines consume them.

Session open ritual (every laptop work session, ~2 min):
```
deploy\sync_workstation.ps1                      # Check mode: git+LFS state report
deploy\install_melodia_studio.ps1 -CheckOnly     # live addon provenance
```
If either is red, fix before authoring. No authoring against stale state.

Session close ritual:
- Addon edits: three-copy sync per convergence skill (P: → C: → AppData), md5 3-hash.
- Work commits: ONLY on collab/laptop/longterm, ONLY with owner approval per push.
- Binary scene files stay in Saved/ (gitignored) until a promotion decision.

Render/bake work: use `deploy\render_worker.ps1 -Mode Blender` for frame-range chunks assigned by the home-PC job manifest (frame-range split rule in the Humber doc §4). Laptop takes the small chunks — 4GB VRAM, EEVEE lane for iteration; Cycles finals stay home/desktop.

Lab machine: `deploy\humber_lab_bootstrap.ps1 -Mode Prepare` before lab sessions; HumberSemester LFS profile only; no persistent jobs after the session.

## S2 — Asset-prep pipeline through Melodia Studio (the ecosystem deliverable)

Target: every game asset prep task routes through a registered builder, not ad-hoc blends.

| Stage | Where | Rule |
|---|---|---|
| Prototype | Saved/Blend/*_workshop.blend (gitignored) | headless gate: realize + poly count > 0 + report.txt in Saved/Audit/ |
| Graduate | deploy/surreal_arch/melodia_gn/<kit>.py via register_builder | category + param schema + harness PASS + three-copy sync |
| Verify | family gate script + registry census diff | zero regression on pre-existing builders |
| Promote | collab/laptop/longterm → PR → origin/main | owner approval per operation |
| Consume | FBX/glTF export → RawArt/ or direct UE import on desktop side | exports are outputs, never inputs |

Immediate S2 backlog (each = one gated graduation):
1. **SDF detail kit** — graduate the workshop's two proven patterns as registered builders: `MEL_sdf_wall_panel` (params: size, recess, voxel size, fillet iterations) and `MEL_moulding_run` (the Dentil_Run grid-instance pattern generalized: profile choice, count, spacing, path curve). Both gate-proven headless already; needs param schemas + category placement (`sdf_detail` or under existing walls/filigree families — check ADDON_AUTHORITY first, extend don't duplicate).
2. **Repeat-zone policy** — Repeat zones stay GUI-evaluated scaffolds in workshop files; registered builders use the grid-instance fallback so every builder is headless-verifiable. (Already the de-facto rule; codify in ADDON_AUTHORITY.)
3. Finish P2 remainder when it lands on main: greybox family (41) rides the shell convergence ladder C2/C3/C4 — desktop-side work; laptop consumes the merged result, never re-implements.

## S3 — Capstone lane

Capstone = the vertical slice itself, so the academic matrix rule applies: only map an assignment to Melodia when it genuinely satisfies the brief, and every mapping must produce two outputs (grade + portfolio/game asset).

- FALL_2026_ACADEMIC_MATRIX.md is the TEMPLATE — populate row-by-row as briefs are released (intake checklist §"Intake checklist" already defined: wording, weight, due, rubric, software, format, permission to reuse project work, smallest strong Melodia deliverable).
- Laptop capstone contributions: Melodia Studio asset builds (S2), technical-art breakdowns (the SDF workflow is already a case study — provenance blend + gate report + graduated builder), GN documentation.
- Heavy capstone compute (final renders, MRQ, bakes): home PC worker per the semester topology; laptop only takes assigned frame chunks.
- Portfolio artifacts land in Saved/RenderFarm/<job>/ then curated promotion — never raw commits.

## S4 — Automation hygiene (laptop cron fleet)

7 jobs already repointed to P: + collab/laptop/longterm (2026-09-06). Keep:
- morning digest + git brief + weekly asset catalog via telegram.
- bp-sweep stays parked (editor-only, desktop).
Add once S0 is green:
- nightly addon census job: headless registry count + live-install -CheckOnly into Saved/Audit/; alert on drift (count change without a matching commit, or provenance mismatch).

---

## Ledger

| Gate | Status | Evidence |
|---|---|---|
| S0 live install byte-clean + GUI smoke | OPEN — blocked on Blender close (owner) | — |
| S0 verify runner fixed (smoke queue) | OPEN | — |
| S1 session rituals adopted | OPEN | — |
| S2.1 SDF detail kit graduated | OPEN — patterns gate-proven, unregistered | Saved/Audit/sdf_kit_workshop/report.txt |
| S2.2 repeat-zone policy codified | OPEN | — |
| S3 matrix populated | WAITING FOR BRIEFS | — |
| S4 nightly census job | OPEN | — |
