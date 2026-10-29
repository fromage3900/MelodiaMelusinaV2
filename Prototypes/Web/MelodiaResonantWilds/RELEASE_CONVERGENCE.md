# Resonant Wilds — single-source integration candidate (2026-10-28)

## Source of truth and fixed baseline
- Canonical authoring repo: `fromage3900/MelodiaMelusinaV2`
- Build path: `Prototypes/Web/MelodiaResonantWilds/`
- Branch base: `d5ab2abb247f5748309e63a908bc00be95535884` (contains Recital, Encore, Sheep concert, expanded world, Mixamo, heritage SVGs)
- Website source for 100 authored GLBs and hard RGB-band preview: `fromage3900/my-site` commit `8f200e1b78a10814287f5d7e4f232edd98e3718f`
- Asset SHA manifest: `ASSET_RELEASE_MANIFEST.json` (63 standalone GLBs; shared 37-part bundle already in both repos)

## Feature boundaries
1. No substitutions of `game.js`, `world.js`, `activities.js`, `audio.js`, `design.js`, `progress.js` or `ui.js` from the *older* website version; they contain newer canonical gameplay.
2. `?grove=glb` continues to use the same three verified instanced families. `?grove=full` opt-in adds a 100-name catalog and at most two intentionally decorative variants per supported world prop type. Variant choice uses a pure coordinate/biome hash, never consumes placement RNG or changes entity interaction, collisions, save IDs or spawn locations.
3. All 63 extra GLBs are retained by SHA and are loadable by name via `loadGroveVisual(name)`. `INT_` and `PICK_` assets are **not scattered**; gameplay logic controls any later POI usage. The release page does not preload all 63 or require their availability for procedural fallback.
4. Material ramps use the tested RGB gradient shader from the website preview. World Chladni/caustic shader hooks are composed rather than overwritten. The five-control cel tuner supports `hard`, `cut`, `dark`, `ink`, `shadow`. Old `kuwahara=1` links remain harmless; `painterly.js` and its GPU render target are removed.
5. Independent optional `?postfx=1` world bloom/outline remains available, not confused with the retired Kuwahara filter. Default P0 render stays direct, with dynamic quality scaling retained.
6. Existing website-made celestial SVGs are already in canonical main; no repeat copies or new renderer needed.

## Release steps / guards
- CI: static gates, 37-bundle GLB header gate, 63 optional GLB SHA manifest, full registry uniqueness, canonical legacy/NPR/Chladni checks, 19 WebGL scenarios, 5-control tuner persistence.
- Keep source release integration branch **draft** until browser tests and real iPhone Safari visuals, touch rhythm, audio start and offline load pass.
- Website release: start a fresh `my-site` branch from its latest `main`. Copy the exact canonical `resonant-wilds/` tree to it, replacing only game-owned paths, leaving Wix/portfolio unaffected. Preserve the 63 additional GLBs; verify model/HTML/JS hashes match. Deploy only after manual QA.
- Record both source/release SHAs. Keep previous website `main` for rollback. Retire stale stacked website PRs only after comparing their unique files against the canonical release manifest.
