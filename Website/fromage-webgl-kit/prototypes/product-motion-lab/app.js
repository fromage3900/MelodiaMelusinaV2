import * as THREE from 'three';
import { createRuntime } from '../../src/core/createRuntime.js';
import { loadAurigaMeter, DEFAULT_AURIGA_URL } from './src/auriga-meter.js';

const stage = document.getElementById('stage');
const slider = document.getElementById('timeline');
const valueOut = document.getElementById('timelineValue');
const playButton = document.getElementById('play');
const resetButton = document.getElementById('reset');
const wireframeButton = document.getElementById('wireframe');
const calloutsButton = document.getElementById('callouts');
const diagnostics = document.getElementById('diagnostics');
const scrollTrack = document.getElementById('scrollTrack');
const calloutEls = [...stage.querySelectorAll('[data-anchor]')];

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const runtime = createRuntime({
  THREE,
  container: stage,
  camera: { fov: 38, x: 3.6, y: 2.5, z: 6.8 },
  pixelRatioCap: 1.75,
});

runtime.scene.background = new THREE.Color(0x15181d);
runtime.camera.lookAt(0, 0.35, 0);

const hemi = new THREE.HemisphereLight(0xe8edf5, 0x30343d, 2.2);
const key = new THREE.DirectionalLight(0xffffff, 5.2);
key.position.set(4, 6, 5);
const rim = new THREE.DirectionalLight(0x9fb8ff, 2.4);
rim.position.set(-5, 2, -4);
runtime.scene.add(hemi, key, rim);

const floor = new THREE.Mesh(
  new THREE.CircleGeometry(4.5, 64),
  new THREE.MeshStandardMaterial({ color: 0x20242b, roughness: 0.92, metalness: 0.02 }),
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1.05;
runtime.scene.add(floor);

const product = new THREE.Group();
product.name = 'generic-product-root';
runtime.scene.add(product);

const shellMat = new THREE.MeshStandardMaterial({ color: 0xced4dc, metalness: 0.55, roughness: 0.28 });
const darkMat = new THREE.MeshStandardMaterial({ color: 0x11151a, metalness: 0.15, roughness: 0.34 });
const glassMat = new THREE.MeshPhysicalMaterial({ color: 0x8fb4d9, roughness: 0.12, metalness: 0.05, transmission: 0.35, thickness: 0.2 });
const accentMat = new THREE.MeshStandardMaterial({ color: 0x7f91ae, metalness: 0.7, roughness: 0.22 });
const materials = [shellMat, darkMat, glassMat, accentMat];

const base = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.52, 1.55, 2, 1, 2), shellMat);
base.position.y = -0.35;
base.name = 'base';
product.add(base);

const top = new THREE.Group();
top.position.set(0, -0.06, -0.6);
top.name = 'lid-assembly';
product.add(top);

const lid = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.22, 1.38, 2, 1, 2), shellMat);
lid.position.set(0, 0, 0.61);
top.add(lid);

const screen = new THREE.Mesh(new THREE.BoxGeometry(1.28, 0.05, 0.72), glassMat);
screen.position.set(0, 0.14, 0.62);
top.add(screen);

const port = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.16, 0.12), darkMat);
port.position.set(1.26, -0.3, 0.15);
product.add(port);

const button = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.08, 32), accentMat);
button.rotation.z = Math.PI / 2;
button.position.set(-1.28, -0.2, 0.18);
product.add(button);

const anchors = {
  screen: new THREE.Object3D(),
  hinge: new THREE.Object3D(),
  port: new THREE.Object3D(),
};
anchors.screen.position.set(0, 0.28, 0.62);
anchors.hinge.position.set(0, 0.04, 0.02);
anchors.port.position.set(1.34, -0.18, 0.18);
top.add(anchors.screen, anchors.hinge);
product.add(anchors.port);

product.rotation.y = -0.55;
product.rotation.x = 0.08;

// --- Auriga GLB path ---------------------------------------------------------
// Until 2026-09-10 this file did not import src/auriga-meter.js at all, so the lane's
// headline asset (a generated web-ready GLB) was unreachable from the lab page: the
// procedural shell below was the only thing anyone could ever see.
//
// Now: try the real GLB, and step the procedural stand-in aside only on success.
// On any failure the procedural shell stays and the reason is surfaced, never swallowed.
let auriga = null;

function setAssetStatus(text) {
  const el = document.getElementById('assetStatus');
  if (el) el.textContent = text;
  else console.info('[product-motion-lab]', text);
}

setAssetStatus('loading GLB…');

loadAurigaMeter({ scene: runtime.scene, url: DEFAULT_AURIGA_URL })
  .then((handle) => {
    auriga = handle;
    product.visible = false; // procedural stand-in steps aside
    setAssetStatus(
      `GLB loaded · ${handle.clips.length} clip(s) · ${handle.duration.toFixed(2)}s · ` +
      `${handle.materials.length} material(s) · anchors ${Object.keys(handle.anchors).length}/3`,
    );
    applyTimeline(timeline);
  })
  .catch((err) => {
    const why = err && err.message ? err.message : String(err);
    setAssetStatus(`GLB unavailable — procedural fallback in use (${why})`);
  });

