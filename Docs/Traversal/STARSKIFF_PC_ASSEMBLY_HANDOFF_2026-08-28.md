# Starskiff + Wakebound Survey Set — PC Assembly Handoff

Date: 2026-08-28
Status: executable P1 assembly checklist / docs-only
Branch: `docs/p1-monolith-character-concepts-2026-08-28`
Related: PR #25, Issue #26, `STARSKIFF_WAKEBOUND_ASSET_AND_VEHICLE_PLAN_2026-08-28.md`, `P1_REEF_THAT_LOOKS_BACK_PLAN_2026-08-28.md`

## Goal

This file is the **PC-side assembly order** for building the first rideable Starskiff greybox and Wakebound Survey Set without committing prematurely to final hero art or a custom boat-physics framework.

The production rule is:

> **Prove the ride, rider pose, waterline, rail capture and Oceanology contact first. Then freeze proportions and sculpt the hero Starskiff.**

---

# 1. Download queue

Download only the items needed to answer a concrete production question.

## Required first downloads

### 1. Free Wooden Rowboat — greybox hull
https://www.fab.com/listings/59573310-9be8-459f-98cb-954a66e5ef2c

Use for:
- rider scale
- mundane hull length/beam reference
- waterline
- collision
- camera framing
- Oceanology buoyancy test

Do **not** treat as final visible art.

### 2. CLO FV2 Puffed-Sleeve Blouse — Wakebound torso block
https://connect.clo-set.com/ko/detail/579f920f3ec84df39c1c59833fab97f6

Use for:
- preserving Melusina's puff-sleeve construction
- testing riding/lean deformation
- rapid field-ready torso blockout

### 3. CLO FV2 Gather Skirt — Wakebound skirt block
https://connect.clo-set.com/portfolio/208988/collection/collections/221102e3493f8866b34c9f868d88727b3021e7?itemId=a508038e5c834127989c4e0901e5743d

Use for:
- skirt volume
- shortening into traversal proportions
- rider clearance

### 4. House of U 2150 U-circular Chiffon — Listening Hem simulation reference
https://connect.clo-set.com/detail/725ae2c9ff524b2ead1795b49071fcf4

Use for:
- asymmetric Listening Hem drape
- finding a stable flare/length before hand-sculpting

## Optional downloads after greybox questions appear

### 5. 13 ft Wooden Skiff — detailed proportion reference
https://www.fab.com/listings/5432a3e7-d97f-4f34-a682-8e88d19f7d29

Only acquire if the free rowboat is too generic for underside, gunwale, seat-height or flat-bottom study.

### 6. Manta Ray — planform / fin-motion reference
https://www.fab.com/listings/a430d1e9-b2e8-4b44-b699-bc6b2c2698c9

Reference only. Abstract the broad pectoral-fin planform into Starskiff resonance fins; do not graft a literal animal onto the boat.

### 7. Alternate puff-sleeve peplum blouse
https://connect.clo-set.com/detail/bb8faa04606341919f8b12ca6e6f9e28

Use if the official puff blouse takes too long to reshape toward Melusina's fitted torso.

### 8. Official FV2/KOFOTI pattern collection
https://connect.clo-set.com/portfolio/208988/collection/collections/2411DDd4ef97a73b324c89a9ee160a79c5d76d

Useful for A-line, princess-line and jacket donor construction.

### 9. FV2 Princess Line Jacket
https://connect.clo-set.com/ja/detail/25a76259a8344989abb862b6c5338c98

Optional basis for the small Mara-influenced survey capelet/jacket.

## Source/licence recording

For every downloaded third-party asset, add a local provenance note containing:
- title
- source URL
- author/store
- licence tier/text as shown at acquisition
- acquisition date
- intended use: `REFERENCE_ONLY`, `GREYBOX`, `KITBASH_DONOR`, or `PRODUCTION_ALLOWED`

Do not assume a source remains downloadable later.

---

