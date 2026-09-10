# Infinity Nikki Musical Decoration System — 2026-09-06

**Status:** Full system built, registered, and applied to Study
**Pipeline:** mesh-curve (guide curve → resample → instance → offset → realize → join)
**Nodes:** All native 5.2 — no Higgsas dependency

---

## Builders Registered (7 new)

| Builder | ID | Technique | Purpose |
|---|---|---|---|
| Nikki Star Pendant | `MEL_nikki_star_pendant` | Curve Star → tube | Tuned star tines along eave |
| Nikki Heart Filigree | `MEL_nikki_heart_filigree` | IcoSphere + cone pair | Heart tokens above windows |
| Nikki Wall Beads | `MEL_nikki_wall_beads` | Vertical bead strings | Rhythm spacing on wall siding |
| SDF Star Panel | `MEL_sdf_star_panel` | Grid + Boolean Difference | Star-shaped void in panel |
| Heart Chain | `MEL_heart_chain` | Line + Instance + Scale | Progressive shrink chain |
| Note Head Filigree | `MEL_note_head_filigree` | Store Named Attribute | Semitone data for shaders |
| Capture Filigree | `MEL_capture_filigree` | Capture Attribute | Curve tangent for width |

---

## Applied to Study (Roof_Main modifier stack)

1. `GN` — base roof (catenary splines, 43 nodes)
2. `Beads_Catenary` — bead dangle from eave guide
3. `Star_Pendants` — star pendants along eave
4. `Heart_Filigree` — heart filigree above windows
5. `Wall_Beads_0/1/2` — vertical bead strings (3 bays)
6. `Star_Pendants_Full` — full star pendant guide
7. `Heart_Filigree_Full` — full heart filigree guide
8. `Wall_Beads_Full_0/1/2` — full wall bead strings
9. `Filigree_Spiral` — capture attribute spiral

**Saved to:** `Saved/MelusinasHouse/Melusinas_Study_FullNikkiDecorated.blend`

---

## The Mesh-Curve Pipeline

```
Guide Curve (Curve object, parented, non-destructive)
  → Resample Curve (Count = musical divisor: 12 chromatic, 7 diatonic)
  → Instance On Points (Star / Heart / Bead template)
  → Scale Instances (L ∝ √(f_ref/f) from chime_row.py)
  → Set Position (Offset down for dangle)
  → Realize Instances
  → Join with original geometry
```

**Key insight:** separate guide curve objects, NOT mesh→curve extraction. The old `Mesh → Curve` approach extracted every edge and created a duplicate roof made of beads. The guide curve is authored once, parented to the roof, swappable, animatable.

---

## Files Changed

- `deploy/surreal_arch/melodia_gn/nikki_musical_decorations.py` — 3 builders (star/heart/beads)
- `deploy/surreal_arch/melodia_gn/nikki_advanced_decorations.py` — 4 builders (SDF/chain/note/capture)
- `deploy/surreal_arch/melodia_gn/__init__.py` — registered both modules
- `Saved/MelusinasHouse/Melusinas_Study_FullNikkiDecorated.blend` — saved result
- `Docs/Production/INFINITY_NIKKI_MUSICAL_DECORATIONS_2026-09-06.md` — closeout

---

## Next Steps

1. Apply materials (GoldBrass stars, AquaGlass hearts, PearlPlaster beads)
2. Add interior dressing moments (reading nook, music corner, display pedestal, wardrobe hook)
3. Extend to full facade (all wall sections, not just Roof_Main)
4. Connect to allee ribbon path spine
5. Render verification screenshots
6. Sync to C: / AppData
