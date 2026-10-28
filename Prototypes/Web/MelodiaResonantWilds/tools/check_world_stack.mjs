// World-expansion source contract; headless browser performs actual runtime tests.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const read = p => readFileSync(join(root, p), 'utf8');
const g = read('js/game.js'), world = read('js/world.js'), a = read('js/activities.js');
const design = read('js/design.js'), sw = read('sw.js'), smoke = read('tools/browser_smoke.mjs');
assert.match(g, /new PostFX\(this\)/);
assert.doesNotMatch(g, /this\.painterly/);
assert.match(g, /this\.postfx\.render\(\)/);
assert.match(world, /get\('worldexp'\) === '1'/);
assert.match(a, /get\('worldexp'\) === '1'/);
assert.match(design, /get\('dressing'\) === 'dense'/);
assert.match(a, /planExploration\(b, bi, rng, this\.pois\.slice\(\)\)/);
assert.match(smoke, /desktop-worldexp-postfx/);
assert.match(sw, /resonant-wilds-v11/);
for (const p of ['js/openworld.js','js/postfx.js','vendor/postprocessing/OutlinePass.js',
 'vendor/postprocessing/UnrealBloomPass.js','vendor/shaders/FXAAShader.js']) {
 assert.ok(existsSync(join(root,p)), p+' missing');
}
console.log('World expansion integration contracts: PASS');
