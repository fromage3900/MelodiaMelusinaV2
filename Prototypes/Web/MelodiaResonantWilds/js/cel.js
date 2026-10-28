// Melodia Resonant Wilds — material-directed NPR V2, Three.js r170.
// Original v1 stays default; V2 opt-in with ?npr=v2. No fork of three.js.
import * as THREE from 'three';

const flags = new URLSearchParams(window.location.search);
export const legacyRender = flags.get('render') === 'legacy';
export const nprV2 = !legacyRender && flags.get('npr') === 'v2';

let gradient;
const ramps = new Map();
// Multiplicative RGB shadow / midtone / light ramps, keeping author-authored
// texture maps, vertex colours, gear dyes and per-material emissive intact.
// Chosen to colour *lighting*, not overwrite surface albedo.
export const NPR_PALETTES = Object.freeze({
  default: [[105, 89, 152], [194, 181, 228], [255, 255, 255]],
  skin:    [[126, 91, 168], [228, 177, 212], [255, 248, 239]],
  fabric:  [[103, 79, 170], [206, 177, 231], [255, 251, 255]],
  foliage: [[74, 118, 163], [177, 214, 204], [255, 255, 238]],
  stone:   [[99, 123, 172], [189, 215, 225], [255, 251, 247]],
  metal:   [[138, 91, 147], [240, 203, 161], [255, 255, 236]],
  crystal: [[87, 133, 193], [180, 208, 255], [255, 255, 255]],
});

export function toonGradient() {
  if (gradient) return gradient;
  gradient = new THREE.DataTexture(new Uint8Array([80, 167, 255]), 3, 1, THREE.RedFormat);
  gradient.minFilter = THREE.NearestFilter;
  gradient.magFilter = THREE.NearestFilter;
  gradient.generateMipmaps = false;
  gradient.colorSpace = THREE.NoColorSpace;
  gradient.needsUpdate = true;
  return gradient;
}

export function paletteGradient(role = 'default') {
  role = NPR_PALETTES[role] ? role : 'default';
  if (ramps.has(role)) return ramps.get(role);
  const pixels = new Uint8Array(12);
  NPR_PALETTES[role].forEach((rgb, i) => pixels.set([...rgb, 255], i * 4));
  const texture = new THREE.DataTexture(pixels, 3, 1, THREE.RGBAFormat);
  texture.minFilter = THREE.NearestFilter;
  texture.magFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  texture.colorSpace = THREE.NoColorSpace;
  texture.needsUpdate = true;
  ramps.set(role, texture);
  return texture;
}

function guessPalette(color) {
  if (typeof color !== 'string' && !color?.isColor && typeof color !== 'number') return 'default';
  const c = new THREE.Color(color), hsl = { h: 0, s: 0, l: 0 };
  c.getHSL(hsl);
  if (hsl.s < 0.13) return hsl.l > 0.7 ? 'fabric' : 'stone';
  if (hsl.h > 0.27 && hsl.h < 0.52) return 'foliage';
  if (hsl.h > 0.50 && hsl.h < 0.70) return 'crystal';
  if (hsl.h > 0.70 && hsl.h < 0.84) return 'fabric';
  if (hsl.h > 0.84) return 'fabric';
  if (hsl.h < 0.13 && hsl.l < 0.43) return 'skin';
  if (hsl.h < 0.16) return 'metal';
  return 'stone';
}

export function celMaterial(color, options = {}) {
  const { nprRole, ...parameters } = options;
  return new THREE.MeshToonMaterial({
    color,
    gradientMap: nprV2 ? paletteGradient(nprRole || guessPalette(color)) : toonGradient(),
    ...parameters,
  });
}

export function environmentMaterial(color, options = {}) {
  const { nprRole, ...parameters } = options;
  return legacyRender
    ? new THREE.MeshLambertMaterial({ color, ...parameters })
    : celMaterial(color, { ...parameters, nprRole });
}
