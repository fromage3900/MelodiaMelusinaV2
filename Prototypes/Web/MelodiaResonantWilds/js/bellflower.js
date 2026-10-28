// Resonant Wilds — 3D Jutsu Resonance Shrine companion: Bellflower Lantern v1.
// Geometry-parity canary based on the authored Higgsfield scene (revision 2).
// This is NOT an imported GLB: replace the procedural template with a vetted
// standalone GLB after binary source handoff. No gameplay or audio authority.
import * as THREE from 'three';
import { environmentMaterial } from './cel.js';

let template;
let glowMaterial;

function material(hex, options = {}) {
  return environmentMaterial(hex, { side: THREE.DoubleSide, ...options });
}
function piece(root, geometry, mat, x = 0, y = 0, z = 0) {
  const mesh = new THREE.Mesh(geometry, mat);
  mesh.position.set(x, y, z);
  root.add(mesh);
  return mesh;
}
function curve(root, points, radius, mat) {
  const spline = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  return piece(root, new THREE.TubeGeometry(spline, Math.max(8, points.length * 5), radius, 6, false), mat);
}
function petalsGeometry() {
  const vertices = [], indices = [];
  const rows = 13, cols = 11;
  for (let n = 0; n < 5; n++) {
    const angle = n * Math.PI * 2 / 5 + 0.10;
    const base = vertices.length / 3;
    for (let i = 0; i < rows; i++) {
      const t = i / (rows - 1);
      const radius = 0.085 + 0.285 * Math.pow(Math.sin(0.5 * Math.PI * t), 1.1);
      const y = 1.425 - 0.55 * t - 0.035 * Math.sin(Math.PI * Math.min(1, t * 1.4));
      const half = 0.52 + 0.04 * Math.sin(Math.PI * t);
      for (let j = 0; j < cols; j++) {
        const s = j / (cols - 1);
        const a = angle + (s - 0.5) * 2 * half;
        const ripple = 1 + 0.065 * Math.cos((s - 0.5) * Math.PI * 2) * t;
        vertices.push(radius * Math.cos(a) * ripple, y - 0.07 * t * t * Math.pow(Math.abs(2 * s - 1), 2), radius * Math.sin(a) * ripple);
      }
    }
    for (let i = 0; i < rows - 1; i++) for (let j = 0; j < cols - 1; j++) {
      const a = base + i * cols + j, b = a + 1, c = a + cols + 1, d = a + cols;
      indices.push(a, b, c, a, c, d);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}
function leafGeometry(side, z, tilt) {
  const v = [], index = [];
  for (let j = 0; j < 9; j++) {
    const t = j / 8, d = 0.05 + 0.33 * t, w = 0.10 * Math.sin(Math.PI * t);
    v.push(side * d, z + tilt * t, -w, side * d, z + tilt * t + 0.025 * Math.sin(Math.PI * t), w);
    if (j < 8) {
      const a = 2 * j;
      index.push(a, a + 1, a + 3, a, a + 3, a + 2);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  geo.setIndex(index);
  geo.computeVertexNormals();
  return geo;
}
export function bellflowerTemplate() {
  if (template) return template;
  const group = new THREE.Group();
  group.name = 'RW_BellflowerLantern_3DJutsu_v1';
  const gold = material('#c5a16a', { metalness: 0.36, roughness: 0.37 });
  const pearl = material('#eee1f2', { roughness: 0.39 });
  const amethyst = material('#59466c');
  const blush = material('#f6a2c5', { roughness: 0.35 });
  const jade = material('#61baa9');
  const lavender = material('#aa92ef');
  glowMaterial = material('#b5f9ff', { emissive: '#38caff', emissiveIntensity: 1.0, roughness: 0.32 });
  const cylinder = (rTop, rBottom, height, mat, y) => piece(group, new THREE.CylinderGeometry(rTop, rBottom, height, 20), mat, 0, y, 0);
  cylinder(.225, .225, .075, amethyst, .0375);
  cylinder(.23, .25, .075, pearl, .1125);
  cylinder(.225, .235, .026, gold, .163);
  cylinder(.06, .075, .069, gold, .211);
  curve(group, [[0,.22,0],[-.03,.49,0],[-.06,.89,0],[-.03,1.28,0],[.11,1.59,0],[.31,1.70,0],[.50,1.59,0],[.55,1.44,0]], .027, gold);
  curve(group, [[.11,1.59,-.022],[.25,1.70,-.03],[.44,1.65,-.025]], .009, pearl);
  for (const [i,side,y,tilt] of [[0,1,.79,.19],[1,-1,1.11,-.13],[2,1,1.34,.12]]) {
    piece(group, leafGeometry(side,y,tilt), jade);
    curve(group, [[side*.04,y,0],[side*.23,y+tilt*.5,0],[side*.39,y+tilt,0]], .007, gold);
  }
  const bloom = new THREE.Group(); bloom.position.x = .55; group.add(bloom);
  piece(bloom, petalsGeometry(), blush);
  piece(bloom, new THREE.CylinderGeometry(.10, .11, .09, 16), gold, 0, 1.415);
  piece(bloom, new THREE.SphereGeometry(.18, 12, 10), pearl, 0, 1.02).scale.set(1,.82,1);
  piece(bloom, new THREE.SphereGeometry(.115, 12, 10), glowMaterial, 0, .92).scale.set(1,1.25,1);
  piece(bloom, new THREE.SphereGeometry(.065, 10, 8), lavender, 0, .805);
  const beadGeo = new THREE.IcosahedronGeometry(.025, 0);
  for (let i = 0; i < 5; i++) {
    const a = .1 + i * Math.PI * 2 / 5;
    piece(bloom, beadGeo, gold, .375 * Math.cos(a), .78, .375 * Math.sin(a));
  }
  template = group;
  return group;
}
export function installBellflowers(plaza, originalLamps, hubHeight) {
  const flag = new URLSearchParams(window.location.search).get('bellflower');
  // Enabled by default on the visual experiment branch; turn off for A/B comparison.
  if (flag === '0') return null;
  if (!originalLamps || originalLamps.length !== 4) return null;
  try {
    const model = bellflowerTemplate();
    for (const lamp of originalLamps) {
      const copy = model.clone(true);
      copy.name = 'RW_Bellflower_Plaza_' + lamp.index;
      copy.position.set(lamp.x, hubHeight, lamp.z);
      copy.rotation.y = lamp.angle - Math.PI / 2;
      copy.scale.setScalar(1.45);
      plaza.add(copy);
      lamp.stem.visible = false;
      lamp.light.visible = false;
    }
    return { glow: glowMaterial, count: originalLamps.length };
  } catch (error) {
    console.warn('Resonant Wilds bellflower geometry unavailable; original lanterns retained', error);
    return null;
  }
}
export function animateBellflowers(state, phase, crescendo) {
  if (!state) return;
  // Visual response only. The existing Web Audio beat clock owns musical timing.
  const pulse = Math.pow(Math.max(0, 1 - Math.abs(phase) * 2), 2);
  state.glow.emissiveIntensity = .65 + pulse * .75 + Math.min(1, crescendo) * .3;
}
