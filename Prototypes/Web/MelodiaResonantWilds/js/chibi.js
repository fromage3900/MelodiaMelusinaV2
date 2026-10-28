// Code-built chibi Melusina, styled from the Melusina chibi sprite sheet: lavender
// wavy hair, pink flowered beret, lavender heart vest, pink bow and puff sleeves,
// cream-and-pink skirt with a treble-clef emblem, lace-up pink boots.
// A jointed toon figure posed every frame from game state. No external model needed.
// Field names match what player.js and the Wardrobe recolouring already use.

import * as THREE from 'three';
import { toon, blob } from './entities.js';
import { nprV2, registerInkMaterial } from './cel.js';
import { clamp, lerp } from './util.js';

const INK = registerInkMaterial(new THREE.MeshBasicMaterial({ color: nprV2 ? '#302344' : '#2a1f3a', side: THREE.BackSide }));
const PAL = {
  skin: '#a6705a', blush: '#e5707f', eyeWhite: '#ffffff', iris: '#8e6ce0', pupil: '#2c1d4a',
  hair: '#b8a4f0', hairLight: '#ddd4ff', hairDeep: '#8a74d6', clip: '#7c5fd6',
  beret: '#f6b8d6', flower: '#ff8fbb', flowerCore: '#ffe27a',
  vest: '#b9a2ea', vestTrim: '#f6cfe6', bow: '#f7a9cb', sleeve: '#f8bcd9', glove: '#f49bc4',
  skirt: '#f9b4d2', skirtInner: '#fff1f6', ruffle: '#6b5bb0', clef: '#ffffff',
  boot: '#f5a3c8', lace: '#ffffff', sock: '#fff8fb', gold: '#ffd978',
};

const easeOut = (x) => 1 - Math.pow(1 - x, 3);

// Dark back-face shell gives every part a cartoon outline.
function inked(mesh, s = 1.05) {
  const o = new THREE.Mesh(mesh.geometry, INK);
  o.scale.setScalar(s);
  mesh.add(o);
  return mesh;
}

function part(geo, color, x = 0, y = 0, z = 0, opts = {}) {
  const role = color === PAL.skin ? 'skin'
    : color === PAL.gold || color === PAL.flowerCore ? 'metal'
    : color === PAL.hair || color === PAL.hairLight || color === PAL.hairDeep ? 'crystal'
    : color === PAL.glove || color === PAL.vest || color === PAL.skirt ? 'fabric'
    : undefined;
  const m = new THREE.Mesh(geo, toon(color, { nprRole: role, ...opts }));
  m.position.set(x, y, z);
  return m;
}

function doubleSided(mat) {
  mat.side = THREE.DoubleSide;
  return mat;
}

// Ease a rotation axis toward a target, frame-rate independent.
function to(obj, axis, target, dt, rate = 14) {
  obj[axis] += (target - obj[axis]) * (1 - Math.exp(-rate * dt));
}

// A hanging lock of hair: a chain of tapered segments, each swaying from the one above.
function hairLock(parent, x, y, z, segCount, radius, segLen, color) {
  const segs = [];
  let p = new THREE.Group();
  p.position.set(x, y, z);
  parent.add(p);
  for (let i = 0; i < segCount; i++) {
    const seg = new THREE.Group();
    seg.position.y = i === 0 ? 0 : -segLen;
    p.add(seg);
    const r0 = radius * (1 - i * 0.12);
    seg.add(part(new THREE.CylinderGeometry(r0 * 0.7, r0, segLen * 1.05, 8), i % 2 ? color : PAL.hairLight, 0, -segLen / 2, 0));
    segs.push(seg);
    p = seg;
  }
  return segs;
}

