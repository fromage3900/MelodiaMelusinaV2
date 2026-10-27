# Resonant Wilds | Cloud Asset Replacement Ledger

**Authoritative gameplay:** `fromage3900/MelodiaMelusinaV2/Prototypes/Web/MelodiaResonantWilds/`.
**Published web mirror:** `fromage3900/my-site/resonant-wilds/`.
**Rule:** maintain gameplay saves, collision/POI rules, and rhythm clock; replace presentation only.
**Branch status:** experiment, not yet merged or browser approved.

## Procedural artwork inventory

| Source | Procedural asset | Preferred replacement | Status |
| --- | --- | --- | --- |
| `js/activities.js:buildMesh` | Music-Key Shrine (four stelae + knot) | `assets/models/resonance-shrine.glb` | **staged; opt-in `?shrine=glb`; fallback retained** |
| `js/player.js` + `js/entities.js` | Melusina primitive character | recovered `js/chibi.js` (temporary) / later authored GLB | **staged; opt-in `?avatar=chibi`** |
| `js/entities.js` | Choral Sheep | low-poly sheep GLB with existing runtime object as fallback | not created |
| `js/entities.js` | Melody Slime + bosses | authored variant GLBs with existing collider/gameplay | not created |
| `js/world.js:_buildPropLibrary` | `sakura` | stylized instanced tree | not created |
| `js/world.js:_buildPropLibrary` | `flower` | flower/grass tufts, shared mesh | not created |
| `js/world.js:_buildPropLibrary` | `rock` | bevelled stone variants | not created |
| `js/world.js:_buildPropLibrary` | `lantern` | enamel-and-gold lantern | not created |
| `js/world.js:_buildPropLibrary` | `bell` | animated musical bellflowers | not created |
| `js/world.js:_buildPropLibrary` | `note` | luminous musical sculpture | not created |
| `js/world.js:_buildPropLibrary` | `pillar` | cathedral column variants | not created |
| `js/world.js:_buildPropLibrary` | `reed` | water reed clump | not created |
| `js/world.js:_buildPropLibrary` | `lily` | water lily | not created |
| `js/world.js:_buildPropLibrary` | `stalagmite` | cave formations | not created |
| `js/world.js:_buildPropLibrary` | `mushroom` | glowing mushroom | not created |
| `js/world.js:_buildPropLibrary` | `crystal` | coloured crystals | not created |
| `js/world.js:_buildPropLibrary` | `spire` | landmark crystal spire | not created |
| `js/world.js:_buildPropLibrary` | `pine` | aurora pine | not created |
| `js/world.js:_buildPropLibrary` | `icespike` | icicle/ice spike | not created |
| `js/activities.js:buildMesh` | pylon, chest, lost sheet, Rift gate, boss altar | individual GLBs, each with source fallback | not created |
| `js/world.js:_buildHub/_buildLandmarks` | houses, obelisk, scenic setpieces | curated GLB kits, maintain occlusion behaviour | not created |

Terrain chunks and water are **shader/geometry systems**, not first-order GLB replacement candidates.
The 14 `world.props` families use `InstancedMesh`. Future imported foliage should be baked into compatible shared geometry/material components and instanced per chunk, not loaded or duplicated per plant.

## Model intake P0

- Source: Higgsfield 3D Jutsu, `Resonant Wilds — Resonance Shrine GLB P0`, revision 1.
- Game GLB: 15 meshes, 5 materials, approx. 2,396 triangles, 165,224 bytes.
- Y-up via glTF export, ground contact at y=0, bounding box 1.34 x 1.34 x 2.26 metres.
- Model exported with authoring camera/lights stripped (scene root only).
- Official `three.js r170` `GLTFLoader.js` and `BufferGeometryUtils.js` vendored under `vendor/examples/jsm/`; reuse existing Three.js MIT licence.
- `js/asset-loader.js` preserves authored colours/maps/emissive and applies shared cel material.
- No runtime lighting, audio, collision or save change. Loading is opt-in, cached by one promise, cloned into POIs; procedural visuals are retained on failure.
- Visual comparison: `?shrine=glb`, `?avatar=chibi`, and both simultaneously; leave URL clean for the original.
- The chibi is code-built, not a GLB. It comes from the earlier isolated `claude/open-world-three-js-game-icm254` branch; the original procedural Melusina remains default.

## Required before merge

1. Run `node --check` for changed files and `node tools/check_cloud_intake.mjs`.
2. Desktop WebGL compilation with shader flags; verify every POI group keeps its fallback.
3. Test `?shrine=glb&avatar=chibi` with movement, attack, dodge, wardrobe, rift travel and shrine dialogue.
4. Check Safari touch and 40+ fps target relative to original, especially chibi draw calls.
5. Check offline PWA: install, first visit, update from cache v1, and page reload with query parameters; icons and dynamic imports resolve.
6. Confirm the published site's GH Pages deploy and service-worker update **only after merge**. Never assume CI replaces browser QA.
7. Review the old Daily Rift, leaderboard and UE music-export branch separately; backend server is not suitable for static GH Pages without a maintained host.
