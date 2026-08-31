# Melodia Emerging-Toolchain Master Index — 2026-08-31

**PURPOSE:** Single authoritative discovery SSOT for all emerging-toolchain / render / audio research.
Read this FIRST before proposing or building anything in these systems. It records, with exact paths:
what is **already present/implemented**, what is **scaffolded**, what is **research-only**, and what is an
**external tool** — so no agent re-derives, duplicates, or claims-absent what exists.

**Supercedes-as-SSOT:** `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md` (keep both; this one
extends it with on-disk verification + the subsystems built 2026-08-31).
**Evidence basis:** everything below was verified against `Source/`, `Plugins/`, `Content/`, and the
research corpus on 2026-08-31 (not assumed).

---

## 0. The non-negotiable rule

> **Before creating a new graph / subsystem / tool for ANY of these systems, check the "STATUS" column
> below and the cited path. If it says PRESENT or SCAFFOLDED, extend it — do not build a parallel copy.**
> "A new parallel implementation is a defect, not progress" (AGENTS.md convergence rule).

---

## 1. Already PRESENT on disk (verified) — do NOT rebuild

| System | Status | Path / evidence |
|---|---|---|
| **SpeedTree** | **PRESENT — Core plant authority** | `Content/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.uasset` · `Content/Python/reset_speedtree_wind_instances.py` |
| **Houdini 22 / Houdini Engine** | **PRESENT** | `Plugins/HoudiniEngine/` · Houdini 22.0.368 at `C:/Program Files/Side Effects Software/Houdini 22.0.368` |
| **Copernicus** (Houdini GPU texture/mask) | **PRESENT (implementation)** | `Tools/Houdini/copernicus/` (README, dress bake, petal variants, fabric sheen, terrain→nanite) |
| **Gaea** | **PRESENT** | `Plugins/GaeaUnrealTools/` |
| **PCG + toolkit** | **PRESENT** | `Plugins/PCGExtendedToolkit/` · UE PCG enabled |
| **Unreal MCP / Monolith** | **PRESENT** | `Plugins/UnrealMCP/` · `Plugins/Monolith/` (1330+ actions) |
| **NNERuntimeORT** | **PRESENT** | in `BS_GodFile.uproject` (enables neural inference) |
| **Audio-Reactive presentation (synesthesia Tiers 1–3)** | **PRESENT — full impl** | `Source/.../MelodiaAudioReactivePresentationSubsystem.h/.cpp` — writes `MPC_Melodia_Palette` + `NPC_Melodia_Palette` (BeatPulse/BeatPhase/BeatIntensity/…). **This is the single audio writer — never add a second.** |
| **Music clock** | **PRESENT** | `Source/.../MelodiaMusicClockSubsystem.h/.cpp` |
| **onnx model** | **PRESENT** | `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx` (34 MB, text-embedding for Claireon) + onnxruntime installed |
| **Claireon** | **PRESENT (isolated agent surface)** | `Plugins/Claireon/` vendored @ `ed0b457`; **never runs alongside Monolith on the main editor** (single-MCP-surface rule). Test lane: worktree `C:/EnvironmentPortfolio/Melodia_ClaireonTest` (branch `claireon-test`, port 57818). `Installed:false`, never built for UE 5.8 yet. Client-side probe `Tools/test_claireon_toolcalls.py` — qwen3-coder:30b scored **7/8** (2026-08-31), 100% surface adherence. UEBlueprintMCP must be disabled before any live Claireon editor run. See `Docs/CLAIREON_PREP_2026-08-20.md`. |

## 2. SCAFFOLDED by me 2026-08-31 (buildable, additive new files) — extend, don't duplicate

| System | Purpose | Source files | Build status |
|---|---|---|---|
| `UMelodiaCaptureRenderSubsystem` | offscreen SceneCapture HDR render pipeline (4-view, PPV gate) | `Source/.../MelodiaCaptureRenderSubsystem.h/.cpp` | needs closed-editor build |
| `UMelodiaDressingSubsystem` | Dash-capability native dressing/art-pass (hero props, debris, composition) | `Source/.../MelodiaDressingSubsystem.h/.cpp` | needs build |
| `UMelodiaVisualRepresentationSubsystem` | Magpie simulation↔visual seam (read-only) | `Source/.../MelodiaVisualRepresentationSubsystem.h/.cpp` | needs build |
| `UMelodiaVegetationGrowthSubsystem` | PCG growth supplementing PRESENT SpeedTree | `Source/.../MelodiaVegetationGrowthSubsystem.h/.cpp` | needs build |
| `UMelodiaCymaticsSubsystem` | audio→geometry Chladni pattern (READ-ONLY consumer of the existing MPC writer) | `Source/.../MelodiaCymaticsSubsystem.h/.cpp` | needs build |

