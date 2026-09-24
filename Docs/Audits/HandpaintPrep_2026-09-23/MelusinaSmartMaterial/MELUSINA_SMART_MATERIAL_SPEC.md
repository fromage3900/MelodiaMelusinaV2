# MELUSINA SMART MATERIAL SPEC - `SMS_Melusina_Handpaint`

**Owner:** Melodia / Melusina / Companions (never GrokBot / GrokStaged prefixes)
**Pilot:** ZenLantern showcase (`ZenLantern_V2_Showcase.fbx`) already in Substance
**Updated:** 2026-09-24 ~02:55 ET (America/Toronto) — VNP folder 11 + Resonance Bloom 15

## Design goals

- Stylized PBR / NPR-friendly: clean albedo, controlled roughness, optional metallic accents
- Masks from `vcol_melodia` + Painter mesh maps (AO / Curvature / WorldSpaceNormal)
- Cymatic accent folder sampling FrozenFracture Height / Emissive / Metallic / Opacity / Normal
- Parameter surface shaped like SimpleDiffuse (few lookdev knobs), workflow clarity shaped like Very Normal Paint (explicit paint slot)
- Melusina-owned **Very Normal workflow** folder (11) — pattern only; does **not** embed Nhance VNP binary
- Creative **Resonance Bloom** emissive stack (15) that remaps unused maps (Opacity / Metallic / Height / AO) into glow masks

## Confirmed vertex-color inputs (`vcol_melodia`)

| Ch | Meaning | Layer drive |
|---|---|---|
| R | Wear / cavity (inv AO) | Cavity multiply intensity |
| G | Decoration density | Motif / edge decoration; CharmFlash sparkle gate |
| B | Audio-reactivity (height) | Beat amplify / cymatic boost / MoonglowHalo |
| A | Emissive zones | Emissive fill mask (06 + 15a ResonanceCore) |

Bake or import vcol as a mesh/additional map before applying the SMS.

## Exposed parameters

| Param | Type | Default | Notes |
|---|---|---|---|
| `PrimaryColor` | Color | paper `#F5ECD7` (ZenLantern) / champagne `#C9A86A` for Melodia heroes | Base albedo |
| `SecondaryColor` | Color | cedar `#8B5E3C` | Secondary wash / wood or accent ID |
| `AccentColor` | Color | glow `#FFC978` | Wear highlight + emissive tint (Resonance Bloom hero) |
| `CavityIntensity` | 0-1 | 0.55 | Scales R x mesh AO |
| `DecorationIntensity` | 0-1 | 0.40 | Scales G x curvature |
| `CymaticIntensity` | 0-1 | 0.35 | FrozenFracture folder opacity |
| `BeatEmissive` | 0-1 | 0.45 | A x (optional x B) → emissive (layer 06 compat) |
| `RoughnessMin` | 0-1 | 0.35 | Clamp low |
| `RoughnessMax` | 0-1 | 0.72 | Clamp high |
| `MetallicAccent` | 0-1 | 0.15 | x Cymatic Metallic / metal ID (channel write in 10c only) |
| `ResonanceCore` | 0-1 | 0.55 | 15a stage-makeup core opacity |
| `MoonglowHalo` | 0-1 | 0.40 | 15b ghost-ring halo opacity |
| `CharmFlash` | 0-1 | 0.35 | 15c sparkle flash opacity |
| `InnerEmber` | 0-1 | 0.25 | 15d cavity lantern glow opacity |

## Layer stack (bottom → top)

Create a **folder** named exactly **`SMS_Melusina_Handpaint`**, then right-click → **Create smart material**.

Stack spirit: **01–10 unchanged** + **11 VeryNormal_Workflow** + **15 ResonanceBloom**.

### `01_Melodia_BaseFill` (Fill)
- Base Color = PrimaryColor; Roughness ≈ 0.55; Metallic = 0; Height = 0.5
- No mask
- Preferred M2: assign SBSAR `SBS_Melusina_SimpleDiffuse` as this fill engine (see PAINTER_WIRE)

