import * as THREE from 'three';
import { createRuntime } from '../../src/core/createRuntime.js';
import { createStateMachine } from '../../src/game/createStateMachine.js';

const stage = document.getElementById('stage');
const status = document.getElementById('status');
const resetButton = document.getElementById('reset');

const runtime = createRuntime({
  THREE,
  container: stage,
  camera: { fov: 48, near: 0.1, far: 100, z: 8 },
  pixelRatioCap: 2,
});

runtime.scene.background = new THREE.Color(0x151a31);
runtime.scene.add(new THREE.HemisphereLight(0xffffff, 0x222744, 2.4));

const key = new THREE.DirectionalLight(0xffffff, 3.2);
key.position.set(4, 5, 6);
runtime.scene.add(key);

const floor = new THREE.Mesh(
  new THREE.CircleGeometry(5.8, 64),
  new THREE.MeshStandardMaterial({ color: 0x1b2140, roughness: 0.9, metalness: 0.05 }),
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -2;
runtime.scene.add(floor);

const machine = createStateMachine({
  initial: 'playing',
  states: {
    playing: { on: { WIN: 'won', RESET: 'playing' } },
    won: { on: { RESET: 'playing' } },
  },
});

const geometryFactories = [
  () => new THREE.IcosahedronGeometry(0.58, 1),
  () => new THREE.TorusKnotGeometry(0.42, 0.14, 80, 12),
  () => new THREE.OctahedronGeometry(0.62, 0),
  () => new THREE.TorusGeometry(0.5, 0.18, 16, 48),
  () => new THREE.DodecahedronGeometry(0.56, 0),
];

const positions = [
  [-2.7, 0.4, 0],
  [-1.35, 1.45, -0.35],
  [0, 0.1, 0.2],
  [1.45, 1.2, -0.2],
  [2.7, 0.25, 0.1],
];

const echoes = geometryFactories.map((makeGeometry, index) => {
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setHSL(0.58 + index * 0.045, 0.45, 0.7),
    roughness: 0.28,
    metalness: 0.18,
    emissive: new THREE.Color().setHSL(0.58 + index * 0.045, 0.35, 0.18),
  });
  const mesh = new THREE.Mesh(makeGeometry(), material);
  mesh.position.set(...positions[index]);
  mesh.userData.echoIndex = index;
  runtime.scene.add(mesh);
  return mesh;
});

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let collected = 0;

function updateStatus() {
  if (machine.snapshot().state === 'won') {
    status.textContent = 'Complete — five of five echoes collected.';
  } else {
    status.textContent = `${collected} / ${echoes.length} echoes collected.`;
  }
}

function collectAt(clientX, clientY) {
  if (machine.snapshot().state !== 'playing') return;

  const rect = runtime.renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, runtime.camera);

  const hit = raycaster.intersectObjects(echoes.filter((mesh) => mesh.visible), false)[0];
  if (!hit) return;

  hit.object.visible = false;
  collected += 1;

  if (collected >= echoes.length) machine.send('WIN');
  updateStatus();
}

runtime.renderer.domElement.addEventListener('pointerdown', (event) => {
  collectAt(event.clientX, event.clientY);
});

function reset() {
  collected = 0;
  machine.send('RESET');
  for (const echo of echoes) echo.visible = true;
  updateStatus();
}

resetButton.addEventListener('click', reset);

const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
if (!reducedMotion) {
  runtime.onFrame(({ delta, now }) => {
    echoes.forEach((echo, index) => {
      if (!echo.visible) return;
      echo.rotation.x += delta * (0.22 + index * 0.03);
      echo.rotation.y += delta * (0.35 + index * 0.025);
      echo.position.y = positions[index][1] + Math.sin(now * 0.0015 + index) * 0.12;
    });
  });
}

updateStatus();
