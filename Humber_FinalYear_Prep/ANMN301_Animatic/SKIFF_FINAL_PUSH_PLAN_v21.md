# SKIFF — FULL AUDIT + FINAL PUSH PLAN (v21 lane) — 2026-09-18

Companion data report: `Docs/Handoffs/SKIFF_BUILD_AUDIT_DATA_2026-09-18.md`
(auto-generated from `SHOREWAKE_proxy_v20_wake.blend`).

## 1. AUDIT — what the build actually is

| Metric | Value | Read |
|---|---|---|
| Objects | 191 (149 mesh, 32 GN hosts, 24 curves, 8 empties, 6 cams, 4 lights) | healthy, one stage |
| Visible evaluated geometry | **71,030 verts / 71,308 polys** | LIGHT — great for stills + bakes |
| Materials in use | 63 | **sprawl**: 15× `M_Regal_Brass_Filigree_Patina.00N` + 12× `M_Nail_*` + 4× `M_Rigging_*` |
| UVs | hull YES; **28 visible meshes have NO UVs** (plates, sail, nest, paddles, steps, perches, ratlines, awning, tiers, foam, jewel hosts…) | **the gating defect for texture work** |
| Texture nodes | hull 4, cushion 2, grating 2, lantern 2, rope 1, sail 2, patina family 1 each; **everything else 0** (flat colours) | the "beautiful but untextured" look |
| Hidden | 17 objects (parked options: pagoda, old pennant, sail sheet, rings…) | fine; document per-option |
| Orphans | 0 materials / 0 meshes | clean |
| Water | 40×40 m, ocean mod res 7 + emission shading + foam collar (v19) + widening-V wake (v20) | the sea reads |
| Loop | `SHOREWAKE_LOOP_v2` pixel-perfect (0 px diff f1↔f120), deltas 0.000000 | asset loops |
| FLIP Fluids | enables but registers NO operators under 5.2 → **broken** | Mantaflow fallback |

### Audit verdict
Structurally the boat is finished and coherent: she reads at thumbnail, everything
snaps flush, cloth is soft, the loop is seamless, the foam hugs the waterline, the
wake widens. What she does NOT yet have is **surface language** — the 63 flat
materials are placeholders for the look the Copernicus lane is meant to give her.

## 2. THE FIX LIST (ordered, each = one generation)

1. **UV the 28 bare meshes** (Smart UV Project headless, per object; pack islands)
   — gating step for every bake below. Hull already UV'd.
2. **Material consolidation**: the 15 `…Patina.00N` copies → ONE shared material
   (they are duplicates with identical settings); same for the `M_Nail_*`/
   `M_Rigging_*` families if truly identical (verify per pair before merging).
3. **Copernicus bake sets** (Section 3).
4. **Lower observation deck** (Section 4).
5. **The closing run**: promoted shot stills (01/07/08/13/15) → panels v3 →
   VSE v03 → MP4 re-encode. Copernicus maps applied first so the stills carry
   the final look.

## 3. COPERNICUS BAKES — the stellar route

Two proven lanes exist in the house; the boat needs BOTH, in this order:

**3a. Generated maps (numpy → PNG, `melodia-copernicus-parallax` route).**
The boat is a STYLIZED asset: its texture value is pattern, not micro-noise.
Generate 4 PBR sets procedurally at 2K, seeded, deterministic:
- `HULL_PLANK` — plank grain + nail-line dashes + cymatic caustic interference
  (the Melodia signature: the hull sings), roughness mask per plank seam.
- `PLATE_OAK` — armor plate: oak rings + forge/patina blotches + edge wear.
- `SAIL_DAMASK` — pearl damask weave + faint cymatic rosette, high sheen mask.
- `BRASS_PATINA` — brushed brass + patina mottling + edge-polish mask
  (drives: base, rough, metal, emission mask for the glow accents).
Each set = BaseColor/Normal/Roughness/Metallic(+Emission mask), 2048², EXR→PNG.

