# Monolith Mesh & Houdini Setup Gap Analysis — 2026-08-29

Purpose: the single per-monolith ledger of **what meshes the Bible demands**, **what Houdini
setups exist**, **what is missing**, and **the next setup to write**. Canon quotes come from
`Docs/Art/MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md` (§ numbers are the Bible's own).

Status legend: **BUILT** (pipeline ran, outputs on disk) · **PARTIAL** (some outputs) ·
**QUEUED** (setup named, not written) · **NOT STARTED**.

Lane roots: `Tools/Houdini/sea_above_reef/` (all builders below live there) · audit outputs in
`Saved/Audit/<lane>/` · every builder is deterministic (seeded) and writes a manifest.

---

## Tier I — Anomalous Naturalism

### #01 The Sea Above — "The Inverted Pelagic Cathedral" — PARTIAL (the flagship lane)
- **Bible Model:** translucent bell shell; 3–5 tendril ribbon families; traversal membranes;
  close-up biological surface kit. (Imply: full organism, second ocean volume, endless tendril field.)
- **Built:** coral ×6, kelp ×3 + sway LUT, islands ×3, rocks ×2, clutter ×4, flora ×3, cloth
  banners ×2, Leviathan, Drowned Organ, VDB volumes ×3, Starskiff MK2, sand texture suite,
  **jellyfish family v1 90 m / v2 GRAND 136 m / v3 SERAPH 190 m / v4 CATHEDRAL (94 parts)**
  — all four with morph contracts verified and FBX+renders; reef MI set; water graft on
  `M_Water_Oceanology_Melodia`.
- **Gaps → next setups:** ① UE import session for the jellyfish FBX family + terrain tiles
  (pending editor window) ② `build_tendril_field.py` — the "endless tendril field" as a PCG/
  ISM scatter over the arm ribbon generator ③ bell membrane interior (translucent inner
  surface, the "traversal membranes" line) ④ close-up biological surface kit (detail normal +
  canal-mask texture pass on the bell).

### #02 The Last Reflection — "The Mirror Littoral" — NOT STARTED
- **Bible Model:** simplified ray silhouette; fin/tail landmarks; portal-edge meshes;
  dual-state architecture pieces.
- **Gaps → next setups:** ① `build_reflection_ray.py` (parametric ray: wing-plan silhouette,
  whip tail; low-poly hero for dual-state swap) ② `build_portal_edges.py` (waterline portal
  frame kit) ③ dual-state architecture set (littoral town pieces with mirrored twins).
- **Priority: HIGH** — Bible P0 signature slice #3; nothing exists.

### #03 The Unfinished Whale — "The Anatomy of Distance" — NOT STARTED
- **Bible Model:** head/tail landmarks; rib fragments; close anatomical traversal surfaces;
  transitional terrain kit.
- **Gaps → next setups:** ① `build_whale_anatomy.py` — spine bezier + rib arc pairs +
  vertebrae stack + fluke landmark (parametric, reuses the molt/terrain patterns) ② rib-cave
  interior traversal surface ③ transitional terrain kit (the cloth-terrain suite generalized
  with a "connective anatomy" biome).

### #04 The Crownless Stag — "The Walking Forest" — NOT STARTED
- **Bible Model:** giant antler spires; root bridges; bark/stone contact kit.
- **Gaps → next setups:** ① `build_antler_spires.py` (L-system antlers — code-L-system pattern
  proven by the dream flora) ② `build_root_bridges.py` (sweep root bundles between anchor
  points) ③ bark/stone contact kit (texture + trim set).

## Tier II — Impossible Biology

### #05 The God That Molts — "The Graveyard of Increasing Scale" — PARTIAL
- **Bible Model:** modular shell kits at multiple scales; fracture seams; membrane interiors;
  shell biome dressing.
- **Built (tonight):** `build_molted_god.py` — 4 instars (Settlement 14 m / Cathedral 44 m /
  Mountain 280 m / FreshMolt 340 m split), golden-ratio tergum bands, golden-angle pores,
  jagged dorsal fracture; OBJs + renders.
- **Gaps → next setups:** ① v1: through-hole pores (trim ops) ② membrane interior (inner-wall
  offset surface per shell) ③ `build_fracture_plates.py` (separable broken plates for
  collapse gameplay) ④ shell biome dressing masks (symbiote growth).

### #06 The Moon Grazer — "The Diminishing Night" — NOT STARTED
- **Bible Model:** mouth/head silhouette; partial fin forms; close eye detail.
- **Gaps → next setups:** ① `build_grazer_silhouette.py` (skybox-scale head/mouth hero, reads
  at horizon) ② fin forms ③ eye landmark (Bible: "only if narratively useful" — owner call).

## Tier III — Geographic Organisms

### #07 The Shoreline Animal — "The Moving Continent" — NOT STARTED
- **Bible Model:** head landmark; scale-island kit; exposed spine regions; shoreline
  deformation setpieces.
- **Gaps → next setups:** ① `build_scale_islands.py` (scale→island kit: each scale a buildable
  island footprint — direct reuse of the island generator pattern) ② spine region meshes ③
  shoreline deformation setpieces (WPO-driven, needs the water lane).

### #08 The White Current — "The Perfect Water" — PARTIAL (another lane)
- Commit `9b79c3a9` landed 6 builders + 18 presets + stage. Not reviewed by this lane yet;
  review pending before any mesh additions.

### #09 The River Serpent — "The Pilgrimage River" — NOT STARTED
- **Bible Model:** head; scale fields; dorsal river groove; spine traversal segments.
- **Gaps → next setups:** ① `build_serpent_spine.py` (spline spine + scale fields + dorsal
  groove channel — the groove doubles as the river bed, one mesh serves both) ② head landmark
  ③ traversal segments. Shares the Shoreline Animal's scale-field kit — build once, use twice.

## Tier IV — Ontological Monoliths

### #10 The Faraway Mother — "The Mountains of Her Dress" — PARTIAL
- **Bible Model:** cloth mountain hero surfaces; seam/embroidery kits; close eye/anatomical
  landmark; traversal-scale fabric deformation zones.
- **Built:** `build_cloth_mountains.py` (v0 hero tile) + `build_terrain_suite.py` (5 biome
  tiles v0.1: Hemlands / PleatedRange / EmbroideredBasin / VeiledMountains / SeamRoad —
  OBJ + .r16 heightmaps + renders).
- **Gaps → next setups:** ① **embroidery texture kit** (stitch masks + motif atlases — the
  cancelled subagent task, re-queued) ② `build_embroidery_kit_meshes.py` (raised-stitch geometry
  kits) ③ the eye landmark (the one modeled anatomical piece) ④ fabric deformation zones
  (WPO LUTs — KelpSway pattern) ⑤ fabric detail normal textures for the tile materials.

### #11 The Folded Sea — "The Ocean Drapery" — NOT STARTED
- **Bible Model:** hero folded-water surfaces; fold seam collision/traversal meshes; exposed
  seabed kit.
- **Gaps → next setups:** ① `build_folded_sea.py` (hero folded surfaces: the cloth-mountain
  math flipped to a water sheet; WPO + collision proxy pairs) ② exposed seabed kit (reuse reef
  sand/clutter) ③ fold seam traversal meshes.

### #12 The Drowned Constellation — "The Sea of Fallen Stars" — NOT STARTED
- **Bible Model:** star-node hero assets; anatomical silhouette fragments; close polyp/crystal
  structures.
- **Gaps → next setups:** ① `build_star_nodes.py` (crystal/polyp node kit with socket for
  constellation splines) ② silhouette fragments ③ Niagra/spline constellation behavior is
  VFX-lane, not meshes.

### #13 The Horizon Eater — "The Smaller World" — NOT STARTED (terminal escalation — deliberately last)
- **Bible Model:** selected vertebrae; one limb/fin/sensory landmark; traversal surface kit;
  final interaction anatomy.
- **Gaps → next setups:** everything. Deliberately after #03 and #09 (vertebrae and limb kits
  should be shared builds: one anatomy library, three consumers).

