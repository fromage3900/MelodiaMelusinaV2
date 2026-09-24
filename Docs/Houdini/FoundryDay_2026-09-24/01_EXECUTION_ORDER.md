# 01 — Execution order, lanes, stop conditions, acceptance

| | |
|---|---|
| **Purpose** | The one ordering of the day. Gates are sequential on the interactive lane; heavy bakes run beside them. |
| **Authority** | Owner (Brennan) decides taste, silhouettes, visual acceptance and canonical selection. Agents (Space Bunny via Hermes) do debugging, sweeps, manifests, validation, logs and docs. |
| **Status** | STAGED. |

## Gate order

| Gate | Name | Doc | Lane | Leave-gate evidence |
|---|---|---|---|---|
| 0 | Repo + environment verification | START_HERE §3 | interactive | `probe_2026-09-24.json` PASS, `hserver -l` licence line, tests green, plugin/Houdini build match recorded |
| 1 | Custom HDA → UE cook/bake/save/reload | `02` | interactive | `hda_engine_smoke_arpeggio_stair/bake_manifest.json` with `ue.saved` + `ue.reloaded_equal` true |
| 2 | Regenerate + promote Crystal Cathedral | `03` | interactive | regen counts == tracked manifest; `HDA_Melodia_CrystalCathedral_1.0.hda` cooks identically |
| 3 | One FieldAtlas tile | `04` | interactive | one tile's channel EXRs + manifest, `verify` PASS |
| 4 | One Sea Above tile → UE | `05` | interactive | tile texture imported, read by one existing consumer, save/reload equal |
| 5 | Launch tiled Sea Above bake | `05` | **heavy** | job started from `plan` output; per-tile manifests land |
| 6 | Glitter / Deposition proof | `06` | interactive (while 5 runs) | rest mesh + active points + density field + manifest; UE Niagara read if time |
| 7 | FlowVolume | `07` | interactive → heavy | vector field + manifest |
| 8 | Volumetric Ecology | `08` | heavy | channel volumes + manifest |
| 9 | Copernicus field integration | `09` | interactive | 9-map set driven by FieldAtlas channels, `verify_tex_contract.py` PASS |
| 10 | PDG / BakeFarm consolidation | `10` | interactive | `TOP_Foundry_BakeFarm` regenerates ≥ 1 recipe from `bake_farm_first_workload.v1.json` |
| 11 | Faraway Mother / Vellum | `11` | heavy | **only if Gates 1–4 are green** |

**Never skip ahead of a red P0 gate.** Gate 1 and 2 are independent. If Gate 1 is blocked by UE (B2), Gate 2's Houdini half and Gates 3/6 can still produce offline outputs. Label them SOURCE, not LIVE.

## Two lanes

| Heavy compute lane (launch, then leave) | Interactive lane (human + agent attention) |
|---|---|
| Sea Above tiled erosion / FieldAtlas (Gate 5) | HDA logic, parameter interfaces |
| VDB volumes (Gates 7–8) | Cathedral promotion + art-direction passes |
| 4K texture bakes (Gate 9) | manifests, field contracts, recipes |
| Vellum textile variants (Gate 11) | UE integration (one editor, one writer) |
| FLIP / ocean intelligence (Gate 8b) | tests, docs, evidence |
| PDG wedges (Gate 10) | |

Rule: **never ask Brennan to watch a cook.** When a heavy job is launched, the next interactive gate starts. Heavy jobs are launched only from a validated recipe + `plan` output, write to `Saved/HoudiniFoundry/`, and log to `Saved/Audit/houdini_foundry/<recipe_id>/cook.log`.

## P0 stop conditions (HOLD, report, do not work around)

1. `probe` is not PASS, or hython hangs (licence server) → stop Houdini work and fix the licence first.
2. The college Houdini build ≠ the Houdini Engine plugin build (22.0.368 for UE 5.8) → do **not** hand-edit `.uplugin` or copy random binaries. Install the SideFX plugin that matches the college build **outside the repo**, record both versions, and keep `Plugins/HoudiniEngine/` in git untouched.
3. UE 5.8 or the project cannot open at college → Gate 1 UE half moves to the owner PC. Continue with offline gates, labelled SOURCE.
4. Any gate would require editing a never-touch file (`.gitignore`, `.gitattributes`, `Config/Default*.ini`, `MF_MeshBlend_*`, `deploy/run_verify.ps1`) → ask the owner.
5. Any `deploy/*LOOP_STOP*` file exists → no writes under `/Game/EnvSandbox/` (this affects cathedral re-import; write new assets under `/Game/Melodia/HoudiniFoundry/` instead).
6. A second writer would appear: a second editor, a second Monolith, an MPC write, a PCG graph rewrite, or Houdini Engine left as a live overlay → stop.
7. Determinism fails: the same recipe gives different hashes → stop that product. A beautiful non-reproducible output is a one-off, not content.
8. Anything touches the owner-authored Sea Above Landscape or `00_CANON/*` transforms → stop.

## Fatigue-safe mode

Brennan arrives short on sleep. The plan must not depend on him debugging.

- **Brennan owns:** art direction, silhouettes, taste, visual acceptance, final canonical selection (e.g. which cathedral variant, which glitter look).
- **Agents own:** Hython/API troubleshooting, parm-name drift (`setp` candidate lists), manifests, parameter sweeps, validation, logs, docs.
- **Ask-first:** anything destructive, architecture-changing or ambiguous (asset deletes, map choice for the HDA smoke, LFS decisions, new UE folders under `EnvSandbox`).
- **Degradation switch:** when judgement visibly slips (repeated re-dos, "fine, whatever"), stop authoring and switch the mission to **bake → export → validate → hash → manifest → document** on already-approved recipes.
- Offer choices as 2–4 rendered options (contact sheet), not open questions.

## Acceptance tiers

| Tier | Requires |
|---|---|
| **Minimum** | repo synced to this branch · Hython healthy (probe PASS) · custom HDA cook → bake → save → reload live proof (Gate 1) · Crystal Cathedral regenerates with counts matching the tracked manifest |
| **Strong** | Minimum + `HDA_Melodia_CrystalCathedral` · one FieldAtlas tile · one Sea Above tile round-trip into UE · PDG skeleton (`TOP_Foundry_BakeFarm` exists and runs one recipe) |
| **Exceptional** | Strong + tiled Sea Above bake · Glitter deposition proof · Houdini-authored distribution driving an existing Niagara system · FlowVolume · musical cathedral geometry (song → facets) |
| **Stretch** | Exceptional + PDG regenerates several products from one bake request · Copernicus consumes FieldAtlas · volumetric ecology · textile variants |

A tier counts only with evidence files in `Saved/Audit/houdini_foundry/` and a `verify` PASS. "The log said it worked" is not evidence (Houdini lane law #4).
