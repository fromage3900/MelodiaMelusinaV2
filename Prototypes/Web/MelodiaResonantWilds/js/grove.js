// Three lightweight Harmonic Grove asset families, using existing r170 GLTFLoader.
// Never modifies biome scatter seeds, collisions, rhythm, saves or POI keepouts.
import * as THREE from 'three';
import { GLTFLoader } from '../vendor/examples/jsm/loaders/GLTFLoader.js';
import { mergeGeometries } from '../vendor/examples/jsm/utils/BufferGeometryUtils.js';
import { celMaterial } from './cel.js';
import { GROVE_NAMES, GROVE_ALL_NAMES, GROVE_DECORATIVE_VARIANTS, GROVE_HEIGHTS, GROVE_INTERACTIVE } from './grove-catalog.js';

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

// Exact release list, including all 63 optional GLBs. Non-scatter assets
// (INT_/PICK_) must be requested explicitly by a POI; never appear as random terrain.
const allNames = new Set(GROVE_ALL_NAMES);
const bundledNames = new Set(GROVE_NAMES);
const partPromises = new Map();
export function groveCatalog() {
  return { total: allNames.size, interactive: [...GROVE_INTERACTIVE], extras: allNames.size - bundledNames.size };
}
export function loadGroveParts(name, height = 1.5) {
  if (!allNames.has(name)) return Promise.reject(new Error('Unknown authored Grove asset: ' + name));
  const key = name + ':' + height;
  if (!partPromises.has(key)) {
    const promise = (async () => {
      let root;
      if (bundledNames.has(name)) {
        root = (await sceneTemplate()).getObjectByName('ASSET_' + name);
      } else {
        const file = name.toLowerCase() + '.glb';
        const url = new URL('../assets/models/' + file, import.meta.url);
        const scene = (await new GLTFLoader().loadAsync(url.href)).scene;
        root = scene?.getObjectByName('ASSET_' + name);
      }
      if (!root) throw new Error('Authored Grove anchor missing: ' + name);
      // A missing optional asset is isolated to its own Promise.
      return buildParts(root, { height, maxParts: 12 });
    })().catch(e => { partPromises.delete(key); throw e; });
    partPromises.set(key, promise);
  }
  return partPromises.get(key);
}
// A later interaction system can request a named waypoint/pickup without
// changing the authoritative placement, inventory, combat or save contracts.
export async function loadGroveVisual(name, { height = 1.5 } = {}) {
  const parts = await loadGroveParts(name, height);
  const group = new THREE.Group();
  group.name = 'GLB_' + name;
  for (const part of parts) {
    const mesh = new THREE.Mesh(part.geo, part.mat);
    mesh.matrix.copy(part.m);
    mesh.matrixAutoUpdate = false;
    group.add(mesh);
  }
  return group;
}
export async function installGroveProps(world, { full = false } = {}) {
  if (!world?.props) throw new Error('World prop library missing');
  const kit = await sceneTemplate();
  const staged = {};
  for (const [type, spec] of Object.entries(GROVE_SELECTION)) {
    if (type === 'flower' && !world.flowerbedsEnabled) continue;
    const root = kit.getObjectByName(spec.root);
    if (!root) throw new Error('Missing Harmonic Grove asset: ' + spec.root);
    staged[type] = buildParts(root, spec);
  }
  // Atomic upgrade of the original three GLB families (legacy ?grove=glb).
  for (const [type, parts] of Object.entries(staged)) {
    world.props[type] = { ...world.props[type], parts, tint: -1 };
  }
  world.groveStatus = 'glb';
  world.groveCounts = Object.fromEntries(Object.entries(staged).map(([type, p]) => [type, p.length]));
  if (!full) return world.groveCounts;

  // Curated deterministic visual variations across biomes. Only the catalog's
  // safe decorative subset is scattered. Other assets remain available by name.
  // Limit each terrain type to TWO variants for predictable mobile draw calls.
  const variants = {};
  const failures = [];
  for (const [type, names] of Object.entries(GROVE_DECORATIVE_VARIANTS)) {
    if (!world.props[type] || (type === 'flower' && !world.flowerbedsEnabled)) continue;
    const results = await Promise.allSettled(names.slice(0, 2).map(name =>
      loadGroveParts(name, GROVE_HEIGHTS[type]).then(parts => ({ name, parts }))));
    variants[type] = results.flatMap((r, i) => r.status === 'fulfilled'
      ? [{ ...world.props[type], ...r.value, tint: -1, palette: null, rockTint: false }]
      : (failures.push(names[i]), []));
  }
  world.groveVariants = variants;
  world.groveStatus = 'full';
  world.groveCatalogSize = allNames.size;
  world.groveActiveVariants = Object.values(variants).reduce((n, a) => n + a.length, 0);
  world.groveMissingOptional = failures;
  return world.groveCounts;
}
