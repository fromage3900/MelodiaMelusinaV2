# MELODIA — A Design System for 3D Environment & Technical Artists

> **Working brand name:** *Melodia* (alt candidates in §11). Rename freely — every token and component is namespaced under `melodia/` for easy find-and-replace.
>
> **Design north star:** *Premium fantasy artbook meets professional technical documentation.*
>
> **Inspiration blend:** **HoYoverse** celestial UI craft (Genshin Impact / Honkai: Star Rail — astral starfields, luminous gold filigree, ornate-but-restrained framing, constellation systems) fused with **luxury editorial** layout (fashion-book grids, high-contrast serifs, generous whitespace). Melodia = *melody + celestial*: a system that feels composed, harmonic, and starlit. We take HoYoverse's sense of premium wonder but keep editorial discipline — never gacha clutter.
>
> This document is the single source of truth for the system. It is paired with two machine artifacts:
> - `tokens.json` — design tokens (Tokens Studio / W3C format) → import into Figma Variables.
> - `melodia-figma-plugin/` — a runnable Figma plugin that builds the variables, text styles, pages, and core components automatically.

---

## 0. How to read this document

| Section | What it gives you |
|---|---|
| §1 Brand foundations | The "why" — pillars, voice, motif rules |
| §2 Color system | Variable-based palette, primitives → semantic, light + dark modes |
| §3 Typography | Full hierarchy + font pairing recommendation |
| §4 Spacing & grid | 8pt system, radii, elevation, layout grids |
| §5 Component library | Full inventory, variants, properties, the Asset Passport |
| §6 Layout templates | 10 templates, all Auto Layout |
| §7 Responsive rules | Desktop / Tablet / Mobile behavior |
| §8 Figma file organization | 7 pages + naming standards |
| §9 Automation support | How data gets populated by scripts/MCP |
| §10 Implementation order | Step-by-step build sequence |
| §11 Personal brand | Turning the system into a recognizable identity |

---

## 1. Brand foundations

### 1.1 Pillars
The design language must always communicate, in priority order:

1. **Clarity** — information legibility is never sacrificed for atmosphere.
2. **Technical expertise** — numbers, specs, and process read as authoritative.
3. **Craftsmanship** — every edge, rule line, and margin is intentional.
4. **Elegance** — restraint, generous whitespace, high typographic contrast.
5. **Premium quality** — print-grade finish; feels like a collector artbook.
6. **Magical atmosphere** — celestial accents, never costume fantasy.
7. **Professionalism** — a studio could ship documentation in this system.

**Governing rule:** *Ornamentation enhances information; it never competes with it.* If a decorative element reduces legibility or scannability, remove it.

### 1.2 The feeling, calibrated
| Lean **into** | Stay **away from** |
|---|---|
| Luxury editorial / fashion-book layout | Gacha clutter, banner spam, pop-ups |
| Astral starfields & luminous gold framing (restrained) | Overly decorative fantasy, scrapbook |
| Modern fantasy, understated | Convention-flyer density |
| Art Nouveau line discipline (not floral excess) | Mobile-game ad aesthetics |
| Japanese collector artbook finish | Visual clutter, drop-shadow soup |
| Architecture presentation boards (grids, rules) | Loud elemental neon / RGB |
| Premium game-studio documentation (HoYoverse-grade splash/artbook) | — |

**HoYoverse cues to borrow (sparingly):** ornate gold **corner frames** on hero plates; faint **constellation/star-chart** backplates behind titles; a single **luminous glow** on the brand mark and key numerals; astral **deep-blue/violet** night surfaces for dark mode. **HoYoverse cues to reject:** elemental neon overload, glassmorphism soup, animated sparkles on body content, busy bordered everything.

### 1.3 Visual motifs (use sparingly)
Primary motif set, all rendered as **thin gold or plum linework**, never filled blobs:

- **Eight-point star** (✸) — the **signature Melodia mark** (HoYoverse-leaning astral burst). Brand glyph, mark lockup, passport kicker.
- **Four-point star** (✦) — secondary sparkle: list bullets, divider centers, spec markers.
- **Constellation / star-chart patterns** — faint connected-dot lines as page-corner accents, title backplates, and section-break art. Opacity ≤ 12% (≤ 18% on dark astral surfaces).
- **Ornate gold corner frames** — HoYoverse-style filigree brackets framing hero plates and covers only; thin (1px) line, never a full ornate border on documentation pages.
- **Thin celestial linework** — 1px hairlines, often with a single star node.
- **Delicate filigree** — Art-Nouveau corner flourishes; reserved for cover/hero and artbook spreads only.
- **Gold rule lines** — the workhorse. 1px champagne-gold rules separate content and frame headers.
- **Luminous glow** — a soft outer glow (gold or astral) reserved for the brand mark and one hero numeral/title per view. Subtle: see `glow/*` effects (§4.4).
- **Paper texture** (light) / **starfield wash** (dark) — a subtle (3–6% opacity) grain on ivory; a faint star-speckle gradient on astral night surfaces.

