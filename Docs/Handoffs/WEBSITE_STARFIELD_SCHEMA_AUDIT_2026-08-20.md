# Website Starfield / Schema / FX Audit — 2026-08-20

**Scope:** Live Vite root `C:\EnvironmentPortfolio\wix\` + `content/site-manifest.json` (+ copy/plates).  
**Live check:** `http://127.0.0.1:3000/` → HTTP 200. Chrome headless `--dump-dom` after ~4s virtual time confirmed FX mounts.  
**Hard reset / HUD cull / magical-girl context:** Index keeps `data-effects="starfield,holo,magical"` and `data-mg="full"`, but deliberately strips orrery / instruments / henshin / wish-toggle chrome via `melodia-home-hardening.css`.

---

## Executive verdict

| Area | Verdict |
|------|---------|
| Homepage FX boot | **Starfield + dream layers + magical-girl ambient mount and run** |
| Homepage visibility | **Starfield canvas lives at `z-index: 0` under opaque hero plates** — intentional HUD cull; hero sparkles replaced by `.hero-star-accents` |
| Schema (FallenMoon vs Orrery) | **Correctly separated** in manifest + index plates; residual pillar-detect conflation in dream-shaders JS |
| Dead / suppressed HUD | Orrery, planetarium, instruments, henshin, wish-toggle on index — leave dead |
| Missed wiring | **application-hub declares `planetarium` but does not load `melodia-planetarium.js` and has no mount** |

---

## Feature status table

