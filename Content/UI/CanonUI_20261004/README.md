# Melodia Canon UI — source + runtime staging (2026-10-04)

Source of truth: native Figma Design `gzMjQjGoHLKNZh0jtexGEE` (**Melodia UI — Canon Storybook + Bow HUD**).

This lane is intentionally **asset-level**, not flattened 1440×900 screenshots.

## Runtime rule

Use the representation that matches the behavior:

- **small irregular atom** → SVG source + deterministic transparent PNG @2× for UE
- **simple paper/card/chrome geometry** → native UMG/Slate style; do not bake a bitmap
- **rings / arcs / repeated radial geometry** → parameterized UI material
- **text, key letters, numbers, quest copy, labels** → live UMG text
- **Bow HUD** → already working at runtime; source SVGs here are reference canon only and must not replace or rewire the live Bow HUD

The 1440×900 Figma layout remains the visual design-space baseline.

## Storybook runtime pack

The runtime staging contract lives at:

- `pipeline/figma/storybook_runtime_manifest.json`
- `specs/ui/storybook_runtime_styles.v1.json`
- `Content/Python/stage_storybook_runtime_tokens.py`
- `Tools/validate_storybook_runtime_manifest.py`

### Texture atoms now staged

- four-point sparkle
- compass/objective waypoint
- minimap player pin
- speech-bubble tail
- menu diamond ornament
- Sir Melodious storybook crest marker
- loading/progress note head

Exact PNG bytes are stored as `.png.b64` text payloads under
`pipeline/figma/storybook_runtime/png_b64/` because connector writes cannot
supply Git-LFS backing objects. The staging script hydrates them losslessly under
`Saved/Staging/StorybookRuntime/` and imports them to:

`/Game/Melodia/UI/Storybook/Textures/Atoms`

### Material / native-UMG assets

These remain SVG/spec references rather than large textures:

- Cosmic Orrery outer, dashed-mid and inner rings
- Orrery disc frame
- Orrery category-node body
- paper/menu/quest/archive/VN card bodies
- compass sign, minimap cluster, loading panel, progress pill
- portrait frame, speaker tab, choice cards and controls

This is deliberate. The current Figma versions of those surfaces are flat
rounded geometry, so rasterizing them would add memory and scaling artifacts
without preserving any extra authored information.

## Texture settings

The Storybook staging importer configures the current small atoms as:

- Compression: `TC_EDITOR_ICON`
- LOD group: `TEXTUREGROUP_UI`
- Mip generation: `TMGS_NO_MIPMAPS`
- sRGB: on
- Never Stream: per manifest (currently on for these tiny persistent atoms)
- Preserve Border: on

Large future illustrations/backgrounds should **not** inherit Never Stream by
default.

## Bow HUD

The Bow HUD already has a functioning runtime implementation and its own older
staging/import contract. This branch does **not** author new Bow `.uasset`
content or change HUD ownership.

The Bow SVG files in `BowHUD/` only preserve the visual source behind the
current native-Figma canon.

## Validation

Run offline:

```bash
python Tools/validate_storybook_runtime_manifest.py
```

That gate checks:

- every declared SVG source exists;
- each texture payload is valid base64 PNG;
- each decoded PNG matches the manifest's @2× dimensions.

Then, in Unreal Editor:

```python
import stage_storybook_runtime_tokens as s
s.main()
```

The import step is additive presentation work only. It does not change gameplay,
save, navigation, Bow HUD, Quill, or battle authority.
