# EDITOR_SESSION_HANDOFF — 2026-09-02

> Orchestration manifest for the next **live-editor** run on BS_GodFile.
> Goal: resolve all editor-gated daemon work in ONE session, in dependency order.
> Editor reachability at authoring: **LIVE** (UnrealEditor.exe PID 50612, Monolith port 9316 listening).
> Compiled from `Saved/Audit/overnight_queue_2026-08-30.json` (blocked_pending_editor items) + daemon specs.
> Guardrails: no dead-gate certification without ledger; every delete is referencer-confirmed first.

---

## Session Order (dependency-ranked)

### Phase 1 — Safe-Delete Triage (referencer-map, read-only) ⛔ do this FIRST

Nothing may be deleted until referencer maps clear it. Run each against **all** `.umap` files under `Content/`.

| Task | Scope | Entry spec | Gate to reach |
|---|---|---|---|
| **1a. Greybox_Kit triage** | 158 `.uasset` in `Content/EnvSandbox/Greybox_Kit/` (untracked, unlabelled) | `Saved/Audit/greybox_kit_safe_delete_triage_spec_2026-09-10.json` | Classify each SAFE_DELETE / KEEP_REFERENCED / KEEP_LABELED |
| **1b. Template Loose-MI dedup** | 357 files in `Content/EnvSandbox/Meshes/Environment/_Loose/` (untracked) | `Saved/Audit/template_loose_mis_dedup_triage_spec_2026-09-10.json` | Dedupe against existing `MI_*.uasset` + MS compliance |
| **1c. VFX Candidates promotion** | 37 `.uasset` in `Content/EnvSandbox/VFX/Candidates/` (untracked) | `Saved/Audit/vfx_candidates_promotion_triage_spec_2026-09-10.json` | PROMOTE / ARCHIVE / DELETE per asset |
| **1d. VFX stub referencer closeout** | 6 stubs under `Content/EnvSandbox/VFX/` | `Saved/Audit/mi_vfx_stub_referencer_gate_2026-09-01.json` | `listdependencies` each, then Kenney-safe-delete |

**1d exact `listdependencies` calls** (from `mi_vfx_stub_referencer_gate_2026-09-01.json`):
```
listdependencies /Game/EnvSandbox/VFX/Curves/C_Audio_bass_td_curve
listdependencies /Game/EnvSandbox/VFX/EffectTypes/ENV_SakuraVFX
listdependencies /Game/EnvSandbox/VFX/Materials/Functions/MF_Niagara_SDF_Sample
listdependencies /Game/EnvSandbox/VFX/MPC/MPC_Magical
listdependencies /Game/EnvSandbox/VFX/MPC/MPC_SakuraDream
listdependencies /Game/EnvSandbox/VFX/MPC/NPC_SakuraDream
```
Record each result in the `echo_run` ledger record `vfx_stub_referencer_gate` before any deletion.

### Phase 2 — Materialize Reef per-mesh MIs (blue variant)

- 20 per-mesh MIs missing for `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/` clutter/coral/kelp/rockchunk.
- Entry spec: `Saved/Audit/mi_seaabove_reef_clutter_shadowdream_blue_spec_2026-09-12.json`
- Convention: `MI_SeaAbove_Reef_<Stem>_ShadowDreamBlue`, parent `M_Master_Toon_Unified`, tint `#8AA0D6` strength `0.55`.
- Target dir `Content/EnvSandbox/Materials/Instances/Architecture/Reef/` — **create dir first** (does not exist).
- Distinct from `MI_SeaAbove_Clutter_*` texture-route suite (no name collision).

### Phase 3 — Materialize MoonlitMoss MI (green, NOT blue/pink)

- No `MI_Copernicus_MoonlitMoss.uasset` yet; 9 PBR maps baked & verified.
- Entry spec: `Saved/Audit/mi_copernicus_moonlitmoss_spec_2026-09-12.json`
- Asset: `/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_MoonlitMoss`, parent `M_Master_Toon_Unified`.
- MoonlitMoss is **bioluminescent green** → ShadowDream blue/pink rider does **not** apply.

### Phase 4 — Referencer-confirm + git rm pre-bevel backups

- 9 `*.obj.pre_bevel_backup` residues in Reef meshes (all TRACKED, committed `6a3ae271`).
- Entry spec: `Saved/Audit/sea_above_reef_pre_bevel_backup_safe_delete_spec_2026-09-12.json`
- HAS REFERENCER CHECK, then `git rm` + one consolidated `chore(sea-above)` cleanup commit.
- Files: `SM_Clutter_Starfish`, `SM_Coral_{Fan,Table,TubeSponges}`, `SM_Kelp_{Cluster,Mid,Tall}`, `SM_RockChunk_{L,M}` `.obj.pre_bevel_backup`.

### Phase 5 — Golden-run P0 preflight → live PIE

- Preflight returned a clean-pass audit (per queue summary); awaiting **live PIE** execution.
- Cross-ref: `Saved/Audit/cymatics_build_preflight_2026-09-01.json` (editor PID 9356 at authoring; current PID 50612).
- Must be ledger-recorded before any "P0 golden run PASS" certification.

---

## Acceptance summary table

| Task | Tool/MCP | Input dir | Acceptance = done when |
|---|---|---|---|
| 1a Greybox_Kit | referencer map | `EnvSandbox/Greybox_Kit` | every asset binned SAFE/kEEP_REF/kEEP_LABELED |
| 1b Loose MI dedup | referencer map + parent read | `Meshes/Environment/_Loose` | duplicates resolved, MS compliant |
| 1c VFX candidates | referencer map | `VFX/Candidates` | PROMOTE/ARCHIVE/DELETE decided per asset |
| 1d VFX stubs | `listdependencies` | `EnvSandbox/VFX` | 6 ledger records, clears then delete |
| 2 Reef MIs | MI materialize | Reef Meshes | 20 MIs created |
| 3 MoonlitMoss MI | MI materialize | Copernicus Instances | 1 MI created |
| 4 pre-bevel rm | referencer + `git rm` | Reef Meshes | 9 files committed-removed in 1 commit |
| 5 Golden run | Play-in-Editor | LV_SeaAbove_Prototype | P0 golden-run PASS in ledger |

---

## Notes / cross-refs

- These blocked items are EDITOR-side; the daemon cannot force them. Owned by user (live editor session).
- Do not merge these into any git commit from daemon — they involve `.uasset` writes + editor state.
- After Phase 1, re-run `git status --short` to confirm the EnvSandbox untracked counts drop.
- Non-ff push guard active (ahead/behind 359/368, push rejected) — local commits only until reconcile.