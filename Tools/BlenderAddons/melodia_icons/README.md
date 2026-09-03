# Melodia Studio icons (Figma → Blender)

Drop **PNG** files here (64×64 or 128×128, transparent). Filename = icon key.

| File | Used by |
|------|---------|
| `starlight.png` | Studio · Stage / Wardrobe Starlight CTA |
| `wardrobe.png` | Studio · Wardrobe panel header (optional) |
| `stage.png` | Studio · Stage |
| `generate.png` | Architecture generate (optional) |
| `gn_stack.png` | Melodia GN Stack |

## Figma export

1. Open Melodia Figma UI kit / icon frame.
2. Select component → Export → PNG @2x.
3. Rename to the keys above and place in this folder.
4. Reload Melodia Studio addon (or Restart Blender).

Blender cannot load Figma files live — only exported PNGs via `bpy.utils.previews`.
Panels use `icon_loader.icon_kwargs(key, fallback)` so missing PNGs fall back to built-in icons.
