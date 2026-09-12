# Melodia — The Ultimate Palette (2026-09-10)

**Status:** PROPOSED — names existing colours, changes nothing visually.
**Owner brief:** *"use a very specific palette inspired by reverse 1999, nikki and melodia to make the ultimate one."*

---

## 0. Provenance — what is and isn't claimed

**Not claimed:** that any hex below is sampled from Reverse: 1999 or Infinity Nikki. I did not
extract colour values from either game, and no source I found publishes a usable palette spec.
Presenting invented values as "the Reverse: 1999 palette" would be a fabrication.

**Claimed:** these are the colours **already live in `my-site/wix/*.css` right now** — the 36 raw
hex literals the token linter flags. They were chosen by the owner over the life of the project;
they were simply never given names. This document names them in a coherent system that reads in the
register those two references occupy.

**Why that matters:** replacing `color: #0a0711` with `color: var(--color-ink-800)`, where
`--color-ink-800: #0a0711`, is **pixel-for-pixel identical**. The linter passes, the freeze is
respected, and the site does not change by one shade. This is a naming pass, not a redesign.

---

## 1. The three registers

| Register | Source of the *quality* | Where it lives in Melodia |
|---|---|---|
| **Ink & Paper** | Reverse: 1999 — period editorial, aged stock, desaturated film, letterpress | The 27 raw hexes already in `works-on-paper.css` / `curated-art.css` — near-black purple-cast inks and warm parchments |
| **Pastel Accent** | Infinity Nikki — high-key fashion-fantasy, soft rose/lavender/aqua/butter, iridescent | The accent hexes already in `works-on-paper.css` (`#d995b6`, `#78cfd8`, `#8f75bc`, `#c8a46a`) |
| **Celestial** | Melodia's own existing system | `--primitive-plum-*`, `--primitive-gold-*`, `--primitive-astral-*`, `--primitive-ivory-*` |

The synthesis is: **Reverse: 1999's aged editorial ground + Nikki's pastel accent register + Melodia's
existing plum/gold celestial spine.** All three are already present in the codebase; the third was
already tokenised.

---

## 2. New primitive families

Values are ordered light → dark, matching the existing `-50 … -900` convention.

### `ink` — near-black, purple-cast (the Reverse: 1999 ground)

| Token | Hex | Currently written as | In |
|---|---|---|---|
| `--primitive-ink-700` | `#0b0914` | `#0b0914` | curated-art.css:11 |
| `--primitive-ink-800` | `#0a0711` | `#0a0711` | works-on-paper.css:2 |
| `--primitive-ink-850` | `#090713` | `#090713` | curated-art.css:5 |
| `--primitive-ink-900` | `#0d0915` | `#0d0915` | works-on-paper.css:78,79 |
| `--primitive-ink-950` | `#08060e` | `#08060e` | works-on-paper.css:79 |
| `--primitive-ink-1000` | `#030307` | (inside `rgba(3,3,7,.985)`) | works-on-paper.css:130 |

### `paper` — aged stock (the editorial ground)

| Token | Hex | Currently written as |
|---|---|---|
| `--primitive-paper-50`  | `#fff8ee` | `#fff8ee` (curated-art 514/547, works-on-paper 130/138) |
| `--primitive-paper-100` | `#f8efe2` | inside `rgba(248,239,226,.68)` |
| `--primitive-paper-200` | `#f7f0e7` | `#f7f0e7` (works-on-paper 78/79) |
| `--primitive-paper-300` | `#f5eddf` | `#f5eddf` (works-on-paper:5) |
| `--primitive-paper-400` | `#eee1d4` | `#eee1d4` (works-on-paper:6) |
| `--primitive-paper-500` | `#ede3d6` | `#ede3d6` (works-on-paper:408) |

> `--primitive-ivory-50` already exists and also resolves to `#fff8ee`. Keep both — `ivory` is the
> celestial register, `paper` is the editorial one. They may legitimately diverge later.

### `dusk` — deep plum-mauve surfaces

