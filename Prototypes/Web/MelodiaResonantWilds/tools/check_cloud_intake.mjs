// Dependency-free cloud intake structural checks. Real WebGL/mobile QA remains required.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const file = (p) => readFileSync(join(root, p), 'utf8');
const exists = (p) => existsSync(join(root, p));
const js = ['js/player.js', 'js/chibi.js', 'js/activities.js',
  'js/cel.js', 'js/asset-loader.js', 'js/world.js',
  'vendor/examples/jsm/loaders/GLTFLoader.js',
  'vendor/examples/jsm/utils/BufferGeometryUtils.js'];
for (const p of js) assert.ok(exists(p), 'missing: ' + p);
assert.match(file('js/player.js'), /get\('avatar'\) === 'chibi'/);
assert.match(file('js/player.js'), /if \(m\.pose\)/);
assert.match(file('js/activities.js'), /get\('shrine'\) === 'glb'/);
assert.match(file('js/asset-loader.js'), /GLTFLoader/);
assert.match(file('js/asset-loader.js'), /procedural/);
assert.match(file('js/cel.js'), /MeshToonMaterial/);
assert.match(file('js/cel.js'), /nprV2/);
const tuner = file('js/npr-tuner.js');
assert.match(tuner, /attachShaderTuner/);
assert.match(tuner, /Soft cel/);
assert.match(tuner, /Copy this look/);
assert.match(file('js/cel.js'), /setNPRBands/);
assert.match(file('js/npr-tuner.js'), /Band hardness/);
assert.match(file('js/npr-tuner.js'), /Shadow darkness/);
assert.match(file('js/asset-loader.js'), /melodiaInk/);
const model = readFileSync(join(root, 'assets/models/resonance-shrine.glb'));
assert.equal(model.subarray(0, 4).toString('ascii'), 'glTF');
assert.equal(model.readUInt32LE(4), 2);
assert.equal(model.readUInt32LE(8), model.byteLength);
assert.ok(model.byteLength < 1024 * 1024, 'P0 GLB must fit 1 MiB');
const manifest = JSON.parse(file('manifest.json'));
for (const icon of manifest.icons) assert.ok(exists(icon.src), 'missing PWA icon ' + icon.src);
const sw = file('sw.js');
assert.match(sw, /resonant-wilds-v7/);
assert.ok(!exists('js/painterly.js'), 'retired Kuwahara shader must be deleted');
assert.doesNotMatch(file('js/game.js'), /painterly|PainterlyFilter|WebGLRenderTarget/);
assert.doesNotMatch(tuner, /game\.painterly|PainterlyFilter|uAnisotropy|uEdgeProtect|key: 'strength'|key: 'radius'|key: 'anisotropy'|key: 'scale'/);
assert.doesNotMatch(sw, /painterly/);
for (const path of sw.matchAll(/'\.\/([^']+)'/g)) {
  const p = path[1];
  if (p) assert.ok(exists(p), 'missing offline dependency ' + p);
}
console.log('Cloud asset intake contracts: PASS');
