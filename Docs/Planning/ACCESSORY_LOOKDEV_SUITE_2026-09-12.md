# Accessory Lookdev Suite — Technical Backend & Staging Schema

**Date:** 2026-09-12
**Status:** DRAFT — for live Blender lookdev session
**Owner:** Brennan (live lookdev) + Agent (backend/organization)

This is the **backend contract** for staging an accessory .blend file using the
existing Melodia Studio schema (Fade sky, Komikaze materials) plus the new
eyewear family. You lookdev live; I organize the technical layer.

---

## 1. Source Assets — Verified Present

| Asset | Path | Status |
|---|---|---|
| Blender 5.2.1 LTS | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` | PRESENT |
| Blender MCP | `127.0.0.1:9876` | LIVE (listening) |
| Komikaze v2 | `G:\programs\BlenderPlugins\plugins\Komikaze v2 (UNZIP ME) vfxmed\Komikaze v2.blend` | PRESENT |
| Komikaze 2.1.5 (4.2) | cached in blender asset library | PRESENT |
| Fade Assets 5.2 | `C:\Users\brenn\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\fadeassets\data\data.blend` | PRESENT |
| Master studio schema | `Tools/setup_melusina_master_studio.py` | PRESENT |
| Portfolio stage v18 | `Exports/PortfolioStages/Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` | PRESENT |
| Study scene (recent) | `Saved/MelusinasHouse/Melusinas_Study_FullNikkiDecorated.blend` | PRESENT |
| Stop flag | `Saved/Audit/MELUSINA_SHADER_AGENT_STOP` | ABSENT (proceed) |

**Note:** `komikaze_stage_looks.py` is NOT a committed file. The master studio
script loads it from the `Tools/` path at runtime (`sys.path.insert(0, str(tools))`).
This is a **live-only dependency** — if it's missing, `_komikaze_append()` will
fail silently and materials won't load. Verify before the session.

---

## 2. Proposed Blend File

**New file** (not an overwrite):
```
Saved/Accessories/Melodia_Accessory_Studio_v1.blend
```

Do NOT open the portfolio stage — the studio script mutates collections, lights,
and render settings. A fresh blend isolates the accessory work.

---

## 3. Scene Schema

### 3.1 World
- **Fade Sky:** `Sky Night` appended from Fade Assets data.blend → renamed `W_MelusinaStudio_Fade`
- **Tint:** Melodia purple — zenith `(0.08, 0.06, 0.18)`, horizon `(0.55, 0.35, 0.62)`
- **Mist:** enabled, start 4.0, depth 18.0, quadratic falloff

### 3.2 Collections
```
Accessories_Studio          (root)
├── StudioSet               (hide_render=False)
│   ├── Ground              (12m plane, 1.4x scale)
│   ├── Studio_Backdrop     (7x4.2m, hidden for beauty — togglable)
│   └── Studio_FloorCard    (64-vert circle, r=2.4, shadow catcher)
├── Eyewear_Display         (the hero subject)
│   ├── Pair_Hero           (MEL_eyewear_pair on Modifier)
│   ├── Pair_Silhouette_Rect
│   ├── Pair_Silhouette_Panto
│   ├── Pair_Silhouette_CatEye
│   └── Lenses_Separate     (MEL_eyewear_lens, toggle)
├── Props_Accent            (lifestyle context, optional)
│   ├── Pedestal            (cylinder, Komikaze material)
│   └── Fabric_Silk         (plane with Komikaze silk)
├── Cameras                 (collection of all rig cameras)
├── Lights_Nikki            (key/rim/fill/gold, tuned)
└── Set_Diorama             (hide_render=True — foliage context, togglable)
```

### 3.3 Camera Rig
5 cameras, all framed to the hero pair (origin at optical centre):

| Camera | Position | Lens | Purpose |
|---|---|---|---|
| Cam_Beauty | (3.05, -4.45, 1.55) | 50mm | Hero ¾ editorial |
| Cam_Front | (0.0, -4.80, 1.35) | 55mm | Ortho-style product |
| Cam_Macro | (0.85, -1.70, 1.46) | 90mm | Hinge/detail close-up |
| Cam_Low | (2.55, -3.55, 0.40) | 42mm | Low-angle drama |
| Cam_Turntable | (3.60, -4.60, 1.60) | 52mm | Turntable orbit |

**Clip start:** 0.0005 m (default 0.1 m clips the 0.134 m glasses away).
**DOF:** Beauty + Macro only, f/2.8–3.5.

### 3.4 Lighting (Nikki beauty balance)
| Light | Energy | Color | Position |
|---|---|---|---|
| L_KeyWarm | 620 | (1.0, 0.93, 0.84) | (2.6, -2.4, 3.4) |
| L_RimPink | 380 | (1.0, 0.45, 0.72) | (-2.4, 1.6, 2.8) |
| L_FillCool | 180 | (0.45, 0.82, 1.0) | (0.4, 2.8, 2.2) |
| L_GoldKick | 90 | (1.0, 0.88, 0.45) | (1.0, -0.8, 4.5) |

Area light sizes: Key 1.8, others 1.2.

### 3.5 Render
- Engine: EEVEE Next (or EEVEE if Next unavailable)
- Resolution: 1600 x 2000 (portrait 4:5)
- TAA: 64 samples
- Bloom: 0.05
- Film: opaque (Fade sky fills frame)
- Output: PNG, RGB

---

## 4. Komikaze Material Plan

Load from `Komikaze v2.blend` via `_komikaze_link()`:

| Surface | Komikaze Material | Notes |
|---|---|---|
| Ground / floor | `Cel Shade 2 Tones (Soft)` | Neutral studio base |
| Backdrop | `Gradient (Radial)` | Subtle vignette behind hero |
| Pedestal | `Voronoi Shader (3 Tones)` | Carved-stone vibe |
| Fabric | `MEL_Mat_NikkiSurface` | Melodia wrapper: Komikaze Halftone |
| Eyewear (default) | NONE | PBR materials — see §5 |

**Palette verified present:** Wood, Tree Shader, Water (Basic/Advance), Voronoi
(Flat/3 Tone), Wireframe, The Wall, MEL_Mat_NikkiSurface, Gradient (Linear/
Radial/Freeform), Cel Shade (2/3 Tones Hard/Soft), Halftone variants.

---

## 5. Eyewear Family Integration

All 5 builders registered under category `eyewear`. Pair parameters are in
**millimetres**, converted once at the graph input (× 0.001).

### 5.1 Default Pair (hero)
- Lens Width A: 54, Lens Height B: 34, Bridge DBL: 18
- Rim Thickness: 4, Rim Depth: 6, Corner Radius: 7
- Silhouette: 0 (rect)
- Rim Edge Break: 1.0 (acetate default)
- Material: PBR acetate (Principled, roughness 0.35–0.55, clearcoat 0.6–1.0)

### 5.2 Silhouette variants (same params, Silhouette = 0/1/2)
- 0 Rect — sharp modern
- 1 Panto — round vintage (Panto Round 0.45)
- 2 Cat-Eye — editorial (Taper 0.88, Sweep 6.0)

### 5.3 Builder application
In live Blender, the eyewear is applied as a **Geometry Nodes modifier** on an
empty host object (the modifier reads group params). The pair emits front + 2
temples + 2 hinges already assembled and positioned.

**For each pair:**
1. Create empty at origin
2. Add Geometry Nodes modifier
3. Set node group to `MEL_eyewear_pair`
4. Adjust params in the modifier UI
5. Rotate -90° about X to stand up (the family lies on its side by convention)

**For lenses as a separate element:**
- Apply `MEL_eyewear_lens` as a second modifier on the same host
- Lens sits 2 mm behind the rim plane, centered on Z = 0

### 5.4 Material note
GN output ships **POSITION + NORMAL only** — no UVs, no TEXCOORD_0. Image textures
cannot be used on the frame until `MEL_eyewear_uv` is authored. For now:
- Frame: solid Principled / vertex-color masks
- Lens: alpha-blend dielectric (alpha 0.15–0.35), NOT transmission (three.js fires
  an extra full-scene render per transmissive material)

---

## 6. File Organization

```
Saved/Accessories/
├── Melodia_Accessory_Studio_v1.blend     # live working file
├── Melodia_Accessory_Studio_v1.001.blend # manual version saves
├── renders/
│   ├── beauty_001.png
│   ├── silhouette_compare_001.png
│   └── macro_hinge_001.png
└── audit/
    └── accessory_studio_session.json     # session report from setup script
