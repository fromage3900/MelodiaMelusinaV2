# GRAPH_SPEC — Melusina Simple Diffuse (ultimate vision)

**Owner:** Melodia / Melusina / Companions (never GrokBot / GrokStaged)
**Package:** `SBS_Melusina_SimpleDiffuse`
**Graph:** `Melusina_SimpleDiffuse`
**Paired SMS:** `SMS_Melusina_Handpaint` (Painter stack; this SBSAR is the fill / generator engine)
**Not:** a clone of Nhance SimpleDiffuse — Melusina-owned param surface inspired by SD knobs + Very Normal Paint clarity.

Generated for HandpaintPrep `2026-09-23`. Designer target: **Adobe Substance 3D Designer 12.2.1**.

---

## 1. Design intent

| Pillar | Goal |
|---|---|
| **Cymatics** | Ring / FrozenFracture contribution into Height, Emissive, Metallic, Opacity, masks |
| **Gouache normals** | Handpainted-looking tangent normals from **curvature bent to height** → Normal From Height (+ optional stroke) |
| **vcol_melodia** | Mask authority: R wear, G decoration, B audio/beat, A emissive zones |
| **Lookdev knobs** | Few SimpleDiffuse-shaped sliders (shadow spread, curvature opacity, roughness min/max, rim/beat, strokes) |
| **Clarity** | Separate outputs + clear Melodia labels — VNP-like “know where to paint / what drives what” |

Pilot palette (ZenLantern): paper `#F5ECD7`, cedar `#8B5E3C`, glow `#FFC978`.

---

## 2. Confirmed `vcol_melodia` (from `vertex_paint.py`)

| Ch | Meaning | Drive |
|---|---|---|
| **R** | Wear / cavity (inverted Cycles AO bake) | Shadow multiply, Mask_Wear, roughness ↑ in cavities |
| **G** | Decoration density (asset bbox rules) | Accent wash, Mask_Decoration |
| **B** | Audio-reactivity (height falloff) | BeatBoost, Mask_Beat, cymatic boost |
| **A** | Emissive zones (asset rules) | Emissive fill mask |

---

## 3. Exposed inputs

### Colors (Melusina Colors)
| Param | Type | Default | Role |
|---|---|---|---|
| `PrimaryColor` | float4 | `#F5ECD7` | Base albedo |
| `SecondaryColor` | float4 | `#8B5E3C` | Wash / wood / secondary ID |
| `AccentColor` | float4 | `#FFC978` | Wear highlight + emissive tint |
| `ShadowColor` | float4 | deep navy/ink | Multiply shadow under AO×R |

### Lookdev (Melusina Lookdev)
| Param | Default | Role |
|---|---|---|
| `BrushStrokeIntensity` | 0.25 | NPR stroke / grunge (wired to BrushStrokeMap opacity in scaffold; deepen in Designer) |
| `GouacheDepth` | 0.55 | How hard curvature bends into Height before NFH |
| `CymaticIntensity` | 0.35 | FrozenFracture / ring strength |
| `BeatBoost` | 0.45 | B-channel amplify for emissive / cymatic |
| `RoughnessMin` / `RoughnessMax` | 0.35 / 0.72 | Clamp range (scaffold blends mid→max by wear) |
| `MetallicAccent` | 0.15 | Metallic × cymatic / metal ID |
| `NormalStrength` | 1.0 (0–4) | Normal From Height intensity |
| `ShadowSpread` | 0.55 | AO/wear tighten (expose → Levels mid in next Designer pass) |
| `CurvatureOpacity` | 0.40 | Decoration / edge treatment opacity |

### Connectable maps
| Input | Type | Usage / notes |
|---|---|---|
| `MeshAO` | grayscale | `ambientOcclusion` |
| `Curvature` | grayscale | `curvature` |
| `WorldNormal` | color | `worldSpaceNormal` (optional; VNP sibling) |
| `vcol_melodia` | color | RGBA Melodia vertex color |
| `CymaticHeight` | grayscale | FrozenFracture Height / procedural seed |
| `CymaticOpacity` | grayscale | Seed / fracture mask |
| `BrushStrokeMap` | grayscale | Optional NPR stroke |

**Output size:** graph `defaultParentSize` = `9x9` (512); override in Designer / Painter instance as needed (1k–4k lookdev).

---

## 4. Outputs (multi-output single graph)

| Identifier | Usage | Intent |
|---|---|---|
| `BaseColor` | baseColor | Primary → Shadow×(AO·R) → Secondary overlay → Accent×(Curv·G) → stroke |
| `Normal` | normal | Gouache: Height (Curv + Cymatic) → **Normal** filter |
| `Roughness` | roughness | Lerp Min→Max by wear |
| `Metallic` | metallic | Accent amount × cymatic opacity |
| `Height` | height | Curvature + CymaticHeight (masked) |
| `Emissive` | emissive | Accent × (A · B) |
| `Opacity` | opacity | Default opaque (open with cymatic later) |
| `Mask_Wear` | custom | AO · vcol.R |
| `Mask_Decoration` | custom | Curv · vcol.G |
| `Mask_Beat` | custom | vcol.B |
| `Mask_Cymatic` | custom | CymaticOpacity · vcol.B |
| `ORM` | custom | Packed approx R=AO, G=Rough, B=Metal |

