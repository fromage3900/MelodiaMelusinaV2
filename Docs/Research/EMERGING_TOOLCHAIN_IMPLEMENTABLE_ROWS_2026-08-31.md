# Emerging-Toolchain Implementable Rows — Implementation 2026-08-31

**Grounding:** `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md` integration matrix.
**Task:** which documented research of the emerging technologies can we try implementing?

---

## 1. The honest split: implementable vs external (CORRECTED 2026-08-31 late — verified on disk)

| Row | Can we build it natively? | Why |
|---|---|---|
| **SpeedTree** | ✅ **CORE — PRESENT, ESTABLISHED** | `M_SpeedTreeMaster.uasset` + `reset_speedtree_wind_instances.py` exist in Content. Production plant authority, present. |
| **Unreal MCP** | ✅ **YES — VERY HIGH PRIORITY** | We already have `Plugins/UnrealMCP` + `Monolith`; the research names the exact safe-tool surface to implement |
| **UE Procedural Vegetation / PCG** | ✅ **YES** | `PCGExtendedToolkit` present; UE-native PCG growth — but must use the PRESENT SpeedTree assets, not "supplement a missing system" |
| **Neural shaders/materials** | ✅ **YES — an .onnx model EXISTS on disk** | `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx` (34 MB) + onnxruntime installed. **Correction:** I previously claimed no model exists — wrong. (The present model is a text-embedding model for Claireon retrieval, not a material-shading network, so a *material* onnx is still a gap — but the claim "no onnx exists" was false.) |
| **Houdini 22 / Houdini Engine** | ✅ **YES — FULLY REVIEWED NOW** | `MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md` is executable: HDA families (`HDA_ENV_TerrainStamp`, `HDA_ENV_PathCorridor`, `HDA_ENV_ScatterMaskBuilder`, `HDA_ENV_HeroRockFamily`, `HDA_ENV_LOD_Collision_Batch`, `HDA_CH_CurlCluster`), Session Sync/Node Sync, bake-not-live-cook rule. **Correction:** I previously did not review the Houdini plans — now reviewed. |
| Copernicus / Gaea | ✅ present | Tools present |
| IlluGen / LiquiGen / EmberGen | ❌ external | JangaFX commercial tools, not vendorable |
| Cascadeur / Toolbag / World Creator | ❌ external | Commercial authoring tools |
| RTX Kit | ❌ external | NVIDIA NvRTX commercial |
| Procedura | ❌ external | Commercial agentic modeling |
| Magpie | ⚠️ seam only | research-only; integrated as read-only seam (see DASH_MAGPIE_NATIVE_INTEGRATION) |

**Corrections made:** SpeedTree is NOT external — it is present and Core. An .onnx model IS on disk (embedding model). The Houdini plans ARE executable and are now reviewed. My earlier matrix misclassified all three.

---

## 2. What I implemented this pass

### 2.1 Unreal-MCP tool surface — `Tools/mcp_tool_surface.py` (VERY HIGH PRIORITY row)

Implements the research's named safe-editor tool surface, sandbox-guarded:
`RunP0SmokeTest`, `RunPerformanceCapture`, `AuditDataLayers`,
`CreateRhythmReactiveMaterialInstance`, `PlaceSpeedTreeBiomeTest`,
`ValidateWaterAuthority`, `ValidateMaraSkeleton`, `BakeHoudiniRegion`, `BuildHLODForRegion`.

- Dry-run by default (`--dry`, no editor). `--live` only against Monolith `:9316` in a sandbox map (research hard guardrail).
- Proven runnable offline; ledger JSON written to `Saved/Audit/mcp_tool_surface_*.json`.

### 2.2 PCG vegetation growth — `UMelodiaVegetationGrowthSubsystem` (C-R&D row)

`PlaceSpeedTreeBiomeTest(RegionAnchor, BiomeFamily)`, `MutateSecondaryGrowth()`, `GraftBranch()`.
Sandbox-only, NOT a SpeedTree replacement (SSOT), PCG is the distribution authority. C++ scaffold, builds next closed-editor window.

### 2.3 (earlier) Magpie seam + Dash dressing — see `DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md`

---

## 3. Not attempted (honest)

- No Polygonflow Dash plugin install (commercial, absent) — native dressing subsystem built instead.
- No Magpie frame renderer (research-only, no impl) — read-only seam built instead.
- No neural `.onnx` model authored (needs a trained model); neural-material *interface* is the scaffold, model is a follow-up.
- No UE Mesh Terrain spike map yet — isolated test-map plan is queued (research guardrail: no chapter map migrates until it survives a production-like spike).

## 4. Guardrails held

Sandbox-only for R&D, no `Content/_PROJECT/` writes, no new material master, no parallel combat/water authority, dry-run default, one editor + Monolith :9316, batch saves `unattended:true`, spec precedes mutation.