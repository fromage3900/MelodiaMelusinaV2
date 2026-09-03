# Expanded GMM Framework — Brass Structure Modifiers (v2 Polished)

## Overview
19 brass-structure geometry modifiers (14 polished + 5 new variants) using mathematically correct formulas for tube construction, acoustic shaping, decorative filigree, and **surface aging**. All integrate with `GeometryModifier` / `ModifierStack` → `UProceduralModelingToolkitModifier`.

**v2 polish:** refined defaults, cross-param validation (clearance, wall breach, pitch), new aging/wear layer. Source truth: `Content/Python/gmm/geometry/brass_modifiers.py`.

---

## Modifier Types — 19 Total

| # | Modifier Type | Mathematical Basis | Purpose |
|---|---|---|---|
| 1 | `brass_tube` | Cylindrical extrusion + thickness sweep | Base tube/pipe primitive |
| 2 | `brass_bell_profile` | Power-law flare `r(z)=R_base+(R_tip-R_base)*(z/H)^exp` | Bell mouth shape |
| 3 | `brass_valve_cylinder` | Revolved cylinder with radial port cutouts | Valve body (piston) |
| 4 | `brass_slide_taper` | Linear interpolation between two diameters | Slide tube taper |
| 5 | `brass_tone_hole` | Circular cutout with chamfer + fillet | Tone hole in tubing |
| 6 | `brass_bracing_hoop` | Torus sweep at strategic angles | Structural bracing |
| 7 | `brass_lead_pipe` | Conical taper `R(z)=R_m-(R_m-R_l)*(z/L)^exp` + roughness | Lead-pipe taper |
| 8 | `brass_rib_formation` | Rib extrusion from tube surface | Rib/strut formation |
| 9 | `brass_filigree_spiral` | Helical wire wrap with pitch control | Decorative spiral wrap |
| 10 | `brass_filigree_chevron` | V-shaped pattern at intervals | Chevron filigree |
| 11 | `brass_mouthpiece_cup` | Parabolic cup `r(z)=R_c-(R_c-B/2)*(z/D)^2` | Mouthpiece inner |
| 12 | `brass_mouthpiece_shank` | Tapered shank with interference fit | Mouthpiece outer |
| 13 | `brass_partial_tone_holes` | Staggered holes per partial `z_n=(n*λ/2)*(1-k*d/R)` | Pitch-bending holes |
| 14 | `brass_wrap_formation` | Coiled helix with pitch/diameter | Coil/wrap formation |
| 15 | `brass_aged_patina` ✨ | Perlin noise + oxidation mask + pit field | **Aged patina / verdigris** |
| 16 | `brass_engraved_filigree` ✨ | Vector-path extrusion, depth-controlled engrave | **Engraved filigree** |
| 17 | `brass_valve_wear` ✨ | Stroke wear-band + polish curve + erosion | **Valve wear** |
| 18 | `brass_tarnish_bloom` ✨ | Sulfur tint + lacquer crackle + bloom falloff | **Tarnish bloom** |
| 19 | `brass_hammer_marks` ✨ | Stochastic dimple field + anneal tint | **Hammer marks** |

✨ = new in v2.

---

## Mathematical Formulas (All Verified)

### 1. `brass_tube` — Base Tube Primitive
```
Given: radius R, thickness T, length L, resolution N
- Cross-section: circle at radius R with wall thickness T
- Parametric: P(θ,z) = ((R+T/2·cosθ)·cos(z/L·2π), (R+T/2·cosθ)·sin(z/L·2π), T/2·sinθ+z)
- Volume: V = 2π·R·T·L
- Surface: A = 2π·(R+T/2)·L + 2π·(R-T/2)²
- Guard: T < R
```
**Params:** `radius`, `thickness`, `length`, `resolution` (8–256)

