# Starskiff Tonight — Free Systems & Download Field Guide

**Date:** 2026-08-28  
**Target:** Sea Above P0 beauty + first Starskiff/Wakebound playable spine  
**Engine:** UE 5.8  
**Rule:** borrow narrow logic; do not import a framework that can destabilize P0.

> **Tonight's thesis:** the best "free asset" is the system already in the project. Oceanology should remain the water authority. Everything else is a donor, a calibration example, or a reference implementation.

---

## 0. Zero-download quick wins already available

### Oceanology NextGen / Pro — use it first

Official docs: https://galidar.com/oceanology-nextgen  
Buoyancy: https://galidar.com/oceanology-nextgen/NextGenBuoyancy  
Changelog: https://galidar.com/changelog

The current Oceanology documentation exposes the exact ingredients Starskiff wants: pontoon buoyancy, spline-driven **FlowController** navigation, force-based propulsion, steering, lateral drag, water velocity, wakes/foam and Niagara crest effects. The August 2026 changelog describes **OceanologyFlowController** as a spline current actor and lists UE5.8 game-ready validation for v1.9.0.

**Steal tonight**
- spline/current representation for `BP_StarskiffRail`
- sampled water height/normal/velocity for `BPC_StarskiffOceanologyAdapter`
- navigation-mode concepts: steering + propulsion + lateral drag
- auto-pontoon setup only as a fast stability baseline
- ship/wake FX as presentation donors, not as a new gameplay framework

**Do not do tonight**
- replace Melodia's existing water interaction authority
- make Starskiff inherit an Oceanology demo pawn just because it works quickly
- spread plugin calls across gameplay Blueprints

All plugin access should collapse behind:

```text
BPC_StarskiffOceanologyAdapter
    SampleSurface(WorldLocation)
    SampleFlow(WorldLocation)
    GetSurfaceNormal(WorldLocation)
    GetCurrentRailData(WorldLocation)
```

If Oceanology APIs change again, only this adapter should hurt.

---

## 1. Ranked download / reference shortlist

| Rank | Source | Cost / license | Use tonight | Integration policy |
|---|---|---|---|---|
| **1** | **Oceanology NextGen/Pro FlowController** | already owned/installed | **YES — immediate** | Use native spline current data; wrap it. |
| **2** | **Epic `BP_BuoyancyExample`** | included with UE Water plugin / Epic sample content | **YES — 10–20 min** | Calibration reference only; do not make Epic Water the authority. |
| **3** | **Jay2645/BuoyancySystem** | MIT, public GitHub | **REFERENCE — 20–40 min max** | Read spring/probe/boat stabilization logic. Do **not** drop old UE4 plugin into UE5.8. |
| **4** | **MrRobinOfficial/Unreal-NebulousVehicle** | MIT, public GitHub, WIP | **REFERENCE if possession/input hurts** | Borrow Enhanced Input / drivable-pawn ideas only. Avoid framework import. |
| **5** | **Epic Water Buoyancy documentation** | free documentation + engine content | **YES — keep open** | Pontoon layout, CoM, damping sanity check. |

### Direct sources

**Epic Water Buoyancy / `BP_BuoyancyExample`**  
https://dev.epicgames.com/documentation/en-us/unreal-engine/water-buoyancy-component-in-unreal-engine

Location in Content Browser after showing plugin content:

```text
Engine > Plugins > Water Content > Blueprints > BP_BuoyancyExample
```

**Jay2645/BuoyancySystem — MIT**  
https://github.com/Jay2645/BuoyancySystem

Safe way to inspect without polluting the project:

```powershell
mkdir _ExternalReference -ErrorAction SilentlyContinue
cd _ExternalReference
git clone --depth 1 https://github.com/Jay2645/BuoyancySystem.git
```

The repository is a UE4-era system and its last code push is old. Treat it as readable physics literature: probe placement, displacement forces, damping, water contact, boat stability. **Do not compile it into Melodia tonight.**

**Nebulous Vehicle — MIT**  
https://github.com/MrRobinOfficial/Unreal-NebulousVehicle

This is a WIP Chaos Vehicle extension, so it is not a Starskiff dependency. Read it only if you need a compact example of a drivable Pawn, Enhanced Input bindings, camera/input separation, or possession flow. Starskiff should remain a plain dedicated Pawn with Melodia-owned movement unless a later physics pass proves otherwise.

### Manual / marketplace downloads

