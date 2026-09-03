# The God That Molts — Production Sheet

**Date:** 2026-08-29  
**Concept:** P1-03 — Exponentially larger shells; god too large to perceive  
**Source:** `Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md`  
**Status:** Build-ready — aquatic arthropod, sequential reveal, breathing, cathedral

---

## Core Phenomenon

Exponentially larger shells are discovered across the world. The actual organism may now be too large to perceive. The player walks through the interior of each shell — a cathedral of ribbed arches and bioluminescent veins. The god is still alive inside, breathing subtly. Each shell is revealed on beat, the camera pulling back to reveal the next larger shell.

---

## Body Map — Model vs. Implied

| Body Part | Approach | Asset | Instance |
|-----------|----------|-------|----------|
| Cephalon (head shell) | Modeled | Trilobite head, segmented, translucent | `BP_Cephalon_Shell` instance |
| Thorax (segmented body) | Modeled | Segmented shell arches, ribbed | `BP_Thorax_Segments` instance |
| Pygidium (tail shell) | Modeled | Tail fan, bioluminescent | `BP_Pygidium_Shell` instance |
| Shell interior | Modeled | Hollow cathedral, ribbed arches | `BP_Shell_Interior` instance |
| Biolum veins | Modeled | Glowing veins, breathing pulse | `BP_Biolum_Veins` instance |
| Fracture seams | Modeled | Crack lines, breaking open | `BP_Fracture_Seams` instance |
| Aftermath fragments | Modeled | Scattered old molt pieces | `BP_Aftermath_Fragments` instance |
| Gravity distortion | Implied | Spacetime warping volume | `BP_Gravity_Well` instance |
| The god itself | Implied | Never seen, only felt | Audio + haptic feedback |

---

## Scale Progression (4 instars)

| Instar | Scale | Size | Location | Feel |
|--------|-------|------|----------|------|
| 1 (recent molt) | Town | 50m | Village ruins | Fresh, translucent, delicate |
| 2 | Mountain | 500m | Mountain valley | Older, mineralized, ribbed |
| 3 | Region | 5km | Regional map | Ancient, cathedral-scale |
| 4 (current) | World | 50km | Planetary shell | The world IS the shell |

---

## Sequential Reveal Contract

| Beat | Reveal | Camera | Effect |
|------|--------|--------|--------|
| 1 | Instar 1 (town) | Close-up, walking through interior | Biolum veins pulse on beat |
| 2 | Instar 2 (mountain) | Pull back, reveal larger shell | Gravity shifts, new cathedral |
| 3 | Instar 3 (region) | Pull back further | Shell becomes the landscape |
| 4 | Instar 4 (world) | Planetary view | The world is inside the god |

---

## GN Builders

### 1. MEL_shell_cephalon
Trilobite head shell. Inputs: Scale, Segment Count, Chillum Opacity, Vein Glow. Translucent chitin with ribbed interior.

### 2. MEL_shell_thorax
Segmented thorax arches. Inputs: Segment Count, Arch Height, Rib Spacing, Breathing Speed. Cathedral ribbed arches.

### 3. MEL_shell_pygidium
Tail fan shell. Inputs: Fan Angle, Vein Density, Biolum Intensity, Pulse Phase. Bioluminescent tail.

### 4. MEL_shell_interior
Walkable hollow shell interior. Inputs: Wall Thickness, Arch Count, Vein Spacing, Cathedral Height. Sacred space.

### 5. MEL_fracture_seam
Crack lines where shell breaks open. Inputs: Crack Count, Crack Depth, Glow Leak, Decay Age. Breaking open.

### 6. MEL_biolum_vein
Glowing bioluminescent veins. Inputs: Vein Count, Pulse Speed, Color Shift, Breathing Depth. Living light.

### 7. MEL_gravity_well
Spacetime distortion volume. Inputs: Distortion Strength, Lens Radius, Chromatic Aberration, Breathing Pulse. Mass warps space.

### 8. MEL_aftermath_fragment
Scattered old molt fragments. Inputs: Fragment Count, Scatter Range, Decay Age, Chillum Remnant. Old shells.

---

## Material Instances (no new masters)

| Instance | Base Master | Key Params |
|----------|-------------|------------|
| `MI_Chitin_Translucent` | `MI_Master_Toon_Universal_Alpha` | Translucency 0.8, amber-blue tint, emission 0.5 |
| `MI_Biolum_Vein` | `MI_Master_Toon_Universal_Alpha` | Emission 2.0, blue-green, pulsing |
| `MI_Fracture_Glow` | `MI_Master_Toon_Universal_Alpha` | Emission 1.5, warm amber, crack glow |
| `MI_Cathedral_Stone` | `MI_Master_Nikki_Landscape` | Dark mineralized, ribbed normal, cool |
| `MI_Gravity_Distort` | Existing material | Chromatic aberration, lensing, distortion |

---

## Level Layout — LV_GodThatMolts_Prototype

```
Composition (sequential reveal, 4 stages):

  [STAGE 1] Instar 1 (Town Scale)
    Camera: Inside the shell, walking through cathedral
      |
    [Cephalon] — head shell, ribbed arches, biolum veins
      |
    [Thorax] — segmented body, breathing pulse
      |
    [Pygidium] — tail fan, glowing
      |
    [Fracture Seams] — cracks leaking light
      |
    BEAT → Camera pulls back, reveal larger shell

  [STAGE 2] Instar 2 (Mountain Scale)
    Camera: Pulled back, instar 1 is now a small shell inside instar 2
      |
    [Larger Cathedral] — same structure, 10x bigger
      |
    [Gravity Well] — subtle distortion around the mass
      |
    BEAT → Camera pulls back further

  [STAGE 3] Instar 3 (Region Scale)
    Camera: Regional view, shell is now landscape
      |
    [Cathedral Landscape] — ribs become valleys, veins become rivers
      |
    [Aftermath Fragments] — scattered old molts around the perimeter
      |
    BEAT → Camera pulls back to planetary

  [STAGE 4] Instar 4 (World Scale)
    Camera: Planetary view, the world IS the shell
      |
    [Planetary Shell] — world-scale chitin dome
      |
    [The God] — implied, never seen, only felt
```

---

## Rhythm + Fashion Integration

| System | Hook |
|--------|------|
| Sequential reveal | Each beat triggers next instar reveal |
| Breathing pulse | All biolum veins pulse with beat |
| Biolum intensity | Rhythm accuracy controls glow brightness |
| Cathedral acoustics | Reverb scales with shell size |
| Fashion | Reflective/chitin-textured clothing attracts the god's attention |
| Checkpoint | Rhythm beat at each stage transition |

---

## Evidence Standard

1. PIE session with sequential capture (4 stages)
2. Assertion report JSON next to captures
3. `Saved/gate_ledger.json` row for `god_that_molts_prototype`
4. SHA-256 hashes of new assets/instances

---

## Build Order

1. Production sheet (this doc) — DONE
2. GN builders (8 new) — ~3 hrs
3. Sequential stage file (4 stages) — ~1 hr
4. Evidence + ledger — ~15 min
