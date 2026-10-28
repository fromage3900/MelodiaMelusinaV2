// Three lightweight Harmonic Grove asset families, using existing r170 GLTFLoader.
// Never modifies biome scatter seeds, collisions, rhythm, saves or POI keepouts.
import * as THREE from 'three';
import { GLTFLoader } from '../vendor/examples/jsm/loaders/GLTFLoader.js';
import { mergeGeometries } from '../vendor/examples/jsm/utils/BufferGeometryUtils.js';
import { celMaterial } from './cel.js';

export const GROVE_SELECTION = Object.freeze({
  flower: { root: 'ASSET_FLR_bellflower_dwarf', height: 0.82, maxParts: 5 },
  bush: { root: 'ASSET_FLR_moonfern_young', height: 1.10, maxParts: 3 },
  grass: { root: 'ASSET_FLR_short_grass', height: 0.64, maxParts: 2 },
});
let cached;
async function sceneTemplate() {
  if (!cached) {
    const url = new URL('../assets/models/harmonic-grove-37.glb', import.meta.url).href;
    cached = new GLTFLoader().loadAsync(url).then(({scene}) => {
      if (!scene) throw new Error('Harmonic Grove has no scene');
      scene.updateMatrixWorld(true);
      return scene;
    }).catch(e => { cached = null; throw e; });
  }
  return cached;
}
// Flatten the original showroom's per-object transforms into geometry in
// asset-local space and merge by material to prevent 533 individual draw calls.
function buildParts(root, spec) {
  root.updateWorldMatrix(true, true);
  const inverse = root.matrixWorld.clone().invert(), groups = new Map();
  root.traverse(obj => {
    if (!obj.isMesh || !obj.geometry?.attributes?.position) return;
    if (Array.isArray(obj.material)) throw new Error(root.name + ': multi-material primitives unsupported');
    const key = obj.material?.name || 'unnamed';
    const mat = inverse.clone().multiply(obj.matrixWorld);
    let geo = obj.geometry.index ? obj.geometry.toNonIndexed() : obj.geometry.clone();
    for (const a of Object.keys(geo.attributes)) if (a !== 'position' && a !== 'normal') geo.deleteAttribute(a);
    if (!geo.attributes.normal) geo.computeVertexNormals();
    geo.applyMatrix4(mat);
    if (!groups.has(key)) groups.set(key, { material: obj.material, geometries: [] });
    groups.get(key).geometries.push(geo);
  });
  if (!groups.size || groups.size > spec.maxParts) throw new Error(root.name + ': material group budget exceeded');
  const merged = [];
  for (const [name, entry] of groups) {
    const geo = mergeGeometries(entry.geometries, false);
    entry.geometries.forEach(g => g.dispose());
    if (!geo) throw new Error(root.name + ': failed merging ' + name);
    merged.push({ geo, material: entry.material });
  }
  const box = new THREE.Box3();
  for (const part of merged) { part.geo.computeBoundingBox(); box.union(part.geo.boundingBox); }
  const h = box.max.y - box.min.y;
  if (!Number.isFinite(h) || h < 0.01) throw new Error(root.name + ': invalid source dimensions');
  const cx = (box.min.x + box.max.x) * 0.5, cz = (box.min.z + box.max.z) * 0.5;
  const scale = spec.height / h;
  return merged.map(({ geo, material: source }) => {
    geo.translate(-cx, -box.min.y, -cz);
    geo.scale(scale, scale, scale);
    geo.computeBoundingSphere();
    return {
      geo,
      mat: celMaterial(source?.color?.clone() || new THREE.Color('#ffffff'), {
        emissive: source?.emissive?.clone() || new THREE.Color('#000000'),
        emissiveIntensity: source?.emissiveIntensity ?? 1,
        transparent: !!source?.transparent,
        opacity: source?.opacity ?? 1,
        side: THREE.DoubleSide,
      }),
      m: new THREE.Matrix4(),
    };
  });
}
export async function installGroveProps(world) {
  if (!world?.props) throw new Error('World prop library missing');
  const kit = await sceneTemplate();
  const staged = {};
  // Stage every family before changing any live props; a failed model download
  // leaves all original authored flowerbeds and procedural foliage untouched.
  for (const [type, spec] of Object.entries(GROVE_SELECTION)) {
    if (type === 'flower' && !world.flowerbedsEnabled) continue;
    const root = kit.getObjectByName(spec.root);
    if (!root) throw new Error('Missing Harmonic Grove asset: ' + spec.root);
    staged[type] = buildParts(root, spec);
  }
  for (const [type, parts] of Object.entries(staged)) {
    // Preserve palette array to preserve RNG call count and placement order;
    // neutral instanced tint (-1) retains the GLB's original enamel material colours.
    world.props[type] = { ...world.props[type], parts, tint: -1 };
  }
  world.groveStatus = 'glb';
  world.groveCounts = Object.fromEntries(Object.entries(staged).map(([type, p]) => [type, p.length]));
  return world.groveCounts;
}
