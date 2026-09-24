# GOAL — Melusina Simple Diffuse (Infinity Nikki bar)

**Product:** Melodia Melusina (rhythm-JRPG) proprietary fill engine  
**Asset:** `SBS_Melusina_SimpleDiffuse` (+ paired `SMS_Melusina_Handpaint`)  
**Bar:** Shipping stylized fashion / prop / companion materials at **Infinity Nikki** production quality — not a reskin of Nhance SimpleDiffuse.  
**Owner:** Melodia / Melusina / Companions naming only  
**Date:** 2026-09-24 · America/Toronto

---

## 1. One-sentence mission

Ship a Melodia-owned Simple Diffuse that paints like Infinity Nikki’s closet and world props: soft gouache light, readable silhouette color, magical micro-detail (cymatics), and beat-aware glow — faster than hand-authoring every map, never flatter than a fashion screenshot.

---

## 2. Why Infinity Nikki is the bar

Infinity Nikki succeeds because materials feel **designed for beauty first**, then for systems:

| Nikki pillar | What the player feels | Melusina translation |
|---|---|---|
| Fashion-readable albedo | Color blocks read at thumbnail + 4K | Primary / Secondary / Accent with intentional shadow wash, not PBR mud |
| Soft NPR light | Gentle AO, painterly edges, no harsh noise | ShadowSpread × mesh AO × `vcol_melodia.R` wear/cavity |
| Fabric / porcelain / metal hierarchy | Materials signal material class instantly | RoughnessMin/Max + MetallicAccent + Melodia palette roles |
| Magical embroidery / sparkle | Micro-story without clutter | **Cymatics** (FrozenFracture + procedural rings) on Height / Emissive / Mask |
| Outfit glow moments | Skill / emotion / night looks | BeatBoost × `vcol.B` + Emissive × `vcol.A` |
| Hand-finished normals | Brush and stitch catch light like paint | **Gouache normals from curvature** (+ stroke map), not photo-scanned grit |
| Modular wardrobe pipeline | One engine, many clothes/props | Same SBSAR fill under SMS handpaint slot across HandpaintPrep ×9 |

We do **not** copy Nikki shaders or assets. We copy the **production standard**: stylized, romantic, readable, magically detailed, pipeline-repeatable.

---

## 3. Player-facing quality goals (acceptance)

A ZenLantern (and later wardrobe / companion) material using Melusina Simple Diffuse must:

1. **Thumbnail test** — Primary / Secondary / Accent still read after 128px downscale.  
2. **Closer than 30cm** — Gouache normal shows brush/edge relief on panels, ribs, charms; no plastic flat.  
3. **Cymatic whisper** — Height + emissive rings/fracture visible in lookdev, controllable 0→hero, never default-noisy.  
4. **Beat glance** — With `vcol.B` / BeatBoost, glow pulses read in motion without crushing albedo.  
5. **Wear story** — `vcol.R` darkens cavities and lifts roughness like lived-in paint, not dirt overlays.  
6. **Decoration lane** — `vcol.G` places motif/edge color like embroidery masks in fashion kits.  
7. **Shelf parity** — One `.sbsar` in Painter materials; artists dial knobs before painting, not after fighting generators.  
8. **Surpass SimpleDiffuse_V2** — Equal or better param clarity **plus** Melusina-only: cymatic outs, gouache NFH, vcol mask outs, beat/emissive, ORM pack.

Fail any of 1–6 on ZenLantern showcase → deepen pass continues.

---

## 4. Technical deliverable (engine)

### 4.1 Graph identity
- Package: `SBS_Melusina_SimpleDiffuse`  
- Graph label: **Melusina Simple Diffuse**  
- Category: `Melodia/Melusina`  
- Pair: Painter SMS `SMS_Melusina_Handpaint` (paint slot + layered masks)

### 4.2 Required inputs
| Input | Role |
|---|---|
| PrimaryColor / SecondaryColor / AccentColor / ShadowColor | Fashion palette |
| MeshAO, Curvature, WorldNormal (opt) | Mesh truth |
| `vcol_melodia` RGBA | Wear / decoration / audio / emissive authority |
| CymaticHeight / CymaticOpacity (opt bitmaps) | FrozenFracture or procedural seed |
| BrushStrokeMap (opt) | Gouache stroke break-up |
| Knobs: ShadowSpread, CurvatureOpacity, GouacheDepth, NormalStrength, CymaticIntensity, BeatBoost, BrushStrokeIntensity, RoughnessMin/Max, MetallicAccent |

