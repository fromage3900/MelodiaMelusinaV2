// Web-game design layer on top of the exported UE data (generated/ue_data.js).
// UE numbers (grades, windows, SP, Crescendo, Encore, toughness, elements, skills, enemies)
// come from the generated module; this file only adds what the ARPG needs on top.

import { UE } from './generated/ue_data.js';

export const RULES = UE.rules;
export const WORLD_SEED = UE.biomes[0]?.seed ?? 3900;

// ---------------------------------------------------------------------------
// Rhythm grades (rules JSON is the source; labels/colours are presentation)
// ---------------------------------------------------------------------------
const gm = RULES.rhythm.grade_multipliers;
const cg = RULES.crescendo.gain;
export const GRADE = {
  Perfect: { mult: gm.perfect, crescendo: cg.perfect, color: '#ffd978', label: 'PERFECT' },
  Great: { mult: gm.great, crescendo: cg.great, color: '#82e3ec', label: 'GREAT' },
  Good: { mult: gm.good, crescendo: cg.good, color: '#c9b6ef', label: 'GOOD' },
  Miss: { mult: gm.miss, crescendo: cg.miss, color: '#8d8698', label: 'MISS' },
};

// Musical dynamics are the Crescendo tiers: the meter is the rules' 0..crescendo_max.
export const DYNAMICS = [
  { at: 0, mark: 'pp', name: 'Pianissimo', crit: 0, speed: 0 },
  { at: 20, mark: 'p', name: 'Piano', crit: 0.02, speed: 0.02 },
  { at: 40, mark: 'mf', name: 'Mezzo-forte', crit: 0.04, speed: 0.04 },
  { at: 60, mark: 'f', name: 'Forte', crit: 0.07, speed: 0.06 },
  { at: 85, mark: 'ff', name: 'Fortissimo', crit: 0.1, speed: 0.08 },
];

export const DIFFICULTY = {
  standard: { name: 'Standard', windowScale: 1.0, rarityBonus: 0 },
  virtuoso: { name: 'Virtuoso', windowScale: 0.6, rarityBonus: 0.35 },
  assist: { name: 'Assist', windowScale: 1.35, rarityBonus: -0.2 },
};

// ---------------------------------------------------------------------------
// Elements (wheel from rules JSON)
// ---------------------------------------------------------------------------
export const ELEMENTS = RULES.elements.cycle;
export const ELEMENT_STYLE = {
  Forte: { color: '#ff7f6e', glyph: 'ƒ' },
  Stone: { color: '#d2ab7c', glyph: '◆' },
  Umbral: { color: '#9a7bf0', glyph: '☾' },
  Arcane: { color: '#e38bff', glyph: '✦' },
  Radiant: { color: '#ffe07a', glyph: '☀' },
  Gale: { color: '#8ff0b4', glyph: '≋' },
  Tide: { color: '#62c8ff', glyph: '∿' },
};
export function elementMultiplier(attacker, defender) {
  if (!attacker || !defender) return 1;
  if (RULES.elements.weakness[attacker] === defender) return RULES.elements.strong_multiplier;
  if (RULES.elements.resist[attacker] === defender) return RULES.elements.weak_multiplier;
  return 1;
}

export const MODIFIERS = Object.fromEntries(RULES.modifiers.map((m) => [m.id, m]));

