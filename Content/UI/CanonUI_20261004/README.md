# Melodia Canon UI — SVG source pack (2026-10-04)

Source of truth: native Figma Design `gzMjQjGoHLKNZh0jtexGEE` (**Melodia UI — Canon Storybook + Bow HUD**).

This folder starts the asset-by-asset UE handoff for the current Storybook runtime and Bow HUD canon. It intentionally stores **atomic vector source**, not flattened 1440×900 screens.

## Rules

- Keep labels, key letters, quest copy, values, combo text and numerals as live UMG text.
- Prefer one reusable asset plus transform/state logic over duplicate rotated copies. Example: `T_UI_BowHUD_ResonantFeather.svg` is rotated around the reticle in UMG.
- SVG here is the editable/lossless source contract. Some project machines do not have an Unreal SVG importer enabled; on those machines rasterize to transparent PNG @2×, then use the established UI texture settings.
- Do not add a second HUD owner. These files are presentation brushes for the existing Storybook/ExploreUI and Bow HUD authorities.
- 1440×900 is the design-space baseline.

## First batch

### Storybook
- four-point sparkle
- compass waypoint
- minimap player pin
- three Cosmic Orrery ring layers
- Orrery category node (numeral stays live UMG text)

### Bow HUD
- resonant feather
- reticle core
- outer timing/filigree ring
- score ring
- vitals gem
- Perfect Cadence sparkle

See `manifest.json` for Figma node IDs, native sizes, usage and UE destination hints.

## Runtime import

If the SVG importer is enabled and proven on the target machine, import the source SVGs directly.

Otherwise rasterize each SVG to a transparent PNG at **2× native size**, then import/configure it exactly like the existing Melodia UI texture pipeline:

- Compression: `TC_EDITOR_ICON`
- LOD group: `TEXTUREGROUP_UI`
- Mip generation: `TMGS_NO_MIPMAPS`
- sRGB: on
- Never Stream: on
- Preserve Border: on

Do not bake text during rasterization.

## Next batches

1. Storybook paper edges / tape / pinned labels / speech-tail atoms
2. Orrery archive tabs and category glyphs
3. Overworld minimap markers, instrument-key frames and interaction ornament
4. Bow prompt/cartouche edge pieces and target plaque atoms
5. VN panel corner cuts / choice markers
6. Rhythm Highway lane, hit-line, note-head and hold-tail atoms