### 2. `brass_bell_profile` — Bell Mouth Taper *(polished)*
```
r(z) = R_base + (R_tip - R_base)·(z/H)^exp   exp=1.5 (flare_exponent), z∈[0,H]
- Revolve around z-axis; rim: torus minor T/4
- flare_angle_deg 2–20, flare_exponent 0.5–3.0
```
**Params:** `base_radius`, `tip_radius`, `height`, `resolution` (8–512), `flare_exponent`, `flare_angle_deg`
**Guard:** `tip_radius > base_radius` (reverse for mute).

### 3. `brass_valve_cylinder` — Valve Body *(polished)*
```
Cylinder R, piston D, port_width P, stroke S, port_count, fillet ρ
- Ports at angles 0°, 120°, 240° (port_count=3)
- Clearance: c = (R - D/2) - P/2  must be >0
- Fillet: ρ = min(P, (R-D)/3)
```
**Params:** `radius`, `piston_diameter`, `port_width`, `stroke`, `port_count` (1–8), `fillet_radius`

### 4. `brass_slide_taper` — Slide Tube *(polished)*
```
D(z) = D0 - (D0-D1)·(z/L)  + optional grease groove w=0.3·(D0-D1)
```
**Params:** `major_diameter`, `minor_diameter`, `length`, `resolution`, `grease_groove_width`

### 5. `brass_tone_hole` — Tone Hole Cutout *(polished)*
```
Hole d at height h; chamfer w=(d/2)·tan(χ/2); fillet ρ; end-correction d_eff=d+0.8·d/√(d/λ)
```
**Params:** `tube_radius`, `hole_diameter`, `height`, `chamfer_angle` (0–180), `fillet_radius`

### 6. `brass_bracing_hoop` — Structural Bracing *(polished)*
```
N hoops at θ_n=2π·n/N+A; torus major R minor d/2; weld bead r=d/6
```
**Params:** `tube_radius`, `hoop_diameter`, `count` (1–32), `angle_offset` (0–360), `weld_bead_radius`

### 7. `brass_lead_pipe` — Lead Pipe Taper *(polished)*
```
R(z)=R_m-(R_m-R_l)·(z/L)^exp  exp=0.8; roughness ε·R(z)·noise; L_eff=L·√(R_m/R_l)
```
**Params:** `mouthpiece_radius`, `lead_start_radius`, `length`, `roughness` (0–0.15), `taper_exponent` (0.3–2.0)

### 8. `brass_rib_formation` — Rib/Strut *(polished)*
```
N ribs at θ_n=2π·n/N; extruded H×W; top fillet W/4; +15% stiffness each
```
**Params:** `tube_radius`, `rib_height`, `rib_width`, `count`, `spacing`, `fillet_radius`

### 9. `brass_filigree_spiral` — Spiral Wrap *(polished)*
```
z(t)=P·t/2π, r=R+d/2, θ(t)=t  t∈[0,2π·T]; L_wire≈T·√((2πR)²+P²)
```
**Params:** `tube_radius`, `wire_diameter`, `spiral_pitch`, `turns` (1–64), `gap` (0–2)

### 10. `brass_filigree_chevron` — Chevron Pattern *(polished)*
```
V-angle α, period P, stripe W; vertex fillet W/6; stagger π phase
```
**Params:** `tube_radius`, `v_angle` (10–180), `period`, `stripe_width`, `fillet_radius`

### 11. `brass_mouthpiece_cup` — Mouthpiece Inner *(polished)*
```
r(z)=R_c-(R_c-B/2)·(z/D)²; back bore B; fillet min(T_r,D/4); V=π·∫r²dz
```
**Params:** `cup_depth`, `cup_radius`, `rim_thickness`, `back_bore_diameter` (< cup_radius)

### 12. `brass_mouthpiece_shank` — Mouthpiece Shank *(polished)*
```
linear: D_m-(D_m-D_s)·(z/L) | parabolic: ·(z/L)² | exp: D_m·exp(-k·z/L)
```
**Params:** `shank_length`, `major_diameter`, `minor_diameter`, `taper_type` ∈ {linear, parabolic, conical_exponential}

