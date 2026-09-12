# Oceanology ↔ Existing UE Water Pipeline — Coexistence Design (2026-08-15)

Status: DESIGN. Oceanology NextGen 1.9.0 (Fab purchase, Galidar) still downloading as of
2026-08-15. A legacy copy **Oceanology v5.7.0 (5.3/5.4)** was found on disk at
`F:\Downloads_Organized\Downloads\Archives\Oceanology v5.7.0 (5.3 5.4).rar.001/.002`
(extracted: `F:\Downloads_Organized\Downloads\Extracted_Folders\Oceanology v5.7.0 (5.3 5.4)\Oceanology v5.7.0 (5.3, 5.4)\Oceanology_Plugin`).
The legacy line targets UE 5.3/5.4 and is NOT the integration target; the purchased
**NextGen** line is. The 2026-07-12 `OceanologyBuildTest_*` logs under
`F:\_FromG_Archive\2026-07-12\Unsorted Review\MelodiaMelusina\` show an earlier attempt
against the MooaToon precompiled engine that died in UBT (`Ionic` missing) **before
touching Oceanology code** — so 5.8 compatibility is unverified, not proven broken.

This doc is the single-writer contract for how Oceanology coexists with the existing
pipeline: `UMelodiaWaterInteractionSubsystem`, `UMelodiaTraversalComponent`,
`UMelodiaWaterNiagaraBridgeComponent`, `UMelodiaWaterRippleMaterialBridgeComponent`,
`UMelodiaWaterUnderwaterPostProcessComponent`, v9/v10 water materials, FLIP pools,
`MS_Water_*` MetaSounds, and `MPC_Melodia_Palette`.

---

## 1. Authority model

Oceanology is the **hero-surface simulation authority** in L_Atlantis ocean regions ONLY.
It is a surface shader + buoyancy provider, never a second writer on gameplay state.

| Concern | Authority (unchanged) | Oceanology's role |
|---|---|---|
| Gameplay water query (`FMelodiaWaterSample`: surface height, depth, normal, velocity, immersion) | `UMelodiaWaterInteractionSubsystem` | Supplies height/velocity through a new **Oceanology-backed adapter** behind the existing sample interface |
| Swim/dive state + tension feed | `UMelodiaTraversalComponent` | **Disabled** (its swimming/buoyancy mechanics off); only the plugin's `Displacement Physics Volume` API may be read |
| Contact events → FLIP pool/splash + `MS_Water_*` | `UMelodiaWaterInteractionSubsystem` event emission | "Wave Crest Splash" toggled **off** — one writer on particles and audio |
| Surface shading | v9/v10 MIs + `UMelodiaWaterRippleMaterialBridgeComponent` (3-slot ripple + bioluminescence impulses, writes by parameter name) | FFT master material **kept intact**; toon `TP_*` profiles + `MPC_Melodia_Palette` pulse params applied at the MI layer |
| Underwater post-process | `UMelodiaWaterUnderwaterPostProcessComponent` (dynamic, music-reactive grade) | Plugin's fog/caustics/absorption/god-rays as photoreal base at LOWER blendable priority; Melodia grade stacks ABOVE (higher priority) so reactivity tints last |
| Audio reactivity | `MPC_Melodia_Palette` single-writer map | Plugin's wave-state audio integration **disabled** — its surface is one more MPC consumer |
| Fluids ladder (Tier 0 analytic → FLIP2D → 3D FLIP hero; `NiagaraFluids` enabled 2026-08-15) | Existing ladder | Lives alongside; gameplay-validated zones stay on the ladder |

## 2. Adapter seam (the one C++ change)

Mirror the existing native adapter pattern inside `MelodiaWaterInteractionSubsystem`:

```
FMelodiaWaterSample ← UMelodiaWaterInteractionSubsystem::Query()
        ▲
        ├─ NativeAdapter (existing: WaterBodyManager::TryQueryWaterInfoClosestToWorldLocation)
        └─ OceanologyAdapter (NEW): samples the plugin surface via its
           Displacement Physics Volume height API → fills height/depth/normal/velocity;
           immersion computed from player depth vs sampled height