Optional future split graphs: `MF_Melusina_GouacheNormal`, `MF_Melusina_CymaticRings` as instances.

---

## 5. Node flow (plain language ≈ SD layers + Melusina forks)

```
BASE
  Uniform(PrimaryColor)
    └─ Multiply ShadowColor   [opacity = MeshAO × vcol.R]     ← SD Shadow/AO
         └─ Overlay SecondaryColor (light)                    ← secondary wash
              └─ Copy AccentColor [opacity = Curv × vcol.G]   ← SD Curvature color
                   └─ Multiply Secondary [opacity = BrushMap] ← SD Brush strokes
                        → OUT BaseColor

HEIGHT / GOUACHE NORMAL
  Curvature ──Add── CymaticHeight [opacity = CymaticOpacity]  ← Melusina cymatic fork
       │                 (GouacheDepth / CymaticIntensity deepen in next pass)
       └─ Normal(intensity=NormalStrength) → OUT Normal
       └─ → OUT Height

SPEC / ROUGH / METAL
  RoughnessMin ──Copy── RoughnessMax [mask=Wear] → OUT Roughness   ← SD Spec cue
  0 ──Copy── MetallicAccent [mask=CymaticOpacity] → OUT Metallic

RIM / BEAT / EMISSIVE
  vcol.A × vcol.B → mask
  black ──Copy── AccentColor [mask] → OUT Emissive               ← SD Rim + Melodia A/B

MASKS
  Wear / Decoration / Beat / Cymatic → dedicated outputs for SMS wiring

POST
  Vertical grade + post multiply/overlay = Painter SMS layers 08/09
  (kept out of this generator so SMS_Melusina_Handpaint owns grade stack)
```

### Melusina forks (exclusive vs Nhance SD)
1. **Cymatic ring/fracture** — sample `T_Cymatic_FrozenFracture_*` (or procedural) into Height / Mask_Cymatic / Metallic / Emissive.
2. **Gouache normal** — curvature (+ stroke) as height → Normal From Height; not a baked WSN converter (VNP stays optional sibling).
3. **vcol-driven masks** — first-class outputs for Painter SMS, not buried only inside albedo.

---

## 6. Resource pack (this folder)