**3b. Baked-from-geometry AO/curvature (dress-bake route) for the pieces where
the silhouette matters** — hull, plates, nest, tiers, paddles: bake AO +
curvature + thickness via `Tools/Houdini/copernicus/copernicus_dress_bake.py`
pattern (adapt path names; same chain: VEX thickness/curvature → VEX AO 64-ray →
OUT_SOP → bakepreprocess → bakegeometrytextures::2.0 → denoise → /out ROPs).
NOTE the H22 truths from the skill (do NOT re-derive): File-COP `.cook()` never
writes; writes go through /out `image` ROPs (+ setres=1); Apprentice caps COP save
at 1920×1080 → **bake at 1024²** (safe) or 1080²; baker input 0 wants an IMAGE;
custom attrib slots take FLOAT only; delete stale `cop_*.png` before every run
(existence checks lie).

**3c. Wiring**: hull + hero pieces get real UVs → image textures (3a) MODULATED by
baked AO/curvature (3b) → the stage's PPV/glow stack stays untouched. The 28
UV-less pieces get either Smart-UV (preferred for hero pieces) or a triplanar
world-space fallback (world coords + ObjectInfo → Mapping) for the small fittings.

**Budget**: 3a ≈ 30-60 min of numpy/COP; 3b ≈ 2 hython firings (1024², 8-9
channels per piece) ≈ 60-90 min; wiring + re-render ≈ 60 min. Total ≈ 3-4 h —
a single overnight lane, or the daemon loop's final items.

## 4. LOWER DECK — "Melusina's observations" (recommended: YES, as a WELL)

**Why it works**: her whole arc is listening to the water; the current deck puts
her 0.43 m above the surface with a rail between her and it. A sunken well drops
her eye line to ~0.30 m over the water — close enough to watch cymatics form —
without cutting the hull.

**Spec (deterministic build, no boolean on the authored hull):**
- Placement: foredeck, x 1.95..3.05, y ±0.34 — clear of oarlocks (x −0.55/0.45),
  Perch_Bow (3.30), guards (±0.435), ladder/mast (x ~0.3).
- Coaming: octagonal brass-bound oak frame (0.10 m wide, 0.14 m tall) resting on
  the deck line z 0.875 — reads as a built well, hides the "not-cut" seam.
- Well floor: plank floor pan at z 0.72, inset 0.06 from the coaming inner edge.
- Bench: two velvet cushions (M_Cushion_Velvet) on the aft + starboard inner
  faces, seat height z 0.78 — knees at the coaming, watchable water in front.
- Brass rail: a low half-arc on the outboard (fore) rim, 0.16 m, bent to match
  the sheer; rope wrap detail from M_Rope_-1.
- A small "specimen tray" recess (0.18×0.12) in the floor pan — for shells,
  chladni tokens, a spyglass.
- Loop note: all static; foam/wake untouched. Add ONE soft glow: a small
  lantern-lit rim (LanternGlow at 0.4) so the well reads at night shots.
- Second charm (optional, same generation): fold-out stern platform at x −3.75,
  z 0.665, 0.8×0.52 m, brass hinges + rope rails — her "toes over the water"
  spot for shots 13-15.

**Verdict**: build it. It is ~40 objects of cheap geometry, it gives the animatic
a NEW acting stage (shots 07/08 ripple answer; 13/15 crossing), and it is the
strongest single "Nikki" beat left: a place the character WANTS to sit.

## 5. SEQUENCE + ACCEPTANCE

1. UV pass → 2. material merge → 3. bake sets 3a → 4. baked 3b → 5. wiring +
deck (one generation) → 6. promoted stills → 7. panels v3 → 8. VSE v03 → MP4.

Acceptance for "stellar": every visible surface either carries a real map set or
is deliberately flat (water/glow); zero UV-less hero pieces; the deck reads at
thumbnail; the loop still pixel-perfect after the changes; the MP4 re-cut carries
the final look end-to-end.