### 13. `brass_partial_tone_holes` — Staggered Tone Holes *(polished)*
```
z_n=(n·λ/2)·(1-k·d/R) k=0.75; side alternates every Δn; ΔL≈0.8·d·(1+d/R)
```
**Params:** `tube_radius`, `hole_diameter`, `start_partial` (1–16), `spacing` (1–8), `end_correction` (0.3–1.2)

### 14. `brass_wrap_formation` — Coil/Wrap *(polished)*
```
Helix z=P·t/2π r=D/2 θ=2π·t/P+A0; L_coil=W·√((πD)²+P²); clearance P-d_w>0
```
**Params:** `coil_diameter`, `wire_diameter`, `wrap_count`, `start_angle` (0–360), `pitch` (> wire_diameter)

---

### 15. `brass_aged_patina` ✨ — Aged Patina / Verdigris
```
Given: tube_radius R, coverage C∈[0,1], verdigris V∈[0,1], pit_density ρ, pit_depth d, noise_scale S, seed
- Patina mask: M(u,v) = smoothstep(1-C, 1, Perlin(S·u, S·v, seed))
  Exposure-driven: crevices (high curvature / low exposure) get M→1
- Verdigris color lerp: base brass → Cu₂(OH)₂CO₃ green via V·M
  Albedo: lerp(#B5A642 brass, #43B3AE verdigris, V·M)
- Micro-pitting: Poisson-disk points with density ρ; each pit: hemispherical
  dimple depth d, radius r_pit ~ 0.6·d, normal perturb = -d·exp(-r²/r_pit²)
- Roughness: +0.3·M (patina is matte)
```
**Params:** `tube_radius`, `coverage` (0–1), `verdigris_intensity` (0–1), `pit_density` (0–0.5), `pit_depth` (0–1mm), `noise_scale` (0.5–20), `seed` (int)
**UE:** drives `MI_Starskiff_Brass` patina mask + `T_RelicBrass_Verdigris` lerp.

### 16. `brass_engraved_filigree` ✨ — Engraved Filigree
```
Given: tube_radius R, pattern P∈{acanthus,scrollwork,guilloche,chevron,fleur_de_lis,baroque},
       engrave_depth E, line_width W, repeat_count N, angle_offset A0, relief_height H
- Pattern vectors: SVG-derived 2D paths tiled N times around circumference
  Each tile: arc length L_tile = 2πR/N; path scaled to L_tile
- Engrave: Boolean subtract along path: V-groove depth E, width W, 60° cutter
  Groove profile: triangular with fillet W/6 at bottom
- Relief: raised land H between grooves (positive displacement)
- Depth guard: E + H < wall thickness (0.7·T)
```
**Params:** `tube_radius`, `pattern` (enum), `engrave_depth` (0–2mm), `line_width`, `repeat_count` (1–64), `angle_offset` (0–360), `relief_height`
**UE:** engrave normal map + AO in `MI_Starskiff_BrassFiligree`.

### 17. `brass_valve_wear` ✨ — Valve Wear
```
Given: cylinder_radius R, stroke S, wear_band_width W<S, polish_factor P∈[0,1],
       erosion_depth E, contact_roughness ε, wear_cycles N
- Wear band: centered at S/2, Gaussian falloff σ=W/3
  Polish curve: roughness(z) = lerp(0.35, 0.06, P·exp(-((z-S/2)/σ)²))
- Erosion: radial inset E·(N/100k)^0.3 at port edges (saturation ~200k cycles)
- Contact roughness: micro-scratch anisotropy along stroke direction, amplitude ε
- Button dish: spherical cap depth 0.4·E at piston top
```
**Params:** `cylinder_radius`, `stroke`, `wear_band_width` (< stroke), `polish_factor` (0–1), `erosion_depth` (0–1), `contact_roughness` (0–0.2), `wear_cycles` (int ≥0)
**UE:** roughness + normal perturbation on valve mesh.

