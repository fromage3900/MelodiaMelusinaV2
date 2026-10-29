// Deterministic, renderer-independent botanical placements for an opt-in art garden.
// Pure data: does not mutate world RNG, biome scatter, collisions, saves or POIs.
// Modes follow the world's existing (n,m) Chladni plate convention.
export const BOTANY_FAMILIES = Object.freeze({
  bellflower: Object.freeze({ asset: 'ASSET_FLR_bellflower_dwarf', scale: 1 }),
  fern: Object.freeze({ asset: 'ASSET_FLR_moonfern_young', scale: 0.85 }),
  rosette: Object.freeze({ asset: 'ASSET_FLR_bellflower_dwarf', scale: 0.65 }),
});
export const BOTANY_MODES = Object.freeze([[2, 3], [3, 5], [4, 7]]);
export function plateField(u, v, n, m) {
  return Math.sin(Math.PI*n*u)*Math.sin(Math.PI*m*v)
       - Math.sin(Math.PI*m*u)*Math.sin(Math.PI*n*v);
}
function hash(a, b, seed) {
  let x = (Math.imul(a + 1, 374761393) ^ Math.imul(b + 1, 668265263) ^ (seed | 0)) | 0;
  x = Math.imul(x ^ (x >>> 13), 1274126177);
  return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
}
/**
 * Sample a local square plate; caller decides where the art-only garden lives.
 * Instances are records {x,z,scale,rotation,family,asset,mode}.
 * No THREE dependency, no external GLBs, no scene or save changes.
 */
export function sampleBotanicalPlate({ family = 'bellflower', mode = [3, 5],
  extent = 12, cells = 48, threshold = 0.075, maxInstances = 240,
  seed = 3900 } = {}) {
  const spec = BOTANY_FAMILIES[family];
  if (!spec) throw new Error('Unknown botanical family: ' + family);
  if (!Array.isArray(mode) || mode.length !== 2 || !mode.every(x => Number.isInteger(x) && x > 0 && x <= 12) || mode[0] === mode[1]) throw new Error('Invalid Chladni mode');
  if (!Number.isFinite(extent) || extent <= 0 || !Number.isInteger(cells) || cells < 4 || cells > 256 || !Number.isFinite(threshold) || threshold <= 0 || threshold > 1 || !Number.isInteger(maxInstances) || maxInstances < 0 || maxInstances > 5000) throw new Error('Invalid botanical budget');
  const out = [];
  for (let iy = 0; iy < cells; iy++) for (let ix = 0; ix < cells; ix++) {
    const u = (ix + 0.5) / cells, v = (iy + 0.5) / cells;
    if (Math.abs(plateField(u, v, mode[0], mode[1])) > threshold) continue;
    if (hash(ix, iy, seed) < 0.22) continue;
    const jitterX = (hash(ix, iy, seed + 1) - 0.5) * 0.25;
    const jitterZ = (hash(ix, iy, seed + 2) - 0.5) * 0.25;
    out.push({ x: (u - 0.5 + jitterX / cells) * extent,
      z: (v - 0.5 + jitterZ / cells) * extent,
      scale: spec.scale * (0.8 + hash(ix, iy, seed + 3) * 0.4),
      rotation: hash(ix, iy, seed + 4) * Math.PI * 2,
      family, asset: spec.asset, mode: [...mode] });
    if (out.length >= maxInstances) return out;
  }
  return out;
}
export function nineBotanicalStudies(options = {}) {
  return Object.keys(BOTANY_FAMILIES).flatMap(family =>
    BOTANY_MODES.map(mode => ({ family, mode, instances: sampleBotanicalPlate({ ...options, family, mode }) })));
}
