# Emerging-Toolchain Implementable Rows — Implementation 2026-08-31

**Grounding:** `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md` integration matrix.
**Task:** which documented research of the emerging technologies can we try implementing?

---

## 1. The honest split: implementable vs external

| Row | Can we build it natively? | Why |
|---|---|---|
| **Unreal MCP** | ✅ **YES — VERY HIGH PRIORITY** | We already have `Plugins/UnrealMCP` + `Monolith`; the research names the exact safe-tool surface to implement |
| **UE Procedural Vegetation / PCG** | ✅ **YES** | `PCGExtendedToolkit` present; UE-native PCG growth (`PlaceSpeedTreeBiomeTest`) |
| **UE Mesh Terrain** | ✅ **YES** | UE 5.8-native mesh terrain; isolated test-map experiment |
| **Neural shaders/materials** | ✅ **YES (scaffold)** | `NNERuntimeORT` already a plugin; material-side neural inference needs an `.onnx` model — interface implementable, model TBD |
| Houdini / Copernicus / Gaea | ✅ already present | HoudiniEngine, Copernicus tools, GaeaUnrealTools already integrated |
| IlluGen / LiquiGen / EmberGen | ❌ external | JangaFX commercial tools, not vendorable |
| Cascadeur / Toolbag / World Creator / SpeedTree-modeler | ❌ external | Commercial authoring tools |
| RTX Kit | ❌ external | NVIDIA NvRTX commercial |
| Procedura | ❌ external | Commercial agentic modeling |
| Magpie | ⚠️ seam only | research-only; integrated as read-only seam (see DASH_MAGPIE_NATIVE_INTEGRATION) |

**Of the ~14 R&D rows, the genuinely buildable ones in UE 5.8 are: Unreal MCP (VHP), UE Procedural Vegetation/PCG (C-R&D), UE Mesh Terrain (A-R&D), Neural materials (Watch, scaffold).** The rest are commercial/external and cannot be natively implemented without purchase/license.

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