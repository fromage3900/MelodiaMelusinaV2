# Melodia Foliage Packs — Convergence + QOL/Expansion Plan (v0.2.x)

## Convergence
- **Product keys canonical** (do not drift):
  - Hedges: `Hedge`, `Hedge_Wild`, `Topiary_Ball`, `Topiary_Cone`, `Topiary_Spline`,
    `Topiary_Heart`, `Topiary_Chladni`, `Foliage_Clutter`.
  - Blooms unchanged.
- **Asset UI tagging**: geometry groups + starters + packed images + mesh cards
  marked `asset_mark` (already wired).
- **Source trace**:
  `deploy/surreal_arch/melodia_gn/{hedge_clutter,trees,core}.py` + `Tools/pack_*_generator.py`.
  `.blend` assets carry descriptions/tags.

## Polish QOL
1. Thumbnail bundle: sample a top-down 512x512 preview per product.
2. README generator lists product keys, params, versions.
3. FBX cleanup: remove duplicate materials; ensure one UV; stable collision helper.
4. LOD variants after clipping density sweep.
5. Asset catalog `.json` in each release for importers.

## Expansion
- Chladni series: additional `(m,n)` variants plus seasons (autumn/snow) via color pass.
- Wind-topiary premium shape.
- Signed material presets tied to audio (bass-rooted).

## Executed to-date
- Heart + Chladni topiaries + their packs + dedicated MeshCards.blend + ChladniCard set.
- Asset marks + unified zip updated.
