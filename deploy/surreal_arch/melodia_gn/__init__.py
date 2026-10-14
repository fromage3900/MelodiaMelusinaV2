from .core import safe_node, link_sockets, color_node, label_tree, new_geometry_tree, make_group_input, make_group_output, TREE_TYPES, GROUP_BUILDERS, GROUP_METADATA, CATEGORY_META, STUDIO_LABELS, TREE_LABEL_MAP, TREE_DESCRIPTIONS, TREE_CATEGORY_MAP, TREE_CATEGORIES, register_builder, get_param_schema, PARAM_SCHEMAS
from .logging import log, install_pref_bridge
from .primitives import build_circular_array, build_linear_array, build_grid_array, build_bounding_box, build_instance_on_spline
from .profiles import build_column, build_baluster, build_post, build_rail, build_star_finial, build_lissajous_curve
from .math_ops import build_add_geometry, build_subtract_geometry, build_power_scale, build_exponent_blend, build_store_named_attr, build_attribute_math
from .effects import build_effect_displace, build_effect_wave, build_effect_cast, build_effect_wireframe, build_effect_smooth, build_effect_magic
from .ornament import build_ornament_vine, build_ornament_radial, build_ornament_grid, build_ornament_frame, build_ornament_panel
from .filigree import build_filigree_spiral, build_decorative_rosette, build_harmonic_orb
from .music import build_music_note_head, build_music_treble_clef, build_music_staff, build_music_harmonic, build_music_phrase, build_music_sheet_rail
from .operations import build_op_iterate, build_op_bounded
from .mesh_tools import (
    build_bevel_profile, build_weighted_bevel, build_multi_bevel,
    build_inset_faces, build_poke_faces, build_subdivision_surface,
    build_remesh_dual, build_smooth_laplacian,
)
from .castle import build_castle_crenellation, build_castle_wall_segment, build_castle_tower, build_castle_gatehouse, build_castle_gothic_window, build_castle_buttress, build_castle_keep, build_castle_curtain_wall, build_castle_machicolations, build_castle_spiral_stairs, build_castle_assembler
from .recursive_castle import build_recursive_castle_spire, build_endless_escher_bridge, build_math_gothic_cathedral
from .polyhedra_gn import build_polyhedra_icosahedron, build_polyhedra_dodecahedron, build_greybox_room_kit
from .structures import build_gazebo, build_arch, build_portico
from .nikki_quarter import build_nikki_quarter
from .escher_belvedere import build_escher_belvedere
from .escher_penrose_stairs import build_escher_penrose_stairs
from .escher_waterfall import build_escher_waterfall
from .sky_observatory import build_sky_observatory
from .stack import CLASSES, register_props, unregister_props, MEL_GN_PT_stack
from .bake import bake_all, save_library, load_library
from .water import (
    build_water_gerstner, build_water_ripples, build_water_foam, build_water_current_markers,
)
from .music_instruments import build_brass_pipe, build_reed_body, build_bell_chime
from . import music_aaa  # noqa: F401 - AAA musical kit (registers via register_builder)
from . import melodia_kit_v2  # noqa: F401 - Kit v2: celesta/glockenspiel/kalimba + harp/waveform v2
from . import melodia_kit_v3  # noqa: F401 - Kit v3: jingle-driven tower/gate/plaza/nook
from . import melodia_kit_v4  # noqa: F401 - Kit v4: timpani/tubular/dulcimer/bamboo
from . import melodia_kit_baroque  # noqa: F401 - Baroque lens: harpsichord/violin/organ/lute (spatial)
from . import chimes_gn  # noqa: F401 - GN chime family (ET-tuned, port of chime_row physics)
from . import music_harps_real  # noqa: F401 - Realistic harps: concert/Ur lyre/kora/siku
from . import musical_mesh_variants  # noqa: F401 - Musical mesh variant sweep (wave/harmonic/pulse/seeded)
from . import phyllotaxis  # noqa: F401 - golden-angle 137.5077 spiral + pave (shared w/ brooch genomes)
from . import horn_dangl  # noqa: F401 - ornate dangle row along a host curve
from . import ue_proxy_kit  # noqa: F401 — UE proxy materials (halftone, fabric, crystal)
from . import music_euro_remainder  # noqa: F401 - Cascading beams, rose window, lancet (P2 remainder)
from . import music_terrain  # noqa: F401 - Walkable roll field/staff bridge terrain
from . import audio_terrain  # noqa: F401 - Blender 5.2 native audio terrain/mesh systems
from . import companion_flock  # noqa: F401 - Choral Sheep flock + wool bloom builders
from . import planetary_terrain  # noqa: F401 - v3 deterministic planetary musical terrain
from . import infinity_nikki_kit  # noqa: F401 - Infinity Nikki expanded wardrobe kit (bloom pavilion/nook/runway)
from . import nikki_musical_decorations  # noqa: F401 - Nikki musical decorations (star/heart/bead generators)
from . import nikki_advanced_decorations  # noqa: F401 - Nikki advanced (SDF, repeat zones, capture/store)
from . import mother  # noqa: F401 - Faraway Mother Monolith kit (8 builders)
from . import white_current  # noqa: F401 - White Current Monolith kit (6 builders)
from . import god_molts  # noqa: F401 - God That Molts Monolith kit (8 builders)
from .notation_extras import build_music_bass_clef, build_music_beam_cluster, build_music_triplet_note, build_music_chord_stack, build_music_fermata, build_music_repeat_bar, build_music_time_signature, build_music_stand
from . import music_port  # noqa: F401 - note_head, staff, treble_clef, sheet_music_railing, cascading_beams + euro
from . import music_higgsas_instruments  # noqa: F401 - Higgsas-led instruments (bandoneon/sax/harmonica/music box/theremin/hurdy-gurdy)
from . import music_percussion_vessels  # noqa: F401 - steelpan/gong/ocarina (P4 gap fill)
from . import music_wind_percussion  # noqa: F401 - flute/clarinet/recorder/marimba/vibraphone/melodica (P4 wave 2)
from .ornament_extras import build_ornament_rosette_sixpetal, build_ornament_scallop_band, build_ornament_keyhole_frame, build_filigree_corner_volute, build_filigree_finial_cross, build_filigree_wreath_ring
from .ribbon import (
    build_ribbon_curve, build_lissajous_ribbon, build_closed_ribbon, build_violin_bow,
)
from .set_dressing import (
    build_water_them_structure, build_water_them_gazebo, build_water_them_arch,
    build_water_them_portico, build_water_them_wall, build_water_them_curtain,
    build_water_them_fountain, build_water_them_dock, build_water_them_deck,
    build_water_them_bridge, build_water_them_canal, build_water_them_waterfall,
    build_music_them_structure, build_music_them_gazebo, build_music_them_arch,
    build_music_them_portico, build_music_them_wall, build_music_them_curtain,
    build_music_them_bandstand, build_music_them_stage, build_music_them_shell,
    build_music_them_recital, build_music_them_bridge, build_music_them_fountain,
)
from .env_extras import build_env_lily_pond, build_env_stepping_stones, build_env_reeds_patch, build_env_buoy_line, build_env_market_stall, build_env_campfire_ring, build_env_village_well, build_env_lantern_post, build_env_hedgerow, build_env_waterfall_pool
from .castle_extras import build_castle_corner_turret, build_castle_portcullis, build_castle_arrow_slit, build_castle_hoarding, build_castle_siege_tower, build_castle_barbican, build_pergola_walkway
from .melusina_house import build_melusina_house_round_interior  # noqa: F401 - Melusina house round-plan interior
from . import melodia_house  # noqa: F401 - unified house module: genome room shell (mh6) + AAA kit
from . import melusina_house_foundation  # noqa: F401 - Melusina House foundation/pod builders
from . import garment_material_id  # noqa: F401 - per-face material ID assignment for garments
from . import garment_smart_bevel  # noqa: F401 - material-aware edge bevel (fabric round, trim sharp)
from . import garment_trim_uv  # noqa: F401 - trim UV layout for garment texturing
from . import garment_vertex_ao  # noqa: F401 - vertex-baked AO for garment detail
from . import dreamy_gothic_arch  # noqa: F401 - slim lancet arch with gold tracery inlay
from . import rose_window  # noqa: F401 - rose window GN builders
from . import curved_wall  # noqa: F401 - adjustable arc wall for dreamy interiors
from . import ornament_strip  # noqa: F401 - gold bead distribution along curves
from . import gold_light_strip  # noqa: F401 - emissive gold LED strip lighting
from . import barrel_vault_kit  # noqa: F401 - barrel vault ceiling GN builder
from . import angel_wings  # noqa: F401 - Angel wing pair + feather row builders (was live-only, untracked)
from . import garment_ribbon  # noqa: F401 - Garment ribbon trail builders (was live-only, untracked)
from . import reaver_wings  # noqa: F401 - Reaver wing builders (was live-only, untracked)
from . import bionic_joint  # noqa: F401 - Bionic joint / ball-seat builder (was live-only, untracked)
from . import aesthetic_fx  # noqa: F401
from . import scifi_fx  # noqa: F401
from . import zen_kit  # noqa: F401 - zen/castle/asian absorbed from monolith (P2)
from . import castle_kit  # noqa: F401
from . import asian_kit  # noqa: F401
from . import civic_kit  # noqa: F401
from . import experimental_kit  # noqa: F401
from . import euro_kit  # noqa: F401
from . import core_forms_kit  # noqa: F401
from . import core_forms_port  # noqa: F401 - tower, organic, hybrid, curved_wall, building
from . import walls_kit  # noqa: F401
from . import paris_wall_detail  # noqa: F401 - Paris lane v2 (Melusina study)
from . import paris_track_a  # noqa: F401 - Track A: FountainLoop + DayNightFacade (owner queue 2026-09-21; kept: still registered on main, file retained)
from . import paris_escher_ladder  # noqa: F401 - Track A: Belvedere ladder device
from . import paris_fountain_loop  # noqa: F401 - Track A: self-feeding courtyard fountain
from . import paris_daynight_facade  # noqa: F401 - Track A: day/night duality facade
from . import paris_mansard  # noqa: F401 - Track A: Haussmann roof band
from . import paris_penrose_arch  # noqa: F401 - Track A: tribar doorway
from . import paris_metamorphosis_frieze  # noqa: F401 - Track A: morph band
from . import brutalist_office  # noqa: F401 - BRUTALIST: office block
from . import brutalist_cubicles  # noqa: F401 - BRUTALIST: cubicle farm
from . import brutalist_city  # noqa: F401 - BRUTALIST: 2D city block massing
from . import brutalist_roofs  # noqa: F401 - BRUTALIST: roof system (6 styles)
from . import office_props  # noqa: F401 - OFFICE: film interior prop kit
from . import higgsas_pipeline  # noqa: F401 - single Higgsas loader (replaces 4 copies)