---

## Shared-library strategy (the actual leverage)

Three kit families recur across monoliths — build once, consume thrice:

1. **Anatomy library** (vertebrae, ribs, scale fields, limb/fin landmarks): #03, #09, #13,
   partially #07. First setup: `build_anatomy_library.py`.
2. **Fabric library** (pleat detail normals, seam masks, embroidery masks/meshes, deformation
   LUTs): #10, #11, Mara's gown (Outfit Hub), the Shorewake dress family. First setup: the
   embroidery texture kit (queued twice now — it keeps getting cancelled with subagents; run it
   in-line next).
3. **Ribbon field library** (the jelly arm generator generalized: length/count/twist/placement
   as parameters): #01 tendril field, #02 ray tail, #12 constellation splines. Exists in four
   frozen variants (v1–v4) — extract the parameter surface into `build_ribbon_field.py`.

## Execution order (this lane's next five)

1. Embroidery texture kit (in-line, headless numpy/PIL) — unblocks #10 materials + Mara's gown.
2. UE import session (jelly family + 5 terrain tiles + molt shells) — needs the editor window.
3. `build_anatomy_library.py` v0 (vertebrae + rib pair + scale field) — unblocks #03/#09/#13.
4. `build_ribbon_field.py` (generalize the jelly arm) — unblocks #01/#02/#12.
5. `build_reflection_ray.py` — opens #02, the last P0 signature slice with zero coverage.
