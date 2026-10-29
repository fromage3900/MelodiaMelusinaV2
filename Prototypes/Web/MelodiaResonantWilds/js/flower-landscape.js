// Resonant Wilds — Floraison P0. Opt-in instanced floral landscape (?botany=1).
// An art-only overlay: existing biome scatter, world RNG, collision, POIs and saves
// remain untouched. One low-poly vertex-coloured mesh per family per loaded chunk.
// Shared geometries/materials survive chunk unload; instance buffers do not.
import * as THREE from 'three';
import { environmentMaterial } from './cel.js';
import { BIOMES, HUB, WORLD_RADIUS, WORLD_SEED } from './design.js';
import { sampleBotanicalPlate } from './resonant-botany.js';

export const FLORAL_FAMILIES = Object.freeze(['bellflower', 'wildflower', 'fern', 'rosette', 'spire']);
export const LANDSCAPE_MODES = Object.freeze([
  { biome: 'sakura_terrace', radius: 108, mode: [2, 3], family: 'rosette', seed: 23 },
  { biome: 'glass_orchard', radius: 208, mode: [3, 5], family: 'bellflower', seed: 35 },
  { biome: 'starlit_moor', radius: 174, mode: [4, 7], family: 'rosette', seed: 47 },
]);
export const FLOWER_CHUNK_BUDGET = Object.freeze({ normal: 150, dense: 260 });
const TAU = Math.PI * 2;
const PETAL = ['#f9c6e1', '#cbb6fa', '#c7f0ee', '#fff0cd', '#eed5ff'];
const LEAF = ['#6fada0', '#80bea7', '#a3cbb5'];
const PALETTES = Object.freeze({
  sakura_terrace: ['#f6d4e7', '#efd8ff', '#efffef'],
  glass_orchard: ['#c7fcf0', '#d2ebff', '#f2e4ff'],
  starlit_moor: ['#e5c9ff', '#afd9e5', '#fae0ff'],
  choir_marsh: ['#d2e9df', '#b4dedc', '#e5d5f1'],
  liquid_cathedral: ['#d4f5e9', '#d1e6f7', '#fff0df'],
});
let cachedKit;