### `02_Melodia_PaintSlot` (Paint layer) - VNP "Paint Here" analogue
- Empty paint layer for hand brushes / particles
- Keep under a subfolder `02_Paint` so artists always know where to stroke

### `03_Cavity_Multiply` (Fill, Multiply) - SD Shadow/AO analogue
- Base Color = darkened Primary / deep navy multiply
- Mask: Generator **Ambient Occlusion** (Levels tighten) **x** `vcol_melodia.R` (Color-to-mask / channel extract after vcol bake)
- Opacity = `CavityIntensity`

### `04_DecorationWear` (Fill) - SD Curvature + G
- Base Color = AccentColor (lighter); Roughness slightly lower
- Mask: Generator **Curvature** (convex) x Levels x `vcol_melodia.G`
- Opacity = `DecorationIntensity`

### `05_RoughnessClamp` (Fill, roughness channel only) - SD Specular cue
- Roughness = lerp(`RoughnessMin`,`RoughnessMax`); optional AO → slightly higher roughness in cavities

### `06_BeatEmissive` (Fill) - SD Rim + Melodia A/B
- EmissiveColor = AccentColor; strength = `BeatEmissive`
- Mask: `vcol_melodia.A` (emissive zones); optionally multiply by `vcol_melodia.B` for beat pulse
- Blend: Add / Passthrough per project emissive workflow
- **Compat note:** leave 06 as-is. Folder **15a_ResonanceCore** is the refined bloom-stack core with clearer naming; both can coexist (dial 06 down when 15 is hero).

### `07_NPR_StrokeGrunge` (optional Fill) - SD Strokes
- Grunge / brush-stroke alpha in mask; very low opacity; roughness micro-variation by default

### `08_VerticalGrade` (Fill pair) - SD Gradients
- Bottom Multiply dark + top Soft Light; mask = Position Y or UV gradient

### `09_MelodiaGrade` (Fill) - SD Post Multiply/Overlay
- Soft Multiply + Overlay color push using Primary/Accent

