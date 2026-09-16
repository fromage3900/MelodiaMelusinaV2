# Fabric Material Lab — Evidence

**Status:** BUILT AND RUNTIME-VERIFIED IN A REAL BROWSER  
**Date:** 2026-09-11  
**Path:** `tools/fromage-webgl-kit/prototypes/fabric-material-lab/`  
**Treasury authority:** [`../../README.md`](../../README.md)

A clean-room Three.js study of tileable PBR textile response. Six neutral-named presets, direct material controls, two inspection lighting rigs, an exportable material state, and a live diagnostics readout.

This prototype exists because the deployed portfolio viewer is not an appropriate clean commercial sample: it contains third-party and project-specific assets. This lab carries none of that.

---

## 1. Existing system inventory and extraction

The deployed system was audited before this clean-room proof was built.

| Capability | Where | Reused? |
|---|---|---|
| Fabric preset switching | `wix/melodia-3d-viewport.js` (`FABRIC_SETS`) | Concept reused; code **not** copied |
| BC / Normal / packed-ORM map usage | `wix/textures/pbr/` | **Textures reused** — owner-authored |
| Roughness / metalness / AO from one ORM | same | **Reused as the convention** |
| Turntable + orbit inspection | `wix/realtime-3d-viewer.html` | Reimplemented minimally |
| Channel-isolation shading modes | `wix/melodia-3d-viewport.js` | Not needed here |
| Turntable atelier surface | `wix/melodia-atelier-lab.*` | Not needed here |
| Material atlas presentation | `wix/sdf-material-gallery.html` | Not needed here |

**Reusable primitive extracted:** the packed-ORM fabric convention (`_BC` sRGB / `_N` tangent / `_ORM` = R-AO, G-roughness, B-metalness, linear), driven by neutral preset identities instead of project-specific ones.

---

## 2. Provenance — every texture classified

Full record: [`../../fabric/MATERIAL_PROVENANCE_MANIFEST.json`](../../fabric/MATERIAL_PROVENANCE_MANIFEST.json)

All six presets trace to one generator in the owner's repository:

```text
BS_GodFile/Content/Python/author_fantasy_fabrics.py
  procedural synthesis of tileable 4K / 2K PBR texture sets
  dependencies: numpy + PIL only — no texture-library import
  preset → file map: lines 610–615
```

| Preset (neutral) | Source texture | Classification |
|---|---|---|
| Velvet-like | `T_Fabric_RoyalVelvet_*` | **OWNER_AUTHORED** |
| Satin-like | `T_Fabric_SheerSilk_*` | **OWNER_AUTHORED** |
| Brocade-like | `T_Fabric_GildedBrocade_*` | **OWNER_AUTHORED** |
| Lace-like | `T_Fabric_BaroqueLace_*` | **OWNER_AUTHORED** |
| Embroidered-like | `T_Fabric_GoldEmbroidery_*` | **OWNER_AUTHORED** |
| Iridescent-like | `T_Fabric_CelestialWeave_*` | **OWNER_AUTHORED** |

**30 texture files, 9.59 MB, cleared for commercial reuse.** Preset identities are deliberately neutralized even though the underlying textures are owned.

---

## 3. Measured browser proof

Chrome on localhost, 1440×900 then 390×844. Verification harness: `tools/fromage-webgl-kit/scripts/verify/verify_fabric_lab.js`.

```text
FPS ~60 · DPR 1.00 · draw calls 1 · triangles 39,000 · textures 8.08 MB (all six sets warm)
```

| Check | Result |
|---|---|
| Page initializes, WebGL context starts | PASS |
| Preset switching | PASS — all six |
| Tint control changes material | PASS |
| Roughness / normal / sheen sliders change state | PASS |
| Grazing-angle rig | PASS |
| Wireframe toggle | PASS |
| Turntable | PASS; reduced-motion disables it |
| Exported state | PASS — valid JSON |
| Phone width 390 px | PASS — no horizontal overflow |
| Console errors | **1** — `favicon.ico` only |
| WebGL-unavailable fallback | implemented, not exercised on this machine |

### Captures

| File | Shows |
|---|---|
| `01_desktop_default.png` | Velvet-like under studio rig |
| `02_satin_like.png` | Satin-like comparison |
| `03_grazing_angle.png` | Grazing-angle inspection |
| `04_controls_changed.png` | Material controls changed |
| `05_wireframe.png` | Wireframe mode |
| `06_phone_390.png` | 390 px layout |

The grazing-angle capture visibly resolves the micro-weave through near-tangent lighting. Under the studio rig the same detail is much less apparent because low-frequency fold shading dominates; that is an honest limitation of the presentation, not a reason to inflate the claim.

---

## 4. Reused vs newly added

**Reused:** owner-authored texture library and packed-ORM convention.

**Added here:**

1. neutral preset identities;
2. tint / roughness / normal-strength / sheen controls;
3. studio + grazing inspection rigs;
4. lightweight JSON material-state export;
5. live FPS/DPR/draw-call/triangle/texture diagnostics;
6. owned procedural draped-cloth geometry;
7. graceful WebGL failure path and reduced-motion handling.

Nothing under `wix/` was modified by this proof.

---

## 5. Not claimed

- No physical colorimetry or measured BRDF.
- No automatic swatch capture or production digitization.
- Sheen is an artistic realtime approximation, not a fitted fiber model.
- No physical-phone, low-end-GPU, Safari or iOS device test.
- No stress-test performance claim; this is one 39k-triangle mesh in one draw call.
- Grazing inspection is an authored two-light rig, not a gonioreflectometer.

---

## 6. Useful client questions

1. What is the delivery target: mid-range-phone configurator, ecommerce viewer, or desktop lookdev/review tool?
2. Which materials need close physical fidelity versus simply reading convincingly on screen?
3. What source material exists already: controlled swatch photography, measurements, manufacturer maps, or only casual references?

---

## Appendix A — assets deliberately excluded

| Asset | Class | Why excluded |
|---|---|---|
| KitBash3D Atlantis props / textures | THIRD_PARTY_RESTRICTED | Licensed third-party pack |
| Zundamon | THIRD_PARTY_RESTRICTED | Third-party character IP |
| Melusina, Sir Melodious, Melody Tokens | MELODIA_SPECIFIC | Project characters |
| `T_Melusina_Shirt_*` | MELODIA_SPECIFIC | Character wardrobe material |

## Appendix B — reproduce

```bash
python -m http.server 8126 --bind 127.0.0.1
# http://localhost:8126/tools/fromage-webgl-kit/prototypes/fabric-material-lab/

node tools/fromage-webgl-kit/scripts/verify/verify_fabric_lab.js
```
