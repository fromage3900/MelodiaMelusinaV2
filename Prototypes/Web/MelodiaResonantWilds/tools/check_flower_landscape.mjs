// Zero-dependency source and Chladni sampler contract for Floraison P0.
// Geometry / shader visual QA still requires WebGL; this is not a render test.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { plateField, sampleBotanicalPlate } from '../js/resonant-botany.js';
const landscape = readFileSync(new URL('../js/flower-landscape.js', import.meta.url),'utf8');
const world = readFileSync(new URL('../js/world.js', import.meta.url),'utf8');
const families = ['bellflower','wildflower','fern','rosette','spire'];
for(const family of families)assert.match(landscape,new RegExp("'"+family+"'"),family+' missing');
assert.match(landscape,/InstancedMesh\(geometry,material,items\.length\)/);
assert.match(landscape,/computeBoundingSphere\(\)/);
assert.match(landscape,/sampleBotanicalPlate\(/);
assert.match(landscape,/poiNear/);
assert.match(landscape,/pathClear/);
assert.match(landscape,/\?botany=1/);
assert.match(world,/if \(this\.botanyEnabled\) installFlowerLandscapeChunk/);
assert.match(world,/this\.botanyEnabled = flowerLandscapeEnabled/);
for(const [n,m] of [[2,3],[3,5],[4,7]]){
  const points=sampleBotanicalPlate({family:'rosette',mode:[n,m],extent:34,cells:52,threshold:.115,maxInstances:170,seed:23});
  assert.ok(points.length>20 && points.length<=170, 'garden density within cap');
  assert.ok(Math.min(...points.map(p=>p.z)) < -14 && Math.max(...points.map(p=>p.z)) > 14, 'full plate coverage');
  assert.deepEqual(points,sampleBotanicalPlate({family:'rosette',mode:[n,m],extent:34,cells:52,threshold:.115,maxInstances:170,seed:23}));
  assert.ok(points.every(p=>Math.abs(plateField(p.x/34+.5,p.z/34+.5,n,m)) < .3), 'nodal positioning');
}
console.log('Floraison contract PASS: five foliage families, three deterministic garden modes, opt-in chunk instancing');
