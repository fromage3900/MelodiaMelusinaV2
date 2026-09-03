# Canonical Shorewake Outfit — Staging Pipeline (Infinity Nikki dev lens)

**Date:** 2026-09-02 · **Schema:** `melodia.canonical_outfit_pkg.v1`
**Source material:** `Saved/CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc` (all-caps canonical, `Sep 2 00:37`)
**Mesh (Blender 5.2.1 export):** `substance_staging/CanonicalOutfit/meshes/SM_CanonicalShorewake.obj` — 270,389 verts, 28 materials
**Staged project:** `substance_staging/CanonicalOutfit/spp/CanonicalOutfit.spp` — 28 open texture sets, 93 base-map resources, `saved: true`

This doc is the pipeline behind that project, written the way an Infinity Nikki developer
would reason about a hero garment: one versatile master, layered specialization, stage the
canvas for the artist, and keep expensive per-asset work only where it earns the hero bar.

---

## 1. What this pipeline is (and is not)

**It is a hand-paint staging + base-map bake kit.** The canonical full outfit is exported from
USD, staged as 28 texture sets in Substance, provisioned with two base-map families — the
**Chladni eigenmode variant maps** (ShorewakeTidepool) and the **bake-of-record AO/geometry
maps** — and handed to the artist to texture. **No maps are wired onto any set.**

That is deliberate and matches two Infinity Nikki rules tied together:
- **P2 versatile master / layered specialization** — the outfit is one stage; the artist adds
  the look; nothing is baked into a wrong-lossy guess.
- **"WPO for light, Chaos for precision, hand-paint for the authored hero** — you, the artist,
  own the material decision.

It all-caps corrects the earlier mistake: the first `.spp` attempt (`ShorewakeGarment.spp`,
09-01/02) was built from the **old Aug 31 night_pkg slotted dress** and — worse — wired the
**old original-Melusina textures** (`T_Melusina_Bow_*`, `T_Melusina_Gloves_*`, SBW…) onto the
new outfit. That would have painted the old look onto the new dress. This build throws none of
that away; it repoints the stage to the canonical and wires nothing.

---

## 2. The chain (stage by stage)

```text
CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc   [57 MB, all-caps, Sep 2 00:37]
   │  (owner's newest weighted + unwrapped export)
   ▼  Blender 5.2.1 (audio geometry-nodes compatibility, NOT 4.5)
SM_CanonicalShorewake.obj
   270,389 verts · 28 MTL materials (rigged garment layer pieces)
   284,883 vt · 0 faces-without-uv   [Painter hard-refuses UV-less meshes]
   │
   ▼  Substance Painter 11.1.1 (startup module, single instance)
CanonicalOutfit.spp  — 28 texture sets, all OPEN
   ├─ Chladni eigenmode variant maps   (ShorewakeTidepool)  → 81 resources (9×2048 + 8-frame flipbook)
   ├─ bake-of-record geometry          (sbs AO/curv/norm/thick/pos) → 7 resources
   ├─ dress relief                     (T_DressShorewake_*)  → 5 resources
   └─ (artist textures)
```

## 3. Accurate inventory — base-map resources in the CanvasOutfit.spp

| Family | Source | Maps | Drive |
|---|---|---|---|
| **Chladni variant (ShorewakeTidepool)** | `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/` | 81 (9 maps × 2048 + 8-frame flipbook) | **Eigenmode lane** — crystal plate `PlateSpec.mode_shape(2,2)+(2,3)` (1618 & 2629 Hz), standing-wave phase crawl. Color: ocean_deep→tide, white foam crests, nacre sheen. |
| **Bake-of-record geometry** | `Saved/Audit/melusina_lookdev/bake/sbs/` | 7 (`…low_ambient-occlusion / normal-from-mesh / curvature / thickness-from-mesh / position`) | sbsbaker 4K, DirectX Y+, UV-projected (shared panel bbox drift ≤0.4% U / 3.7% V) |
| **Dress relief** | `Saved/Audit/melusina_lookdev/bake/` | 5 (`T_DressShorewake_{AO,Curvature,Normal,Position,Thickness}`) | Prior relief set |

Per-material note: only the rigged garment *pieces* carry fabric maps. The shader/effect
materials in the canonical (`Cel_Shade_2_Tones__Soft_`, `Glitter`, `Gradient__Radial_*`,
`Halftone_*`, `Iridescence_002`, `M_NikkiMistCard`, `Metal_2__Matcap__002`,
`Outline_Shader___026`, `Material*`) describe **stylized effect shading**, not fabric — they
stay as open sets. Wiring the old outfit's maps there would be the exact error this build avoids.

## 4. Night-pkg hand-paint schema, reapplied

The night_pkg (08-31) defined the hand-paint schema this build mirrors (`melodia.shorewake_night_pkg.v1`):

