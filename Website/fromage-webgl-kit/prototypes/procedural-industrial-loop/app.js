import * as THREE from 'three';
import { RoundedBoxGeometry } from 'https://cdn.jsdelivr.net/npm/three@0.186.0/examples/jsm/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'https://cdn.jsdelivr.net/npm/three@0.186.0/examples/jsm/environments/RoomEnvironment.js';
import { createRuntime } from '../../src/core/createRuntime.js';
import { createDeterministicTimeline } from '../../src/animation/createDeterministicTimeline.js';

const stage = document.getElementById('stage');
const timeline = document.getElementById('timeline');
const timeValue = document.getElementById('timeValue');
const seedSelect = document.getElementById('seed');
const playButton = document.getElementById('play');
const resetButton = document.getElementById('reset');
const diagnostics = document.getElementById('diagnostics');
const diagnosticsDetails = document.getElementById('diagnosticsDetails');
const modeBadge = document.getElementById('modeBadge');
const modeButtons = [...document.querySelectorAll('.mode')];

const LOOP_SECONDS = 16;
const CANONICAL_SEED = 1;
const VALID_MODES = new Set(['base', 'structural', 'flow', 'thermal']);
const params = new URLSearchParams(window.location.search);
const captureMode = params.get('capture') === '1';
const requestedSeed = Number.parseInt(params.get('seed') ?? '', 10);
const requestedTime = Number.parseFloat(params.get('t') ?? '');
const requestedMode = params.get('mode');
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

if (captureMode) document.documentElement.classList.add('capture');

const motionTimeline = createDeterministicTimeline({
  duration: LOOP_SECONDS,
  channels: {
    stationAOffsetX: [
      { start: 0, end: 2, from: 0, to: 0.72 },
      { start: 12, end: 14, from: 0.72, to: 0 },
    ],
    stationBRotationY: [
      { start: 2, end: 4, from: 0, to: Math.PI * 0.5 },
      { start: 10, end: 12, from: Math.PI * 0.5, to: 0 },
    ],
    stationCOffsetY: [
      { start: 4, end: 6, from: 0, to: 0.82 },
      { start: 8, end: 10, from: 0.82, to: 0 },
    ],
  },
});

const phases = [
  { start: 0, end: 2, name: 'A_TRANSLATE_OUT' },
  { start: 2, end: 4, name: 'B_ROTATE_OUT' },
  { start: 4, end: 6, name: 'C_LIFT_OUT' },
  { start: 6, end: 8, name: 'HARD_HOLD_A' },
  { start: 8, end: 10, name: 'C_LIFT_RETURN' },
  { start: 10, end: 12, name: 'B_ROTATE_RETURN' },
  { start: 12, end: 14, name: 'A_TRANSLATE_RETURN' },
  { start: 14, end: 16, name: 'HARD_HOLD_B' },
];

const runtime = createRuntime({
  THREE,
  container: stage,
  camera: { fov: 28, near: 0.1, far: 120, x: 10.8, y: 6.8, z: 13.8 },
  renderer: { antialias: true, alpha: false },
  pixelRatioCap: captureMode ? 2 : 1.75,
});

runtime.renderer.setClearColor(0xd9d9d5, 1);
runtime.renderer.shadowMap.enabled = true;
runtime.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
runtime.renderer.toneMapping = THREE.ACESFilmicToneMapping;
runtime.renderer.toneMappingExposure = 1.0;
runtime.camera.lookAt(0, 1.25, 0);

const pmrem = new THREE.PMREMGenerator(runtime.renderer);
const roomEnvironment = new RoomEnvironment();
const environmentTarget = pmrem.fromScene(roomEnvironment, 0.04);
runtime.scene.environment = environmentTarget.texture;
roomEnvironment.dispose();
pmrem.dispose();

const hemi = new THREE.HemisphereLight(0xffffff, 0x8f918f, 1.45);
const key = new THREE.DirectionalLight(0xffffff, 4.3);
key.position.set(5.5, 9.5, 6.5);
key.castShadow = true;
key.shadow.mapSize.set(1536, 1536);
key.shadow.camera.left = -13;
key.shadow.camera.right = 13;
key.shadow.camera.top = 9;
key.shadow.camera.bottom = -6;
key.shadow.bias = -0.00025;
const fill = new THREE.DirectionalLight(0xffffff, 0.9);
fill.position.set(-8, 4, 3);
runtime.scene.add(hemi, key, fill);