**Density budget per page:** no more than **3 motif instances** on a working documentation page; up to 6 on a hero or artbook cover. When in doubt, delete one.

---

## 2. Color system (variable-based)

Two-tier model: **primitives** (raw palette, never used directly in designs) → **semantic tokens** (what you actually apply). Semantic tokens carry **two modes**: `Light` (**Ivory** — editorial artbook) and `Dark` (**Astral Night** — HoYoverse-leaning starfield). The dark mode is a first-class hero, not an afterthought: deep astral blue-violet surfaces with luminous gold + iris accents, ideal for ArtStation covers and splash art.

### 2.1 Primitive palette

> **Portfolio lookbook Light = gilded ivory (2026-07-15 SSOT).** Live site polish (`melodia-editorial-polish.css`) and Figma Grandmaster Light primitives use warmer parchment for recruiter/lookbook surfaces — not the cooler print paper below this note's historical names. Print/ArtStation breakouts may still read cooler; web lookbook must match these warmer hexes. Dark / `astral/*` values are unchanged.

| Token | Hex | Note |
|---|---|---|
| `ivory/50` | `#FFF8EE` | **Gilded Moonlight** — purest lookbook surface (was `#FCFBF8` cool print) |
| `ivory/100` | `#F8ECD6` | **Gilded Ivory** — default lookbook paper (was `#F7F4EF`) |
| `ivory/200` | `#F3E6C8` | sunken / parchment fill (was `#EFEAE1`) |
| `ivory/300` | `#E3DACE` | hairline on ivory |
| `plum/500` | `#6E6080` | muted plum (disabled, faint) |
| `plum/600` | `#463A54` | plum mid |
| `plum/700` | `#2E2438` | plum deep |
| `plum/800` | `#241B2E` | **Midnight Plum** — primary dark |
| `plum/900` | `#1C1426` | darkest, dark-mode base |
| `gold/100` | `#F0E6D2` | gold tint fill |
| `gold/300` | `#DDC79B` | gold light |
| `gold/500` | `#C9A86A` | **Champagne Gold** — accent / rules |
| `gold/700` | `#A7884E` | gold text (AA on ivory) |
| `lavender/100` | `#E8E4F2` | lavender tint |
| `lavender/300` | `#C2BAE0` | lavender light |
| `lavender/500` | `#9F94C6` | **Lavender** — secondary accent |
| `sakura/100` | `#F5E8EA` | sakura tint |
| `sakura/300` | `#E7C9CE` | **Dusty Sakura** — tertiary accent |
| `sakura/500` | `#D6A9B0` | sakura saturated (rare) |
| `slate/200` | `#D5D8DE` | border default |
| `slate/300` | `#AEB4BF` | border strong |
| `slate/400` | `#828A98` | text tertiary |
| `slate/500` | `#5A6170` | **Slate Grey** — text secondary |
| `slate/700` | `#3C414B` | slate deep |
| `astral/100` | `#E5EAF5` | astral tint (light) |
| `astral/300` | `#8AA9D6` | astral light |
| `astral/500` | `#3C5C9E` | **Astral Blue** — HoYoverse night accent |
| `astral/700` | `#26365E` | deep astral (dark surface tone) |
| `astral/900` | `#141A30` | **Astral Night** — dark-mode base |
| `iris/100` | `#ECE6F4` | iris tint |
| `iris/300` | `#A99AD0` | iris light |
| `iris/500` | `#6E5AA6` | **Iris/Amethyst** — Honkai-leaning violet accent |
| `status/success` | `#5E8B7E` | muted sage |
| `status/warning` | `#B8862F` | aged amber |
| `status/error` | `#A85751` | muted terracotta |
| `status/info` | `#6B7CA8` | muted slate-blue |

> **Pink discipline:** Dusty Sakura is a *tertiary* accent only — used for ≤5% of any composition (a single tag, a hairline, a star fill). Never a background, never primary.

### 2.2 Semantic tokens (the layer you design with)

| Semantic token | Light mode → primitive | Dark mode → primitive |
|---|---|---|
| `color/surface/base` | `ivory/100` | `astral/900` |
| `color/surface/raised` | `ivory/50` | `astral/700` |
| `color/surface/sunken` | `ivory/200` | `plum/900` |
| `color/surface/inverse` | `plum/800` | `ivory/100` |
| `color/text/primary` | `plum/800` | `ivory/50` |
| `color/text/secondary` | `slate/500` | `slate/300` |
| `color/text/tertiary` | `slate/400` | `slate/400` |
| `color/text/inverse` | `ivory/50` | `astral/900` |
| `color/text/accent` | `gold/700` | `gold/300` |
| `color/border/subtle` | `ivory/300` | `astral/700` |
| `color/border/default` | `slate/200` | `astral/500` |
| `color/border/strong` | `slate/300` | `iris/500` |
| `color/accent/primary` | `gold/500` | `gold/500` |
| `color/accent/secondary` | `lavender/500` | `lavender/300` |
| `color/accent/tertiary` | `sakura/300` | `sakura/300` |
| `color/accent/astral` | `astral/500` | `astral/300` |
| `color/accent/iris` | `iris/500` | `iris/300` |
| `color/rule/gold` | `gold/500` | `gold/500` |
| `color/feedback/success` | `status/success` | `status/success` |
| `color/feedback/warning` | `status/warning` | `status/warning` |
| `color/feedback/error` | `status/error` | `status/error` |
| `color/feedback/info` | `status/info` | `status/info` |

