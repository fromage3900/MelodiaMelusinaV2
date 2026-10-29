// Dependency-free cloud intake structural checks. Real WebGL/mobile QA remains required.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const file = (p) => readFileSync(join(root, p), 'utf8');
const exists = (p) => existsSync(join(root, p));
const js = ['js/player.js', 'js/chibi.js', 'js/mixamo.js', 'js/activities.js',
  'js/cel.js', 'js/asset-loader.js', 'js/world.js', 'js/heritage-timeline.js',
  'vendor/examples/jsm/loaders/GLTFLoader.js',
  'vendor/examples/jsm/utils/BufferGeometryUtils.js'];
for (const p of js) assert.ok(exists(p), 'missing: ' + p);
assert.match(file('js/player.js'), /get\('avatar'\)/);
assert.match(file('js/player.js'), /avatar === 'chibi'/);
assert.match(file('js/player.js'), /mixamoOptIn/);
assert.match(file('js/player.js'), /if \(m\.pose\)/);
assert.match(file('js/activities.js'), /get\('shrine'\) === 'glb'/);
assert.match(file('js/asset-loader.js'), /GLTFLoader/);
assert.match(file('js/asset-loader.js'), /procedural/);
for (const name of ['chromatic-orbit', 'note-medallion', 'filigree-frame', 'resonance-core']) {
  const svg = file('assets/heritage/' + name + '.svg');
  assert.match(svg, /<svg\s/);
  assert.match(svg, /viewBox=/);
}
assert.match(file('index.html'), /title-sigil-orbit/);
assert.match(file('index.html'), /shrine-crest/);
assert.match(file('js/activities.js'), /createDeterministicTimeline/);
assert.match(file('js/cel.js'), /MeshToonMaterial/);
assert.match(file('js/cel.js'), /nprV2/);
assert.ok(!exists('js/painterly.js'), 'Kuwahara implementation is retired');
assert.doesNotMatch(file('js/game.js'), /PainterlyFilter|this\.painterly/);
assert.match(file('js/cel.js'), /RGB_BANDS_GLSL/);
assert.match(file('js/world.js'), /previousShaderHook/);
const catalog = await import('../js/grove-catalog.js');
assert.equal(catalog.GROVE_ALL_NAMES.length, 100);
assert.equal(new Set(catalog.GROVE_ALL_NAMES).size, 100);
assert.equal(catalog.GROVE_INTERACTIVE.length, 13);
const inventory = JSON.parse(file('ASSET_RELEASE_MANIFEST.json'));
assert.equal(inventory.optionalModels.length, 63);
for (const asset of inventory.optionalModels) {
  assert.ok(exists('assets/models/' + asset.filename), asset.filename + ' missing');
}
assert.match(file('js/grove.js'), /loadGroveVisual/);
const tuner = file('js/npr-tuner.js');
assert.match(tuner, /attachShaderTuner/);
assert.match(tuner, /Soft cel/);
assert.match(tuner, /Copy this look/);
assert.match(file('js/asset-loader.js'), /melodiaInk/);
const model = readFileSync(join(root, 'assets/models/resonance-shrine.glb'));
assert.equal(model.subarray(0, 4).toString('ascii'), 'glTF');
assert.equal(model.readUInt32LE(4), 2);
assert.equal(model.readUInt32LE(8), model.byteLength);
assert.ok(model.byteLength < 1024 * 1024, 'P0 GLB must fit 1 MiB');
const manifest = JSON.parse(file('manifest.json'));
for (const icon of manifest.icons) assert.ok(exists(icon.src), 'missing PWA icon ' + icon.src);
const sw = file('sw.js');
assert.match(sw, /resonant-wilds-v15-20261029-floraison-release/);
assert.match(sw, /js\/playground\.js/);
assert.match(sw, /js\/flags\.js/);
assert.match(sw, /js\/grove-catalog\.js/);
assert.match(sw, /js\/mixamo\.js/);
assert.match(sw, /mixamo-hero\.glb/);
assert.doesNotMatch(sw, /painterly\.js/);
assert.match(sw, /js\/echo\.js/);
assert.match(sw, /assets\/icons\/echo_phrase\.svg/);
assert.match(sw, /js\/grove\.js/);
for (const name of ['chromatic-orbit', 'note-medallion', 'filigree-frame', 'resonance-core']) {
  assert.ok(sw.includes('assets/heritage/' + name + '.svg'), 'missing cached heritage SVG ' + name);
}
assert.match(sw, /js\/heritage-timeline\.js/);
assert.match(sw, /harmonic-grove-37\.glb/);
for (const path of sw.matchAll(/'\.\/([^']+)'/g)) {
  const p = path[1];
  if (p) assert.ok(exists(p), 'missing offline dependency ' + p);
}
console.log('Cloud asset intake contracts: PASS');
