# Material Authoring Guide — SDF / Toon / Nikki

**Purpose:** everything needed to author a new material master without
rediscovering it. Every pin name below was *verified* against the live editor
via Monolith, not inferred. Companion doc: `Docs/MELODIA_MCP_TOOL_REFERENCE.md`.

Established 2026-09-06 while building the PetalPrism family.

---

## 0. Read this first — the one rule that saves an hour

**Do not guess pin names.** Verify them:

```bash
python Tools/mono.py get_expression_pin_info "{\"class_name\":\"Noise\"}"
```

Cost of guessing, measured: four failed attempts at reading expressions by
Python property, then two wrong pin names that silently produced a broken
material which still compiled clean. `connect_material_expressions` returns
`False` on a bad pin and **does not raise** — so a wrong name gives you a
material that builds, runs, and quietly ignores a parameter.

Always run `validate_material` afterwards. Island nodes are how you find this.

---

## 1. Reading a material graph

`unreal.Material` does **not** expose expressions as an editor property on
UE 5.8. All of these fail:

```python
mat.get_editor_property("expressions")            # no such property
mat.get_editor_property("expression_collection")  # no such property
mat.get_editor_property("editor_only_data")       # returns base class, no expressions
```

The accessor that works:

```python
unreal.MaterialEditingLibrary.get_material_expressions(mat)
```

It is typed to `UMaterial` and **hard-rejects `UMaterialFunction`**:

```
TypeError: Cannot nativize 'MaterialFunction' as 'Material'
```

For functions, use Monolith `get_function_info` (see §5).

Precedent in repo: `Tools/fix_dream_gate_wiring.py`, `Tools/_fix_ink_wiring.py`.

---

## 2. Verified pin names

### SubstrateToonBSDF
`MaterialExpressionSubstrateToonBSDF`, 9 inputs, 1 unnamed output.

| idx | pin |
|-----|-----|
| 0 | `BaseColor` |
| 1 | `Metallic` |
| 2 | `Specular` |
| 3 | `Roughness` |
| 4 | `Normal` |
| 5 | `EmissiveColor` |
| 6 | `PatternUVs` |
| 7 | `Anisotropy` |
| 8 | `Tangent` |

Output goes to `MP_FRONT_MATERIAL`, **not** `MP_BASE_COLOR`:

```python
MEL.connect_material_property(bsdf, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
```

Set `bUsesSubstrate = True` on the material, and assign a
`toon_profile` (e.g. `/Game/EnvSandbox/Materials/ToonProfiles/TP_NikkiDream`).

### Common nodes — the ones with surprising names

| class | inputs | notes |
|---|---|---|
| `Noise` | `World Position`, `FilterWidth` | **space in the name.** Not `Position` |
| `Power` | `Base`, `Exp` | **`Exp`**, not `Exponent` |
| `WorldPosition` | — | outputs `XYZ` / `XY` / `Z`; **must name the output** |
| `Fresnel` | `ExponentIn`, `BaseReflectFractionIn`, `Normal` | |
| `LinearInterpolate` | `A`, `B`, `Alpha` | |
| `Multiply` / `Add` | `A`, `B` | |
| `Sine`, `Saturate`, `OneMinus`, `Time`, `TextureCoordinate`, `Constant` | no named inputs — pass `""` | |

Those first three each caused a silent failure in the first PetalPrism build.

---

## 3. The Nikki function chain

Every Nikki function follows one signature shape: takes `BaseColor` (Vector3),
returns `Color`. **They are designed to compose linearly** — feed one's `Color`
into the next's `BaseColor`.

```
base → PastelGrade → PearlSheen → IridescenceSheen → RimGlow → GlitterHalo
```

| function | inputs | outputs |
|---|---|---|
| `MF_NikkiDreamGrade` | `BaseColorIn` | `Emissive`, `Color` |
| `MF_NikkiRimGlow` | `BaseColor`, `Normal`, `RimColor`, `RimIntensity`, `RimWidth`, `GlowIntensity`, `BloomBoost` | `Color` |
| `MF_NikkiSparkle` | `BaseColor`, `UV`, `SparkleMask` *(Texture2D)*, `SparkleIntensity`, `SparkleThreshold`, `SparkleColor` | `Color` |
| `MF_NikkiIridescenceSheen` | `BaseColor`, `Normal`, `Iridescence`, `IridescenceTint`, `IridescencePower`, `FabricSheen`, `SheenTint` | `Color` |
| `MF_NikkiPearlSheen` | `BaseColor`, `Normal`, `Mask`, `Frequency`, `SecondFrequency`, `Strength`, `PearlTint` | `Color` |
| `MF_NikkiPastelGrade` | `BaseColor`, `Mask`, `RampLow`, `RampMid`, `RampHigh`, `RampPosMid`, `Strength`, `PastelLift`, `Bloom` | `Color` |
| `MF_NikkiGlitterHalo` | `BaseColor`, `Normal`, `WorldPosition`, `Mask`, `Scale`, `Amount`, `Intensity`, `GlitterColor`, `HaloStrength`, `HaloPower`, `TwinkleSpeed`, `Time` | `Color` |

Note `DreamGrade` breaks the pattern slightly — input is `BaseColorIn`, and it
gives you a separate `Emissive` output worth routing.

**`MF_NikkiSparkle` requires a Texture2D.** For texture-free materials use
`MF_NikkiGlitterHalo` instead — it is procedural (WorldPosition + Time).

### Known-broken — do not wire blind

| function | symptom |
|---|---|
| `MF_ParallaxCore` | every input reported 3×, all types `Vector3` incl. textures/scalars |
| `MF_RealParallax` | **no inputs**, 3 identical `Result` outputs |
| `MF_SDF_BandRelief` | **no inputs**, 35 identical `Result` outputs |