### 18. `brass_tarnish_bloom` ✨ — Tarnish Bloom
```
Given: tube_radius R, tarnish_level T∈[0,1], bloom_radius Rb, lacquer_crack_density D,
       fingerprint_intensity F, sulfur_tint S∈[0,1]
- Tarnish gradient: radial bloom from contact points (valve grip, bell rim)
  Falloff: T·exp(-r²/Rb²); sulfur tint shifts yellow→brown via S
  Albedo lerp: brass → #8B7355 tarnish via T·falloff
- Lacquer crackle: Voronoi cells density D; crack lines = cell edges, width 0.15mm
  Crack exposes raw brass (revert tarnish) + micro-height 0.05mm
- Fingerprint bloom: low-freq smudge texture scaled by F, modulated by handling heatmap
- Roughness: +0.15·T in bloom zones
```
**Params:** `tube_radius`, `tarnish_level` (0–1), `bloom_radius`, `lacquer_crack_density` (0–1), `fingerprint_intensity` (0–1), `sulfur_tint` (0–1)

### 19. `brass_hammer_marks` ✨ — Hammer Marks (Planishing)
```
Given: tube_radius R, dimple_diameter D, dimple_depth d, density ρ∈[0,0.8],
       jitter J∈[0,1], anneal_tint A∈[0,1], seed
- Dimple field: Poisson-disk with mean spacing D/√ρ; jitter J randomizes position
  Each dimple: spherical cap depth d, diameter D, normal perturb analytic
- Overlap: dimples may overlap if ρ>0.3 → creates organic hand-hammered look
- Anneal tint: heat discoloration lerp straw→peacock→blue via A
  Thresholds: A<0.3 straw, 0.3–0.6 peacock, >0.6 blue; modulated by dimple density
```
**Params:** `tube_radius`, `dimple_diameter`, `dimple_depth` (0–1.5), `density` (0–0.8), `jitter` (0–1), `anneal_tint` (0–1), `seed` (int)

---

## Integration with Existing Pipeline

### Adding a Brass Modifier to a Stack
```python
from gmm.geometry.modifiers import GeometryModifier, ModifierStack

stack = ModifierStack(target="SM_BrassInstrument")

# Base tube
stack.add(GeometryModifier("body_tube", "brass_tube",
    parameters={"radius": 12.5, "thickness": 1.2, "length": 350.0, "resolution": 32}))

# Bell with polished flare controls
stack.add(GeometryModifier("bell_mouth", "brass_bell_profile",
    parameters={"base_radius": 12.5, "tip_radius": 28.0, "height": 35.0, "resolution": 64,
                "flare_exponent": 1.5, "flare_angle_deg": 10.0}))

# Aged patina overlay — no geometry change, material-driven
stack.add(GeometryModifier("patina", "brass_aged_patina",
    parameters={"tube_radius": 12.5, "coverage": 0.35, "verdigris_intensity": 0.6,
                "pit_density": 0.08, "pit_depth": 0.15, "noise_scale": 4.0, "seed": 1337}))

# Valve wear (stack after valve cylinders)
stack.add(GeometryModifier("wear_v1", "brass_valve_wear",
    parameters={"cylinder_radius": 14.0, "stroke": 40.0, "wear_band_width": 6.0,
                "polish_factor": 0.7, "erosion_depth": 0.12, "wear_cycles": 50000}))

data = stack.to_dict()  # → UE adapter
```

### High-Level Builder
```python
from gmm.melodia.brass_architect import (
    build_trumpet_bb, build_trombone_bb, build_french_horn_f, build_tuba_cc,
    load_preset, list_presets,
)
stack = build_trumpet_bb(key="C", ensemble="vintage")
stack = load_preset("trumpet_aged_patina.json")
print(list_presets())  # 9 presets
```