### 2.3 Accessibility floor
- Body/`text/primary` on `surface/base`: target **≥ 7:1** (AAA). `plum/800` on `ivory/100` ≈ 11:1. ✓
- `text/secondary` on `surface/base`: **≥ 4.5:1**. `slate/500` on `ivory/100` ≈ 5.1:1. ✓
- Gold is **never** used for body text — only `gold/700` for short accent text (≈ 4.6:1) and `gold/500` for rules/decoration.
- Status colors are paired with an icon/label, never color-only.

---

## 3. Typography system

### 3.1 Font pairing recommendation

Three roles. Recommended stack uses **free, high-quality Google Fonts** so the system is shareable; premium upgrades listed for when budget allows.

| Role | Token SSOT (`tokens.json`) | Status | Why |
|---|---|---|---|
| **Display / Titles** | **Fraunces** | **Live** | Editorial serif for heroes and passports |
| **Body / UI** | **Inter** | **Live** | Lookbook body and cards |
| **Technical / Metadata** | **IBM Plex Mono** | **Live** | Specs, passport rows, dividers |
| **Cover / Hero caps** *(optional)* | **Cinzel** | **Live** | Engraved wordmark / cover titles only |

**Portfolio type SSOT:** Fraunces / Inter / IBM Plex Mono, with Cinzel for the wordmark
(`tokens.json → global.fontFamilies`, `melodia-luxury-type.css`, and the Figma plugin's
`code.js` — all three agree). Pairing logic is a high-contrast serif + a neutral sans + a mono.

> **Superseded 2026-09-11.** This section previously declared **Syne / Instrument Serif /
> Bricolage Grotesque / Azeret Mono** as the SSOT and instructed *"do not restyle portfolio
> lookbook UI to Fraunces/Inter."* That instruction contradicted the system's own token source:
> `tokens.json` and the Figma plugin had already been building Fraunces / Inter / IBM Plex Mono,
> so the doc described a stack nothing else implemented. The site CSS was the last surface
> still carrying the old names and has been corrected to match the tokens. **The token source
> wins over this prose — if they diverge again, fix the prose.**

### 3.2 Type scale

Sizes in px. Tracking in em. All steps are **text styles** in Figma (`melodia/...`).

| Style | Font | Size / Line | Weight | Tracking | Case | Use |
|---|---|---|---|---|---|---|
| `Display/XL` | Fraunces | 72 / 76 | 300 | -0.02 | — | Cover titles, hero |
| `Display/Large` | Fraunces | 56 / 60 | 300 | -0.02 | — | Section openers, artbook |
| `Title/Project` | Fraunces | 40 / 44 | 400 | -0.01 | — | Project name on breakdowns |
| `Header/Section` | Fraunces | 28 / 34 | 500 | 0 | — | In-page section headers |
| `Header/Sub` | Inter | 20 / 28 | 600 | 0 | — | Subheaders, card titles |
| `Body/Large` | Inter | 18 / 30 | 400 | 0 | — | Lead paragraphs, intros |
| `Body/Default` | Inter | 16 / 26 | 400 | 0 | — | Standard body copy |
| `Caption` | Inter | 13 / 18 | 400 | 0.01 | — | Image captions, footnotes |
| `Label/Technical` | IBM Plex Mono | 12 / 16 | 500 | 0.08 | UPPER | Tag labels, spec keys |
| `Metadata` | IBM Plex Mono | 11 / 14 | 400 | 0.06 | UPPER | Passport fields, fine print |

### 3.3 Type rules
- **One serif moment per view.** Don't stack Display XL and Display Large together; the serif is a feature, not a texture.
- **Numbers are mono.** Any spec value (poly count, resolution, version) renders in IBM Plex Mono with `tabular` figures for column alignment.
- **Measure:** body line length 60–75 characters. Enforce via column width, not manual breaks.
- **Tracking:** only mono labels/metadata get positive tracking; serif display gets negative tracking for tightness.

---

## 4. Spacing, grid, radius, elevation

### 4.1 8pt spacing scale
Base unit **8** (with a **4** micro-unit for icon/optical nudges only).

