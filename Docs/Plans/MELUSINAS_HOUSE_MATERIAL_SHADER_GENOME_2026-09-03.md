# ♫ Melusina's House — Material + Shader Genome

**Date:** 2026-09-03  
**Discovery tokens:** `melusinashouseplan`, `Melusina materials`, `pink plaster`, `blue shingles`, `pearl shader`, `iridescent glass`, `Substance Sampler`, `Unreal materials`, `house palette`  
**Parent:** [`../../melusinashouseplan.md`](../../melusinashouseplan.md)

> **Goal:** turn the pink/blue Baroque house palette into a small, coherent material language that survives the Blender → Unreal handoff. Materials should reinforce the house's acoustic / marine / domestic identity without becoming a shader-tech demo. Atmosphere first; spectacle only where meaningfully earned. ♪

---

## 𝄞 Core rule — a genome, not fifty bespoke materials

Start with a small family of master surfaces and derive instances/variants.

```text
house geometry
→ stable material zone
→ master material family
→ controlled instance parameters
→ room-specific variation
```

Do not author one unique material per prop.

The house should feel unified because the same few physical ideas recur:

- chalky pearl plaster;
- glazed shell / ceramic;
- blue-lavender roof scales;
- warm brass/gold;
- washed pale wood;
- soft textile;
- watery / opalescent glass;
- actual water;
- low-intensity bioluminescent accents.

---

# ♪ Canonical palette

Use these as **art-direction targets**, not hard color-management laws.

| Zone | Suggested family | Character |
|---|---|---|
| `MH_PLASTER_PINK` | pearl blush | warm chalk, soft roughness variation |
| `MH_PLASTER_LAVENDER` | shell lavender | cooler secondary wall / inset |
| `MH_TRIM_IVORY` | pearl ivory | carved moulding, high readability |
| `MH_ROOF_BLUE` | powder / sea blue | dominant shingle color |
| `MH_ROOF_LAVENDER` | mist lavender | controlled roof variation |
| `MH_ROOF_BLUSH` | faint shell pink | rare accent shingles |
| `MH_METAL_GOLD` | warm aged brass | edges, finials, hardware |
| `MH_WOOD_WASHED` | pale rose-tan wood | doors, furniture frames |
| `MH_PEARL_IRIDESCENT` | opalescent pearl | hero shell / jewelry accents |
| `MH_GLASS_AQUA` | watery blue glass | windows / vessels / grotto |
| `MH_FABRIC_LAVENDER` | matte textile | drapes, upholstery |
| `MH_WATER_CLEAR` | clear blue water | Blue Room / basin |
| `MH_GLOW_SOFT` | moon-aqua emission | extremely restrained accent |

### Palette discipline

Use the hierarchy:

```text
pink / ivory masses
→ blue-lavender roof + glass
→ warm gold linework
→ tiny aqua / pearl magic accents
```

If everything is iridescent, nothing is iridescent.

---

# ♬ Blender lookdev material families

Blender materials are primarily **authoring/lookdev references**. Unreal owns final runtime shading.

Suggested Blender names:

```text
MAT_MH_Plaster_Pink
MAT_MH_Plaster_Lavender
MAT_MH_Trim_Ivory
MAT_MH_Roof_Scale
MAT_MH_Brass
MAT_MH_Wood_Washed
MAT_MH_Pearl
MAT_MH_Glass_Aqua
MAT_MH_Fabric
MAT_MH_WaterPreview
MAT_MH_GlowPreview
```

Keep node graphs simple enough that they communicate intent clearly when the asset is opened on the laptop.

---

# ♪ Material family 01 — pearl blush plaster

### Visual target

Not candy plastic. Not flat pink paint.

Think:

```text
chalky mineral plaster
+ very subtle warm/cool clouding
+ tiny roughness breakup
+ softened edges catching warm light
```

### Blender prototype

```text
Base Color
← pink/ivory mix
← low-frequency Noise / ColorRamp

Roughness
← 0.55–0.78
← subtle noise ±0.06

Normal
← extremely fine bump
```

Keep displacement negligible at game scale.

### Unreal target

```text
M_MH_Surface_Master
MI_MH_Plaster_Pink
MI_MH_Plaster_Lavender
```

Useful instance parameters:

```text
BaseTint
SecondaryTint
MacroVariationScale
MacroVariationStrength
RoughnessBase
RoughnessVariation
NormalStrength
EdgeWarmth
```

A single master should cover most opaque wall / ceramic-like surfaces unless performance or artistic requirements say otherwise.

---

# ♫ Material family 02 — scallop roof genome

The roof is a major hero surface and needs variation without confetti.

### Material zones

Use one roof master with instance / per-mesh variation rather than separate shaders for every shingle color.

Suggested target:

```text
M_MH_Roof_Master
MI_MH_Roof_BlueLavender
```

