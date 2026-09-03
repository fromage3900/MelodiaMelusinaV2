# P0 Material + Sea Above Gate — 2026-08-27

This handoff records the current evidence boundary for the six material masters
and the Mesh Terrain / Gaea preparation lane. It is not a claim of final visual
approval or a completed Sea Above level.

## Six-master live compile baseline

Queried through Monolith `material_query.get_compilation_stats` on 2026-08-27.

| Master | Compile | VS / PS | PS texture samples | Samplers | Domain |
|---|---:|---:|---:|---:|---|
| `M_Master_Toon_Universal` | PASS | 313 / 1182 | 23 | 16 | Opaque |
| `M_Master_Toon_Landscape_HeightBlend` | PASS | 153 / 593 | 25 | 13 | Opaque |
| `M_Master_Nikki` | PASS | 153 / 292 | 4 | 0 | Opaque |
| `M_Master_Nikki_Landscape` | PASS | 153 / 307 | 0 | 0 | Opaque |
| `M_Master_Toon_Universal_Alpha` | PASS | 313 / 1183 | 23 | 0 | Masked, two-sided |
| `M_Water_Master_Grand_v10_Upgrade` | PASS | 260 / 1727 | 12 | 0 | Opaque, two-sided |

## Validation interpretation

The water master reports zero Monolith validation issues. The two Universal
variants report large `broken_texture_ref` / island lists that are known
validator false positives for the project's TextureObjectParameter →
TextureSample pattern, plus genuine inert islands. Do not run auto-fix or
delete-island operations on these masters without a fresh owner-approved graph
backup; prior deletion attempts crashed the editor.

Landscape and Nikki validation reports contain island/unused-parameter findings
but live compilation passes. These remain cleanup debt, not a reason to rewire
the production masters during the Sea Above prototype.

Native thumbnails were generated for all six masters. The default master
thumbnails are diagnostic spheres, not approved lookdev captures; lookdev must
be judged on named material instances in an isolated map.

Representative instance inspection found the following current state:

| Master family | Representative instance | Direct overrides |
|---|---|---:|
| Universal | `MI_Show_NikkiDream` | 0 |
| Landscape | `MI_Gaea_SakuraTerrace_Substrate` | 0 |
| Nikki | `MI_Nikki_Show_PearlSheen` | 0 |
| Nikki Landscape | `MI_Landscape_NikkiDream` | 0 |
| Universal Alpha | `MI_AtlasLeafA` | 0 |
| Water V10 | `MI_WaterV10_Integrated_OceanPreview` | 0 |

This explains the neutral diagnostic thumbnails: these representatives inherit
defaults rather than carrying a lookdev override set. The existing
`MI_WaterV10_Integrated_CinematicHero` is a useful counterexample with 39 live
overrides and is the better starting point for the Sea Above false-ocean look.
No arbitrary overrides were injected into the six representative assets.

## Mesh Terrain / Gaea gate

- UE P0 substrate: Mesh Terrain only; no classic Landscape actor.
- Existing adapter smoke handoff: present under
  `Saved/Audit/gaea2unreal_adapter_smoke_20260825/ue_handoff/`.
- Existing Substrate instance apply report: all recorded setup rows are `OK`.
- Sea Above native Gaea export: **blocked**. Installed assemblies identify as
  Gaea `2.3.0.1`; the committed exporter is pinned to `2.2.3.2` and fails during
  reflection loading. No Sea Above terrain graph or map outputs were accepted.
- The wrapper now propagates failure and refuses to claim success without a
  destination graph and handoff manifest.

## Sea Above prototype assets

Created through the live Monolith surface under the isolated namespace:

- `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
- `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_SeaAbove_SurfaceOcean`
- `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_SeaAbove_FalseOcean`

`MI_SeaAbove_SurfaceOcean` is duplicated from the integrated CalmPond instance.
`MI_SeaAbove_FalseOcean` is duplicated from the integrated CinematicHero
instance and has a disposable low-motion profile: WaveAmplitude `0.018`,
WaveSpeed `0.06`, FoamIntensity `0.05`, RippleStrength `0.12`, RippleSpeed
`0.08`, and world UV blend `1.0`. After lookdev review, the false-ocean
emissive/caustic response was muted in the prototype only: BioIntensity `0`,
BioFlashRate `0`, all bioluminescence weights `0`, CausticIntensity `0.08`,
SparkleDensity `0.02`, and the main foam weights reduced to `0.20`, `0.20`,
and `0.15`. Singular parameter readback matched the requested values and the
asset was saved successfully. Preview evidence is
`Saved/Audit/sea_above_false_ocean_muted_preview.png`.

During level lookdev the false-ocean preview was subdued, while the isolated
map contained two full-weight Ultra Dynamic Sky post-process components. A
prototype-only lighting diagnostic was applied and saved: both UDS
post-process blend weights are `0.0`, the UDS Sun intensity is `1.5`, and both
UDS SkyLight components are `0.35`. This is intentionally reversible and does
not alter the UDS asset or any production level.

The original prototype instances were found to inherit 39–40 integrated
lookdev overrides, which made their emissive behavior unsuitable as a neutral
baseline. Two clean instances were created directly from the V10 master:
`MI_SeaAbove_SurfaceOcean_Clean` and `MI_SeaAbove_FalseOcean_Clean`. Each has
20 intentional scalar overrides; the false-ocean readback confirms
`BioIntensity=0`, `BioFlashRate=0`, all three primary bioluminescence weights
at `0`, `CausticIntensity=0.08`, and `SparkleDensity=0.02`. Both assets are
saved. The false-ocean plane in the World Partition prototype is now bound to
the clean false-ocean instance, and the WP map save plus scoped dirty-package
audit both pass.

The level is intentionally a disposable blockout at this stage. Mesh Terrain
partition and hero-camera capture remain unbuilt; the Bell proxy, membrane, and
Niagara anomaly now have prototype work in progress.

The isolated level now contains a saved blockout pass authored through Monolith:

- `SeaAbove_BellProxy_Prototype` — large sphere proxy at Z `-18000` cm.
- `SeaAbove_CentralCore_Proxy` — inner sphere proxy at Z `-16000` cm.
- `SeaAbove_ObservationCliff_Prototype` — cylinder staging platform at origin.
- `SeaAbove_FalseOceanPlane_Prototype` — large thin plane at Z `-5000` cm using
  `MI_SeaAbove_FalseOcean`.

`M_SeaAbove_Membrane_Prototype` is a separate translucent, unlit, two-sided
material with `MembraneTint` and `MembraneOpacity` parameters, Fresnel-driven
opacity, and a time/sine pulse wired to emissive. Monolith recompile passed:
191 pixel instructions, 339 vertex instructions, 2 samplers, and no compile
errors. The level was saved through the editor scripting subsystem.

An isolated Niagara system was also created at:

`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/VFX/NS_SeaAbove_UpwardDroplets_Prototype`

Its `UpwardDropletsEmitter` uses CPU simulation, SpawnRate, InitializeParticle,
ShapeLocation, AddVelocity, GravityForce, SolveForcesAndVelocity, and a sprite
renderer. The isolated membrane material was marked for Niagara sprite usage,
and the duplicate renderer was removed.
Synchronous Niagara diagnostics reported `error_count: 0`, `warning_count: 0`,
and both particle scripts `UpToDate`; the final compact summary reports one
sprite renderer and nine total modules. The final `save_system` request returned
`saved: true, was_dirty: true`, so the sprite-material assignment and solver
mutation are persisted and revalidated through Monolith.

The saved prototype level now contains one idempotently bound `NiagaraActor`
named `SeaAbove_UpwardDroplets_Prototype`, using
`NS_SeaAbove_UpwardDroplets_Prototype` and tagged `SeaAbove_Prototype` plus
`UpwardAnomaly`. Editor Python inspection confirmed the actor alongside the
Bell, Core, ObservationCliff, and FalseOcean blockout actors. A scoped dirty
package audit returned zero packages after the Niagara system was saved.

## Next P0 actions

1. Use a verified Gaea 2.2.3.2 installation or port the exporter against 2.3.0.1
   with a disposable copy of the graph.
2. Import one real heightmap through the isolated Mesh Terrain namespace.
3. Assign a derived `M_Master_Toon_Landscape_HeightBlend` instance and verify
   partition build, PCG reads, PIE, and a clean fixed-camera capture.
4. Complete the isolated Sea Above prototype: add the 12–20 second pulse, then
   capture the fixed-camera reveal.
5. Resolve PPV drift separately: current ZenForest state is a four-blendable
   PortfolioHero stack rather than the documented three-blendable
   GameplayStandard stack.

The first Sea Above candidate staging attempt was intentionally terminated
after the editor viewport became unusable. It created only the isolated
`Terrain/SM_SeaAbove_LiquidCathedral_257` mesh and
`Terrain/MI_SeaAbove_LiquidCathedral_Substrate` asset; no stage report or
MeshPartition bridge result was produced, so partition build remains
unverified. Do not delete or re-run over these assets until the editor viewport
and modal state are recovered.
