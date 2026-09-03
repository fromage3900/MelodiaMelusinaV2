# TouchDesigner Page — Design Spec (distilled from my-site-clean)

Date: 2026-07-18 · Prepared by: Site_Design_Analyst (read-only analysis)
Source of truth: `C:/EnvironmentPortfolio/BS_GodFile/my-site-clean/` — **do not modify**; this doc is the contract for whoever authors the new page.

Proposed new page: `wix/touchdesigner-architecture.html`
Working title: **"Surreal Architecture Lookbook — TouchDesigner"** (editorial, magical-girl-ready lookbook for the 13 Escher-inspired worldgen pieces).

---

## 1. Exact token values

### 1.1 Color tokens — `wix/melodia-tokens.css` (core; pulled in via `melodia-editorial.css`)

```css
--void: #0d1224;
--celestial-deep: #0d1224;
--astral: #1a1f3a;
--plum: #2a3055;
--iri-cyan: #66d9ff;
--iri-gold: #ffe666;
--iri-purple: #cc99ff;
--iri-magenta: #ff6eb4;
--iri-pearl: #f0dcf0;
--ink: rgba(236, 234, 244, 0.92);
--muted: rgba(236, 234, 244, 0.66);
--line: rgba(201, 168, 106, 0.34);
--max: 1180px;
```

### 1.2 Night-theme overrides — `wix/melodia-night-theme.css` (auto-imported by editorial.css)

```css
--night-void: #070912;
--night-ink: #0b0f1f;
--night-astral: #101736;
--night-plum: #1c1633;
--night-lavender: rgba(236, 234, 244, 0.92);
--night-muted: rgba(236, 234, 244, 0.66);
--night-line: rgba(201, 168, 106, 0.28);
--night-soft-line: rgba(233, 229, 242, 0.10);
```

### 1.3 Premium/fashion accents — `wix/melodia-premium-system.css` + `wix/melodia-fashion-editorial.css`

```css
--gold: #C9A86A;
--gold-soft: #E8C9B8;
--iris: #9B8FC4;
--sakura: #E8C9B8;
--lavender: #E8E4F2;
--pearl: #F0DCF0;
--luxury-platinum: #D4C5A9;
--iridescent-cyan: #7BB8B8;
--editorial-cream: #FEFAF2;
--text-primary: #ECEAF4;
--text-secondary: #A9A7C0;
--text-accent: #E8C9B8;
--text-muted: #6E6080;
--gold-iridescent: linear-gradient(135deg, #C9A86A 0%, #E8C9B8 25%, #D4C5A9 50%, #C9A86A 75%, #E8C9B8 100%);
--fashion-ink: #1a1520;
--fashion-cream: #f3ece1;
--fashion-champagne: #d4b87a;
--fashion-rose: #c9a0a8;
--fashion-foil: linear-gradient(118deg, #e8d5a8 0%, #c8a45e 38%, #f0e6c8 62%, #a8864a 100%);
```

Backdrop gradient used on `.melodia-shell.fashion-mode` (from `melodia-fashion-editorial.css`):

```css
background:
  radial-gradient(circle at 8% 12%, rgba(201, 160, 168, 0.10), transparent 22%),
  radial-gradient(circle at 92% 8%, rgba(212, 184, 122, 0.08), transparent 26%),
  radial-gradient(circle at 50% 80%, rgba(102, 217, 255, 0.06), transparent 40%),
  linear-gradient(180deg, var(--night-void, #070912) 0%, var(--night-astral, #101736) 48%, var(--night-ink, #0b0f1f) 100%);
```

### 1.4 Font stacks — `wix/melodia-luxury-type.css`

Google Fonts import (verbatim):

```css
@import url("https://fonts.googleapis.com/css2?family=Azeret+Mono:wght@400;500;600&family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700&family=Instrument+Serif:ital@0;1&family=Syne:wght@500;600;700;800&display=swap");
```

Stacks and tracking:

```css
--font-brand: "Syne", "Avenir Next", "Segoe UI", sans-serif;
--font-display: "Instrument Serif", "Iowan Old Style", "Palatino Linotype", Palatino, serif;
--font-body: "Bricolage Grotesque", "Avenir Next", "Segoe UI", sans-serif;
--font-mono: "Azeret Mono", ui-monospace, "Cascadia Mono", "Segoe UI Mono", monospace;
--font-lede: "Instrument Serif", "Iowan Old Style", Palatino, serif;
--tracking-brand: 0.14em;
--tracking-display: 0.01em;
--tracking-body: 0.005em;
--tracking-mono: 0.08em;
```

`html[data-display-font="syne"]` swaps display to Syne (used by surreal-architecture.html; recommended for the TD page — denser, more technical lookbook signal).

Role mapping (from the same file): `h1/h2/h3`, `.section-head h2` → `--font-display`; `.lede`, `.human-lede` → `--font-lede` italic; `.eyebrow`, `.kicker`, `.magazine-kicker`, `.button`, `.nav-cta`, `.footer`, nav links → `--font-mono` uppercase.

### 1.5 Spacing / rhythm scale — from `melodia-editorial.css` + `melodia-site-chrome.css`

```css
--max: 1180px;                                        /* content column */
.melodia-shell .band .inner {
  width: min(100%, var(--max, 1180px));
  margin-inline: auto;
  padding-inline: clamp(1.1rem, 3vw, 2.75rem);
}
.melodia-shell .band { padding-block: clamp(3.25rem, 7vw, 5.5rem); }
.band { padding: 84px 40px; }                          /* editorial.css base */
@media (min-width: 900px) { .band { padding: 88px 46px; } }
@media (max-width: 680px) { .hero-inner, .band { padding-left: 18px; padding-right: 18px; } }
.section-head { gap: 32px 48px; margin-bottom: 36px; }
h1 { font-size: clamp(3.2rem, 8vw, 6.8rem); line-height: 0.88; margin-top: 14px; }
h2 { font-size: clamp(2.4rem, 5vw, 4.2rem); line-height: 0.92; }
h3 { font-size: 1.85rem; line-height: 1.05; }
.lede { font-size: clamp(1.25rem, 2.4vw, 1.65rem); line-height: 1.36; margin: 28px 0 0; }
```

Z-index scale (tokens): `--z-starfield: 0; --z-aurora: 0; --z-content: 1; --z-hero-celestial: 5; --z-nav: 50;`

---

## 2. Shared chrome recipe

### 2.1 `<head>` block (pattern from `surreal-architecture.html`, minimal variant)

```html
<!DOCTYPE html>
<html lang="en" data-page="touchdesigner-architecture" data-display-font="syne">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>TouchDesigner Surreal Architecture | Brennan Shepherd</title>
<meta name="description" content="TouchDesigner procedural worldgen — 13 Escher-inspired architecture pieces for Melodia, from Penrose stairs to Möbius structures, with TD→FBX→UE handoff." />
<meta property="og:title" content="Surreal Architecture Lookbook — TouchDesigner" />
<meta property="og:description" content="13 Escher-inspired procedural worldgen pieces. TouchDesigner → FBX → Unreal Engine." />
<meta property="og:image" content="https://fromage3900.github.io/my-site/generated/assets/touchdesigner/wg_relativity.png" />
<meta property="og:url" content="https://fromage3900.github.io/my-site/wix/touchdesigner-architecture.html" />
<meta name="twitter:card" content="summary_large_image" />
<link rel="stylesheet" href="melodia-luxury-type.css">
<link rel="stylesheet" href="melodia-editorial.css">
<link rel="stylesheet" href="melodia-fashion-editorial.css">
<link rel="stylesheet" href="melodia-premium-system.css">
<link rel="stylesheet" href="melodia-visual-breakdown.css">
</head>
```

**Do NOT hand-link** `melodia-tokens.css`, `melodia-site-chrome.css`, `melodia-starfield.css`, `melodia-night-theme.css` — `melodia-editorial.css` already `@import`s all of them (lines 1–12). `melodia-visual-breakdown.css` is required if using `viz-beat` / `viz-plate` / `viz-rail` patterns (recommended for the editorial + pipeline sections; see hero-renders.html precedent).

### 2.2 Shell + nav (verbatim pattern from surreal-architecture.html, lines 39–49)

