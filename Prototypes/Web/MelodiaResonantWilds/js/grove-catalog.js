// Canonical 100-asset Harmonic Grove catalog; derived verbatim from website main.
// Interactive INT_ and PICK_ objects are addressable assets, NOT generic terrain scatter.
export const GROVE_NAMES = Object.freeze([
  'FLR_bellflower_tall', 'FLR_bellflower_double', 'FLR_bellflower_triple',
  'FLR_bellflower_dwarf', 'FLR_bellflower_pearl',
  'FLR_moonfern_wide', 'FLR_moonfern_young', 'FLR_moonfern_spiral', 'FLR_moonfern_clump',
  'FLR_satin_grass', 'FLR_choral_grass', 'FLR_short_grass', 'FLR_fluffy_grass',
  'FLR_choir_reeds', 'FLR_shallow_reeds', 'FLR_high_reeds',
  'FUN_lilac_mooncaps', 'FUN_mini_mooncaps', 'FUN_pearl_fungi', 'FUN_violet_mooncaps',
  'GEO_moonstone_scatter', 'GEO_jade_boulders', 'GEO_shore_pebbles', 'GEO_rough_hearthstone',
  'GEO_choir_crystals', 'GEO_glassbuds', 'GEO_aether_cluster',
  'ARC_pearl_path', 'ARC_round_resonance_step', 'ARC_tessera_steps',
  'ARC_tuning_path_stone', 'ARC_pearl_column', 'ARC_ruined_column', 'ARC_column_pillar_small',
  'PRP_choral_chime', 'PRP_petite_chime', 'PRP_harmonic_seedpod',
]);

// Kit 02 is loaded opportunistically after base gameplay is ready.
export const GROVE_KIT02_NAMES = Object.freeze([
  "ARC_arched_trellis",
  "ARC_broken_lyre_gate",
  "ARC_garden_balustrade",
  "ARC_lyre_gate",
  "ARC_moonbridge",
  "ARC_pearl_stairs",
  "ARC_wall_corner",
  "ARC_wall_straight",
  "BUSH_jade_topiary",
  "BUSH_laceleaf_hedge",
  "BUSH_lavender_hedge",
  "BUSH_pearlescent_bramble",
  "BUSH_rosebell_hedge",
  "CAN_amethyst_oak",
  "CAN_blush_cherry",
  "CAN_cyan_cypress",
  "CAN_jade_bonsai",
  "CAN_lantern_sapling",
  "CAN_moonwillow",
  "POND_floating_pads",
  "POND_lily_pads",
  "POND_lotus_glow",
  "POND_riverfan",
  "POND_shellstone",
  "POND_singing_rushes",
  "PRP_celestial_signpost",
  "PRP_choral_bellpost",
  "PRP_dream_fountain",
  "PRP_harp_plinth",
  "PRP_note_obelisk",
  "PRP_resonance_cache",
  "PRP_waystone_monolith"
]);

// Kit 03 adds gameplay-ready visual prefabs. Their logic stays in the game.
export const GROVE_KIT03_NAMES = Object.freeze([
  "INT_checkpoint_spire",
  "INT_echo_bowl",
  "INT_harmony_switch",
  "INT_lyre_lock",
  "INT_song_prism",
  "INT_tuning_plinth",
  "ORN_breeze_ribbon",
  "ORN_choral_ring_chimes",
  "ORN_crescent_mobile",
  "ORN_lantern_chain",
  "ORN_memory_urn",
  "ORN_wisp_nest",
  "PICK_cyan_note",
  "PICK_dew_pearls",
  "PICK_gold_chord",
  "PICK_lavender_note",
  "PICK_moonseal",
  "PICK_rose_petals",
  "PICK_starshard",
  "SCAT_crystal_spores",
  "SCAT_fallen_pearl_log",
  "SCAT_hollow_moonstone",
  "SCAT_lichen_slates",
  "SCAT_moonmoss_patch",
  "SCAT_satin_root_tangle",
  "WAY_dual_milestones",
  "WAY_feather_banner",
  "WAY_harmonic_arrow",
  "WAY_lullaby_stone",
  "WAY_petite_goal_arch",
  "WAY_songwheel"
]);
export const GROVE_EXTRA_NAMES = Object.freeze([...GROVE_KIT02_NAMES, ...GROVE_KIT03_NAMES]);

