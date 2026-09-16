// Fabric Material Lab — clean-room Three.js textile study.
//
// Every texture used here is procedurally generated and owner-authored
// (BS_GodFile/Content/Python/author_fantasy_fabrics.py). Preset identities are
// deliberately neutral — "velvet-like", not a brand or product name — so nothing
// in this demo carries third-party or project-specific IP. See
// ../../fabric/MATERIAL_PROVENANCE_MANIFEST.json for the classification.

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Presets. Neutral identities mapped onto owner-authored generated texture sets.
// ---------------------------------------------------------------------------
const DIR = './assets/textiles/';
const TEX = DIR + 'T_Fabric_';
const PRESETS = [
  { id: 'velvet-like',      label: 'Velvet-like',      kind: 'pile / dual-sheen', base: 'RoyalVelvet',    sheen: 'T_Fabric_RoyalVelvet_Sheen.png',    rough: 0.85, metal: 0.02 },
  { id: 'satin-like',       label: 'Satin-like',       kind: 'fine weave',        base: 'SheerSilk',      sheen: 'T_Fabric_SheerSilk_Sheen.png',      rough: 0.42, metal: 0.05 },
  { id: 'brocade-like',     label: 'Brocade-like',     kind: 'raised jacquard',   base: 'GildedBrocade',  sheen: null,                                rough: 0.55, metal: 0.35 },
  { id: 'lace-like',        label: 'Lace-like',        kind: 'openwork tracery',  base: 'BaroqueLace',    sheen: null,                                rough: 0.70, metal: 0.04 },
  { id: 'embroidered-like', label: 'Embroidered-like', kind: 'raised bullion',    base: 'GoldEmbroidery', sheen: null,                                rough: 0.48, metal: 0.55 },
  { id: 'iridescent-like',  label: 'Iridescent-like',  kind: 'view-shift weave',  base: 'CelestialWeave', sheen: null,                                rough: 0.38, metal: 0.25 },
];

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const canvas = document.getElementById('c');
const diagEl = document.getElementById('diag');
const stateEl = document.getElementById('state');
const pPreset = document.getElementById('p-preset');
const pLight = document.getElementById('p-light');

// ---- state -----------------------------------------------------------------
const state = {
  preset: PRESETS[0].id,
  tint: '#ffffff',
  roughnessScale: 1,
  normalScale: 1,
  sheenScale: 1,
  grazing: false,
  wireframe: false,
  turntable: !reduceMotion,
};

let renderer, scene, camera, mesh, material, group;
let roughTex = null, normTex = null, bcTex = null, sheenTex = null;
let frames = 0, lastFpsAt = performance.now(), fps = 0;
let loadedBytes = 0;

// ---- graceful failure ------------------------------------------------------
function fail(msg) {
  const f = document.getElementById('fallback');
  f.style.display = 'grid';
  f.textContent = msg;
  diagEl.textContent = 'WebGL unavailable';
}

// ---- geometry: a draped cloth panel (procedural, owned) ---------------------
function makeCloth() {
  const g = new THREE.PlaneGeometry(2.6, 2.2, 150, 130);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    // two sine folds plus a subtle edge curl - deterministic, no noise library
    const fold = Math.sin(x * 3.1) * 0.085 + Math.sin(x * 7.3 + y * 1.4) * 0.028;
    const curl = Math.pow(Math.abs(x) / 1.3, 3) * 0.16;
    const sag = Math.cos(y * 1.15) * 0.05;
    p.setZ(i, fold + curl - sag);
  }
  g.computeVertexNormals();
  return g;
}

// ---- lighting rigs ---------------------------------------------------------
function buildLights(grazing) {
  const grp = new THREE.Group();
  if (grazing) {
    // near-tangent light: the rig that reveals roughness and normal response
    const k = new THREE.DirectionalLight(0xffffff, 3.4);
    k.position.set(-3.4, 0.42, 1.5);
    grp.add(k);
    grp.add(new THREE.AmbientLight(0xffffff, 0.16));
    const rim = new THREE.DirectionalLight(0x9fb6ff, 0.7);
    rim.position.set(3, 0.2, -2.4);
    grp.add(rim);
  } else {
    const k = new THREE.DirectionalLight(0xffffff, 2.1);
    k.position.set(2.6, 3.6, 3.2);
    grp.add(k);
    const fill = new THREE.DirectionalLight(0xbfd0ff, 0.75);
    fill.position.set(-3.2, 1.2, 1.6);
    grp.add(fill);
    grp.add(new THREE.AmbientLight(0xffffff, 0.28));
  }
  return grp;
}