// ---------------------------------------------------------------------------
// Biomes: identity from the Gaea setups, gameplay from here.
// angle = position around Shorewake (radians, XZ plane). Levels rise with order.
// ---------------------------------------------------------------------------
const BIOME_PLAY = {
  sakura_terrace: {
    order: 0, levels: [1, 9], bpm: 96, meter: 3, key: 62, mode: 'major', style: 'waltz',
    prog: [[0, 'maj'], [9, 'min'], [5, 'maj'], [7, 'maj']],
    elements: ['Radiant', 'Gale', 'Forte'], boss: 'SlimeRadianceWaltz', bossName: 'Maestra of the Petal Waltz',
    colors: { grass: '#a7d98f', grass2: '#f4bfd6', rock: '#b99f96', sand: '#f3dfc4', snow: '#fff4fa', fog: '#f6dbe7', water: '#8fd8e6', light: '#fff1e6' },
    props: [['sakura', 7], ['flower', 34], ['rock', 3], ['lantern', 1.2], ['bell', 2.5], ['note', 0.25]],
    motif: [0, 2, 4, 7, 4, 2],
  },
  liquid_cathedral: {
    order: 1, levels: [8, 17], bpm: 108, meter: 4, key: 63, mode: 'major', style: 'cathedral',
    prog: [[0, 'maj'], [7, 'maj'], [9, 'min'], [5, 'maj']],
    elements: ['Tide', 'Arcane'], boss: 'SlimeTideSurge', bossName: 'Cantor of the Liquid Nave',
    colors: { grass: '#7fc7a9', grass2: '#bfe6d8', rock: '#9fb1c2', sand: '#e7e0cf', snow: '#f4fbff', fog: '#cfe8f1', water: '#4fb8d8', light: '#eaf7ff' },
    props: [['pillar', 2.2], ['reed', 14], ['lily', 10], ['rock', 3], ['bell', 2], ['note', 0.35]],
    motif: [0, 4, 7, 11, 9, 7],
  },
  fugue_grotto: {
    order: 2, levels: [16, 25], bpm: 120, meter: 4, key: 62, mode: 'minor', style: 'fugue',
    prog: [[0, 'min'], [8, 'maj'], [3, 'maj'], [10, 'maj']],
    elements: ['Stone', 'Umbral'], boss: 'SlimeStonemaul', bossName: 'The Fugue Maw',
    colors: { grass: '#8a8f6e', grass2: '#6d6582', rock: '#6f6474', sand: '#b8a58c', snow: '#d9d4e6', fog: '#b7aec6', water: '#6aa6b8', light: '#f2e6ff' },
    props: [['stalagmite', 9], ['mushroom', 7], ['rock', 8], ['bell', 1.5], ['note', 0.3]],
    motif: [0, 3, 7, 5, 3, 2],
  },
  cadence_crystal_ridge: {
    order: 3, levels: [24, 33], bpm: 132, meter: 4, key: 57, mode: 'minor', style: 'toccata',
    prog: [[0, 'min'], [5, 'min'], [7, 'maj'], [0, 'min']],
    elements: ['Forte', 'Arcane', 'Radiant'], boss: 'SlimeMelodicStorm', bossName: 'Toccata Colossus',
    colors: { grass: '#9aa6c4', grass2: '#c9b8ea', rock: '#7d7896', sand: '#d8cfe6', snow: '#f3f0ff', fog: '#d6d0ee', water: '#7fb6e8', light: '#f7f2ff' },
    props: [['crystal', 10], ['rock', 6], ['spire', 1], ['bell', 1.5], ['note', 0.4]],
    motif: [0, 7, 12, 10, 7, 3],
  },
  aurora_glacier: {
    order: 4, levels: [32, 45], bpm: 84, meter: 4, key: 66, mode: 'minor', style: 'glacial',
    prog: [[0, 'min'], [8, 'maj'], [5, 'min'], [7, 'maj']],
    elements: ['Tide', 'Gale', 'Umbral'], boss: 'SlimeShadowWaltz', bossName: 'Aurora Fugue-Wyrm',
    colors: { grass: '#dbeaf4', grass2: '#bcd6ea', rock: '#8ea3b8', sand: '#e9f1f7', snow: '#ffffff', fog: '#d9e8f5', water: '#9fd6ee', light: '#eef8ff' },
    props: [['pine', 8], ['icespike', 6], ['rock', 4], ['bell', 1.5], ['note', 0.3]],
    motif: [0, 5, 7, 8, 7, 3],
  },
};

