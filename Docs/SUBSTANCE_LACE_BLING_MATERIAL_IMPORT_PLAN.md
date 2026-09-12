# Substance Lace and Bling Material Import Plan

**Date:** 2026-07-13  
**Scope:** Purchased/source materials into `M_Master_Toon_Universal` instances  
**Status:** Prepared; editor import is intentionally not run until the Substance UE plugin is installed and the source set is confirmed.

## Current Audit

- `M_Master_Toon_Universal` exists at `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`.
- `MPC_Portfolio_Audio` and `MF_AudioReactiveBlend` exist, and the current audit reports all 12 canonical runtime channels present.
- No Substance plugin is currently present under `BS_GodFile/Plugins` or enabled in `BS_GodFile.uproject`.
- The likely authoritative purchased bling source is `F:\bling surface pbr material vol3.rar` (39.6 MB, dated 2026-01-31). The project also contains a large `bling_surface_vol3_*` Unreal texture family in autosaves; treat those as recovery/reference until the archive contents are inspected.
- The separate Melodia source drive contains a real Substance archive at:
  `G:\MelodiaMelusina\MELUSINATILEABLE TEXTURES\bricks\floralbrickgreayscale\floralbrickgreayscale.sbsar`
  and baked crystal, floral-brick, grass, landscape, soil, and starry-weave maps. No clearly named lace `.sbsar` was found in the scanned source roots. The bling archive is RAR rather than `.sbsar`, so it may contain baked maps or a Substance project and must be unpacked outside `Content/` before import.

## Import Sequence

1. Extract `F:\bling surface pbr material vol3.rar` to a staging directory outside `Content/`, then inventory its extensions and map sets. Keep the archive immutable.
2. Install the UE 5.8-compatible Substance 3D plugin from the licensed source. Confirm the plugin version supports the project engine before enabling it. Do not enable an unverified plugin in a packaging build.
3. Preserve the purchased source files outside `Content/`; record source path, product name, license receipt/reference, plugin version, and import date in an audit manifest.
4. Import `.sbsar` sources through the Substance plugin into:
   - `/Game/EnvSandbox/Materials/Substance/Source/Lace`
   - `/Game/EnvSandbox/Materials/Substance/Source/Bling`
5. Use plugin-generated outputs only as source textures. Create project-owned, named texture assets under:
   - `/Game/EnvSandbox/Materials/Textures/Lace`
   - `/Game/EnvSandbox/Materials/Textures/Bling`
6. If a source has no `.sbsar`, import the complete baked set and document it as `BAKED` rather than pretending it is procedurally editable.
7. Create material instances only from `M_Master_Toon_Universal`; never duplicate the master for a material variant.

## Texture Mapping

| Source output | Universal master input | Import rule |
|---|---|---|
| Base Color / Albedo | Layer A or Layer B albedo | sRGB on |
| Normal | Layer A or Layer B normal | Normal map compression |
| Roughness | ORM or roughness input | linear, no sRGB |
| Metallic | ORM or metallic input | linear, no sRGB |
| Ambient Occlusion | ORM or AO input | linear, no sRGB |
| Height | Parallax / height input | linear, no sRGB; mobile optional |
| Opacity / Lace Mask | opacity or masked blend input | only for lace instances; validate blend mode |
| Specular / sparkle mask | Nikki sparkle or controlled emissive mask | keep artist-weighted and capped |

## First Instances

- `MI_Substance_Lace_Universal`: opaque/masked lace test, neutral toon response, low parallax.
- `MI_Substance_Bling_Universal`: metallic/sparkle test, restrained emissive and iridescence.
- `MI_Substance_Bling_AudioReactive`: duplicate of the bling instance with only audio-reactive controls changed.

Recommended exposed controls, only if the master already lacks an equivalent:

- `LaceMaskStrength`
- `LaceOpacityCutoff`
- `BlingMaskStrength`
- `BlingIntensity`
- `BlingNormalStrength`
- `BlingRoughnessBias`
- `BlingAudioResponse`

Defaults must be neutral/off so existing instances remain visually unchanged. Route `BeatPulse`, `CommandEnergy`, and `VictoryPulse` through the existing audio-reactive emissive path, never through base color or gameplay authority.

## Validation Gates

### Asset gate

- Every imported texture has a project path, source record, correct color space, and platform compression setting.
- Lace has a deliberate blend mode and tested opacity cutoff.
- Bling has bounded emissive/specular response and no material washout.
- No machine-specific absolute paths are referenced by project assets.

### Master gate

- `M_Master_Toon_Universal` still compiles.
- Existing showcase instances render unchanged.
- New instances inherit the master and expose only approved overrides.
- Audio channels remain optional and fall back to zero response.

### Platform gate

- PC: height/parallax and richer sparkle may be enabled after baseline validation.
- Mobile: use baked normal/roughness, disable mandatory height, spectrum, and expensive sparkle paths.
- Test with the actual Melusina outfit and a neutral greybox mesh before applying to hero assets.

### Runtime gate

- Apply the new instances to a small material test fixture first.
- Verify Basic, Skill, Break, and Victory pulses affect only intended accents.
- Confirm no post-battle glow persists after encounter reset.
- Run the project material audit and a ZenForestTest PIE smoke after the plugin import is complete.

## Known Blockers

- Substance UE plugin installation/compatibility is outstanding.
- A named purchased lace/bling source archive was not found in the scanned roots; confirm whether the current `bling_surface_vol3_*` maps are the purchased export or a prior Unreal import before re-importing.
- Headless PCG verification confirms structural actors but not generated ISM counts; visual PCG confirmation still requires an interactive editor viewport.

## Do Not Do Yet

- Do not rebuild or broadly rewire the universal master before the source maps are identified.
- Do not migrate autosave `.uasset` files as a substitute for the original licensed source.
- Do not add a runtime Substance dependency to the packaged game; imported outputs must stand alone.
- Do not modify PCG or gameplay systems as part of this material import.
