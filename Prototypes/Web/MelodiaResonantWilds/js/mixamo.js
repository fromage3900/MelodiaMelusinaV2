// Opt-in Mixamo hero avatar (`?avatar=mixamo`).
// Uses the Three.js r170 Soldier.glb (Mixamo-rigged) via the vendored GLTFLoader.
// Presentation only — procedural Melusina remains the default fallback.

import * as THREE from 'three';
import { GLTFLoader } from '../vendor/examples/jsm/loaders/GLTFLoader.js';
import { blob } from './entities.js';
import { toon } from './entities.js';

const MIXAMO_URL = new URL('../assets/models/mixamo-hero.glb', import.meta.url).href;

let mixamoPromise = null;

function loadMixamoGltf() {
  if (!mixamoPromise) {
    mixamoPromise = new GLTFLoader().loadAsync(MIXAMO_URL).catch((err) => {
      mixamoPromise = null;
      throw err;
    });
  }
  return mixamoPromise;
}

function pickClip(clips, ...names) {
  const lower = names.map((n) => n.toLowerCase());
  return clips.find((c) => lower.some((n) => c.name.toLowerCase().includes(n))) || clips[0] || null;
}

/**
 * Build a Melusina-shaped avatar API backed by a Mixamo skinned mesh + mixer.
 * Returns null on failure so the caller keeps the procedural body.
 */
export async function buildMixamoAvatar() {
  const gltf = await loadMixamoGltf();
  const root = gltf.scene || gltf.scenes?.[0];
  if (!root) throw new Error('Mixamo GLB has no scene');

  const group = new THREE.Group();
  group.name = 'MixamoHero';
  const model = root.clone(true);
  // Soldier is ~1.7m Y-up; nudge to Melusina scale / footing.
  model.scale.setScalar(1.15);
  model.position.y = 0;
  model.rotation.y = Math.PI; // face +Z like procedural Melusina default facing
  group.add(model);

  const mixer = new THREE.AnimationMixer(model);
  const clips = gltf.animations || [];
  const idleClip = pickClip(clips, 'idle', 'stand');
  const walkClip = pickClip(clips, 'walk');
  const runClip = pickClip(clips, 'run');
  const actions = {
    idle: idleClip ? mixer.clipAction(idleClip) : null,
    walk: walkClip ? mixer.clipAction(walkClip) : null,
    run: runClip ? mixer.clipAction(runClip) : null,
  };
  for (const a of Object.values(actions)) {
    if (!a) continue;
    a.enabled = true;
    a.setEffectiveTimeScale(1);
    a.setEffectiveWeight(1);
    a.play();
  }
  let current = 'idle';
  if (actions.idle) actions.idle.play();
  if (actions.walk) { actions.walk.play(); actions.walk.setEffectiveWeight(0); }
  if (actions.run) { actions.run.play(); actions.run.setEffectiveWeight(0); }

  // Wardrobe dress() stubs — tint a primary mesh when gown changes.
  let gownMat = null;
  model.traverse((n) => {
    if (!n.isMesh || gownMat) return;
    if (n.material) {
      const m = Array.isArray(n.material) ? n.material[0] : n.material;
      if (m && m.color) gownMat = m;
    }
  });
  if (!gownMat) gownMat = toon('#bda8df');

  const crown = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.04, 6, 12), toon('#ffd978', { emissive: '#d9bc72', emissiveIntensity: 0.3 }));
  crown.position.set(0, 1.95, 0); crown.rotation.x = Math.PI / 2; crown.visible = false;
  group.add(crown);
  const shoes = new THREE.Object3D(); shoes.visible = false;
  const lyre = new THREE.Object3D(); lyre.visible = true;
  const baton = new THREE.Object3D(); baton.visible = false;
  const inst = new THREE.Group();
  const instMat = toon('#ffe7a8', { emissive: '#ffcf6a', emissiveIntensity: 0.35 });
  const body = group;
  const shadow = blob(0.9);

  function crossfade(next, dtFade = 0.22) {
    if (next === current || !actions[next]) return;
    const from = actions[current];
    const to = actions[next];
    if (to) to.reset().setEffectiveWeight(1).fadeIn(dtFade).play();
    if (from) from.fadeOut(dtFade);
    current = next;
  }

  function pose(dt, _time, state = {}) {
    mixer.update(dt);
    const speed = state.speed || 0;
    if (speed > 0.72 && actions.run) crossfade('run');
    else if (speed > 0.12 && actions.walk) crossfade('walk');
    else if (actions.idle) crossfade('idle');
    // Light squash on dodge / hurt without fighting the skeleton.
    const stretch = state.stretch || 1;
    group.scale.set(1 / Math.sqrt(stretch), stretch, 1 / Math.sqrt(stretch));
  }

  return {
    group, body, gownMat, hairMat: gownMat, crown, shoes, inst, instMat, lyre, baton, shadow,
    pose, mixer, mixamo: true,
  };
}

export function mixamoOptIn() {
  return new URLSearchParams(window.location.search).get('avatar') === 'mixamo';
}
