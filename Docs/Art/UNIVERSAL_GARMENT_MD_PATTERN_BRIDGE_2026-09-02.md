# Universal Garment — Marvelous Designer Pattern Bridge (2026-09-02)

**Seed:** `20260902` · **Status:** Live spec (pattern mapping inferred, needs-MD-confirmation)
**Authority:** `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md` (10-layer Chladni grid, cloth tiers, master family) · `Saved/Audit/melusina_lookdev/night_pkg_2026-08-31/garment_layers_manifest.json` (48→10, seed 20260902) · `Saved/Audit/universal_garment/md_integration_report.json` (MD install audit, seed 20260902) · `Saved/Audit/melusina_lookdev/garment_refresh/*` (PBR kits) · `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` (cloth tiers + clipping doctrine)
**Companion:** `Saved/Audit/universal_garment/md_pattern_bridge.json` (machine-validated seed)

This is **track 1b** of the universal-garment fan-out: pattern authoring + UV layout +
material seam for Marvelous Designer. It turns the **10 Mesh garment layers** into
MD-usable pattern flats, and re-transfers the verified-master-family PBR maps back
onto the MD-draped meshes.

> **Honest headless fact (from track 1a `md_integration_report.json`):** the installed
> Marvelous Designer **Enterprise OnlineAuth is GUI-only — no script/headless API on
> disk** (zero `.pyd`/`.py`, empty `PythonLib/`, stdlib-only CPython 3.7, only the GUI
> exe + QtWebEngine + uninstaller). It **does** have verified native USD export
> (Omniverse resolver + „Export garment simulation data to USD“), plus FBX/Alembic/OBJ.
> → Every drape is **operator-driven or desktop-UI-automated (cua)**; never claim a
> scripted MD automation path. Pattern authoring decisions below are **inferred** from
> the silhouette/vertex manifest and require MD confirmation — exact geometry/pattern
> piece counts are MD-authoring discretion.

---

## 1. Per-garment-layer pattern mapping (48 panels → 10 layers → MD flats)

Silhouette data is from `garment_layers_manifest.json`. `azimuth` is cylindrical
azimuth about the dress axis; `rmean/rmax` radial spread (m); `w/d` AABB width/depth (m);
`zlo/zhi/zsp` elevation span (m). All mappings are **inferred / needs-MD-confirmation.**

| Garment layer | Panels | Chladni | Tier | Master | Inferred MD pattern pieces (confirm) |
|---|---|---|---|---|---|
| `M_Underskirt` | P01 (1) | (3,5) | C | M_Universal_Enhanced_Fabric | Front + back slip panels, or a 2-3 gore circle-slip; full-azimuth waistband-to-hem slip (zsp 0.307) |
| `M_Bodice_Upper` | P02, P46 (2) | (1,3) | C | M_Master_Nikki | Upper bodice band = front (P46 lighter) + back (P02 heavy) band, meeting at princess seams |
| `M_Shoulder_Trim` | P03–P10, P13–P14 (10) | (4,8) | A | M_Master_Toon_Universal_Alpha | Left+right armhole-cap/epaulette trims (5 small pieces per side; mirrored azimuth). Rigid lace, pattern-only |
| `M_Sleeve` | P11, P12 (2) | (2,7) | C | M_Universal_Enhanced_Fabric | Two-piece sleeve (outer/back + under/inner), overlapping mid-upper arm span |
| `M_Shoulder_Ornament` | P15–P28 (14) | (8,8) | A | M_Master_Nikki | 7 mirrored bead/stud clusters per shoulder; MD applique stamps or baked detail, not draped cloth |
| `M_Bodice_Side` | P29, P45 (2) | (2,6) | C | M_Master_Nikki | Side torso panels — side gore + side-back gore meeting the front at side princess seams |
| `M_Bodice_Front` | P30, P31, P33–P44 (14) | (3,4) | C | M_Master_Nikki | Dense front yoke row re-cut to **4-6 true flats** (CF, L/R bust, yoke, underbust). 14 source panels ≠ 14 MD pieces; mirror left half |
| `M_Collar` | P32 (1) | (6,6) | A | M_Master_Toon_Universal_Alpha | Wrap-around collar band (front + back) or CF/back split at shoulder points; rigid lace, pattern-only |
| `M_Bodice_Torso` | P47 (1) | (5,7) | C | M_Master_Nikki | Two-piece princess-seam bodice (front + back shell), bust darts, separate back shell carrying the widest shoulder span (w 1.63) |
| `M_Skirt_Full` | P48 (1) | (7,9) | **B (hero)** | M_Universal_Enhanced_Fabric | **6-8 radial gores** (CF, 2-4 side, CB) or flared A-line panel set. Wide hem flare (rmax 0.604 vs waist rmean 0.265) → flared/gored cut. Monolithic P48 MUST be re-drafted into sewable gores |

