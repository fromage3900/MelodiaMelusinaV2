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
const painterly = file('js/painterly.js');
assert.match(painterly, /painterlyEnabled/);
assert.match(painterly, /structure tensor/);
assert.match(painterly, /WebGLRenderTarget/);
assert.match(painterly, /coherence/);
assert.match(file('js/game.js'), /this\.painterly\.render/);
const tuner = file('js/npr-tuner.js');
assert.match(tuner, /attachShaderTuner/);
assert.match(tuner, /Soft wash/);
assert.match(tuner, /Copy this look/);
assert.match(painterly, /applySettings/);
assert.match(painterly, /uAnisotropy/);
assert.match(painterly, /uEdgeProtect/);
assert.match(file('js/asset-loader.js'), /melodiaInk/);
const model = readFileSync(join(root, 'assets/models/resonance-shrine.glb'));
assert.equal(model.subarray(0, 4).toString('ascii'), 'glTF');
assert.equal(model.readUInt32LE(4), 2);
assert.equal(model.readUInt32LE(8), model.byteLength);
assert.ok(model.byteLength < 1024 * 1024, 'P0 GLB must fit 1 MiB');
const manifest = JSON.parse(file('manifest.json'));
for (const icon of manifest.icons) assert.ok(exists(icon.src), 'missing PWA icon ' + icon.src);
const sw = file('sw.js');
assert.match(sw, /resonant-wilds-v13-20261029-nikki-ability/);
assert.match(sw, /js\/playground\.js/);
assert.match(sw, /js\/flags\.js/);
assert.match(sw, /js\/echo\.js/);
assert.match(sw, /assets\/icons\/echo_phrase\.svg/);
assert.match(sw, /js\/grove\.js/);
assert.match(sw, /js\/mixamo\.js/);
assert.match(sw, /mixamo-hero\.glb/);
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
