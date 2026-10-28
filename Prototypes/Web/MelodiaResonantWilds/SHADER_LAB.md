# Resonant Wilds — Shader Lab P0

**Scope:** WebGL / Three.js r170 browser prototype only. Unreal remains authoritative for the game. No Three.js upgrade, postprocessing chain, new assets, combat or data changes.

## Shipped in this experiment

- **Cel-shading baseline**: one shared three-tone, nearest-filtered gradient is used by Melusina, Choral Sheep, slimes, terrain, instanced props, plaza, landmarks, and Rift geometry. `js/cel.js` is the material helper.
- **Chladni (real plate modes)**: bounded nodal-line glow near Melusina uses the rectangular plate field
  `cos(nπx)cos(mπy) − cos(mπx)cos(nπy)`, driven by live uniforms `uModeN` / `uModeM` / `uPhase` / `uSharpness`.
  Default mode is Faraway canon **(3,5)**. Response still scales with Crescendo; ceremony flashes add a short `uCeremony` bloom.
  Extends `World._resonate()` and does not touch the rhythm clock.
- **Chladni Burst sync**: `Web_Cymatic_ChladniBurst` samples the same field for nodal particles; **Perfect** hops the mode ladder and sparks antinode gold.
- **Shore / water lace**: terrain caustics and near-player water caustics brighten on antinodes and dim on nodal lines (still gated by `uCaustics` / `uIsRift`).
- **Caustics**: low-cost interference highlights on the water surface and gently animated illumination near the waterline of terrain. Disable ground caustics in the Rift; retain existing wave displacement and beat ripple uniforms.

## A/B comparisons

Open a local dev server from the repo root with `python -m http.server 8080`, visit `/Prototypes/Web/MelodiaResonantWilds/` and compare:

- No query string — all effects enabled, mode (3,5).
- `?mode=2,3` / `?mode=5,7` — pin a plate mode (comma, `x`, or `/` separators).
- `?chladni=0` — cel + caustics, but no Chladni.
- `?caustics=0` — cel + Chladni, but no caustics.
- `?chladni=0&caustics=0` — cel baseline only.
- `?render=legacy` — original Lambert terrain/props and the original character gradient; no Chladni or caustics. The original beat-ripple shader remains operational.

## Publish / preview

**Canonical public mirror (owner publish):** `https://fromage3900.github.io/my-site/resonant-wilds/` after syncing this folder into `fromage3900/my-site/resonant-wilds/` and confirming the SW cache (`resonant-wilds-v10-*`) activates.

Temporary raw.githack previews are retired for release claims — use the GH Pages mirror or a local `python -m http.server` from the repo root. Try `?avatar=chibi&shrine=glb` or `?render=legacy` at the end. GitHub Actions Chromium smoke checks structural boot; desktop and iPhone Safari gameplay QA remain required before calling the mirror browser-approved.

In devtools `window.__melodia.world.uniforms` offers live sliders:

| Uniform | Range | Notes |
|---------|-------|-------|
| `uChladni` | 0–1 | Master nodal intensity |
| `uCaustics` | 0–1 | Shore + water caustics |
| `uModeN` / `uModeM` | ≥1 | Plate indices (or `world.setMode(n,m)` / `world.hopMode(true)`) |
| `uSharpness` | 0–1.5 | Nodal line thinness |
| `uCeremony` | 0–1 | Transient Recital bloom (driven by `ceremonyFigure`) |
| `uPhase` | free | Beat-driven in `frame()` |

Keep the actual rhythm clock as the source of beat events.

## Acceptance before publishing

1. `node --check` for `js/world.js`, `js/entities.js`, `js/cel.js`, `js/combat.js`, `js/ui.js`, plus `node tools/check_shader_lab.mjs`.
2. Desktop Chrome: no shader compile errors; world, water, characters, and Rift visible; movement, strikes, loot, saves still work.
3. Cast **Chladni Burst** on Perfect and confirm the floor figure changes mode; Recital inherit/miss flashes should bloom nodal particles.
4. iPhone Safari: reliable first-tap Web Audio unlock and touch movement; visually compare all query combinations in landscape.
5. Observe frame pacing in Shorewake and Liquid Cathedral while moving; keep existing automatic render resolution and avoid new postprocessing.
6. Check near-shore caustics and Chladni overlap; avoid washed-out colors. Confirm the Rift has no water caustics.
7. If the mobile FPS degrades materially, reduce `uCaustics`, then `uChladni`, instead of changing render-pipeline authority.

## GLB follow-up

Use this shared `celMaterial()` for new simple Tripo meshes initially. For GLTFLoader-imported textured meshes, do not discard texture/alpha maps blindly. The first GLB should be a non-authoritative visual child of the existing companion/prop transform, with the current procedural mesh retained as fallback.
