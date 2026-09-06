# GN Tension Folds + Anime Garment Research — 2026-09-03

## Community validation (we are on the right road)
- Folds Modifier (BlenderArtists #1554977 + tutorial): real-time GN folds from
  a tension/stress map, compression vs stretch separated into controllable
  behavior, micro-detail layered through normals — exactly our
  MEL_garment_tension_folds architecture (compression branch + stretch branch
  + striation). No simulation, non-destructive.
- Modifier order doctrine: armature -> tension map -> subdivision -> folds.
  Our bake-lane builders should document the same stack order for the pairing guide.
- Tension map as grayscale control mask: dark = compression/intensity, mid = neutral,
  light = suppress. Our procedurally-derived mask (edge-length deviation) is the
  unbaked equivalent; a PAINTED mask lane is the natural v2 (artist override).
- Blender 5.2 LTS XPBD (blenderdeluxe 1077): Cloth = Geometry + Pin Group +
  Stretchiness/Bendiness + Substeps/Constraint Steps + Typed Bundles World I/O;
  minimal graph = input + Cloth Dynamics + XPBD Solver. Matches our
  MEL_garment_xpbd_drape wrapper. Headless bake stays NO-GO (our verdict stands).

## v2 recommendations for the loom (ranked)
1. Paintable tension-mask input on MEL_garment_tension_folds (attribute override
   beside the procedural deviation; artist paints where folds gather).
2. Modifier-stack pairing doc (armature/Tension/subdiv/folds order) for each preset.
3. Asset-library distribution (catalog `fold modifier`, drag-and-drop) per tutorial.
4. Normal-domain micro-detail layer (wrinkle normals without extra geometry).
5. High->low wrinkle bake path (sculpt hero, bake maps) for close-up garments.

## Anime garment pipeline (Quora distilled, mapped to ours)
Sculpt hero OR simulate macro -> refine -> bake Normal/Height/AO/Curvature to
low-poly -> toon shade. Our lanes already cover: tension folds (macro),
Copernicus bakes (Height/Normal/curvature/thickness maps), retopo pre-intake
(low-poly). Missing vs this workflow: the sculpt-hero step (owner-side or
future lane) and a toon-shade mapping note for M_Master_Toon_Universal.
