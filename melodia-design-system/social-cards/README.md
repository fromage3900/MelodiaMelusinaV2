# Melodia Social Card Templates

Reusable post layouts for portfolio updates, sculpt studies, sketches, shader breakdowns, and process carousels.

North star: premium fantasy artbook meets professional technical documentation. These templates stay close to the original Melodia direction:

- Fraunces / Cinzel / IBM Plex Mono style roles.
- Ivory editorial and Astral Night surfaces.
- Champagne gold rules, constellation fields, ornate corners, and asset-passport metadata.
- Ornament supports the information. It should never compete with the artwork.

## Exports

Generated PNGs live in `exports/`:

- `melodia-zbrush-sculpt-square.png` - dark asset-passport sculpt card.
- `melodia-sketch-study-square.png` - ivory editorial sketch card.
- `melodia-shader-breakdown-square.png` - technical shader breakdown card.
- `melodia-geometry-nodes-square.png` - procedural/geometry-node process card.
- `melodia-process-carousel-portrait.png` - 4:5 carousel cover.
- `melodia-blender-retopo-square.png` - Blender topology/retopo breakdown.
- `melodia-blender-trimsheet-square.png` - Blender/Substance trimsheet presentation.
- `melodia-ue-material-instance-square.png` - Unreal material instance controls.
- `melodia-ue-niagara-ambience-square.png` - Unreal Niagara ambience/VFX capture.
- `melodia-ue-pcg-route-square.png` - Unreal PCG route/debug breakdown.
- `melodia-blender-geometry-nodes-portrait.png` - 4:5 Geometry Nodes process carousel cover.

## Source Files

- `social-card-templates.html` - browser-editable layout reference.
- `generate_social_cards.py` - deterministic PNG exporter.
- `generate_layered_svgs.py` - deterministic layered SVG exporter for Figma import.
- `sources/` - named-layer SVG source files.
- `FIGMA_IRIDESCENCE_GUIDE.md` - how to create editable iridescent material effects in Figma.
- `PROJECT_REVIEW.md` - current status, editability notes, and next-pass recommendations.

## Updating Text

Edit the `CARDS` list inside `generate_social_cards.py`, then run:

```powershell
python .\social-cards\generate_social_cards.py
```

Keep copy short. The cards are intended to frame artwork or breakdown screenshots, not replace the post caption.

## Editing in Figma

Import the SVG files from `sources/`. The groups are named for editing:

- `Text/EditMe`
- `ArtworkSlot/ReplaceMe`
- `BreakdownSpecs/EditRows`
- `IridescentShaderOverlay/FigmaEditable`
- `FrameAndFiligree`
- `Metadata/Tags`

The PNG files in `exports/` are flat posting files; use the SVG files when you want layers.

The exported PNGs include the iridescent wash already baked in. The SVG files keep that wash editable as `IridescentShaderOverlay/FigmaEditable`.
