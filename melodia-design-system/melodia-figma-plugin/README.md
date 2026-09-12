# Melodia Design System Builder — Figma plugin

One click → builds the foundations of the Melodia design system directly in a Figma file:

- **Pages:** `00 Cover`, `01 Foundations`, `02 Tokens`, `03 Components`, `04 Patterns`, `05 Layouts`, `06 Templates`, `07 Archive`
- **Variables:** `Primitives` (raw palette incl. **astral** + **iris**), `Semantic` (modes **Light** = Ivory editorial + **Dark** = Astral Night, aliased to primitives), `Spacing`, `Radius`
- **Text styles:** the full type hierarchy (Display/XL → Metadata)
- **Effect styles:** `shadow/sm`, `shadow/md`, and HoYoverse-style `glow/gold`, `glow/astral`
- **Core components** on `03 Components`: `Star/8pt` (signature astral burst w/ glow), `Star/4pt`, `Star/Constellation` (star-chart backplate), `Frame/Corner` (ornate gold brackets, corner-pinned), `Brand/Mark` (✸ + Cinzel wordmark), `Divider/Section`, `Row/Spec`, `Tag/Technical`, `Tag/Software`, `Card/Info`, and the signature **`Brand/AssetPassport`** variant set (`Format = Card / Banner / Compact`, with automation-ready text properties).
- **Hero templates** on `06 Templates` (1440×900, using the components above): **Constellation** (Astral Night), **Nebula** (iris-forward bloom), **Ornate Frame** cover, and **Ivory Editorial + sparkle** (light). The three dark templates use an explicit Dark/Astral Night variable mode so the Passport + tokens recolor automatically.

This automates **steps 1–9 + a starter set of step-12 templates** of the implementation order in `DESIGN-SYSTEM.md §10`. Continue manually for the remaining layouts/templates + responsive variants.

---

## Run it

1. Install the fonts first for exact styles (optional but recommended): **Fraunces**, **Inter**, **IBM Plex Mono**, and **Cinzel** (wordmark) — all free on Google Fonts. If a font is missing the plugin falls back to Inter/Roboto and tells you — install + re-run for pixel-perfect type.
2. Open **Figma desktop app** → open or create a design file.
3. Menu → **Plugins → Development → Import plugin from manifest…**
4. Select `melodia-figma-plugin/manifest.json`.
5. Menu → **Plugins → Development → Melodia Design System Builder**. It runs, builds everything, and closes with a summary (see the dev console: **Plugins → Development → Open console**).

> Re-running is safe for pages (it won't duplicate them) but will create additional copies of variables/styles/components. Run once on a fresh file, or clean up before re-running.

---

## Two ways to get the tokens in

- **This plugin** (recommended for a turnkey file): creates variables *and* components.
- **`../tokens.json` via the free Tokens Studio plugin** (recommended if you maintain tokens in Git): in Tokens Studio, paste/load `tokens.json`, then "Create/Update Variables." Sets map to: `primitives` → Primitives collection, `semantic-light`/`semantic-dark` → Semantic collection modes (via the `$themes` Light/Dark), `global` → Spacing/Radius/typography.

Use whichever fits your workflow; they describe the same system.

---

## Automation: populating projects from data

The signature `Brand/AssetPassport` (and `Card/Info`, `Tag/Technical`) expose **component properties whose names match the data schema** in `DESIGN-SYSTEM.md §9.1`. A second plugin/script can fill any project in seconds. Minimal example (`populate.js`), run as a plugin against a selected passport instance:

```js
// Example data — produced by a Blender export / Python / MCP step
const data = {
  projectName: "Ashen Cathedral",
  category: "ENVIRONMENT",
  triangles: 482318,
  textureResolution: "4K",
  materials: 12,
  software: ["Blender", "ZBrush", "Houdini"],
  engine: "Unreal Engine 5.4",
  date: "2026-03",
  version: "1.2",
};

const fmt = n => typeof n === "number" ? n.toLocaleString("en-US") : String(n);

function fillPassport(instance, d) {
  instance.setProperties({
    projectName: d.projectName,
    category: String(d.category).toUpperCase(),
    triangles: fmt(d.triangles),
    textureResolution: d.textureResolution,
    materials: String(d.materials),
    software: d.software.join(" · "),
    engine: d.engine,
    date: d.date,
    version: "v" + d.version,
  });
}

for (const node of figma.currentPage.selection) {
  if (node.type === "INSTANCE") fillPassport(node, data);
}
figma.closePlugin("Passport populated.");
```

**Pipeline:** Blender Python writes `project.melodia.json` (scene stats) → an MCP tool / CI step reads it → a Figma plugin (like above) calls `instance.setProperties(...)`. Because property names are stable and match the schema, the same JSON drives every surface (passport, cards, tags). See `DESIGN-SYSTEM.md §9`.

---

## Notes / limitations

- Requires a recent Figma (Variables API). The plugin is version-tolerant: if variable→fill binding or component properties aren't supported, it falls back to resolved colors / static text and logs which feature was skipped.
- It builds the **core** component set as a high-quality starting point — not all 16 components or all 10 templates. Extend on pages `03`–`06` following the spec.
- `networkAccess` is `none`; the plugin makes no network calls.