### `10_Cymatic_FrozenFracture` (folder) - Melodia exclusive
Resources (hardlinked in `resources\cymatic\`):

| Map | Channel use |
|---|---|
| `T_Cymatic_FrozenFracture_Height.png` | Height (low scale); also soft mask contributor for 15b |
| `T_Cymatic_FrozenFracture_Emissive.png` | Emissive x `CymaticIntensity` x (opt x B) |
| `T_Cymatic_FrozenFracture_Metallic.png` | Metallic x `MetallicAccent` in 10c; **remapped as sparkle mask** in 15c (not written to Metallic there) |
| `T_Cymatic_FrozenFracture_Opacity.png` | Folder / layer mask in 10; **inverted as ghost-ring shutter** in 15b |
| `T_Cymatic_FrozenFracture_Normal.png` | Normal @ low strength (ZenLantern guide: ~0.2 on frame); optional SoftLight in 11d |
| `T_Cymatic_FrozenFracture_BaseColor.png` | Optional desaturated wash - keep Melodia palette hero |

ZenLantern paint_guide recipe reminders: Opacity on paper panels ~0.5; Emissive on paper ~0.55; Normal on cedar frame ~0.2.

---

### `11_VeryNormal_Workflow` (folder) — VNP pattern, Melusina-owned

Do **not** embed Nhance Very Normal Paint binary. Melusina ships named placeholders + TODOs so hero handpaint normals stay clear.

#### `11a_WSN_Inject` (Fill, Normal)
- Normal channel fill (flat placeholder until wired)
- TODO: assign baked mesh **World Space Normal** (Add WS Normal HERE analogue)
- Bake WSN before wiring

#### `11b_Paint` / `11b_PaintNormals` (Paint)
- Empty paint layer under subfolder `11b_Paint`
- Stroke normals here (VNP Paint Here)

#### `11c_WSN_Anchor` (Fill, Normal)
- Named fill/anchor placeholder (DataActionAnchor analogue — Painter may only allow a named fill + note)
- TODO: Anchor WSN contribution; opacity starts at 0 until artist wires

#### `11d_TangentCombine` (Fill, Normal)
- TODO: mesh **Tangent Normal** and/or Very Normal Converter if artist drops shelf filter
- Melusina does **NOT** ship VNP converter SBSAR
- Optional: low-strength Cymatic Normal SoftLight if bitmap available (~0.15)

---

### `15_ResonanceBloom` (folder) — creative emissive, remap unused maps

Accent / glow color `#FFC978`. Emissive channel **Add** blend where API allows. Leaves 06 intact for compatibility.

#### Map remapping rationale

| Unused / underused map | Remap as | Why |
|---|---|---|
| Cymatic **Opacity** | 15b mask (invert) | Ghost-ring shutter — paper opacity becomes halo gate |
| Cymatic **Height** | 15b mask multiply | Who catches beat light |
| Cymatic **Metallic** | 15c mask only | Sparkle bits without writing Metallic channel |
| Mesh **AO** (inverted) | 15d mask | Lantern cavities glow warm instead of only darkening |
| `vcol.A` / `vcol.B` / `vcol.G` | 15a / 15b / 15c gates | Stage zones, beat pulse, decoration sparkle |

#### `15a_ResonanceCore` (Fill, Emissive Add)
- Emissive = AccentColor; opacity = `ResonanceCore` (0.55)
- Mask TODO: `vcol_melodia.A` (optionally × B)
- Refined stage-makeup core above 06

#### `15b_MoonglowHalo` (Fill, Emissive Add)
- Emissive = Accent (slightly cooler optional); opacity = `MoonglowHalo` (0.40)
- Mask TODO: `(1 − Cymatic Opacity) × soft Height × vcol.B`
- Plugin tries Opacity → mask fill; artist **INVERT** in UI, then multiply Height × vcol.B

#### `15c_CharmFlash` (Fill, Emissive Add)
- Emissive = Accent (slightly hotter optional); opacity = `CharmFlash` (0.35)
- Mask TODO: `vcol.G × Cymatic Metallic` bitmap as emissive mask (**not** Metallic channel)
- Plugin tries Metallic → mask fill; artist multiply by vcol.G

#### `15d_InnerEmber` (Fill, Emissive Add)
- Emissive = warm cedar-leaning tint `(0.55, 0.28, 0.12)` (or Accent×Secondary mix)
- Opacity = `InnerEmber` (0.25)
- Mask TODO: inverted mesh Ambient Occlusion — lantern cavities glow warm

---

## Mesh map bake checklist (before apply)

1. Ambient Occlusion (also for 15d invert)
2. **World Space Normal** (required before 11*)
3. Curvature
4. Position (optional, gradients)
5. Tangent / Object Space Normal if using 11d converter path
6. Vertex Color / `vcol_melodia` (or imported texture)

## Preferred M2 order (see PAINTER_WIRE)

1. SBSAR as `01` fill engine
2. Folder `11_VeryNormal_Workflow` optional for hero handpaint normals
3. Folder `15_ResonanceBloom` on top of / beside `06_BeatEmissive`

## Naming / export

- Smart material name: **`SMS_Melusina_Handpaint`**
- After Create smart material, copy resulting `.spsm` → `exports\SMS_Melusina_Handpaint.spsm`
- `exports\Melodia_Melusina_Handpaint_REF.spsm` is **Very Normal Paint** reference only - not Melusina
- Never invent fake `.spsm` bytes offline

## What Melusina deliberately does NOT ship

- No redistributed SimpleDiffuse binary as Melusina IP
- No embedded Nhance Very Normal Paint / converter SBSAR
- No fake authored HDF5/SPSM bytes
- No GrokBot / GrokStaged prefixes