| Token | Hex | Currently written as |
|---|---|---|
| `--primitive-dusk-600` | `#291f33` | `#291f33` (works-on-paper:180) |
| `--primitive-dusk-700` | `#271c30` | `#271c30` (works-on-paper:7) |
| `--primitive-dusk-800` | `#241b2e` | inside `(#241B2E` (melodia-recruiter-hardening.css:4) |
| `--primitive-dusk-900` | `#201929` | `#201929` (curated-art.css:10) |

### `mauve` — muted grey-violet text

| Token | Hex | Currently written as |
|---|---|---|
| `--primitive-mauve-300` | `#d8d4dc` | inside `rgba(216,212,220,…)` |
| `--primitive-mauve-500` | `#807b87` | `#807b87` (works-on-paper:250) |
| `--primitive-mauve-600` | `#796b7d` | `#796b7d` (works-on-paper:8) |
| `--primitive-mauve-700` | `#716c78` | `#716c78` (works-on-paper:250) |

### Nikki accent register

| Token | Hex | Currently written as | Reads as |
|---|---|---|---|
| `--primitive-rose-400`   | `#d995b6` | `#d995b6` | sakura rose |
| `--primitive-aqua-400`   | `#78cfd8` | `#78cfd8` | seafoam / aqua |
| `--primitive-wisteria-400` | `#8f75bc` | `#8f75bc` | soft violet |
| `--primitive-brass-400`  | `#c8a46a` | `#c8a46a`, `#C9A86A` | warm brass (two casings — one token) |
| `--primitive-copper-500` | `#bb7c55` | `#bb7c55` | copper |
| `--primitive-bronze-700` | `#5b372b` | `#5b372b` | deep bronze |
| `--primitive-bronze-800` | `#4d2b26` | `#4d2b26` | darker bronze |

### Aliases

| Token | Hex | Note |
|---|---|---|
| `--primitive-paper-0` | `#ffffff` | `#fff` / `#ffffff` — pure white, keep explicit and rare |

---

## 3. Semantic layer

Primitives are not used directly in components. These alias them:

```
--color-ink            → --primitive-ink-900     (default body ink on paper)
--color-ink-deep       → --primitive-ink-1000    (true black ground)
--color-paper          → --primitive-paper-300   (default page stock)
--color-paper-light    → --primitive-paper-50    (highlight stock)
--color-dusk           → --primitive-dusk-800    (dark section ground)
--color-text-on-paper  → --primitive-ink-800
--color-text-on-dusk   → --primitive-paper-200
--color-text-muted     → --primitive-mauve-600
--color-rule           → --primitive-mauve-300   (thin dividers)
--color-accent-rose    → --primitive-rose-400
--color-accent-aqua    → --primitive-aqua-400
--color-accent-violet  → --primitive-wisteria-400
--color-accent-brass   → --primitive-brass-400
```

---

## 4. What this unlocks

`npm run lint:tokens` currently reports **36 hard errors**. Every one is a raw hex that this document
names. Mapping them is mechanical and pixel-neutral, so the token step can become **blocking in CI**
(delete `continue-on-error` in the advisory step added in PR #12) without changing the site.

**This is the actual "ultimate palette": not new colours, but every colour finally having a name.**

---

## 5. Honest caveats

- **The two reference palettes were not sampled.** If you want true extraction, the source is the
  Reverse: 1999 Art Book Vol. 1 and Infinity Nikki's in-game dye palettes — both need a human looking
  at images, not a web search.
- **`--primitive-ink-1000: #030307`** arrives only via `rgba(3,3,7,.985)`. Naming it means splitting
  the alpha into a separate channel; do that deliberately, not by rounding.
- **Two casings of one colour** (`#c8a46a` / `#C9A86A`) collapse to a single token. That is a real
  fix, but confirm the CSS was not relying on the difference.
- **Freeze:** adding tokens to `wix/melodia-tokens.css` and editing the 5 stylesheets
  (`works-on-paper.css`, `curated-art.css`, `melodia-editorial.css`, `melodia-mahou-flourish.css`,
  `melodia-recruiter-hardening.css`) touches paths **not** on the `allowed_exact` list. Even though
  the change is pixel-neutral, it should register a freeze exception naming those paths — the
  manifest's own rule says a deliberate exception must be recorded, not assumed.