No marketplace download is required for tonight's Starskiff prototype beyond the Oceanology build already in the project. If a Fab page, sample project, or account-gated asset requires accepting a separate license, **download it manually and keep it out of Git/LFS until its license and redistribution terms are checked.** Do not mirror third-party binaries into this repository just for convenience.

---

## 2. Tonight's 30-minute path

### A. Make `BP_StarskiffRail` before making a "vehicle system"

The rail is a **world rule**, not a generic vehicle feature.

```text
BP_StarskiffRail
├─ Spline
├─ RailStrength         = 0.0–1.0
├─ RailWidth            = world-space falloff radius
├─ EntryEaseDistance
├─ ExitEaseDistance
├─ MaxRailSpeed
├─ VisualRibbon / Niagara reference
└─ Optional Oceanology FlowController reference
```

At runtime:

```text
GetClosestPointOnSpline(StarskiffLocation)
→ GetDistanceAlongSpline
→ GetTangentAtDistance
→ Calculate lateral error to spline
→ RailAcceleration = Tangent * Strength
→ Correction = -LateralError * CenteringStrength
→ TargetVelocity += RailAcceleration + Correction
```

Never teleport the skiff to the spline. It should feel like a current that **persuades** the vessel into a path.

### B. `BPC_StarskiffMovement` owns motion

```text
Input2D
→ desired heading / throttle
→ sample adapter surface + flow
→ compose target planar velocity
→ add rail acceleration when active
→ apply accel / drag / turn response
→ solve vertical surface offset
→ SafeMoveUpdatedComponent
→ SlideAlongSurface
```

Start with a kinematic movement component. Let the visual hull bob/lean separately. This is dramatically easier to tune for a magical manta-skiff than full rigid-body boat physics.

### C. Put Oceanology behind one seam

`BPC_StarskiffMovement` must not know which Oceanology Blueprint/C++ class provides the data.

```text
BPC_StarskiffMovement
    ↓ asks
BPC_StarskiffOceanologyAdapter
    ↓ translates
Oceanology surface / wave / current API
```

This is the protection against plugin churn and the difference between "we used Oceanology" and "our game architecture became Oceanology."

---

## 3. 1–2 hour playable behavior

### SKIM

```text
FlowVector = Adapter.SampleFlow(Location)
PlayerVector = Forward * Throttle + Right * SteerAssist
TargetVelocity = PlayerVector * CruiseSpeed + FlowVector * FlowInfluence
Velocity = VInterpTo(Velocity, TargetVelocity, DeltaSeconds, AccelResponse)
```

**First-pass feel**
- fast acceleration, slower deceleration
- yaw follows movement with a little lag
- visible hull banks after the gameplay root already knows where it is going
- surface offset follows water slowly enough to feel buoyant, not magnetized

### CURRENT RAIL

```text
RailAlpha = smooth falloff from rail width
RailVelocity = RailTangent * RailSpeed * RailAlpha
Velocity = lerp(FreeSkimVelocity, RailVelocity + PlayerBias, RailCapture)
```

Player agency must survive rail capture. Keep a small steering bias so the current feels rideable, not cinematic autopilot.

### ANCHOR

Fantasy: Mara's measured certainty stabilizes a world that wants to move.

```text
if Anchor:
    ThrottleScale ↓
    LinearDamping ↑
    AngularVisualLean ↓
    RailCapture can remain
    WorldDriftResponse ↓
```

Do not implement Anchor as `SetActorLocation` lock. It should still breathe with the sea.

### SOUNDING LEAP

For the P1 prototype, fake the clean game-feel version first:

```text
LeapPressed
→ cache normal surface-follow mode
→ add vertical impulse / scripted vertical velocity
→ reduce water-follow strength for a short window
→ apex visual FX
→ restore surface-follow blend on descent
```

Only move to real rigid-body impulse if this cannot produce the desired readability.

---

## 4. Mount / dismount: build the 12-node version

Do not import a mount framework for one vehicle.

### `BPI_Mountable`

```text
CanEnter(Interactor) -> bool
Enter(Interactor)
Exit(Interactor)
GetExitTransform() -> Transform
```

### Enter flow

```text
Player interacts with Starskiff
→ cache current Character Pawn
→ disable character movement/input presentation
→ PlayerController.Possess(BP_Starskiff)
→ attach/hide character to SeatAnchor as required
→ switch Input Mapping Context
```

### Exit flow

