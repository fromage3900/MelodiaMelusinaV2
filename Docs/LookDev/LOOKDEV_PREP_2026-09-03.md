
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

---

## 8. Oceanology — CORRECTION: it is not driven by a material instance at all

Owner identified the actors as **OceanologyInfiniteOcean**. Reading
`BP_OceanologyInfiniteOcean`'s CDO settles the whole lane:

```
UserOverrideMaterial : false
Material             : None
MaterialFar          : None
```

The ocean does **not** use an assigned material asset. Its look comes from **actor
properties** — chiefly the `SurfaceScattering` struct — which the plugin feeds into its
own internal material.

**This is why `MI_Oceanology_Melodia_Hero` is an orphan referenced by nothing.** The
material-instance approach was never going to work here. Any amount of MI tuning would
have been invisible. Section 2 above stands corrected: the knob list there is right, but
the *location* is the actor/preset, not an MI.

### Current values (CDO defaults) causing "too deep and dark"

| Property | Value |
|---|---|
| `SurfaceScattering.DeepScatteringColor` | `(0.05, 0.25, 0.30, A 0.15)` |
| `SurfaceScattering.Absorption` | `(70, 180, 350)` |
| `SurfaceScattering.DeepAbsorptionCoefficient` | `7` |
| `SurfaceScattering.ScatterBoost` | `10` |
| `GroundCaustics.MaximumDarkness` | `-4000` |
| `Preset` / `GroupedWaterPresets.*` | **all `None`** — no preset assigned |

### The fix already ships with the plugin

`GroupedWaterPresets.Color` takes a `UOceanologyWaterColorPreset`. Comparing two:

| | CDO default | `DA_Color_AnimeLightBlue` | **`DA_Color_LightBlue`** |
|---|---|---|---|
| `Absorption` | (70, 180, 350) | (70, 180, 350) | **(20, 40, 100)** |
| `DeepScatteringColor` | (0.05, 0.25, 0.30, A .15) | (0.05, 0.25, 0.30, A .15) | **(0.21, 0.72, 0.63, A .65)** |

Two things follow:

1. **`DA_Color_LightBlue` is the fix** — 3.5x lower absorption (light travels much
   further before dying) and a far brighter aqua deep-scatter colour with alpha 0.65
   instead of 0.15.
2. **`DA_Color_AnimeLightBlue` is a decoy** — despite the name it is byte-identical to
   the defaults except `WaterSpecular`/`WaterFresnelSpecular` = 0. Assigning it would
   change nothing about depth or darkness. Do not reach for it by name.

### Resolved: the `Absorption` convention

Section 2 flagged as unverified whether `Absorption` is an extinction *coefficient*
(higher = darker) or a *distance* (higher = clearer). The preset comparison settles it
empirically: the preset named **LightBlue** has the **lower** absorption. It is a
**coefficient** — higher means darker. My "B=350 > R=70 suggests distance" guess was
wrong, and would have sent the tuning in the wrong direction.

### Applying it — blast radius is an owner call

- **Per actor / per level** — set `GroupedWaterPresets.Color` on each
  OceanologyInfiniteOcean. Contained, but must be repeated per ocean.
- **BP CDO default** — fixes every ocean at once, but edits **plugin content**, which a
  plugin update overwrites.

Only one OceanologyInfiniteOcean is confirmed placed: the parked test fixture at Z-5000
in `MelodiaIntegrationMap`, which `CLAUDE.md` explicitly protects. A `.umap` text scan is
not reliable for finding the rest (umaps are compressed), so the full placement list is
not yet established.

### 8a. P0 target located: `LV_SeaAbove_Prototype`

Owner scoped the ocean work to **P0 Sea Above**. Two level copies exist:

- `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
- `/Game/LV_SeaAbove_Prototype`  (root-level duplicate)

The level is World Partition, so its actors live as individual files under
`Content/__ExternalActors__/`. Grepping those found **two Oceanology actors**, present
under *both* level paths with identical GUID filenames:

```
__ExternalActors__/.../LV_SeaAbove_Prototype/B/X0/YQRDXBQR534T08Q6G2HZDQ.uasset   (11,870 b)
__ExternalActors__/.../LV_SeaAbove_Prototype/C/VB/VHWRT1P58KT1SXWCO9HLIA.uasset   (31,302 b)
```

(A third file, `B/AL/YFXFMLGF2C7PE8UFCIG14M`, matches "Oceanology" but not
"OceanologyInfinite" — likely a related volume or manager, not the ocean itself.)

**Whether these actors already have a `GroupedWaterPresets.Color` assigned is NOT yet
known.** `grep -l` matches "Oceanology" in the raw bytes of these files, but `strings`
extracts nothing from them — not even the class name it matched on — so the name table
is encoded or compressed. Absence of a `DA_Color_*` string in them is therefore **not**
evidence that no preset is set. This must be read in the editor.

That check is currently blocked: a modal dialog
(`title='BS_GodFile - Unreal Editor' text='This asset editor has no docked tabs.'`)
is holding the game thread, so Monolith cannot answer even though port 9316 is
listening. 12 MODAL_OPEN entries are logged with no matching close.

**Likely cause of the modal:** repeated `capture_scene_preview` calls open asset editor
windows. Worth watching for during long capture loops.