```

**Version discipline:** never save over v1. Increment manually before major
changes. The studio script never auto-saves (`save_mainfile` is forbidden).

---

## 7. Live Workflow

1. **Open** `Saved/Accessories/Melodia_Accessory_Studio_v1.blend` (new, empty)
2. **Run** the setup script to establish world, studio set, cameras, lights
3. **Append** Komikaze materials to ground/backdrop/pedestal
4. **Create** host empties, apply `MEL_eyewear_pair` + `MEL_eyewear_lens` modifiers
5. **Position** 4 silhouette variants in a grid OR focus on the hero pair
6. **Lookdev** — iterate materials, lighting, camera framing live
7. **Render** from each camera, save to `renders/`
8. **Manual version save** before major changes

---

## 8. Risks / Open Questions

| Risk | Mitigation |
|---|---|
| `komikaze_stage_looks.py` is live-only | Verify in `Tools/` before session; commit if present |
| Komikaze blend path is `G:\programs\...` (desktop) | Laptop may not have G: drive; verify path or copy blend locally |
| Eyewear pair is 0.134 m wide — clip_start must be tiny | Set 0.0005 m in camera defaults |
| GN output has no UVs → no image textures | PBR solid colors + vertex masks for now |
| 5.2 EEVEE vs EEVEE Next availability | Script checks both; fall back gracefully |
| Stop flag not present | Proceed — artist consent implied by the request |

---

## 9. Next Actions

**Before the session:**
- [ ] Verify `komikaze_stage_looks.py` exists in `Tools/` (commit if so)
- [ ] Verify `Komikaze v2.blend` path is accessible from the laptop
- [ ] Create `Saved/Accessories/` directory structure

**During the session (agent-side):**
- [ ] Generate the setup script for a fresh accessory blend (not stage)
- [ ] Apply Fade sky + Komikaze materials
- [ ] Set up 5 cameras with correct clip_start
- [ ] Apply eyewear modifiers to host empties
- [ ] Render hero + silhouette variants from each camera
- [ ] Save renders + version-save the blend

---

*Draft by Melodia Agent, 2026-09-12. Review before the live session.*
