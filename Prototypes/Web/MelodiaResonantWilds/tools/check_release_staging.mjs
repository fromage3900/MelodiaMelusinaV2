// Release-stage fail-closed contract: Nikki v14 semantics + hard cel 100-GLB
// Grove + Floraison v15 PWA + no accidental LFS pointer promotion.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { GROVE_ALL_NAMES, GROVE_INTERACTIVE } from '../js/grove-catalog.js';

const dir = dirname(dirname(fileURLToPath(import.meta.url)));
const read = p => readFileSync(join(dir, p), 'utf8');
const sw = read('sw.js'), game = read('js/game.js');
const world = read('js/world.js'), ui = read('js/ui.js');
const progress = read('js/progress.js'), activities = read('js/activities.js');
const manifest = JSON.parse(read('ASSET_RELEASE_MANIFEST.json'));
assert.equal(GROVE_ALL_NAMES.length, 100, '100 named assets');
assert.equal(new Set(GROVE_ALL_NAMES).size, 100, 'no duplicate catalog assets');
assert.equal(manifest.optionalModels.length, 63, '63 distinct optional GLB files');
assert.ok(GROVE_INTERACTIVE.length > 0, 'interactive objects retained as separate category');

// Check every GLB in the release manifest is present as its actual blob, not
// a truncated download or a 129-byte Git LFS pointer.
for (const item of manifest.optionalModels) {
  const model = readFileSync(join(dir, 'assets/models', item.filename));
  assert.equal(model.length, item.bytes, item.filename + ': byte length mismatch');
  const hash = createHash('sha1').update(Buffer.from('blob ' + model.length + '\0')).update(model).digest('hex');
  assert.equal(hash, item.blobSha, item.filename + ': Git blob SHA mismatch');
  assert.notEqual(model.subarray(0, 32).toString('utf8').includes('git-lfs.github.com'), true,
    item.filename + ': LFS pointer instead of GLB');
}
assert.match(sw, /resonant-wilds-v15-20261029-floraison-release/);
for (const module of ['js/flags.js', 'js/playground.js', 'js/grove-catalog.js',
  'js/floraison-pov.js', 'js/flower-landscape.js', 'js/resonant-botany.js']) {
  assert.ok(sw.includes("'./" + module + "'"), module + ' missing offline cache');
}
assert.doesNotMatch(sw, /painterly\.js/);
assert.equal(existsSync(join(dir, 'js/painterly.js')), false, 'Kuwahara remains retired');
assert.match(game, /flagPostfx/);
assert.match(game, /groveMode === 'full'/);
assert.match(game, /new FloraisonPOV\(this\)/);
assert.match(game, /installGroveProps\(this\.world, \{ full:/);
assert.match(world, /previousShaderHook/);
assert.match(world, /installFlowerLandscapeChunk/);
assert.match(world, /flagWorldexp/);
assert.match(progress, /abilityOutfits/);
assert.match(progress, /regionsDone/);
assert.match(activities, /abilityOutfit/);
assert.match(ui, /btnFloraisonPOV/);
assert.match(ui, /povMoveVector/);
assert.match(ui, /Regions 100%/);
assert.ok(read('tools/sync_to_mysite.sh').includes('Git LFS pointer'),
  'publisher must preserve real my-site icons');
console.log('RELEASE STAGE PASS: 100 GLBs (63 byte+hash verified), Nikki, Grove, hard cel, Floraison, SW v15');
