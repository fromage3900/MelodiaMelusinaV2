# Starskiff + Wakebound Survey Set — Asset Sourcing and Vehicle Plan

Date: 2026-08-28
Status: P1 production plan / docs-only
Branch: `docs/p1-monolith-character-concepts-2026-08-28`
Related: PR #25, Issue #26, `P1_REEF_THAT_LOOKS_BACK_PLAN_2026-08-28.md`

## Decision

Do **not** build the Starskiff from Unreal's wheeled-car physics template and do **not** ship a marketplace boat with cosmetic changes.

Use a **hybrid hero-asset workflow**:

1. Acquire one inexpensive/free real skiff/rowboat mesh for scale, waterline, rider position, collision reference, and mundane hull proportions.
2. Acquire one manta-ray mesh for underside/fin/anatomical reference only.
3. Build a new visible Starskiff hero shell around Melodia's language: **small skiff + manta/hydrofoil + hydrographic instrument**.
4. Use Oceanology NextGen's own pontoon buoyancy / vessel support as the water-contact foundation.
5. Put Melodia-specific traversal in a dedicated Starskiff Pawn/movement layer: **Skim, Current Rail, Anchor Brake, Sounding Leap, Bellwake Drift**.

The goal is to prototype a Melodia traversal system first and a boat second.

---

## Direct asset shortlist — Starskiff sculpt/blockout

### A. Recommended blockout hull: Wooden Rowboat — FREE
https://www.fab.com/listings/59573310-9be8-459f-98cb-954a66e5ef2c

Why:
- free
- real dimensions / centimetre units
- approximately 6.7k polygons
- FBX/OBJ/GLB formats
- clean enough to establish rider height, waterline, bow/stern proportions and collision

Use as **throwaway greybox/reference**, not final visible art.

### B. Higher-detail skiff reference: 13 ft Wooden Skiff
https://www.fab.com/listings/5432a3e7-d97f-4f34-a682-8e88d19f7d29

Why:
- explicit 13-foot skiff proportions
- flat-bottom/sheet-construction hull
- ~22k tris
- FBX/OBJ/Blender
- useful for believable underside, seat height, gunwale and waterline proportions

Use if the free boat is too generic for close proportion study.

### C. Manta anatomy / fin-motion reference
https://www.fab.com/listings/a430d1e9-b2e8-4b44-b699-bc6b2c2698c9

Why:
- game-ready manta
- rigged
- 3 LODs
- useful to inspect broad pectoral-fin planform and underside rhythm

Do **not** literally graft a manta onto a boat. Abstract the anatomy into the hull/fin language.

### D. Optional mechanical/helm donor
https://www.fab.com/listings/b13b2535-0dba-4157-9df2-36e1c6527d9f

Use for scale/reference or kitbash of a compact marine control, then redesign into Mara's sounding/calibration hardware.

### E. Ultra-light alternative reference hull
https://www.fab.com/listings/da1983c5-212d-4c9f-94bb-aa7ded2ff0e6

~3.5k-poly rowboat with FBX/OBJ. Useful if a minimal collision/LOD donor is preferable.

### Licensing rule
Verify the selected Fab licence at acquisition and record the licence/source in project provenance. Purchased/downloaded hulls are reference/kitbash inputs; the final hero silhouette should be newly authored.

---

## Direct asset shortlist — Wakebound Survey Set / CLO

Wakebound art rule remains:

> **~70% Melusina / ~20% Shorelistener / ~10% Mara engineering.**

Do not turn Melusina into a naval/steampunk character.

### A. Free official FV2 Puffed-Sleeve Blouse
https://connect.clo-set.com/ko/detail/579f920f3ec84df39c1c59833fab97f6

Best base for preserving Melusina's established puff-sleeve language while building a more field-ready torso.

### B. Free Button-Front Puff Sleeve Peplum Blouse / Lace Trim
https://connect.clo-set.com/detail/bb8faa04606341919f8b12ca6e6f9e28

Useful alternate because the fitted torso + peplum already approaches Melusina's sculpted garment proportions.

### C. Free FV2 Gather Skirt
https://connect.clo-set.com/portfolio/208988/collection/collections/221102e3493f8866b34c9f868d88727b3021e7?itemId=a508038e5c834127989c4e0901e5743d

Use as a neutral structural skirt block. Shorten and redesign; do not inherit the final silhouette.

### D. Free official KOFOTI/FV2 female pattern collection
https://connect.clo-set.com/portfolio/208988/collection/collections/2411DDd4ef97a73b324c89a9ee160a79c5d76d

Contains free Puffed-Sleeve Blouse, A-Line Midi Skirt, Princess Line Coat/Jacket and other useful blocks.