### UE Adapter Hook
`UProceduralModelingToolkitModifier::Execute()` dispatches each `brass_*` to `Execute_brass_*(mesh, params)`.
Each validates via `validate_brass_parameters()`, generates DynamicMesh via formulas above, returns `FProceduralModelingToolkitModifierResult(success=True)`.

---

## Files — v2

| Path | Purpose |
|------|---------|
| `Content/Python/gmm/geometry/brass_modifiers.py` | 19 types: defaults + validators + `compute_brass_*` helpers |
| `Content/Python/gmm/geometry/modifiers.py` | Extended `SUPPORTED_TYPES` (=24 core + 19 brass = 43 types) |
| `Content/Python/gmm/geometry/schemas.py` | Re-exports `validate_brass_parameters` |
| `Content/Python/gmm/geometry/__init__.py` | Re-exports brass symbols |
| `Content/Python/gmm/melodia/brass_architect.py` | High-level builders: `build_trumpet_bb` etc. + `load_preset` |
| `Content/Python/gmm/melodia/brass_presets/*.json` | **9 presets** (4 original polished + 5 new variants) |
| `Plugins/ProceduralModelingToolkit/Content/Presets/*.json` | Mirror of above for UE import |

### Presets — 9 Total

| Preset | Instrument | Variant | Story |
|--------|------------|---------|-------|
| `vintage_trumpet_1920s.json` | Trumpet Bb | Heritage (polished) | Barn-find brass, original spec |
| `modern_trombone.json` | Trombone Bb | Modern (polished) | Open-wrap F-attachment |
| `period_french_horn.json` | Horn F | Period (polished) | Single horn, double-routed |
| `continental_tuba.json` | Tuba C | 4-valve (polished) | Continental system |
| `trumpet_aged_patina.json` ✨ | Trumpet Bb | **Aged patina** | Century in attic — verdigris + pits |
| `trumpet_engraved_filigree.json` ✨ | Trumpet C | **Engraved filigree** | Palace herald — acanthus + guilloche |
| `trumpet_valve_wear.json` ✨ | Trumpet Bb | **Valve wear** | 15yr daily player — polished bands |
| `trombone_tarnish_bloom.json` ✨ | Trombone Bb | **Tarnish bloom** | Smoky club case — sulfur + crackle |
| `horn_hammer_marks.json` ✨ | Horn F | **Hammer marks** | Village smith — planishing + anneal |

---

## Validation Checklist (v2)
- [ ] All radius/thickness >0 and T < R
- [ ] Bell: `tip_radius > base_radius` unless mute; `flare_exponent` 0.5–3.0
- [ ] Valves: clearance `R - D/2 - P/2 > 0`; `port_count` 1–8
- [ ] Wrap: `pitch > wire_diameter`
- [ ] Aged patina: `coverage`/`verdigris` 0–1; `pit_depth` ≤1mm
- [ ] Engraved: `engrave_depth` ≤2mm; `pattern` ∈ allowed enum
- [ ] Valve wear: `wear_band_width < stroke`; `polish_factor` 0–1
- [ ] Tarnish: all 0–1 lerps bounded
- [ ] Hammer: `dimple_depth` ≤1.5mm; `density` 0–0.8
- [ ] Stack `validate()` returns `[]`

---

## Helpers
```python
from gmm.geometry.brass_modifiers import compute_brass_volume, compute_brass_surface_area, bell_radius_at, lead_pipe_radius_at

vol = compute_brass_volume("brass_tube", {"radius": 12.5, "thickness": 1.2, "length": 350.0})
area = compute_brass_surface_area("brass_bell_profile", {"base_radius": 12.5, "tip_radius": 28.0, "height": 35.0})
r_mid = bell_radius_at(12.5, 28.0, 35.0, z=17.5, exponent=1.5)  # ~18.0
```

**Ready for world-building.** 19 modifiers cover structure + ornament + age. All parametric, all validated, all UE-ready.
