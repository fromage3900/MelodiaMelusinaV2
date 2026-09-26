# PAINTER_WIRE - SMS_Melusina_Handpaint ↔ SBS_Melusina_SimpleDiffuse

**When:** 2026-09-24 ~02:55 ET (America/Toronto)  
**SMS:** `SMS_Melusina_Handpaint`  
**Engine:** `SBS_Melusina_SimpleDiffuse.sbsar`  
**Naming:** Melodia / Melusina only.  
**Stack:** 01–10 + `11_VeryNormal_Workflow` + `15_ResonanceBloom`

---

## Roles

| Asset | Role |
|---|---|
| **SBSAR** | Fill / multi-output **generator** (BaseColor, Gouache Normal, Rough, Metal, Height, Emissive, Opacity, 4 masks, ORM) |
| **SMS_Melusina_Handpaint** | Painter **workflow stack** (paint slot + grade + cymatic + VNP normals + Resonance Bloom) |
| **FrozenFracture bitmaps** | Accent maps — bind as SBSAR inputs **or** keep on SMS folder `10_Cymatic_FrozenFracture`; also remapped as **masks** in folder 15 |

Nhance `SimpleDiffuse_V2.sbsar` stays shelf reference only - not Melusina IP.  
Nhance Very Normal Paint stays shelf reference only - Melusina folder **11** is pattern-owned, no VNP binary embed.

---

## Paths (fromage)

| What | Path |
|---|---|
| Authorable SBS | `...\MelusinaSmartMaterial\designer\SBS_Melusina_SimpleDiffuse\SBS_Melusina_SimpleDiffuse.sbs` |
| Cooked export | `...\designer\SBS_Melusina_SimpleDiffuse\exports\SBS_Melusina_SimpleDiffuse.sbsar` |
| Painter shelf | `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\assets\materials\SBS_Melusina_SimpleDiffuse.sbsar` |
| Cymatic bitmaps | `...\SBS_Melusina_SimpleDiffuse\resources\T_Cymatic_FrozenFracture_*.png` (hardlinked) |

Reload Painter resources (or restart) after shelf copy.

---

## Preferred M2 order

1. **SBSAR as `01` fill engine** — Melusina Simple Diffuse drives albedo / gouache normal / rough baseline.
2. **Folder `11_VeryNormal_Workflow` (optional)** — hero handpaint normals after WSN bake; use when the prop needs VNP-clarity stroke normals.
3. **Folder `15_ResonanceBloom`** — on top of / beside `06_BeatEmissive`. Leave 06 for compat; dial 15a–d for stage-makeup bloom. Remap Opacity / Metallic / Height / AO as masks (see SPEC).

Folder `10_Cymatic_FrozenFracture` stays the bitmap accent lane (paper Opacity ~0.5, Emissive ~0.55, cedar Normal ~0.2).

---

## How SMS uses this SBSAR

### Preferred - SBSAR as `01` fill engine

1. Bake AO / Curvature / WSN / Normal; ensure `vcol_melodia` is available.
2. Folder `01_Melodia_BaseFill`: Substance fill → **Melusina Simple Diffuse**.
3. Hook inputs: MeshAO, Curvature, WorldNormal (opt), vcol_melodia, CymaticHeight/Opacity (or leave empty).
4. Enable channels: Base Color, Normal, Roughness, Metallic, Height, Emissive.
5. Keep `02_Melodia_PaintSlot` empty for hand work (VNP clarity).
6. Route mask outs (`Mask_Wear` / `Mask_Decoration` / `Mask_Beat` / `Mask_Cymatic`) into layers `03` / `04` / `06` / `10` when replacing black placeholder masks.
7. Optional: enable `11_*` after WSN bake for hero normals.
8. Wire `15_*` Resonance Bloom masks (Opacity invert, Metallic-as-sparkle, inverted AO).

### Hybrid - SMS bitmaps still own cymatics

- SBSAR drives albedo / gouache normal / rough baseline (`CymaticIntensity` low).
- Folder `10_Cymatic_FrozenFracture` keeps bitmap Height/Emissive/Metallic/Opacity/Normal.
- Folder `15` remaps those same bitmaps into emissive **masks** (does not double-write Metallic in 15c).

### Bitmap-only cymatics

Disconnect SBSAR cymatic inputs; rings live only in SMS `10_*` (+ bloom masks in `15_*`).

---

## Param map

| SMS (SPEC) | SBSAR |
|---|---|
| PrimaryColor | PrimaryColor |
| SecondaryColor | SecondaryColor |
| AccentColor | AccentColor |
| CavityIntensity | ShadowSpread (+ Mask_Wear) |
| DecorationIntensity | CurvatureOpacity |
| CymaticIntensity | CymaticIntensity |
| BeatEmissive | BeatBoost |
| RoughnessMin/Max | RoughnessMin / RoughnessMax |
| MetallicAccent | MetallicAccent |
| ResonanceCore / MoonglowHalo / CharmFlash / InnerEmber | SMS-only (Painter layer opacities; no Designer re-cook required for this milestone) |

---

## Build SMS (Painter)

```python
import melodia_build_sms_handpaint as m; m.build_sms()
```

Then right-click folder → Create smart material. See root `BUILD_RECEIPT_RESONANCE_BLOOM.md` / `BUILD_NEXT.md`.

---

## Do not

- Ship Nhance SimpleDiffuse or VNP converter as Melusina.
- Fake `.spsm` bytes.
- Use GrokBot / GrokStaged / Monolith names.
- Call Monolith `save_packages` / recompile for this SMS milestone.
