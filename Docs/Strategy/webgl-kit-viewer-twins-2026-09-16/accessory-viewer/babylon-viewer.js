import { DEFAULT_HERO, HEROES, heroOptions } from './catalog.js';

const viewer = document.getElementById('viewer');
const selector = document.getElementById('heroSelector');
const rotateToggle = document.getElementById('rotateToggle');
const diagnostics = document.getElementById('diagnostics');
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

const params = new URLSearchParams(window.location.search);
const queryHero = params.get('hero');
const captureMode = params.get('capture') === '1';
let currentHero = HEROES[queryHero] ? queryHero : DEFAULT_HERO;
let lastRoot = null;

heroOptions().forEach((hero) => {
  const option = document.createElement('option');
  option.value = hero.id;
  option.textContent = hero.label;
  selector.append(option);
});
selector.value = currentHero;

function heroUrl(id) {
  const hero = HEROES[id] || HEROES[DEFAULT_HERO];
  return new URL(hero.url, window.location.href).href;
}

function updateDiagnostics(extra = '') {
  const hero = HEROES[currentHero];
  diagnostics.textContent = [
    `Hero     ${hero.label}`,
    `Src      ${hero.url.split('/').pop()}`,
    `Viewer   Babylon.js Viewer 8`,
    `Engine   WebGL2`,
    `Facing   quaternion cleared, −PI/2 X, reframe`,
    `Variants separate GLBs, not KHR_materials_variants`,
    extra,
  ].filter(Boolean).join('\n');
}

function faceAtelier() {
  const details = viewer.viewerDetails;
  const scene = details?.scene;
  if (!scene) return false;
  const root = scene.getMeshByName('__root__')
    || scene.getTransformNodeByName('__root__');
  if (!root) return false;
  if (root !== lastRoot) {
    root.rotationQuaternion = null;
    root.rotation.set(-Math.PI / 2, 0, 0);
    root.computeWorldMatrix?.(true);
    scene.meshes.forEach((mesh) => mesh.computeWorldMatrix(true));
    lastRoot = root;
    viewer.removeAttribute('camera-target');
    viewer.removeAttribute('camera-orbit');
    const extents = scene.getWorldExtends((mesh) => mesh.name !== 'hdrSkyBox' && mesh.isVisible);
    const min = extents.min;
    const max = extents.max;
    const cx = (min.x + max.x) / 2;
    const cy = (min.y + max.y) / 2;
    const cz = (min.z + max.z) / 2;
    const span = Math.max(max.x - min.x, max.y - min.y, max.z - min.z);
    const radius = Math.max(span * 2.4, 0.18);
    viewer.setAttribute('camera-target', `${cx} ${cy} ${cz}`);
    viewer.setAttribute('camera-orbit', `0.42 1.22 ${radius}`);
    details.viewer?.updateCamera?.({
      alpha: 0.42,
      beta: 1.22,
      radius,
      targetX: cx,
      targetY: cy,
      targetZ: cz,
    });
  }
  return true;
}

function setHero(id) {
  const hero = HEROES[id] || HEROES[DEFAULT_HERO];
  currentHero = id in HEROES ? id : DEFAULT_HERO;
  selector.value = currentHero;
  lastRoot = null;
  viewer.setAttribute('source', heroUrl(currentHero));
  const url = new URL(window.location.href);
  url.searchParams.set('hero', currentHero);
  history.replaceState({}, '', url);
  updateDiagnostics('Status   loading');
}

selector.addEventListener('change', () => setHero(selector.value));

rotateToggle.addEventListener('click', () => {
  const on = rotateToggle.getAttribute('aria-pressed') !== 'true';
  rotateToggle.setAttribute('aria-pressed', String(on));
  if (on) viewer.setAttribute('camera-auto-orbit', '');
  else viewer.removeAttribute('camera-auto-orbit');
});

viewer.addEventListener('modelchange', () => {
  const faced = faceAtelier();
  updateDiagnostics(faced ? 'Status   loaded' : 'Status   loaded · facing pending');
});
viewer.addEventListener('viewerready', () => {
  if (faceAtelier()) updateDiagnostics('Status   loaded');
});

if (!reducedMotion && !captureMode) {
  rotateToggle.setAttribute('aria-pressed', 'true');
  viewer.setAttribute('camera-auto-orbit', '');
} else {
  rotateToggle.setAttribute('aria-pressed', 'false');
  viewer.removeAttribute('camera-auto-orbit');
}

const facePoll = window.setInterval(() => {
  if (faceAtelier()) {
    updateDiagnostics('Status   loaded');
    window.clearInterval(facePoll);
  }
}, 250);
window.setTimeout(() => window.clearInterval(facePoll), 12000);

setHero(currentHero);
