# Painter click-path - `SMS_Melusina_Handpaint` in <15 min

**Pilot mesh:** `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern\substance\meshes\ZenLantern_V2_Showcase.fbx`  
**Cymatic bitmaps:** `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial\resources\cymatic\`  
**Spec:** `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial\MELUSINA_SMART_MATERIAL_SPEC.md`  
**Plugin:** `melodia_build_sms_handpaint.py` (Documents + OneDrive Painter `python\plugins\` + `MelusinaSmartMaterial\painter_plugins\`)  
**Stack:** 01–10 + `11_VeryNormal_Workflow` + `15_ResonanceBloom`

## Scripted build (preferred)

1. Open ZenLantern Showcase in Painter (launch with the FBX above, or File → Open if an `.spp` exists). New Project if needed: **PBR Metallic Roughness**, **4K**, import **vertex colors**.
2. **Bake mesh maps** (AO, **World Space Normal**, Curvature, Position, Tangent Normal if available) + ensure `vcol_melodia` is present.  
   **Bake WSN before wiring folder 11*** (11a / 11c need it).
3. Python → Reload plugins list (or restart Painter) so the Resonance Bloom plugin is live.
4. Python console (or menu **Melodia: Build SMS_Melusina_Handpaint**):

```python
import melodia_build_sms_handpaint as m; m.build_sms()
```

5. Manual mask wires the script leaves as TODO (1–3 clicks each):  
   - `03_Cavity_Multiply` → AO generator x `vcol_melodia.R`  
   - `04_DecorationWear` → Curvature x `vcol_melodia.G`  
   - `06_BeatEmissive` → `vcol_melodia.A` (x B optional)  
   - `11a_WSN_Inject` → assign baked **World Space Normal** into Normal  
   - `11c_WSN_Anchor` → anchor / note WSN contribution as needed  
   - `11d_TangentCombine` → mesh Tangent Normal and/or shelf Very Normal Converter (optional); Melusina does not ship the converter  
   - `15a_ResonanceCore` → mask `vcol_melodia.A` (opt × B)  
   - `15b_MoonglowHalo` → if Opacity landed in mask: **INVERT**, then multiply soft Height × `vcol.B`  
   - `15c_CharmFlash` → if Metallic landed in mask: multiply by `vcol.G` (sparkle remap — do **not** write Metallic channel)  
   - `15d_InnerEmber` → AO generator + **Invert** (cavity lantern glow)
6. Right-click folder **`SMS_Melusina_Handpaint`** → **Create smart material** (if API create did not fire). Copy resulting `.spsm` →  
   `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial\exports\SMS_Melusina_Handpaint.spsm`

## Manual fallback (no script)

1. **Open** ZenLantern Showcase FBX / Texture Set (path above).
2. **Bake mesh maps** (4K, AA 4x if time): AO, **World Space Normal**, Curvature, Position. Bake or import **`vcol_melodia`** (R wear/cavity, G decoration, B audio, A emissive).
3. **Import Cymatic textures:** File → Import resources → select PNGs in `resources\cymatic\` → import to **project**. Usage = texture.
4. **Optional compare:** drag shelf Smart Material **Very Normal Paint SM** onto a spare Texture Set, note the paint-slot pattern, then delete that instance. Do **not** ship Nhance VNP inside Melusina.
5. **Optional SD look:** add Fill → assign material **SimpleDiffuse_V2** or **Melusina Simple Diffuse** SBSAR; dial params; Melusina SBSAR is preferred for ship.
6. In the Layer Stack, **Add folder** named **`SMS_Melusina_Handpaint`**.
7. Inside it, create layers **01–10** exactly as in the SPEC (Fill / Paint / folder for Cymatic). Wire masks:
   - `03` → AO generator x vcol **R**
   - `04` → Curvature x vcol **G**
   - `06` → vcol **A** (x **B** optional)
   - `10` → assign Height/Emissive/Metallic/Opacity/Normal from imported Cymatic maps; folder opacity = CymaticIntensity
8. Add folder **`11_VeryNormal_Workflow`**: `11a_WSN_Inject`, `11b_Paint`/`11b_PaintNormals`, `11c_WSN_Anchor`, `11d_TangentCombine` per SPEC.
9. Add folder **`15_ResonanceBloom`**: `15a`–`15d` emissive Add layers; remap Opacity/Metallic/AO as masks per SPEC.
10. Set Primary / Secondary / Accent to ZenLantern palette (paper `#F5ECD7` / cedar `#8B5E3C` / glow `#FFC978`); set RoughnessMin/Max + ResonanceCore / MoonglowHalo / CharmFlash / InnerEmber.
11. **Right-click folder `SMS_Melusina_Handpaint` → Create smart material.** Confirm it appears under Shelf → Smart materials.
12. Reveal in Explorer; copy the new `.spsm` to:  
    `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial\exports\SMS_Melusina_Handpaint.spsm`
13. **Permanent shelf (optional):** copy into  
    `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\assets\smart-materials\`

## Done when

- SMS applies to ZenLantern with visible cavity (R), decoration (G), glow (A), FrozenFracture accents, optional handpaint normals (11), and Resonance Bloom (15) without breaking the Melodia palette.
- No GrokBot / GrokStaged / Monolith naming; smart material is exactly **`SMS_Melusina_Handpaint`**.
- No fake `.spsm` bytes.
