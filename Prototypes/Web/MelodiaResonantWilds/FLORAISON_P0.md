# Floraison — playable flower landscape P0 (experimental)

**Branch:** `experiment/resonant-botany-chladni-p0-20261029`  
**Scope:** visual-only art experiment for the canonical Resonant Wilds world. No publishing or production merge.

## How to preview

Serve `Prototypes/Web/MelodiaResonantWilds/` through the game's normal HTTP server and visit:
- `?botany=1`: layered meadows + three Chladni figure gardens.
- `?botany=dense`: fuller meadows; higher phone/GPU cost.
- `?botany=0` or bare URL: current production scenery unchanged.
- `?botany=1&pov=1&npr=v2`: **first-person Flower POV shot** with the painterly hard-banded foliage look. This enters POV at the current save/spawn point; walk from Shorewake out along the Sakura Terrace road to see the dense meadow and (2,3) garden. No teleport or save change.
- With `?botany=1` or `?botany=dense`, press **P** or tap **✿ Flower POV** by the map to switch between first-person and the regular third-person camera. While in POV, drag on the uncovered game canvas to look around; **WASD / mobile joystick** move relative to view. Press P or tap **Exit POV** to restore the usual lens.
- POV uses a **1.48 m eye-height lens**, slightly downward framing, a close near-plane and gentle walking sway. The player mesh/shadow are hidden only in POV; the companion, gameplay, saves and combat state are unchanged. On entering the Rift or player death, it exits automatically. Attack taps on the canvas become look gestures in POV; action buttons and keyboard combat remain available.
- Combine `?botany=1&flowerbeds=1&npr=v2` for pastel flowerbeds and the hard-banded NPR look.
- `?botany=1&grove=glb` keeps authored Harmonic Grove GLBs for existing props while adding the floral overlay.

## Look direction

**Floraison** uses five low-poly, vertex-coloured procedural families: lavender/pearl Bellflower Choir, blush Wildflower Carpets, jade Pearl Ferns, circular Rosette Beds and tall cyan/lavender Spires. Plant silhouettes are small clustered shapes, not single spike cones. All geometry uses the existing stylized toon material and InstancedMesh chunk streamer.

Meadow clumps are deterministic in world space and concentrated into irregular bands; POI circles, hub structures, radial roads, water and steep slopes are excluded. Three hand-composed gardens use the existing Chladni nodal sampler:
- Sakura Terrace / 2,3 / rosettes, near the village route.
- Glass Orchard / 3,5 / bellflower lattice.
- Starlit Moor / 4,7 / intricate rosette filigree.

The garden mode labels describe **static authored planting patterns**, not live mesh deformation. A beat-reactive bloom pass is a separate, unimplemented follow-up.

## Budgets and ownership

- Normal: at most 150 meadow placement attempts per streamed 64 m chunk, dense: 260. Only valid samples instantiate. Gardens have at most 170 candidates per pattern, partitioned by chunk.
- Five shared geometry/material resources; one draw call per **populated family per chunk** (up to five), no mesh-per-flower.
- The existing `world._buildProps` and gameplay RNG stream are untouched.
- Chunk disposal uses the current `_disposeChunk` path to dispose instance buffers. Shared kit resources remain alive for later chunks.
- No GLB/LFS downloads, save changes, collision changes, NPC placement changes, service-worker changes, or website publication.

## Verification gates

1. `node tools/check_resonant_botany.mjs`
2. `node tools/check_flower_landscape.mjs`
3. `node --check js/flower-landscape.js && node --check js/world.js`
4. Desktop Chrome WebGL smoke: spawn, leave hub toward Sakura Terrace, inspect flower coverage and garden legibility, roam into Glass Orchard; compare `?botany=0`.
5. iPhone Safari: capture FPS, WebGL draw calls, renderer.info.memory, page visibility/reload, camera occlusion and traversal.
6. Rebase against canonical release after #575, #577 and #571 are reconciled. No live deployment until gates pass.

**Status:** committed implementation, not browser-tested or visually approved.
