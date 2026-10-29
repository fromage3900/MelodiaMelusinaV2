// Open-world authoring workflow for Resonant Wilds.
// Distilled from production notes on Infinity Nikki, Genshin Impact,
// Wuthering Waves and Zenless Zone Zero — implemented as data that drives
// the existing World / Activities generators (not a second world authority).
//
// Sources (research, 2026-10-27):
// - Infinity Nikki / Infold: theme-led pathways; prototype before polish;
//   detail at every scale; Impression → Creation → Production; lived-in hubs;
//   outfit-gated traversal as exploration identity (Apple / UE interviews).
// - Genshin / HoYoverse: region theme from real-world refs; gate landmarks
//   between regions (Stone Gate); vista reveals; POI/puzzle/resource density;
//   TOD/weather as mood (Developer Insight Liyue; Dragonspine).
// - Wuthering Waves / Kuro: TOD + character lighting consistency across open
//   world; deferred pipeline for maintainable biome weather/atmosphere.
// - Zenless Zone Zero / miHoYo: signature hub district as stylized “menu with
//   legs”; dense local life detail; function POIs within short walks
//   (Sixth Street postmortem).

import { BIOMES, HUB, WORLD_RADIUS } from './design.js';
import { clamp, lerp, smoothstep, angleDiff } from './util.js';

/** Production stages — Nikki's Impression → Creation → Production cycle. */
export const OW_STAGES = Object.freeze({
  impression: 'Theme keywords, palette, one hero silhouette, one gate feeling.',
  creation: 'Route + gate + vista + landmark graph; density budget; playable greybox.',
  production: 'Dress layers, POIs, combat camps, music binding, mobile perf pass.',
});

/**
 * Shared mobile-anime open-world rules.
 * Distances are metres in Resonant Wilds world space.
 */
export const OW_RULES = Object.freeze({
  // ZZZ: hub is a signature district; every function is a short walk.
  hub: {
    radius: HUB.radius,
    functionWalkMax: 28,
    lifeDetailSpacing: 6,
    signatureStylization: 'high',
  },
  // Genshin: gate → reveal → landmark spine.
  approach: {
    gateAt: HUB.radius + 2,
    revealAt: 140,
    landmarkCoreAt: 390,
    corridorHalfWidth: 28,
    identityBlendStart: 90,
    identityBlendEnd: 220,
  },
  // Nested dressing (Nikki "details all the time" + Genshin density).
  layers: {
    near: { maxDist: 40, mul: 1.85 },   // Nikki foot-detail denser
    mid: { maxDist: 120, mul: 1.2 },
    far: { maxDist: 280, mul: 0.6 },
  },
  // Landmark silhouette scale so hubs read destinations from the roads.
  landmarkScale: 1.35,
  // Exploration density budget per biome ring (targets, not hard caps).
  // Inspired by Genshin's POI/puzzle/resource mix — musicalized for Melodia.
  density: {
    // Cap identical combat camps so verb variety has room (Nikki/Genshin mix).
    campsPerBiome: 14,
    chestsPerBiome: 10,
    shrinesPerBiome: 3,
    sheetsPerBiome: 5,
    overlooksPerBiome: 4,
    chimeClustersPerBiome: 6,
    photoSpotsPerBiome: 4,
    musicGatesPerBiome: 2,
    cleansePerBiome: 2,
    ariaGatesPerBiome: 1,
    destinationsPerBiome: 2,
    minSpacing: {
      camp: 42,
      chest: 22,
      shrine: 48,
      sheet: 30,
      overlook: 55,
      chime: 28,
      photo: 40,
      musicgate: 48,
      cleanse: 40,
      ariagate: 55,
      destination: 70,
    },
  },
  // Mobile perf: keep streamed prop budgets honest on phones.
  mobile: {
    chunkPropBudget: 220,
    hubFringeOnlySoft: true,
  },
});

