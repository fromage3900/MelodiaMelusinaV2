// Source-only 37-object Higgsfield GLB preservation gate. No browser loading.
// This does not validate per-object transforms, materials, instancing or performance.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const raw = readFileSync(join(root, 'assets/models/harmonic-grove-37.glb'));
assert.equal(raw.toString('ascii', 0, 4), 'glTF');
assert.equal(raw.readUInt32LE(4), 2, 'GLB version');
assert.equal(raw.readUInt32LE(8), raw.byteLength, 'GLB header byte length');
assert.ok(raw.byteLength <= 1024 * 1024, 'P0 asset budget must be <=1 MiB');
assert.equal(raw.readUInt32LE(16), 0x4E4F534A, 'GLB JSON chunk');
const n = raw.readUInt32LE(12);
assert.ok(n > 0 && n + 20 <= raw.length, 'JSON chunk length');
const data = JSON.parse(raw.subarray(20, 20 + n).toString('utf8'));
const anchors = data.nodes.filter(x => x.name?.startsWith('ASSET_')).map(x => x.name);
assert.equal(anchors.length, 37, '37 authored roots');
assert.equal(new Set(anchors).size, 37, 'no duplicate root names');
assert.ok(data.meshes?.length > 0, 'GLB must contain meshes');
console.log('Harmonic Grove source GLB: PASS', {
  bytes: raw.byteLength,
  roots: anchors.length,
  meshes: data.meshes.length,
  materials: data.materials?.length ?? 0,
});