# 2. Suggested local working folders

These are **working-source folders**, not final Unreal content paths.

```text
MelodiaMelusinaV2/
  ExternalSource/
    Starskiff/
      Reference_Hulls/
      Reference_Manta/
      Licenses/
      Screenshots/
    Wakebound/
      CLO_Blocks/
      CLO_Fabrics/
      Exports/
      Licenses/
```

If `ExternalSource/` is intentionally gitignored, keep the provenance markdown/text files in a tracked project-doc location instead.

Suggested tracked provenance destination:

```text
Docs/Provenance/P1_Starskiff_Wakebound/
```

Do not commit purchased source packages to Git unless their licence explicitly permits redistribution and the repository policy intends it.

---

# 3. Unreal content layout

Recommended project-native destinations for newly authored/derived game assets:

```text
Content/Melodia/Traversal/Starskiff/
  Blueprints/
  Meshes/
  Materials/
  VFX/
  Audio/
  Animation/
  Data/
  Test/

Content/Melodia/Characters/Melusina/Outfits/Wakebound/
  Meshes/
  Materials/
  Textures/
  Animation/
  Data/
```

Vendor/plugin content stays inside its own plugin/content namespace. Do not move or edit Oceanology vendor content unless the local port already requires it.

---

# 4. First PC session — assembly order

## A. Verify local Oceanology 5.8 port

Before making the Starskiff Blueprint:

1. Launch the project and confirm the ported Oceanology plugin loads without compile errors.
2. Search the plugin/example content for its sample boat/vessel Blueprint, pontoon/buoyancy component(s), wake system and any FlowController/spline navigation examples.
3. Write down the **exact local class and node names**. Public docs may not match the locally ported 5.8 build.
4. Play the vendor sample boat, if present, on the current Oceanology ocean.
5. Confirm representative waves do not explode the sample physics before copying any setup.

**Stop condition:** if the vendor sample boat is unstable in the port, solve/contain that before adding Melodia traversal logic.

---

## B. Import the throwaway rowboat

1. Import the free Wooden Rowboat into:
   `Content/Melodia/Traversal/Starskiff/Test/ReferenceBoat/`
2. Use real-world scale; do not arbitrarily scale by eye until Melusina is standing beside it.
3. Create simple collision appropriate for buoyancy and rider blocking.
4. Place Melusina's actual skeletal mesh beside/in it.
5. Establish:
   - rider root location
   - seat/standing position
   - feet clearance
   - skirt/Listening Hem clearance
   - bow visibility in gameplay camera
   - approximate waterline
6. Capture screenshots from front/side/top for later sculpt reference.

The reference rowboat should be ugly and disposable.

---

# 5. Planned Blueprint pipeline

## Ownership rule

**Oceanology owns water/environment contact. Starskiff owns traversal state. Existing Melodia systems own rhythm/Niagara/world authority.**

Do not make Oceanology vendor classes responsible for Melodia-specific outfit, party or Monolith logic.

## Core objects

```text
BP_Starskiff
  Pawn
  Owns possession, rider presentation, camera and high-level Starskiff API.

BPC_StarskiffMovement
  Actor Component
  Owns Starskiff traversal state machine and authored movement requests.

BPC_StarskiffOceanologyAdapter
  Actor Component preferred over direct vendor inheritance where practical.
  Reads/forwards the minimum plugin-facing buoyancy/water functionality required by Starskiff.
  Exact local nodes/classes must be verified against the UE 5.8 port.

BP_StarskiffRail
  Actor containing Spline + rail metadata.
  Authored Current Rail route; owns capture radius, direction, branch/exit metadata and presentation hooks.

BP_StarskiffAnchorPoint
  Optional authored anchor/stability target.
  Used by Mara's Anchor Brake / fixed-reference moments.

DA_StarskiffTuning
  Data Asset or equivalent tuning container.
  Holds speeds, acceleration, damping, rail capture/exit values, leap curve and camera tuning without hardcoding all values in the Pawn.
```