| Feature | Status | Evidence path | Recommend |
|---------|--------|---------------|-----------|
| **data-effects (index)** `starfield,holo,magical` | **live** | `wix/index.html` L61 | Keep — recruiter-safe cosmic shell |
| **data-effects orrery (index)** | **missing** (culled) | Not in index `data-effects`; present on `cosmic-orrery.html`, `shader-breakdowns.html`, etc. | **leave dead** on homepage |
| **data-effects planetarium (index)** | **missing** (culled) | Index has no `planetarium`; `application-hub.html` declares it | Soft restore on **hub** only (see below), not index |
| **data-effects instruments (index)** | **missing** (culled) | Only full suite on `melodia-atelier-lab.html` | **leave dead** on homepage |
| **data-effects holo** | **live** | Index + editorial `bootEffects` → `MelodiaDreamShaders.init()` | Keep |
| **data-effects magical** | **live** (ambient) / **suppressed** (wish HUD) | `melodia-magical-girl.js` boots; wish toggle + henshin hidden by home-hardening | Ambient restore soft already; **leave dead** wish/henshin on index |
| **MelodiaStarfield canvas** `#ambient-starfield` | **live** (boots) / **suppressed** (under hero) | JS: `melodia-starfield.js`; CSS: `melodia-starfield.css` `z-index:0`; comment in `melodia-home-hardening.css` L743–747; dump-dom: canvas present, `data-starfield-intensity="cosmic"` | **restore soft** in transparent astral/void bands only — do not put HUD over hero |
| **starfield-reduced** | **live** when `prefers-reduced-motion` | `melodia-starfield.js` adds class; opacity 0.36 in `melodia-starfield.css` | Keep a11y behavior |
| **Legacy `.star-layer`** | **deprecated** | `melodia-editorial.css` L377–380 `display:none !important` | **delete** markup if any remains; CSS can stay until sweep |
| **parallax-layer-3 (nebula)** | **deprecated / suppressed** | `melodia-dream-shaders.css` L748–750 `display:none`; **absent from index HTML** | **leave dead** (warped smear noted in CSS comment) |
| **parallax-layer-4 (constellation)** | **deprecated / missing** | Defined in `enhanced-cosmic-hero-premium.css`; driven by `premium-cosmic-hero.js`; **not linked on index** | **leave dead** on index; live on case-study pages that load premium hero |
| **dream-sparkle-layer** | **live** (index boosted) | Base was near-invisible `opacity:0.03` + twinkle 0.02–0.04; index override `0.48` in home-hardening L757–761 | Soft base bump applied 2026-08-20 (see Safe restores) |
| **dream-aurora-layer** | **live** (subtle) | Mounted by `melodia-dream-shaders.js`; opacity ~0.18 | Keep / optional soft raise later |
| **dream-planet-layer (Figma planet)** | **live but quiet** | Mounted always with holo; cosmic hero opacity 0.22 (`melodia-dream-shaders.css` L264–266); **no index boost** (unlike sparkle/bubbles) | **restore soft** on index void shell |
| **figma-bubble-layer** | **live** (index boosted) | Home-hardening L769–772 `opacity:0.38 !important` | Keep |
| **hero-star-accents / diamonds** | **live** | `index.html` L136–142 + home-hardening L774–986; z-index 9 over hero media | Keep as hero replacement for culled global starfield |
| **cosmic-instruments** | **suppressed / orphaned CSS** | CSS imported via `melodia-editorial.css` `@import melodia-cosmic-instruments.css`; JS not on index; home-hardening `display:none !important` L180 | **leave dead** on index; unload JS on pages that declare no `instruments` (cleanup later) |
| **hero-orrery-detail / MelodiaOrrery** | **suppressed / missing on index** | No `melodia-orrery-system.js` on index; hardening hides `.hero-orrery-detail` | **leave dead** on index; keep on `cosmic-orrery.html` |
| **Planetarium mini** | **live** on recruiter / world-bible / hero-renders; **broken flag on hub** | Mounts: `recruiter-one-sheet.html`, `world-bible.html`, `hero-renders.html`. Hub: `data-effects` includes `planetarium` but **no** `melodia-planetarium.js` and **no** `[data-planetarium]` | **restore soft** on hub: link script + mini mount |
| **Magical-girl ambient (crystals / ribbons)** | **live** | dump-dom: `mg-layer`, `mg-tier-full`, `mg-ambient` | Keep |
| **mg-bow-toggle (wish-mode)** | **suppressed** | Mounted in DOM; `html[data-page="index"] … Toggle wish-mode` → `display:none !important` (home-hardening L186) | **leave dead** (HUD cull) |
| **Henshin / mahou burst** | **suppressed / mostly unloaded** | Index links `melodia-mahou-flourish.css` but not JS; triggers hidden by hardening | **leave dead** on index |
| **Cosmic Orrery page / nav** | **live** | `content/site-manifest.json` env slug `cosmic-orrery` worldNum 5; `melodia-site-nav.js` Orrery link; index footer/env note link | Keep |
| **L_FallenMoon vs Orrery naming** | **live / clarified** | Manifest: FallenMoon = World 04 / `pcg-system-impact`; Orrery = Pillar / separate. Index plate alt + hub copy: “not Orrery terrain” | Keep separation; fix pillar-detect conflation |
| **dream-shaders `detectPillar`** | **deprecated logic bug** | `melodia-dream-shaders.js` L41 maps `orrery\|cosmic\|orbit` → `'fallenmoon'` | **restore soft**: split `orrery` pillar from `fallenmoon` |
| **site-manifest pages nav flags** | **live (partial drift)** | Manifest `nav:true`: index, recruiter, hiring-dossier, resume, cosmic-orrery, shader-breakdowns. Runtime nav (`melodia-site-nav.js`) differs (Hub, Breakdown, Renders, Stage, Worlds…) | Align later; not FX-blocking |
| **Index local nav** | **live** | Site-nav keeps index `#` anchors (`melodia-site-nav.js` L86–92) | Keep |
| **OG / meta “4 canonical levels”** | **stale copy** | `index.html` meta still says 4 levels; manifest has 5 envs including Orrery pillar | Soft copy update |
| **Deprecated pages (`_deprecated/*`)** | **deprecated** | e.g. `baroque-grotto.html`, old infold-application with full FX suite | **leave dead** / archive; do not re-link from live nav |
| **enhanced-cosmic-hero / premium parallax** | **missing on index** | Loaded on case studies + orrery; not on index | **leave dead** on index (replaced by home-hardening hero stack) |

---

## data-effects matrix (live pages, abbreviated)

| Page | data-effects | Scripts that matter |
|------|--------------|---------------------|
| **index** | `starfield,holo,magical` | starfield, dream-shaders, magical-girl — **no** orrery / planetarium / instruments |
| cosmic-orrery | `starfield,orrery,holo,magical` | + orrery-system, premium-cosmic-hero |
| application-hub | `starfield,planetarium,holo,magical` | starfield, magical, orrery-system — **planetarium JS missing** |
| recruiter-one-sheet | `starfield,holo,magical` | + planetarium.js + mini mount (planetarium boots via mountAll regardless of flag) |
| melodia-atelier-lab | full suite incl. instruments | full FX lab |
| melodia-gameplay-loop / world-bible | includes orrery + planetarium | scripts present |
| resume / chrome pages | often `starfield,holo` (no magical) | lighter |

Editorial default when `data-effects` omitted: `['starfield','holo','magical']` (`melodia-editorial.js` `getEffects`).

---

## Starfield deep dive

