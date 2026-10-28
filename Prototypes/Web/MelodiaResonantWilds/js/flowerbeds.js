// Petal Cantata — three-blossom authored flower family built for the existing
// per-chunk InstancedMesh spawner. One shared geometry per material role; never
// clone a GLB or create individual draw calls per flower.
import * as THREE from 'three';

function geometry(vertices, indices) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  g.computeBoundingSphere();
  return g;
}
function triangle(v, i, a, b, c) {
  const start = v.length / 3;
  v.push(...a, ...b, ...c);
  i.push(start, start + 1, start + 2);
}
function quad(v, i, a, b, c, d) {
  triangle(v, i, a, b, c);
  triangle(v, i, a, c, d);
}

// Each blossom has a slightly different height and tilt; the entire cluster
// remains one artistic scatter instance in the game's existing seed/exclusion logic.
const HEADS = [
  [-0.22, 0.45, -0.09, 1.00],
  [0.19, 0.36, 0.18, 0.84],
  [0.15, 0.30, -0.20, 0.69],
];
export function createFlowerbedParts(M, L, white) {
  const pv = [], pi = [], gv = [], gi = [], cv = [], ci = [];
  for (const [index, [cx, cy, cz, s]] of HEADS.entries()) {
    const origin = [cx, cy, cz];
    // Five rounded, gently upturned pointed petals; tinted by the original
    // five-colour flower palette through InstancedMesh.instanceColor.
    for (let j = 0; j < 5; j++) {
      const angle = (j / 5) * Math.PI * 2 + index * 0.21;
      const r = 0.08 * s, tip = 0.21 * s;
      const side1 = [cx + Math.cos(angle - .52) * r, cy + .005, cz + Math.sin(angle - .52) * r];
      const side2 = [cx + Math.cos(angle + .52) * r, cy + .005, cz + Math.sin(angle + .52) * r];
      const mid = [cx + Math.cos(angle) * (0.145 * s), cy + .037 * s, cz + Math.sin(angle) * (0.145 * s)];
      const end = [cx + Math.cos(angle) * tip, cy - .018 * s, cz + Math.sin(angle) * tip];
      quad(pv, pi, side1, mid, end, side2);
    }
    // Narrow cross-section stems and paired graphic leaves share a jade draw call.
    for (const theta of [0, Math.PI / 2]) {
      const dx = Math.cos(theta) * .014, dz = Math.sin(theta) * .014;
      quad(gv, gi, [0,0,0], [dx,0,dz], [cx+dx,cy,cz+dz], origin);
    }
    for (const side of [-1, 1]) {
      const sx = cx * .45, sz = cz * .45, sy = cy * .48;
      quad(gv, gi, [sx,sy,sz], [sx+side*.11,sy+.055,sz+.055],
        [sx+side*.24,sy+.02,sz+.03], [sx+side*.11,sy-.025,sz-.035]);
    }
    // Four facets of a subtle champagne-gold pollen center.
    const base = .045 * s;
    for (let k = 0; k < 4; k++) {
      const a = (k / 4) * Math.PI * 2;
      const b = ((k+1) / 4) * Math.PI * 2;
      triangle(cv, ci,
        [cx+Math.cos(a)*base,cy+.017,cz+Math.sin(a)*base],
        [cx+Math.cos(b)*base,cy+.017,cz+Math.sin(b)*base],
        [cx,cy+.075*s,cz]);
    }
  }
  const petalMat = white;
  petalMat.side = THREE.DoubleSide;
  const leafMat = L('#65b49a', { side: THREE.DoubleSide });
  const pollenMat = L('#f6da93', { side: THREE.DoubleSide, emissive: '#9e7830', emissiveIntensity: 0.06 });
  return [
    M(geometry(pv, pi), petalMat),
    M(geometry(gv, gi), leafMat),
    M(geometry(cv, ci), pollenMat),
  ];
}
export const FLOWERBED_BLOOMS = HEADS.length;