```html
<body>
<div class="melodia-shell fashion-mode" data-mg="chrome" data-hero="editorial" data-effects="starfield,holo" data-nav-cta="application-hub.html" data-nav-cta-label="Application hub">
<header class="shell-nav" aria-label="Portfolio navigation">
  <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"></span>Brennan Shepherd</a>
  <nav class="nav-links" aria-label="Sections">
    <a href="index.html">Home</a>
    <a href="geometry-nodes.html">Geometry</a>
    <a href="surreal-architecture.html">Surreal Arch</a>
    <a href="hero-renders.html">Renders</a>
  </nav>
  <a class="nav-cta button-premium" href="application-hub.html">Application hub</a>
</header>
```

Notes:
- `melodia-site-nav.js` (end of body) reads `data-nav-cta` / `data-nav-cta-label` and marks the current page link `.is-active` (gold, per `melodia-site-chrome.css:28-34`).
- `data-effects="starfield,holo"` is the chrome-level effects set; the fuller lookbook variant (hero-renders.html) uses `data-mg="full" data-hero="cosmic" data-visual="lookbook" data-effects="starfield,orrery,holo,magical"`. Use the fuller set for the TD page since the brief asks for magical-girl-ready lookbook energy; keep `data-visual="lookbook"` so `melodia-visual-breakdown.css` lookbook overrides engage.
- Optional: `data-starfield-intensity="cosmic"` (index.html) — starfield canvas opacity 0.72 vs default 0.62.

### 2.3 Footer (verbatim pattern)

```html
<footer class="footer">
  <div class="inner">
    <span>Brennan Shepherd / Surreal Architecture — TouchDesigner</span>
    <span>13 worldgen pieces · TD → FBX → UE</span>
  </div>
</footer>
```

### 2.4 Script stack (end of `<body>`, order matters — from hero-renders.html / surreal-architecture.html)

```html
<script src="melodia-magical-girl.js"></script>
<script src="melodia-starfield.js"></script>
<script src="melodia-dream-shaders.js"></script>
<script src="melodia-site-nav.js"></script>
```

Add `melodia-orrery-system.js` + `melodia-planetarium.js` only if using `.section-orrery` slots. Note: `melodia-escher-interact.js` already exists in wix/ — reuse it for any interactive tessellation element rather than writing new drag logic.

### 2.5 Starfield / background approach

- Background = fixed-position `<canvas class="melodia-starfield-canvas">` injected by `melodia-starfield.js` inside `.melodia-shell` (`melodia-starfield.css`): `position: fixed; inset: 0; z-index: 0; pointer-events: none; mix-blend-mode: screen; opacity: 0.62`.
- Base shell gradient comes from `.melodia-shell.fashion-mode` (see §1.3). Bands alternate `.band paper` / `.band astral` (night overrides force paper bands dark: `linear-gradient(180deg, rgba(16, 23, 54, 0.92), rgba(7, 9, 18, 0.94))`).
- `.band.paper + .band.astral::before` auto-draws a 2px gold hairline between alternating bands (editorial.css:604-610) — free ornament if you keep the paper/astral alternation.

---

## 3. Page section blueprint

Band alternation: hero → paper → astral → paper → astral → paper (matches surreal-architecture.html rhythm). Every content section uses `.band > .inner`, with `.section-head` (eyebrow + h2 left, `.human-lede` right) as the standard opener.

### 3.1 Hero (band-as-hero pattern, surreal-architecture.html lines 52–67)

```html
<main id="main">
<section class="band sx-open" aria-labelledby="td-title">
  <div class="inner">
    <p class="eyebrow magazine-kicker">TouchDesigner · Procedural worldgen</p>
    <h1 id="td-title">Rooms Escher never finished.</h1>
    <p class="lede">Thirteen impossible architectures grown node-by-node in TouchDesigner — Penrose stairs to Möbius halls — baked to FBX and walked in Unreal.</p>
    <ul class="sx-stat-row" aria-label="Project proof stats">
      <li><strong>Pieces</strong> 13</li>
      <li><strong>Source</strong> TouchDesigner</li>
      <li><strong>Handoff</strong> FBX → UE5</li>
      <li><strong>Plate</strong> 1600 × 1200</li>
    </ul>
    <div class="button-row" style="margin-top:1.25rem;">
      <a class="button primary button-premium-primary" href="#lookbook">Open the lookbook</a>
      <a class="button button-premium" href="surreal-architecture.html">Blender genomes</a>
      <a class="button button-premium" href="geometry-nodes.html">Geometry pipelines</a>
    </div>
    <figure class="sx-hero-plate">
      <img src="../generated/assets/touchdesigner/wg_relativity.png" alt="Relativity — TouchDesigner procedural worldgen plate, Melodia" width="1600" height="1200" />
    </figure>
  </div>
</section>
```