`resources\` hardlinks to MelusinaSmartMaterial cymatic set:

- `T_Cymatic_FrozenFracture_{Height,Opacity,Normal,Emissive,Metallic,BaseColor}.png`

In Designer: create Bitmap nodes pointing at these (or keep connectable inputs and bind in Painter).

---

## 7. Evolution path (Designer clicks after open)

1. Open `.sbs` → bind `GouacheDepth` / `CymaticIntensity` / `ShadowSpread` / `CurvatureOpacity` into Levels / Blend opacity dynamic values (scaffold exposes them; some are ready for wiring).
2. Add Perlin / Tile Generator ring for procedural cymatics when bitmap absent.
3. Instance `MF_` micro-graphs for gouache + cymatic.
4. Re-cook → refresh Painter shelf SBSAR.
5. Point `SMS_Melusina_Handpaint` fill layers at this SBSAR (see `PAINTER_WIRE.md`).

---

## 11. Gouache + Cymatic deepen (v3, 2026-10-05)

Cooked `.sbs` 149,484 B; `.sbsar` **4,410 B** (was 3,740 B), sbscooker exit 0, shelf refreshed.

### New exposed lookdev knobs (all dynamically wired)

| Group | Param | Default | Wiring |
|---|---|---|---|
| Gouache | `GouacheStrokeBreakup` | 0.40 | Stroke → gouache height blend opacity (separate from albedo `BrushStrokeIntensity`) |
| Gouache | `GouacheBlur` | 0.55 | Blur intensity before NFH |
| Gouache | `GouacheSharpen` | 0.20 | Sharpen intensity after HQ blur |
| Cymatic | `RingDistance` | 48 | Distance-filter reach |
| Cymatic | `RingWarp` | 12 | Warp intensity on ring bands |
| Cymatic | `RingSwirl` | 8 | Directional-warp intensity |
| Cymatic | `RingAngle` | 35 | Directional-warp angle |
| Cymatic | `RingBandTightness` | 0.40 | Ring-band levels mid |
| Cymatic | `HistogramPosition` | 0.55 | Histogram-scan edge position |
| Curvature | `CurvatureEdgeLight` | 0.25 | Accent edge-light overlay on sharpened curvature |
| Curvature | `CurvatureEmissive` | 0.15 | Curvature-edge emissive whisper |

Curvature lane is now first-class on both albedo (edge light) and emissive (edge sparkle), in addition to the existing decoration/wear/gouache-height lanes.

See `BUILD_RECEIPT_DESIGNER.md` for the v3 receipt.

## 12. Slope blur + emissive halo (v4, 2026-10-05)

Cooked `.sbsar` **4,691 B**, sbscooker exit 0, shelf refreshed. New knobs:

| Group | Param | Default | Wiring |
|---|---|---|---|
| Slope | `SlopeThreshold` | 0.50 | WorldNormal-Z levels mid for the slope mask |
| Slope | `SlopeBlur` | 0.45 | Blur intensity of the soft gouache-height branch |
| Slope | `SlopeRoughnessLift` | 0.20 | Roughness lift on sloped/receding surfaces (cloth hierarchy) |
| Emissive | `EmissiveGlow` | 0.25 | Blurred emissive mask added back as a soft halo around beat/resonance |

**Slope blur setup:** `WorldNormal` → extract Z → `SlopeThreshold` levels → mask. Height =
crisp gouache relief on open faces, slope-blurred relief on receding/vertical surfaces. The
same slope mask lifts roughness so fabric reads matte on slopes (Infinity Nikki cloth hierarchy:
crisp reads up front, soft reads in the paint). If your mesh has no `WorldNormal` bake, the Z
channel defaults to mid-gray and the soft/crisp blend sits at ~50% — bake it (or raise
`SlopeThreshold`) for a firm split.

## v3 knobs (retained)

*Source of truth for Painter layer names: `MELUSINA_SMART_MATERIAL_SPEC.md`. This GRAPH_SPEC owns the Designer generator.*

---

## 8. Scaffold honesty (build_sbs.py / cooked SBSAR)

Cooked successfully with Designer **sbscooker** (magic `37 7A BC AF`).  
**Live dynamic:** `NormalStrength` → Normal filter intensity; colors + map inputs + vcol splits + blend chain + masks.  
**Exposed for Designer GUI pass:** BrushStrokeIntensity, GouacheDepth, CymaticIntensity, BeatBoost, ShadowSpread, CurvatureOpacity, RoughnessMin/Max, MetallicAccent — bind to Blend `opacitymult` / Levels next.

Package identifier / graph identifier: `SBS_Melusina_SimpleDiffuse` / `Melusina_SimpleDiffuse`.


---

## 9. Implemented in v2 (M1 Nikki deepen — 2026-09-24)

**Status:** Cooked + shelf refreshed. SBSAR **2456 → 3740 B** (real sbscooker). Bar: `GOAL_INFINITY_NIKKI_BAR.md` / execute `GOAL_V2_GO.md`.

### Color stack (fashion-readable)
1. Primary  
2. Multiply ShadowColor × Mask_Wear (AO·vcol.R shaped by **ShadowSpread** levels)  
3. SoftLight Secondary (light overall cedar wash)  
4. Overlay Secondary × sharpened Decoration (Curv·vcol.G) × **CurvatureOpacity**  
5. Accent rim on decoration ∪ cymatic kiss  
6. Multiply Secondary × BrushStrokeMap × **BrushStrokeIntensity**  
7. Soft post Overlay Primary + SoftLight Accent whisper (thumbnail read)

### Gouache Normal
Curvature → levels(**GouacheDepth**) → + stroke breakup → + cymatic height → blur → **blur_hq** → light sharpen → **Normal From Height(NormalStrength)** → Overlay WorldNormal @0.2

### Moonglow cymatics (not HUD)
Curvature seed → sharpen → **gaussian_spots_1** × **shape** disk tiling → **histogram_scan** edges → distance rings → warp → directionalwarp → blur → mix FrozenFracture Height×Opacity → gate **CymaticIntensity** → BeatBoost×vcol.B for emissive/mask

### Masks / PBR
Mask_Wear, Mask_Decoration (sharpened), Mask_Beat (leveled B), Mask_Cymatic · RoughnessMin→Max by wear · MetallicAccent jewelry×cymatic · Emissive Accent×(A ∪ cymatic-beat) · Opacity mostly opaque · ORM packed

### ZenLantern palette defaults
Paper `#F5ECD7` · Cedar `#8B5E3C` · Glow `#FFC978` · Shadow cool grey-lavender `(0.22, 0.20, 0.28)`

### Still Designer-optional
Fine-tune shape Pattern/Tiling, embed FrozenFracture bitmaps if a fatter offline SBSAR is desired, instance micro-graphs `MF_Melusina_*`.


---

## 10. SMS-side Resonance Bloom + VNP workflow (2026-09-24)

**Designer re-cook NOT required for this milestone.** Bloom lives in Painter SMS `SMS_Melusina_Handpaint`:

- Folder `11_VeryNormal_Workflow` (`11a_WSN_Inject` … `11d_TangentCombine`) — Melusina-owned VNP pattern; no Nhance converter SBSAR.
- Folder `15_ResonanceBloom` (`15a_ResonanceCore` … `15d_InnerEmber`) — remaps Cymatic Opacity / Metallic / Height and mesh AO into emissive **masks**.

Params (SMS layer opacities): ResonanceCore 0.55, MoonglowHalo 0.40, CharmFlash 0.35, InnerEmber 0.25.

Optional later: cheap SBSAR mask outs for Moonglow / Charm / Ember if we want one-click wiring — not blocking M2.

See `MELUSINA_SMART_MATERIAL_SPEC.md`, `PAINTER_WIRE.md`, `BUILD_RECEIPT_RESONANCE_BLOOM.md`.
