# Melodia on Wix — fromageart.xyz

Wix can't import a Figma file, so this kit translates the Melodia system into things Wix *can* use: a color + font cheat sheet you apply once in the Editor, two ready-to-paste **HTML embeds** (Asset Passport + Hero banner), and the layered **.psd** files for anything you'd rather composite by hand.

---

## 1. Fonts (add once)

Melodia uses 4 free Google Fonts. Two are built into Wix's font list; add the others as **Custom site fonts** if you want them on native Wix text (the HTML embeds load all four on their own, so this step is only for normal Wix text elements).

| Role | Font | In Wix? |
|---|---|---|
| Display / titles | **Fraunces** | Built in (search "Fraunces") |
| Body / UI | **Inter** | Built in |
| Technical / metadata | **IBM Plex Mono** | Built in (search "Plex Mono") |
| Wordmark (optional) | **Cinzel** | Add as custom font if desired |

**Set the Text Theme** (Editor → *Site Design / Text*):
- Headings → Fraunces (Display XL ~64–80px, H1 ~40–56px, H2 ~28–32px)
- Paragraphs → Inter (Body 16–18px)
- Use IBM Plex Mono for spec labels / captions (letter-spacing ~0.12–0.24em, UPPERCASE).

---

## 2. Color palette (paste into Wix "Site Colors" → custom)

**Astral Night (dark sections)**
| Token | Hex |
|---|---|
| Surface / base | `#141A30` |
| Surface / raised | `#1C2340` |
| Accent / astral blue | `#3C5C9E` |
| Accent / iris | `#6E5AA6` |
| Gold (rules / mark) | `#C9A86A` |
| Gold soft | `#DDC79B` |
| Text / primary | `#ECEAF4` |
| Text / secondary | `#A9A7C0` |

**Ivory Editorial (light sections)**
| Token | Hex |
|---|---|
| Surface / base | `#F7F4EF` |
| Surface / lift | `#FCFBF8` |
| Text / primary (plum) | `#241B2E` |
| Text / secondary | `#6E6080` |
| Gold | `#B08D4F` |
| Lavender accent | `#9F94C6` |
| Sakura accent | `#D6A9B0` |

> Keep pink strictly as a tiny accent (rules, tags) — never a fill.

---

## 3. The HTML embeds (the good part)

Two self-contained files in `wix/`:

- **`melodia-passport-embed.html`** — the signature Asset Passport (dark or light).
- **`melodia-hero-embed.html`** — a full-width hero banner (Constellation / Nebula / Ivory themes).

**To add one:**
1. Wix Editor → **Add (+) → Embed Code → Embed HTML → "Enter Code"**.
2. Open the `.html` file in a text editor, copy **everything**, paste into the box.
3. Resize/position:
   - Passport: ~ **360 × 560** (dark) — drag to fit; it centers itself.
   - Hero: stretch **full-width**, height ~ **440–520px**. It's fluid (`clamp()` type) so it scales on mobile.

**Editing content — two ways:**
- **Inline:** edit the `DATA = { ... }` block near the top of each file (project name, stats, theme).
- **By URL (great for automation later):** the embeds read query params. Example for the passport:
  ```
  ?theme=dark&project=Ashen%20Cathedral&category=Environment&triangles=482,318&textures=4K&materials=12&software=Blender%20%C2%B7%20ZBrush&engine=Unreal%20Engine%205.4&date=2026-03&version=v1.2
  ```
  Hero supports `?theme=dark|nebula|ivory&title=...&kicker=...&sub=...`.
  This is the same field schema as the Figma Asset Passport and the `DESIGN-SYSTEM.md §9` automation JSON, so a future Blender→export step can feed both Figma and Wix from one data source.

> Note: Wix HTML embeds run in a sandboxed iframe. Fonts load from Google Fonts inside the iframe (already wired). If your section background is dark, use `theme=dark`; on ivory sections use `theme=light`/`theme=ivory`.

---

## 4. Using the .psd files

`psd/` contains layered Photoshop files (open in Photoshop or free Photopea.com):

| File | Layers |
|---|---|
| `Melodia-Hero-Constellation.psd` | Background · Atmosphere · Brand Mark · Headline · Asset Passport |
| `Melodia-Hero-Nebula.psd` | same |
| `Melodia-Cover-OrnateFrame.psd` | Background · Atmosphere · Brand Mark · Headline |
| `Melodia-Hero-IvoryEditorial.psd` | same as heroes |
| `Melodia-AssetPassport-Dark.psd` / `-Light.psd` | Asset Passport |

Each section is a separate raster layer, so you can recolor, mask, swap the headline, or export a flattened PNG/JPG to drop into Wix as a normal image (good for social posts and ArtStation covers). Text is high-res raster — tell me if you want **live editable text layers** instead and I'll regenerate.

---

## 5. Suggested page structure for fromageart.xyz
- **Home hero:** `melodia-hero-embed.html` (Constellation) full-width.
- **Project pages:** project image, then the `melodia-passport-embed.html` as the spec plate (recognizable across every project = your brand signature).
- **About / commissions:** Ivory sections (`theme=light`) for readability.
- Keep one hero treatment per page; don't stack sparkle effects.