export const BIOMES = UE.biomes
  .filter((b) => BIOME_PLAY[b.id])
  .map((b) => {
    const play = BIOME_PLAY[b.id];
    const hr = b.height_range_m ? b.height_range_m[1] : 600;
    return {
      ...b,
      ...play,
      angle: -Math.PI / 2 + play.order * ((Math.PI * 2) / 5),
      amp: 7 + hr / 90,
      terrace: b.terrace_strength ?? 0,
      flow: b.flow_strength ?? 0.25,
      hasLakes: (b.graph_chain || []).includes('Lake') || (b.graph_chain || []).includes('SeaLevel'),
      radial: (b.graph_chain || []).includes('RadialGradient'),
    };
  })
  .sort((a, b) => a.order - b.order);

export const HUB = {
  id: 'hub', name: 'Shorewake Village', bpm: 90, meter: 4, key: 60, mode: 'major', style: 'morning',
  prog: [[0, 'maj'], [5, 'maj'], [9, 'min'], [7, 'maj']],
  colors: { grass: '#b4dea0', grass2: '#e9d6a8', rock: '#c0aa98', sand: '#f1e2c6', snow: '#fff', fog: '#f3e6dc', water: '#86d4e4', light: '#fff4e6' },
  radius: 60,
};

export const RIFT_STYLE = {
  id: 'rift', name: 'Resonance Rift', meter: 4, key: 61, mode: 'minor', style: 'rift',
  prog: [[0, 'min'], [1, 'maj'], [8, 'maj'], [7, 'maj']],
  colors: { grass: '#3b2a55', grass2: '#5b3d78', rock: '#2a2140', sand: '#6b5590', snow: '#c8b4ff', fog: '#1d1430', water: '#7b5cff', light: '#d9c8ff' },
};

export const WORLD_RADIUS = 700;

