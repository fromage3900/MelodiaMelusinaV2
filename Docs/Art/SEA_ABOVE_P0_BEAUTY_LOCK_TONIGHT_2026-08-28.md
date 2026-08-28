# Sea Above P0 — Beauty Lock for Tonight

**Date:** 2026-08-28  
**Purpose:** protect the first public slice from feature creep while making it feel authored, expensive and unmistakably Melodia.

> **P0 is successful when the player believes the landscape for long enough that the biological reveal changes what they thought they were looking at.**

---

## The five-image experience

P0 only needs five unforgettable visual states.

### I — CERULEAN LITTORAL

**Read:** “I want to stay here.”

- clean, serene Oceanology surface
- warm/cool painterly shore value grouping
- visible authored foreground rocks / plants / cloth motion
- horizon extremely calm and readable
- Melusina is a small, colorful human-scale anchor
- Shorewake is mostly ordinary cloth here

**Do not foreshadow with horror.** Foreshadow with impossible consistency.

---

### II — THE WORLD IS SLIGHTLY WRONG

**Read:** “Did the water just…?”

Use three quiet anomalies, not twelve:

1. one cluster of droplets travels upward;
2. one distant school / debris motion violates expected vertical direction;
3. Shorewake hem leans toward an invisible line instead of the wind.

Keep normal nearby motion intact. The anomaly is powerful because most of the simulation still behaves beautifully.

---

### III — SECOND HORIZON

**Read:** “There is another ocean under the ocean.”

The visual hierarchy:

```text
real horizon                  high contrast / normal response
fog/depth gap                 soft loss of information
false second horizon          unnaturally coherent
false ocean field             nearly still
Bell proxy                    not yet readable as anatomy
```

**Critical scale trick:**

```text
foreground movement      normal
mid-distance movement    slower
false horizon movement   almost none
Bell movement            barely perceptible
```

The more enormous something is, the less screen-space motion it needs.

Never reveal the Bell perimeter.

---

### IV — THE BELL BREATHES

**Read:** “The landscape is anatomy.”

Use one pulse rather than a boss attack.

Suggested prototype curve:

```text
0.0 s     0.00
6.0 s     ~0.00
8.0 s     0.18
9.2 s     1.00
10.8 s    0.35
16.0 s    0.00
```

Coordinate:

- Bell membrane opacity / Fresnel response
- low-frequency interior color shift
- upward droplets
- a restrained water/fog light response
- Shorewake clasp + tide line response at low amplitude
- one audio/rumble/breath event

The Bell is allowed to be strange; the camera is not. Keep the camera readable and let the environment do the impossible thing.

---

### V — AFTERMATH

**Read:** “It is still there.”

Do not immediately explain the organism.

- world settles
- false horizon remains
- one tiny upward droplet persists
- Shorewake hem takes a beat longer to return to normal
- optional distant survey instrument / Mara foreshadowing can report an impossible value without introducing her fully

End while the player wants to move toward the answer.

---

# P0 layer contract

```text
┌──────────────────────────────────────────────┐
│ SKY / ATMOSPHERE                             │
├──────────────────────────────────────────────┤
│ REAL OCEAN — gameplay water authority        │
│ Oceanology / existing Melodia water seams    │
├──────────────────────────────────────────────┤
│ FOG / DEPTH GAP — information is removed     │
├──────────────────────────────────────────────┤
│ FALSE OCEAN — presentation-only plane        │
│ almost-still second horizon                  │
├──────────────────────────────────────────────┤
│ BELL MEMBRANE — giant organism proxy         │
│ never show complete edge                     │
├──────────────────────────────────────────────┤
│ OPTIONAL UNDER-SKY CARDS / VOLUME CUES       │
└──────────────────────────────────────────────┘
```

**False ocean is never a Water Body, Water Zone or gameplay interaction authority.**

---

# Bell shader: one elegant material, not a water clone

Suggested dedicated family:

```text
M_SeaAbove_BellMembrane_Prototype
MI_SeaAbove_BellMembrane_Hero
```

Inputs:

```text
SeaAbovePulse           0–1
BellTintDeep
BellTintPearl
FresnelExponent
MembraneOpacity
InteriorNoiseScale
InteriorNoiseSpeed
PulseEmission
PulseWPO
```

Core:

```text
F = Fresnel
N = two low-frequency panning noises
Pulse = SeaAbovePulse

BaseColor = lerp(BellTintDeep, BellTintPearl, N * 0.25 + F * 0.25)
Opacity = BaseOpacity + F * RimOpacity + Pulse * PulseOpacity
Emissive = BellTintPearl * Pulse * PulseEmission * subtle interior mask
WPO = VertexNormalWS * N * Pulse * very_small_amount
```

The membrane must read as **volume and tissue at geographic scale**, not as a force field.

Do not add red/gore to P0. The first realization should remain beautiful.

---

# Shorewake coordination

See `SHOREWAKE_DRESS_P0_SHADER_COOKBOOK_2026-08-28.md`.

The outfit response should be staged beneath the world response:

```text
Bell hero intensity          1.00
false horizon                0.70
upward droplets              0.45
Shorewake horizon line       0.25
Shorewake clasp              0.18
rhythm micro-pulse           0.08
```

These are **relative visual priorities**, not literal shader multipliers.

The player should remember the Bell, then later realize the dress had been telling them the truth first.

---

# One-night Niagara pass

Use a single prototype system if needed:

```text
NS_SeaAbove_UpwardDroplets_Prototype
```

Desired controls:

```text
User.SeaAbovePulse
User.SeamProximity
User.UpDirection
User.SpawnScale
```

Behavior:

- sparse before reveal;
- stronger during Bell pulse;
- movement biased upward / toward the impossible sea;
- some particles slow near the false horizon;
- no giant splash spam;
- no unrelated glitter field.

The current project-wide Niagara fanout actor owns shared `User.*` rhythm/VFX fanout. Do not create a second shared global broadcaster just for P0.

---

# Lighting lock

P0 lighting should support a **serene-to-impossible** transformation without a hard cinematic relight.

### Before reveal
- soft readable directional light
- ocean specular controlled enough to preserve horizon silhouette
- fog gives depth rather than whitening the whole scene
- cyan/lavender accents appear in character, not everywhere

### During pulse
- prefer **localized membrane / fog / reflection response** over changing the entire sun/sky exposure
- protect Melusina skin values
- do not crush shoreline blacks
- keep the false horizon legible

### After pulse
- restore almost everything
- retain one tiny impossible cue

A global blue flash is cheap. A localized biological response feels authored.

---

# Camera lock

For the hero reveal:

- use a human-scale foreground reference: Melusina, rock, railing, grass or shore object;
- leave negative space around the second horizon;
- do not use an ultra-wide lens so extreme that it advertises “boss scale”; let the scale be inferred;
- avoid camera shake until after the player understands the shape change;
- if using a push-in, make it slower than expected.

**Never frame the complete Bell.** The player's mind should finish the organism.

---

# Audio lock

The ideal reveal stack:

```text
shore ambience
→ subtle high-frequency omission / quieting
→ low distant pressure tone
→ Bell pulse / breath
→ one delayed water response
→ ambience returns with a new, barely audible undertone
```

If the rhythm system participates, it should entrain the pulse subtly. Do not fake rhythm events from the Sea Above director.

---

# Tonight schedule

## 0–30 min — lock the picture

- choose one hero shoreline camera
- establish false horizon height
- tune fog gap
- ensure Bell perimeter cannot be seen
- take a screenshot before touching more systems

## 30–75 min — Bell pulse

- dedicated membrane material/MID
- local prototype timeline / director
- one opacity/Fresnel/interior response
- one pulse curve
- verify camera reads the reveal

## 75–120 min — Shorewake

- stable painterly fabric
- hero tide gradient
- separate translucent hem
- tiny wrong-gravity response
- stop before microdetail if the silhouette already sings

## 120–150 min — anomaly FX

- upward droplets
- one false-horizon accent
- one synchronized dress response

## 150–180 min — capture + package check

- run from player start
- no editor-only assumptions
- check exposure transitions
- check translucent sorting
- check shader compile warnings
- capture 3 stills + one short reveal clip
- package only after the visual spine works in PIE/Standalone

---

# Hard cut list for tonight

Cut immediately if it threatens the reveal:

- full Starskiff combat
- generic quest framework
- complex mount inventory
- new dialogue framework
- new water authority
- FLIP simulation experiments
- world partition architecture work
- broad C++ refactors
- outfit customization UI
- extra Bell attacks
- complete Monolith anatomy
- perfect Oceanology abstraction beyond the adapter seam

The Starskiff can prove **one current ride** later; it does not need to invade the Sea Above opening.

---

# P0 acceptance checklist

## World
- [ ] Real ocean looks intentional and stable
- [ ] False horizon reads as water before it reads as creature
- [ ] Fog separates the two water layers cleanly
- [ ] Bell perimeter is never visible
- [ ] Nearby/mid/far motion scales sell impossible size

## Reveal
- [ ] First 5–10 seconds can be mistaken for scenery
- [ ] Anomaly cues appear before anatomy
- [ ] Bell pulse has one unmistakable silhouette/value change
- [ ] Reveal remains beautiful rather than immediately grotesque
- [ ] Aftermath preserves uncertainty

## Melusina / Shorewake
- [ ] Character reads as young adult, painterly, handcrafted
- [ ] Outfit is simpler than future legendary looks
- [ ] Hem is the main magical material feature
- [ ] Tide line can align with second horizon
- [ ] No rhythm response overpowers world event

## Technical
- [ ] False ocean does not publish water gameplay samples
- [ ] No duplicate shared Niagara/rhythm bus
- [ ] No new C++ required for reveal
- [ ] Water V10 study line untouched
- [ ] No accidental per-frame MID creation
- [ ] Translucent hem tested against hair/ocean/fog
- [ ] Standalone test passes

---

# Final P0 rule

> **Do not add more until the second horizon is beautiful enough to stand still and stare at.**

If the player gets the serene coast, the impossible water and the Bell breath, P0 has already communicated the game's identity.
