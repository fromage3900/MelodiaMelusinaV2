# Figma Variable Export — 2026-09-22

**Source:** Melodia Grandmaster Figma `Yx8ud7n39NdWZvnNvo4Xlf`  
**Destination SSOT:** `melodia-design-system/tokens.json`  
**Scope:** design tokens only  
**Status:** exported from live Figma Variables; pending/subject to normal git CI until merged

## Export summary

Figma currently contains **103 variables across 7 collections**.

Design-token collections synchronized into `tokens.json`:

- `primitives` — 36 variables
- `semantic` — 22 variables, exported as `semantic-light` / `semantic-dark`
- `global` — 19 variables
- `portfolio` — 16 variables
- `pillar` — 1 variable with Sakura / Cosmic / Grotto / Orrery modes, exported as four mode sets

Total design variables synchronized: **94**.

Intentionally excluded from the design-token SSOT:

- `bridge-token` — 4 scene/content variables
- `bridge-spec` — 5 scene telemetry/spec variables

Those bridge collections contain values such as level path, scene title, tris, and draw calls. They are Figma variables but are not design tokens and should not become palette/style authority.

## Git diff against previous SSOT

- Existing token leaves before export: **116**
- Token leaves after export: **141**
- Added: **25**
- Existing values changed: **3**
- Removed: **0**

Existing values changed to match the live Figma Variables:

| Token | Previous git | Live Figma |
| --- | --- | --- |
| `primitives.ivory.50` | `#FCFBF8` | `#FFF8EE` |
| `primitives.ivory.100` | `#F7F4EF` | `#F8ECD6` |
| `primitives.ivory.200` | `#EFEAE1` | `#F3E6C8` |

New variable-backed families include:

- `global.z.*`
- `global.layout.max`
- `portfolio.color.*`
- `portfolio.color.iri.*`
- `portfolio.color.motif.*`
- `pillar-{sakura,cosmic,grotto,orrery}.color.motif.accent`

Examples from the live export:

- `portfolio.color.void = #0D1224`
- `portfolio.color.astral-surface = #1A1F3A`
- `portfolio.color.iri.cyan = #66D9FF`
- `portfolio.color.iri.gold = #FFE666`
- `portfolio.color.iri.purple = #CC99FF`
- `portfolio.color.iri.magenta = #FF6EB4`

## Preservation rules

The export updates **Figma-variable-backed values only**.

Existing git-owned typography, font-family, shadow, glow, and other non-variable token blocks are preserved because they cannot be reconstructed truthfully from the current Figma Variables API alone.

The new native Figma Motion tracks and motion-study timings are **not** serialized into `tokens.json`; they remain motion behavior, not design tokens.

## Downstream

`Content/Python/generate_melodia_design_tokens.py` remains the canonical Unreal token generator and can consume the updated token document. New `number` and `string` token families are harmless to the current generator; it continues to emit the token classes it explicitly supports.

The website CSS mirror is **not changed by this export**. Apply/regenerate web CSS separately if a showcase pass intentionally promotes these token changes to the live site.