```

- **Integration spike #1 (post-install):** confirm the exact C++ surface-query entry point
  in the purchased NextGen build. If it exposes no direct location query, fall back to a
  probe-based sampler (a lightweight actor reading the displacement material) — do NOT
  GPU-readback from game code.
- The contract struct `FMelodiaWaterSample` does not change; consumers are untouched.
- Region gate: adapter returns "no water" outside the L_Atlantis ocean bounds so native
  Water Body regions keep their authority (per-region, multi-instance).

## 3. Material-layer integration (toon substrate, non-destructive)

1. Plugin master materials stay owned by the plugin (reparenting breaks FFT wiring).
2. Create `MI_*` instances under `/Game/EnvSandbox/Materials/Instances/Oceanology/`
   parenting the plugin masters; apply `TP_Default` baseline (surface), `TP_Gold`
   (crest sparkle bands).
3. `UMelodiaWaterRippleMaterialBridgeComponent` already writes normalized params to
   "ordinary actor mesh materials" — drive the ocean MIs by parameter name with the same
   ripple-ring + bioluminescence impulses as the v9/v10 surfaces. Parameter names
   confirmed at install time (spike #2: capture plugin MI param list via reflection).
4. `MPC_Melodia_Palette` (`BeatPulse`, `GlobalEmissiveBoost`, `DreadPresence`, …) feeds
   the plugin MIs through the same accumulator chain as v9/v10 — the ocean is a consumer.
5. The plugin's own content props (boats, buoyancy geometry) route through
   `Content/Python/ingest_aaa_underwater_packs.py` into `M_Master_Toon_Universal`
   instances, matching the KitBash3D Atlantis treatment.

## 4. Underwater post-process priority

```
[Base]  Oceanology underwater PP (fog, caustics, absorption, god rays) — photoreal base
[Top]   UMelodiaWaterUnderwaterPostProcessComponent (dynamic v9 underwater material) —
        music-reactive grade tinted last by MPC
```
Reconcile caustics: disable plugin caustics if the Melodia underwater material already
projects caustics; otherwise both may double. Decide in L_Atlantis slice (spike #3).

## 5. Region model & budgets

- Oceanology (RTX 3080/4070+ class) scoped to L_Atlantis hero ocean vistas.
- Interior grottos / celestial ponds / gameplay-validated zones: native Water +
  v10 FLIP ladder — unchanged.
- Multi-instance + preset system used for per-region tuning; day/night of the plugin may
  run only in the hero vista.

## 6. Post-install verification checklist

1. Closed-editor build with plugin enabled (AGENTS.md rules 15/21 — full rebuild, not
   just Live Coding; unity collisions checked).
2. Spike #1: surface-query entry point confirmed; adapter fills all `FMelodiaWaterSample`
   fields; gameplay consumers see identical behavior vs native regions.
3. PIE: swim/dive via `UMelodiaTraversalComponent` still authoritative; contact events
   spawn FLIP pool/splash once; `MS_Water_*` MetaSounds fire once per event.
4. Material: bridge param writes land on the Oceanology MIs (verify via material
   telemetry params, same method as v9); MPC pulse visibly drives the ocean surface.
5. Post-process stack: both layers active, Melodia grade on top, no double caustics.
6. Audit report into `Saved/Audit/`; update this doc's spikes to verdicts.

## 7. Decisions required (owner)

- [ ] Oceanology plugin built-in swimming/buoyancy mechanics: **off** (Melodia traversal wins)?
- [ ] Plugin wave-state audio integration: **off** (single writer on `MS_Water_*`)?
- [ ] Plugin caustics in underwater PP: **off** if Melodia caustics stay on?
- [ ] Legacy v5.7.0 copy on F:: keep as archive reference only (no import) — confirm?

Related: `Imports/Oceanology/PROVENANCE.md`, `Imports/KitBash3D_Atlantis/PROVENANCE.md`,
`Content/Python/ingest_aaa_underwater_packs.py`,
`Docs/WATER_SYSTEM_EXPANSION_RESEARCH_2026-08-08.md` (NiagaraFluids re-enabled note).