1. **Init gate:** `hasEffect(shell, 'starfield') && MelodiaStarfield` → intensity `cosmic` when `data-hero="cosmic"` (index qualifies).
2. **Mount:** canvas `#ambient-starfield.melodia-starfield-canvas` as first child of `.melodia-shell`.
3. **CSS:** `position:fixed; inset:0; z-index:0; mix-blend-mode:screen; opacity:0.62` (0.72 cosmic).
4. **Why “gone” on first paint:** Home-hardening documents that global starfield + dream-sparkle sit **behind opaque hero media**. Hero replacement FX = `.hero-star-accents` at z-index 9.
5. **Void band opportunity:** Index forces `.band.astral { background: transparent }` (home-hardening L1174–1177), so the fixed starfield **can** peek through mid-page astral sections if shell/body don’t paint opaque over it. Soft restore = ensure band scrims stay translucent + optionally raise canvas opacity slightly in those regions (not instruments HUD).
6. **Reduced motion:** Headless dump showed `starfield-reduced` + `dream-reduced` (Chrome prefers-reduced-motion in that run). Real user browsers without the preference get full animation; with preference, opacity drops and sparkle animation is killed (index rules).

---

## Schema notes (FallenMoon vs Orrery)

| Entity | Manifest | Homepage plate | Notes |
|--------|----------|----------------|-------|
| L_FallenMoon | World 04 → `pcg-system-impact.html` | `level_fallen_moon.png` | Cosmic crater / PCG — **not** Orrery terrain |
| Cosmic Orrery | Pillar · World 05 → `cosmic-orrery.html` | Linked in env grid caption / hub plate | Standalone celestial case study; `nav: true` |
| Pillar detect bug | — | — | `detectPillar` collapses orrery tokens into `fallenmoon` — holo rim tint can mis-tag Orrery cards |

No dead Orrery slug in manifest. Duplicate *world naming* is intentional separation, not a merge error — residual risk is **UI copy** and **auto pillar tagging**.

---

## Prioritized restore list (void / magical-girl homepage) — top 5

1. **Soft starfield peek on transparent astral/void bands** — keep canvas behind hero; verify/raise mid-page visibility without reintroducing instruments/orrery HUD. *(restore soft)*
2. **Soft `dream-planet-layer` boost on index** — mirror sparkle/bubble index boosts (~0.28–0.36 opacity, screen blend); Figma planet is mounted but quiet. *(restore soft)*
3. **Keep / polish hero-star-accents** — already the correct magical-girl sparkle plane over opaque hero; optional density tweak only. *(live — polish)*
4. **Fix hub planetarium wiring** — `application-hub` already advertises `planetarium` in `data-effects`; add `melodia-planetarium.js` + a mini mount (same pattern as recruiter). *(restore soft — hub, not home HUD)*
5. **Split `detectPillar` orrery vs fallenmoon** — prevents schema bleed in holo rims / motif accents. *(restore soft / correctness)*

**Do not restore on homepage:** cosmic-instruments, hero orrery detail, henshin burst, wish-mode bow toggle, parallax-layer-3/4, legacy `.star-layer`.

---

## Safe restores applied this pass

| Change | File | Why |
|--------|------|-----|
| Bumped global `.dream-sparkle-layer` opacity `0.03` → `0.22` | `wix/melodia-dream-shaders.css` | Base sparkle was effectively invisible on non-index void shells |
| Bumped `@keyframes dream-sparkle-twinkle` `0.02/0.04` → `0.16/0.28` | same | Animation was collapsing opacity back to near-zero |

Index still overrides sparkle to ~0.48 via home-hardening (unchanged). No HUD / instruments / orrery re-enabled.

---

## Missed opportunities (backlog)

- Soft starfield in footer / transparent astral bands (index already transparentizes `.band.astral`).
- Optional `data-planetarium="mini"` band on hub or world-bible cross-link from homepage env section (link to Orrery already exists).
- Align `site-manifest` `nav` flags with `melodia-site-nav.js` LINKS.
- Update index meta/OG from “4 canonical levels” → 4 levels + Cosmic Orrery pillar.
- Stop importing `melodia-cosmic-instruments.css` on pages that never mount instruments (bundle hygiene).

---

## Live dump-dom snapshot (2026-08-20, headless)

```
shell classes: astral-mode starfield-reduced dream-reduced mg-ui-chrome mg-tier-full mg-ambient
data-effects: starfield,holo,magical
data-starfield-intensity: cosmic
canvas #ambient-starfield: present
dream-sparkle / aurora / planet / figma-bubble: present
hero-star-accents: present
cosmic-instruments / planetarium: absent
mg-bow-toggle: present in DOM (CSS-hidden on index)
parallax-layer-3 / 4: absent
```

---

## Suggested next agent prompt

> Soft-restore homepage void starfield peek + index `dream-planet-layer` opacity (no instruments/orrery/henshin). Wire `melodia-planetarium.js` + mini mount on `application-hub.html`. Split dream-shaders `detectPillar` orrery vs fallenmoon.
