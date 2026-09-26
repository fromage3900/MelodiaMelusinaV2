# Research Index — Melodia / BS_GodFile

> **Canonical toolchain research:** [`EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`](EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md) — **start here.**

This file is the fast-finding index for `Docs/Research`. The Emerging 3D Toolchain doc is the
single source of truth for tool adoption decisions (CORE / TEST NOW / OPTIONAL / WATCH / RESEARCH ONLY).

## Emerging 3D toolchain set (2026-08-30/31)

| Doc | What it is |
| --- | --- |
| **[EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md](EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md)** | **CANONICAL** — full tool catalog, integration matrix, super-pipeline, adoption rules |
| [TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md](TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md) | Benchmarks A–E, safety rules, day schedule, result template |
| [TOOLCHAIN_KICKOFF_2026-08-30_CASCADEUR_ILLUGEN_BLENDER_RHYTHM.md](TOOLCHAIN_KICKOFF_2026-08-30_CASCADEUR_ILLUGEN_BLENDER_RHYTHM.md) | Kickoff notes: Cascadeur, IlluGen, Blender, Rhythm |
| [EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md) | Trench sweep 2 findings |
| [EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md) | Trench sweep 3 findings |
| [TOOLCHAIN_TRENCH_SWEEP_02_TEST_PLAN_2026-08-31.md](TOOLCHAIN_TRENCH_SWEEP_02_TEST_PLAN_2026-08-31.md) | Test plan derived from sweep 2 |

## Key decisions at a glance (see canonical doc for full matrix)

- **CORE:** ZBrush, SpeedTree, Houdini 22 + Copernicus, Substance, UE 5.8, Oceanology (runtime water authority)
- **TEST NOW:** **IlluGen** (VFX textures / flowmaps — *no shipping dependency until proven*), **LiquiGen** ("flipfluids" rapid liquid sketches), Cascadeur, Unreal MCP (experimental only)
- **OPTIONAL/TEST:** EmberGen (atmosphere sketches), Dash, Toolbag
- **WATCH / RESEARCH ONLY:** RTX Kit, neural shaders, Procedura, Magpie, UE Mesh Terrain, PVE

## Scaffolding for the active spikes

Runnable scaffolds live at the repo root: `C:\EnvironmentPortfolio\toolchain\`

```
toolchain/
├── illugen/         IlluGen spike — Benchmark A molt texture family + export conventions
├── liquigen/        LiquiGen ("flipfluids") spike — Benchmark E Sea Above liquid shot
├── houdini_hython/  Headless Houdini (hython) FLIP + ocean tooling feeding LiquiGen/UE
└── qwen/            Overnight Qwen daemon briefs for these spikes (generated output is under generated/overnight/toolchain/)
```

## Adoption rules (condensed — full list in canonical doc)

1. No tool enters the core stack on demo-reel merit; must beat the current workflow on a real Melodia task.
2. Authoring-only dependencies are safer than runtime dependencies; prefer baked UE-native outputs.
3. One benchmark asset per tool; record version/license/export format before use.
4. Every test ends in **Adopt / Park / Reject**; undocumented "maybe later" becomes Park.


---

## Latest repo-aware procedural-worldbuilding sweep — 2026-09-25

Start with [EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-09-25.md](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-09-25.md) before proposing new Unreal/Houdini/PCG environment R&D.

It explicitly filters current research against the implemented Melodia baseline. In particular, the following are **not new experiments anymore**: PCG Python semantic enrichment, Resonance-driven per-instance material data, generic Houdini->UE procedural work, World Compiler ecology dressing, and the existence of a Mesh Terrain source pipeline.

Current bounded research order:

1. PCG Manual Editing / Data Overrides;
2. Houdini 22 Copernicus HDA -> Unreal texture iteration;
3. local-statistics anti-tiling for large surfaces;
4. iso-contour terrain authoring feeding existing terrain handoff;
5. stochastic erosion / InfiniteDiffusion / neural-material ideas only as parked offline R&D.

The current production ledger still parks broad procedural-system expansion. These are canaries, not new authorities.
