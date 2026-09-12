# Oceanology ↔ v10 Stylization ↔ Melusina Traversal — Deep Study & Verification — 2026-08-29

Every claim below was checked against source on disk (plugin C++, project C++, `.uasset` name
tables, engine shader source, file mtimes). Where a doc in the tree says something different,
the doc is named and corrected. Nothing here was taken from a Monolith return value or from a
prior handoff without re-checking.

---

## 0. TL;DR

1. **The integration is further along than the docs say.** The Oceanology ocean is already
   placed in `LV_SeaAbove_Prototype` (World Partition external actors) *and already overridden
   onto the project's grafted master*. Only the eyeball check is missing.
2. **Spike #1 is answered.** `AOceanologyWaterParent::GetWaveInfoAtLocation(FVector)` is a
   public, BlueprintPure, virtual CPU query returning wave offset, water depth and two SDFs.
   The adapter is ~50 lines.
3. **The stylization/physics balance has one hard rule, and it is derivable from the plugin's
   own source**: Oceanology's CPU wave solver is a *literal C++ clone of its HLSL*. Stylize
   **shading**; never touch **displacement**. The current graft obeys this. Keep it that way.
4. **UE 5.8's new Substrate Toon BSDF cannot be used on the ocean.** Verified in engine shader
   source: Single Layer Water and the toon complex path are mutually exclusive Substrate
   material modes. This kills an attractive-looking approach before it costs a session.
5. **One live defect found**: the "beat drives the ocean" path in
   `MelodiaAudioReactivePresentationSubsystem` writes into an orphan MID and reaches nothing,
   because `UOceanologyWaterMeshComponent::SetMaterial()` is an empty function body.

---

## 1. What is actually on disk

### 1.1 Plugin

`Plugins/Oceanology_Plugin/` — NextGen `1.1.0`, `EngineVersion 5.8.0`, two modules (Runtime
`PostConfigInit` + UncookedOnly editor), Win64 only. 49 `.cpp` / 80 `.h`, 17 `.ush` under
`Shaders/Private/`. Descriptor and binaries both match engine BuildId `55116800`.

Class shape that matters:

```
AOceanologyWaterParent (AActor)          <- surface authority, owns WaterMID + WaveSolver
 |- AOceanologyInfiniteOcean             <- ocean
 \- AOceanologyLake
AOceanologyWaterVolume : APhysicsVolume  <- *** this is why UE swimming works at all ***
AOceanologyManager (AActor)              <- RVT heightmap, game time
UOceanologyWaveSolverComponent (abstract)
 \- UOceanologyGerstnerWaveSolverComponent
UOceanSwimmingComponent : UOceanInteractorComponent   <- full parallel swim stack (keep OFF)
UOceanBuoyancyComponent
```

### 1.2 Project water lane

`Source/BS_GodFile/MelodiaIntegration/` carries 20 `MelodiaWater*` files plus
`MelodiaTraversalComponent`. `EMelodiaWaterQueryProvider` has exactly three values —
`Fallback`, `NativeWaterBody`, `BakedShallowWater`. **There is no Oceanology provider.**
The only project-to-plugin C++ contact is `MelodiaAudioReactivePresentationSubsystem`, which
matches the actor class *by name string* so the file stays buildable with the plugin off.
No Oceanology headers are included anywhere in `Source/`.

### 1.3 Materials

| Asset | State |
|---|---|
| `Masters/M_Water_Oceanology_Melodia` | 51.8 KB, 08-29 01:46. Name table confirms `MF_Oceanology` + `MF_SpectralGerstner` (plugin) **and** `MF_WaterBioluminescence_v9` (project). All 15 new params present: `Toon_Bands`, `Toon_Weight`, 13 x `Biolum_*`. |
| `Masters/M_Water_Oceanology_Melodia_Inst` | 15.7 KB, 08-29 01:46 |
| `Instances/Oceanology/MI_Oceanology_Melodia_Hero` | 5.2 KB, 08-27 20:45 — older lane, superseded |
| `SeaAbove/Prototype/Materials/MI_SeaAbove_{False,Surface}Ocean_Oceanology` | 08-28 23:45, **read-only on disk** (`-r--r--r--`) |
| `Masters/M_Water_Master_Grand_v10_Upgrade` | present — the canonical v10 line, untouched |
| `Saved/Quarantine/M_Water_Oceanology_Melodia.CORRUPT_AttributeGetTypes_2026-08-29.uasset` | 50.6 KB, 08-29 00:45 — the failed graft, correctly quarantined |

