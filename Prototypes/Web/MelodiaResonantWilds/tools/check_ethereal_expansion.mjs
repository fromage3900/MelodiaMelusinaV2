// Static contract: 2× map, eight biomes, ethereal styles + ambience ids.
import assert from 'node:assert/strict';
import { BIOMES, WORLD_RADIUS, HUB, RIFT_STYLE } from '../js/design.js';

assert.equal(WORLD_RADIUS, 1400, 'WORLD_RADIUS must be 2× the prior 700');
assert.equal(BIOMES.length, 8, 'expected eight biomes');

const ids = BIOMES.map((b) => b.id);
for (const id of ['choir_marsh', 'glass_orchard', 'starlit_moor']) {
  assert.ok(ids.includes(id), `missing invented biome ${id}`);
}

const styles = new Set(['waltz', 'cathedral', 'choir', 'fugue', 'glass', 'toccata', 'starlit', 'glacial']);
for (const b of BIOMES) {
  assert.ok(styles.has(b.style), `${b.id} style ${b.style}`);
  assert.ok(b.ambience, `${b.id} missing ambience`);
  assert.ok(Array.isArray(b.motif) && b.motif.length >= 4, `${b.id} motif`);
  assert.ok(b.boss && b.bossName, `${b.id} boss`);
  assert.ok(Number.isFinite(b.angle), `${b.id} angle`);
  assert.ok(b.props?.length, `${b.id} props`);
}

assert.equal(HUB.ambience, 'hub');
assert.equal(HUB.style, 'morning');
assert.equal(RIFT_STYLE.ambience, 'rift');

const orders = BIOMES.map((b) => b.order);
assert.deepEqual(orders, [...orders].sort((a, b) => a - b), 'biomes must be order-sorted');
assert.equal(new Set(orders).size, 8, 'biome orders must be unique');

console.log('Ethereal expansion contracts: PASS (' + ids.join(', ') + ')');
