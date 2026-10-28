# Resonant Wilds — Shader Lab P0

**Scope:** WebGL / Three.js r170 browser prototype only. Unreal remains authoritative for the game. No Three.js upgrade, postprocessing chain, new assets, combat or data changes.

## Shipped in this experiment

- **Cel-shading baseline**: one shared three-tone, nearest-filtered gradient is used by Melusina, Choral Sheep, slimes, terrain, instanced props, plaza, landmarks, and Rift geometry. `js/cel.js` is the material helper.
- **Chladni**: a bounded nodal-line glow near Melusina, whose response scales with the existing Crescendo level. This extends the existing `World._resonate()` injection and does not touch the rhythm clock.
- **Caustics**: low-cost interference highlights on the water surface and gently animated illumination near the waterline of terrain. Disable ground caustics in the Rift; retain existing wave displacement and beat ripple uniforms.

## A/B comparisons

Open a local dev server from the repo root with `python -m http.server 8080`, visit `/Prototypes/Web/MelodiaResonantWilds/` and compare:

- No query string — all effects enabled.
- `?chladni=0` — cel + caustics, but no Chladni.
- `?caustics=0` — cel + Chladni, but no caustics.
- `?chladni=0&caustics=0` — cel baseline only.
- `?render=legacy` — original Lambert terrain/props and the original character gradient; no Chladni or caustics. The original beat-ripple shader remains operational.

## Cloud preview

This is a public, **temporary** preview of the branch; it isn't a GitHub Pages release. GitHack is an independent GitHub-source proxy, not an OpenAI or GitHub service.

`https://raw.githack.com/fromage3900/my-site/feat/resonant-wilds-cloud-intake-20261027/resonant-wilds/index.html`

Try `?avatar=chibi&shrine=glb` or `?render=legacy` at the end. A separate GitHub Actions Chromium smoke checks all four combinations. Do not merge before manual desktop and iPhone Safari gameplay QA.

In devtools the existing `window.__melodia.world.uniforms` offers live sliders via `uChladni.value` and `uCaustics.value` (nominal range 0–1). Set either to 0 without recompiling a program. Keep the actual rhythm clock as the source of beat events.

## Acceptance before publishing

1. `node --check` for `js/world.js`, `js/entities.js`, and `js/cel.js`, plus optional `node tools/check_shader_lab.mjs`.
2. Desktop Chrome: no shader compile errors; world, water, characters, and Rift visible; movement, strikes, loot, saves still work.
3. iPhone Safari: reliable first-tap Web Audio unlock and touch movement; visually compare all query combinations in landscape.
4. Observe frame pacing in Shorewake and Liquid Cathedral while moving; keep existing automatic render resolution and avoid new postprocessing.
5. Check near-shore caustics and Chladni overlap; avoid washed-out colors. Confirm the Rift has no water caustics.
6. If the mobile FPS degrades materially, reduce `uCaustics`, then `uChladni`, instead of changing render-pipeline authority.

## GLB follow-up

Use this shared `celMaterial()` for new simple Tripo meshes initially. For GLTFLoader-imported textured meshes, do not discard texture/alpha maps blindly. The first GLB should be a non-authoritative visual child of the existing companion/prop transform, with the current procedural mesh retained as fallback.