// ---------------------------------------------------------------------------
// Skills: every UE skill chart becomes a castable skill. `kind` picks the
// web delivery shape; SP cost, power, element and MIDI notes come from UE.
// cd is in beats, so faster biomes literally cycle skills faster.
// ---------------------------------------------------------------------------
export const SKILL_KIT = {
  Chart_Forte_CadenceStrike: { kind: 'strike', range: 7, width: 2.6, coef: 1.6, cd: 6, tough: 1.4, desc: 'Dash through a line of foes and cut on the beat.' },
  Chart_Forte_Slam: { kind: 'slam', radius: 4, coef: 1.8, cd: 8, tough: 1.8, desc: 'Leap and slam a crowd. A breaker.' },
  Chart_Forte_Beat: { kind: 'cone', range: 6, angle: 85, coef: 1.4, cd: 4, tough: 1.0, desc: 'A driving cone of sound.' },
  Chart_Forte_Bassline: { kind: 'wave', range: 11, width: 3, coef: 1.3, cd: 5, knock: 4, tough: 1.2, desc: 'A low bass wave that shoves enemies back.' },
  Chart_Forte_BeatWave: { kind: 'ringwave', radius: 9, coef: 1.3, cd: 8, tough: 1.0, desc: 'An expanding ring of rhythm.' },
  Chart_Forte_EchoBurst: { kind: 'echo', radius: 4.6, coef: 1.2, echoes: 2, cd: 10, tough: 1.0, desc: 'Burst, then echo on the next beats.' },
  Chart_Forte_Rise: { kind: 'pulses', radius: 4.2, coef: 0.95, count: 3, cd: 12, tough: 1.2, desc: 'Three rising pulses, one per beat.' },
  Chart_Gale_Whirlwind: { kind: 'whirl', radius: 3.8, coef: 0.6, beats: 2, cd: 8, tough: 0.9, desc: 'Spin for two beats, cutting everything near.' },
  Chart_Gale_Tornado: { kind: 'tornado', coef: 0.5, cd: 8, tough: 0.8, desc: 'Loose a travelling tornado.' },
  Chart_Gale_StormChase: { kind: 'bolts', count: 5, coef: 0.6, cd: 8, tough: 0.6, desc: 'Five homing gusts chase enemies.' },
  Chart_Gale_Burst: { kind: 'cone', range: 6.5, angle: 110, coef: 1.2, knock: 5, cd: 6, tough: 0.9, desc: 'Blast a wide cone and scatter foes.' },
  Chart_Gale_WindTune: { kind: 'dash', dist: 8, coef: 0.9, buff: 'HasteDance', cd: 4, tough: 0.9, desc: 'Glide forward and gain Haste Dance.' },
  Chart_Radiant_LullabyMend: { kind: 'heal', heal: 0.3, cd: 12, niche: 'Calm', desc: 'Heal 30% HP and cleanse. Perfect heals more.' },
  Chart_Radiant_Shine: { kind: 'beam', range: 14, width: 1.9, coef: 1.5, cd: 4, tough: 1.0, desc: 'A piercing beam of light.' },
  Chart_Radiant_Flare: { kind: 'projectile', speed: 26, radius: 2.8, coef: 1.6, cd: 6, tough: 1.0, desc: 'A flare that bursts on impact.' },
  Chart_Radiant_Sparkle: { kind: 'nova', radius: 4.8, coef: 1.1, cd: 4, tough: 0.8, desc: 'A sparkling nova around you.' },
  Chart_Tide_Wave: { kind: 'wave', range: 12, width: 3.6, coef: 1.35, knock: 5, cd: 6, tough: 1.8, desc: 'A breaking tide. Big toughness damage.' },
  Chart_Tide_AbyssalSong: { kind: 'pool', radius: 4.4, coef: 0.4, bars: 2, cd: 10, tough: 0.5, desc: 'A singing pool that slows and drowns.' },
  Chart_Stone_Rock: { kind: 'projectile', speed: 22, radius: 2, coef: 1.3, cd: 3, tough: 1.2, desc: 'Hurl a resonant stone.' },
  Chart_Stone_RockBurst: { kind: 'meteor', radius: 3.6, count: 3, coef: 1.6, cd: 10, tough: 1.6, desc: 'Three stones fall on the beat.' },
  Chart_Stone_TerraFirma: { kind: 'shield', shield: 0.3, bars: 4, buff: 'GuardHymn', cd: 16, niche: 'Calm', desc: 'Shield for 30% HP and gain Guard Hymn.' },
  Chart_Arcane_Flare: { kind: 'projectile', speed: 30, radius: 1.8, coef: 1.25, cd: 3, tough: 0.8, desc: 'A quick arcane bolt.' },
  Chart_Arcane_CosmicResonance: { kind: 'meteor', radius: 3.4, count: 7, coef: 1.15, cd: 16, tough: 1.0, desc: 'Rain seven cosmic notes over two bars.' },
  Chart_Arcane_Shadow: { kind: 'projectile', speed: 28, radius: 1.8, coef: 1.2, cd: 3, tough: 0.8, desc: 'A shadowed bolt.' },
  Chart_Arcane_ShadowBolt: { kind: 'bolts', count: 3, coef: 1.1, cd: 8, tough: 0.8, name: 'Shadow Bolt Volley', desc: 'Three seeking shadow bolts.' },
  Chart_Arcane_Spellweaver: { kind: 'orbit', count: 3, coef: 0.65, bars: 3, cd: 12, tough: 0.5, desc: 'Weave three orbiting notes around you.' },
  Chart_Arcane_SummonFlux: { kind: 'summon', coef: 0.7, bars: 4, cd: 16, tough: 0.5, desc: 'Summon a metronome that fires every beat.' },
  Chart_Umbral_DissonantSilence: { kind: 'debuff', radius: 6.5, vuln: 0.25, bars: 2, coef: 0.8, cd: 12, niche: 'Sad', tough: 1.0, desc: 'Silence foes and make them Vulnerable.' },
  Chart_Umbral_Shade: { kind: 'dash', dist: 7, coef: 1.2, cd: 4, tough: 0.8, desc: 'Dance through shadows, cutting on the way.' },
  Chart_Umbral_ShadowDance: { kind: 'cone', range: 5.2, angle: 130, coef: 1.3, cd: 4, tough: 0.9, desc: 'A sweeping umbral dance.' },
  Chart_Umbral_Shadowfall: { kind: 'meteor', radius: 6.8, count: 1, coef: 3.4, delay: 2, cd: 14, tough: 2.0, desc: 'After two beats, the sky falls.' },
};