// ---- texture loading -------------------------------------------------------
function loadTex(url, colorSpace, repeat) {
  return new Promise((resolve) => {
    if (!url) return resolve(null);
    new THREE.TextureLoader().load(
      url,
      (t) => {
        t.wrapS = t.wrapT = THREE.RepeatWrapping;
        t.repeat.set(repeat, repeat);
        t.anisotropy = 4;
        if (colorSpace) t.colorSpace = colorSpace;
        fetch(url, { method: 'HEAD' }).then((r) => {
          const n = Number(r.headers.get('content-length') || 0);
          loadedBytes += n;
        }).catch(() => {});
        resolve(t);
      },
      undefined,
      () => resolve(null),
    );
  });
}

async function applyPreset(id) {
  const def = PRESETS.find((p) => p.id === id) || PRESETS[0];
  state.preset = def.id;
  pPreset.textContent = def.label;

  // dispose previous
  [roughTex, normTex, bcTex, sheenTex].forEach((t) => t && t.dispose());

  const rep = def.base === 'BaroqueLace' ? 2.2 : 1.6;
  [bcTex, normTex, roughTex, sheenTex] = await Promise.all([
    loadTex(`${TEX}${def.base}_BC.png`, THREE.SRGBColorSpace, rep),
    loadTex(`${TEX}${def.base}_N.png`, THREE.NoColorSpace, rep),
    loadTex(`${TEX}${def.base}_ORM.png`, THREE.NoColorSpace, rep),
    loadTex(def.sheen ? DIR + def.sheen : null, THREE.NoColorSpace, rep),
  ]);

  if (!material) {
    material = new THREE.MeshPhysicalMaterial({ side: THREE.DoubleSide, clearcoat: 0.35, clearcoatRoughness: 0.42 });
    mesh = new THREE.Mesh(makeCloth(), material);
    mesh.rotation.x = -0.18;
    group.add(mesh);
  }

  material.map = bcTex;
  material.normalMap = normTex;
  material.roughnessMap = roughTex;
  material.metalnessMap = roughTex;
  material.aoMap = roughTex;
  material.baseRoughness = def.rough;
  material.baseMetalness = def.metal;

  if (sheenTex && material.sheen !== undefined) {
    material.sheenColorMap = sheenTex;
    material.sheen = 0.6;
    material.sheenRoughness = 0.35;
  } else if (material.sheen !== undefined) {
    material.sheenColorMap = null;
    material.sheen = def.base === 'RoyalVelvet' ? 0.45 : 0.0;
  }
  refreshMaterial();
}

function refreshMaterial() {
  if (!material) return;
  material.color = new THREE.Color(state.tint);
  material.roughness = THREE.MathUtils.clamp((material.baseRoughness || 0.6) * state.roughnessScale, 0.02, 1);
  material.metalness = THREE.MathUtils.clamp(material.baseMetalness || 0.05, 0, 1);
  const ns = new THREE.Vector2(state.normalScale, state.normalScale);
  material.normalScale = ns;
  if (material.sheen !== undefined && material.sheen > 0) {
    material.sheen = THREE.MathUtils.clamp(material.sheen * state.sheenScale, 0, 1);
  }
  material.wireframe = state.wireframe;
  material.needsUpdate = true;
  renderState();
}

function renderState() {
  const def = PRESETS.find((p) => p.id === state.preset);
  stateEl.textContent = JSON.stringify({
    preset: state.preset,
    textileKind: def ? def.kind : null,
    tint: state.tint,
    roughnessScale: Number(state.roughnessScale.toFixed(2)),
    normalScale: Number(state.normalScale.toFixed(2)),
    sheenScale: Number(state.sheenScale.toFixed(2)),
    grazingInspection: state.grazing,
    wireframe: state.wireframe,
    source: 'owner-authored procedural textures',
  }, null, 1);
}