/** Per-biome impression cards (theme keywords + reveal + hero prop). */
export const BIOME_IMPRESSIONS = Object.freeze({
  sakura_terrace: {
    keywords: ['petal', 'waltz', 'terrace', 'welcome'],
    gateFeeling: 'A blossom arch opens the petal cantata.',
    vistaLine: 'Terraces cascade pink under a soft waltz sky.',
    heroProp: 'sakura',
    accent: '#f7b8d2',
    approachProps: [['flower', 1.4], ['sakura', 1.2], ['lantern', 1.3], ['grass', 1.5]],
  },
  liquid_cathedral: {
    keywords: ['nave', 'water', 'organ', 'procession'],
    gateFeeling: 'Pillars rise like an organ case beside the canal.',
    vistaLine: 'The basin opens — water and stone sing the same chord.',
    heroProp: 'pillar',
    accent: '#5fc6ff',
    approachProps: [['reed', 1.5], ['lily', 1.3], ['pillar', 1.1], ['lantern', 1.2]],
  },
  fugue_grotto: {
    keywords: ['subject', 'answer', 'gully', 'echo'],
    gateFeeling: 'Stalagmites answer each other across the path.',
    vistaLine: 'Branching gullies repeat the motif into shadow.',
    heroProp: 'stalagmite',
    accent: '#9a7bf0',
    approachProps: [['mushroom', 1.4], ['stalagmite', 1.3], ['rock', 1.2], ['bush', 1.2]],
  },
  cadence_crystal_ridge: {
    keywords: ['toccata', 'ridge', 'crystal', 'ascent'],
    gateFeeling: 'Crystal shards mark the climb like metronome ticks.',
    vistaLine: 'The ridge skyline flashes a toccata of light.',
    heroProp: 'crystal',
    accent: '#8a6cff',
    approachProps: [['crystal', 1.5], ['rock', 1.2], ['spire', 1.1], ['lantern', 1.2]],
  },
  aurora_glacier: {
    keywords: ['glacial', 'aurora', 'fugue', 'cold'],
    gateFeeling: 'Ice spines lean into an aurora hush.',
    vistaLine: 'Shelves of snow open under a slow glacial pulse.',
    heroProp: 'icespike',
    accent: '#7fc8ff',
    approachProps: [['pine', 1.4], ['icespike', 1.4], ['crystal', 1.1], ['rock', 1.1]],
  },
});

/**
 * Nikki Ability Outfit analogues — wardrobe slot → traversal identity.
 * Ethereal biomes each get one authored outfit beat (equip → space opens).
 */
export const ABILITY_OUTFITS = Object.freeze({
  mist_float: {
    id: 'mist_float', name: 'Mist Float', slot: 'shoes', slotLabel: 'Shoes',
    biome: 'choir_marsh', color: '#9fe6ff',
    lockedLine: 'Ability Outfit · Mist Float — equip Shoes in Wardrobe',
    readyLine: 'Mist Float ready — the fog will lift under your step',
    openTitle: 'Ability Outfit · Mist Float',
    openSub: 'Your shoes part the marsh fog',
  },
  prism_veil: {
    id: 'prism_veil', name: 'Prism Veil', slot: 'gown', slotLabel: 'Gown',
    biome: 'glass_orchard', color: '#c8b6ef',
    lockedLine: 'Ability Outfit · Prism Veil — equip a Gown in Wardrobe',
    readyLine: 'Prism Veil ready — glass stairs will answer your dress',
    openTitle: 'Ability Outfit · Prism Veil',
    openSub: 'Your gown refracts the orchard light',
  },
  nightbell_glide: {
    id: 'nightbell_glide', name: 'Nightbell Glide', slot: 'shoes', slotLabel: 'Shoes',
    biome: 'starlit_moor', color: '#ffd978',
    lockedLine: 'Ability Outfit · Nightbell Glide — equip Shoes in Wardrobe',
    readyLine: 'Nightbell Glide ready — the high shelf will hold your step',
    openTitle: 'Ability Outfit · Nightbell Glide',
    openSub: 'Your step rings the moor bells open',
  },
});

