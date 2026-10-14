# 06 — Gate 6 (P0 reference): `HDA_Foundry_Deposition` — Glitter Pile

| | |
|---|---|
| **Purpose** | One general accumulation generator (surface + source + gravity + flow + wind + grain settings → accumulation distribution), proven on a Glitter Pile. |
| **Authority** | Houdini computes the distribution offline. UE runtime is **static baked bulk** plus **Niagara for active grains only**, through the canonical Niagara stack (`Docs/VFX/README.md`, existing effect types). No new Niagara framework, no MPC writes, no millions of live grains. |
| **Inputs** | `recipes/houdini_foundry/deposition_glitter_pile_reference.v1.json`; surface geometry; source shape; optional FieldAtlas `flow` / wind channels. |
| **Outputs** | hero resting mesh · active-grain points CSV (≤ 5k) · surface density · unstable-grain mask · shell mask · depth · normal · low-res density VDB · optional velocity VDB · `bake_manifest.json`. |
| **Evidence** | `Saved/Audit/houdini_foundry/deposition_glitter_pile_reference/` |
| **Status** | STAGED. Texture-only precedent exists: `_build_glitter_pile` in `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`, which is numpy and not deterministic across processes. Reuse its *look* (palette, sparkle), not its seeding. |

## 2026-10-13 native smoke check

The G: candidate `hda/HDA_Foundry_Deposition_1.0.hda` loads in Houdini 22.0.368 Apprentice. A disposable in-memory cook at 4,000 grains produced `OUT_Grains` with 4,000 points and the `accumulation`, `active`, `flow`, `pile_h`, `seedf`, `sparkle`, and rest-position attributes. `OUT_RestMesh` and `OUT_PileField` each produced 20,383 points, 16,129 primitives, and UVs; no node cook errors were reported.

This is a native Hython smoke check only. It did not write the manifest, CSV, VDB, or EXR exports, and it provides no UE integration proof. The current candidate uses deterministic height-grid VEX deposition; it has not completed the POP/Vellum and export contract described below, so the gate remains **STAGED**.

## HDA interface

| Parm | Default | Notes |
|---|---|---|
| `Seed` | recipe seed | all scatter/sim randomness |
| `GrainCount` | 200 000 | offline only |
| `GrainRadius` | 0.15 cm | |
| `Gravity` | (0, 0, −981) cm/s² | |
| `WindVector` | (0, 0, 0) | or sample FieldAtlas `wind_x/wind_y/wind_strength` (baked data only) |
| `FlowInfluence` | 0 | sample FieldAtlas `flow` / `flowdir` |
| `AngleOfRepose` | 32° | drives unstable mask |
| `SimFrames` | 120 | settle frames (grain solver or POP + collision) |
| `ActiveGrainBudget` | 5000 | cap on exported Niagara points |

Inputs: 0 = receiving surface, 1 = source shape, 2 = optional FieldAtlas raster(s).

## Network outline

`source → scatter grains (Seed) → POP/Vellum-grain settle on surface (SimFrames, cache to Saved/HoudiniFoundry/.../cache — never commit) → classify: settled / unstable (slope > repose or low contact count) / shell (outer layer) → bulk: VDB from particles → convert to hero rest mesh (reduce to a Nanite-friendly triangle count) → rasterise to surface UV/level XY: density, depth, normal, unstable, shell → export active grains (unstable ∪ sampled shell, ≤ ActiveGrainBudget) as CSV with position, normal, radius, sparkle_weight`.

## UE integration target (after Gate 1)

1. Import the rest mesh (static, Nanite) + density/normal textures → an existing master (no new master). If the parent needs a sparkle input, use the **existing** sparkle/iridescence lanes.
2. Active grains: a **point cache input to an existing canonical Niagara system**. Spawn from the CSV as a data asset (Niagara "Spawn from data" via an array/DataTable user parameter) or from a static-mesh-surface sampler weighted by the `unstable` mask texture. Pick whichever the existing system already supports. Behaviour (slip, twinkle) is Niagara's; distribution is Houdini's.
3. Reactivity (optional): read `Cymatic_BeatPulse` from `MPC_Cymatics_Driver` **read-only** inside Niagara/material.

Proof chain: **Houdini distribution → baked field → UE → Niagara behaviour**.

## Done when

Minimum: a deterministic manifest with all static outputs (two cooks, same hashes). Exceptional: the active grains spawn from the Houdini points in one existing Niagara system in UE, saved and reloaded, and Brennan approves the look.