from . import buildings_kit  # noqa: F401 - buildings absorbed (P2)
from . import misc_props_kit  # noqa: F401
from . import materials_kit  # noqa: F401 - materials absorbed (P2)
from . import filigree_kit  # noqa: F401 - filigree absorbed (P2)  # noqa: F401 - misc props absorbed (P2)  # noqa: F401 - walls absorbed from monolith (P2)  # noqa: F401 - core forms absorbed from monolith (P2)  # noqa: F401 - euro-classical absorbed from monolith (P2)  # noqa: F401 - experimental+2 core-forms absorbed (P2)  # noqa: F401 - civic absorbed from monolith (P2)  # noqa: F401  # noqa: F401 - 7 effect passes absorbed from monolith (P2)  # noqa: F401 - 70 effect passes absorbed from monolith (P2)
from . import greybox_port  # noqa: F401 - greybox room/corridor convergence
from . import house_dress  # noqa: F401 - mh_* dressing builders (piano walk, sheet rail, lanterns...) - unified house module: genome room shell (mh6) + AAA kit (cornice/dentil/scallop/lissajous)
from .melodia_city_gen import (  # noqa: F401 - Melodia City Gen kit (register via register_builder)
    build_city_house_cell, build_city_avenue, build_city_block,
    build_city_plan_round, build_city_plan_salon, build_city_plan_courtyard,
    build_city_corridors,
)
from .geometry_extras import (
    build_vortex_twist, build_radial_wave, build_shell_thicken, build_edge_ring_inset,
    build_symmetry_weld, build_vertex_relax, build_attr_ramp_mix, build_attr_vector_rotate,
    build_edge_band_weight, build_gear, build_stepped_pyramid, build_torus_cross,
    build_egg_dart_rail, build_baluster_collar, build_op_power_clamp,
)
from .pcg_integration import (
    pcg_water_tags, pcg_water_tags_v2, pcg_music_tags, pcg_music_tags_v2,
    material_crosswalk_integration, material_crosswalk_v2,
)
from .aaa_quality import aaq_quality_checklist, naming_convention_audit, aaq_roadmap
from .presets import (
    BUILDERS_PRESETS, builders_with_presets, preset_names, preset_param_sets,
    export_builder_preset, export_all_presets_json, audit_presets,
)
from . import nikki_decor  # noqa: F401 - Nikki decor: beads, stars, hearts, crystals, cords, guide-driven strings
from . import nikki_aaa_tokens  # noqa: F401 - Nikki AAA: fabric, ribbon, gem, petal, star token, heart token

