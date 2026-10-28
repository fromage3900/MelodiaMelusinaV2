// Source contract checks for this zero-dependency Three.js shader experiment.
// This does NOT replace a WebGL compilation and real browser frame test.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import assert from 'node:assert/strict';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const read = (p) => readFileSync(join(root, p), 'utf8');
const world = read('js/world.js');
const entities = read('js/entities.js');
const cel = read('js/cel.js');
assert.match(cel, /MeshToonMaterial/);
assert.match(cel, /gradientMap: nprV2 \? paletteGradient/);
assert.match(cel, /: toonGradient\(\)/);
assert.match(cel, /NearestFilter/);
assert.match(world, /this\.terrainMat = environmentMaterial/);
assert.match(cel, /export const legacyRender/);
assert.match(cel, /MeshLambertMaterial/);
assert.match(cel, /NPR_PALETTES/);
assert.match(cel, /paletteGradient/);
assert.match(cel, /RGBAFormat/);
assert.match(world, /if \(legacyRender\)/);
assert.match(world, /rwChladni\(/);
assert.match(world, /rwCaustic\(/);
assert.match(world, /uIsRift\.value = on \? 1 : 0/);
assert.match(world, /shaderFlags\.get\('chladni'\)/);
assert.match(world, /shaderFlags\.get\('caustics'\)/);
assert.match(entities, /celMaterial\(color, o\)/);
assert.doesNotMatch(world, /new THREE\.MeshLambertMaterial/);
console.log('Shader Lab P0 source contracts passed. Browser/WebGL QA still required.');