/** Ethereal biome → Ability Outfit id for that region's veil / float beat. */
export const ETHEREAL_ABILITY_BY_BIOME = Object.freeze({
  choir_marsh: 'mist_float',
  glass_orchard: 'prism_veil',
  starlit_moor: 'nightbell_glide',
});

/**
 * Nikki-style named micro-destinations (2 per biome).
 * Pins are { r, da, kit, gate } relative to biome angle — authored places, not RNG scatter.
 * gate: null | 'float' (Wardrobe shoes/gown / Ability Outfit) | 'purify' (Harmonize cleanse at mouth).
 */
export const BIOME_DESTINATIONS = Object.freeze({
  sakura_terrace: [
    { key: 'tea', name: 'Petal Tea Terrace', kit: 'tea', r: 175, da: 0.11, gate: null, line: 'Porcelain cups wait under a waltz of petals.' },
    { key: 'archive', name: 'Blossom Archive', kit: 'archive', r: 285, da: -0.12, gate: 'float', line: 'A cloister of sheets hangs above the terrace path.' },
  ],
  liquid_cathedral: [
    { key: 'quay', name: 'Canal Quay Choir', kit: 'quay', r: 180, da: -0.1, gate: null, line: 'Pilgrims once sang from this pier into the nave.' },
    { key: 'nave', name: 'Organ Nave Walk', kit: 'nave', r: 300, da: 0.09, gate: 'purify', line: 'Colonnades hold a dissonant hush until cleansed.' },
  ],
  choir_marsh: [
    { key: 'reed', name: 'Mist Choir Reedwalk', kit: 'quay', r: 178, da: 0.09, gate: null, line: 'Reeds hum a soft choir under the fog veil.', fashionPhoto: 'modulation' },
    { key: 'lantern', name: 'Lantern Marsh Atelier', kit: 'archive', r: 292, da: -0.1, gate: 'float', abilityOutfit: 'mist_float', line: 'Mist Float shoes lift you to the lantern atelier.', fashionPhoto: 'modulation' },
  ],
  fugue_grotto: [
    { key: 'amph', name: 'Echo Amphitheater', kit: 'amph', r: 190, da: 0.08, gate: null, line: 'Stone seats answer every footfall twice.' },
    { key: 'cave', name: 'Subject Cave', kit: 'cave', r: 310, da: -0.11, gate: 'purify', line: 'The subject theme sleeps behind a blot of dissonance.' },
  ],
  glass_orchard: [
    { key: 'prism', name: 'Prism Picnic Glade', kit: 'tea', r: 182, da: -0.08, gate: null, line: 'Glass leaves cast a fashion-ready light pool.', fashionPhoto: 'veil' },
    { key: 'mirror', name: 'Mirror Orchard Balcony', kit: 'stair', r: 298, da: 0.11, gate: 'float', abilityOutfit: 'prism_veil', line: 'Prism Veil gown unlocks the mirror balcony.', fashionPhoto: 'veil' },
  ],
  cadence_crystal_ridge: [
    { key: 'metro', name: 'Metronome Plaza', kit: 'metro', r: 185, da: -0.07, gate: null, line: 'Stepped plates tick a toccata into the ridge wind.' },
    { key: 'stair', name: 'Crystal Stair Garden', kit: 'stair', r: 295, da: 0.13, gate: 'float', line: 'Shard steps rise — wardrobe cadence required.' },
  ],
  starlit_moor: [
    { key: 'moongate', name: 'Starlit Moongate', kit: 'amph', r: 188, da: 0.07, gate: null, line: 'A moor ring waits for a gold Reprise photo.', fashionPhoto: 'reprise' },
    { key: 'bells', name: 'Bellflower Night Shelf', kit: 'shelf', r: 302, da: -0.12, gate: 'float', abilityOutfit: 'nightbell_glide', line: 'Nightbell Glide shoes reach the high shelf.', fashionPhoto: 'reprise' },
  ],
  aurora_glacier: [
    { key: 'shelf', name: 'Aurora Shelf', kit: 'shelf', r: 195, da: 0.1, gate: null, line: 'A glacial ledge opens under the green curtain.' },
    { key: 'hollow', name: 'Ice Choir Hollow', kit: 'hollow', r: 305, da: -0.09, gate: 'purify', line: 'Ice voices wait for Harmonize to thaw the mouth.' },
  ],
});