const BASE_MATERIALS = {
  BODY: new THREE.MeshStandardMaterial({ name: 'MAT_BODY', color: 0xbfc0bd, roughness: 0.52, metalness: 0.64 }),
  SHELL: new THREE.MeshStandardMaterial({ name: 'MAT_SHELL', color: 0xe2e2de, roughness: 0.72, metalness: 0.14 }),
  ACCENT: new THREE.MeshStandardMaterial({ name: 'MAT_ACCENT', color: 0x777a79, roughness: 0.38, metalness: 0.72 }),
  MACHINE: new THREE.MeshStandardMaterial({ name: 'MAT_MACHINE', color: 0x4d5050, roughness: 0.46, metalness: 0.78 }),
  ACTUATOR: new THREE.MeshStandardMaterial({ name: 'MAT_ACTUATOR', color: 0x969896, roughness: 0.32, metalness: 0.86 }),
};

const vizMaterialCache = new Map();
const sharedCylinder = new THREE.CylinderGeometry(1, 1, 1, 28, 1, false);
const sharedRod = new THREE.CylinderGeometry(1, 1, 1, 18, 1, false);

const floorMaterial = new THREE.MeshStandardMaterial({ color: 0xd4d4cf, roughness: 0.96, metalness: 0.01 });
const floor = new THREE.Mesh(new THREE.PlaneGeometry(32, 20), floorMaterial);
floor.name = 'STUDIO_FLOOR';
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.06;
floor.receiveShadow = true;
runtime.scene.add(floor);

const sceneRoot = new THREE.Group();
sceneRoot.name = 'PROC_IndustrialSystemRoot';
runtime.scene.add(sceneRoot);

let currentSeed = Number.isInteger(requestedSeed) && requestedSeed >= 1 && requestedSeed <= 3 ? requestedSeed : CANONICAL_SEED;
let currentMode = VALID_MODES.has(requestedMode) ? requestedMode : 'base';
let playing = !reducedMotion && !captureMode && !Number.isFinite(requestedTime);
let timeSeconds = Number.isFinite(requestedTime) ? THREE.MathUtils.clamp(requestedTime, 0, LOOP_SECONDS) : 0;
let lastFrameSeconds = performance.now() / 1000;
let fpsSmoothed = 60;
let diagAccumulator = 0;
let assembly = null;

seedSelect.value = String(currentSeed);

