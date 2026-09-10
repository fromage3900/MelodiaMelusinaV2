# Choral Sheep — Triple-A Bake Runbook (Substance + Houdini COPs) — 2026-09-09

Companion to the night record `CHORAL_SHEEP_CYMATICS_INTEGRATION_2026-09-09.md`.
This document covers the TEXTURE side: fixed topology, fixed UCVs, professional
Substance bakes, and Houdini Copernicus Chladni bakes. Author: Melusina (agent pass
`sheep_final_prep_20260909.py`, report `Saved/Audit/choral_sheep/sheep_final_prep_report.json`).

## 1. Fixed topology (FROZEN — do not re-retopo)

| Role | Object | Faces | Quads | Manifold | Notes |
|---|---|---|---|---|---|
| LOD0 hero | `Skin_Sheep_ZSpheres2` | 5,916 | 100% | clean (0 boundary / 0 non-manifold / 0 loose) | parented to `shee` rig |
| LOD1 follow | `Retopo_Skin_Sheep_ZSpheres2` | 548 | 100% | clean | same shape family |
| HIGH | `sheephighpolydone` | 1,364,675 | 78.9% quads | clean | bake source ONLY — never ships to UE |

Welded at 0.0001, normals recalculated, verified by re-reading the saved file.
If anyone proposes Quadriflow on the LOWs: refuse. They are already 100% quad,
connected, and the coat MIs + shape keys depend on their vertex order.

## 2. Fixed UCV contract (identical on LOD0 + LOD1 → ONE texture set)

| Channel | Name | Purpose | Never do |
|---|---|---|---|
| UCV1 | `UVMap` | legacy game UV, existing coats reference it | repack, move, or rename |
| UCV2 | `BakeUV` | ALL bakes (Substance + COPs + ID) | repack after Substance project opens (stitches = texel identity) |
| HIGH UCV1 | `UVMap` | Substance "bake from mesh → select/highsource by UV" | — |

## 3. Substance Painter professional bake — exact steps

Inputs (already staged, verified sizes):
```
Saved/Audit/choral_sheep/SubstanceInput/ChoralSheep_LOD0.fbx   619 KB  (LOD0 + deform-only armature)
Saved/Audit/choral_sheep/SubstanceInput/ChoralSheep_LOD1.fbx    65 KB
Saved/Audit/choral_sheep/SubstanceInput/ChoralSheep_HIGH.fbx    60 MB (highsource)
Saved/Audit/choral_sheep/SubstanceInput/ChoralSheep_HIGH.obj    158 MB (alt highsource)
```

1. New project → mesh `ChoralSheep_LOD0.fbx` → texture set resolution **2048**,
   document bit depth 16, **UV channel: BakeUV (index 1)** — if SP shows
   `0: UVMap / 1: BakeUV`, pick 1. This is the fixed-UCV payoff.
2. Highsource: "from file" → `ChoralSheep_HIGH.fbx`, **bakeNormalsFrom=mesh**,
   max ray distance ≈ 0.02 (scene units) — the sculpt hugs the cage.
3. Bake the standard set ONCE, 2048: Normal, AO (16 rays fine), Curvature,
   Position, Texcoord, **ID map (UV: BakeUV)**. This is your Professional
   Lighting/normal layer; keep the raw bakes in `bake/` before any smart
   material touches them.
4. Paint path: wool = base color from the rekeyed v2 albedos
   (`houdini_variants_v2/ChoralWool_PC_*.png`, sat 0.38 hue-wheel done) as a
   Projection/Clone stamp source; nodal detail from the Chladni height set (§4)
   as a Height channel layer, not painted by hand — deterministic beats hand
   noise for 12 pitch classes.
5. Export preset UE4-PBR-metal-rough, but **RMAO order** (UE ORM): 2048,
   BaseColor sRGB; Normal, Roughness, Metallic, AO linear; Height linear.
   Output into `Saved/Audit/choral_sheep/substance_export/`.
6. The 12-coat truth: the sheep's UE wool master is ONE `M_Chorus_Wool_Master`
   with per-PC tints — Substance only needs ONE hero texture set (Body/face/legs
   material IDs); the fleece pattern itself is procedural (Chladni + MPC driver),
   so DO NOT let baked detail override the cymatic emissive chain. Bakes feed
   BaseColor/Normal/Roughness; Emissive stays the pattern lane (commit `7871c5ef`).
7. Handoff to UE after owner eyes: import as `choralsheepbase_*` replacements or
   new `T_ChoralSheep_*` set next to existing; MIs repoint via
   `Tools/Houdini/ingest_sheep_normals.py --src Saved/Audit/choral_sheep/sculpted_normals --verify`
   for the Normal slot, then `Content/Python/apply_choral_sheep_normals.py` in UE.

## 4. Houdini Copernicus (COPs) Chladni bakes — v3

- Generator: `Tools/Houdini/copernicus/chladni_sheep_v3.py` (hython-compatible;
  pattern math from `chladni_eigen.py` — exact simply-supported-plate eigenmodes,
  not heuristic m,n).
- 12 distinct modes (one per pitch class C→B), 1024²:
  `ChoralWool_PC_{label}_Chladni.png` (height), `_Emissive.png` (nodal glow),
  `_v3.png` (blended albedo). QA in `chladni_v3_qa.json` + contact sheet.
- H22 caps: Apprentice max save 1080², so 1024 is the professional square.
  Disk writes go through /out image ROPs only.

## 5. Verify standard (applies to every bake here)

Fresh mtime + expected size + per-map distinct sha12 + pixel-variance check.
`success: true` is not a bake. Owner eyes are ground truth for quality;
these checks are ground truth for existence.

## 6. Honest boundaries

- LOD0 BakeUV coverage measured u∈[0.001,0.999] v∈[0.001,0.763] — V wastes
  ~24%: acceptable for a bake set (islands are body-hugging), re-pack ONLY if
  SP texel density looks wrong in a test Normal bake.
- `Material.001` on LOD0 was renamed to `ME_Sheep_Coat_PC_C` in the Final blend;
  the STAGE blend is unchanged (still the old name) — re-run the script instead
  of copying meshes between the two.
- The export FBXs carry the deform-only 106-bone skeleton (rule from
  `export_choral_sheep.py`); UE retarget mapping is unchanged from
  `SK_ChoralSheep`.
- v3 Chladni maps are agent-verified for existence/variance, NOT visually
  approved — owner review pass required before they feed the wool master.