---

## 2. Corrections to existing docs

### 2.1 `_SESSION_HANDOFF.md`: "THE C++ TREE DOES NOT COMPILE" — **stale**

`Binaries/Win64/UnrealEditor-BS_GodFile.dll` is **Aug 28 16:50**. The newest header in
`MelodiaIntegration/` is `MelodiaWaterGameplayControllerComponent.h` at **16:49**. The
in-flight build completed. `MelodiaWaterGameplaySubsystem.h` is fully migrated to
`FGameplayTag` (all maps are `TMap<FGameplayTag, ...>`; no residual `TSet<FName>`).

### 2.2 `UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN` §5.7 spike #1 — **answered**

The doc says "confirm the exact C++ surface-query entry point... if it exposes no direct
location query, fall back to a probe-based sampler". It does expose one. Two, in fact:

```cpp
// OceanologyWaterParentActor.h:198
UFUNCTION(BlueprintPure, Category="Waves")
virtual FOceanologyWaveInfo GetWaveInfoAtLocation(const FVector& Location);

// OceanologyWaveSolverComponent.h — same, plus:
FVector   ComputeWaterWaveOffset(const FVector& Location);
float     GetMinWaveHeight() / GetMaxWaveHeight();
FVector2D GetWindDirection();
```

`FOceanologyWaveInfo` returns `WaveOffset`, `WaterWaveOffset`, `BreakingWaveOffset`,
`WaterDepth`, `WaterDepthClamped`, `SDFShoreline`, `SDFOcean`. That covers every field
`FMelodiaWaterSample` needs except normal and velocity, both derivable (§5.3).

Note: `UOceanology_PluginBPLibrary` is a **stub** — one `Oceanology_PluginSampleFunction(float)`.
Do not go looking there.

### 2.3 `OCEANOLOGY_WATER_COEXISTENCE` §3.2 material override — the mechanism is not what it looks like

`UserOverrideMaterial` is declared in `OceanologyWaterParentActor.h:212` and **is never read
anywhere in the plugin's C++**. `grep -rn UserOverrideMaterial Plugins/Oceanology_Plugin/Source/`
returns three hits, all in that one header — the bool itself and two `EditCondition` metas.

The real mechanism is `InitSurface_Implementation`:

```cpp
if (!Material) { Material = GetDefaultMaterial(); }   // lines 491-494
```

So `Material` on the placed instance wins if it is non-null. The bool only *reveals the slot in
the Details panel*. Setting `Material` directly (Python/Monolith) works even with the bool false.

### 2.4 `SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29` §1 "NOT YET SEEN RENDERED" — wiring is done

`LV_SeaAbove_Prototype` is World Partition. Three external actors carry Oceanology:

| Actor | Package | mtime |
|---|---|---|
| `AOceanologyManager` (+ heightmap/gametime components, RVT_Heightmap) | `.../B/AL/YFXFMLGF2C7PE8UFCIG14M` | 08-28 04:30 |
| `AOceanologyWaterVolume` (bound to `OceanologyWater` = the ocean) | `.../B/X0/YQRDXBQR534T08Q6G2HZDQ` | 08-28 04:38 |
| `AOceanologyInfiniteOcean_UAID_7C5758FA1CAC29FC02` | `.../C/VB/VHWRT1P58KT1SXWCO9HLIA` | **08-29 01:40** |

The ocean actor's name table contains
`/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia_Inst` plus `Material`,
`MaterialFar`, `UserOverrideMaterial`, `SpectralGerstner`, `SurfaceScattering`, `BeaufortScale`,
`QuadTreeSettings`, and presets `DA_Wave_Calm` + `DefaultOceanPreset`.

**The graft is already assigned to the live ocean.** What is outstanding is only: open the map
and look at it, then dial `Toon_Weight`.

### 2.5 New — the beat-to-ocean path is dead code

`MelodiaAudioReactivePresentationSubsystem.cpp :: DriveOceanBeatValues` does:

```cpp
if (UMeshComponent* Mesh = Actor->FindComponentByClass<UMeshComponent>())
  if (UMaterialInterface* Base = Mesh->GetMaterial(0))
    if (UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(Base, Actor))
      Mesh->SetMaterial(0, Mid);          // <- reaches nothing
```

Because:

```cpp
// OceanologyWaterMeshComponent.cpp
void UOceanologyWaterMeshComponent::SetMaterial(int32, UMaterialInterface*)
{
    // (entire body commented out — "not compatible ... auto-populated")
}
```