Tools (runnable, committed): `Tools/mcp_tool_surface.py` (Unreal-MCP safe tool surface, dry-run default),
`Tools/test_dressing.py`, `Tools/test_visual_seam.py`, `Tools/test_cymatics.py`, `Tools/test_dash_capture.py`,
`Tools/branch_health.py`. Probes → `Saved/Audit/{dressing,visual_seam,cymatics,dash_probe}_*.json`.

## 3. Research-only / WATCH — do NOT promote without an explicit task

| System | Status | Where |
|---|---|---|
| **Magpie** (generative realtime renderer) | WATCH — seam scaffolded only, NO renderer | `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md` |
| **Neural shaders / materials** | WATCH — needs a *material* onnx (present onnx is embedding-only) | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §neural |
| **Procedura** | RESEARCH ONLY | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Procedura |
| **RTX Kit / NvRTX** | WATCH — do not fork shipping renderer | `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03` §14 |

## 4. External commercial tools — NOT buildable natively, not vendored

IlluGen, LiquiGen, EmberGen (JangaFX) · Cascadeur · Marmoset Toolbag · World Creator · Rokoko Vision ·
MetaTailor · InstaMAT · Material Maker · ArmorPaint · Style3D · Autodesk Flow Studio · Notch · D5/Octane/V-Ray ·
Polygonflow **Dash** (dressing plugin — absent; native `UMelodiaDressingSubsystem` is the buildable fallback).
Full catalog + Melodia roles: `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md` (24 tools),
`EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md`.

## 5. Two architecture contracts to formalize (do NOT build a giant framework)

**5a. SpeedTree semantic bridge** — 9 world-description fields Houdini/PCG/material systems use to decide
how SpeedTree assets appear (SpeedTree does NOT ingest these directly):
`melodia_moisture, melodia_slope, melodia_wind_exposure, melodia_soil_depth, melodia_monolith_proximity,
melodia_molt_age, melodia_filter_flow, melodia_tension, melodia_ecological_density`.
Source: `TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md` §SpeedTree.

**5b. Melodia World Field Bus** — a *minimum* shared spatial-field contract so plugins stop inventing their
own world truth: `WorldField.FilterFlow / Tension / Moisture / Contact / Residue / Reaction /
AnchorStability / Resonance`. Representations by scale (MPC / RVTs / Niagara grids / Houdini fields / PCG
metadata). **Do not build a generalized field framework tomorrow** — discover the minimum contract via R&D.
Source: `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md` §A.

## 6. Houdini execution plan (executable, reviewed)

`Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md` — Mara + P0–P3. HDA families:
`HDA_ENV_TerrainStamp, HDA_ENV_PathCorridor, HDA_ENV_ScatterMaskBuilder, HDA_ENV_HeroRockFamily,
HDA_ENV_LOD_Collision_Batch, HDA_CH_CurlCluster`. **Primary rule: Houdini manufactures reusable geometry/
masks/LODs/scatter; gameplay authority + final composition stay in Unreal. Bake — never leave final playable
scenes dependent on live HDA cooking.** Companion: `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`.

## 7. Cymatics / audio-visual synesthesia (implemented thread)

`Docs/MELODIA_AUDIO_VISUAL_SYNESTHESIA_LAYER_2026-08-28.md` — 5-tier (Music Clock → MPC → MetaSounds/PPV/Niagara).
Tiers 1–3 implemented (`MelodiaAudioReactivePresentationSubsystem`); audio→geometry (Test E) scaffolded as
`UMelodiaCymaticsSubsystem` (Chladni pattern, read-only). The only "Sakura" here is `NS_Melodia_PetalLoop`
(audible-reactive petals) — a **legitimate** melodic use, distinct from the banned art direction.

## 8. Integration spike plan — 16 tests, tiered

`Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`: Tier A (Copernicus, IlluGen, Cascadeur,
Unreal MCP, Mesh Terrain+PCG), Tier B (Dash, LiquiGen, EmberGen, Toolbag, Gaea, World Creator, PVE),
Tier C/D (RTX, neural, Procedura, Magpie). **Every test uses the required-result template; ADOPT/PARK/REJECT gates.**

## 9. Anti-duplication checklist (read before proposing)

1. Is the system in §1 (PRESENT)? Extend it, don't rebuild. Especially: audio writer (single), music clock.
2. Is it in §2 (SCAFFOLDED)? Finish it before starting a parallel copy.
3. Is it in §3 (WATCH)? Requires an explicit owner task to promote.
4. Is it §4 (external)? You cannot build it natively; say so, don't fake it.
5. Is the field-name you want already in §5 (World Field Bus / SpeedTree bridge)? Reuse the contract.
6. Editor: one instance, one :9316. Batch saves `unattended:true`. No `Content/_PROJECT/` writes.
7. Evidence: offline probe + live PIE + ledger row. Prose is not a row.