### Variation recipe

```text
80% blue / powder-blue family
15% lavender family
5% blush / aqua family
```

That is a distribution concept, not a requirement that each individual tile draw a random color at runtime.

Prefer stable authored variation generated in Blender or encoded through material slots / vertex data where the export path is proven.

### Surface response

- moderately rough glazed scale;
- broad soft highlight;
- subtle edge lightening;
- occasional pearl accent, not full iridescence.

Do not make the roof read as metallic.

---

# 𝄞 Material family 03 — ivory carved trim

The trim must stay readable against pink walls and blue roof.

Target:

```text
warm pearl-white
roughness ~0.40–0.58
slightly softer / smoother than plaster
minimal subsurface-like softness only if cheap and visually justified
```

Use the same family on:

- shells;
- rosettes;
- window surrounds;
- stair cheeks;
- carved furniture trim.

Hero pearl inserts are a separate accent family.

---

# ♪ Material family 04 — warm brass / aged gold

Avoid mirror-gold fantasy trim.

Target:

```text
warm brass
+ modest roughness
+ darker recesses
+ occasional brighter edge polish
```

Unreal:

```text
M_MH_Metal_Master
MI_MH_Brass_Warm
MI_MH_Brass_Polished_Accent
```

Parameters:

```text
Metallic = 1
BaseTint
Roughness
EdgePolish
PatinaStrength
PatinaTint
```

Keep patina extremely subtle on an inhabited, cared-for house.

---

# ♬ Material family 05 — washed wood

Doors, bedframe cores, cabinetry and table structures should not introduce a dark brown visual language.

Use pale washed wood:

- rose-beige;
- honey ivory;
- desaturated shell tan.

Wood grain should support form, not dominate it.

### Substance Sampler lane

A fast workflow:

1. start from a royalty-free wood scan / source with known license;
2. generate clean basecolor / roughness / normal;
3. soften contrast;
4. tint toward rose-honey;
5. reduce deep dark grain;
6. test under the actual house light temperature;
7. export a standard PBR set with provenance recorded.

Do not use third-party textures with unclear redistribution/commercial terms.

---

# ♫ Material family 06 — opalescent pearl

Pearl is a **hero accent**, not the whole house.

Use for:

- finials;
- door insets;
- chandelier drops;
- shell centers;
- mirror accents;
- wardrobe pedestal details.

### Visual model

```text
ivory base
+ very low-saturation cyan/pink/violet Fresnel shift
+ medium-low roughness
+ tiny micro-normal
```

Avoid rainbow gasoline-film intensity.

Unreal target:

```text
M_MH_Pearl_Master
MI_MH_Pearl_Ivory
MI_MH_Pearl_BlueRoom
```

Parameters:

```text
BaseTint
FresnelTintA
FresnelTintB
FresnelStrength
Roughness
MicroNormal
```

If an experimental advanced shading path is tested later, keep a stable conventional fallback material.

---

# ♪ Material family 07 — aqua glass

Windows should read as glass but still support the illustrative palette.

Use two modes:

```text
WINDOW_GLASS
DECORATIVE_GLASS
```

### Window glass

- restrained tint;
- readable reflection;
- not perfectly transparent;
- optional subtle unevenness.

### Decorative glass

For chandelier drops / bottles / shell insets:

- stronger aqua/lavender tint;
- slightly higher refraction distortion where appropriate;
- more visible Fresnel.

Keep glass meshes separated from opaque Nanite candidate assemblies unless the Unreal validation pass proves the chosen material/rendering path is appropriate.

---

# ♬ Material family 08 — lavender textile

Textiles include:

- drapes;
- awnings;
- upholstery;
- bed canopy;
- cushions.

Target:

```text
matte / fibrous
+ broad soft shading
+ very small weave normal
+ restrained color variation
```

Do not make every textile velvet.

Suggested Unreal hierarchy:

```text
M_MH_Fabric_Master
MI_MH_Fabric_Lavender
MI_MH_Fabric_Blush
MI_MH_Fabric_BlueRoom
```

If cloth animation is required, runtime cloth setup is a separate task from material authoring.

---

# 𝄞 Material family 09 — Blue Room water

Blender only needs a convincing preview.

Unreal owns the actual runtime water material / interaction.

### Visual goals

- clear enough to see submerged steps;
- blue-cyan body color;
- slow readable caustic language;
- warm reflected interior light;
- subtle bioluminescent accents in selected pockets.

Do not make the Blue Room a neon aquarium.

### Separate concerns

```text
water surface
underwater wall tint
caustic projection / light function
bioluminescent props
wetness near waterline
```

Those should not all live in one monster shader.

---

# ♪ Material family 10 — restrained magical glow

Use emission only where the house is actually expressing something:

- pearl note on the Resonance Mobile;
- tiny grotto organism;
- water-touched bell;
- selected score inlay;
- rare window tracery accent.

Target average intensity should be low enough that the warm practical lights remain dominant.

### Rule

> If the screenshot still looks magical with emission disabled, the art direction is healthy.

---

# ♫ Geometry Nodes ↔ material contract

Inside Blender, house wrappers may author semantic values such as:

```text
mh_material_zone
mh_ornament_tier
mh_water_affinity
mh_resonance_band
```

But **do not assume arbitrary named Geometry Nodes attributes automatically survive FBX into Unreal as usable metadata**.

For production handoff, rely first on explicit, tested channels:

1. material slots;
2. separate mesh sections when necessary;
3. vertex color channels only where the import path is verified;
4. asset naming / sidecar metadata if later automation needs richer semantics.

The authoring attributes remain valuable for:

- debugging;
- material assignment inside Blender;
- generating export copies;
- deciding which material slot gets applied.

---

# ♬ Suggested material-slot contract

Keep slot count bounded.

Hero exterior mesh candidates should generally aim for a small set such as:

```text
0 Plaster
1 IvoryTrim
2 Roof
3 Brass
4 Wood
5 Pearl
```

Transparent glass and water should usually remain separate meshes / assemblies.

Furniture assets can use a smaller subset:

```text
0 WoodOrBody
1 Trim
2 Brass
3 Fabric
4 PearlOrGlass
```

Avoid 15-slot furniture meshes.

---

# ♪ Material naming in Unreal

Suggested structure:

```text
/Game/Melodia/Environment/MelusinasHouse/Materials/
├── Masters/
│   ├── M_MH_Surface_Master
│   ├── M_MH_Roof_Master
│   ├── M_MH_Metal_Master
│   ├── M_MH_Pearl_Master
│   ├── M_MH_Glass_Master
│   └── M_MH_Fabric_Master
├── Instances/
│   ├── MI_MH_Plaster_Pink
│   ├── MI_MH_Plaster_Lavender
│   ├── MI_MH_Trim_Ivory
│   ├── MI_MH_Roof_BlueLavender
│   ├── MI_MH_Brass_Warm
│   ├── MI_MH_Wood_Washed
│   ├── MI_MH_Pearl_Ivory
│   ├── MI_MH_Glass_Aqua
│   └── MI_MH_Fabric_Lavender
└── Functions/
    ├── MF_MH_MacroVariation
    ├── MF_MH_PearlFresnel
    └── MF_MH_EdgeSoftening
```

Do not create the Functions folder until repetition justifies it.

---

# 𝄞 Material parameter discipline

Every master material should expose only parameters with a real art-direction use.

Good:

```text
BaseTint
RoughnessBase
VariationStrength
VariationScale
NormalStrength
FresnelStrength
EmissionStrength
```

Bad:

```text
34 mystery scalar parameters named Amount1–Amount34
```

The goal is fast iteration on a second workstation without reverse-engineering the shader graph.

---

# ♪ First shader session — ~2 hours

## Pass A — clay + palette separation · 15 min

Render the house with only flat zone colors.

Verify silhouette and color hierarchy before clever shading.

## Pass B — plaster + trim · 25 min

- pink plaster master;
- ivory trim variant;
- macro roughness variation.

## Pass C — roof · 25 min

- blue/lavender roof master;
- stable non-confetti variation;
- check at gameplay camera distance.

## Pass D — brass + pearl · 25 min

- warm brass;
- restrained pearl Fresnel.

## Pass E — glass + fabric · 20 min

- one window material;
- one lavender textile.

## Pass F — Blue Room lookdev · 10 min

- water preview;
- one bioluminescent accent;
- test warm/cool balance.

---

# ♫ Evidence captures

Save:

```text
Saved/Audit/melusinashouse/materials/
```

Suggested captures:

```text
MH_MAT_flat_zones.png
MH_MAT_plaster_trim.png
MH_MAT_roof_variation.png
MH_MAT_brass_pearl.png
MH_MAT_glass_fabric.png
MH_MAT_blue_room.png
```

Each screenshot should include enough context to judge whether the material supports the room, not just a material ball.

---

# ♬ Definition of done

The Phase-3 shader genome is successful when:

- the house uses a bounded material family instead of bespoke-per-object shaders;
- pink plaster still reads as plaster;
- blue/lavender shingles read as a coherent roof, not confetti;
- brass is warm and restrained;
- pearl is special because it is rare;
- glass/water are kept as clear separate rendering concerns;
- Blender lookdev communicates intent without pretending to be the UE runtime shader;
- Unreal material names and instance responsibilities are already decided before import;
- provenance for any texture source is known and recorded.

---

> **The materials should make the house feel touched by salt, shell, fabric and song — not coated in effects.** ♫