Diagnose before use. Unresolved as of 2026-09-06.

---

## 4. Parameter grouping convention

Follows `M_Master_Toon_Universal`. Numbered prefixes so the MI panel sorts
correctly. Assign `group` **and** `sort_priority` — step priorities by 10 so
params can be inserted later without renumbering.

```
01 | Base Surface        albedo, palette, Roughness, Metallic
02 | Gilding             gild / gold / leaf
03 | Glow & Emissive     glow, emissive, bloom, rim
04 | Iridescence         irid, shimmer, sheen, pearl, sparkle, glitter
05 | Layer Blending      layer weights, edge, contact
06 | Pattern & SDF       pattern, crack, sdf, shape controls
07 | Textures            *Tex, *Texture, *Map (incl. HeightMap, NormalMap)
08 | Relief & Depth      parallax/depth scalars
09 | Ink & Paint         ink, oilpaint, impasto
10 | UV & Projection     uv, tiling, worldalign
11 | Animation           speed, pan, pulse, phase
12 | Audio Reactive      audio, beat, rhythm
```

Grouping is **UI metadata only** — no shader change, fully reversible. It is
the cheapest large usability win available.

### Two defects to avoid

**Duplicate parameter names.** UE collapses same-name same-type params into one
MI entry that drives *every* matching node. Found in the wild:
`M_SDF_GildedFiligree` has `GlowAmount` ×3 and `GlowColor` ×3;
`M_SDF_GildedStucco` has `GlowAmount` ×2 and `Scale` ×2. One slider, several
destinations, no way to tell from the panel. Audit with
`get_material_parameters` before shipping a master.

**Ungrouped params.** Everything in group `None` is why a 14-parameter material
feels unusable. See `Tools/slice_a_phase1_grouping.py`.

---

## 5. Custom HLSL nodes

```python
c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
c.set_editor_property("code", hlsl_string)
c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)

arr = []
for nm in ["UV", "PetalCount"]:
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", nm)
    arr.append(ci)
c.set_editor_property("inputs", arr)
```

Input pin names are then whatever you declared, and the HLSL references them as
bare identifiers. `CMOT_FLOAT1` for scalar output.

### SDF shape recipes that work

Polar rose / petal rosette:
```hlsl
float2 p = UV - 0.5;
float r = length(p) * 2.0;
float a = atan2(p.y, p.x);
float rose = abs(cos(a * max(PetalCount, 1.0) * 0.5));
return (rose * 0.7 + PetalFill) - r;   // positive inside
```

Mandala lace (rings ∩ radial star):
```hlsl
float ring = abs(frac(r * max(Rings,1.0)) - 0.5) * 2.0;
float star = abs(cos(a * max(Points,3.0) * 0.5));
return 0.55 - min(ring, 1.0 - star * 0.85);
```

Ribbon spiral:
```hlsl
float spiral = frac(a / 6.2831853 * max(Twists,0.5) + r * 2.0);
return Width - abs(spiral - 0.5) * 2.0;
```

Sharpened starburst:
```hlsl
float spike = pow(abs(cos(a * max(Arms,3.0) * 0.5)), max(Sharp,0.1));
return (spike * 0.8 + Core) - r;
```

Soften any SDF into a 0..1 mask: `saturate(sdf * Softness)`.

---

## 6. Procedural sparkle without textures

```
WorldPosition[XYZ] → Multiply(Scale) → Noise["World Position"]
Noise → Power(Base) ; Constant(9.0) → Power["Exp"]
Time → Multiply(Speed) → Add(Noise) → Sine → Saturate    # twinkle
Power × Saturate × Amount × Color → emissive
```

World-space means glints sit in the world and drift as the camera moves, rather
than crawling across UVs. No texture dependency, so it cannot break from a
missing reference.

---

## 7. Authoring checklist

1. `get_expression_pin_info` for every node class you will wire
2. `get_function_info` for every function you will call
3. Build. Have your wire helper **collect and print failures** — do not let
   `connect_material_expressions` return `False` unnoticed
4. `validate_material` — resolve every island and unused_parameter
5. `get_compilation_stats` — confirm `is_compiled: true`, sanity-check
   instruction count
6. Confirm no duplicate parameter names
7. Confirm every parameter has a group and sort_priority

Reference implementations: `Tools/create_m_sdf_petal_prism.py` (classic output),
`Tools/build_toon_sdf_family.py` (Substrate Toon + Nikki chain).

---

## 8. The family so far

| master | shape | chain | palette |
|---|---|---|---|
| `M_SDF_PetalPrism` | polar rose | procedural irid + sparkle | plum → blush |
| `M_SDF_MoonlitLace` | mandala lace | PearlSheen → RimGlow | midnight → moonlight |
| `M_SDF_RibbonCandy` | ribbon spiral | PastelGrade → GlitterHalo | raspberry → cream |
| `M_SDF_StarBloom` | starburst | DreamGrade → IridescenceSheen | violet void |

All procedural, no texture dependencies, grouped params, no duplicate names.
The last three output through `SubstrateToonBSDF`.

---

## 9. Gotcha ledger

- Expressions are not a Python property — use `MEL.get_material_expressions`
- That call rejects MaterialFunction — use Monolith `get_function_info`
- `Noise` input is `World Position`, with a space
- `Power` exponent pin is `Exp`
- `WorldPosition` has no default output — name `XYZ`
- Substrate goes to `MP_FRONT_MATERIAL`, not `MP_BASE_COLOR`
- `connect_material_expressions` returns `False` silently; it never raises
- A material with unwired inputs still compiles clean — validate always
- Monolith path param is `asset_path` (not `path` or `function_path`)
- `Content/EnvSandbox/*` and `Tools/*` are gitignored in this repo