function mulberry32(seed) {
  let state = seed >>> 0;
  return function random() {
    state += 0x6D2B79F5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function field(structural, flow, thermal) {
  return { structural, flow, thermal };
}

function roundedPart(parent, size, position, name, scalarField, family = 'BODY', radius = 0.08, castShadow = false) {
  const [x, y, z] = size;
  const safeRadius = Math.min(radius, Math.min(x, y, z) * 0.22);
  const geometry = new RoundedBoxGeometry(x, y, z, 4, safeRadius);
  const mesh = new THREE.Mesh(geometry, BASE_MATERIALS[family]);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.castShadow = castShadow;
  mesh.receiveShadow = true;
  mesh.userData.field = scalarField;
  mesh.userData.materialFamily = family;
  parent.add(mesh);
  return mesh;
}

function cylinderPart(parent, radius, length, position, rotation, name, scalarField, family = 'ACCENT', castShadow = false, geometry = sharedCylinder) {
  const mesh = new THREE.Mesh(geometry, BASE_MATERIALS[family]);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.rotation.set(...rotation);
  mesh.scale.set(radius, length, radius);
  mesh.castShadow = castShadow;
  mesh.receiveShadow = true;
  mesh.userData.field = scalarField;
  mesh.userData.materialFamily = family;
  parent.add(mesh);
  return mesh;
}

function addFastener(parent, x, y, z, name) {
  return cylinderPart(parent, 0.055, 0.055, [x, y, z], [Math.PI / 2, 0, 0], name, field(0.54, 0.16, 0.38), 'MACHINE', false, sharedRod);
}

function createStation(index, x, random) {
  const prefix = `STATION_${String(index + 1).padStart(2, '0')}`;
  const group = new THREE.Group();
  group.name = prefix;
  group.position.x = x;

  const width = 2.45 + random() * 0.24;
  const height = 2.55 + random() * 0.24;
  const depth = 2.15 + random() * 0.18;
  const columnOffset = width * 0.39;

  roundedPart(group, [width + 0.46, 0.22, depth + 0.5], [0, 0.12, 0], `${prefix}_DECK`, field(0.18, 0.08, 0.15), 'SHELL', 0.07, true);
  roundedPart(group, [width, 0.34, depth], [0, 0.32, 0], `${prefix}_BASE_HOUSING`, field(0.32, 0.11, 0.22), 'BODY', 0.08, true);

  for (const sx of [-1, 1]) {
    for (const sz of [-1, 1]) {
      roundedPart(group, [0.18, 0.16, 0.18], [sx * width * 0.37, -0.02, sz * depth * 0.36], `${prefix}_FOOT_${sx > 0 ? 'R' : 'L'}_${sz > 0 ? 'F' : 'B'}`, field(0.58, 0.08, 0.28), 'MACHINE', 0.035, false);
    }
  }

  roundedPart(group, [0.27, height, 0.31], [-columnOffset, height * 0.5 + 0.35, 0], `${prefix}_COLUMN_L`, field(0.84, 0.12, 0.37), 'MACHINE', 0.045, true);
  roundedPart(group, [0.27, height, 0.31], [columnOffset, height * 0.5 + 0.35, 0], `${prefix}_COLUMN_R`, field(0.79, 0.18, 0.43), 'MACHINE', 0.045, true);
  roundedPart(group, [width * 0.94, 0.26, 0.36], [0, height + 0.32, 0], `${prefix}_GANTRY`, field(0.94, 0.28, 0.52), 'BODY', 0.055, true);
  roundedPart(group, [width * 0.58, 0.12, depth * 0.64], [0, height + 0.51, 0], `${prefix}_SERVICE_TRAY_TOP`, field(0.42, 0.62, 0.48), 'SHELL', 0.035, false);
  roundedPart(group, [0.12, 0.9, depth * 0.72], [-width * 0.49, 1.18, 0], `${prefix}_SERVICE_TRAY_L`, field(0.48, 0.78, 0.44), 'SHELL', 0.028, false);
  roundedPart(group, [0.12, 0.9, depth * 0.72], [width * 0.49, 1.18, 0], `${prefix}_SERVICE_TRAY_R`, field(0.44, 0.74, 0.4), 'SHELL', 0.028, false);

  const core = cylinderPart(group, 0.52, 1.35, [0, 1.18, 0], [0, 0, Math.PI / 2], `${prefix}_CORE`, field(0.58, 0.76, 0.72), 'ACCENT', true);
  core.scale.set(0.52, 1.35, 0.52);
  cylinderPart(group, 0.61, 0.12, [-0.68, 1.18, 0], [0, 0, Math.PI / 2], `${prefix}_COLLAR_L`, field(0.62, 0.7, 0.67), 'ACTUATOR', false);
  cylinderPart(group, 0.61, 0.12, [0.68, 1.18, 0], [0, 0, Math.PI / 2], `${prefix}_COLLAR_R`, field(0.63, 0.72, 0.69), 'ACTUATOR', false);
  cylinderPart(group, 0.15, 2.58, [0, 1.18, 0], [0, 0, Math.PI / 2], `${prefix}_MANIFOLD`, field(0.36, 0.95, 0.64), 'BODY', true, sharedRod);
  roundedPart(group, [0.74, 0.72, 0.7], [0, 1.18, -depth * 0.36], `${prefix}_REAR_HOUSING`, field(0.48, 0.54, 0.78), 'SHELL', 0.08, true);
  roundedPart(group, [0.42, 0.42, 0.22], [0, 1.18, -depth * 0.74], `${prefix}_REAR_RISER`, field(0.52, 0.61, 0.82), 'MACHINE', 0.045, false);

  const moving = new THREE.Group();
  moving.name = `${prefix}_ACTUATOR`;
  moving.position.set(0, 1.18, depth * 0.51);
  group.add(moving);
  roundedPart(moving, [0.94, 0.68, 0.36], [0, 0, 0], `${prefix}_ACTUATOR_BLOCK`, field(0.69, 0.56, 0.89), 'ACTUATOR', 0.075, true);
  roundedPart(moving, [0.7, 0.13, 0.43], [0, 0.38, 0], `${prefix}_ACTUATOR_CAP`, field(0.74, 0.48, 0.82), 'SHELL', 0.035, false);
  cylinderPart(moving, 0.085, 1.3, [0, -0.64, 0], [0, 0, 0], `${prefix}_ACTUATOR_ROD`, field(0.73, 0.5, 0.83), 'ACTUATOR', true, sharedRod);

  addFastener(group, -width * 0.37, 0.5, depth * 0.51, `${prefix}_FASTENER_01`);
  addFastener(group, width * 0.37, 0.5, depth * 0.51, `${prefix}_FASTENER_02`);
  addFastener(group, -width * 0.37, 0.5, -depth * 0.51, `${prefix}_FASTENER_03`);
  addFastener(group, width * 0.37, 0.5, -depth * 0.51, `${prefix}_FASTENER_04`);

  sceneRoot.add(group);
  return { group, moving, width, height, depth, baseMovingY: 1.18 };
}

function disposeAssemblyChildren() {
  const children = [...sceneRoot.children];
  for (const child of children) {
    sceneRoot.remove(child);
    child.traverse((object) => {
      if (object.geometry && object.geometry !== sharedCylinder && object.geometry !== sharedRod) object.geometry.dispose?.();
    });
  }
}

function buildAssembly(seed) {
  disposeAssemblyChildren();
  const random = mulberry32(seed * 1009 + 97);
  const spacing = 4.15 + random() * 0.25;
  const stations = [createStation(0, -spacing, random), createStation(1, 0, random), createStation(2, spacing, random)];

  roundedPart(sceneRoot, [spacing * 2.75, 0.16, 0.22], [0, 0.05, -1.55], 'SYSTEM_RAIL_REAR', field(0.68, 0.47, 0.34), 'MACHINE', 0.035, true);
  roundedPart(sceneRoot, [spacing * 2.75, 0.11, 0.14], [0, 0.16, 1.4], 'SYSTEM_RAIL_FRONT', field(0.64, 0.52, 0.38), 'ACCENT', 0.025, false);
  roundedPart(sceneRoot, [spacing * 2.5, 0.08, 0.38], [0, 0.1, -1.85], 'SYSTEM_CABLE_TRAY', field(0.36, 0.83, 0.44), 'SHELL', 0.025, false);

  assembly = { stations, spacing };
  applyVisualization(currentMode);
  applyTimeline(timeSeconds);
}

const ramps = {
  structural: [0x31547c, 0x6485a7, 0xc8cfd5, 0xc48758, 0x7d3d34],
  flow: [0x24465e, 0x3b7f9e, 0x82b6bd, 0xd6cf9b, 0xb96649],
  thermal: [0x2e4b72, 0x6e72a2, 0xb4a4a4, 0xcf845e, 0x853c31],
};

function sampleRamp(mode, value) {
  const ramp = ramps[mode];
  const clamped = THREE.MathUtils.clamp(value ?? 0, 0, 0.9999);
  return ramp[Math.floor(clamped * ramp.length)];
}

function getVizMaterial(mode, value) {
  const bucket = Math.floor(THREE.MathUtils.clamp(value ?? 0, 0, 0.9999) * 5);
  const keyName = `${mode}:${bucket}`;
  if (!vizMaterialCache.has(keyName)) {
    const color = sampleRamp(mode, (bucket + 0.5) / 5);
    vizMaterialCache.set(keyName, new THREE.MeshStandardMaterial({
      name: `MAT_${mode.toUpperCase()}_${bucket}`,
      color,
      roughness: 0.58,
      metalness: 0.32,
      emissive: color,
      emissiveIntensity: 0.02,
    }));
  }
  return vizMaterialCache.get(keyName);
}

function applyVisualization(mode) {
  currentMode = VALID_MODES.has(mode) ? mode : 'base';
  sceneRoot.traverse((object) => {
    if (!object.isMesh) return;
    const family = object.userData.materialFamily ?? 'BODY';
    const scalarField = object.userData.field;
    object.material = currentMode === 'base' || !scalarField
      ? BASE_MATERIALS[family]
      : getVizMaterial(currentMode, scalarField[currentMode]);
  });
  modeButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.mode === currentMode)));
  modeBadge.textContent = `${currentMode.toUpperCase()} / SEED ${String(currentSeed).padStart(2, '0')}`;
}