export const STARTING_SKILLS = ['Chart_Forte_CadenceStrike', 'Chart_Gale_Whirlwind', 'Chart_Radiant_LullabyMend', 'Chart_Arcane_Flare'];

export const SKILLS = UE.skills
  .filter((s) => SKILL_KIT[s.id])
  .map((s) => ({ ...s, ...SKILL_KIT[s.id], name: SKILL_KIT[s.id].name || s.name }))
  .sort((a, b) => a.tier - b.tier || a.sp - b.sp || a.name.localeCompare(b.name));

{
  // Unlock levels: tier 1 early, tier 3 late. Starting skills are free.
  const perTier = { 1: [2, 9], 2: [10, 24], 3: [22, 40] };
  const byTier = { 1: [], 2: [], 3: [] };
  for (const s of SKILLS) if (!STARTING_SKILLS.includes(s.id)) byTier[s.tier].push(s);
  for (const t of [1, 2, 3]) {
    const list = byTier[t];
    list.forEach((s, i) => {
      const [a, b] = perTier[t];
      s.unlockLevel = Math.round(a + ((b - a) * i) / Math.max(1, list.length - 1));
    });
  }
  for (const s of SKILLS) if (STARTING_SKILLS.includes(s.id)) s.unlockLevel = 1;
}
export const SKILL_BY_ID = Object.fromEntries(SKILLS.map((s) => [s.id, s]));

// ---------------------------------------------------------------------------
// Enemies (UE roster) grouped per biome by element.
// ---------------------------------------------------------------------------
export const ENEMIES = UE.enemies;
export const ENEMY_BY_ID = Object.fromEntries(ENEMIES.map((e) => [e.id, e]));
for (const b of BIOMES) {
  const pool = ENEMIES.filter((e) => b.elements.includes(e.element) && e.id !== b.boss).sort((x, y) => x.hp - y.hp);
  const cut = Math.max(2, Math.floor(pool.length * 0.65));
  b.trash = pool.slice(0, cut);
  b.elites = pool.slice(Math.max(0, cut - 2));
}
export const RIFT_POOL = ENEMIES.slice().sort((x, y) => x.hp - y.hp);

export const ELITE_AFFIXES = [
  { id: 'fortissimo', name: 'Fortissimo', desc: '+60% health' },
  { id: 'presto', name: 'Presto', desc: 'Attacks every other beat' },
  { id: 'canon', name: 'Canon', desc: 'Every attack echoes one beat later' },
  { id: 'dissonant', name: 'Dissonant', desc: 'Leaves a dissonant pool on death' },
];

// ---------------------------------------------------------------------------
// Loot. Slots are the Wardrobe slots; Opus arias come from DT_Artifacts and
// the authored rhythm-skill DataAssets.
// ---------------------------------------------------------------------------
export const RARITIES = [
  { id: 'common', name: 'Common', color: '#ddd7e6', weight: 58, affixes: 0, mult: 1.0 },
  { id: 'tuned', name: 'Tuned', color: '#7fe69a', weight: 27, affixes: 1, mult: 1.08 },
  { id: 'resonant', name: 'Resonant', color: '#6fb8ff', weight: 11, affixes: 2, mult: 1.17 },
  { id: 'virtuoso', name: 'Virtuoso', color: '#c690ff', weight: 3.5, affixes: 3, mult: 1.28 },
  { id: 'opus', name: 'Opus', color: '#ffae45', weight: 0.5, affixes: 3, mult: 1.42 },
];