```text
Find safe GetExitTransform
→ PlayerController.Possess(Character)
→ restore character transform / visibility / movement
→ restore character Input Mapping Context
```

If this becomes painful, inspect the MIT vehicle reference for patterns. **Do not adopt a generic vehicle inventory/garage framework.**

---

## 5. Enhanced Input — minimum map

```text
IMC_Starskiff
├─ IA_Starskiff_Move      Vector2D
├─ IA_Starskiff_Anchor    Bool
├─ IA_Starskiff_Leap      Bool
├─ IA_Starskiff_Exit      Bool
└─ IA_Starskiff_Look      Vector2D
```

Map it only while Starskiff is possessed. Keep gamepad curves in the Input Mapping Context, not scattered through movement math.

---

## 6. Wake / splash quick win

Do not stop P0 to build a general VFX framework.

Reuse Oceanology's water information and Niagara examples where stable, but make one Melodia-owned presentation system:

```text
NS_Starskiff_Wake_Prototype
Inputs:
    User.Speed01
    User.Turn01
    User.Rail01
    User.Leap01
    User.WaterNormal
```

Emit from two stern sockets or a short ribbon behind the hull.

**Visual priorities**
1. long pearly wake line at cruise
2. compact bright fan on hard turns
3. upward droplets when crossing Sea Above anomalies
4. almost no foam when Anchored
5. a thin cyan/lavender "second wake" offset vertically by a few centimeters when RailAlpha is high

The second wake is more Melodia than another realistic splash library.

---

## 7. What each source contributes to our exact assets

### `BP_Starskiff`
- **Oceanology:** world water state and buoyant surface reference
- **Epic Buoyancy example:** CoM/pontoon intuition only
- **NebulousVehicle:** optional possession/input/camera reference

### `BPC_StarskiffMovement`
- **Oceanology:** current / surface inputs
- **Jay2645:** only if we need damping/stability ideas
- **Melodia code:** remains authoritative movement behavior

### `BPC_StarskiffOceanologyAdapter`
- **Oceanology only.** This is where version-specific calls live.

### `BP_StarskiffRail`
- **Oceanology FlowController / spline** as the implementation reference
- Melodia owns capture rules, rhythm response, visual language and route authoring

### Wakebound / Shorewake outfit
- no third-party runtime framework needed
- reacts to the same seam/current data as the skiff
- outfit detects the current before the vehicle can ride it

### Sea Above P0
- do **not** make Starskiff a prerequisite for the first reveal
- borrow wakes/upward droplets only if they improve the hero shot without creating new failure modes

---

## 8. The P0 protection rule

If an external system takes **more than ten minutes** to understand, compile, migrate or repair, close it and continue with the Melodia facade.

Tonight's success condition is not "we integrated five free systems." It is:

> **The coast feels authored, the second horizon feels impossible, the Bell pulse reads, and one Starskiff current ride proves the next layer of the game is real.**

---

## 9. Agent handoff — Claude / Codex / editor agent

When implementing from this document:

1. Inspect the current asset tree and Oceanology version before writing anything.
2. Do not invent Oceanology Blueprint function names. Find the actual v1.9/ported API in this project.
3. Do not add a second water gameplay authority.
4. Do not add new C++ merely to reproduce a 15-node Blueprint prototype.
5. Keep all Oceanology calls inside `BPC_StarskiffOceanologyAdapter`.
6. Build the rail and movement facade first; VFX second.
7. Compile/save after each Blueprint milestone.
8. Keep each commit narrow and reversible.
9. Never modify the water V10 study master merely to support Starskiff.
10. If third-party code is copied rather than merely studied, preserve its license and attribution and record exactly what was copied.

### Suggested commit sequence

```text
feat(starskiff): add minimal mountable pawn shell
feat(starskiff): add Oceanology adapter facade
feat(starskiff): add skim movement prototype
feat(starskiff): add authored current rail
fx(starskiff): add prototype wake and rail response
```

---

## 10. Download checklist

- [x] Oceanology — already in project; verify current build/API
- [x] Epic `BP_BuoyancyExample` — already available in engine plugin content
- [ ] Jay2645/BuoyancySystem — clone **outside** project only if stabilization logic is needed
- [ ] NebulousVehicle — open/clone **outside** project only if possession/input architecture is needed
- [ ] No other framework download until the P0/P1 slice proves a concrete missing capability

**Default tonight:** download nothing else, build the Melodia-owned layer, and use the references as a microscope rather than a foundation.
