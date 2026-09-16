import { DEFAULT_HERO, HEROES, heroOptions } from './catalog.js';
import { babylon as bjs, modelViewer as mv } from './viewer-contract.js';

const stage = document.getElementById('stage');
const googleViewer = document.getElementById('googleViewer');
const selector = document.getElementById('heroSelector');
const rotateToggle = document.getElementById('rotateToggle');
const diagnostics = document.getElementById('diagnostics');
const engineButtons = [...document.querySelectorAll('[data-engine]')];
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

const params = new URLSearchParams(window.location.search);
const queryHero = params.get('hero');
const captureMode = params.get('capture') === '1';
const ENGINES = new Set(['google', 'babylon']);
let currentHero = HEROES[queryHero] ? queryHero : DEFAULT_HERO;
let currentEngine = ENGINES.has(params.get('engine')) ? params.get('engine') : 'google';
let babylonViewer = null;
let babylonRoot = null;
let autoRotate = !reducedMotion && !captureMode;

heroOptions().forEach((hero) => {
  const option = document.createElement('option');
  option.value = hero.id;
  option.textContent = hero.label;
  selector.append(option);
});
selector.value = currentHero;

googleViewer.setAttribute('orientation', mv.orientation);
googleViewer.setAttribute('camera-orbit', mv.orbit);
googleViewer.setAttribute('camera-target', mv.target);
googleViewer.setAttribute('field-of-view', mv.fov);

function heroUrl(id) {
  const hero = HEROES[id] || HEROES[DEFAULT_HERO];
  return new URL(hero.url, window.location.href).href;
}

function writeUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set('hero', currentHero);
  url.searchParams.set('engine', currentEngine);
  if (captureMode) url.searchParams.set('capture', '1');
  history.replaceState({}, '', url);
}

function updateDiagnostics(extra = '') {
  const hero = HEROES[currentHero];
  diagnostics.textContent = [
    `Hero     ${hero.label}`,
    `Src      ${hero.url.split('/').pop()}`,
    `Engine   ${currentEngine === 'babylon' ? 'Babylon.js Viewer 8' : 'Google model-viewer 4.0'}`,
    `Camera   ${currentEngine === 'babylon' ? '24° / 74° span-relative' : mv.orbit}`,
    `Facing   ${mv.orientation} / root X −PI/2`,
    `AR       ${currentEngine === 'google' ? 'webxr / scene-viewer (no USDZ)' : 'n/a on this engine'}`,
    `Variants separate GLBs, not KHR_materials_variants`,
    extra,
  ].filter(Boolean).join('\n');
}

function applyGoogle() {
  const hero = HEROES[currentHero];
  googleViewer.src = hero.url;
  googleViewer.alt = `${hero.label} — original eyewear study`;
  if (autoRotate) googleViewer.setAttribute('auto-rotate', '');
  else googleViewer.removeAttribute('auto-rotate');
}

function faceBabylon() {
  const details = babylonViewer?.viewerDetails;
  const scene = details?.scene;
  if (!scene) return false;
  const root = scene.getMeshByName('__root__') || scene.getTransformNodeByName('__root__');
  if (!root) return false;
  if (root !== babylonRoot) {
    root.rotationQuaternion = null;
    root.rotation.set(bjs.rootRotationX, 0, 0);
    root.computeWorldMatrix?.(true);
    scene.meshes.forEach((mesh) => mesh.computeWorldMatrix(true));
    babylonRoot = root;
    const extents = scene.getWorldExtends((mesh) => mesh.name !== 'hdrSkyBox' && mesh.isVisible);
    const min = extents.min;
    const max = extents.max;
    const target = {
      x: (min.x + max.x) / 2,
      y: (min.y + max.y) / 2,
      z: (min.z + max.z) / 2,
    };
    const span = Math.max(max.x - min.x, max.y - min.y, max.z - min.z);
    const radius = Math.max(span * bjs.radiusOverSpan, bjs.minRadius);
    const camera = scene.activeCamera;
    if (camera) {
      camera.alpha = bjs.alpha;
      camera.beta = bjs.beta;
      camera.radius = radius;
      camera.target?.set?.(target.x, target.y, target.z);
    }
    babylonViewer.setAttribute('camera-orbit', `${bjs.alpha} ${bjs.beta} ${radius}`);
    babylonViewer.setAttribute('camera-target', `${target.x} ${target.y} ${target.z}`);
    details.viewer?.updateCamera?.({
      alpha: bjs.alpha,
      beta: bjs.beta,
      radius,
      targetX: target.x,
      targetY: target.y,
      targetZ: target.z,
    });
  }
  return true;
}

