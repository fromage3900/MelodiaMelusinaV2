# Melodia — 3D Environment & Technical Artist Design System

A complete, reusable Figma design system for a premium 3D/technical-art portfolio.
North star: **premium fantasy artbook meets professional technical documentation.**
Inspiration: **HoYoverse** celestial UI (Genshin / Honkai: Star Rail) × **luxury editorial** — ivory editorial *Light* theme + HoYoverse-grade *Astral Night* dark theme, 8-point astral star mark, luminous gold glow, restrained gold filigree.

## Contents
| File | What it is |
|---|---|
| [`DESIGN-SYSTEM.md`](./DESIGN-SYSTEM.md) | **The spec.** Brand foundations, color/type/spacing systems, full component + layout inventory, Figma page structure & naming standards, responsive rules, automation hooks, step-by-step implementation order, and a personal-branding playbook. |
| [`tokens.json`](./tokens.json) | Design tokens (Tokens Studio / W3C). Color w/ **Light + Dark** modes, typography, spacing, radius. Import → Figma Variables. |
| [`melodia-figma-plugin/`](./melodia-figma-plugin) | A **runnable Figma plugin** that auto-builds the variables, text/effect styles, 7-page structure, core components (incl. the signature **Asset Passport** variant set, `Star/Constellation`, `Frame/Corner`), and **responsive hero templates** (Constellation / Nebula / Ornate / Ivory × Desktop/Tablet/Mobile). See its [README](./melodia-figma-plugin/README.md). |
| [`WIX-GUIDE.md`](./WIX-GUIDE.md) + [`wix/`](./wix) | **Wix kit for fromageart.xyz:** color + font cheat sheet, plus paste-ready HTML embeds — `melodia-passport-embed.html` (Asset Passport) and `melodia-hero-embed.html` (hero banner). Both data-driven via the same field schema. |
| [`psd/`](./psd) | **Layered Photoshop files** — 4 hero treatments + Asset Passport (dark/light). Each section is a separate layer. Built reproducibly via `psd.html` + `render_psd.py` + `assemble_psd.js`. |
| [`social-cards/`](./social-cards) | **Reusable social post cards** for ZBrush sculpts, sketches, shader/texture breakdowns, geometry nodes, and process carousels. Includes editable HTML reference, layered SVG/Figma sources, PNG exporters, default PNG exports, and iridescent-material guidance. |

## Fastest path to a working file
1. Run the plugin (`melodia-figma-plugin/README.md`) → instant variables + styles + pages + core components.
2. Or import `tokens.json` via the free Tokens Studio plugin for tokens-only.
3. Follow `DESIGN-SYSTEM.md §10` to build patterns → layouts → the 10 templates.

## Recommended fonts (free)
Fraunces (display) · Inter (body/UI) · IBM Plex Mono (technical/metadata) · Cinzel (wordmark / cover caps).