If a vendor sample boat Pawn is the fastest viable greybox, duplicate/derive only long enough to prove buoyancy; then isolate Melodia behavior behind the adapter/movement layer rather than permanently building game rules inside vendor code.

---

# 6. BP_Starskiff component sketch

Recommended component tree, adjusted to the exact Oceanology port:

```text
BP_Starskiff (Pawn)
  SceneRoot
  HullCollision
  ReferenceHullMesh / HeroHullMesh
  OceanologyBuoyancyComponent(s) or local equivalent
  BPC_StarskiffOceanologyAdapter
  BPC_StarskiffMovement
  RiderRoot
    MelusinaRiderMarker
  CameraRoot
    SpringArm
      FollowCamera
  VFXRoot
    WakeAttach
    FinLAttach
    FinRAttach
    SoundingBellAttach
  InteractionRoot
```

The final hero hull can replace `ReferenceHullMesh` without replacing the Pawn or movement logic.

---

# 7. Traversal state machine

Use an explicit enum/state variable such as:

```text
EStarskiffMode
  Disabled
  Skim
  RailCapture
  CurrentRail
  AnchorBrake
  SoundingLeap
  BellwakeDrift
```

## Enter Skim

```text
MountStarskiff(Melusina)
  -> attach/pose rider
  -> disable normal character locomotion input
  -> add IMC_Starskiff
  -> possess BP_Starskiff or route control through agreed possession architecture
  -> set mode = Skim
  -> Oceanology adapter active
```

## Skim tick / movement request

```text
Input throttle/steer
  -> BPC_StarskiffMovement builds desired forward/yaw request
  -> Oceanology adapter provides water-contact/buoyancy foundation
  -> movement applies authored propulsion/steering
  -> damp pitch/roll for readable fantasy handling
  -> update wake/audio/camera parameters
```

Prioritize fun/readability over naval simulation.

## Rail capture

```text
Starskiff overlaps BP_StarskiffRail capture volume
  AND player presses/holds Attune
  AND mode == Skim
    -> cache current linear velocity
    -> choose spline input key / direction
    -> set mode = RailCapture
    -> blend toward rail frame over short authored curve
    -> on blend complete: mode = CurrentRail
```

## Current Rail

```text
Each update:
  target transform = spline transform at progress
  speed input adjusts rail speed within limits
  steer input becomes lateral bias / lean / branch preference
  maintain readable player agency
  allow authored exit windows
```

The rail must feel like **riding a current**, not entering a cutscene.

## Anchor Brake

```text
Press Anchor while in Skim or valid CurrentRail window
  -> validate Mara/anchor availability
  -> set mode = AnchorBrake
  -> smoothly converge to water/current-relative anchor frame
  -> suppress drift without freezing visuals
  -> hold until release/timeout/event
  -> return to prior valid mode
```

This is Mara establishing a temporary reference frame, not a car handbrake.

## Sounding Leap

```text
Press Leap in valid state
  -> set mode = SoundingLeap
  -> preserve horizontal momentum
  -> apply tuned vertical + forward impulse/curve
  -> temporarily reduce water adhesion/contact correction
  -> airborne camera/VFX response
  -> detect safe recapture/contact
  -> blend back to Skim or CurrentRail
```

Reliable recapture is a hard gate before hero sculpt polish.

## Bellwake Drift

Do not expose as a dock tutorial ability.

P1 climax only:

```text
Monolith/EncounterDirector exposes Bellwake current
  -> Shorelistener/party resonance validates it
  -> Starskiff captures impossible current
  -> mode = BellwakeDrift
  -> stronger authored camera + VFX + speed envelope
  -> route culminates in Look Back reveal
```

---

# 8. Enhanced Input plan

Create a dedicated context such as `IMC_Starskiff`.

Recommended actions:

```text
IA_StarskiffThrottle
IA_StarskiffSteer
IA_StarskiffLeap
IA_StarskiffAnchor
IA_StarskiffAttune
IA_StarskiffInteract
IA_StarskiffDismount
```

Suggested prototype mapping:

```text
W / RT          Throttle
S / LT          Slow / low-speed reverse
A,D / LS        Steer; rail lateral bias when captured
Space / South   Sounding Leap
Q / LB          Anchor Brake
Shift / RB      Attune / Current Rail capture
E               Contextual Mara Tune / interaction
F               Dismount in safe states
```

When mounting, add the Starskiff context and suppress conflicting character movement mappings. On dismount, restore character contexts deterministically.

---

# 9. Party/system hooks

Keep character identity outside raw vehicle physics.

## Melusina / Shorelistener

Provides:
- Tide Seam perception
- permission/presentation for authored Current Rail discovery
- Bellwake interpretation

Vehicle should receive a simple high-level result such as `RailRevealed` or `BellwakeAvailable`; it should not inspect outfit internals every tick.

## Mara

Provides:
- Anchor Brake availability
- tune/calibration interactions
- narrative/field instrumentation

Vehicle should call a stable interface/event such as `RequestAnchorReference`, not directly depend on Mara animation internals.

## Sir Melodious

Provides:
- resonance preview
- anomaly response
- safe-route/pulse presentation cues

Do not make basic vehicle steering depend on his animation/audio assets.

## P1 Encounter Director

`BP_ReefLooksBack_EncounterDirector` may:
- expose/enable rails
- change route availability
- trigger chromatophore/environment response
- unlock Bellwake Drift for the climax

It should not replace the Starskiff state machine.

---

# 10. Oceanology adapter boundary

The adapter exists because the 5.8 port may diverge from public documentation.

Only expose the smallest API Starskiff needs, for example:

```text
IsWaterContactValid()
GetWaterSurfaceLocationAndNormal()
SetBuoyancyEnabled(bool)
SetWakeIntensity(float)
RequestForwardPropulsion(float)
RequestSteering(float)
ResetWaterContact()
```

These names are **design-facing placeholders**, not claims about Oceanology's shipped API. The gameplay agent must map them onto exact locally available plugin functions/components after inspection.

Do not scatter vendor-specific calls throughout `BP_Starskiff` and P1 encounter graphs.

---

# 11. First greybox acceptance test

The first useful build is not beautiful.

It passes when all are true:

- [ ] Melusina mounts and dismounts without input-context corruption
- [ ] reference hull floats stably on representative Oceanology waves
- [ ] rider pose/camera/waterline are believable
- [ ] throttle and steering feel responsive
- [ ] no car wheel/suspension physics are used
- [ ] one `BP_StarskiffRail` captures cleanly
- [ ] player retains meaningful input while on the rail
- [ ] rail exit returns to stable Skim
- [ ] Anchor Brake creates a readable fixed-reference pause
- [ ] Sounding Leap lands and recaptures water reliably
- [ ] Wakebound skirt/hem can survive maximum expected rider lean without catastrophic clipping
- [ ] logic is separated enough that replacing the rowboat mesh does not require rewriting traversal

Only after this gate: freeze hero proportions.

---

# 12. Starskiff hero-mesh handoff after gameplay gate

Once the greybox is approved:

1. Duplicate reference dimensions into a Blender/ZBrush blockout scene.
2. Keep gameplay collision/waterline dimensions as the non-negotiable envelope.
3. Replace the donor silhouette with a newly authored form:
   - recognisable small skiff at gameplay distance
   - manta/hydrofoil planform below/around the hull
   - broad sea-glass resonance fins
   - Mara sounding/calibration hardware
   - pearl lacquer and Melusina tide-reactive material lines
4. Avoid literal animal face/eyes.
5. Keep rider hand/foot and camera occlusion zones clean.
6. Separate meshes:
   - rigid hull
   - simple collision hull
   - resonance fins
   - sounding/anchor hardware
   - optional tiny articulated fin rig