**First MD hero drape = `M_Skirt_Full`** — see §4 worked example.

---

## 2. UV + texture-transfer contract

### 2.1 UV layout contract
- **Source UV state:** slotted OBJ = 31,664 UVs over 186,955 faces → sparse,
  overlapping per-panel islands. **Not transfer-ready;** the MD pattern pass re-lays UVs.
- **MD** → export with **„Unified UV Coordinates“ + „Preserve Area UV“** (verified native),
  one UV0 region per MD pattern piece, locked to a fabric region.
- **Region→layer binding:** every MD region is tagged `SW_Dress_Pxx → M_<Layer>` so
  texture assignment is deterministic. After export the draped mesh inherits this layout —
  **in UE: swap textures only, never re-unwrap**; re-run UV transfer from the `.zpac` if
  an FBX/USD path drifts UVs.
- **Seamless invariant:** all garment_refresh + cymatic maps are seamless/tiling at 2K →
  layout exactness only matters for occlusions/parallax orientation, cheap insurance for
  free MD re-layout.
- **Handedness:** height-derived normals are OpenGL Y+ (flip G on UE import); keep
  Unity-Forward / MD +Y-up vs UE Z-up flips consistent.
- **Flipbook:** `cymatic/animated/` 8-frame flipbook needs stable single-UV across frames.

Let me rewrite the markdown (this get truncated). I'll finalize in the write.

### 2.2 Master-family slot contract (no new masters)
Map sources — `garment_refresh/` (8 maps/layer: BaseColor, Normal, Height, AO, Roughness,
Metal, Iridescence, Sheen · **present**) · `garment_refresh/cymatic/` (9 maps/layer plus
Emissive, ORM, Opacity + animated flipbook · **present**) · `seasons/` (**EMPTY dir —
placeholder, no maps to bind yet**).

| Master | Usage | Slots bound |
|---|---|---|
| `M_Master_Nikki` | bodice, torso, ornament | BaseColor, Normal, Roughness, Metal/Metallic, Iridescence, Sheen, Height(parallax) |
| `M_Universal_Enhanced_Fabric` | skirt, sleeve, underskirt | BaseColor, Normal, Roughness, Metallic(near-0), Iridescence, Sheen, Height, AO/ORM-red |
| `M_Master_Toon_Universal_Alpha` | lace collars, shoulder trim | BaseColor, Normal, Roughness, Metallic, Iridescence, Sheen(fringe), **Opacity (cymatic, lace cutout)**, Height |

- **Opacity** binds only on Collar + Shoulder_Trim (from cymatic set). All Bodice/Sleeve/
  Underskirt/Skirt_Full stay opaque (1.0) or cymatic Opacity=1.0.
- **Selection rule:** neutral derived maps default to `garment_refresh` (Moon palette);
  swap to `cymatic` for emissive/iridescence (the „sing“). When `seasons/` is populated,
  its seasonal variants override neutral BaseColor/Iridescence.
- **Per-MI naming:** `MI_Melusina_Shorewake_Cymatic_<Layer>`, one per layer on the assigned
  master, driven by the layer-restricted UV region mapping.

---

## 3. The MD authoring loop (generic, 9 steps)