`UOceanologyWaterMeshComponent : UMeshComponent`, so `FindComponentByClass` finds it and the
`SetMaterial` silently no-ops. The subsystem then writes `PhaseGLow`, `HighlightBoost`,
`ScatterBoost`, `DeepScatteringColor` into a MID nothing renders.

Second, independent reason it would still fail if the assignment worked: those four names are
exactly the ones `UOceanologySurfaceScatteringHelper::SetMaterialParameters` re-pushes on every
`UpdateWaterMaterialParameters(...SurfaceScattering)` call, so the plugin would stomp them.

**Correct path** — the plugin's own public API, which writes `WaterMID` *and* the far-distance
MID together:

```cpp
AOceanologyWaterParent::SetScalarParameterValue(FName, float);
AOceanologyWaterParent::SetVectorParameterValue(FName, FLinearColor);
```

**And write our own parameter names, not the plugin's.** `Biolum_Intensity`, `Toon_Weight` etc.
exist only on `M_Water_Oceanology_Melodia`; the plugin has no helper for them and will never
overwrite them. That is the whole reason the graft is worth having.

---

## 3. The physics/stylization coupling (the core question)

### 3.1 Why Oceanology's buoyancy and its visuals agree

`OceanologyComputeSpectralGerstnerUtils.cpp` opens with:

> *"This is a C++ clone version of the HLSL code Spectral Gerstner"*

and reimplements the shader constant-for-constant (`GRAVITY 981.0`, `SQRT_GRAVITY`,
`DETAIL_FACTOR 5.0`, `AMPLITUDE_SCALE 0.1`, `TWO_PI_1_37`), including HLSL `saturate`/`frac`/
`sign` shims. `ComputeWaterWaveOffset_Implementation` calls it with the same
`FOceanologySpectralGerstner` struct the material reads.

That single fact is the whole architecture: **the surface a character floats on and the surface
you see are the same equation evaluated twice.** Buoyancy, swimming, surface-lock rotation and
the rendered crest agree because neither side is an approximation of the other.

### 3.2 The invariant that follows

> **Stylize shading. Never stylize displacement.**

Anything that changes surface *height* on the GPU only — posterized WPO for a stepped
"Wind Waker" crest, reducing wave count on the render side, snapping crests to bands — makes
Melusina float above or sink below the water you can see. There is no cheap fix for that; you
would have to clone the stylization into the CPU solver too, and then you own a fork.

The plugin author names this exact tradeoff himself, in the one place he exposes it:

```cpp
/** WARNING: Using this option may cause water visuals and water surface
    (buoyancy / swimming) to mismatch! */
float SurfaceSpectrumResolution = 1.0f;    // gated by UseSurfaceSpectrumResolution = true
```

Default is `1.0` — full agreement. Treat lowering it as a *performance* lever with a known
visual/physical cost, never as an art lever.

### 3.3 The current graft already obeys this

Per the 08-29 closeout diagram, the graft inserts after `MF_Oceanology` and touches only two
material attributes:

```
GetMA[Emissive Color] -> Add <- MF_WaterBioluminescence_v9 x Biolum_Weight   -> SetMA_0
GetMA[Base Color]     -> xToon_Bands -> Floor -> /Toon_Bands -> Lerp(Toon_Weight) -> SetMA_1
```

No WPO node. No displacement. Pixel-shader instruction count moved 1590 -> 1638, which is the
only hard evidence anywhere that the graft reaches the compiled shader at all. **This is the
correct shape. Do not let a later pass "improve" it by adding a WPO branch.**

### 3.4 Where the industry lands on the same question

This is the standard answer, not a local one. Rare's Sea of Thieves runs Tessendorf FFT for the
wave field and applies its stylization entirely in *shading and supplementary surface
simulation* on top — the physical wave field stays physical because the ship physics ride it.
Galidar markets Oceanology NextGen the same way: one core system spanning photoreal ocean
rendering through stylized toon shading. And the CPU/GPU-sync problem is the first thing every
from-scratch Gerstner buoyancy writeup hits. Links in §9.

---

## 4. The Substrate Toon dead end — verified closed

UE 5.8 ships a first-class Substrate Toon BSDF. It is real and it is in the installed engine:

```
Engine/Shaders/Private/Substrate/SubstrateToonBSDF.ush
Substrate.ush:434   #define COMPLEXPATH_MODE_TOON  2
Substrate.ush:720   // Toon BSDF members — TOON_PROFILEID, TOON_BASECOLOR, TOON_ROUGHNESS ...
```