7. Replace `ReferenceHullMesh` in `BP_Starskiff`; do not replace the Pawn.
8. Re-test waterline and all traversal modes before detail baking.

---

# 13. Wakebound PC assembly sequence

1. Import Melusina's actual body/avatar into CLO at verified scale.
2. Fit the FV2 Puffed-Sleeve Blouse.
3. Reshape torso toward Melusina's existing fitted/puff silhouette rather than accepting the donor design.
4. Fit/shorten Gather Skirt for traversal.
5. Add **one** asymmetric Listening Hem using chiffon-like simulation.
6. Test neutral standing pose.
7. Test Starskiff seated/standing/riding lean poses before detail.
8. Freeze cloth only after rider clearance works.
9. Export to Blender/ZBrush.
10. Hand-sculpt painterly folds, scallops and silhouette exaggeration.
11. Reuse/modify Melusina's existing boots rather than replacing her whole visual language.
12. Model rigid survey pieces separately:
    - Tide-Marked Brooch
    - harness
    - pouches
    - brass fasteners
    - depth graduations
    - reinforced cuffs/gloves
13. Skin and re-test maximum Starskiff lean.

Visual target remains:

> **~70% Melusina / ~20% Shorelistener / ~10% Mara engineering.**

---

# 14. Minimal P1 build order after assembly

```text
1. Oceanology sample-vessel verification
2. Reference rowboat import
3. BP_Starskiff possession + camera
4. Oceanology buoyancy/contact
5. Skim
6. BP_StarskiffRail + capture/exit
7. Anchor Brake
8. Sounding Leap
9. Wakebound ride-pose cloth test
10. Freeze Starskiff envelope
11. Hero Starskiff sculpt
12. Final Wakebound sculpt
13. P1 Glassgarden rail blockout
14. Sir Melodious resonance cue
15. Mara tune/anchor presentation
16. Bellwake Drift
17. Look Back climax
```

Do not reverse this order by polishing the boat before steps 1–9 are stable.

---

# 15. First PC checklist — copy/paste

```text
[ ] Pull docs/p1-monolith-character-concepts-2026-08-28
[ ] Open STARSKIFF_WAKEBOUND_ASSET_AND_VEHICLE_PLAN_2026-08-28.md
[ ] Download free Wooden Rowboat
[ ] Download CLO FV2 Puffed-Sleeve Blouse
[ ] Download CLO FV2 Gather Skirt
[ ] Download House of U chiffon
[ ] Record licences/provenance
[ ] Inspect Oceanology 5.8 sample vessel locally
[ ] Record exact local Oceanology classes/nodes
[ ] Import rowboat into Starskiff/Test/ReferenceBoat
[ ] Fit Melusina against hull
[ ] Create BP_Starskiff
[ ] Create BPC_StarskiffMovement
[ ] Create BPC_StarskiffOceanologyAdapter
[ ] Create IMC_Starskiff + input actions
[ ] Prove mount/dismount
[ ] Prove Oceanology water contact
[ ] Prove Skim
[ ] Create one BP_StarskiffRail
[ ] Prove rail capture/ride/exit
[ ] Prove Anchor Brake
[ ] Prove Sounding Leap + water recapture
[ ] Fit Wakebound CLO block to Starskiff rider pose
[ ] Freeze hero hull/rider envelope
[ ] Begin final Starskiff sculpt
```

---

## Non-goals for the first PC assembly

Do not add yet:
- custom global buoyancy framework
- wheeled Chaos Vehicle inheritance
- free-roam flight
- full naval simulation
- combat from the Starskiff
- procedural rails
- multiple vehicles
- underwater Starskiff mode
- final ornate hero mesh before greybox acceptance
- new global rhythm or water authority

The P1 objective is one authored magical traversal route that feels unmistakably Melodia and makes the Reef That Looks Back reveal possible.