export function buildChibi() {
  // ---- hierarchy: root > hips (waist pivot) > chest (shoulder pivot) > head/arms
  const root = new THREE.Group();
  const hips = new THREE.Group();
  hips.position.y = 0.72;
  root.add(hips);

  // Skirt: cream petticoat, pink outer layer (gear tints this), navy ruffle, treble-clef emblem.
  const skirt = new THREE.Group();
  skirt.position.y = -0.25;
  hips.add(skirt);
  const innerMat = doubleSided(toon(PAL.skirtInner));
  skirt.add(new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.47, 0.46, 22, 1, true), innerMat));
  const gownMat = doubleSided(toon(PAL.skirt));
  const outer = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.52, 0.42, 22, 1, true), gownMat);
  outer.position.y = 0.03;
  skirt.add(outer);
  const ruffle = part(new THREE.TorusGeometry(0.5, 0.05, 6, 26), PAL.ruffle, 0, -0.2, 0);
  ruffle.rotation.x = Math.PI / 2;
  skirt.add(ruffle);
  for (const [y, r] of [[-0.08, 0.36], [-0.14, 0.44]]) {
    const tier = part(new THREE.TorusGeometry(r, 0.035, 6, 30), PAL.skirtInner, 0, y, 0);
    tier.rotation.x = Math.PI / 2;
    skirt.add(tier);
  }
  // Treble-clef emblem on the front panel, built from tube strokes.
  const clef = new THREE.Group();
  clef.position.set(0, 0.0, 0.5);
  clef.rotation.x = -0.12;
  clef.add(part(new THREE.TorusGeometry(0.075, 0.018, 6, 14), PAL.clef, 0, 0.07, 0));
  clef.add(part(new THREE.CylinderGeometry(0.014, 0.014, 0.26, 6), PAL.clef, 0, -0.02, 0));
  clef.add(part(new THREE.TorusGeometry(0.05, 0.016, 6, 12, Math.PI * 1.4), PAL.clef, 0, -0.13, 0));
  skirt.add(clef);

  // Waist: lavender band and a pink sash.
  hips.add(part(new THREE.CylinderGeometry(0.2, 0.17, 0.2, 16), PAL.vest, 0, 0.1, 0));
  const sash = part(new THREE.TorusGeometry(0.19, 0.03, 6, 18), PAL.vestTrim, 0, 0.0, 0);
  sash.rotation.x = Math.PI / 2;
  hips.add(sash);

  // Back bow, tied at the waist.
  const bow = new THREE.Group();
  bow.position.set(0, 0.02, -0.22);
  for (const s of [-1, 1]) {
    const loop = part(new THREE.SphereGeometry(0.13, 10, 8), PAL.bow, s * 0.13, 0.02, 0);
    loop.scale.set(1, 1.1, 0.5);
    bow.add(inked(loop, 1.05));
  }
  bow.add(part(new THREE.SphereGeometry(0.05, 8, 6), PAL.bow, 0, 0.02, 0.02));
  hips.add(bow);

  // Legs: white socks, lace-up pink boots. `shoes` (gear flag) adds gold cuffs on top.
  const shoes = new THREE.Group();
  const legs = [];
  for (const s of [-1, 1]) {
    const leg = new THREE.Group();
    leg.position.set(s * 0.13, -0.3, 0);
    hips.add(leg);
    leg.add(part(new THREE.CylinderGeometry(0.07, 0.065, 0.3, 10), PAL.sock, 0, -0.15, 0));
    const boot = part(new THREE.SphereGeometry(0.12, 12, 10), PAL.boot, 0, -0.33, 0.03);
    boot.scale.set(1, 0.85, 1.35);
    leg.add(inked(boot, 1.05));
    for (const ly of [-0.27, -0.32]) {
      const lace = part(new THREE.TorusGeometry(0.095, 0.014, 5, 12), PAL.lace, 0, ly, 0.06);
      lace.rotation.x = Math.PI / 2;
      leg.add(lace);
    }
    const cuff = part(new THREE.TorusGeometry(0.128, 0.022, 6, 16), PAL.gold, s * 0.13, -0.55, 0.03);
    cuff.rotation.x = Math.PI / 2;
    shoes.add(cuff);
    legs.push(leg);
  }
  hips.add(shoes);

  // ---- chest (shoulder pivot): lavender vest with a pink heart, bow at the neck
  const chest = new THREE.Group();
  chest.position.y = 0.3;
  hips.add(chest);
  const vest = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.2, 0.24, 18, 1, true), doubleSided(toon(PAL.vest)));
  vest.position.y = -0.06;
  chest.add(vest);
  const heart = new THREE.Group();
  heart.position.set(0, -0.04, 0.21);
  for (const s of [-1, 1]) heart.add(part(new THREE.SphereGeometry(0.035, 8, 6), PAL.vestTrim, s * 0.03, 0.02, 0));
  const point = part(new THREE.ConeGeometry(0.05, 0.07, 6), PAL.vestTrim, 0, -0.03, 0);
  point.rotation.z = Math.PI;
  heart.add(point);
  chest.add(heart);
  const neckBow = new THREE.Group();
  neckBow.position.set(0, 0.13, 0.2);
  for (const s of [-1, 1]) {
    const w = part(new THREE.SphereGeometry(0.06, 8, 6), PAL.bow, s * 0.07, 0, 0);
    w.scale.set(1.3, 0.85, 0.5);
    neckBow.add(inked(w, 1.06));
  }
  neckBow.add(part(new THREE.SphereGeometry(0.03, 6, 5), PAL.flowerCore, 0, 0, 0.02));
  chest.add(neckBow);

  // ---- head
  const head = new THREE.Group();
  head.position.set(0, 0.34, 0.02);
  chest.add(head);
  head.add(inked(part(new THREE.SphereGeometry(0.46, 22, 16), PAL.skin, 0, 0, 0)));

  // Big anime eyes: white sclera, lavender iris, dark pupil, highlight.
  const eyes = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group();
    eye.position.set(s * 0.17, -0.05, 0.4);
    const white = part(new THREE.SphereGeometry(0.095, 12, 10), PAL.eyeWhite, 0, 0, 0);
    white.scale.set(0.9, 1.25, 0.4);
    eye.add(white);
    const iris = part(new THREE.SphereGeometry(0.068, 10, 8), PAL.iris, 0, -0.01, 0.03);
    iris.scale.set(0.95, 1.1, 0.5);
    eye.add(iris);
    eye.add(part(new THREE.SphereGeometry(0.035, 8, 6), PAL.pupil, 0, -0.01, 0.05));
    eye.add(part(new THREE.SphereGeometry(0.02, 6, 5), '#ffffff', 0.025, 0.035, 0.07));
    head.add(eye);
    eyes.push(eye);
    const blush = new THREE.Mesh(
      new THREE.CircleGeometry(0.09, 16),
      new THREE.MeshBasicMaterial({ color: PAL.blush, transparent: true, opacity: 0.5, depthWrite: false }),
    );
    blush.position.set(s * 0.28, -0.14, 0.38);
    blush.rotation.y = s * 0.7;
    head.add(blush);
  }
  const mouth = part(new THREE.TorusGeometry(0.035, 0.012, 6, 10, Math.PI), PAL.pupil, 0, -0.17, 0.44);
  mouth.rotation.z = Math.PI;
  head.add(mouth);

  // Long lavender hair: a crown, a swept fringe, a full back, and hanging side and back locks.
  const hairMat = toon(PAL.hair);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.49, 24, 14, 0, Math.PI * 2, 0, Math.PI * 0.36), hairMat);
  cap.position.y = 0.03;
  head.add(cap);
  for (const [x, y, z, rz] of [[-0.3, 0.1, 0.3, 0.9], [-0.2, 0.16, 0.36, 0.5], [-0.08, 0.19, 0.41, 0.2], [0.08, 0.19, 0.41, -0.2], [0.2, 0.16, 0.36, -0.5], [0.3, 0.1, 0.3, -0.9]]) {
    const bang = new THREE.Mesh(new THREE.SphereGeometry(0.13, 10, 8), toon(PAL.hairLight));
    bang.scale.set(1.3, 0.6, 0.55);
    bang.position.set(x, y, z);
    bang.rotation.z = rz;
    head.add(bang);
  }
  const backHair = new THREE.Mesh(new THREE.SphereGeometry(0.47, 16, 12), hairMat);
  backHair.scale.set(1.05, 1.5, 0.75);
  backHair.position.set(0, -0.25, -0.22);
  head.add(backHair);
  for (const s of [-1, 1]) {
    const clip = part(new THREE.BoxGeometry(0.11, 0.025, 0.03), PAL.clip, s * 0.3, 0.2, 0.36);
    clip.rotation.z = s * 0.5;
    head.add(clip);
  }
  // Long wavy locks. Their segments form the sway chain.
  const tail = [];
  for (const [x, y, z] of [[-0.36, 0.0, -0.02], [0.36, 0.0, -0.02], [-0.22, -0.1, -0.36], [0.22, -0.1, -0.36]]) {
    tail.push(...hairLock(head, x, y, z, 4, 0.085, 0.26, PAL.hair));
  }

  // Pink beret with a flower, tilted on the top-right of the head.
  const beret = new THREE.Group();
  beret.position.set(0.1, 0.4, 0.04);
  beret.rotation.z = -0.22;
  head.add(beret);
  const berRet = new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 10), toon(PAL.beret));
  berRet.scale.set(1.2, 0.36, 1.1);
  beret.add(inked(berRet, 1.04));
  beret.add(part(new THREE.CylinderGeometry(0.03, 0.03, 0.04, 8), PAL.beret, 0, 0.1, 0));
  const flower = new THREE.Group();
  flower.position.set(0.22, 0.04, 0.22);
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2;
    flower.add(part(new THREE.SphereGeometry(0.06, 8, 6), PAL.flower, Math.cos(a) * 0.07, 0, Math.sin(a) * 0.07));
  }
  flower.add(part(new THREE.SphereGeometry(0.04, 8, 6), PAL.flowerCore, 0, 0.01, 0));
  beret.add(flower);

  // Headpiece gear: a gold circlet, shown when a head item is equipped.
  const crown = part(new THREE.TorusGeometry(0.22, 0.045, 6, 16), PAL.gold, 0, 0.52, 0, { emissive: '#d9bc72', emissiveIntensity: 0.3 });
  crown.rotation.x = Math.PI / 2;
  crown.visible = false;
  head.add(crown);

  // ---- arms: pink puff sleeve at the shoulder, long pink glove, hand
  const arms = {};
  for (const s of [-1, 1]) {
    const shoulder = new THREE.Group();
    shoulder.position.set(s * 0.27, -0.02, 0);
    chest.add(shoulder);
    shoulder.add(inked(part(new THREE.SphereGeometry(0.14, 12, 10), PAL.sleeve, 0, 0, 0)));
    const elbow = new THREE.Group();
    elbow.position.y = -0.16;
    shoulder.add(elbow);
    elbow.add(part(new THREE.CylinderGeometry(0.075, 0.065, 0.26, 10), PAL.glove, 0, -0.13, 0));
    const hand = new THREE.Group();
    hand.position.y = -0.3;
    elbow.add(hand);
    hand.add(part(new THREE.SphereGeometry(0.09, 10, 8), PAL.glove, 0, 0, 0));
    arms[s < 0 ? 'L' : 'R'] = { shoulder, elbow, hand };
  }

  // Instrument in the right hand: a gold lyre arc (ranged) or a baton (melee).
  const instMat = toon(PAL.gold, { emissive: '#ffcf6a', emissiveIntensity: 0.35 });
  const inst = new THREE.Group();
  inst.position.set(0.02, 0.02, 0.07);
  const lyre = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.035, 6, 14, Math.PI * 1.3), instMat);
  lyre.rotation.z = -Math.PI * 0.15;
  const baton = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.04, 0.8, 6), instMat);
  baton.rotation.x = Math.PI / 2.3;
  baton.visible = false;
  inst.add(lyre, baton);
  arms.R.hand.add(inst);
  // Swing trail: a faint arc in front of Melusina that follows the attack swing.
  const trail = new THREE.Mesh(
    new THREE.TorusGeometry(0.75, 0.05, 6, 24, Math.PI * 0.9),
    new THREE.MeshBasicMaterial({ color: PAL.gold, transparent: true, opacity: 0, depthWrite: false }),
  );
  trail.position.set(0, 0.95, 0);
  trail.rotation.x = Math.PI / 2;
  chest.add(trail);
  // Sparkles that circle the head, matching the sprite sheet's star accents.
  const sparkles = [];
  for (let k = 0; k < 3; k++) {
    const sp = part(new THREE.OctahedronGeometry(0.05, 0), '#ffffff', 0, 0, 0, { emissive: '#fff4c2', emissiveIntensity: 0.9 });
    sparkles.push(sp);
    root.add(sp);
  }

  root.scale.setScalar(1.35);
  const shadow = blob(0.9);

  // Pose from state. s: { speed 0..1, beatPhase 0..1, swing 0..1 or -1, swingStep,
  // cast 0..1, dodge 0..1, hurt 0..1, stretch }. Beat-locked: bounce peaks on the beat.
  function pose(dt, t, s = {}) {
    const speed = clamp(s.speed ?? 0, 0, 1);
    const beat = 1 - (s.beatPhase ?? 0);
    const b2 = beat * beat;
    const stride = Math.sin(t * 10.5) * speed;
    const breathe = Math.sin(t * 2.2) * 0.04;
    const swing = s.swing ?? -1;
    const cast = clamp(s.cast ?? 0, 0, 1);
    const dodge = clamp(s.dodge ?? 0, 0, 1);
    const hurt = clamp(s.hurt ?? 0, 0, 1);
    const stretch = s.stretch ?? 1;

    // Legs and arms: opposite-phase walk cycle; attack and cast override the arms.
    to(legs[0].rotation, 'x', stride * 0.75, dt);
    to(legs[1].rotation, 'x', -stride * 0.75, dt);
    let lx = 0.12 + breathe - stride * 0.5, lz = 0.24;
    let rx = 0.12 + breathe + stride * 0.5, rz = -0.24;
    let chestX = 0.12 * speed + 0.3 * dodge - 0.25 * hurt;
    let chestY = 0, headX = 0, headZ = Math.sin(t * 40) * 0.15 * hurt;
    if (swing >= 0) {
      const e = easeOut(clamp(swing, 0, 1));
      rx = lerp(-1.7, 1.5, e);
      rz = -0.4;
      chestY = (s.swingStep % 2 ? -1 : 1) * 0.35 * Math.sin(clamp(swing, 0, 1) * Math.PI);
    }
    if (cast > 0) {
      // Both arms raised out to the sides in a V, so the gesture reads from the camera.
      lx = lerp(lx, 0, cast); lz = lerp(lz, -2.6, cast);
      rx = lerp(rx, 0, cast); rz = lerp(rz, 2.6, cast);
      headX = -0.25 * cast;
    }
    to(arms.L.shoulder.rotation, 'x', lx, dt, 16);
    to(arms.L.shoulder.rotation, 'z', lz, dt, 16);
    to(arms.R.shoulder.rotation, 'x', rx, dt, 16);
    to(arms.R.shoulder.rotation, 'z', rz, dt, 16);
    to(arms.L.elbow.rotation, 'x', -0.3, dt);
    to(arms.R.elbow.rotation, 'x', -0.3 + (swing >= 0 ? -0.4 : 0), dt);

    to(chest.rotation, 'x', chestX, dt);
    to(chest.rotation, 'y', chestY, dt);
    to(head.rotation, 'x', headX, dt);
    to(head.rotation, 'z', headZ, dt, 20);

    // Beat bounce on the waist and head, plus dodge stretch.
    hips.position.y = 0.72 + b2 * 0.02 * (1 - speed * 0.5);
    hips.scale.set(1 / Math.sqrt(stretch), stretch * (1 + b2 * 0.03), 1 / Math.sqrt(stretch));
    head.position.y = 0.34 + b2 * 0.025;

    // Hair locks lag the segment above them and stream back when running.
    tail.forEach((seg, i) => {
      const target = Math.sin(t * 3.1 - i * 0.7) * 0.1 + speed * 0.16 + dodge * 0.2;
      to(seg.rotation, 'x', target, dt, 6);
    });

    // Attack trail follows the swing and fades out at its end.
    const sw = swing >= 0 ? clamp(swing, 0, 1) : -1;
    trail.material.opacity = sw >= 0 ? Math.sin(sw * Math.PI) * 0.55 : 0;
    trail.rotation.z = sw >= 0 ? lerp(-1.2, 1.2, easeOut(sw)) : 0;
    // Sparkles orbit the head, bobbing with the beat.
    sparkles.forEach((sp, k) => {
      const a = t * 0.9 + (k * Math.PI * 2) / 3;
      sp.position.set(Math.cos(a) * 0.62, 1.9 + Math.sin(t * 2 + k) * 0.08 + b2 * 0.05, Math.sin(a) * 0.5);
      sp.rotation.y = t * 3;
    });

    // Blink every ~3.4 s.
    const blink = t % 3.4 < 0.12 ? 0.12 : 1;
    for (const e of eyes) e.scale.y = blink;
  }

  return {
    group: root,
    shadow,
    body: hips,
    gownMat,
    crown,
    shoes,
    inst,
    instMat,
    lyre,
    baton,
    pose,
    rig: { root, hips, chest, head, eyes, arms, legs, tail, trail, sparkles },
  };
}