`r.Substrate=True` is already set (`Config/DefaultEngine.ini:39`), and this project's toon
masters would benefit. So the obvious idea is: put the ocean on the toon BSDF and delete the
`Toon_Weight` lerp.

**It cannot be done.** Substrate stores material mode as one field in the packed header:

```cpp
// Substrate.ush:2490, 2499-2500
bool IsSingleLayerWater() { return (State & HEADER_MASK_MATERIALMODE) == HEADER_MATERIALMODE_SLWATER; }
case HEADER_MATERIALMODE_SLAB_COMPLEX: return HEADER_GETCOMPLEXPATHMODE(State) == COMPLEXPATH_MODE_TOON
                                            ? SUBSTRATE_BSDF_TYPE_TOON : SUBSTRATE_BSDF_TYPE_SLAB;
case HEADER_MATERIALMODE_SLWATER:      return SUBSTRATE_BSDF_TYPE_SINGLELAYERWATER;
```

`HEADER_MATERIALMODE_SLWATER` and `HEADER_MATERIALMODE_SLAB_COMPLEX` are alternatives in one
switch. A material is Single Layer Water **or** a complex slab carrying the toon path — never
both. Oceanology's master is legacy `MSM_SINGLE_LAYER_WATER` auto-converting to
`HEADER_MATERIALMODE_SLWATER`, and it must stay there: SLW is what gives depth-based absorption,
refraction of what is beneath, and the water's own render pass.

**Consequence for art direction, and it is not small:** the reef, the characters and the
wardrobe can go on the native Substrate toon BSDF with real light-driven banding. The ocean
cannot. Its bands come from quantizing Base Color before the SLW output — a *different*
banding model that responds to albedo, not to lights.

Those two will not match by accident. `Toon_Bands` on the water has to be hand-matched by eye
against whatever band count the toon profile uses on the reef, and re-matched whenever the
lighting changes. Budget that as an art task, not a settings copy.

---

## 5. Melusina traversal integration

### 5.1 The seam is one line

```cpp
// MelodiaTraversalComponent.cpp :: UpdateWaterState
bHasWaterSample = WaterSubsystem->QueryWaterAtLocationForActor(Owner, Owner->GetActorLocation(), WaterSample);
bHasAuthoritativeWaterSurface = bHasWaterSample && WaterSample.bSurfaceValid;
if (bHasAuthoritativeWaterSurface) { WaterLevelZ = WaterSample.SurfaceLocation.Z; }

const bool bInWater = bHasWaterSample ? WaterSample.bUnderwater : Movement->IsSwimming();
```

Everything downstream — `StartSwim`/`StopSwim`/`StartDive`, breath, swim stamina, the FLIP/audio
contact bus, the exploration-tension publish — hangs off `bInWater` and `WaterLevelZ`.

### 5.2 What works today, and what is quietly wrong

**Works, with no code at all.** `AOceanologyWaterVolume : APhysicsVolume` with
`EnableSwimmingInArea = true` and `PhysicsVolumeFluidFriction = 0.7`. Stock UE sets
`MOVE_Swimming` on overlap, so `Movement->IsSwimming()` goes true and the fallback branch fires.
Melusina will swim in the Sea Above ocean right now. This is not a second writer — it is
`APhysicsVolume` doing its normal job.

**Quietly wrong.** `bHasWaterSample` is false in that region, so:

- `WaterLevelZ` is **never updated** and stays at its `0.0f` initializer.
- Proximity falls back to `|CharacterZ - WaterLevelZ| / 1000` — measured against Z=0, not
  against the wave surface.
- Which corrupts, in order: `OnWaterProximityChanged`, the `ProximityEntered`/`ProximityExited`
  contact events, the FLIP/splash spawns and `MS_Water_*` audio those drive, the exploration
  tension publish into `UMelodiaRhythmReactivitySubsystem`, and the bioluminescence impulses the
  material bridge derives from contacts.

So the ocean *looks* integrated and *swims* correctly while every reactive system reading water
proximity is being fed a flat plane at world zero. This is the highest-value fix in the lane,
and it is also the thing that makes the bioluminescence graft actually respond to Melusina
rather than just glowing on a timer.

### 5.3 The adapter

Add `EMelodiaWaterQueryProvider::Oceanology` and a branch in
`UMelodiaWaterInteractionSubsystem` mirroring the existing native adapter:

| `FMelodiaWaterSample` field | source |
|---|---|
| `SurfaceLocation` | `WaveInfo.WaveOffset` — already absolute; the base impl adds `WorldPosition` before returning |
| `DistanceToSurface` | `ActorLocation.Z - SurfaceLocation.Z` |
| `bUnderwater` | `DistanceToSurface < 0` |
| `bSurfaceValid` / `bValid` | true when a `AOceanologyWaterParent` is resolved for the region |
| `Immersion` | `clamp(-DistanceToSurface / CapsuleHeight, 0, 1)` |
| `SurfaceNormal` | central difference: 2 extra `GetWaveInfoAtLocation` at ±delta on X and Y, cross the tangents |
| `SurfaceVelocity` | `GetWindDirection() * BeaufortScale`, or per-actor cached `d(WaveOffset)/dt` |
| `WaterBodyId` | `FName` of the `AOceanologyWaterParent` |

Cost is 3-5 `ComputeSpectralGerstner` evaluations per querying actor per frame at
`WaveComponentCount = 128`. Measure it. If it bites, the lever is `SurfaceSpectrumResolution`
below 1.0 — with §3.2's caveat firmly in mind, and only for non-player actors.

Region gating stays as designed: outside the Oceanology bounds the adapter returns "no water"
so native Water Bodies keep authority in the grottos and ponds.

### 5.4 Keep `UOceanSwimmingComponent` off — and know why

It is not a small component. It owns: swim / water-walk / submerged / drowning state machines,
13 multicast delegates, ~10 replicated control axes with server RPCs, surface-lock position and
wave-angle rotation, head/foot/trail Niagara bubble effects with socket lookups, and it
**mutates `UCharacterMovementComponent` directly** — `MaxWalkSpeed`, `MaxSwimSpeed`,
`OrientRotationToMovement`, `UseControllerRotationYaw`, `Buoyancy` — caching `Original*` values
to restore later.

`UMelodiaTraversalComponent` writes the same movement properties. Two components caching and
restoring each other's movement state is precisely the failure class this project already paid
for once with `BP_MelodiaJRPGPlayerController`. The coexistence contract's "plugin swimming OFF"
is correct and should be treated as settled, not re-litigated.

What is worth *reading* from that component later: `SurfaceLockedSwimmingFollowWaveAngle` is a
genuinely nice feel detail — the character pitches to the wave face. Reimplement it in
`MelodiaTraversalComponent` from `GetWaveInfoAtLocation` normals if it is wanted; do not enable
the component to get it.

---

## 6. The division of labour — what each system should own

| Concern | Owner | Rationale |
|---|---|---|
| Wave displacement (WPO + CPU) | **Oceanology, unmodified** | CPU/GPU clone; touching either half desyncs swimming |
| Water depth, SDF shoreline, breaking waves | **Oceanology** | `CalculateWaterDepth` + `ComputeBreakingWaves` feed both render and gameplay |
| Refraction, absorption, SLW output | **Oceanology** | Substrate SLW pass; cannot be replicated in a slab |
| Underwater fog / caustics base | **Oceanology** (lower PPV priority) | photoreal base |
| Base-colour banding | **Project** — `Toon_Weight` / `Toon_Bands` on the graft | pre-BSDF quantization; the only banding SLW permits |
| Emissive bioluminescence | **Project** — `MF_WaterBioluminescence_v9` x `Biolum_*` | shared `I(t)=I0*e^(-lambda*dt)` with grotto water |
| Water colour palette | **Oceanology presets, then override** | ships `DA_Color_AnimeLightBlue` — start there |
| Foam character | **Oceanology presets, then override** | ships `DA_Foam_Stylized`; `FoamEmissive` is a real emissive input |
| Audio-reactive drive | **Project**, via `SetScalarParameterValue` on **our** param names | see §2.5 |
| Underwater grade (music-reactive) | **Project** (top PPV priority) | `AddCachedPPBlend`, per-pawn |
| Swim/dive state | **`UMelodiaTraversalComponent`** | single writer on CharacterMovement |
| Water query | **`UMelodiaWaterInteractionSubsystem`** + Oceanology adapter | one contract, many providers |
| Contact -> FLIP / `MS_Water_*` | **Project** | single writer on particles and audio |

`DA_Color_AnimeLightBlue` and `DA_Foam_Stylized` shipping in the plugin is worth pausing on:
the author anticipated non-photoreal use and gave you tuned starting points *inside* the
physically-correct scattering model. Reading what those presets set is cheaper than inventing
values, and they will not fight the SLW absorption the way hand-picked colours do.