function getPhaseName(time) {
  if (time >= LOOP_SECONDS) return 'LOOP_END';
  const clamped = Math.max(0, time);
  return phases.find((phase) => clamped >= phase.start && clamped < phase.end)?.name ?? 'LOOP_END';
}

function applyTimeline(time) {
  if (!assembly) return;
  const sample = motionTimeline.sample(time);
  const [a, b, c] = assembly.stations;
  a.moving.position.x = sample.values.stationAOffsetX;
  a.moving.rotation.y = 0;
  b.moving.rotation.y = sample.values.stationBRotationY;
  b.moving.position.x = 0;
  c.moving.position.y = c.baseMovingY + sample.values.stationCOffsetY;
  c.moving.rotation.y = 0;
  timeline.value = sample.time.toFixed(2);
  timeValue.value = `${sample.time.toFixed(1)}s`;
}

function setTime(nextTime, pause = true) {
  timeSeconds = THREE.MathUtils.clamp(Number(nextTime) || 0, 0, LOOP_SECONDS);
  if (pause) playing = false;
  applyTimeline(timeSeconds);
  updatePlayButton();
}

function setSeed(nextSeed) {
  const parsed = Number.parseInt(nextSeed, 10);
  currentSeed = Number.isInteger(parsed) && parsed >= 1 && parsed <= 3 ? parsed : CANONICAL_SEED;
  seedSelect.value = String(currentSeed);
  buildAssembly(currentSeed);
}