| Token | Value | Primary usage |
|---|---|---|
| `space/4` | 4 | micro: icon-to-label gap, optical nudge (use sparingly) |
| `space/8` | 8 | tight: chip padding, inline gaps |
| `space/16` | 16 | default: control padding, small stacks |
| `space/24` | 24 | card padding, paragraph rhythm |
| `space/32` | 32 | block separation within a section |
| `space/48` | 48 | section padding, card grid gaps |
| `space/64` | 64 | major section separation |
| `space/96` | 96 | page top/bottom margins (desktop) |
| `space/128` | 128 | hero whitespace, artbook spread margins |

**Usage rules**
- **Inside components:** 8 / 16 / 24 only.
- **Between components:** 24 / 32 / 48.
- **Between sections:** 64 / 96.
- **Page-frame margins:** 96 (desktop), 48 (tablet), 24 (mobile).
- Never use a value off the scale. If something "needs" 20px, the real problem is the adjacent element's size.

### 4.2 Layout grids
| Breakpoint | Frame width | Columns | Gutter | Margin |
|---|---|---|---|---|
| Desktop | 1440 | 12 | 24 | 96 |
| Tablet | 834 | 8 | 24 | 48 |
| Mobile | 390 | 4 | 16 | 24 |

Artbook spreads use a **2-page** frame (2880 wide) with a center gutter of 128 and mirrored margins.

### 4.3 Radius
Editorial = **near-sharp**. Soft corners read as "app," not "print."

| Token | Value | Use |
|---|---|---|
| `radius/none` | 0 | dividers, rule frames, image plates |
| `radius/sm` | 2 | tags, chips, default cards |
| `radius/md` | 4 | larger cards, modals |
| `radius/lg` | 8 | rare: featured callouts only |
| `radius/pill` | 999 | status dots only (not buttons) |

### 4.4 Elevation
Premium = **flat with rules**, not shadow stacks. Two shadows max.

| Token | Value | Use |
|---|---|---|
| `shadow/none` | — | default everything |
| `shadow/sm` | `0 1px 2px rgba(36,27,46,0.06)` | hover lift on cards |
| `shadow/md` | `0 8px 24px rgba(36,27,46,0.10)` | overlays/modals only |
| `glow/gold` | `0 0 16px rgba(201,168,106,0.45)` | **HoYoverse glow** — brand mark + one hero numeral/title only |
| `glow/astral` | `0 0 20px rgba(60,92,158,0.50)` | luminous accent on astral-night hero plates only |

Separation is achieved primarily with `border/subtle` + `rule/gold`, not shadow. **Glow is rationed:** at most one glow element per view — it marks the single "hero" moment (the mark, the key stat, the title), never decorates body content. On light/ivory pages glow is barely-there; it shines on dark astral surfaces.

---

## 5. Component library

Naming: `Category/Component`, variants via Figma **Variant properties**. Data slots exposed as **Component Properties** (text/boolean/instance-swap) so automation can set them — see §9.

### 5.1 Section Dividers — `Divider/Section`
Horizontal rule with an optional centered celestial node.

| Property | Values |
|---|---|
| `Style` (variant) | `Star` (✦ centered on gold rule), `Moon` (crescent line node), `Floral` (Art-Nouveau filigree node), `Minimal` (plain gold hairline, no node) |
| `Width` (variant) | `Full`, `Short` (240px centered) |
| `Weight` (variant) | `Hairline` (1px), `Light` (1.5px) |

Construction: an Auto Layout row → `[rule] [node] [rule]`, rule color `color/rule/gold`, node is an instance-swap slot.

### 5.2 Technical Tags — `Tag/Technical`
Spec chip: mono label + value, optional leading icon.

| Property | Values |
|---|---|
| `Type` (variant) | `Poly Count`, `Triangle Count`, `Material Count`, `Texture Count`, `Draw Calls`, `LOD`, `Nanite`, `Platform` |
| `Emphasis` (variant) | `Default` (ivory fill, gold hairline), `Strong` (plum fill, ivory text) |
| `Value` (text prop) | e.g. `42,318` |
| `showIcon` (bool prop) | toggles leading glyph |

Anatomy: `[icon] [LABEL · Label/Technical] [value · Metadata, tabular]`, padding `8/12`, radius `sm`, gap `8`.

### 5.3 Software Tags — `Tag/Software`
Tool attribution chip with brand glyph.

| Property | Values |
|---|---|
| `Tool` (variant) | `Blender`, `ZBrush`, `Substance Painter`, `Substance Designer`, `Material Maker`, `Houdini`, `Unreal Engine`, `Unity` |
| `Style` (variant) | `Chip` (icon + name), `Icon` (icon only), `Pill` (icon + name, pill) |

Icons are an instance-swap slot fed from an `Icon/Software/*` set (monochrome line icons tinted `text/secondary`, brand color optional).

### 5.4 Info Cards — `Card/Info`
Bordered content block; the layout atom for breakdowns.

| Property | Values |
|---|---|
| `Type` (variant) | `Project Information`, `Asset Statistics`, `Material Statistics`, `Shader Statistics` |
| `Header` (variant) | `WithRule` (title + gold rule), `Plain` |
| `Title` (text prop) | card title |

