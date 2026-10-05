# MelodySlime Cymatic Bake — Bounded Plan
# 2026-10-04

## Goal
Bake creative cymatic PBR maps from the high-poly MelodySlime sculpt (280K verts) for interesting shader info.

## Assets (confirmed on disk)
- High-poly sculpt: Exports/MelodySlime/SM_MelodySlime_HighPoly.fbx (10.8 MB, 280,459 verts)
- Low-poly game mesh: Exports/MelodySlime/SM_MelodySlime.fbx (28 KB)
- Source blend: G:/BlenderArchive/MelodySlime1.blend (11.6 MB)
- Existing cymatic set: Saved/Audit/copernicus_cymatic/SlimeTideChoir/ (8 variants, 9 maps each)

## Tools Available
- Houdini 22.0.368 (hython headless, editor-open safe)
- Blender 5.2 (headless export done)
- Copernicus cymatic pipeline (29 variants, 9 maps each)
- Chladni eigenmode solver (physics-accurate plate modes)
- Jev (TypeSafe System One) for next-action selection

## Creative Bake Ideas (cymatic → shader info)
1. **Chladni nodal patterns** — bake standing-wave node lines as emissive mask (singing slime)
2. **Cymatic height → parallax** — use Chladni relief as parallax occlusion map
3. **Eigenmode displacement** — bake exact plate mode shapes as displacement map
4. **Cymatic AO** — bake AO from high-poly with cymatic-modulated ray density
5. **Iridescent thin-film** — use cymatic interference patterns as iridescence map
6. **Curvature → cymatic mask** — bake curvature from high-poly, modulate with Chladni pattern

## Bounded Steps
1. Export high-poly from Blender (DONE)
2. Write Hython bake script (normal, displacement, AO, curvature from high-poly)
3. Write cymatic modulation script (Chladni patterns → emissive/iridescence masks)
4. Run hython bakes
5. Verify outputs (PNG magic, size, manifest)
6. Report results

## Jev Audit Request
Next best step: which bake set to prioritize for maximum shader interest?
