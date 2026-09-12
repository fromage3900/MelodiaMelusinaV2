# Material Layering, Parallax, and Nikki MF Review

## Purpose

This review defines the professional cleanup lane for the universal material system before portfolio capture. It does not redesign the god-master architecture. It identifies where layering, parallax, and Nikki-style material functions need discipline so portfolio renders read as intentional art direction rather than feature stacking.

## Executive Assessment

The material platform is strong enough to support portfolio work, but the risk is over-complex presentation. The universal master, landscape height blend, grand water, trimsheets, and themed instances already provide broad range. The next pass should focus on predictability, proof, and restraint:

- Make layer order obvious and documented.
- Keep parallax meaningful only on surfaces where depth helps.
- Use Nikki/Magical/FairyDust features as art-direction controls, not default decoration.
- Produce visual proof from `L_Template` and material passports before claiming portfolio-ready status.

## Main Problems

| Area | Problem | Portfolio Risk | Action |
| --- | --- | --- | --- |
| Layering | Some materials combine base texture, macro tint, motif, wetness, rim, glow, and stylization in one stack. | The surface can look noisy or unfocused in close-up. | Define a preferred order: base surface, normal/height, macro tint, wear/wetness, stylization, emissive accents. |
| Parallax | Parallax/POM appears across showcase and trimsheet lanes, but not every material benefits from depth. | Overuse can shimmer, flatten silhouettes, or distract from sculpted assets. | Restrict hero parallax to stone, trims, cliffs, carved ornament, and deliberate magical depth. |
| Nikki MF | Nikki lanes add rim, sparkle, pastel lift, dream hue, glow, and iridescence. | Too much can make every material read as the same magical finish. | Use presets: subtle, hero, magical, cinematic. Default to subtle for environment assets. |
| Output Proof | Current manifest is metadata-ready, but previews are not individually certified. | Website/Figma pages may list materials without visual evidence. | Capture material grid and per-family hero swatches before promotion. |
| Family Coverage | Current manifest covers Showcase, Zen, and Baroque but not all Landscape, Water, Trimsheet, and Sakura instances. | Portfolio package under-represents the actual material system. | Expand the manifest producer to include landscape, water, trimsheet, and allowed Sakura material families. |

## Recommended Layer Order

1. Base texture or procedural color.
2. Normal, roughness, metallic, and height/parallax.
3. Macro variation, triplanar/world alignment, and biome tint.
4. Wear, moss, wetness, shoreline, or dirt accumulation.
5. Style grade: pastel lift, dream saturation, ink wash, flower shadow, celestial ramp.
6. Emissive accents: sparkle, glyphs, rim, glow, fairy dust.
7. Distance fade and cinematic contact effects.

## Parallax Rules

| Use Parallax | Avoid Parallax |
| --- | --- |
| Cliffs, stone steps, temple blocks, carved trims, baroque ornament, roof tiles, damaged plaster. | Grass cards, petals, soft fabric, shoji paper, simple painted surfaces, broad landscape layers seen at distance. |
| Close-up material passports and hero asset breakdowns. | Dense shots where camera motion causes shimmer. |
| Trimsheet demonstrations where stepped depth proves workflow sophistication. | Anything that hides actual mesh silhouette quality. |

## Nikki MF Rules

| Preset | Intent | Typical Values |
| --- | --- | --- |
| Subtle | Environment default. Keeps palette soft without taking over. | Low rim, low sparkle, low glow, restrained pastel lift. |
| Hero | Hero assets, close-ups, stylized focal props. | Medium rim, controlled sparkle, higher dream contrast. |
| Magical | Transformation, fairy, celestial, or fantasy proof shots. | Stronger glow/iridescence, motif-driven accents. |
| Cinematic | Reel shots and contact-rim hero plates. | Contact rim, distance fade, carefully exposed emissive. |

## Execution Plan

1. Generate the full material manifest and readiness report.
2. Add missing Landscape, Water, Trimsheet, and Sakura material families to the manifest lane.
3. Build `L_Template` material capture grids by family.
4. Promote only materials with preview proof to `portfolio_ready`.
5. For each hero material, write one material passport: intent, parent, key parameters, maps, capture, and where it belongs in a portfolio environment.

## Acceptance Gates

| Gate | Requirement |
| --- | --- |
| Technical | No missing texture references in the promoted material set. |
| Visual | Close-up capture clearly shows base read, roughness, normal/height, and style intent. |
| Restraint | Nikki/Magical features support the material instead of dominating it. |
| Parallax | Parallax surfaces show believable depth without shimmer in motion. |
| Portfolio | Each promoted material has a preview image and metadata entry in `portfolio_package.json`. |

## Producer Notes

Japanese and Sakura-themed material instances are allowed as reusable look-dev assets. The protected boundary is the Sakura level composition and art pass, not the existence of Sakura-compatible materials.