/** Attach impression + workflow rings onto each biome (called once from design consumers). */
export function biomeWorkflow(b) {
  const imp = BIOME_IMPRESSIONS[b.id] || {
    keywords: [b.style], gateFeeling: b.name, vistaLine: b.name, heroProp: 'rock', accent: '#ffd978', approachProps: b.props.slice(0, 4),
  };
  return {
    ...imp,
    stages: OW_STAGES,
    gate: polar(b.angle, OW_RULES.approach.gateAt),
    reveal: polar(b.angle, OW_RULES.approach.revealAt),
    core: { x: b.cx, z: b.cz },
    rings: [
      { name: 'approach', r0: 70, r1: 160, density: 1.25 },
      { name: 'midland', r0: 160, r1: 320, density: 1.0 },
      { name: 'heartland', r0: 320, r1: 520, density: 0.85 },
      { name: 'frontier', r0: 520, r1: WORLD_RADIUS - 40, density: 0.55 },
    ],
  };
}

function polar(angle, r) {
  return { x: Math.cos(angle) * r, z: Math.sin(angle) * r, angle, r };
}

/** How strongly a point should dress as this biome's identity (Genshin approach blend). */
export function approachIdentity(b, x, z) {
  const r = Math.hypot(x, z);
  const dAng = Math.abs(angleDiff(Math.atan2(z, x), b.angle));
  const corridor = 1 - smoothstep(0.12, 0.42, dAng);
  const along = smoothstep(OW_RULES.approach.identityBlendStart, OW_RULES.approach.identityBlendEnd, r);
  return clamp(corridor * along, 0, 1);
}

/** Layer multiplier for prop scattering relative to the player (Nikki near detail). */
export function layerMul(distToPlayer) {
  const L = OW_RULES.layers;
  if (distToPlayer <= L.near.maxDist) return L.near.mul;
  if (distToPlayer <= L.mid.maxDist) return lerp(L.near.mul, L.mid.mul, (distToPlayer - L.near.maxDist) / (L.mid.maxDist - L.near.maxDist));
  if (distToPlayer <= L.far.maxDist) return lerp(L.mid.mul, L.far.mul, (distToPlayer - L.mid.maxDist) / (L.far.maxDist - L.mid.maxDist));
  return L.far.mul * 0.35;
}

/** Density scale for a biome ring containing radius r. */
export function ringDensity(wf, r) {
  for (const ring of wf.rings) {
    if (r >= ring.r0 && r < ring.r1) return ring.density;
  }
  return 0.4;
}

/**
 * Place exploration POIs from the density budget.
 * Returns plain {type,x,z,...} descriptors for Activities to adopt.
 */
