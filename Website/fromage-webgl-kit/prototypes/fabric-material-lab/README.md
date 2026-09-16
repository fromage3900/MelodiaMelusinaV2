# Fabric Material Lab

**Status:** BUILT — runtime-verified in a real browser. See [`EVIDENCE.md`](./EVIDENCE.md).  
**Treasury authority:** [`../../README.md`](../../README.md)

A clean-room Three.js study of tileable PBR textile response. Six neutral-named presets, direct material controls, studio and grazing-angle inspection rigs, exportable material state, and a live diagnostics readout.

## Why this exists

The deployed portfolio viewer cannot serve as a commercial sample: it is built largely from third-party assets (KitBash3D Atlantis props, Zundamon) and project-specific ones (Melusina, Sir Melodious, Melody Tokens). This lab carries none of that.

**Every texture here is procedurally generated and owner-authored** by `BS_GodFile/Content/Python/author_fantasy_fabrics.py`. Provenance is recorded in [`../../fabric/MATERIAL_PROVENANCE_MANIFEST.json`](../../fabric/MATERIAL_PROVENANCE_MANIFEST.json).

## Presets

Identities are deliberately neutral — no product or project names.

| Preset | Textile kind | Source (owner-authored) |
|---|---|---|
| Velvet-like | pile / dual-sheen | `T_Fabric_RoyalVelvet_*` |
| Satin-like | fine weave | `T_Fabric_SheerSilk_*` |
| Brocade-like | raised jacquard | `T_Fabric_GildedBrocade_*` |
| Lace-like | openwork tracery | `T_Fabric_BaroqueLace_*` |
| Embroidered-like | raised bullion | `T_Fabric_GoldEmbroidery_*` |
| Iridescent-like | view-shift weave | `T_Fabric_CelestialWeave_*` |

## Run

```bash
# from the repository root
python -m http.server 8126 --bind 127.0.0.1
# http://localhost:8126/tools/fromage-webgl-kit/prototypes/fabric-material-lab/
```

## Measured

```text
FPS ~60 · DPR 1.00 · draw calls 1 · triangles 39,000 · console errors 1 (favicon)
phone width 390px · no horizontal overflow
```

## Constraints honoured

- No Melodia characters, names, logos, music or project-specific textures.
- No third-party commercial IP.
- Deployed portfolio pages **unchanged** by this pass.
- Mobile-width behaviour verified; `prefers-reduced-motion` disables the turntable.
- Graceful fallback when WebGL is unavailable.
- No backend, accounts, ecommerce, CMS or external API scope.