The parameters that actually move the look, all already exposed and all shading-side:

- `FOceanologySurfaceScattering` — `DeepScatteringColor`, `ShallowScatteringColor`, `Absorption`,
  `PhaseGLow/High`, `ScatterBoost`, `WaterRoughness`, `WaterFresnelExponent`
- `FOceanologyFoam` — `FoamContrastLevel` (0.05 default; raising it is the single strongest
  "cartoon foam" lever), `FoamOpacity`, `FoamMapping`, `FoamEmissive`
- `FOceanologySpectralGerstner` — `BeaufortScale`, `MaxWaveHeight`, `WaveComponentCount`.
  These are *physics* parameters: they change both surfaces together, so they are safe, but
  they change how it swims as well as how it looks. Tune them as gameplay, not as art.

---

## 7. Recommended order

| # | Step | Editor? | Why |
|---|---|---|---|
| 1 | Open `LV_SeaAbove_Prototype`, look at the ocean, sweep `Toon_Weight` 0->1 and `Toon_Bands` 2->8 | yes | Everything else is guesswork until the band look is chosen. Wiring is already done (§2.4). |
| 2 | Apply `DA_Color_AnimeLightBlue` + `DA_Foam_Stylized`, then override from there | yes | Cheapest large move toward the target look |
| 3 | Fix §2.5 — route beat drive through `AOceanologyWaterParent::SetScalarParameterValue` onto `Biolum_*` / `Toon_Weight`, delete the `SetMaterial` MID path | no (C++) | Small, self-contained; unblocks audio-reactive ocean |
| 4 | Build the Oceanology query adapter (§5.3) | no (C++) | Fixes proximity / contact / tension / biolum correctness |
| 5 | PIE: swim the ocean, confirm proximity events fire at the *wave* surface, not Z=0 | yes | The gate that proves 3 and 4 |
| 6 | Caustics dedup (spike #3) — plugin caustics vs Melodia underwater projection | yes | Deferred; needs 1 and 5 done to judge |
| 7 | Match reef/character Substrate-toon band count to `Toon_Bands` by eye (§4) | yes | Art task; do it once the ocean look is fixed |

Steps 3 and 4 are both closed-editor C++ and can share one rebuild.

---

## 8. Still open / not verified here

- **Never rendered.** No frame of the grafted master has been looked at. Everything in §1.3 is
  structural verification of the package, not visual confirmation.
- `SurfaceSpectrumResolution` cost at `WaveComponentCount = 128` — unmeasured.
- Caustics doubling — plugin caustics vs `M_Water_Underwater_Post_v10` — unmeasured.
- Plugin example Blueprints fail to compile on 5.8 (per `OCEANOLOGY_ENABLE_STATE_2026-08-27`).
  Not on the path; do not fix plugin content.
- `M_UnderOcean_PostProcess_Vo...` reported missing from plugin content on 08-27; not re-checked.
- The two `MI_SeaAbove_*_Oceanology` instances are **read-only on disk** — part of the 2,719
  read-only `.uasset` population. Saves against them will fail silently.

---

## 9. Sources

- [Rare — *The Technical Art of Sea of Thieves*](https://www.researchgate.net/publication/326906476_The_technical_art_of_sea_of_thieves)
- [Galidar — Oceanology NextGen](https://galidar.com/oceanology-nextgen)
- [maythaswang — *On Stylized Ocean Environment, Unreal Engine 5*](https://maythaswang.github.io/posts/002_fishies_ocean/)
- [Epic — Single Layer Water Shading Model (UE 5.8)](https://dev.epicgames.com/documentation/unreal-engine/single-layer-water-shading-model-in-unreal-engine)
- [Epic — Water Meshing System and Surface Rendering (UE 5.8)](https://dev.epicgames.com/documentation/unreal-engine/water-meshing-system-and-surface-rendering-in-unreal-engine)
- [StraySpark — UE 5.8 Substrate Toon Shader](https://www.strayspark.studio/blog/substrate-toon-shader-ue5-8-tutorial)

Related in-tree: `Docs/Handoffs/OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md` ·
`Docs/Handoffs/OCEANOLOGY_ENABLE_STATE_2026-08-27.md` ·
`Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md` ·
`Docs/Handoffs/SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29.md` ·
`Docs/WATER_V10_FINALIZATION_STATUS_2026-08-09.md` ·
`Docs/Production/Materials/UNIVERSAL_WATER_FAMILY.md`