function random01(a, b, salt = 0) {
  let h = (Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263) ^ Math.imul((salt | 0) + WORLD_SEED, 2246822519)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function builder() {
  const p = [], colors = [];
  function tri(a, b, c, hex) {
    const color = new THREE.Color(hex);
    for (const v of [a, b, c]) { p.push(v[0], v[1], v[2]); colors.push(color.r, color.g, color.b); }
  }
  function quad(a, b, c, d, color) { tri(a, b, c, color); tri(a, c, d, color); }
  function stalk(x, z, h, color = '#6fada0') {
    const w = 0.019;
    quad([x-w, 0, z], [x+w, 0, z], [x+w, h, z], [x-w, h, z], color);
    quad([x, 0, z-w], [x, 0, z+w], [x, h, z+w], [x, h, z-w], color);
  }
  function foliage(x, y, z, theta, size, color = '#86c2a6') {
    const dx = Math.cos(theta), dz = Math.sin(theta), qx = -dz, qz = dx;
    const origin = [x, y, z], tip = [x+dx*size, y+size*.18, z+dz*size];
    tri(origin, [x+dx*size*.45+qx*size*.19,y+size*.22,z+dz*size*.45+qz*size*.19], tip, color);
    tri(origin, tip, [x+dx*size*.45-qx*size*.19,y+size*.2,z+dz*size*.45-qz*size*.19], color);
  }
  function flower(x, y, z, radius, petals, palette, spin = 0) {
    const centre = [x, y+radius*.11, z];
    for (let i = 0; i < petals; i++) {
      const a = spin + TAU*i/petals, edge = a+TAU/petals;
      const r0 = radius*.29, r1 = radius, r2 = radius*.72;
      const start = [x+Math.cos(a)*r0,y,z+Math.sin(a)*r0];
      const mid = [x+Math.cos(a+TAU/(petals*2))*r1,y+radius*.16,z+Math.sin(a+TAU/(petals*2))*r1];
      const end = [x+Math.cos(edge)*r0,y,z+Math.sin(edge)*r0];
      tri(start, mid, end, palette[i%palette.length]);
      tri(start, [x+Math.cos(a+TAU/(petals*2))*r2,y+radius*.35,z+Math.sin(a+TAU/(petals*2))*r2], end, palette[i%palette.length]);
    }
    const pollen = '#f9e6a1';
    for (let k = 0; k < 5; k++) {
      const a = TAU*k/5, b = TAU*(k+1)/5;
      tri([x+Math.cos(a)*radius*.17,y,z+Math.sin(a)*radius*.17],
          [x+Math.cos(b)*radius*.17,y,z+Math.sin(b)*radius*.17], centre, pollen);
    }
  }
  function bell(x, y, z, radius, palette) {
    for (let j = 0; j < 6; j++) {
      const a = TAU*j/6, b = TAU*(j+1)/6;
      const lipA = [x+Math.cos(a)*radius,y-radius*.6,z+Math.sin(a)*radius];
      const lipB = [x+Math.cos(b)*radius,y-radius*.6,z+Math.sin(b)*radius];
      tri([x,y+radius*.6,z],lipA,lipB,palette[j%palette.length]);
      tri(lipA,[x+Math.cos(a+.18)*radius*1.12,y-radius*.96,z+Math.sin(a+.18)*radius*1.12],lipB,palette[j%palette.length]);
    }
    tri([x-.06,y-radius*.7,z], [x+.06,y-radius*.7,z], [x,y-radius*1.15,z], '#f9e9af');
  }
  function geometry() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(p,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    g.computeVertexNormals(); g.computeBoundingSphere();
    return g;
  }
  return { stalk, foliage, flower, bell, geometry };
}
function makeFlowerGeometry(family) {
  const b = builder();
  if (family === 'bellflower') {
    for (let i = 0; i < 3; i++) {
      const a = TAU*i/3+0.4, x = Math.cos(a)*.28, z = Math.sin(a)*.28, h = 1.1+i*.12;
      b.stalk(x,z,h,LEAF[i]); b.foliage(x*.45,h*.4,z*.45,a+.8,.23,LEAF[(i+1)%3]);
      b.bell(x,h,z,.21,[PETAL[(i+1)%5],PETAL[i%5],PETAL[(i+2)%5]]);
    }
  } else if (family === 'wildflower' || family === 'rosette') {
    const heads = family === 'rosette' ? 5 : 4;
    for (let i = 0; i < heads; i++) {
      const a = TAU*i/heads+.7, r = family==='rosette'?.23:.30, x = Math.cos(a)*r, z = Math.sin(a)*r;
      const h = (family==='rosette'?.53:.69)+.09*Math.sin(i*2.4);
      b.stalk(x,z,h); b.foliage(x*.5,h*.45,z*.5,a+.6,.24);
      b.flower(x,h,z,family==='rosette'?.22:.18,5,
        [PETAL[i%5],PETAL[(i+1)%5],PETAL[(i+3)%5]],i*.19);
    }
  } else if (family === 'fern') {
    for (let j = 0; j < 6; j++) {
      const a = TAU*j/6, dx = Math.cos(a), dz = Math.sin(a), length = .65+(j%3)*.1;
      for (let k = 1; k < 7; k++) {
        const t = k/7, x = dx*length*t, z = dz*length*t, y = .08+Math.sin(t*Math.PI)*.35;
        const across = a+Math.PI/2;
        const size = .18*(1-t*.6);
        b.foliage(x,y,z,across,size,LEAF[(j+k)%3]);
        b.foliage(x,y,z,across+Math.PI,size,LEAF[(j+k+1)%3]);
      }
      b.foliage(dx*length*.88,.24,dz*length*.88,a,.12,'#c7e6cb');
    }
  } else if (family === 'spire') {
    b.stalk(0,0,2.15,'#5f9e86');
    for (let k = 0; k < 4; k++) {
      const a = TAU*k/4, h = .6+k*.34, r = .19*(1-k*.12);
      b.foliage(0,h*.73,0,a+.35,.36,LEAF[k%3]);
      b.bell(Math.cos(a)*r,h,Math.sin(a)*r,.22-k*.014,
        [PETAL[k%5],PETAL[(k+2)%5],PETAL[(k+3)%5]]);
    }
  }
  return b.geometry();
}
function kit() {
  if (!cachedKit) {
    cachedKit = Object.fromEntries(FLORAL_FAMILIES.map(family => [family, {
      geometry: makeFlowerGeometry(family),
      material: environmentMaterial('#ffffff', { vertexColors: true, flatShading: true, side: THREE.DoubleSide, nprRole: 'foliage' }),
    }]));
  }
  return cachedKit;
}
function gardenLocations() {
  return LANDSCAPE_MODES.map(spec => {
    const biome = BIOMES.find(b => b.id === spec.biome);
    if (!biome) return null;
    return { ...spec, x: Math.cos(biome.angle)*spec.radius, z: Math.sin(biome.angle)*spec.radius };
  }).filter(Boolean);
}
export const BOTANICAL_GARDENS = gardenLocations();

export function flowerLandscapeEnabled(search) {
  const val = new URLSearchParams(search).get('botany');
  return val === '1' || val === 'dense';
}
function pathClear(x, z, radius) {
  const r = Math.hypot(x,z);
  if (r < HUB.radius - 7) return false;
  if (r < 125) {
    const angle = Math.atan2(z,x);
    for (const biome of BIOMES) {
      let d = Math.abs(angle - biome.angle);
      d = Math.min(d, TAU-d);
      // Keep radial spoke roads unobstructed; shorter plants may flank them.
      if (d*r < 6.5+radius) return false;
    }
  }
  return true;
}
function gardenAt(x,z) {
  for (const garden of BOTANICAL_GARDENS)
    if (Math.hypot(x-garden.x,z-garden.z)<20) return true;
  return false;
}
function acceptable(world,x,z,pois) {
  if (!pathClear(x,z,0.7) || Math.hypot(x,z)>WORLD_RADIUS-40) return null;
  const h=world.sample(x,z);
  if (h < .6) return null;
  if (Math.abs(world.sample(x+1,z)-h)>.65 || Math.abs(world.sample(x,z+1)-h)>.65) return null;
  if (pois.some(p=>(p.x-x)**2+(p.z-z)**2<64)) return null;
  return h;
}
function tint(family, x, z, hue) {
  const t = random01(Math.floor(x*3),Math.floor(z*3),71)*.13;
  const c = new THREE.Color();
  // Deliberately gentle tint so leaves retain their jade material identity.
  if (family==='fern') c.setRGB(.88+t*.4,1,.94+t*.3);
  else if (family==='spire') c.setRGB(.94+t*.3,.95+t*.2,1);
  else c.set(hue).lerp(new THREE.Color('#ffffff'),.78+t);
  return c;
}
export function installFlowerLandscapeChunk(world,cx,cz,chunk,chunkSize=64,dense=false) {
  const x0=cx*chunkSize,z0=cz*chunkSize;
  const pois=world.game.poiNear?world.game.poiNear(x0+chunkSize/2,z0+chunkSize/2,chunkSize):[];
  const planted = Object.fromEntries(FLORAL_FAMILIES.map(f=>[f,[]]));
  const budget=dense?FLOWER_CHUNK_BUDGET.dense:FLOWER_CHUNK_BUDGET.normal;
  // Macro patches ebb across tiles without repeating per-chunk rings or changing game RNG.
  for(let i=0;i<budget;i++) {
    const x=x0+random01(cx,i,901)*chunkSize, z=z0+random01(cz,i,902)*chunkSize;
    if (gardenAt(x,z)) continue; // authored Chladni figures remain legible
    const macro=.5+.25*Math.sin(x*.038+Math.sin(z*.021))+.25*Math.cos(z*.047-x*.014);
    if(random01(cx+cz,i,903)>Math.max(.08,macro))continue;
    const h=acceptable(world,x,z,pois);
    if(h===null)continue;
    const biome=world.dominantBiome(x,z).biome.id;
    if(!PALETTES[biome]) continue;
    const r=random01(cx,i,904);
    const family=r<.32?'bellflower':r<.68?'wildflower':r<.91?'fern':r<.98?'rosette':'spire';
    const s=(family==='spire'?.85:1)*(0.68+random01(cz,i,905)*.65);
    planted[family].push({x,y:h-.035,z,scale:s,angle:random01(cx,i,906)*TAU,
      color:tint(family,x,z,PALETTES[biome][i%3])});
  }
  // Three distinct full-scale node figures, composed from the same sampler as P0.
  for(const garden of BOTANICAL_GARDENS){
    if(garden.x+20<x0||garden.x-20>=x0+chunkSize||garden.z+20<z0||garden.z-20>=z0+chunkSize)continue;
    const plants=sampleBotanicalPlate({family:garden.family,mode:garden.mode,
      extent:34,cells:52,threshold:.115,maxInstances:170,seed:garden.seed});
    for(const p of plants){
      const x=garden.x+p.x,z=garden.z+p.z;
      if(x<x0||x>=x0+chunkSize||z<z0||z>=z0+chunkSize)continue;
      const h=acceptable(world,x,z,pois);
      if(h===null)continue;
      planted[p.family].push({x,y:h-.035,z,scale:p.scale*(.92+random01(Math.round(x),Math.round(z),8)*.2),
        angle:p.rotation,color:tint(p.family,x,z,'#e8c4f2')});
    }
  }
  const resources=kit(),matrix=new THREE.Matrix4(),position=new THREE.Vector3();
  const rotation=new THREE.Quaternion(),euler=new THREE.Euler(0,0,0),scale=new THREE.Vector3();
  let instances=0,draws=0;
  for(const family of FLORAL_FAMILIES){
    const items=planted[family];
    if(!items.length)continue;
    const {geometry,material}=resources[family];
    const mesh=new THREE.InstancedMesh(geometry,material,items.length);
    mesh.name='RW_Floraison_'+family;
    mesh.frustumCulled=true;
    for(let i=0;i<items.length;i++){
      const p=items[i];
      position.set(p.x,p.y,p.z);euler.y=p.angle;rotation.setFromEuler(euler);
      scale.setScalar(p.scale);matrix.compose(position,rotation,scale);
      mesh.setMatrixAt(i,matrix);mesh.setColorAt(i,p.color);
    }
    mesh.instanceMatrix.needsUpdate=true;
    if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;
    mesh.computeBoundingSphere();
    chunk.add(mesh);instances+=items.length;draws++;
  }
  return {instances,draws};
}