async function ensureBabylon() {
  if (babylonViewer) return babylonViewer;
  if (!customElements.get('babylon-viewer')) {
    await import('https://cdn.jsdelivr.net/npm/@babylonjs/viewer@8.29.1/dist/babylon-viewer.esm.min.js');
  }
  babylonViewer = document.createElement('babylon-viewer');
  babylonViewer.id = 'babylonViewer';
  babylonViewer.setAttribute('engine', 'WebGL2');
  babylonViewer.setAttribute('environment-lighting', 'auto');
  babylonViewer.addEventListener('modelchange', () => {
    const faced = faceBabylon();
    updateDiagnostics(faced ? 'Status   loaded' : 'Status   loaded · facing pending');
  });
  stage.append(babylonViewer);
  return babylonViewer;
}

async function applyBabylon() {
  babylonRoot = null;
  const viewer = await ensureBabylon();
  if (autoRotate) viewer.setAttribute('camera-auto-orbit', '');
  else viewer.removeAttribute('camera-auto-orbit');
  viewer.setAttribute('source', heroUrl(currentHero));
  const poll = window.setInterval(() => {
    if (faceBabylon()) {
      updateDiagnostics('Status   loaded');
      window.clearInterval(poll);
    }
  }, 250);
  window.setTimeout(() => window.clearInterval(poll), 12000);
}

function showEngine(engine) {
  currentEngine = ENGINES.has(engine) ? engine : 'google';
  const googleOn = currentEngine === 'google';
  googleViewer.hidden = !googleOn;
  if (babylonViewer) babylonViewer.hidden = googleOn;
  engineButtons.forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.engine === currentEngine));
  });
}

async function setHero(id) {
  currentHero = id in HEROES ? id : DEFAULT_HERO;
  selector.value = currentHero;
  writeUrl();
  updateDiagnostics('Status   loading');
  if (currentEngine === 'babylon') await applyBabylon();
  else applyGoogle();
}

async function setEngine(engine) {
  showEngine(engine);
  writeUrl();
  updateDiagnostics('Status   loading');
  if (currentEngine === 'babylon') await applyBabylon();
  else applyGoogle();
}

selector.addEventListener('change', () => setHero(selector.value));
engineButtons.forEach((button) => {
  button.addEventListener('click', () => setEngine(button.dataset.engine));
});

rotateToggle.addEventListener('click', () => {
  autoRotate = rotateToggle.getAttribute('aria-pressed') !== 'true';
  rotateToggle.setAttribute('aria-pressed', String(autoRotate));
  if (currentEngine === 'babylon') {
    if (autoRotate) babylonViewer?.setAttribute('camera-auto-orbit', '');
    else babylonViewer?.removeAttribute('camera-auto-orbit');
  } else if (autoRotate) googleViewer.setAttribute('auto-rotate', '');
  else googleViewer.removeAttribute('auto-rotate');
});

googleViewer.addEventListener('load', () => {
  if (currentEngine === 'google') updateDiagnostics('Status   loaded');
});
googleViewer.addEventListener('error', (event) => {
  if (currentEngine === 'google') {
    updateDiagnostics(`Status   error · ${event.detail?.type || 'failed'}`);
  }
});

rotateToggle.setAttribute('aria-pressed', String(autoRotate));
showEngine(currentEngine);
setHero(currentHero);
