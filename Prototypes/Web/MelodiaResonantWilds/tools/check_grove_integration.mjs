// Zero-dependency source contract; browser CI validates exact GLB loader runtime.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const read = path => readFileSync(join(root,path),'utf8');
const module = read('js/grove.js'), game=read('js/game.js'),
  sw=read('sw.js'), browser=read('tools/browser_smoke.mjs');
for (const token of ['ASSET_FLR_bellflower_dwarf','ASSET_FLR_moonfern_young',
 'ASSET_FLR_short_grass','mergeGeometries','installGroveProps',
 'tint: -1','!world.flowerbedsEnabled']) assert.ok(module.includes(token), token);
assert.ok(game.includes('await installGroveProps(this.world)'));
assert.ok(game.includes("this.world.groveStatus = 'fallback'"));
assert.ok(sw.includes('resonant-wilds-v9'));
assert.ok(sw.includes('./js/grove.js'));
assert.ok(sw.includes('./assets/models/harmonic-grove-37.glb'));
for (const state of ['desktop-grove-glb','mobile-grove-dense',
 'desktop-grove-fallback','desktop-npr-colour-review']) assert.ok(browser.includes(state));
console.log('Harmonic Grove optional runtime intake contract: PASS');