### 4.3 Required outputs
BaseColor · Normal (gouache) · Roughness · Metallic · Height · Emissive · Opacity · Mask_Wear · Mask_Decoration · Mask_Beat · Mask_Cymatic · ORM

### 4.4 Node pillars (must be denser than v1 scaffold)
1. **Color stack** — Base → AO/wear shadow → curvature secondary wash → accent rim → stroke overlay → post grade (Nikki-like soft multiply/overlay).  
2. **Gouache normal** — Curvature (+ stroke) → height shaping → blur → Normal From Height → strength; light combine with mesh normal.  
3. **Cymatics** — Procedural rings/fracture and/or FrozenFracture maps → Height / Emissive / MetallicAccent / Opacity / Mask_Cymatic; BeatBoost × vcol.B.  
4. **Mask authority** — Explicit Melodia masks for SMS and UE (wear, decoration, beat, cymatic).  
5. **Roughness story** — Clamp band + wear/cavity lifts; no random grit soup.

### 4.5 Cook / shelf
- Real `sbscooker` `.sbsar` only (no fake binaries).  
- Refresh OneDrive Painter `assets/materials/SBS_Melusina_SimpleDiffuse.sbsar`.  
- Size/density goal: clearly richer than 2.5 KB v1; chase ≥ SimpleDiffuse_V2 (~25 KB) when graph depth allows.

---

## 5. Art direction notes (Nikki language → Melusina)

- **Porcelain + paper lantern** — albedo stays cream/paper clean; shadow is cool lavender-grey, not brown mud.  
- **Cedar / lacquer accents** — Secondary on ribs, frames, charms; metallic only as jewelry kisses.  
- **Moonglow embroidery** — Cymatics = sacred geometry stitch, not sci-fi HUD.  
- **Performance makeup** — Beat emissive is stage light on cheeks of the prop (flame, glyph), not full-surface neon.  
- **Hand finish** — Normals feel brushed gouache / soft impasto at edges; never photogrammetry pores.

ZenLantern pilot palette (defaults): paper `#F5ECD7`, cedar `#8B5E3C`, glow `#FFC978`.

---

## 6. Pipeline placement

```
Mesh (HandpaintPrep) + vcol_melodia
        ↓
SBS_Melusina_SimpleDiffuse  ← fill engine (this goal)
        ↓
SMS_Melusina_Handpaint      ← paint slot + layered Melodia stack
        ↓
Export → UE (Nikki Master / Melodia NPR parents — not Custom_MS for characters)
```

UE hard rules unchanged: owner Ctrl+S only; never Monolith `save_packages` / `recompile_material`.

---

## 7. Milestones

| Milestone | Done when |
|---|---|
| **M0** v1 scaffold | Openable `.sbs` + cooked `.sbsar` on shelf (DONE 2026-09-24) |
| **M1** Nikki deepen | Color stack + gouache NFH + cymatic fork + masks denser than SimpleDiffuse_V2 param surface; ZenLantern passes §3 tests 1–6 |
| **M2** SMS bind | SMS fill uses Melusina SBSAR; PAINTER_WIRE verified on showcase |
| **M3** Kit scale | Same engine on remaining HandpaintPrep ×8 without per-asset graph forks |
| **M4** Wardrobe / doll | Character cloth/porcelain presets (Nikki Master–safe) documented |

---

## 8. Non-goals

- Cloning or redistributing Nhance SimpleDiffuse graphs/IP  
- Photoreal skin/fabric detail  
- Auto-generating finished hero gouache with zero painting (SMS paint slot remains sacred)  
- Fake `.sbsar` / `.spsm` bytes  
- Replacing HeightBlend study lanes or unrelated Melodia masters

---

## 9. Success quote (internal)

> “If it could hang in Infinity Nikki’s wardrobe UI and still feel like Melusina’s rhythm magic, we shipped it.”

---

## 10. Immediate next actions

1. Deepen Designer graph to **M1** (gouache + cymatic density).  
2. Re-cook + refresh Painter shelf.  
3. Apply on ZenLantern showcase; run §3 acceptance.  
4. Wire as SMS fill per `PAINTER_WIRE.md`.

---

## GO pointer (2026-09-24 02:27 ET)

**Active work order:** `GOAL_V2_GO.md` — Milestone M1 deepen + re-cook is IN FLIGHT.  
Vision in this document remains authoritative; V2 is the execution checklist.
