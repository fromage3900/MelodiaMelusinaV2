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

heroOptions().forEach((hero) => {
  const option = document.createElement('option');
  option.value = hero.id;
  option.textContent = hero.label;
  selector.append(option);
});
selector.value = currentHero;

function setHero(id) {
  const hero = HEROES[id] || HEROES[DEFAULT_HERO];
  currentHero = id in HEROES ? id : DEFAULT_HERO;
  selector.value = currentHero;
  viewer.src = hero.url;
  viewer.alt = `${hero.label} — original eyewear study`;
  const url = new URL(window.location.href);
  url.searchParams.set('hero', currentHero);
  history.replaceState({}, '', url);
  updateDiagnostics('Loading…');
}

function updateDiagnostics(extra = '') {
  const hero = HEROES[currentHero];
  diagnostics.textContent = [
    `Hero     ${hero.label}`,
    `Src      ${hero.url.split('/').pop()}`,
    `Viewer   Google model-viewer 4.0`,
    `Tone     commerce (Khronos PBR Neutral)`,
    `AR       webxr / scene-viewer (no USDZ)`,
    `Variants separate GLBs, not KHR_materials_variants`,
    extra,
  ].filter(Boolean).join('\n');
}

selector.addEventListener('change', () => setHero(selector.value));

rotateToggle.addEventListener('click', () => {
  const on = rotateToggle.getAttribute('aria-pressed') !== 'true';
  rotateToggle.setAttribute('aria-pressed', String(on));
  if (on) viewer.setAttribute('auto-rotate', '');
  else viewer.removeAttribute('auto-rotate');
});

viewer.addEventListener('load', () => {
  updateDiagnostics('Status   loaded');
});
viewer.addEventListener('error', (event) => {
  updateDiagnostics(`Status   error · ${event.detail?.type || 'failed'}`);
});

if (!reducedMotion && !captureMode) {
  rotateToggle.setAttribute('aria-pressed', 'true');
  viewer.setAttribute('auto-rotate', '');
}

setHero(currentHero);