function setMode(nextMode) {
  applyVisualization(VALID_MODES.has(nextMode) ? nextMode : 'base');
}

function resetTimeline() {
  setTime(0, true);
}

function endpointDelta() {
  const start = motionTimeline.sample(0).values;
  const end = motionTimeline.sample(LOOP_SECONDS).values;
  return Object.keys(start).reduce((sum, keyName) => sum + Math.abs((end[keyName] ?? 0) - (start[keyName] ?? 0)), 0);
}

function updatePlayButton() {
  playButton.textContent = playing ? 'Pause' : 'Play';
  playButton.setAttribute('aria-pressed', String(playing));
}

function updateDiagnostics(delta) {
  if (delta > 0) fpsSmoothed += ((1 / delta) - fpsSmoothed) * 0.08;
  diagAccumulator += delta;
  if (diagAccumulator < 0.35) return;
  diagAccumulator = 0;
  const info = runtime.renderer.info.render;
  const memory = runtime.renderer.info.memory;
  diagnostics.textContent = [
    `MODE   ${currentMode.toUpperCase()}`,
    `SEED   ${String(currentSeed).padStart(2, '0')}${currentSeed === CANONICAL_SEED ? ' / CANONICAL' : ''}`,
    `TIME   ${timeSeconds.toFixed(2)}s / ${getPhaseName(timeSeconds)}`,
    `LOOP Δ ${endpointDelta().toFixed(6)}`,
    `FPS    ${Math.round(fpsSmoothed)}`,
    `DPR    ${runtime.renderer.getPixelRatio().toFixed(2)}`,
    `DRAWS  ${info.calls}`,
    `TRIS   ${info.triangles}`,
    `GEOMS  ${memory.geometries}`,
  ].join('\n');
}

playButton.addEventListener('click', () => {
  playing = !playing;
  if (playing && timeSeconds >= LOOP_SECONDS) timeSeconds = 0;
  lastFrameSeconds = performance.now() / 1000;
  updatePlayButton();
});
resetButton.addEventListener('click', resetTimeline);
timeline.addEventListener('input', () => setTime(Number(timeline.value), true));
seedSelect.addEventListener('change', () => setSeed(seedSelect.value));
modeButtons.forEach((button) => button.addEventListener('click', () => setMode(button.dataset.mode)));

buildAssembly(currentSeed);
applyVisualization(currentMode);
applyTimeline(timeSeconds);
updatePlayButton();
if (captureMode) diagnosticsDetails?.removeAttribute('open');

runtime.onFrame(({ delta, now }) => {
  const nowSeconds = now / 1000;
  const elapsed = Math.min(Math.max(nowSeconds - lastFrameSeconds, 0), 0.1);
  lastFrameSeconds = nowSeconds;
  if (playing) {
    timeSeconds = motionTimeline.wrap(timeSeconds + elapsed);
    applyTimeline(timeSeconds);
  }
  updateDiagnostics(delta);
});

window.__industrialLoop = {
  getState() {
    return {
      mode: currentMode,
      seed: currentSeed,
      canonicalSeed: CANONICAL_SEED,
      time: timeSeconds,
      phase: getPhaseName(timeSeconds),
      loopDelta: endpointDelta(),
      capture: captureMode,
      draws: runtime.renderer.info.render.calls,
      tris: runtime.renderer.info.render.triangles,
      geometries: runtime.renderer.info.memory.geometries,
    };
  },
  setTime,
  setSeed,
  setMode,
  play() { playing = true; updatePlayButton(); },
  pause() { playing = false; updatePlayButton(); },
  reset: resetTimeline,
};