export function planExploration(b, bi, rng, occupied) {
  const wf = biomeWorkflow(b);
  const D = OW_RULES.density;
  const out = [];
  const take = (type, count, r0, r1, spread, spacing, extra = {}) => {
    let n = 0, guard = 0;
    while (n < count && guard++ < count * 40) {
      const a = b.angle + (rng() * 2 - 1) * spread;
      const r = r0 + rng() * (r1 - r0);
      const x = Math.cos(a) * r, z = Math.sin(a) * r;
      if (Math.hypot(x, z) < HUB.radius + 8) continue;
      if (occupied.some((p) => (p.x - x) ** 2 + (p.z - z) ** 2 < spacing * spacing)) continue;
      if (out.some((p) => (p.x - x) ** 2 + (p.z - z) ** 2 < spacing * spacing)) continue;
      const p = { type, biome: bi, x, z, ...extra };
      // Spacing probe only — Activities owns pushing into the live POI list.
      occupied.push({ x, z, type });
      out.push(p);
      n++;
    }
  };

  // Distinct verbs first along the approach corridor so density packing cannot crowd them out.
  // Deterministic corridor pins guarantee at least one of each verb per biome.
  const pin = (type, r, da, extra) => {
    const a = b.angle + da, x = Math.cos(a) * r, z = Math.sin(a) * r;
    if (Math.hypot(x, z) < HUB.radius + 8) return;
    const p = { type, biome: bi, x, z, ...extra };
    occupied.push({ x, z, type });
    out.push(p);
  };
  pin('musicgate', 168, 0.05, { name: 'Phrase Bridge', workflow: 'puzzle', open: false });
  pin('musicgate', 230, -0.08, { name: 'Phrase Bridge', workflow: 'puzzle', open: false });
  pin('cleanse', 145, 0.14, { name: 'Dissonant Blot', workflow: 'companion', cleared: false });
  pin('cleanse', 260, -0.16, { name: 'Dissonant Blot', workflow: 'companion', cleared: false });
  const etherealAbility = ETHEREAL_ABILITY_BY_BIOME[b.id] || null;
  const ab = etherealAbility ? ABILITY_OUTFITS[etherealAbility] : null;
  pin('ariagate', 250, 0.02, {
    name: ab ? `${ab.name} Veil` : 'Aria Veil',
    workflow: 'traversal', open: false, needAria: true,
    needSlot: ab?.slot || 'shoes',
    abilityOutfit: etherealAbility,
  });

  // Nikki named micro-destinations — authored places with Resonance Dew.
  const dests = BIOME_DESTINATIONS[b.id] || [];
  dests.forEach((d, di) => {
    pin('destination', d.r, d.da, {
      name: d.name, kit: d.kit, gate: d.gate || null, line: d.line,
      key: d.key, workflow: 'destination', revealed: false, dewTaken: false,
      needsPurify: d.gate === 'purify', needsFloat: d.gate === 'float', purified: d.gate !== 'purify',
      fashionPhoto: d.fashionPhoto || null,
      abilityOutfit: d.abilityOutfit || (d.gate === 'float' ? etherealAbility : null),
    });
    // Outfit → space → photo setpiece: a Whim Frame pinned at the destination that wants a fashion Encore tint.
    if (d.fashionPhoto) {
      pin('photo', d.r + 8, d.da + 0.02, {
        name: `${d.name} Fashion Frame`, workflow: 'fashion', challenge: true,
        fashionEncore: d.fashionPhoto, setpiece: true,
      });
    }
  });

  // Approach / midland get denser content (Genshin first-impression ring).
  take('overlook', D.overlooksPerBiome, 130, 360, 0.35, D.minSpacing.overlook, { name: `${b.name.split('—')[0].trim()} Overlook`, workflow: 'vista' });
  take('photo', D.photoSpotsPerBiome, 100, 420, 0.4, D.minSpacing.photo, { name: 'Whim Frame', workflow: 'impression', challenge: true });
  take('chime', D.chimeClustersPerBiome, 90, 480, 0.5, D.minSpacing.chime, { name: 'Resonance Chimes', workflow: 'detail' });

  // Core combat / reward density — counts tuned by ring weights.
  const campN = Math.round(D.campsPerBiome);
  take('camp', Math.ceil(campN * 0.35), 110, 200, 0.45, D.minSpacing.camp, { active: false, clearedAt: -999, enemies: [], ring: 'approach' });
  take('camp', Math.ceil(campN * 0.4), 200, 400, 0.5, D.minSpacing.camp, { active: false, clearedAt: -999, enemies: [], ring: 'midland' });
  take('camp', Math.floor(campN * 0.25), 400, 620, 0.45, D.minSpacing.camp, { active: false, clearedAt: -999, enemies: [], ring: 'frontier' });

  take('chest', D.chestsPerBiome, 100, 650, 0.55, D.minSpacing.chest, { openedAt: -999 });
  take('shrine', D.shrinesPerBiome, 140, 600, 0.5, D.minSpacing.shrine, { id: null, name: 'Music-Key Shrine', cdUntil: 0 });
  take('sheet', D.sheetsPerBiome, 120, 650, 0.55, D.minSpacing.sheet);

  // Stamp shrine/sheet/photo ids + Whim Frame facing prompts after placement.
  let si = 0, sh = 0, ph = 0, mg = 0, cl = 0, ag = 0, dest = 0;
  for (const p of out) {
    if (p.type === 'shrine') p.id = `shrine_${b.id}_${si++}`;
    if (p.type === 'sheet') p.id = `sheet_${b.id}_${sh++}`;
    if (p.type === 'photo') {
      p.id = `photo_${b.id}_${ph++}`;
      // Angle prompt: face the biome landmark (or a random scenic heading).
      p.aimAngle = Math.atan2(wf.core.x - p.x, wf.core.z - p.z);
      p.aimLabel = ph % 2 ? 'Face the landmark' : 'Frame the skyline';
      p.challenge = ph % 2 === 1 || D.photoSpotsPerBiome <= 3;
    }
    if (p.type === 'musicgate') p.id = `mgate_${b.id}_${mg++}`;
    if (p.type === 'cleanse') p.id = `cleanse_${b.id}_${cl++}`;
    if (p.type === 'ariagate') p.id = `agate_${b.id}_${ag++}`;
    if (p.type === 'destination') {
      p.id = `dest_${b.id}_${p.key || dest}`;
      dest++;
    }
  }
  return { pois: out, workflow: wf };
}

