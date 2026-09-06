# Melusina Animation Stage — Template

> Pre-lit, pre-rigged Blender template for character animation work.
> Open this file to start animating immediately — no setup required.

---

## What's in This Template

| Element | Details |
|---------|---------|
| **Character** | FinalUERig43 (canonical UE skeleton) |
| **Key Light** | Area light, 800W, warm white, 45° up-right-front |
| **Fill Light** | Area light, 300W, cool white, opposite side, lower |
| **Rim Light** | Spot light, 500W, behind subject, for silhouette edge |
| **Beauty Camera** | 85mm, f/2.8, aimed at chest (portrait) |
| **Macro Camera** | 90mm, f/2.8, aimed at head (close-up) |
| **Ground** | Shadow-catcher plane |
| **Render Settings** | 1600×2000, EEVEE Next, 30 FPS |

---

## How to Use

1. Open `Templates/Melusina_Animation_Stage.blend`
2. Import your animation (FBX from UE, or mocap from Rokoko)
3. Switch to the camera you want (Beauty or Macro)
4. Press Play to preview
5. Render > Render Animation

---

## Scene Setup

### Collections
- `Character` — Melusina rig + mesh
- `Lighting` — Key, Fill, Rim lights
- `Cameras` — Beauty, Macro
- `Stage` — Ground, backdrop

### Render Settings
- Resolution: 1600×2000 (4:5 portrait)
- Frame Rate: 30 FPS
- Engine: EEVEE Next
- Samples: 64 (preview), 256 (final)

---

## Notes

- The rig is FinalUERig43 — the canonical UE skeleton
- All lights are named and organized
- Cameras have DOF enabled for cinematic look
- Ground is a shadow catcher (invisible in render, shows shadows)

---

*Template version: 1.0 | Created: 2026-09-03*
