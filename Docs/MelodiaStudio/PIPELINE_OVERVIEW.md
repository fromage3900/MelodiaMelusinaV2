# ♬ Melodia Studio — 3D Asset Pipeline Overview

**Date:** 2026-09-06 (written on `pipeline/melodia-studio-3d`, verified against `origin/main` the same evening)
**One page, whole lane.** If you read nothing else before touching Blender here, read this.
**Discovery tokens:** `Melodia Studio`, `melodia_studio`, `MEL_`, `surreal_arch`, `Melusina House`, `V7`, `RawArt`.

## Machine truth

Two workstations, one authority: **this git repo** (`fromage3900/MelodiaMelusinaV2`).

| Copy | Path | Role |
|---|---|---|
| Repo (authority) | `Tools/BlenderAddons/melodia_studio/` + `deploy/surreal_arch/` | source of truth, versioned, PR-reviewed |
| AppData (live) | `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\` | what the running Blender loads |

- After every addon edit: sync repo → AppData and md5-verify. AppData sync only while
  `blender.exe` is not running (SHIP CHECKLIST rule, still true).
- `P:` was an old drive letter on the laptop. It is **gone**; ignore `P:/...` paths in
  archived 09-03/09-04 docs — those files stay verbatim as history, this table is the map.
- Cross-machine handoff of `.blend` sources = Git LFS + locks. One workstation edits a
  locked file at a time:
  `git lfs lock <path>` → edit → commit → push → unlock (only after the push is visible).
- Blender target: **5.2.1 LTS**, headless-capable; every gate below runs
  `blender --background --python <script>` with no UI.

## Intake rail

One path from idea to shipped asset. No stage script builds mesh or node trees inline —
if a feature is missing, it becomes a registered builder first.

```
idea
  └─ grep the registry FIRST (both trees + GROUP_BUILDERS + monolith props)
      └─ builder lands in melodia_studio / melodia_gn module, registered MEL_* id
          └─ headless verify: python Tools/verify_full_registry.py
              (baseline: Tools/registry_baseline.json — diffs are regressions)
              └─ stage script nests the builder (deploy/surreal_arch/, integration.py wires)
                  └─ house scene: RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend
                      (build script: Tools/house_v7_base_build.py — reproducible headless)
                      └─ realize instances, then count verts; judge by print lines
                          └─ FBX/USD export (per-cell realize + materials)
                              └─ UE import + lookdev pass (Docs/LookDev/, PPV rules)
```

## Where everything lives

```
Tools/BlenderAddons/melodia_studio/     addon package (panel, chrome, batch, tests)
deploy/surreal_arch/                    monolith-adjacent wiring: bootstrap, melodia_gn/
                                        builders, integration.py (overhaul layer — 13 importers)
deploy/surreal_architecture_gen.py      the 38k-line monolith; register() calls integration
RawArt/MelusinasHouse/                  LFS-locked .blend handoff surface
  ├─ MelusinasHouse_V7_Base.blend       canonical editable house source
  └─ Intermediates/                     recovered greybox→v6 archaeology (see its README)
Tools/verify_full_registry.py           per-builder headless harness
Tools/registry_baseline.json            403 package ids + 209 monolith ids — the regression gate
Saved/Audit/melusinashouse/             evidence drops (renders, verify JSON/logs)
Docs/MelodiaStudio/                     this lane's living docs (plan, roadmap, overview)
Docs/Music/                             music-kit inventories (Splice samples)
```

**LFS pointer trap:** every `.blend` here is LFS-tracked. A fresh checkout without
`git lfs pull` shows 3-line pointer files that look like corruption. They aren't.
Lockable: `*.blend`, `.fbx`, `.uasset`, `.umap` (.gitattributes:25–34).

## Open ledger (decisions owned, not made yet)

| Item | State | Where it's written |
|---|---|---|
| V0 cell rewiring (nest `MEL_mh6_room_shell` in `MEL_city_house_cell` via C1 adapter) | shell DEFECTS FIXED + RE-PROVEN 2026-09-06 (`Tools/house_v0_shell_proof.py`: guard holds 87,856 v, openings survive) — strict bbox-identity gate awaits owner tolerance call (SDF quantization +0.085 Z) | `MELUSINA_HOUSE_V7_PLAN.md` Ledger |
| 16 dead builders (mother_v3 ×8, mother_tapestry_wall, p4_ ×7) — registered nowhere, never imported | OPEN — quarantine behind harness | V7 plan V5 phases table |
| 8 passthrough stubs (same files) — geometry-less trees, two conflicting signatures | OPEN — flag `role='research'` | V7 plan V5 phases table |
| Rebrand: (1) Melodia Studio umbrella [recommended] / (2) Surreal Studio / (3) Melodia Forge | **OWNER DECISION** — no MEL_* renames in v1 either way | V7 plan V5 |
| Grandmaster lane (14 family kits `0b50b42d` + Melusina's Study blend `027dce9b`) | MERGED 2026-09-06 into `pipeline/melodia-studio-3d` (`7135bde3`); registry reconciled at 466 ids, zero regressions (`e5e0c28f`) — PR to main pending | `Docs/MelodiaStudio/PIPELINE_OVERVIEW.md` |
| Study dressing: blend committed as WIP shell (interior unfurnished, camera unaimed) | OWNER fetching decorated state from laptop 2026-09-06 evening | this row |

## Standing rituals

1. **Discovery before creation** — grep registry + GROUP_BUILDERS + monolith props
   before writing any new builder. (268 package builders, 209 monolith ids exist; the
   V5 study found six parallel-authority clusters — do not add a seventh.)
2. **Prose is not a ledger row** — every gate flips to `PASS <date>` only with an
   evidence path under `Saved/Audit/`.
3. **Realize, then measure** — headless verify with realize-instances before any vert
   count claim.
4. **integration.py is load-bearing** — main lost it once in merge `a72e2eee` and the
   overhaul layer died silently (the monolith's `except Exception` swallowed it). If you
   touch the deploy wiring, run the import smoke, don't trust the green.
5. **Commit style** — `type(scope): what + why`, evidence in the body.

## Ledger

| Gate | Status | Evidence |
|---|---|---|
| Pipeline overview written | PASS 2026-09-06 | this file; every path above confirmed via `git ls-files` on `pipeline/melodia-studio-3d` |
| integration.py restored | PASS 2026-09-06 | blob `b7fe7f10` at `deploy/surreal_arch/integration.py`; 908 lines, ast parse clean; carried by `5862f539` |
| V0 re-proof run | PARTIAL 2026-09-06 — guard/openings PASS, strict identity awaits tolerance call | `Tools/house_v0_shell_proof.py`; `Saved/Audit/melusinashouse/v0_proof_last.json` |
| Registry regression gate | BASELINE 466/209 ids refreshed post-merge — 352 pkg ok, 208/209 mono, 0 regressions | `Tools/registry_baseline.json` (9 known errors unchanged) |
