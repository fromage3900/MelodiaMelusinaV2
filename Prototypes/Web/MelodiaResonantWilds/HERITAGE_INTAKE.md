# Resonant Wilds — Website Heritage Intake P0

Source: `fromage3900/my-site` `main` (Oct 28, 2026), from `tools/fromage-webgl-kit`. This is **our own existing site art and JavaScript** reused in the browser game's stacked experimental draft. No paid assets, external npm dependencies, separate WebGL contexts or narrative-scope changes.

## Imported, SHA-identical

| Original website asset / utility | Browser game destination | Use |
|---|---|---|
| `accessory-viewer/resonance/chromatic-orbit.svg` | `assets/heritage/chromatic-orbit.svg` | title-screen celestial orbit |
| `accessory-viewer/resonance/note-medallion.svg` | `assets/heritage/note-medallion.svg` | central title musical emblem |
| `accessory-viewer/resonance/filigree-frame.svg` | `assets/heritage/filigree-frame.svg` | Music-Key Shrine card |
| `accessory-viewer/resonance/resonance-core.svg` | `assets/heritage/resonance-core.svg` | shrine motif layered with filigree |
| `src/animation/createDeterministicTimeline.js` | `js/heritage-timeline.js` | subtle 3D yaw/lift of existing imported shrine GLB |

The visuals are referenced as plain `img` files from the **existing HUD**, not rasterized with an additional Three.js renderer. Hidden shrine artwork is decorative and never intercepts input. The title orbit uses CSS animation; `prefers-reduced-motion: reduce` freezes it. Short-viewport styling preserves the Play button and shrine tap controls.

The timeline helper is pure math; the game samples it inside `Activities.update(dt)` using the existing game clock. It animates only the optional GLB shrine root and does not touch its POI collider, save profile, rhythm call-and-response rules, or procedural shrine fallback. Motion also disables for reduced-motion settings.

## Existing website systems audited — do not transplant wholesale

- `src/core/createRuntime.js`: redundant renderer, second canvas, RAF and resize lifecycle. Resonant Wilds already owns these.
- `src/assets/createGLBLoader.js`: redundant wrapper because the game already uses the matching pinned Three.js r170 `GLTFLoader` and a cached shrine template.
- `src/audio/createAudioReactiveBus.js`: would add another audio context and analyser; **do not disturb** the game's single authoritative rhythm clock.
- `src/game/createStateMachine.js`: useful later if we build a *new* branching quest module, but this P0 retains `Progress.objective()`, tutorial hints, and the existing shrine state transitions.
- `wix/melodia-mahou-flourish.js` / `components/melodia-star-system.js`: broad DOM pointer and animation effects; defer. They would compete with touch gameplay and reduced-motion settings.

## Tests / release contract

- Four original SVGs are served, loadable, and included in the PWA offline cache.
- Deterministic timeline exists, samples zero-crossing at t=2 seconds, and never starts its own RAF.
- Existing 8-mode browser smoke covers legacy, NPR V2, mobile, chibi, optional GLB, retired Kuwahara links, and live shader tuning.
- No new WebGL renderer, package, shader filter or audio engine.
- Both branches remain **draft and unmerged** pending visual / mobile Safari QA.
- Production rollout order still depends on the site foundation PR #83, NPR V2 #84 and their original merge gates; this is a stacked, non-blocking visual PR.

## Follow-on work (not implemented in this pass)

A short first-play capture (spawn → established objective → Choral Sheep → shrine) will determine if a bespoke tutorial flourish or cinematography is warranted. Avoid changing the canonical JRPG narrative or music systems based solely on this browser-site test.