let timeline = 0;
let playing = false;
let playStart = 0;
let calloutsVisible = true;
let frameCounter = 0;
let fpsWindowStart = performance.now();
let fps = 0;

function clamp01(v) { return Math.min(1, Math.max(0, v)); }
function segment(t, a, b) { return clamp01((t - a) / Math.max(0.0001, b - a)); }

function applyTimeline(t) {
  timeline = clamp01(t);
  slider.value = timeline.toFixed(3);
  valueOut.value = timeline.toFixed(2);
  valueOut.textContent = timeline.toFixed(2);

  const intro = segment(timeline, 0.0, 0.28);
  const open = segment(timeline, 0.28, 0.62);
  const inspect = segment(timeline, 0.62, 1.0);

  product.rotation.y = -0.55 + intro * 0.9 + inspect * 0.25;
  product.position.y = Math.sin(intro * Math.PI) * 0.12;
  top.rotation.x = -open * 1.05;
  button.rotation.x = inspect * Math.PI * 2;
  screen.material.emissive = new THREE.Color(0x19354a);
  screen.material.emissiveIntensity = 0.15 + inspect * 1.1;

  // Drive the real GLB's authored clip when it is loaded. The procedural values above
  // remain valid for the fallback path, so both branches stay coherent.
  if (auriga) auriga.applyTimeline(timeline);
}

function projectCallouts() {
  const rect = stage.getBoundingClientRect();
  const temp = new THREE.Vector3();
  // Prefer the loaded GLB's own annotation anchors; fall back to the procedural ones.
  const anchorSet = auriga ? auriga.anchors : anchors;
  for (const el of calloutEls) {
    const anchor = anchorSet[el.dataset.anchor];
    if (!anchor || !calloutsVisible) {
      el.hidden = true;
      continue;
    }
    anchor.getWorldPosition(temp);
    temp.project(runtime.camera);
    const visible = temp.z > -1 && temp.z < 1;
    el.hidden = !visible;
    if (!visible) continue;
    el.style.left = `${(temp.x * 0.5 + 0.5) * rect.width}px`;
    el.style.top = `${(-temp.y * 0.5 + 0.5) * rect.height}px`;
  }
}

function updateDiagnostics(now) {
  frameCounter += 1;
  if (now - fpsWindowStart >= 600) {
    fps = Math.round((frameCounter * 1000) / (now - fpsWindowStart));
    frameCounter = 0;
    fpsWindowStart = now;
  }
  const info = runtime.renderer.info.render;
  diagnostics.textContent = [
    `FPS ~${fps || '…'}`,
    `DPR ${runtime.renderer.getPixelRatio().toFixed(2)}`,
    `Draw calls ${info.calls}`,
    `Triangles ${info.triangles.toLocaleString()}`,
    `Timeline ${timeline.toFixed(3)}`,
  ].join('\n');
}

runtime.onFrame(({ now }) => {
  if (playing && !reducedMotion) {
    const elapsed = (now - playStart) / 4200;
    if (elapsed >= 1) {
      playing = false;
      playButton.textContent = 'Play';
      applyTimeline(1);
    } else {
      applyTimeline(elapsed);
    }
  }
  projectCallouts();
  updateDiagnostics(now);
});

slider.addEventListener('input', () => {
  playing = false;
  playButton.textContent = 'Play';
  applyTimeline(Number(slider.value));
});

playButton.addEventListener('click', () => {
  if (reducedMotion) {
    applyTimeline(timeline < 1 ? 1 : 0);
    return;
  }
  playing = !playing;
  playButton.textContent = playing ? 'Pause' : 'Play';
  if (playing) playStart = performance.now() - timeline * 4200;
});

resetButton.addEventListener('click', () => {
  playing = false;
  playButton.textContent = 'Play';
  applyTimeline(0);
});

wireframeButton.addEventListener('click', () => {
  const enabled = wireframeButton.getAttribute('aria-pressed') !== 'true';
  wireframeButton.setAttribute('aria-pressed', String(enabled));
  for (const material of materials) material.wireframe = enabled;
  if (auriga) auriga.setWireframe(enabled);
});

calloutsButton.addEventListener('click', () => {
  calloutsVisible = !calloutsVisible;
  calloutsButton.setAttribute('aria-pressed', String(calloutsVisible));
  projectCallouts();
});

if (!reducedMotion) {
  window.addEventListener('scroll', () => {
    const rect = scrollTrack.getBoundingClientRect();
    const viewport = window.innerHeight || 1;
    const start = viewport * 0.78;
    const end = -Math.max(1, rect.height - viewport * 0.2);
    const p = clamp01((start - rect.top) / Math.max(1, start - end));
    if (rect.top < start && rect.bottom > viewport * 0.1) {
      playing = false;
      playButton.textContent = 'Play';
      applyTimeline(p);
    }
  }, { passive: true });
}

applyTimeline(0);