# --- 2026-09-14 wave (wired 2026-09-16): audio-reactive study decor + Escher math ---
from . import audio_architecture  # noqa: F401 - MEL_audio_facade, MEL_audio_landscape
from . import audio_reactivity_v2  # noqa: F401 - Advanced audio-reactive builders (multiband, waveform, ripple, emission, beat)
from . import cute_decor  # noqa: F401 - 14 cute decor builders (crystal drops, dangls, chains...)
from . import escher_decor  # noqa: F401 - hyperbolic window, Penrose triangle, Mobius strip, escher tessellation
from . import skirt_decor  # noqa: F401 - garment hem decor: pearl-drop charms + guide-ring dangl row
from . import study_ground  # noqa: F401 - audio-reactive study ground
from . import note_school  # noqa: F401 - note fish school (Melody Aquarium): MEL_music_note_fish

# Rebuild derived lookup tables now that all builder modules
# have imported and called register_builder(). Mutates core containers
# in place so early importers (stack UI) see live catalog sections.
from . import barrel_vault_kit  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import curved_wall  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import dreamy_gothic_arch  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import garment_material_id  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import garment_smart_bevel  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import garment_trim_uv  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import garment_vertex_ao  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import gold_light_strip  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import melusina_house_foundation  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import music_euro_remainder  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import musical_mesh_variants  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import nikki_advanced_decorations  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import nikki_musical_decorations  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import ornament_strip  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import rose_window  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import ue_proxy_kit  # noqa: F401 - recovered 2026-09-11 (was live-only)
from . import eyewear  # noqa: F401 - Eyewear: CAD-level frame front from ISO 8624 boxing measurements
from . import music_percussion_kit  # noqa: F401 - P4 wave 3: snare/bass drum, cymbals, tambourine, carillon, kit rail
from . import music_string_kit  # noqa: F401 - P4 wave 4: cello/viola/double bass/banjo/mandolin/ukulele
from . import music_world_strings  # noqa: F401 - P4 wave 5: sitar/koto/balalaika/shamisen/erhu/guzheng
from . import music_wind_reed_brass  # noqa: F401 - P4 wave 6: oboe/bassoon/trumpet/tuba/accordion/bagpipes
from . import music_wind_folk  # noqa: F401 - P4 wave 7: dizi/xiao/bawu/hulusi/suona/sheng
from . import music_keyboard_kit  # noqa: F401 - P4 wave 8: grand/upright piano, harmonium, clavinet, mellotron, tonewheel organ
from . import music_electronics_kit  # noqa: F401 - P4 wave 9: synthesizer, drum machine, turntable, mixer, sequencer, sampler
from . import music_world_percussion  # noqa: F401 - P4 wave 10: djembe, congas, bongos, cajon, frame drum, tabla
from . import music_aux_percussion  # noqa: F401 - P4 wave 11: tom-tom, xylophone, washboard, claves, cabasa, guiro
from . import music_wind_solo  # noqa: F401 - P4 wave 12: shakuhachi, xun, panpipes, quena, didgeridoo, tin whistle
from . import music_aux_percussion2  # noqa: F401 - P4 wave 13: maracas, wood block, cowbell, castanets, shaker, vibraslap
from . import music_signal_percussion  # noqa: F401 - P4 wave 14: temple block, ratchet, bodhran, slapstick, slit drum, handpan
from . import music_wind_flute_family  # noqa: F401 - P4 wave 15: piccolo, alto/bass flute, bansuri, low whistle, fife
from . import music_notation_glyphs  # noqa: F401 - P5 wave 16: alto/tenor clef, sharp, flat, natural, quarter rest
from . import music_note_durations  # noqa: F401 - P5 wave 17: whole/half/quarter/eighth notes + whole/half rests
from . import music_notation_extras  # noqa: F401 - P5 wave 18: sixteenth note, rests, dynamics, hairpins, percussion clef
from . import music_notation_marks  # noqa: F401 - P5 wave 20: thirty-second note, bar lines, tenuto, caesura
from . import music_notation_signs  # noqa: F401 - P5 wave 21: double sharp/flat, coda, segno, breath mark, sforzando
from . import music_notation_signs2  # noqa: F401 - P5 wave 22: trill, mordent, turn, inverted turn, glissando, arpeggio, pedal marks, octave shift, key signature, tempo mark
from . import music_notation_express  # noqa: F401 - P5 wave 23: tie, slur, grace note, tremolo, up-bow, down-bow
# == UE proxy material kit UI ========================================
# integration.py registers melodia_gn.CLASSES. UE_PROXY_CLASSES was orphaned
# when ue_proxy_kit was recovered (2026-09-11); the panel/operator never
# registered. Fold it in here; do not remove. Gate: Tools/verify_proxy_materials.py
from .ue_proxy_kit import UE_PROXY_CLASSES as _UE_PROXY_CLASSES

CLASSES = list(CLASSES) + list(_UE_PROXY_CLASSES)

from .core import _rebuild_derived_data
_rebuild_derived_data()

# Back-compat aliases for anything that imported stack.TREE_* historically
from . import stack as _stack_mod
from . import core as _core_mod
_stack_mod.ALL_TREE_NAMES.clear()
_stack_mod.ALL_TREE_NAMES.extend(name for name, _ in _core_mod.TREE_TYPES)
# Prefer core.TREE_* - these names track the rebuilt containers
_STACK_CATS = _core_mod.TREE_CATEGORIES
_STACK_DESC = _core_mod.TREE_DESCRIPTIONS
_STACK_CATMAP = _core_mod.TREE_CATEGORY_MAP
_STACK_LABMAP = _core_mod.TREE_LABEL_MAP