### E. Free House of U 2150 U-circular Chiffon
https://connect.clo-set.com/detail/725ae2c9ff524b2ead1795b49071fcf4

Use to discover the drape/flaring behaviour of the translucent **Listening Hem** before deliberately stylizing it in ZBrush/Blender.

### F. Free FV2 Princess Line Jacket
https://connect.clo-set.com/ja/detail/25a76259a8344989abb862b6c5338c98

Optional donor for the small Mara-influenced survey capelet/jacket construction.

### Wakebound pieces to model/sculpt directly
- Tide-Marked Brooch / receiver
- Survey Harness and small pouches
- brass fasteners and depth graduations
- gloves/cuffs
- reinforced boots using Melusina's existing boots as the base
- asymmetric translucent Listening Hem
- ornamental tide motif / embroidery

Do not waste CLO time on rigid accessories.

---

## Oceanology vehicle foundation

Oceanology NextGen documentation:
https://galidar.com/oceanology-nextgen

The current docs describe:
- pontoon-based buoyancy for vessels
- `AutoConfigurePontoons` based on hull collision geometry
- force-based ship navigation along splines / FlowController
- vessel wakes / foam integration

Therefore: **prototype with Oceanology's buoyancy first before writing custom floating physics.**

Important local caveat: this project uses a locally ported UE 5.8 build. Public Oceanology docs currently list official NextGen support through UE 5.7, so exact Blueprint/C++ API names must be verified in-editor against the port rather than assumed from public docs.

Oceanology remains the water/environment authority. Starskiff owns traversal state.

---

## Vehicle architecture

### Do not inherit car physics
The UE Vehicle Template is useful only for:
- possession
- Enhanced Input organization
- spring-arm/camera conventions
- mount/dismount UX
- debug HUD ideas

Do not inherit wheel/suspension assumptions.

### Recommended runtime objects

```text
BP_Starskiff                      // Pawn / possession + presentation
BPC_StarskiffMovement             // Melodia-specific traversal state machine
BP_StarskiffOceanologyAdapter     // thin plugin-facing water query/buoyancy adapter
BP_StarskiffRail                  // Current Rail authored spline/data
BP_StarskiffAnchorPoint           // optional authored stability/interaction point
```

If Oceanology's own sample boat Pawn is clean and replaceable, it may be used as the **first greybox implementation donor**, but Starskiff-specific logic should be moved behind the Melodia movement/adapter boundary instead of permanently living inside vendor classes.

### Movement modes

```text
Disabled
  -> Skim
      -> RailCapture -> CurrentRail
      -> AnchorBrake
      -> SoundingLeap
      -> BellwakeDrift
```

#### Skim
Oceanology buoyancy + controlled propulsion and damped pitch/roll. Prioritize authored feel over naval simulation.

#### Current Rail
Spline/current becomes dominant; player retains speed, lean/lateral bias and branch choice. This is the main cinematic traversal tool for Glassgarden Shoals.

#### Anchor Brake
Mara establishes a temporary fixed reference. Converge smoothly toward an anchor/current-relative transform; it is not a normal handbrake.

#### Sounding Leap
Preserve horizontal momentum, apply an authored vertical/forward impulse, reduce water adhesion, then recapture Oceanology water on landing.

#### Bellwake Drift
P1 climax mode. The Monolith emits an impossible current; Starskiff learns to ride it. Do not present this as a generic boost at the dock.

---

## Input prototype

Use a dedicated Enhanced Input context while mounted.

```text
W / RT        throttle
S / LT        slow / low-speed reverse
A,D / LS      steer; lateral bias while on rail
Space / South Sounding Leap
Q / LB        Anchor Brake
Shift / RB    attune/capture Current Rail
E / contextual Mara Tune / interaction
F             dismount in safe states
```

Current Rail should change what steering means, not remove player agency.

---

## First implementation spike — do this before final sculpt

### Target
A rideable ugly prototype over the current P0 Oceanology ocean.

### Build
1. Import/download the free Wooden Rowboat.
2. Size it against Melusina's real skeletal mesh.
3. Establish rider socket/pose, camera and waterline.
4. Convert/copy the Oceanology example boat setup or add the same pontoon buoyancy mechanism.
5. Expose 3–5 stable water contact points: bow, stern L/R, optional fin L/R.
6. Add forward acceleration + steering.
7. Make one `BP_StarskiffRail` spline through a Sea Above/P1 test cove.
8. Add rail capture and exit.
9. Add one Anchor Brake point/state.
10. Only when this feels good, freeze final Starskiff proportions and start hero sculpt.

### Gate
Do not spend multiple days detailing the hero mesh until:
- skimming feels good
- rail capture feels magical rather than automated
- landing after a jump is reliable
- the camera reads the water/Monolith scale
- Melusina's outfit does not intersect the hull at maximum lean

