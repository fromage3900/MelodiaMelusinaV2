# MELODIA GLASSES / ACCESSORY ATELIER — ULTIMATE PLAN — 2026-09-14
*Updated after full surreal_arch audit + 23 decor + 9 eyewear GN builders confirmed*

## Inventory — what we own (all committed to git)

### Eyewear (`deploy/surreal_arch/melodia_gn/eyewear.py`) — 9 builders
- `MEL_eyewear_front` — Front frame curve + Silhouette param (rect/panto/cateye/aviator/browline/round)
- `MEL_eyewear_temple` — Temple arms
- `MEL_eyewear_hinge` — Hinge hardware
- `MEL_eyewear_pair` — Assembles front + temples + hinges + lenses
- `MEL_eyewear_lens` — Lens geometry
- `MEL_eyewear_lens_gradient` — Smoky lens tint gradient
- `MEL_eyewear_tortoise` — Tortoise marble finish (COLOR_0 byte-exact)
- `MEL_eyewear_uv` — Box-projected UVs (0-1)
- `MEL_eyewear_hero` — Master hero builder (assembles all above + material slots)

### Nikki Decor (`deploy/surreal_arch/melodia_gn/nikki_decor.py`) — 8 builders
- `MEL_nikki_bead` — Pearl/drop bead (Radius, Squash, Teardrop, Faceted)
- `MEL_nikki_star` — Pointed star solid (Points, Outer/Inner Radius, Thickness)
- `MEL_nikki_heart` — Plump boolean heart (Size, Point, Depth)
- `MEL_nikki_crystal` — Faceted double-terminated crystal (Size, Sides, Upper, Lower)
- `MEL_nikki_cord` — Standalone sagging cord (Count, Length, Sag, Cord Radius)
- `MEL_nikki_bead_string` — Guide-driven bead strand (Bead Count, Bead Radius, Droop, Taper, Jitter, Cord Radius, Show Cord)
- `MEL_nikki_star_pendant` — Star pendants on drooping cord (Pendant Count, Star Size, Hang, Droop)
- `MEL_nikki_heart_filigree` — Hearts under cord + optional wreath (Heart Count, Heart Size, Hang, Droop, Filigree Wreath toggle)

### Nikki Advanced (`deploy/surreal_arch/melodia_gn/nikki_advanced_decorations.py`) — 4 builders
- `MEL_sdf_star_panel` — Star-shaped void cut into thin panel (SDF boolean)
- `MEL_heart_chain` — Heart chain progressive shrink (Repeat Zone)
- `MEL_note_head_filigree` — Musical note heads storing semitone as named attribute
- `MEL_capture_filigree` — Filigree spiral carrying curve tangent as named attribute

### Nikki Musical Legacy (`deploy/surreal_arch/melodia_gn/nikki_musical_decorations.py`) — 3 builders
- `MEL_nikki_legacy_star_pendant` — Star-shaped musical pendant (Curve Star → Curve to Mesh)
- `MEL_nikki_legacy_heart_filigree` — Heart token filigree (IcoSphere + cone pair)
- `MEL_nikki_wall_beads` — Vertical bead strings for wall siding

## Phase 0 — Enable + verify
- [ ] Enable surreal_arch addon in 9877 Blender
- [ ] Save Preferences
- [ ] Socket probe confirms 32+ GN groups loaded
- [ ] Hero builder params confirmed (Silhouette enum, base_curve, lens_tint, material slots)

## Phase 1 — Wire decor onto eyewear hero
**Approach:** Add boolean toggles to `MEL_eyewear_hero` that invoke decor sub-builders:
- `Decor_Toggle_Bead` → invokes `MEL_nikki_bead_string` hanging from TempleL/TempleR tips
- `Decor_Toggle_Star` → invokes `MEL_nikki_star_pendant` single charm
- `Decor_Toggle_Heart` → invokes `MEL_nikki_heart_filigree` + optional wreath
- `Decor_Toggle_None` → zero geometry cost (default)

**Mechanism:** Use `MEL_nikki_bead_string`'s `Guide Curve` socket — feed it a small curve object parented to each temple tip. The guide handles are already `NodeSocketObject` inputs, so they can be driven by empty/curve children of the eyewear rig.

## Phase 2 — New silhouettes (6 → 10+)
- [ ] Add: hexagonal, butterfly, navigator, Y2K mini, clubmaster
- [ ] One enum `Silhouette` drives all — same param box, instant preview

## Phase 3 — Material library (Substance + EEVEE)
- [ ] Tortoise marble (COLOR_0 byte-exact, Rochegrosse palette)
- [ ] Champagne acetate, pearl, brushed gold, iridescent lens KTX2
- [ ] Bake: Curvature/AO from high-poly → PBR textures in Substance Painter
- [ ] EEVEE: ACES 1.08, soft shadow 1024, film transparent, 1080² transparent stills per hero

## Phase 4 — Web Atelier (Three.js)
- [ ] `floral-study.html` grows: 10 silhouettes × 4 finishes × 4 lenses × 3 decor toggles = 480 variants
- [ ] Hero/Front/Hinge/Bridge + beauty/wire/clay + auto-rotate
- [ ] Shopify variant pricing from param schema

## Phase 5 — Portfolio + Pitch
- [ ] EEVEE/Cycles hero cards per silhouette + decor combo
- [ ] Upwork case study → $100 buyer becomes ongoing catalogue
- [ ] Figma Grandmaster (drag `tokens.json`)

## Done this session
- Viewer face-forward fix (32afcc5) + lens polish + figma pack (d6152e4) pushed
- Atelier polish (96f7395): tactile pressed state + vignette
- Proposal drafted (submissions/2026-09-14_3d-blender-designer_eyewear_proposal.md)
- Semester ledgers marked 6/6
- 9876/9877 ports mapped: 9876=Sheep, 9877=eyewear_demo_live

## Next action
1. User enables addon in 9877 Blender
2. Confirm all 32+ GN groups loaded via socket
3. Wire bead string decor to temple tips
