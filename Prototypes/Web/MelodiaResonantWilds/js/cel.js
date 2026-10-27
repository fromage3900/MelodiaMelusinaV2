// Shared, mobile-friendly cel material for the browser prototype (Three.js r170).
// Keep the tonal bands identical across characters, terrain, landmarks and props.
import * as THREE from 'three';

let gradient;
export function toonGradient() {
  if (gradient) return gradient;
  const bands = new Uint8Array([80, 167, 255]);
  gradient = new THREE.DataTexture(bands, 3, 1, THREE.RedFormat);
  gradient.minFilter = THREE.NearestFilter;
  gradient.magFilter = THREE.NearestFilter;
  gradient.generateMipmaps = false;
  gradient.colorSpace = THREE.NoColorSpace;
  gradient.needsUpdate = true;
  return gradient;
}

export function celMaterial(color, options = {}) {
  return new THREE.MeshToonMaterial({
    color,
    gradientMap: toonGradient(),
    ...options,
  });
}