/** Prop count multiplier for a scatter sample under the workflow. */
export function propWorkflowMul(b, x, z, type, playerPos = null) {
  const wf = biomeWorkflow(b);
  const r = Math.hypot(x, z);
  let m = ringDensity(wf, r);
  m *= 0.85 + approachIdentity(b, x, z) * 0.55;
  if (playerPos) m *= layerMul(Math.hypot(x - playerPos.x, z - playerPos.z));
  // Boost hero / approach props along the corridor.
  const boosted = (wf.approachProps || []).some(([t]) => t === type);
  if (boosted) m *= 1.4 + approachIdentity(b, x, z) * 0.55;
  // Near-field flowers/grass get an extra Nikki "details at feet" bump.
  if (type === 'flower' || type === 'grass' || type === 'bush') m *= 1.15;
  return m;
}

/** Machine-readable recipe sheet for audits / README / future UE handoff. */
export function workflowManifest() {
  return {
    id: 'melodia.resonant_wilds.openworld_workflow.v1',
    researched: ['Infinity Nikki', 'Genshin Impact', 'Wuthering Waves', 'Zenless Zone Zero'],
    stages: OW_STAGES,
    rules: OW_RULES,
    biomes: BIOMES.map((b) => {
      const wf = biomeWorkflow(b);
      return {
        id: b.id,
        name: b.name,
        keywords: wf.keywords,
        gateFeeling: wf.gateFeeling,
        vistaLine: wf.vistaLine,
        gate: wf.gate,
        reveal: wf.reveal,
        core: wf.core,
        rings: wf.rings,
        destinations: BIOME_DESTINATIONS[b.id] || [],
        bpm: b.bpm,
        meter: b.meter,
        style: b.style,
      };
    }),
  };
}
