# Resonant Wilds — Floraison Release Stage (October 29, 2026)

**Candidate branch:** `release/resonant-wilds-v15-floraison-20261029`  
**Status:** staging / validation only; **not merged to canonical main** and **not published** to `my-site`.

## Source ownership

- **Baseline:** current canonical `fromage3900/MelodiaMelusinaV2/main`, reviewed at `8e1bbabc552211fabc658a3e001d77c033e61461`.
- **Already merged gameplay:** #564 (cooler loops), #565 (PWA publish), #566 (heritage SVGs), #567 (Recital / fashion), #568 (ethereal destinations), #569 (SFX routing), #570 (Chladni VFX), #573 (safe overlay publisher), #574 (Chladni sand / Sheep charge / giant gown), #575 (Mist Float, Prism Veil, Nightbell Glide), #576 (smoke contracts), #577 (Nikki-by-default / region 100% / Dew ping).
- **Release-specific integration:** #579 reconverges the unique work of #571: 100-asset catalog (37 bundled plus 63 standalone GLBs), deterministic instanced Grove variants, hard RGB cel shading preserving the Chladni shader hook, removal of Kuwahara, opt-in Grove full, and fail-safe website overlay. Do **not** merge obsolete #571 separately or replace Nikki gameplay with the old website tree.
- **New art/POV:** #580 Floraison: low-poly bellflowers, rosettes, wildflowers, ferns and spires; three (2,3)/(3,5)/(4,7) gardens; optional ground-level first-person POV with keyboard/phone look and restored third-person fallback.

## Flags and default behavior

- Bare URL: Nikki worldexp/dense dressing/daycycle/postfx from current `flags.js`, hard-banded cel default from #579; Floraison **off** until visual approval.
- `?botany=1`: normal Floraison meadow + Chladni gardens.
- `?botany=dense`: denser meadow candidate; additional mobile cost.
- `?botany=1&pov=1`: start at flower-level first-person camera; **P** / **✿ Flower POV** toggles, drag to look, WASD/joystick camera-relative movement.
- `?grove=full&botany=1&pov=1`: combine optional Grove variants and flower POV; all remain cosmetic.
- `?lite=1`: Nikki lower-cost escape; existing flag owner retained. Add `&botany=0` for baseline.
- `?npr=v1` or `?render=legacy`: A/B controls for look verification; Kuwahara code remains retired.

## Offline/package strategy

- Candidate service worker: **`resonant-wilds-v15-20261029-floraison-release`**. This *advances* main's v14 while retaining its `flags.js` + `playground.js` cache coverage; adds `grove-catalog.js`, `floraison-pov.js`, `flower-landscape.js`, `resonant-botany.js`.
- Keep the 63 separate GLBs optional/streamed: do not precache all model binaries on phone. Retain the existing 37-root `harmonic-grove-37.glb` asset.
- `tools/sync_to_mysite.sh` remains overlay-by-default, preserves website-only Tripo/asset-gallery files, and avoids overwriting valid PNG icons with 129-byte Git LFS pointers. **Do not use `--delete`**.
- Existing `my-site` live mirror is older. Prior Cursor push returned **HTTP 403**; publishing requires an authorized site push after canonical approval. Do not claim live sync.

## Quality and approval gates

1. **Static and data** — Echo Static Gates and Cloud Intake zero-dependency checks, new Floraison controller tests, + `tools/check_release_staging.mjs`: checks 100 unique catalog names, 63 GLB byte lengths *and Git blob SHA*, Nikki outfit/region contracts and v15 precache.
2. **WebGL** — existing Cloud Intake headless Chrome scenarios, including standard exploration, Grove full, mode switching, postfx, saves and wardrobe. Add a manual `?botany=1&pov=1&grove=full` browser walkthrough; existing headless tests may not explicitly screenshot the new POV.
3. **Art** — desktop flower-height Sakura Terrace approach, Glass Orchard bellflower garden, Starlit Moor filigree, Chladni visibility, road/POI clearances, hero camera framing, clipping and draw calls.
4. **Mobile** — real iPhone Safari: movement / drag-to-look / camera return, dress unlock, Dew region 100%, Sheep and combat buttons, offline reload, memory, FPS and pointer capture.
5. **Publication** — compare exact canonical and website staged files, confirm icons are genuine PNGs and that original website-only assets remain. Authorized push to `my-site`; confirm Cache Storage v15 and real device smoke. Only then approve the updated live release.

**Not verified at authoring:** Safari manual QA, website deploy, icon runtime availability, and visual approval of the new meadow composition.
