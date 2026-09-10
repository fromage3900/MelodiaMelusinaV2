# Social Card Project Review

## Current Status

- Eleven ready-to-post PNG defaults exist in `exports/`.
- Eleven layered SVG sources exist in `sources/` for Figma import and editing.
- HTML preview exists for browser/design review.
- PNG generation is deterministic via `generate_social_cards.py`.
- SVG generation is deterministic via `generate_layered_svgs.py`.
- Iridescent material washes are baked into PNG exports and remain editable in SVG sources.

## What Is Editable

- PNGs are flat final exports.
- SVGs are layered and Figma-friendly:
  - `Background`
  - `IridescentShaderOverlay/FigmaEditable`
  - `Motifs/ConstellationField`
  - `FrameAndFiligree`
  - `Brand`
  - `Text/EditMe`
  - `ArtworkSlot/ReplaceMe`
  - `BreakdownSpecs/EditRows`
  - `Metadata/Tags`
  - `Metadata/Footer`

## Design Fit

The templates follow the original Melodia rules:

- Premium fantasy artbook plus professional technical documentation.
- Ivory editorial and Astral Night modes.
- Thin gold rules, constellation motifs, four-point stars, and restrained ornate corners.
- `pear-fect` is only used in shader/texture cards, not personal identity copy.

## Gaps

- Current SVG text imports as text if fonts are available, but Figma may substitute fonts until Fraunces, Cinzel, Inter, and IBM Plex Mono are installed/enabled.
- The SVG sources are intentionally generic placeholders. They still need final art imports for Sakura Dream, Space Cathedral, Baroque Castle, and Bioluminescent Grotto.
- No native `.fig` file is generated. Figma import is the editing path for now.

## Recommended Next Pass

- Add 4:5 Instagram carousel inner-slide variants: `Beauty`, `Wireframe`, `Shader Graph`, `Material Stats`, `Final Notes`.
- Add vertical story/Reels cover variants.
- Add an ArtStation thumbnail set using the same SVG source structure.
- Add a Figma plugin command that builds these cards directly as frames/components.