| Schema element | night_pkg (old dress) | canonical outfit (this build) |
|---|---|---|
| Source | `Shorewake_48MAT_frozen_snapshot.blend` | `CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc` (Blender 5.2 export) |
| Texture sets | 48 `SW_Dress_P01..P48` | **28 canonical garment-layer materials** (rigged, layered pieces) |
| Mask workflow | `T_DressShorewake_PanelID_4K.png` (48 flat colors, luminance-ordered) | canonical open sets + `T_Cymatic_ShorewakeTidepool_*` + AO/geometry as paint resources |
| Base maps | sbs AO / normal / curv / thick / position (DirectX) | same sbs bake-of-record + new Chladni eigenmode variant set |
| Bake res | 4K / margin 16 / UV 0–1 | **2048** for Chladni variant, 4K geometry bake-of-record |
| Normal convention | sbs=DirectX Y+; tiling=OpenGL Y+ | Chladni variant = OpenGL Y+ (flip G on UE export) |
| Determinism | seed `20260831` everywhere | Chladni eigenmode = deterministic (physical plate, no RNG); Blender export = deterministic |
| Evidence | `night_pkg_manifest.json` + contact sheet | `canonical_outfit_pkg_manifest.json` + `CANONICAL_OUTFIT_contact_sheet.png` |

**The two channel conventions to keep straight (unchanged from night_pkg):**
- **sbsbaker geometry = DirectX Y+** (pre-flipped for UE).
- **Chladni/tiling variant normals = OpenGL Y+** — flip G on import if you mix them in one project.

## 5. Standardized PBR inputs (Nikki §1.4 lens)

Following the Infinity Nikki "standardized PBR inputs" rule, the stage feeds a normalized set,
not bespoke properties, so the artist can drop the Chladni/Albedo/Normal/ORM lanes into any UE
master:

```text
BaseColor   T_Cymatic_ShorewakeTidepool_BaseColor.png  (sRGB)
Normal      T_Cymatic_ShorewakeTidepool_Normal.png     (OpenGL → flip G to DirectX)
RM/AO/Metal T_Cymatic_ShorewakeTidepool_ORM.png        (packed R/G/B)
Height      T_Cymatic_ShorewakeTidepool_Height.png     (parallax)
Emissive    T_Cymatic_ShorewakeTidepool_Emissive.png   (sRGB; foam-glow, MPC-ready)
Iridescence T_Cymatic_ShorewakeTidepool_Iridescence.png (pearl/caustic hue shift)
+ sbs AO / curvature / thickness / position as masking + relief sources
```

## 6. Variant staging (fast hand-painted versioning)

Because the Chladni family is **eigenmode-driven and deterministic**, you get cohesive variant
base maps fast:
- Drop `T_Cymatic_ShorewakeTidepool_*` into a `START_*` fill per set, paint over it, save the
  `.spp`/export → a new canonical variant.
- The 8-frame flipbook (`_*.1..8`) is available for animated / beat-reactive lanes later — no
  new writers, texture-side only; the audio contract (single `MPC_Melodia_Palette` writer) is
  untouched.

## 7. Scripts

| Script | Role |
|---|---|
| `Tools/Houdini/sea_above_reef/canonical_outfit_painter.py` | Substance staging builder (master; self-deleting on success). Deployed as `canonical_outfit_builder.py`. |
| `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py` | Chladni variant generator (+ new `ShorewakeTidepool`). |
| `Tools/Houdini/copernicus/chladni_eigen.py` | Physics-accurate plate eigenmode solver (crystal 2,2 / 2,3). |
| Blender 5.2.1 | USD→OBJ export (audio geometry-nodes compatible). |

## 8. Evidence / files

- **Project:** `substance_staging/CanonicalOutfit/spp/CanonicalOutfit.spp` (196 MB, `saved: true`)
- **Mesh:** `substance_staging/CanonicalOutfit/meshes/SM_CanonicalShorewake.obj` + `.mtl` (28 mats)
- **Pkg manifest:** `substance_staging/CanonicalOutfit/canonical_outfit_pkg_manifest.json`
- **Contact sheet:** `substance_staging/CanonicalOutfit/CANONICAL_OUTFIT_contact_sheet.png`
- **Builder done-marker:** `painter_build_done.json` (`saved: true`, 28 sets, chladni 81 / sbs 7 / dress 5)
- **Chladni variant source:** `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/`
- **Bake-of-record:** `Saved/Audit/melusina_lookdev/bake/sbs/`

### Provenance honesty
- Uses **Blender 5.2.1 only** (NOT 4.5) — matching the audio geometry-nodes workflow requirement.
- The 270-k vert / 28-mat canonical is the newest full outfit; any future change means re-exporting
  the USDZ→OBJ with 5.2 and re-running the builder.
- No `.uasset`, no `Content/**` writes, no second author in this pass — Substance + Blender +
  Houdini only, per the working agreement.