Supporting CSS (copy verbatim from surreal-architecture.html lines 18–21):

```css
.sx-hero-plate { margin-top: 1.75rem; max-width: 920px; }
.sx-hero-plate img { width: 100%; height: auto; display: block; border: 1px solid rgba(255,255,255,0.12); }
.sx-stat-row { display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; margin: 1.25rem 0 0; padding: 0; list-style: none; font-family: var(--font-mono); font-size: 0.68rem; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(240,220,240,0.78); }
.sx-stat-row strong { color: var(--iri-gold, #ffe666); font-weight: 500; }
```

(`sx-open` is already styled as an editorial band-hero in `melodia-site-chrome.css:72-78` — reuse, don't rename.)

### 3.2 Lookbook grid — 13 pieces (`.band paper`, id="lookbook")

Standard opener:

```html
<section class="band paper fashion-band" id="lookbook" aria-labelledby="td-lookbook-title">
  <div class="inner">
    <div class="editorial-rule"><span class="diamond" aria-hidden="true"></span><span>The Lookbook · 13 pieces</span><span class="diamond" aria-hidden="true"></span></div>
    <div class="section-head">
      <div>
        <p class="eyebrow magazine-kicker">Worldgen plates</p>
        <h2 id="td-lookbook-title">Thirteen impossible rooms, one grid.</h2>
      </div>
      <p class="human-lede">Each plate is a single TouchDesigner network — geometry, light, and capture in one graph. Click any plate for full size.</p>
    </div>
    <div class="image-grid lookbook-grid">
      <!-- card pattern below × 13 -->
    </div>
  </div>
</section>
```

Card pattern — copied from hero-renders.html lines 59–62 (`.image-card.fashion-frame` inside `.image-grid.lookbook-grid`). The `4/5` portrait crop comes from the proof-grid pattern (surreal-architecture.html line 33: `aspect-ratio: 4/5; object-fit: cover;`); adapt to 4/3 to match the 1600×1200 plates:

```html
<a class="image-card fashion-frame" href="../generated/assets/touchdesigner/wg_penrose_stairs.png">
  <img src="../generated/assets/touchdesigner/wg_penrose_stairs.png" alt="Penrose Stairs — TouchDesigner worldgen plate" loading="lazy" width="1600" height="1200" />
  <div>
    <h3>Penrose Stairs</h3>
    <p><em>After M.C. Escher, "Ascending and Descending" (1960)</em> — a staircase that climbs forever and arrives nowhere, grown from a single feedback loop.</p>
  </div>
</a>
```

Small page-local CSS for the 4:3 crop + Escher-reference line:

```css
.lookbook-grid .image-card img { aspect-ratio: 4 / 3; object-fit: cover; }
.lookbook-grid .image-card p em { color: var(--gold); font-style: italic; }
```

The 13 pieces (slug ↔ Escher reference):

| # | slug (`wg_<slug>.png`) | Piece name | Escher reference |
|---|---|---|---|
| 1 | `penrose_stairs` | Penrose Stairs | Ascending and Descending (1960) |
| 2 | `spiral_staircase` | Spiral Staircase | House of Stairs (1951) |
| 3 | `fractal_tower` | Fractal Tower | Belvedere-adjacent tower studies |
| 4 | `tessellation` | Tessellation | Regular Division of the Plane |
| 5 | `belvedere` | Belvedere | Belvedere (1958) |
| 6 | `waterfall` | Waterfall | Waterfall (1961) |
| 7 | `infinite_library` | Infinite Library | library-of-Babel reading of his interiors |
| 8 | `relativity` | Relativity | Relativity (1953) |
| 9 | `ascending_descending` | Ascending & Descending | Ascending and Descending (1960) |
| 10 | `infinite_corridor` | Infinite Corridor | perspective corridor studies |
| 11 | `impossible_cube` | Impossible Cube | Necker-cube prints / Belvedere's cube |
| 12 | `stair_well` | Stair Well | House of Stairs (1951) |
| 13 | `mobius_architecture` | Möbius Architecture | Möbius Strip II (1963) |

### 3.3 Pipeline section — TD → FBX → UE (`.band astral`, `path-list` pattern)

The site's canonical "process steps" component is `.path-list` / `.path-row` (melodia-editorial.css:760-780):

```html
<section class="band astral" aria-labelledby="td-pipeline-title">
  <div class="inner">
    <div class="section-head">
      <div>
        <p class="eyebrow">Pipeline</p>
        <h2 id="td-pipeline-title">Node graph to game world.</h2>
      </div>
      <p class="human-lede">Every piece follows the same honest path: TouchDesigner procedural build, FBX bake, Unreal Engine staging under Melodia lighting.</p>
    </div>
    <div class="path-list">
      <div class="path-row">
        <span>Step 01</span>
        <div>
          <h3>TouchDesigner worldgen</h3>
          <p>SOP/CHOP-driven procedural architecture — feedback loops, instancing, and Escher constraint solvers in a single .toe network.</p>
        </div>
        <b>.toe</b>
      </div>
      <div class="path-row">
        <span>Step 02</span>
        <div>
          <h3>FBX bake</h3>
          <p>Geometry locked and exported per piece — named meshes, clean pivots, ready for kitbash reuse beside the SurrealArch Blender library.</p>
        </div>
        <b>.fbx</b>
      </div>
      <div class="path-row">
        <span>Step 03</span>
        <div>
          <h3>Unreal staging</h3>
          <p>Imported into the EnvSandbox (L_EscherAscent) under Melodia night lighting — walkable proof that the impossible rooms hold up in-engine.</p>
        </div>
        <b>UE5</b>
      </div>
    </div>
  </div>
</section>
```

(`.path-row` collapses to single column under 680px automatically — editorial.css:923.)

### 3.4 Editorial section — Escher research notes (`.band paper`, `viz-beat` pattern)

Copied from hero-renders.html lines 71–94 (`viz-spine` / `viz-beat` / `is-flip`) — the site's editorial "image beside copy" spine. Requires `melodia-visual-breakdown.css`:

```html
<section class="band paper fashion-band" aria-labelledby="td-research-title">
  <div class="inner">
    <div class="editorial-rule"><span class="diamond" aria-hidden="true"></span><span>Escher · research notes</span><span class="diamond" aria-hidden="true"></span></div>
    <div class="section-head">
      <div><h2 id="td-research-title">What the lithographs taught the graphs.</h2></div>
      <p class="human-lede">Working notes from rebuilding thirteen Escher spaces as procedural systems — where the math bent, and where the magic had to be staged.</p>
    </div>
    <div class="viz-spine">
      <article class="viz-beat">
        <a class="viz-plate" href="../generated/assets/touchdesigner/wg_waterfall.png">
          <img src="../generated/assets/touchdesigner/wg_waterfall.png" alt="Waterfall — TouchDesigner worldgen plate" loading="lazy" />
          <div class="viz-caption"><strong>Waterfall</strong><span>Perpetual motion</span></div>
        </a>
        <div class="viz-copy">
          <h3>The mill that powers itself.</h3>
          <p>Escher's aqueduct only works from one camera. The TD build keeps the paradox volumetric — the fall is real geometry; the return is a masked loop.</p>
        </div>
      </article>
      <article class="viz-beat is-flip">
        <a class="viz-plate" href="../generated/assets/touchdesigner/wg_relativity.png">
          <img src="../generated/assets/touchdesigner/wg_relativity.png" alt="Relativity — TouchDesigner worldgen plate" loading="lazy" />
          <div class="viz-caption"><strong>Relativity</strong><span>Three gravities</span></div>
        </a>
        <div class="viz-copy">
          <h3>Gravity as an instancing parameter.</h3>
          <p>Three stair systems, three up-vectors, one SOP network. The inhabitants are placement masks; the impossibility is just rotation math.</p>
        </div>
      </article>
    </div>
  </div>
</section>
```

Optional cross-links (patterns already on the site): `application-hub.html#logic` (interactive Escher tessellation graph), `world-bible.html` (art direction), `surreal-architecture.html` (Blender GN sibling project).

---

## 4. Asset path convention

- Pages live in `wix/`; assets live in `generated/assets/`; references from a wix page are always **`../generated/assets/...`** (see every `<img>` in hero-renders.html / surreal-architecture.html).
- TD plates: `generated/assets/touchdesigner/wg_<slug>.png`, **1600 × 1200** (4:3). Slugs per the table in §3.2. Directory does not exist yet — create `generated/assets/touchdesigner/` when the first renders land.
- Hero `<img>` carries explicit `width="1600" height="1200"` (CLS reservation, matching `width="1600" height="2000"` precedent in surreal-architecture.html line 64).
- OG/social images are absolute URLs: `https://fromage3900.github.io/my-site/generated/...` (see index.html lines 10–11). Use one of the 13 plates as og:image (suggested: `wg_relativity.png`).
- CDN cache-busting, where needed, uses `?v=YYYYMMDDxx` query strings on local CSS links (e.g. `melodia-fashion-editorial.css?v=20260715p4`) — plain links are fine for a new page.

---

## 5. Accessibility & performance conventions already on the site

1. **Skip link** — `.skip-link` styles ship in `melodia-site-chrome.css` and `melodia-editorial.css`; surreal-architecture.html doesn't render one but index.html-pattern pages do. Recommended markup first inside `.melodia-shell`: `<a class="skip-link" href="#main">Skip to content</a>` with `<main id="main">`.
2. **Landmarks & labelling** — `<header class="shell-nav" aria-label="Portfolio navigation">`, `<nav class="nav-links" aria-label="Sections">`, every `<section class="band" aria-labelledby="...">` tied to its `h2 id`.
3. **Decorative elements** — `aria-hidden="true"` on `.brand-mark`, orrery slots, `.editorial-rule .diamond`, parallax layers.
4. **Focus visibility** — `.shell-nav a:focus-visible`, `.button:focus-visible`, `.image-card:focus-visible` get `outline: 2px solid rgba(102, 217, 255, 0.85); outline-offset: 3px` (editorial.css:104-112). Keep lookbook cards as `<a class="image-card">` so they inherit this.
5. **Reduced motion** — `@media (prefers-reduced-motion: reduce)` handled globally: starfield dims to 0.4 (starfield.css:36-40), orrery/ring animations disabled (fashion-editorial.css:211-214), scroll-behavior auto, shimmer/iridescent animations off (premium-system.css:334-351), landscape videos hidden with poster fallback (editorial.css:351-361). No new page-level work needed if you reuse these classes.
6. **Lazy loading** — every below-fold `<img>` uses `loading="lazy"`; the hero plate is eager (no attribute).
7. **Touch targets** — `.nav-cta, .button { min-height: 44px; }` (editorial.css:206-219).
8. **Dynamic content** — JS-injected grids use `aria-live="polite"` (hero-renders.html `id="shaderProofGrid"` etc.). If the TD page is fully static, not needed.
9. **`text-wrap: balance`** on `.section-head h2` (editorial.css:624-627); `overflow-x: clip` on shell.
10. **Alt text convention** — `"<Piece name> — TouchDesigner worldgen plate, Melodia"`; descriptive, not keyword-stuffed.

---

## 6. Checklist for the authoring pass

- [ ] New file `wix/touchdesigner-architecture.html` using §2.1 head + §2.2 nav + §2.3 footer + §2.4 scripts
- [ ] `data-page="touchdesigner-architecture"`, `data-display-font="syne"`, `data-visual="lookbook"`
- [ ] Hero → lookbook (13 cards) → pipeline (3 path-rows) → editorial (2 viz-beats) sections; alternate `.band paper` / `.band astral`
- [ ] 13 renders exported to `generated/assets/touchdesigner/wg_<slug>.png` at 1600×1200
- [ ] og:image + twitter card absolute URLs; description meta under ~160 chars
- [ ] Verify: skip-link focus, reduced-motion pass, mobile (720px nav hides CTA; 680px grids collapse), starfield renders under content