export const SLOTS = [
  { id: 'instrument', name: 'Instrument', icon: '🎻', bases: [['Baton', 'melee'], ['Violin Bow', 'melee'], ['Chime Staff', 'melee'], ['Flute', 'ranged'], ['Harp', 'ranged'], ['Lyre', 'ranged']] },
  { id: 'head', name: 'Headpiece', icon: '👑', bases: [['Tiara'], ['Ribbon'], ['Circlet'], ['Veil'], ['Sun Hat']] },
  { id: 'gown', name: 'Gown', icon: '👗', bases: [['Gown'], ['Coat'], ['Robe'], ['Dress'], ['Kimono']] },
  { id: 'gloves', name: 'Gloves', icon: '🧤', bases: [['Gloves'], ['Mitts'], ['Gauntlets']] },
  { id: 'shoes', name: 'Shoes', icon: '👠', bases: [['Slippers'], ['Boots'], ['Heels']] },
  { id: 'charm', name: 'Charm', icon: '🐚', bases: [['Shell Charm'], ['Clef Pendant'], ['Brooch'], ['Music Box']] },
];
export const SLOT_BY_ID = Object.fromEntries(SLOTS.map((s) => [s.id, s]));

export const AFFIXES = [
  { key: 'dmg', text: '+{v}% Damage', min: 3, max: 12, unit: '%' },
  { key: 'elem', text: '+{v}% {e} Damage', min: 6, max: 22, unit: '%', element: true },
  { key: 'crit', text: '+{v}% Crit Chance', min: 2, max: 7, unit: '%' },
  { key: 'critdmg', text: '+{v}% Crit Damage', min: 10, max: 36, unit: '%' },
  { key: 'perfectms', text: '+{v}ms Perfect Window', min: 4, max: 16, unit: 'ms' },
  { key: 'hp', text: '+{v} Max HP', flat: 6.5 },
  { key: 'armor', text: '+{v} Poise', flat: 1.7 },
  { key: 'speed', text: '+{v}% Move Speed', min: 3, max: 10, unit: '%' },
  { key: 'encore', text: '+{v}% Encore Gain', min: 8, max: 25, unit: '%' },
  { key: 'harmony', text: '{v}% chance: Harmony on Great', min: 10, max: 35, unit: '%' },
  { key: 'cdr', text: '+{v}% Cooldown Reduction', min: 3, max: 10, unit: '%' },
  { key: 'gold', text: '+{v}% Gold Find', min: 10, max: 40, unit: '%' },
  { key: 'break', text: '+{v}% Toughness Damage', min: 8, max: 28, unit: '%' },
  { key: 'drain', text: '{v}% Resonant Drain', min: 1, max: 4, unit: '%' },
  { key: 'magic', text: '+{v}% Rarity Find', min: 5, max: 20, unit: '%' },
];
export const AFFIX_BY_KEY = Object.fromEntries(AFFIXES.map((a) => [a.key, a]));

