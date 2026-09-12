# Melusina Loom — Batch 05 (2026-09-02 09:32–10:05 EDT)

**Repo:** `C:/EnvironmentPortfolio/BS_GodFile` · UE5.8 · main ahead 378 / behind 359 (divergent remote — see Push)
**Editor MCP:** live on `:9316` (PID 50612) · **Working tree:** clean after 4 triaged commits

## Learn (hour craft)
- **Emerging tech (WATCH): NVIDIA RTX Kit / NvRTX.** Neuronal materials + neural texture compression
  require a *material* onnx — the present onnx (`Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8`) is
  embedding-only. Still on the owner-task gate (§3 of Master Index); not promoted this batch.
- **Reddit/forums thread — WPO-on-instanced performance discipline.** Key learning, directly applied to
  `MF_FabricMountainWPO` on `HISM_Faraway_FabricRidge`:
  - WPO driven by an MPC scalar is ultra cheap; "animating" thousands of HISM instances is far more expensive
    than animating one material parameter that all of them read.
  - Merge + minimize the instances that actually carry WPO; keep those meshes geometrically simple.
  - Drive WPO from a UV/MPC channel, not per-vertex logic; multiply the WPO output by a cull-distance mask.
  - Pitfall: "Update Instance Transform" rotation is a known Unreal 5.0+ break for WPO vertex anim on
    Instanced Static Meshes (transform material function needed Instance/Particle→World space support).
  - VAT (vertex-animation textures) + ISM/HISM is the performant path for large moving/bent crowds.

## Build (3 subagent lanes — height-aware, no new Landscape, instances-only, single MPC writer)
| Lane | Result | Evidence |
|---|---|---|
| **Brass + Sea Above schema validation** | **PASS** (brass_pass, sea_above_pass) | trumpet stacked 9 mods / tuba 11 mods, orders 0..N, all 7/8 types in `brass_modifiers.py` + framework doc; Sea Above spec 16 instances = 16 placements, CanonicalLandscape raycast-destination-only contract upheld, owning PCG graph referenced |
| **World Field Bus PIE gate** | **UNBLOCKED** (single_writer_pass, aliases_present, chladni_present) | `TickPresentation` (AudioReactivePresentation.cpp:307–326) sole writer of audio namespace (Bass/Mid/Treble/Beat* + BassIntensity/MidIntensity/BeatTracker aliases); Cymatics + CymaticsWriter both read-only on the palette MPC; Chladni `cos(nπu)cos(mπv)−cos(mπu)cos(nπv)` confirmed (lines 76–81); probe 5/5 PASS → **Build + PIE next window** |
| **VDM real cook + Gaea readiness** | A/B/C EXR cook **REAL** (lane script failed, evidence verified independently) | 3 valid 32f OpenEXR (magic `76 2f 31 01`): A 7.88MB / B 6.92MB / C 5.51MB + .npy/.png, `vdm_qa_2026-09-02.json` nonblank+mask_valid+exr_roundtrip PASS all; Gaea **ready**: 4 WP terrain levels × 3 locked frames = **12 frames** |

## Commits (isolated triaged batches, `--no-verify` not needed — pre-commit hook passed on all)
1. `7ef2eb1f` **brass(presets)**: trumpet aurora_oxide + tuba deep_sea_bell GMM presets
2. `307a5570` **cymatic(audit)**: refresh copernicus cymatic manifest
3. `cee1944e` **faraway(scaffold)**: Sea Above meshed lane height-aware placements spec (16 inst)
4. `09f1a5b2` **audit(state)**: loom batch 05 — brass/sea-above PASS, WFB PIE gate unblocked, VDM EXR cook + Gaea ready

## Push
`git push --dry-run origin main` → **REJECTED non-fast-forward** (local behind 359 commits of remote work).
Working tree clean; **no force-push issued** — remote reconciliation is an owner call (per project rule).

## Notes / next
- **VDM lane script pitfall (recorded):** in a hython `attribcreate` the attribute-name parm is `name1` (not `name`),
  and its type/`class` parm was not settable via `.set()` in the scratch driver. Baker script itself is fine; scratch
  driver was the failure. KleinVeil still lacks a 32f EXR (only .npy/.png) — candidate next cook.
- **Brass spec path discrepancy (non-blocking):** validation spec named `Content/Python/gmm/geometry/modifiers/`
  but the real modifier source is `Content/Python/gmm/geometry/brass_modifiers.py`. Presets are clean.
- Editor live → next loom window can run **WFB Build+PIE** and the **Gaea 12-frame capture** (MRQ/CinematicCamera rig precedent `build_faraway_mother_capture_rig.py`).
- Evidence files: `Saved/Audit/loom_batch05_{brass_seaabove_validation,wfb_pie_gate,vdm_cook_gaea}.json`.