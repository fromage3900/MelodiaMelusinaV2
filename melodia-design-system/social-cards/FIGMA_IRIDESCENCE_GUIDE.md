# Figma Iridescent Shader Notes

Figma cannot run a real material shader, but it can mimic the look with editable gradient layers. The layered SVG files in `sources/` include a named layer:

`Background/IridescentShaderOverlay/FigmaEditable`

After importing a card SVG into Figma:

1. Select `IridescentShaderOverlay/FigmaEditable`.
2. Keep the fill as a linear gradient.
3. Set blend mode to `Screen`, `Soft Light`, or `Overlay`.
4. Use 18-38% opacity for documentation cards, 40-55% for hero/social splash cards.
5. For a satin shader read, duplicate the layer and rotate the gradient 35-60 degrees.
6. For a sparkle mask read, clip a subtle star/noise layer inside the artwork slot.

Recommended gradient stops:

| Stop | Color | Opacity |
|---|---|---|
| 0% | `#F5E8EA` sakura tint | 0-12% |
| 28% | `#E7C9CE` dusty sakura | 24-36% |
| 54% | `#A99AD0` iris light | 22-34% |
| 78% | `#8AA9D6` astral light | 18-30% |
| 100% | `#DDC79B` gold light | 12-22% |

Usage rule: iridescence is a material cue, not a page background. Use it on shader cards, texture breakdowns, or art slots. Avoid applying it to body text or dense metadata.

## Layer Editing Order

- Replace artwork in `ArtworkSlot/ReplaceMe`.
- Edit titles in `Text/EditMe`.
- Edit technical rows in `BreakdownSpecs/EditRows`.
- Keep `FrameAndFiligree` and `Motifs/ConstellationField` locked once placed.