Structure: vertical Auto Layout, padding `24`, gap `16`, `border/subtle`, radius `sm`, optional top `Divider/Section[Minimal]`. Body is a slot containing a **Spec Row** repeater (`key · Label/Technical` left, `value · Metadata` right, space-between).

### 5.5 Spec Row — `Row/Spec`
Atomic key/value line used inside cards and the passport.
- Auto Layout row, `space-between`, gap `16`, vertical padding `8`.
- `key` → `Label/Technical`, `text/secondary`.
- `value` → `Metadata`, `text/primary`, tabular figures.
- Optional `divider` boolean adds a `border/subtle` bottom hairline.

### 5.6 ⭐ Asset Passport — `Brand/AssetPassport` (signature component)
The recognizable branding element placed on **every** project. Think of it as the "spec plate" of a museum piece.

**Fields (all text/instance Component Properties for automation):**
`Project Name`, `Category`, `Triangles`, `Texture Resolution`, `Materials`, `Software`, `Engine`, `Date`, `Version`.

**Layout (default `Card` variant):**
```
┌─────────────────────────────────────────────┐
│ ✸  ASSET PASSPORT            v{Version}      │  ← gold ✸ astral-star glyph + mono kicker, version right
│ ───────────────────────────────────────────  │  ← gold rule (rule/gold, hairline)
│ {Project Name}                  · Title/Project│
│ {Category}                      · Label/Tech   │
│ ───────────────────────────────────────────  │  ← divider/subtle
│ TRIANGLES        {Triangles}                  │  ← Row/Spec ×N
│ TEXTURES         {Texture Resolution}         │
│ MATERIALS        {Materials}                  │
│ SOFTWARE         [Tag/Software ...]           │  ← instance-swap row
│ ENGINE           {Engine}                     │
│ DATE             {Date}                        │
│ ───────────────────────────────────────────  │
│ ✸                                  MELODIA    │  ← brand mark footer (8-pt astral star + wordmark)
└─────────────────────────────────────────────┘
```

| Property | Values |
|---|---|
| `Format` (variant) | `Card` (portrait, ~360w), `Banner` (landscape, full-width strip), `Compact` (titles + 3 key specs) |
| `Theme` (variant) | `Light`, `Dark` (maps to color modes) |
| field props | the 9 fields above (text), `Software` is an instance-swap list |

**Why it brands:** consistent gold ✸ kicker + rule + mono spec grid + footer mark, with an optional `glow/gold` on the star for the HoYoverse touch. Repeated across ArtStation, web, and breakdowns, it becomes instantly recognizable as *your* work. On the `Dark` (Astral Night) theme it reads like a Honkai/Genshin spec plate; on `Light` it reads like an editorial colophon.

### 5.7 Supporting components
| Component | Variants / Notes |
|---|---|
| `Brand/Mark` | `Star` (✸ 8-pt astral burst — primary glyph), `Wordmark` (MELODIA in Cinzel), `Lockup` (✸ + MELODIA) — the logo system; optional `glow/gold` |
| `Star` | `4pt` (✦), `8pt` (✸ signature), `Constellation`, `StarChart` (corner-frame) — reusable motif primitives (line + fill) |
| `Frame/Corner` | `Filigree`, `Astral` — HoYoverse-style ornate gold corner brackets for hero/cover plates only |
| `Image/Plate` | `Default`, `WithCaption`, `Beauty` (full-bleed) — image frame with gold hairline + caption slot |
| `Callout` | `Note`, `Tip`, `Warning` — feedback colors, icon + text |
| `Button` | `Primary` (plum fill), `Secondary` (gold hairline), `Ghost`; `Size` = `sm/md`; near-sharp `radius/sm` |
| `Breadcrumb/Pager` | artbook page numbers + section path |
| `Legend/Swatch` | material/color legend rows for material presentations |
| `Process/Step` | numbered step with ✦ marker, used in process breakdowns |
| `Footer/Signature` | brand mark + handle + contact, placed on every template |

### 5.8 Component hierarchy
```
Primitives:    Star, Brand/Mark, Icon/Software/*, Row/Spec, Divider/Section
Elements:      Tag/Technical, Tag/Software, Button, Callout, Legend/Swatch, Image/Plate
Composites:    Card/Info, Process/Step, Breadcrumb/Pager, Footer/Signature
Signature:     Brand/AssetPassport
Patterns:      Stat Cluster, Spec Sheet, Beauty + Passport pairing  (see §6)
```

---

## 6. Layout templates (all Auto Layout)

Each template is a Figma frame on **06 Templates**, built from components, using the §4.2 grids, and ships in Desktop/Tablet/Mobile sizes. Each carries a `Footer/Signature` and at least one `Brand/AssetPassport`.