---

## Hero sculpt plan

### Starskiff form hierarchy

1. **Real skiff read at gameplay distance** — clear bow, rider area, hull volume.
2. **Manta influence in plan/underside** — broad resonance fins, soft wing-like negative spaces.
3. **Mara engineering at close range** — sounding assembly, calibrated brass/glass, hydrographic markings.
4. **Melusina response layer** — pearl lacquer, sea-glass fins, tide-reactive material lines.

Avoid literal animal face/eyes. It should feel like an engineered object whose geometry has learned the language of a living current.

### Mesh split
- rigid static/Nanite-friendly hull where appropriate
- separate fin meshes or tiny skeletal rig only where articulation is visible
- separate sounding/anchor mechanism
- dedicated simple collision hull
- separate translucent resonance-fin material sections

---

## Wakebound sculpt plan

Start from Melusina's actual body + existing costume proportions.

1. Fit the puff-sleeve blouse block to her avatar.
2. Modify toward her recognizable fitted/puffed torso.
3. Use Gather/A-line logic for a shorter traversal skirt.
4. Add exactly one large asymmetric chiffon Listening Hem.
5. Freeze cloth once silhouette works.
6. Export to Blender/ZBrush.
7. Sculpt the painterly heroic folds and stylized scallops by hand.
8. Model survey hardware rigidly in Blender/ZBrush, not CLO.
9. Skin/test against Starskiff riding pose before final details.

Material zones:
- painterly main cloth
- pearl/iridescent Shorelistener carryover
- restrained aged brass/glass Mara hardware
- darker marine reinforcement at boots/cuffs/harness
- isolated translucent/cheap-fallback Listening Hem

---

## P1 integration sequence

1. Mara introduces/calibrates the prototype Starskiff after P0.
2. Player learns **Skim** at the survey dock.
3. Sir Melodious previews resonance before first rail.
4. Shorelistener reveals the first Tide Seam / Current Rail.
5. Mara teaches **Anchor Brake** at an unstable junction.
6. Player learns **Sounding Leap** across a broken reef gap.
7. Reef performs kilometre-scale chromatophore pulse.
8. A new impossible current appears that Mara's model cannot explain.
9. Melusina rides it: **Bellwake Drift** is learned from the Monolith itself.
10. Elevated Look Back reveal.

This keeps the mount mechanically tied to the party:

> **Melusina perceives the route. Mara tunes/stabilizes the reference. Sir Melodious previews resonance. The Starskiff makes it traversable.**

---

## Immediate purchase/download order

1. **Download the free Wooden Rowboat** first. No reason to spend money before the rideable greybox proves scale.
2. Download the free CLO Puffed-Sleeve Blouse, Gather Skirt and chiffon.
3. Prototype Oceanology buoyancy using the sample/boat setup already shipped with the plugin if available locally.
4. Only buy the detailed 13 ft skiff if the free rowboat does not answer the proportion questions.
5. Manta asset is optional; useful mainly if its rig/shape speeds fin/underside study.
6. Do not buy a large vehicle framework unless Oceanology's included boat foundation proves inadequate.

---

## Agent handoff

### Gameplay agent
- inspect local Oceanology 5.8 port for sample boat / buoyancy classes and Blueprint nodes
- document exact classes/nodes actually present
- build `BP_Starskiff` greybox + dedicated input context
- prove Skim + one Current Rail before expanding
- do not create a second global water system

### Character-art agent
- use the listed CLO blocks
- preserve Melusina proportions and painterly silhouette
- test Wakebound against rider pose early
- keep Mara engineering to ~10% of the outfit's visual read

### Prop/vehicle-art agent
- use reference hull only for dimensions/waterline
- author a new Starskiff silhouette
- lock hull/rider contact before detail
- separate articulated fins/hardware from rigid hull

### Tech-art/VFX agent
- reuse existing water/Niagara authority
- add wake/rail/anchor/Bellwake presentation only after state transitions are stable
- make translucent fin/hem sections isolated and replaceable with cheaper masked fallbacks

---

## Definition of P1 traversal MVP

P1 traversal is prototype-ready when:
- Melusina can mount/dismount the Starskiff
- Oceanology water contact survives representative P1 waves
- Skim feels responsive
- one authored Current Rail can be captured, ridden and exited
- Anchor Brake creates a useful stable pause
- Sounding Leap lands reliably
- Wakebound silhouette survives the ride pose
- Sir Melodious/Mara hooks can be called without vehicle logic depending on their animation/audio internals
- no new global water/rhythm authority has been introduced

Bellwake Drift and final hero art come after this gate.