// ---- boot ------------------------------------------------------------------
function init() {
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  } catch (e) {
    return fail('WebGL could not start on this device.');
  }
  if (!renderer.getContext()) return fail('WebGL could not start on this device.');

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0c0d12);

  camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 0.25, 4.4);
  camera.lookAt(0, 0, 0);

  group = new THREE.Group();
  scene.add(group);
  scene.add(buildLights(state.grazing));

  // preset buttons
  const host = document.getElementById('presets');
  PRESETS.forEach((p) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'preset';
    b.setAttribute('aria-pressed', String(p.id === state.preset));
    b.innerHTML = `<span>${p.label}</span><span class="kind">${p.kind}</span>`;
    b.addEventListener('click', () => {
      host.querySelectorAll('.preset').forEach((x) => x.setAttribute('aria-pressed', 'false'));
      b.setAttribute('aria-pressed', 'true');
      applyPreset(p.id);
    });
    host.appendChild(b);
  });

  // controls
  const bindRange = (id, key, outId, fmt) => {
    const el = document.getElementById(id);
    const out = document.getElementById(outId);
    el.addEventListener('input', () => {
      state[key] = parseFloat(el.value);
      out.textContent = fmt(state[key]);
      refreshMaterial();
    });
  };
  bindRange('rough', 'roughnessScale', 'v-rough', (v) => v.toFixed(2) + '×');
  bindRange('normal', 'normalScale', 'v-normal', (v) => v.toFixed(2) + '×');
  bindRange('sheen', 'sheenScale', 'v-sheen', (v) => v.toFixed(2) + '×');

  const tint = document.getElementById('tint');
  tint.addEventListener('input', () => {
    state.tint = tint.value;
    document.getElementById('v-tint').textContent = tint.value;
    refreshMaterial();
  });

  const toggle = (id, key, onAfter) => {
    const b = document.getElementById(id);
    b.addEventListener('click', () => {
      state[key] = !state[key];
      b.setAttribute('aria-pressed', String(state[key]));
      if (onAfter) onAfter();
    });
  };
  toggle('b-wire', 'wireframe', refreshMaterial);
  toggle('b-spin', 'turntable');
  toggle('b-light', 'grazing', () => {
    scene.remove(scene.children.find((o) => o.isGroup && o !== group));
    scene.add(buildLights(state.grazing));
    pLight.textContent = 'lighting: ' + (state.grazing ? 'grazing' : 'studio');
  });

  document.getElementById('b-reset').addEventListener('click', () => {
    tint.value = '#ffffff';
    document.getElementById('v-tint').textContent = '#ffffff';
    ['rough', 'normal', 'sheen'].forEach((k, i) => {
      const el = document.getElementById(k);
      el.value = '1';
      document.getElementById(['v-rough', 'v-normal', 'v-sheen'][i]).textContent = '1.00×';
    });
    state.tint = '#ffffff';
    state.roughnessScale = state.normalScale = state.sheenScale = 1;
    state.grazing = false; state.wireframe = false;
    document.getElementById('b-light').setAttribute('aria-pressed', 'false');
    document.getElementById('b-wire').setAttribute('aria-pressed', 'false');
    refreshMaterial();
  });

  document.getElementById('b-copy').addEventListener('click', () => {
    navigator.clipboard && navigator.clipboard.writeText(stateEl.textContent);
  });

  if (reduceMotion) document.getElementById('b-spin').setAttribute('aria-pressed', 'false');

  // resize + render loop
  const resize = () => {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / r.height;
    camera.updateProjectionMatrix();
  };
  window.addEventListener('resize', resize);
  resize();

  let t = 0;
  const tick = () => {
    requestAnimationFrame(tick);
    if (state.turntable) { t += 0.004; group.rotation.y = t; }
    renderer.render(scene, camera);

    frames++;
    const now = performance.now();
    if (now - lastFpsAt >= 500) {
      fps = Math.round((frames * 1000) / (now - lastFpsAt));
      frames = 0; lastFpsAt = now;
      const info = renderer.info;
      diagEl.innerHTML =
        `FPS ~<b>${fps}</b> · DPR <b>${(renderer.getPixelRatio()).toFixed(2)}</b> · ` +
        `draw calls <b>${info.render.calls}</b> · triangles <b>${info.render.triangles.toLocaleString()}</b>` +
        (loadedBytes ? ` · textures <b>${(loadedBytes / 1048576).toFixed(2)} MB</b>` : '');
    }
  };
  tick();

  applyPreset(state.preset);
  renderState();
}

init();