1. **Source prep (offline)** — extract the layer's panel group(s) as OBJ, confirm vs manifest sha256.
2. **Draft flats (MD, INTERACTIVE)** — re-cut monolithic shells into sewable pattern pieces; assign seam allowances; mirror symmetry.
3. **Fabric properties** — map the 10 cymatic garment materials onto MD fabric presets (charmeuse/satin for bodice+skirt, silk sheet for skirt hero, rigid lace for collar/trim).
4. **Drape on Melusina silhouette** — simulate rest pose; save `.zpac` to `Saved/Audit/universal_garment/md_project/` (source of truth).
5. **Export** — FBX (primary) or USD „simulation data“ (verified native); Unified UV + Preserve Area UV.
6. **UE import (editor-gated)** — Interchange/USD importer; keep hand flips; no re-unwrap.
7. **Textures** — create per-layer MI on the assigned master; bind §2.2 slots.
8. **Cloth tier** — A rigid (static), B Chaos (hero), C WPO; depth-sort overlapping layers per clipping doctrine.
9. **Verify (LookDev)** — `capture_material_grid` on L_MaterialPreview_Studio; gate on seams/flare/lane reading.

---

## 4. Worked example — `M_Skirt_Full` (hero)

`M_Skirt_Full` (P48: 69,145 verts, full-length to floor zsp 1.211, rmean 0.265 / rmax 0.604,
w 1.112 × d 0.888) is the **tier-B hero plate** — MD drape is source of truth, Chaos handles
collision. First and best hero drape.

1. **Prepare source** — extract P48 as its own OBJ; confirm sha256; note it must be re-drafted into gores, not imported as one flat.
2. **Draft flats** — 6–8 radial gores (CF, side, CB), matching waist rmean 0.265 → hem rmax 0.604 flare; add waistband + hem allowances.
3. **Fabric** — half-satin charmeuse silk preset; tune friction/shear to hold the Chladni (7,9) flare and not sag to floor plane.
4. **Drape** — simulate on the bodied silhouette; resolve pendant folds + floor sweep; save `SKIRT_FULL_v1.zpac`.
5. **Export** — FBX (primary) or USD; Unified UV + Preserve Area UV; tag regions `M_Skirt_Full`.
6. **UE import** — Interchange/USD; hand flips; no re-unwrap.
7. **Textures** — `MI_Melusina_Shorewake_Cymatic_Skirt` on `M_Universal_Enhanced_Fabric`; bind garment_refresh BaseColor/Normal/Roughness/Metal/Iridescence/Sheen/Height/AO, cymatic Emissive/Iridescence/ORM for the sing; Opacity opaque.
8. **Cloth tier** — Chaos Cloth on the draped skirt; verify no clip against Underskirt (P01 zlo 0.734–1.041) — segment depth-sort Underskirt C/WPO under Skirt_Full B/Chaos.
9. **Verify** — LookDev gate: flare ≈ rmax 0.604, gores seam-invisible at 2K, iridescence lane reads.

**Acceptance:** draped hero skirt holds the (7,9) sheen/flare, re-textures through the
verified family with no UV seams, Chaos-collides with floor/legs within vertex budget.

---

## 5. Open questions for the MD integration track

1. **Headless gap** — MD is GUI-only; owner decision: desktop UI automation (cua) vs all-operator drapes. Pattern authoring + draping cannot be scripted on this install.
2. **Skirt_Full gore count** — manifest gives silhouette bounds only; what count conserves the rmax 0.604 hem and (7,9) node density at 2K? Needs an MD test drape.
3. **Bodice_Front dense row** — consolidate 14 slivers to a princess-seam front (4–6 pieces) or keep seam logic? Aesthetic/seam-hiding tradeoff.
4. **UV provenance** — accept MD Unified-UV re-layout vs preserve original panel islands?
5. **Seasons/** — empty; scope the per-season variant set + which map subset overrides per season (owner).
6. **Flipbook vs sim-deform** — confirm MD FBX/USD export doesn't bake per-frame UVs that break the 8-frame flipbook.
7. **Ornament + Shoulder_Trim** — do rigid studs/trims ever enter the sim, or stay baked applique/detail?
8. **Chaos spend** — confirm hero Chaos on Skirt_Full vs tier-C WPO fallback for non-hero moods.

## 6. Deliverables

| Path | What | Evidence |
|---|---|---|
| `Docs/Art/UNIVERSAL_GARMENT_MD_PATTERN_BRIDGE_2026-09-02.md` | This spec | — |
| `Saved/Audit/universal_garment/md_pattern_bridge.json` | Machine-validated seed 20260902: per-layer table, UV contract, texture contract, worked example, open questions | JSON valid, 10 layers |

**First MD hero drape: `M_Skirt_Full`.**