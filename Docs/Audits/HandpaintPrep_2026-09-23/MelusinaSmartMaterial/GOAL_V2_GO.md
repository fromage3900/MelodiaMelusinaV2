# GOAL v2 - Melusina Simple Diffuse (Infinity Nikki bar) - GO

**Status:** ACTIVE — Milestone **M2 SMS Resonance Bloom + VNP workflow** (Designer re-cook NOT required for this SMS milestone)  
**Updated:** 2026-09-24 02:55 ET  
**Package:** `SBS_Melusina_SimpleDiffuse`  
**Pair:** `SMS_Melusina_Handpaint` (01–10 + 11 VeryNormal + 15 ResonanceBloom)  
**Pilot:** ZenLantern V2 Showcase  
**Bar:** Infinity Nikki wardrobe / world-prop production quality  
**Beat SimpleDiffuse_V2** on clarity **and** Melusina-only magic (cymatics, gouache NFH, vcol masks, beat glow, Resonance Bloom)

---

## Mission (one line)

Build Melodia's own Simple Diffuse so Melusina props and outfits look Nikki-shelf beautiful: soft gouache light, thumbnail-readable fashion color, moonglow cymatics, beat-aware glow - with a fill engine denser and more purposeful than Nhance SimpleDiffuse_V2 — paired with an SMS that owns VNP-clarity normals and Resonance Bloom emissive.

---

## M2 - SMS now (this milestone)

1. **Folder `11_VeryNormal_Workflow`** — Melusina-owned VNP pattern (`11a`–`11d`); bake WSN first; no Nhance binary embed.
2. **Folder `15_ResonanceBloom`** — emissive stack remapping Opacity / Metallic / Height / AO as glow masks; params ResonanceCore / MoonglowHalo / CharmFlash / InnerEmber.
3. **Update SPEC + plugin + PAINTER_WIRE + CLICKPATH**; sync plugin to Documents + OneDrive Painter plugins.
4. **Receipt:** `BUILD_RECEIPT_RESONANCE_BLOOM.md`
5. Designer re-cook **not** required unless adding cheap new SBSAR mask outs later.

### Preferred M2 Painter order
SBSAR as `01` fill engine → optional `11` hero normals → `15` Resonance Bloom on top of / beside `06`.

---

## M1 - Designer (still the engine bar; already cooked)

1. **Expand the Designer graph** past the 2.5 KB scaffold (done in v2 cook):
   - Color stack: Primary → AO/wear shadow → curvature Secondary wash → Accent rim → stroke overlay → soft post
   - Gouache Normal: Curvature (+ stroke) → height shape → blur → Normal From Height → NormalStrength
   - Cymatics: procedural rings/fracture + FrozenFracture bitmaps → Height / Emissive / MetallicAccent / Opacity / Mask_Cymatic; x BeatBoost x vcol.B
   - Masks: Wear (RxAO), Decoration (Gxcurv), Beat (B), Cymatic
   - RoughnessMin/Max band + wear lift; MetallicAccent jewelry only
2. **Re-cook** real `.sbsar` via `sbscooker` (no fake bytes) — already done for M1
3. **Refresh shelf:** `...\Adobe Substance 3D Painter\assets\materials\SBS_Melusina_SimpleDiffuse.sbsar`
4. **Receipt:** before/after sizes vs SimpleDiffuse_V2 (~25 KB); list what surpasses SD
5. **ZenLantern ready:** document which inputs to plug (MeshAO, Curvature, vcol_melodia, cymatic maps from `resources\`)

### Default ZenLantern palette
- Primary paper `#F5ECD7` · Secondary cedar `#8B5E3C` · Accent glow `#FFC978` · Shadow cool grey-lavender

### vcol_melodia
| Ch | Drive |
|----|--------|
| R | Wear / cavity |
| G | Decoration (+ CharmFlash gate) |
| B | Audio / beat (+ MoonglowHalo) |
| A | Emissive zones (06 + 15a) |

---

## Acceptance (ship M2 SMS if)

- [x] SPEC lists 11a–d and 15a–d with map remapping rationale
- [x] Plugin builds those folders/layers and logs TODOs
- [x] Plugin synced to Documents + OneDrive (if paths exist)
- [x] Receipt written; Melodia/Melusina names only; no fake spsm; no Grok* prefixes
- [ ] Brennan: reload plugins → `m.build_sms()` → Create smart material → copy real `.spsm` to exports

## Acceptance (ship M1 Designer only if)

- [ ] Thumbnail: 3-color read at ~128px
- [ ] Close-up: gouache normal relief visible
- [ ] CymaticIntensity 0→hero without default noise soup
- [ ] Beat glow readable without crushing albedo
- [ ] Cook exit 0; SBSAR ≥ 2456 B; shelf updated
- [ ] GRAPH_SPEC "Implemented in v2" + BUILD_RECEIPT updated
- [ ] Melodia names only

## Explicitly better than SimpleDiffuse_V2

| SD_V2 | Melusina |
|-------|----------|
| Soft diffuse / AO / curv / rim / strokes | Same clarity of knobs |
| - | Gouache Normal From Curvature |
| - | Cymatic Height/Emissive/Mask outs |
| - | vcol_melodia mask outs (W/D/B/C) |
| - | BeatBoost x audio channel |
| - | ORM + Melodia category shelf |
| - | SMS Resonance Bloom (Opacity/Metallic/AO remapped as emissive masks) |
| - | SMS Melusina-owned VNP workflow folder (no foreign binary) |

## Non-goals
No SD IP clone · no fake SBSAR/SPSM · no zero-paint auto-hero (SMS paint slot stays) · no Monolith saves · no Nhance VNP embed

## Success line
> Could hang in Infinity Nikki's wardrobe UI and still feel like Melusina's rhythm magic.

## Paths
- SBS dir: `...\MelusinaSmartMaterial\designer\SBS_Melusina_SimpleDiffuse\`
- Prior goal: `GOAL_INFINITY_NIKKI_BAR.md` (vision)
- This file: `GOAL_V2_GO.md` (execution)
- SMS receipt: `BUILD_RECEIPT_RESONANCE_BLOOM.md`
