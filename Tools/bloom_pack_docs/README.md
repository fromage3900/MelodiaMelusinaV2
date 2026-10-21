# Resonant Blooms — a musical flower generator for Blender (Geometry Nodes)

Procedural roses, peonies, melody vines and loose petals. Every flower is built from whorls of one shared petal placed at
the **golden angle**, with Fibonacci petal counts, and a single **Growth** dial that takes it from bud to full bloom.

**Requires Blender 5.2 or newer** (node groups are authored on 5.2 and will not open in older versions).

## What is in the box

| File | What it is |
|---|---|
| `ResonantBlooms.blend` | The asset library: 4 node groups + 4 materials, all marked as assets. Add this folder in *Preferences ▸ File Paths ▸ Asset Libraries*, or just `File ▸ Append` the node groups. |
| `ResonantBlooms_Demo.blend` | A lit demo scene: bud / half / full roses and peonies, two vines. |
| `previews/` | Renders of the demo scene. |
| `source/` | The Python that builds the node groups (readable, editable — see `EXTENDING.md`). |

## Quick start

1. Open `ResonantBlooms_Demo.blend` and drag the **Growth** slider on any flower's *Bloom* modifier.
2. To use in your own scene: add any mesh object (an empty mesh is fine), add a **Geometry Nodes** modifier, and pick
   `Bloom_Rose`, `Bloom_Peony`, `Bloom_Vine` or `Bloom_Petal`. The bundled materials are filled in as defaults.
3. Change the `Seed` for a different flower. Same seed = same flower.

## The node groups

### Bloom_Rose  ("Resonant Rose") and Bloom_Peony  ("Cadence Peony")
Rose: 4 whorls of 3 / 5 / 8 / 13 petals. Peony: 5 whorls of 5 / 8 / 13 / 21 / 21 petals. Each whorl is rotated by the
golden angle (137.5077°) relative to the one inside it. Outer whorls open first, inner whorls last.

| Input | Meaning |
|---|---|
| Growth (0–1) | 0 = tight bud, 1 = full bloom. Animatable. |
| Seed | Random variation of petal angle / tilt. |
| Scale | Overall size (1 = rose bloom about 29 cm wide, peony about 44 cm wide, 22 cm stem; scene units are metres). |
| Length, Width | Petal proportions. |
| Ruffle | Wavy petal edge. |
| Thickness | Petal thickness (the petals are solid, not planes). |
| Stem Length, Stem Radius | Stem and calyx. |
| Petal / Accent / Stem Material | Material pickers. Petal = petals, Accent = stamens, Stem = stem + calyx. |

### Bloom_Vine  ("Melody Vine")
A swaying vine whose **length is the Growth value** (0 = nothing, 1 = full length), with leaves and curling tendrils placed on
`Notes` points along it. Leaves and tendrils unfurl as the vine reaches them.
Inputs: Growth, Seed, Vine Length, Vine Radius, Notes, Sway, leaf Length / Width / Ruffle / Thickness, 3 materials.

### Bloom_Petal
One curled petal, for scattering or particle petal-fall.

## Colour

Petals read a vertex-colour attribute named **`GrowthCol`**:
`R` = how late this petal opens, `G` = which whorl (0 inner … 1 outer), `B` = distance from the flower's centre, `A` = 1 on petals and 0 on stem / stamens / calyx.
The bundled petal materials use `B` to blend centre → edge colour (open the material and edit the colour ramp).
Because it is a colour attribute it also survives FBX/glTF export, so game engines can use the same masks.

## Performance

Rose ≈ 9.5k triangles, Peony ≈ 22k triangles, Vine ≈ 9k triangles at defaults. They are evaluated live; use *Realize* /
*Apply* the modifier when you are done editing, or lower petal grid resolution in `source/blooms.py` for scatter work.

## Known limits (v0.1)

* The open rose is a shallow saucer rather than a deep bowl; peony outer petals can look flat at Growth 1.
* One petal shape per flower (whorls differ by size, tilt and position, not shape).
* Blender 5.2+ only.

## Credits & licence

All geometry nodes, materials and Python were authored for this product. No third-party assets are included.
Licence terms: see `LICENSE_DRAFT.txt` (draft — to be finalised by the seller before release).
