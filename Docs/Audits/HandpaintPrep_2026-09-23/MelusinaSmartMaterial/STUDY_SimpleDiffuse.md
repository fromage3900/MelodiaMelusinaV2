# STUDY: Simple Diffuse + Very Normal Paint (on-disk)

**Generated:** '"$STAMP"' (America/Toronto)
**HandpaintPrep:** `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23`
**Scaffold:** `...\MelusinaSmartMaterial\`
**Shelf root (OneDrive, not local Documents):**
`C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\assets\`

---

## 1. Assets located

| Kind | Size | Path |
|---|---|---|
| **SimpleDiffuse_V2.sbsar** (fill / material generator) | 25,667 B | `...\assets\materials\SimpleDiffuse_V2.sbsar` |
| alg_meta | 909 B | `...\assets\materials\.alg_meta\SimpleDiffuse_V2.sbsar` |
| **Very Normal Paint SM.spsm** | 408,406 B | `...\assets\smart-materials\Very Normal Paint SM.spsm` |
| Very Normal Paint SM_1.spsm | 306,879 B | `...\assets\smart-materials\Very Normal Paint SM_1.spsm` |
| Related Melodia shelf SMS | — | `melodytoken.spsm`, `glowing_crystal.spsm`, `water_toon.spsm` |

Copies under `study_extract\` and `resources\references\`.

---

## 2. SimpleDiffuse_V2 — role & structure

### What it is
Nhance School **SimpleDiffuse** shipped as a Substance Designer–authored **`.sbsar` fill material** (not a layered `.spsm`). Painter treats it like a material/filter you drop into a Fill layer; it drives stylized diffuse shading from **baked mesh maps**.

- Magic header: `37 7A BC AF` (Substance archive) — **opaque binary**; parameter names are not fully recoverable from strings (compressed graph).
- XMP: `CreatorTool = Substance Designer`; 128×128 preview.
- alg_meta GuiName: **`SimpleDiffuse`**; graph-id: **`SimpleDiffuse_V2/SimpleDiffuse`**.

### Public parameter groups (product docs → Melusina mapping)

| SD control | Intent | Melusina analogue |
|---|---|---|
| Base Color | Main albedo | `01_Melodia_BaseFill` PrimaryColor |
| Shadow Color + Spread | Multiplied shadow | `03_Cavity_Multiply` × `vcol_melodia.R` + AO |
| AO Color + Spread | Soft AO | Mesh-map AO levels + R channel |
| Curvature Color / Opacity | Edge treatment (handpaint-friendly) | `04_EdgeWear` / decoration × curvature + G |
| Specular Color/Height/Rotation/Exponent | Soft specular cue | `05_RoughnessClamp` |
| Rim Light | Presentation glow | `06_BeatGlow` / A emissive + B audio |
| Brush Strokes FX | NPR stroke detail | `07_NPR_StrokeGrunge` |
| Gradients (bottom dark / top light) | Vertical grade | `08_VerticalGrade` |
| Post Multiply / Overlay | Final color push | `09_MelodiaGrade` |

Presets (public): Default, Stone, Gold, Bronze, Human Skin, Orc Skin.

### Architectural lesson
SD is **generator-first**: few exposed knobs → baked AO/curvature + optional stroke/grade post. Melusina should expose the **same shape of controls**, but bind masks to Melodia vertex colors + Cymatic bitmaps instead of only mesh maps.

---

## 3. Very Normal Paint SM — SPSM stack

### Format
- Header `89 48 44 46` = **HDF5** (Painter smart-material container). **Not zip** — Expand-Archive fails by design.
- Embeds filter graph: `/Very_Normal_Converter/Very_Normal_Converter?...sbsar`.

### Reconstructed layer folder stack (from HDF5 strings)

Bottom → top (Painter stack draws bottom first):

1. **Master Opacity** — group opacity gate  
2. **1. WSN** / **Add WS Normal HERE** — World-Space Normal injection (`resourcealias:NormalWorldSpace`)  
3. **2. Paint Layers** / **Paint Here** — handpaint fill/paint slot (`DataActionFill`, `strokeWires`)  
4. **3. WSN Anchor** (`DataActionAnchor`) — anchors WSN contribution  
5. **4. Tangent Normal** + **Very Normal Converter** — converts/combines toward tangent-space normal (`resourcealias:Normal`, `invert_WSN`)

Also present: `DataLayerGroup`, `DataStackLayers`, `DataLayersPreset`, `blendingMode`, `perChannelBlending`, `maskEnabled` / `geometryMaskType`.

### Architectural lesson
VNP is a **workflow SMS**: it does not paint a full PBR look for you; it scaffolds **where** normals + paint live so handpaint stays clean. Melusina should keep that clarity (dedicated paint folder + controlled wear/glow folders) while adding Melodia-specific cavity/decoration/beat/cymatic layers SD-style.

---

## 4. Confirmed `vcol_melodia` (from HandpaintPrep sources)

**Source of truth:** `vertex_paint.py` docstring + ZenLantern `paint_guide.md` Phase 5b.

| Channel | Meaning (actual code) | Painter use |
|---|---|---|
| **R** | Wear / cavity (inverted Cycles AO bake) | Multiply darken, dirt catch, cavity intensity |
| **G** | Decoration density (asset bbox rules) | Motif / edge-decoration mask |
| **B** | Audio-reactivity weight (height falloff) | Beat amplify / grade / cymatic boost |
| **A** | Emissive zones (asset rules; ZenLantern fire-box band) | Emissive fill mask |

ZenLantern palette (paint_guide): paper `#F5ECD7`, cedar `#8B5E3C`, glow `#FFC978`, cord `#F7A8B8`, metal `#6B6F7E`.

Pilot mesh: `ZenLantern_V2_Showcase.fbx` (~15.5k faces) with refreshed `vcol_melodia`.

---

## 5. SD / VNP → Melusina concept map

| Source concept | Melusina layer |
|---|---|
| SD Base Color | `01_Melodia_BaseFill` |
| SD Shadow / AO | `03_Cavity_Multiply` (R + mesh AO) |
| SD Curvature | `04_DecorationWear` (G × curvature) |
| SD Specular / roughness cue | `05_RoughnessClamp` |
| SD Rim | `06_BeatEmissive` (A × B) |
| SD Strokes | `07_NPR_StrokeGrunge` |
| SD Gradients + Post | `08_VerticalGrade` + `09_MelodiaGrade` |
| VNP Paint Here | `02_Melodia_PaintSlot` (empty paint layer for handwork) |
| VNP WSN / Tangent Normal | Mesh-map normals + optional Cymatic Normal @ low strength |
| Melodia exclusive | `10_Cymatic_FrozenFracture` (Height/Emissive/Metallic/Opacity) |

---

## 6. Blockers for binary reverse-engineering

- **SBSAR**: compressed Substance graph — no readable layer XML; study uses public param surface + alg_meta identity.
- **SPSM**: HDF5 — strings recover folder titles; full serialized layer JSON not exposed without Painter or h5py schema knowledge.
- **Decision:** do **not** invent fake `.spsm` bytes. Deliver SPEC + click-path; optional REF copy of VNP for side-by-side comparison only.

---
*See `MELUSINA_SMART_MATERIAL_SPEC.md`, `BUILD_RECEIPT.md`, `build_recipe\PAINTER_CLICKPATH.md`.*