| # | Template | Structure (top → bottom) | Key components |
|---|---|---|---|
| 1 | **Hero Page** | Full-bleed beauty `Image/Plate[Beauty]` → `Display/XL` title overlay → `Asset Passport[Banner]` → scroll cue | Mark, Passport, Plate |
| 2 | **Asset Breakdown** | Title block → beauty shot → 12-col grid of `Card/Info[Asset Statistics]` + wireframe/UV plates → `Tag/Technical` cluster | Cards, Tags, Plates |
| 3 | **Environment Breakdown** | Wide beauty → "Composition" annotated plate → modular-kit grid → lighting passes row → `Card/Info` stats | Plates, Cards, Dividers |
| 4 | **Material Presentation** | Material hero sphere/plane → channel grid (Albedo/Normal/Roughness/etc. `Image/Plate` + `Legend/Swatch`) → `Card/Info[Material Statistics]` | Plates, Legend, Cards |
| 5 | **Shader Breakdown** | Result beauty → node-graph plate → parameter table (`Row/Spec`) → `Card/Info[Shader Statistics]` → math/notes `Callout` | Cards, Rows, Callout |
| 6 | **Trim Sheet Presentation** | Trim sheet flat → usage examples grid → density/texel `Tag/Technical` → application beauty | Plates, Tags |
| 7 | **Technical Documentation** | Doc header + `Breadcrumb/Pager` → TOC → body sections w/ `Header/Section` + `Divider` → code/spec `Callout` | Dividers, Callout, Pager |
| 8 | **Process Breakdown** | Title → numbered `Process/Step` timeline (✦ markers) → stage plates → final beauty + Passport | Process/Step, Plates |
| 9 | **Commission Sheet** | Brand lockup header → service tiers as `Card/Info` → pricing `Row/Spec` → ToS fine print → contact `Footer/Signature` | Cards, Rows, Mark |
| 10 | **Artbook Spread** | 2-page frame → full-bleed art left, editorial text + `Display/Large` right → constellation corner accents → page numbers | Plate, Star, Pager |

**Recurring patterns (page 04):**
- **Stat Cluster** — responsive wrap of `Tag/Technical`.
- **Spec Sheet** — `Card/Info` + repeated `Row/Spec`.
- **Beauty + Passport** — full-bleed image with Passport overlaid bottom-left (the hero signature).
- **Channel Grid** — uniform `Image/Plate` grid with mono captions (materials/shaders).

---

## 7. Responsive rules

Single source design at Desktop, then adapt. Components are built so they **reflow**, not rescale.

| Concern | Desktop (1440) | Tablet (834) | Mobile (390) |
|---|---|---|---|
| Grid | 12 col / 96 margin | 8 col / 48 margin | 4 col / 24 margin |
| Section spacing | 96 | 64 | 48 |
| Card grids | 3–4 up | 2 up | 1 up (stack) |
| `Display/XL` | 72 | 56 | 40 |
| `Title/Project` | 40 | 32 | 28 |
| Asset Passport | `Banner` or `Card` | `Card` | `Compact` |
| Tag clusters | single row | wrap | wrap, full-width chips |
| Image plates | side-by-side | 2-up | full-width stacked |
| Artbook spread | 2-page | single page, stacked | single page, stacked |

