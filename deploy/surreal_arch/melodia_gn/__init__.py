from .core import safe_node, link_sockets, color_node, label_tree, new_geometry_tree, make_group_input, make_group_output, TREE_TYPES, GROUP_BUILDERS, GROUP_METADATA, CATEGORY_META, STUDIO_LABELS, TREE_LABEL_MAP, TREE_DESCRIPTIONS, TREE_CATEGORY_MAP, TREE_CATEGORIES, register_builder
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
from . import music_heroes  # noqa: F401 - hero music kit (key/piano-roll/sheet-rail/room-shell/harp register here, not via terrain chain)
from . import music_harps_real  # noqa: F401 - Realistic harps: concert/Ur lyre/kora/siku
from . import music_terrain  # noqa: F401 - Walkable roll field/staff bridge terrain
from . import audio_terrain  # noqa: F401 - Blender 5.2 native audio terrain/mesh systems
from . import planetary_terrain  # noqa: F401 - v3 deterministic planetary musical terrain
from . import infinity_nikki_kit  # noqa: F401 - Infinity Nikki expanded wardrobe kit (bloom pavilion/nook/runway)
from . import mother  # noqa: F401 - Faraway Mother Monolith kit (8 builders)
from . import white_current  # noqa: F401 - White Current Monolith kit (6 builders)
from . import god_molts  # noqa: F401 - God That Molts Monolith kit (8 builders)
from .notation_extras import build_music_bass_clef, build_music_beam_cluster, build_music_triplet_note, build_music_chord_stack, build_music_fermata, build_music_repeat_bar, build_music_time_signature, build_music_stand
from .ornament_extras import build_ornament_rosette_sixpetal, build_ornament_scallop_band, build_ornament_keyhole_frame, build_filigree_corner_volute, build_filigree_finial_cross, build_filigree_wreath_ring
from .ribbon import (
    build_ribbon_curve, build_lissajous_ribbon, build_closed_ribbon, build_violin_bow,
    build_allee_ribbon,
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
from . import house_dress  # noqa: F401 - Mansion house-dress kit (piano walk/sheet rail/staff/xylo/stones/lanterns/tree line) registers via register_builder
from .env_extras import build_env_lily_pond, build_env_stepping_stones, build_env_reeds_patch, build_env_buoy_line, build_env_market_stall, build_env_campfire_ring, build_env_village_well, build_env_lantern_post, build_env_hedgerow, build_env_waterfall_pool
from .castle_extras import build_castle_corner_turret, build_castle_portcullis, build_castle_arrow_slit, build_castle_hoarding, build_castle_siege_tower, build_castle_barbican, build_pergola_walkway
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

# Rebuild derived lookup tables now that all builder modules
# have imported and called register_builder(). Mutates core containers
# in place so early importers (stack UI) see live catalog sections.
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
