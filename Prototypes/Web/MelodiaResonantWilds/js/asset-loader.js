// Resonant Wilds: optional game-ready Higgsfield model intake.
// Uses the matching Three.js r170 official GLTFLoader; no new rendering framework.
import * as THREE from 'three';
import { GLTFLoader } from '../vendor/examples/jsm/loaders/GLTFLoader.js';
import { celMaterial, legacyRender, nprV2 } from './cel.js';
const shrineInk = new THREE.MeshBasicMaterial({ color: '#302344', side: THREE.BackSide });
function roleOf(node) {
  const label = ((node.name || '') + ' ' + (node.material?.name || '')).toLowerCase();
  if (/gold|rail|halo|orbit|lyre|crown|finial|metal/.test(label)) return 'metal';
  if (/glow|gem|crystal|resonance/.test(label)) return 'crystal';
  return 'stone';
}
function addSelectiveInk(node) {
  // Only important silhouettes. No outlines on every flower or each tiny piece.
  if (!/HERO_outer_gem|PRP_orbit_gold|PRP_foot_pearl/.test(node.name)) return;
  const hull = new THREE.Mesh(node.geometry, shrineInk);
  hull.name = 'NPR_ink_' + node.name;
  hull.userData.melodiaInk = true;
  hull.scale.setScalar(1.055);
  node.add(hull);
}

let shrinePromise;
function shrineTemplate() {
  if (!shrinePromise) {
    const url = new URL('../assets/models/resonance-shrine.glb', import.meta.url).href;
    shrinePromise = new GLTFLoader().loadAsync(url).then(({ scene }) => {
      if (!scene) throw new Error('GLB has no scene');
      scene.traverse((node) => {
        if (!node.isMesh || node.userData.melodiaInk) return;
        const m = node.material;
        // Preserve author-assigned colour, alpha and emission. Reintroduce lighting
        // in Three.js, not as Blender-baked PBR/preview studio illumination.
        if (m && !legacyRender) {
          node.material = celMaterial(m.color?.clone() || new THREE.Color('#ffffff'), {
            map: m.map ?? null,
            transparent: m.transparent,
            opacity: m.opacity,
            side: m.side,
            emissive: m.emissive?.clone() || new THREE.Color('#000000'),
            emissiveIntensity: m.emissiveIntensity ?? 1,
            nprRole: roleOf(node),
          });
        }
        if (nprV2) addSelectiveInk(node);
      });
      scene.name = 'ResonanceShrine_P0';
      return scene;
    }).catch((err) => { shrinePromise = null; throw err; });
  }
  return shrinePromise;
}

export async function attachShrineVisual(group, poi) {
  try {
    const template = await shrineTemplate();
    // A POI can be disposed before the network request finishes.
    if (!group.parent) return false;
    const model = template.clone(true);
    model.name = 'GLB_ResonanceShrine';
    const procedural = group.children.slice();
    group.add(model);
    procedural.forEach((child) => { child.visible = false; });
    poi.assetVisual = model;
    return true;
  } catch (err) {
    console.warn('Resonant Wilds: shrine GLB failed; keeping procedural fallback', err);
    return false;
  }
}