**Mechanics**
- Use Auto Layout `Wrap` for tag/card clusters so they reflow automatically.
- Use **min/max width** constraints on cards (`min 280`, `max 1fr`).
- Type steps are **variant-swapped** by breakpoint (don't free-scale text).
- Passport switches `Format` variant by breakpoint rather than shrinking.
- Test each template at all three widths before publishing.

---

## 8. Figma file organization

### 8.1 Pages
```
01 Foundations   → brand intro, motifs, color/type/spacing specimens, logo system, do/don't
02 Tokens        → variable collections rendered as swatches/specimens (source of truth display)
03 Components    → the component library, organized by §5.8 hierarchy, with usage notes
04 Patterns      → recurring composites (Stat Cluster, Spec Sheet, Beauty+Passport, Channel Grid)
05 Layouts       → grid systems, responsive frames, spacing/elevation references
06 Templates     → the 10 production templates × {Desktop, Tablet, Mobile}
07 Archive       → deprecated components/versions; never delete, move here
```
> Optional `00 Cover` page with the brand lockup for the file thumbnail.

### 8.2 Naming conventions

**Layers**
- Frames: `PascalCase` descriptive (`HeroPage/Desktop`).
- No default names (`Frame 12`, `Group 3`) — ever.
- Prefix utility layers with `_` (`_grid`, `_bg`, `_spacer`).

**Components** — `Category/Component`
- e.g. `Tag/Technical`, `Card/Info`, `Brand/AssetPassport`, `Divider/Section`.
- Categories: `Brand`, `Tag`, `Card`, `Divider`, `Row`, `Image`, `Button`, `Icon`, `Process`, `Footer`, `Legend`, `Breadcrumb`, `Star`.
- Component sets (multi-variant) use the bare `Category/Component` name; variants live inside.

**Variant properties** — `Property=Value`, properties `PascalCase`, values `PascalCase` or human strings
- e.g. `Type=Triangle Count`, `Emphasis=Strong`, `Format=Banner`, `Theme=Dark`.
- Booleans named with a verb/state: `showIcon`, `hasDivider`.
- Order variant properties consistently: `Type` → `Style/Emphasis/Format` → `Theme` → `Size` → booleans.

**Component (data) properties**
- Text props use the **automation field name** verbatim (see §9): `projectName`, `triangleCount`, `textureResolution`, `materialCount`, `engine`, `version`, `date`, `category`.
- Instance-swap props: `softwareTag`, `dividerNode`, `softwareIcon`.

**Variables / tokens** — `group/subgroup/name`
- Color: `color/surface/base`, `color/text/primary`, `color/accent/primary`.
- Spacing: `space/8` … `space/128`.
- Radius: `radius/sm`. Collections: `Color` (modes: Light, Dark), `Spacing`, `Radius`.

**Text styles** — `Group/Name`: `Display/XL`, `Header/Section`, `Label/Technical`, `Metadata`.

**Styles/effects** — `shadow/sm`, `shadow/md`.

---

## 9. Automation support (data-driven by design)

Goal: a Blender export / Python / MCP pipeline populates portfolio artifacts **without manual typing**. The system is built so every dynamic value is a named, settable slot.

### 9.1 Canonical data schema
The single contract between tooling and design. Component text-property names **match these keys exactly**.

```json
{
  "projectName": "Ashen Cathedral",
  "category": "Environment",
  "triangleCount": 482318,
  "polyCount": 248110,
  "materialCount": 12,
  "textureCount": 36,
  "textureResolution": "4K",
  "drawCalls": 184,
  "lod": "LOD0–LOD3",
  "nanite": true,
  "platform": "PC / Console",
  "software": ["Blender", "ZBrush", "Substance Painter", "Houdini"],
  "engine": "Unreal Engine 5.4",
  "date": "2026-03",
  "version": "1.2"
}
```

### 9.2 How automation populates a design
- **Tokens Studio + JSON:** import `tokens.json` → variables; tooling can regenerate token files for theme variants.
- **Figma Plugin API (recommended path):** a plugin reads the JSON above, finds instances of `Brand/AssetPassport` / `Card/Info` / `Tag/Technical`, and sets their component properties by name:
  ```js
  passport.setProperties({
    projectName: data.projectName,
    triangleCount: formatNum(data.triangleCount),
    textureResolution: data.textureResolution,
    materialCount: String(data.materialCount),
    engine: data.engine,
    version: data.version,
    date: data.date,
    category: data.category
  });
  ```
- **MCP automation:** an MCP server exposes `populate_passport(fileKey, nodeId, data)` that wraps the plugin/REST calls; the same `data` schema flows end to end (Blender → JSON → MCP → Figma).
- **Blender export:** a small Python operator writes the §9.1 JSON from scene stats (`len(mesh.polygons)`, material slots, texture sizes) into `project.melodia.json` next to the render.

### 9.3 Design rules that make automation reliable
1. **Every dynamic value is a Component Property** named per the schema — never raw text baked into a layer.
2. **Stable names, stable structure.** Don't rename props or reorder the passport's spec rows casually; tooling matches by name.
3. **Formatting lives in components** (tabular figures, uppercase via style) so tooling can pass raw values.
4. **Lists via instance-swap** (`software`) so adding a tool = swapping/duplicating an `Icon/Software/*`.
5. **One schema, many surfaces:** the same JSON fills the Passport, Info Cards, and Tag clusters — author the mapping once.

---

## 10. Implementation order (step-by-step)

Build foundations → tokens → components → patterns → layouts. Do not jump ahead; later steps consume earlier ones.

1. **File + pages.** Create the 7 pages (§8.1). Add `00 Cover`. *(Plugin does this.)*
2. **Variables.** Create `Color` (Light+Dark modes), `Spacing`, `Radius` collections from §2/§4. *(Plugin + `tokens.json`.)*
3. **Text styles.** Create §3.2 styles. Load **Fraunces / Inter / IBM Plex Mono** first — that is the token SSOT, and Cinzel for the wordmark. *(Plugin.)*
4. **Effects.** Create `shadow/sm`, `shadow/md`.
5. **Motif primitives.** `Star/8pt` (signature), `Star/4pt`, `Constellation`, `Frame/Corner`, `Brand/Mark` lockups (Cinzel wordmark + ✸). Draw once, componentize.
6. **Atoms.** `Row/Spec`, `Divider/Section`, `Icon/Software/*`.
7. **Elements.** `Tag/Technical`, `Tag/Software`, `Button`, `Callout`, `Image/Plate`, `Legend/Swatch`.
8. **Composites.** `Card/Info`, `Process/Step`, `Breadcrumb/Pager`, `Footer/Signature`.
9. **Signature.** `Brand/AssetPassport` (all formats + themes) — wire component properties to §9.1 names.
10. **Patterns (page 04).** Assemble Stat Cluster, Spec Sheet, Beauty+Passport, Channel Grid.
11. **Layouts (page 05).** Grids + spacing/elevation reference frames.
12. **Templates (page 06).** Build all 10 at Desktop, then derive Tablet + Mobile via variant swaps + reflow.
13. **Documentation (page 01).** Specimens, do/don'ts, usage notes.
14. **Publish** as a Figma Library; enable for ArtStation/web exports.
15. **Automation hookup.** Wire the populate plugin/MCP to §9.1 schema; dry-run on one real project.

> Fast start: run `melodia-figma-plugin` to auto-execute steps 1–9 **plus** a starter set of step-12 hero templates, then continue manually for the remaining layouts/templates.

### 10.1 Hero treatments (style variations, same theme)
Four interchangeable hero/cover styles ship as templates on `06 Templates` — same palette + type, different mood and sparkle level. Use one per piece; don't stack them.

| Treatment | Surface | Sparkle level | Best for |
|---|---|---|---|
| **Constellation** | Astral Night | low–medium (`Star/Constellation` backplate + faint scatter) | default hero, ArtStation cover |
| **Nebula (iris-forward)** | Astral Night + iris/astral bloom | medium (glowing gold sparkles) | dramatic hero pieces, key art |
| **Ornate Frame** | Astral Night | low (`Frame/Corner` brackets) | covers, end-cards, artbook plates |
| **Ivory Editorial + sparkle** | Ivory | very low (a few gold `Star/4pt`) | breakdowns, print, readability-first |

**Sparkle budget:** dark surfaces may carry a faint white starfield + ≤ 1 glowing gold star per view; ivory surfaces get only a handful of low-opacity gold `Star/4pt`. Glow stays rationed to the brand mark + one hero element (§4.4).

---

## 11. Building the personal brand

The system *is* the brand. **Name: Melodia** (*melody + celestial* — composed, harmonic, starlit). To make it unmistakably yours:

- **Name + mark.** **MELODIA**, wordmark set in **Cinzel** (engraved celestial caps), paired with the **eight-point astral star ✸** as the standalone glyph (favicon, watermark, end-card). The ✸ with a faint `glow/gold` is the HoYoverse-leaning signature; the ✦ four-point star is the secondary sparkle.
- **The Asset Passport is your signature.** Put it on every ArtStation post, every breakdown, every spread. Consistency is the brand — viewers should recognize the spec plate before they read your name.
- **A signature gesture:** the **gold ✸ + hairline rule** kicker above every section title. Cheap to apply, instantly recognizable.
- **Two-world identity.** *Light = Ivory editorial colophon* (galleries, print, web) and *Dark = Astral Night* (HoYoverse-grade ArtStation covers / splash). Same system, two moods — lead with Astral Night for hero pieces.
- **Own a color memory.** Champagne gold + midnight plum on ivory, and luminous gold + iris on astral blue, are the palettes people will remember; resist trendier hues.
- **Tri-voice type as identity.** Portfolio type SSOT = Fraunces + Inter + IBM Plex Mono (Cinzel for the wordmark). The site CSS, `tokens.json`, and the Figma plugin all agree on this set; the earlier Syne / Instrument Serif / Bricolage / Azeret stack is retired.
- **Consistent surfaces:** ArtStation cover, website hero, PDF breakdowns, and social posts all use the same templates + Passport → cross-platform cohesion.
- **Social system:** a square (1080) and portrait (1080×1350) template variant carrying the Passport + one beauty shot; a story (1080×1920) variant with the Astral Night wordmark end-card.
- **Watermark, lightly.** A 6%-opacity ✸ or constellation in a consistent corner of beauty shots.
- **Motion later:** a 1s ✸ "draw-on" + rule wipe + gentle gold glow bloom as an intro sting for reels/turntables — the HoYoverse splash feel, reusing the same gold.
- **Govern it.** Keep `07 Archive` honest, version the library, and write 5 do/don'ts on `01 Foundations` so the brand stays disciplined as it grows.

---

### Appendix A — Component inventory (quick list)
Brand/Mark, Brand/AssetPassport, Star (4pt/8pt/Constellation/StarChart), Frame/Corner, Divider/Section, Row/Spec, Tag/Technical, Tag/Software, Icon/Software/*, Card/Info, Callout, Button, Image/Plate, Legend/Swatch, Process/Step, Breadcrumb/Pager, Footer/Signature.

### Appendix B — Layout inventory (quick list)
Hero Page, Asset Breakdown, Environment Breakdown, Material Presentation, Shader Breakdown, Trim Sheet Presentation, Technical Documentation, Process Breakdown, Commission Sheet, Artbook Spread — each in Desktop/Tablet/Mobile.

### Appendix C — Token collections (quick list)
`Color` (modes: Light, Dark), `Spacing`, `Radius`; text styles under Display/Title/Header/Body/Caption/Label/Metadata; effects `shadow/sm`, `shadow/md`.
