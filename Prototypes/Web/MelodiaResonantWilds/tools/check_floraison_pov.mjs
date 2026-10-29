import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { FloraisonPOV, povMoveVector, povLookVector } from '../js/floraison-pov.js';

// Controller only uses window at construction, not while the module is imported.
globalThis.window = { location: { search: '?botany=1&pov=1' } };
const close = (actual, expected, msg) => assert.ok(Math.abs(actual - expected) < 1e-8, msg);
for (const {yaw, expectedX, expectedZ} of [
  {yaw: Math.PI, expectedX: 0, expectedZ: -1},
  {yaw: Math.PI/2, expectedX: 1, expectedZ: 0},
  {yaw: 0, expectedX: 0, expectedZ: 1},
]) {
  const v = povMoveVector(0, -1, yaw);
  close(v.x, expectedX, 'W forward x'); close(v.z, expectedZ, 'W forward z');
}
const strafe = povMoveVector(1, 0, Math.PI);
close(strafe.x, -1, 'strafing uses the camera-facing right vector');
close(strafe.z, 0, 'strafing orthogonal to camera');
const dir = povLookVector(Math.PI, -0.1);
close(Math.hypot(dir.x, dir.y, dir.z), 1, 'normalized look direction');

let lensRefresh = 0, buttonRefresh = 0, cameraLook, cameraPos;
const game = {
  world: { botanyEnabled: true, inRift: false },
  player: {
    facing: Math.PI, dead: false,
    pos: { x: 0, y: 2.2, z: 55 },
    vel: { x: 0, z: 0 },
    m: { group: { visible: true }, shadow: { visible: true } },
  },
  camera: {
    position: { set(...args) { cameraPos = args; } },
    lookAt(...args) { cameraLook = args; },
  },
  sun: {
    position: { set() {} },
    target: { position: { copy() {} }, updateMatrixWorld() {} },
  },
  time: 0, paused: false,
  resize() { lensRefresh++; },
  ui: { syncFloraisonPOV() { buttonRefresh++; } },
};
const pov = new FloraisonPOV(game);
assert.equal(pov.enabled, true, 'query activates preview only with botany');
assert.equal(pov.update(1/60), true);
assert.ok(cameraPos[1] < 4 && cameraPos[1] > 3, 'eye height looks into flowers');
assert.ok(cameraLook[2] < cameraPos[2], 'facing initially looks toward -z');
assert.equal(game.player.m.group.visible, false, 'body hidden at first-person lens');
pov.look(800, 500);
assert.ok(pov.pitch >= -0.66 && pov.pitch <= 0.40, 'look pitch clamped');
pov.toggle();
assert.equal(pov.enabled, false);
assert.equal(game.player.m.group.visible, true, 'third-person body restored');
assert.equal(game.player.m.shadow.visible, true, 'third-person shadow restored');
assert.equal(lensRefresh, 1, 'camera projection refreshed on exit');
assert.equal(buttonRefresh, 1, 'HUD button status refreshed');
game.world.inRift = true;
assert.equal(pov.set(true), false, 'first person disabled in rift');
const controls = readFileSync(new URL('../js/ui.js', import.meta.url),'utf8');
const core = readFileSync(new URL('../js/game.js', import.meta.url),'utf8');
const markup = readFileSync(new URL('../index.html', import.meta.url),'utf8');
assert.match(controls, /KeyP/);
assert.match(controls, /povMoveVector/);
assert.match(controls, /povDrag/);
assert.match(core, /if \(this\.floraisonPOV\?\.update\(dt\)\) return;/);
assert.match(markup, /id="btnFloraisonPOV"/);
console.log('Floraison POV camera PASS — lens, look, movement, touch routing, reversible visibility');
