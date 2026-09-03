
---

## 6. Shirt tuning result (executed 2026-09-03, measured)

Target = Blender reference torso region, mean RGB **(128, 102, 165)**, luminance **51.6%**.
Measurement = fixed torso region x480-620, y450-700 of the standard capture recipe.

| step | TextureWeight | DreamTint | measured | luminance | abs error |
|---|---|---|---|---|---|
| before | 1.796 | 1.00 / 0.85 / 0.92 | (56, 49, 94) | 26.0% | 196 |
| 1 | 1.796 | 2.06 / 1.77 / 1.56 | (80, 69, 105) | 33.2% | 141 |
| 2 | 0.80 | 2.06 / 1.77 / 1.56 | (111, 105, 116) | 43.4% | 69 |
| **final** | **0.80** | **2.37 / 1.72 / 2.22** | (111, 104, 122) | 44.1% | **62** |

**`TextureWeight` is the lever, not `DreamTint`.** Tint alone asymptotes near 38%
luminance however far it is pushed — doubling it bought only 1.35x output. Lowering
`TextureWeight` lets the tint carry the value.

**Residual gap is almost entirely blue** (122 vs 165). Raising the blue tint 42% moved
the result 6 points, so the toon master resists saturation at this weight. Closing it
properly needs the **albedo texture** brightened — `T_Melusina_UpdatedShirt_BaseColor`
measures mean (66, 48, 121), ~31% luminance, DXT1, 4096x4096 — not more tint.

Visible win beyond the numbers: the bodice filigree is now readable; it was entirely
buried at the old exposure. Before/after: `shirt_BEFORE.png`, `shirt_AFTER.png`.

### Measurement traps hit while doing this

- The capture preview uses a **full HDRI backdrop** (office building, grass, sky), not a
  flat background. A background-difference heuristic therefore samples the *environment*
  and returns a neutral grey mean. That produced a false "the albedo is not reaching the
  output" reading which the actual image immediately disproved. **Sample a fixed garment
  region, not a background-difference mask.**
- A chroma filter (`max-min > 25 and b > g and r > g`) silently drops pixels as the
  material brightens toward neutral, so the sample count fell from 9541 to 536 and the
  means were not comparable across steps. Fixed-region sampling fixed this.

## 7. `SK_MelusinaHair` exists — earlier claim retracted

`Content/Melodia/Characters/Melusina/Hair/SK_MelusinaHair.uasset` (plus
`SK_Melusina_Hair_Skeleton`, and `SK_Melusina_FIXED_Hair` at the character root).
My earlier "does not exist" came from the stale 2026-09-01 spec plus a truncated search
whose results were flooded by `chair` matches. Both gaps in that spec are now disproven:
the hair mesh exists and `MI_Melusina_WaterHair` exists.