const ARTIFACT_ARIA = Object.fromEntries(UE.artifacts.map((a) => [a.artifact_id, a]));
export const ARIAS = [
  { id: 'BurningChord', name: ARTIFACT_ARIA.BurningChord?.display_name || 'Burning Chord', desc: 'Skills deal +50% damage but cost +1 Harmony.' },
  { id: 'EchoingBeat', name: ARTIFACT_ARIA.EchoingBeat?.display_name || 'Echoing Beat', desc: 'Perfect hits echo for 50% damage on the next beat.' },
  { id: 'SwiftTempo', name: ARTIFACT_ARIA.SwiftTempo?.display_name || 'Swift Tempo', desc: '+20% move speed. Perfect dodges have no cooldown.' },
  { id: 'StoneCarapace', name: ARTIFACT_ARIA.StoneCarapace?.display_name || 'Stone Carapace', desc: 'Take 20% less damage.' },
  { id: 'CrescendoWave', name: 'Crescendo Wave', desc: 'At forte (f) or louder, skills gain +35% area.' },
  { id: 'DownbeatBreak', name: 'Downbeat Break', desc: 'Hits on the downbeat deal triple toughness damage.' },
  { id: 'HarmonyShield', name: 'Harmony Shield', desc: 'Perfect hits grant a 3% Max HP shield (up to 30%).' },
  { id: 'TempoShift', name: 'Tempo Shift', desc: 'Perfect dodges cut all skill cooldowns by 4 beats.' },
  { id: 'DissonantSilence', name: 'Dissonant Silence', desc: 'Your hits make enemies Vulnerable (+15% damage) for a bar.' },
  { id: 'SkyboundRefrain', name: 'Skybound Refrain', desc: 'Every 4th Perfect calls a Skybound note strike (300%).' },
  { id: 'PetalCadence', name: 'Petal Cadence', desc: 'Every 3rd basic hit fires a spiral of petal blades.' },
  { id: 'ChoralFleece', name: 'Choral Fleece', desc: 'Your Choral Sheep harmonizes every bar instead of every 2 bars.' },
];
export const ARIA_BY_ID = Object.fromEntries(ARIAS.map((a) => [a.id, a]));

export const SHARDS = UE.tokens.filter((t) => t.Element).map((t) => ({ id: t.TokenID, name: t.DisplayName, element: t.Element, value: t.Value, rarity: t.Rarity }));
export const SHARD_BY_ELEMENT = Object.fromEntries(SHARDS.map((s) => [s.element, s]));

// Forge honing (Lost Ark style): chance falls with level, failures bank pity.
export function honeChance(level) {
  if (level < 5) return 1;
  if (level < 8) return 0.75;
  if (level < 11) return 0.55;
  if (level < 13) return 0.4;
  return 0.3;
}
export const HONE_MAX = 15;

// Blessings from DT_Blessings are bought with Golden Notes (bounty/rift currency).
export const BLESSINGS = UE.blessings;
export const BURDENS = UE.burdens;

export const BOUNTY_TEMPLATES = [
  { id: 'kill_element', text: 'Defeat {n} {e} slimes', n: [12, 24] },
  { id: 'perfects', text: 'Land {n} Perfect hits', n: [40, 90] },
  { id: 'crescendo', text: 'Reach ff (Fortissimo) {n} times', n: [2, 4] },
  { id: 'chests', text: 'Open {n} chests', n: [2, 4] },
  { id: 'elites', text: 'Defeat {n} elite choruses', n: [2, 4] },
  { id: 'rift', text: 'Clear {n} Resonance Rift', n: [1, 1] },
  { id: 'shrine', text: 'Attune {n} music-key shrine', n: [1, 1] },
  { id: 'kills', text: 'Defeat {n} slimes', n: [30, 60] },
];

export function xpToNext(level) {
  return Math.floor(45 * Math.pow(level, 1.55) + 25 * level);
}
export const MAX_LEVEL = 60;

export const TUTORIAL = [
  'Drag on the left to move. The ring on ⚔ closes on every beat.',
  'Tap ⚔ as the ring closes: PERFECT ×1.5 · GREAT ×1.25 · GOOD ×1.0 · MISS ×0.55.',
  'On-beat hits build Crescendo: pp → p → mf → f → ff. Louder = crit & speed.',
  'Skills cost Harmony ◆. Perfect basic hits give Harmony back.',
  'Fill the Encore gauge, then unleash ENCORE for triple damage.',
  'Enemy attacks land on the beat. Dodge on the landing beat for a PERFECT DODGE.',
];
