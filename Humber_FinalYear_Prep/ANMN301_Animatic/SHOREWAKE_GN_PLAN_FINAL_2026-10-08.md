# SHOREWAKE — FINAL GN PLAN (2026-10-08)

The geometry-node lane is **closed** except optional cleanup and the standing owner
calls. Everything below is measured (audits 2026-10-07/08, receipts in `Saved/Audit/`).

## 1. Tree census — 47 trees, dispositions

**A. Boat builders — ours, editable (all verified wired & used, 0 dead refs):**
MEL_skiff_plates · MEL_skiff_ribcage · MEL_skiff_balljoints · MEL_starskiff_hull_form ·
MEL_starskiff_hull_audio · MEL_mh_aaa_lissajous_pearl · MEL_lissajous (+ _arch_shell,
_realize, _ribbon) · MEL_heart_chain · MEL_chime_carillon_tier · MEL_chime_tube ·
MEL_balcony · MEL_cn_tiered_pagoda · MEL_filigree_wreath_ring · MEL_heraldic_banner ·
MEL_mother_draped_curtain · MEL_mother_hair_cascade (+ _b) · MEL_nikki_bead (+ _string,
_heart, _star, _star_pendant ×4) · MEL_ornament_rosette_sixpetal · MEL_star_finial.

**B. Kit & vendor — PROTECT (do not edit internals):**
Water (Advance) · Water Basic · Noise Texture (Komikaze) · Kustom Koordinates + Mapping .KK ·
Object Koordinates .KK · Emission + Transparent Output .KK · Fresnel (Hard/Soft) ·
Gradient (PBR) · Diffuse Color +Baked Diffuse .KK · World Color (Press TAB) ·
World Color +Light Source TINT .KK · Mask Mix .KK · .Alpha Input · OLD Scene Time (Animation).
Only sanctioned knobs: the Water group inputs (Mapping mode, Global Scale, Emission Strength,
wave speeds) — tune from the shader, never the tree.

**C. System — read-only:** Smooth by Angle (library, 27 modifier users + 1 local copy).

## 2. Landmark values to gate on the master merge

- Pearl seaward: realized 5246 v / 61 instances; tree `MEL_mh_aaa_lissajous_pearl`:
  DIVIDE in1 = 20.3718318939209, Curve-to-Points mode = EVALUATED. Aft: 60-bead loop.
- Chains: Chain_BoomEnd / Chain_BowRail / Chain_NestRail = 5576 v each (heart-chain group).
- Chime: 14 chimes, uniform tubes (the semitone field stays dropped — 5.2 collapses it).
- GN census: 66 modifiers, 0 with `node_group = None`.

## 3. Optional ops (owner word, one line each)

- Litter (5 provably inert nodes; wiring archived in `gn_litter_context_20261007.json`):
  chime `Index`; curtain `Combine XYZ` ×2 (Tension/Fold); hull-form `Clamp` (Symmetry);
  Water Basic `Math.019` (vendor — leave alone).
- Half-wired branches: finish (needs intent) or remove.
- D2 hide-flip (carillon vs pagoda); D4 legacy deletions — FLIP Domain + fluid_surface are
  parked and deletion-ready; WakeTrail object deletion-ready (keys already window-clean).
- Hull nails: CLOSED — all 28 verified seated (0.000 m to the full boat surface).

## 4. Rules card (traps that have bitten; full detail in the skill)

- Group-node refs read via `n.node_tree` — `n.node_group` is the MODIFIER property and
  returns NOATTR on scene nodes (false "dead tree" alarms).
- Modifier socket values: `mod.properties.inputs[identifier]["value"]` (identifier style).
- A modifier with `node_group = None` silently vanishes — rewire, then re-measure; never
  trust the wire call itself.
- Never debug by rebuilding a tree — edit node inputs on live instances.
- Keyframe removal: always `reversed(list(...))` (forward removal throws).
- After any material/hybrid pass: re-verify LanternGlow flicker cycles (emissives stay
  original) and re-measure the pearl/chain landmarks above.

## 5. Definition of done (GN lane)

Master merge passes §2 in full; no further tree edits without a demonstrated blocker;
cleanup items only on explicit request.