// Match shapes by gameplay silhouette. Trees, ice, and other unmodelled
// characters retain their original visuals instead of being replaced with a bad mesh.
export const GROVE_TYPES = Object.freeze({
  sakura: ['CAN_blush_cherry', 'CAN_moonwillow', 'CAN_amethyst_oak', 'CAN_jade_bonsai'],
  pine: ['CAN_cyan_cypress', 'CAN_lantern_sapling'],
  lily: ['POND_lily_pads', 'POND_floating_pads', 'POND_lotus_glow'],
  flower: ['FLR_bellflower_tall', 'FLR_bellflower_double', 'FLR_bellflower_triple', 'FLR_bellflower_dwarf', 'FLR_bellflower_pearl'],
  rock: ['GEO_moonstone_scatter', 'GEO_jade_boulders', 'GEO_shore_pebbles', 'GEO_rough_hearthstone'],
  bell: ['FLR_bellflower_tall', 'FLR_bellflower_pearl', 'PRP_choral_chime', 'PRP_petite_chime'],
  note: ['PRP_harmonic_seedpod', 'PRP_petite_chime', 'PICK_cyan_note', 'PICK_lavender_note', 'PICK_gold_chord'],
  lantern: ['PRP_choral_chime', 'PRP_petite_chime'],
  pillar: ['ARC_pearl_column', 'ARC_ruined_column', 'ARC_column_pillar_small'],
  reed: ['FLR_choir_reeds', 'FLR_shallow_reeds', 'FLR_high_reeds'],
  mushroom: ['FUN_lilac_mooncaps', 'FUN_mini_mooncaps', 'FUN_pearl_fungi', 'FUN_violet_mooncaps'],
  crystal: ['GEO_choir_crystals', 'GEO_glassbuds', 'GEO_aether_cluster'],
  spire: ['GEO_aether_cluster', 'GEO_choir_crystals'],
  icespike: ['GEO_glassbuds', 'GEO_aether_cluster'],
  stalagmite: ['GEO_rough_hearthstone', 'GEO_moonstone_scatter'],
});

// Decorative sets intentionally vary by biome. All 37 assets are eligible
// for deterministic chunk placement (path stones, ferns, crystals and chimes).
const DECOR_BUSH = GROVE_KIT02_NAMES.filter(n => n.startsWith('BUSH_'));
const DECOR_CANOPY = GROVE_KIT02_NAMES.filter(n => n.startsWith('CAN_'));
const DECOR_SCATTER = GROVE_KIT03_NAMES.filter(n => n.startsWith('SCAT_'));
const DECOR_ORN = GROVE_KIT03_NAMES.filter(n => ['ORN_wisp_nest', 'ORN_memory_urn'].includes(n));
export const GROVE_DECOR = Object.freeze({
  sakura_terrace: GROVE_NAMES.filter(n => n.startsWith('FLR_') || n.startsWith('FUN_') || n.startsWith('PRP_')).concat(DECOR_BUSH, DECOR_CANOPY, DECOR_SCATTER),
  liquid_cathedral: GROVE_NAMES.filter(n => n.startsWith('ARC_') || n.includes('reeds') || n.includes('crystals') || n.includes('moonfern')).concat(DECOR_BUSH, DECOR_SCATTER),
  fugue_grotto: GROVE_NAMES.filter(n => n.startsWith('FUN_') || n.startsWith('GEO_') || n.includes('column')).concat(DECOR_SCATTER, DECOR_ORN),
  cadence_crystal_ridge: GROVE_NAMES.filter(n => n.startsWith('GEO_') || n.startsWith('ARC_') || n.startsWith('PRP_')).concat(DECOR_SCATTER),
  aurora_glacier: GROVE_NAMES.filter(n => n.startsWith('GEO_') || n.startsWith('FLR_') || n.includes('chime')).concat(DECOR_CANOPY.filter(n => n.includes('cypress')), DECOR_SCATTER),
});


export const GROVE_ALL_NAMES = Object.freeze([...GROVE_NAMES, ...GROVE_EXTRA_NAMES]);
export const GROVE_DECORATIVE_VARIANTS = Object.freeze({
  flower: ['FLR_bellflower_dwarf', 'FLR_bellflower_double'],
  bush: ['FLR_moonfern_young', 'BUSH_laceleaf_hedge'],
  grass: ['FLR_short_grass', 'FLR_choral_grass'],
  rock: ['GEO_jade_boulders', 'SCAT_hollow_moonstone'],
  crystal: ['GEO_choir_crystals', 'GEO_glassbuds'],
  sakura: ['CAN_blush_cherry', 'CAN_jade_bonsai'],
  pine: ['CAN_cyan_cypress', 'CAN_lantern_sapling'],
  lily: ['POND_lily_pads', 'POND_lotus_glow'],
  reed: ['FLR_choir_reeds', 'POND_singing_rushes'],
  mushroom: ['FUN_lilac_mooncaps', 'FUN_violet_mooncaps'],
  pillar: ['ARC_pearl_column', 'ARC_ruined_column'],
  bell: ['PRP_choral_chime', 'PRP_petite_chime'],
});
export const GROVE_HEIGHTS = Object.freeze({
  flower: 0.82, bush: 1.10, grass: 0.64, rock: 1.15,
  crystal: 3.0, sakura: 7.3, pine: 5.3, lily: 0.50,
  reed: 1.8, mushroom: 1.7, pillar: 9.0, bell: 2.7,
});
export const GROVE_INTERACTIVE = Object.freeze(GROVE_ALL_NAMES.filter(n =>
  n.startsWith('INT_') || n.startsWith('PICK_')));
