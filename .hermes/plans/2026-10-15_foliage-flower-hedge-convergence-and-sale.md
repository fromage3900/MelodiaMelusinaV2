# Melodia Foliage v0.2 — converge flower + hedge systems, texture-pack, sell

**Owner direction (2026-10-15):** fold the procedural flower lane (Resonant Blooms) and
the procedural hedge lane (Melodia Hedges) into one sellable family, on the updated
Blender 5.2 workflows, and close the gap that the mesh cards still ship without their
proper Melodia foliage textures.

Scope stays inside `deploy/surreal_arch/melodia_gn/` + `Tools/pack_*_generator.py` +
pack docs. No engine, no Config, no Content changes.

## What already exists (ground truth)
- Builders: `blooms.py` (Rose, Peony, Vine, Petal), `hedge_clutter.py`
  (Hedge, Hedge_Wild, Topiary Ball/Cone/Spline, Foliage_Clutter), `topiary_cards.py`,
  `grown_flower.py`, `trees.py`.
- Packs: `Tools/pack_bloom_generator.py` -> `ResonantBlooms_v0.1`,
  `Tools/pack_hedge_generator.py` -> `MelodiaHedges_v0.1`.
- Source textures/cards: `G:/MelodiaMelusina/MelusinaFoliage/` (FBX mesh cards +
  `foliagetextures/{leafcool,note,treble,cello,stem1,stembell}/` PBR sets +
  `foliagecards/*.png`).
- Staging proof: `Saved/Staging/MelusinaBlooms/release/...` packs run headless.

## Core gap to close
Packed .blend files ship procedural Principled colors only. They do **not** carry the
Melodia foliage texture sets, and the mesh-card scatter rigs (topiary_cards) depend on
FBX cards living outside the addon. Buyers cannot reproduce the look out of the box.

## Lane 0 — shared proof harness (first, ~45 min)
1. One `Tools/foliage_pipeline/foliage_proof.py` (clone of bloom_proof pattern):
   - `--factory-startup`, delete default cube, purge `sys.modules` (AppData stale
     copy guard), re-import from repo, assert `pkg.__file__`.
   - Build every builder in `blooms` + `hedge_clutter` + `topiary_cards` +
     `grown_flower`, vert census > 0 per stage, link-type gate (no Geometry-only
     cross-domain empty links).
   - Preset-socket audit: every `PRODUCT` key is a real input socket.
2. Gate: green + per-species vert/face census. Only then edit.

## Lane 1 — convergence edit (builders)
1. Freeze two naming conventions now: `Seed`, `Scale`, `Density` on every scatter;
   `Growth` 0..1 on everything floral. Audit both modules against this; patch missing.
2. Fold `grown_flower` into the bloom family (new `Bloom_Grown` row in the combined
   `PRODUCT` map), not a parallel lane.
3. Decide scope for `topiary_cards`: either (a) bundle the 7 FBX cards into the
   pack and keep collection scatters, or (b) drop topiary_cards from v0.2 and ship
   the procedural topiary only. Recommendation: keep procedural topiary as the sale
   SKU; ship `topiary_cards` in an advanced add-on folder with import steps.
4. Neutral-default audit (the latent-mesh-bloat rule): no “neutral” default that
   silently costs vertices.

## Lane 2 — texture packing (the actual sale gap)
1. Add `Tools/foliage_pipeline/pack_textures.py` that, given a source texture dir,
   reads a manifest list (leafcool, leaf1, leaf2, note, treble, cello, stem1,
   stembell, flower cards) and imports each PNG into `bpy.data.images`.
2. Enable autopack: `bpy.context.preferences.filepaths.use_autopack = True` before
   save, so textures embed in the .blend.
3. Build two material families in the pack scripts:
   - `MelodiaLeaf_Mat`: image textures (base/normal/alpha/roughness) from leaf sets.
   - `MelodiaCard_Mat`: named card materials for topiary scatter collections.
4. Update `pack_bloom_generator.py` and `pack_hedge_generator.py` to call the loader,
   assign these materials as defaults where inputs allow, and keep the procedural
   color materials as fallbacks (so clay mode still works).
5. Copy the texture folder into the release dir (`MelodiaFoliage/Textures/...`) and
   the 7 mesh-card FBXs into `MelodiaFoliage/Cards/`, so buyers wanting FBX/export
   paths are not hunting for files.

## Lane 3 — unified pack (one product, not two zips)
1. Create `Tools/pack_foliage_kit.py` that runs both pack generators into one root:
   `MelodiaFoliage_v0.2/{Blooms/, Hedges/, Textures/, Cards/, previews/, source/, README.md, LICENSE.txt}`.
   One top-level zip: `MelodiaFoliage_v0.2.zip`.
2. README (update from both `bloom_pack_docs` + `hedge_pack_docs`) documents:
   - the texture license/origin, how to relink, and how the card scatter works.
   - the Blender 5.2-only rule.
3. `source/` copies all four builder modules + both legacy pack scripts + the new
   unifier, for editable buyers.

## Lane 4 — render & sale-proof gates
1. Cycles CPU renders of: bloom demo + hedge demo (already) + one mixed garden
   scene that uses both families and the card-scatter topiary.
2. Fresh-Blender open test: open the packed .blend on a clean 5.2 instance, confirm
   zero missing-image prompts (autopack survived the zip round-trip).
3. Zip integrity: rebuild zip twice, compare hashes, verify `MelodiaFoliage_v0.2.zip`
   exists and non-zero.
4. Owner reviews renders + license text (draft stays draft until owner/legal).
5. List sale listing (BlenderMarket/Gumroad) outside repo — not here.

## Hard constraints
- Keep Blender headless proof first; registry PASS is not proof.
- `--factory-startup`, purge module cache (AppData stale copy trap).
- Mirror any addon-dir changes with `cp` + `cmp`.
- No Perforce submit, no touching Config/Content/Material masters.
- License terms stay DRAFT until owner finalizes.

## Progress (2026-10-15)
- Lane 0 proof: **PASS** — receipt `Saved/Audit/foliage_proof/foliage_proof_20261016T000513Z.json`.
- Lane 2 textures: helper collects **81** curated PNGs (88 files incl. 7 card FBXs); hedge pack `PACKED_VERIFY 81`; bloom pack `PACKED_VERIFY 81`; both zips ~69 MB.
- `Tools/foliage_pipeline/foliage_proof.py` green.
- `MelodiaFoliage_v0.2.zip` on disk, self-contained textures (autopack verified),
  renders in previews, builders editable in source/.
- Open tasks in CURRENT_STATE.md updated only for sale-status (no scope drift).
