# ZBrush Installation + GoZ Setup Guide

**Date:** 2026-08-28
**Status:** ZBrush NOT installed — must be purchased/installed

---

## Software Status

| Software | Status | Path |
|----------|--------|------|
| ZBrush 2024/2025 | **NOT INSTALLED** | Must purchase from Maxon |
| Substance Painter | INSTALLED | `C:/Program Files/Adobe/Adobe Substance 3D Painter/` |
| Substance Designer | INSTALLED | `C:/Program Files/Adobe/Adobe Substance 3D Designer/` |
| Substance Sampler | INSTALLED | `C:/Program Files/Adobe/Adobe Substance 3D Sampler/` |
| Blender 5.2 | INSTALLED | `C:/Program Files/Blender Foundation/Blender 5.2/` |
| Blender 5.1 | INSTALLED | `C:/Program Files/Blender Foundation/Blender 5.1/` |
| Blender 4.5 | INSTALLED | `C:/Program Files/Blender Foundation/Blender 4.5/` |
| Blender 4.4-alpha | INSTALLED | `C:/Program Files/Blender Foundation/blender-4.4.0-alpha+npr-prototype/` |
| Blender 4.3 | INSTALLED | `C:/Program Files/Blender Foundation/Blender 4.3/` |
| Blender 4.2 | INSTALLED | `C:/Program Files/Blender Foundation/Blender 4.2/` |
| GoZ for Blender | **NOT INSTALLED** | Must install from ZBrush installation |

---

## Step 1: Purchase & Install ZBrush

1. Go to https://www.maxon.net/en/zbrush
2. Purchase ZBrush 2024 (~$895) or subscribe to Maxon One (~$1,200/yr)
3. Download and install to default path: `C:/Program Files/Maxon ZBrush 2024/`
4. Launch ZBrush and activate license

---

## Step 2: Install GoZ for Blender

GoZ comes with ZBrush. After installing ZBrush:

1. Navigate to `C:/Program Files/Maxon ZBrush 2024/GoZApps/`
2. Run the GoZ installer for Blender
3. Or manually copy the GoZ addon to Blender's addons folder:
   - Source: `C:/Program Files/Maxon ZBrush 2024/GoZApps/Blender/`
   - Destination: `C:/Users/froma/AppData/Roaming/Blender Foundation/Blender/5.2/scripts/addons/`
4. In Blender: Edit > Preferences > Add-ons > Install > select GoZ addon
5. Enable the GoZ addon
6. Configure GoZ path: Preferences > Add-ons > GoZ > set ZBrush path to `C:/Program Files/Maxon ZBrush 2024/`

---

## Step 3: Configure GoZ for Melusina

1. Open FinalUERig43.blend in Blender 5.2
2. Select the Melusina mesh
3. Click GoZ button (in the 3D viewport toolbar)
4. Mesh opens in ZBrush automatically
5. Sculpt in ZBrush
6. Click GoZ button in ZBrush to send back to Blender

---

## Step 4: ZBrush Sculpt Pipeline for v25

### High-Poly Sculpt

1. Start with the GoZ'd Melusina mesh
2. Use DynaMesh to add detail without topology constraints
3. Sculpt face details: eyes, nose, lips, ears
4. Sculpt hair: individual strands, volume
5. Sculpt body: muscle definition, cloth folds
6. Use layers for non-destructive editing

### Retopology

1. Use ZRemesher to create clean topology
2. Target 50-80k polygons for game-ready mesh
3. Preserve edge loops around joints (shoulders, elbows, knees)

### UV Unwrapping

1. Use UV Master (ZBrush plugin) for auto-UV
2. Or export to Blender for manual UV unwrap
3. Ensure UV islands are evenly spaced

### Map Baking

1. In ZBrush: Tool > Multi Map Exporter
2. Bake Normal map (2048x2048 or 4096x4096)
3. Bake Ambient Occlusion map
4. Bake Curvature map
5. Export all maps as PNG/TGA

### Texturing in Substance Painter

1. Open Substance Painter
2. File > New > select the low-poly mesh
3. Import baked maps (normal, AO, curvature)
4. Paint textures: base color, roughness, metallic, emission
5. Export as PNG/TGA for UE

---

## Step 5: Export to UE 5.8

1. In Blender: File > Export > FBX
2. Settings:
   - Scale: 1.0
   - Forward: -Z Forward
   - Up: Y Up
   - Apply Scalings: FBX All
   - Smoothing: Face
   - Include: Armature, Mesh, UVs, Materials
3. Export to `Content/Melodia/Characters/Melusina/v25/` (NEW PATH, not overwriting existing)
4. In UE: Import FBX to the new path
5. Create Material Instances with the new textures
6. Assign to the new skeletal mesh
7. Retarget Cascadeur anims to the new skeleton

---

## Alternative: No ZBrush

If you don't want to purchase ZBrush yet, you can:

1. **Sculpt in Blender** — Blender 5.2 has excellent sculpting tools (DynaTopo, Multiresolution, Remesh)
2. **Use ZBrush Core Mini** — Free version of ZBrush with limited features (~$10/mo)
3. **Use Nomad Sculpt** — $15 one-time, iPad/Windows, great for character sculpting
4. **Use existing high-poly** — The FinalUERig43.blend (812MB) may already have sculpted detail

### Blender Sculpt Pipeline (No ZBrush)

1. Open FinalUERig43.blend in Blender 5.2
2. Select mesh, enter Sculpt Mode
3. Enable DynaTopo (dynamic topology) for free sculpting
4. Sculpt face, hair, body details
5. Use Multiresolution modifier for controlled subdivision
6. UV unwrap in Blender
7. Bake maps in Blender (Render > Bake)
8. Export to Substance Painter for texturing
9. Export to UE

---

## Recommendation

**Use Blender 5.2 sculpting for now.** It's free, it's installed, and it's capable. You can always add ZBrush later for more advanced features. The Blender sculpt pipeline is:

```
FinalUERig43.blend → Blender Sculpt Mode → DynaTopo → High-poly mesh
    → Multiresolution → UV unwrap → Bake maps → Substance Painter → UE 5.8
```

This gets you to v25 without spending $895 on ZBrush.
