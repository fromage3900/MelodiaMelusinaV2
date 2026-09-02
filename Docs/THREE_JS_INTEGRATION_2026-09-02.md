# Melodia Three.js Integration

**Date:** 2026-09-02  
**Repo:** `fromage3900/my-site`  
**Branch:** `cursor/threejs-integration-d313`

## What shipped

1. **Shared core** (`wix/melodia-three-core.js`) — one CDN load path for Three.js r128, OrbitControls, OBJ/GLTF/FBX loaders; capability + reduced-motion gates.
2. **WebGL starfield** — additive Points shader sky when `data-effects` includes `three` (supersedes 2D `#ambient-starfield`).
3. **World constellation** — interactive orbit map of 4 levels + Cosmic Orrery pillar on the homepage (`#three-constellation`).
4. **WebGL orrery** — drag-tilt armillary on Cosmic Orrery + Application Hub (`[data-three-orrery]`).
5. **Hub restore** — `melodia-planetarium.js` + mini mount wired (was declared in `data-effects` but never loaded).
6. **Nav** — Realtime 3D Studio link in shared `melodia-site-nav.js`.
7. **Asset viewer** — `melodia-3d-viewport.js` prefers `MelodiaThreeCore` (legacy CDN chain kept as fallback).

## Authoring

```html
<div class="melodia-shell" data-effects="starfield,three,holo,magical">
  <div id="three-constellation-mount" data-three-constellation></div>
  <div data-three-orrery data-orrery-size="1"></div>
</div>
```

Include scripts: `melodia-three-core.js` → starfield / orrery / constellation → `melodia-editorial.js`.

## A11y

`prefers-reduced-motion: reduce` hides Three canvases (CSS) and `MelodiaThreeCore.canBoot()` refuses to mount.
