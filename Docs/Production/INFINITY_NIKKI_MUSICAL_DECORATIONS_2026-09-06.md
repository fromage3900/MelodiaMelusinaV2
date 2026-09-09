# Infinity Nikki Musical Decorations — 2026-09-06

**Status:** generators built and registered, applied to Study
**Pipeline:** mesh-curve (guide curve → resample → instance → offset → realize → join)

---

## What was built

Three new Melodia Studio GN builders in `melodia_gn/nikki_musical_decorations.py`:

| Builder | ID | Shape | Musical Function |
|---|---|---|---|
| Nikki Star Pendant | `MEL_nikki_star_pendant` | Curve Star → tube | Tuned tines (chime_row math) |
| Nikki Heart Filigree | `MEL_nikki_heart_filigree` | IcoSphere + cone pair | Resonance token above windows |
| Nikki Wall Beads | `MEL_nikki_wall_beads` | Vertical bead strings | Rhythm spacing on wall siding |

All native 5.2 nodes — no Higgsas dependency. Higgsas library not present on this machine (`G:\programs\BlenderPlugins\` absent).

---

## Application to Study

**Current modifier stack on Roof_Main:**
1. `GN` — base roof geometry (catenary splines, 43 nodes)
2. `Beads_Catenary` — bead dangle from eave guide curve
3. `Star_Pendants` — star pendants along eave guide
4. `Heart_Filigree` — heart filigree above windows
5. `Wall_Beads_0/1/2` — vertical bead strings at shoulder + center bays

**Saved to:** `Saved/MelusinasHouse/Melusinas_Study_Decorated.blend`

---

## The mesh-curve pipeline

```
Eave/Wall Guide (Curve object, parented, non-destructive)
  → Resample Curve (Count = musical divisor: 12 chromatic, 7 diatonic)
  → Instance On Points (Star / Heart / Bead template)
  → Scale Instances (L ∝ √(f_ref/f) from chime_row.py)
  → Set Position (Offset down for dangle)
  → Realize Instances
  → Join with original geometry
```

**Key insight:** separate guide curve object, NOT mesh→curve extraction. The old `Mesh → Curve` approach extracted every edge and created a duplicate roof made of beads. The guide curve is authored once, parented to the roof, swappable, animatable.

---

## Builder parameters

**MEL_nikki_star_pendant:**
- Pendant Count (3-50)
- Star Size (0.01-0.2)
- Drop (0.0-1.0)
- Point Count (3-12)
- Inner Ratio (0.1-0.9)

**MEL_nikki_heart_filigree:**
- Heart Count (1-30)
- Heart Size (0.01-0.2)
- Drop (-0.5 to 0.5)

**MEL_nikki_wall_beads:**
- String Count (1-10)
- Beads Per String (2-30)
- Bead Radius (0.005-0.1)
- String Drop (0.0-3.0)
- Spacing (0.1-2.0)

---

## Execution status

- [x] Fix duplicate bead-roof (guide curve extraction)
- [x] Build star pendant guide + modifier
- [x] Build heart filigree guide + modifier
- [x] Build wall bead string guides (3 bays) + modifiers
- [x] Register as Melodia Studio builders (`nikki_musical_decorations.py`)
- [x] Save decorated blend
- [ ] Apply materials (GoldBrass stars, AquaGlass hearts, PearlPlaster beads)
- [ ] Add to Study interior (reading nook, music corner, display pedestal, wardrobe hook)
- [ ] Sync to C: / AppData
- [ ] Verify in GUI after addon reload

---

## Next steps

1. Reload addon in Blender GUI to see the new builders in GN Stack
2. Apply materials from the 6-material palette
3. Extend to the full facade (all wall sections, not just Roof_Main)
4. Connect to the allee ribbon path spine
5. Render verification screenshots
