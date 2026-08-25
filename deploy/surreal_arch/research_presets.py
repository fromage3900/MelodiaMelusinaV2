"""Architecturally researched quick-launch presets (v2.65)."""

from __future__ import annotations

import bpy

RESEARCH_PRESETS = {
    "romanesque_cloister_arcade": {
        "label": "Romanesque Cloister Arcade",
        "description": "Round arches on colonettes, barrel vault segment, snap at bay ends",
        "research_ref": "Cistercian cloister typology - paired colonettes + semicircular arch + quadripartite vault rhythm",
        "props": dict(
            arch_type="GB_ROMANESQUE_ARCADE",
            gb_width=3.2,
            gb_height=4.2,
            gb_wall_thick=0.35,
            gb_leg_thick=0.18,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.06,
            gb_corridor_ceiling="FULL",
            material_choice="STONE",
            unit_size=3.2,
        ),
    },
    "brutalist_pilotis_hall": {
        "label": "Brutalist Pilotis Hall",
        "description": "Column grid + slab, offset recess panels for trim sheets",
        "research_ref": "Le Corbusier pilotis + béton brut - structural grid with deep panel recesses",
        "props": dict(
            arch_type="GREYBOX_PILLAR_HALL",
            gb_cols_x=4,
            gb_cols_y=3,
            gb_spacing=4.0,
            gb_height=3.6,
            gb_wall_thick=0.45,
            gb_leg_thick=0.55,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.08,
            gb_wainscot_height=0.0,
            gb_baseboard_height=0.15,
            material_choice="STONE",
            unit_size=4.0,
        ),
    },
    "venetian_loggia_bay": {
        "label": "Venetian Loggia Bay",
        "description": "Bifora rhythm + cornice shelf - Palazzo piano nobile reference",
        "research_ref": "Venetian Gothic bifora + loggia cornice (Boscarino et al. façade analysis)",
        "props": dict(
            arch_type="GB_VENETIAN_LOGGIA",
            gb_width=3.0,
            gb_height=4.8,
            gb_wall_thick=0.35,
            gb_window_sill=1.0,
            gb_window_height=2.6,
            bifora_lights=2,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.05,
            material_choice="MARBLE",
            unit_size=3.0,
        ),
    },
    "romanesque_apse_choir": {
        "label": "Romanesque Choir + Apse",
        "description": "Semicircular apse recess with barrel vault - choir terminus",
        "research_ref": "Cistercian choir apse typology - semicircular shell + barrel vault cap",
        "props": dict(
            arch_type="GB_ROMANESQUE_APSE",
            gb_width=4.0,
            gb_depth=3.5,
            gb_height=4.5,
            gb_wall_thick=0.35,
            gb_leg_thick=0.18,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.06,
            gb_corridor_ceiling="FULL",
            material_choice="STONE",
            unit_size=4.0,
        ),
    },
    "scifi_pressure_door_airlock": {
        "label": "Sci-Fi Pressure Door Airlock",
        "description": "Gasket recess, frame offset, MUST_CONNECT door snap",
        "research_ref": "Industrial airlock gasket recess + pressure-frame offset for modular sci-fi corridors",
        "props": dict(
            arch_type="GB_SCIFI_PRESSURE_DOOR",
            gb_length=3.5,
            gb_corridor_profile="DOUBLE",
            gb_height=3.2,
            gb_wall_thick=0.35,
            gb_door_width=1.2,
            gb_door_height=2.35,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.1,
            gb_frame=True,
            material_choice="AUTO",
            unit_size=3.5,
        ),
    },
    "scifi_airlock_graph": {
        "label": "Sci-Fi Airlock Graph",
        "description": "Full airlock chain - corridor, pressure doors, sealed room, offset leg",
        "research_ref": "Modular sci-fi airlock typology - scifi_airlock_v1 genome + SCIFI_AIRLOCK graph",
        "group": "SCIFI",
        "graph_id": "SCIFI_AIRLOCK",
        "genome_id": "scifi_airlock_v1",
        "props": dict(
            arch_type="GB_SCIFI_PRESSURE_DOOR",
            gb_length=3.5,
            gb_door_width=1.2,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.1,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="scifi_airlock_v1",
        ),
    },
    "gothic_cloister_graph": {
        "label": "Gothic Cloister Graph",
        "description": "Gothic cloister walk - double corridor, bend, portal termination",
        "research_ref": "Gothic cloister typology - gothic_cloister_v1 genome + CLOISTER graph",
        "group": "GOTHIC",
        "graph_id": "CLOISTER",
        "genome_id": "gothic_cloister_v1",
        "props": dict(
            arch_type="GREYBOX_CORRIDOR",
            gb_length=8.0,
            gb_corridor_profile="DOUBLE",
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="gothic_cloister_v1",
        ),
    },
    "gothic_chapter_house_graph": {
        "label": "Gothic Chapter House",
        "description": "Portal nave, window bay, buttress, transept bend, tracery screen",
        "research_ref": "Cathedral chapter house typology - gothic_chapter_house_v1 + GOTHIC_CHAPTER_HOUSE graph",
        "group": "GOTHIC",
        "graph_id": "GOTHIC_CHAPTER_HOUSE",
        "genome_id": "gothic_chapter_house_v1",
        "props": dict(
            arch_type="GB_GOTHIC_PORTAL",
            gb_door_width=1.6,
            gb_door_height=3.0,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="gothic_chapter_house_v1",
        ),
    },
    "gothic_nave_crossing_graph": {
        "label": "Gothic Nave Crossing",
        "description": "Long nave, T-crossing, transept arm, buttress piers, rose clerestory",
        "research_ref": "Cathedral crossing typology - gothic_nave_crossing_v1 + GOTHIC_NAVE_CROSSING graph",
        "group": "GOTHIC",
        "graph_id": "GOTHIC_NAVE_CROSSING",
        "genome_id": "gothic_nave_crossing_v1",
        "props": dict(
            arch_type="GB_GOTHIC_PORTAL",
            gb_door_width=1.8,
            gb_door_height=3.2,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="gothic_nave_crossing_v1",
        ),
    },
    "romanesque_cloister_graph": {
        "label": "Romanesque Cloister Graph",
        "description": "Full cloister arcade chain - bays alternating with offset corridor legs",
        "research_ref": "Cistercian cloister - romanesque_cloister_v1 genome + ROMANESQUE_CLOISTER graph",
        "group": "ROMANESQUE",
        "graph_id": "ROMANESQUE_CLOISTER",
        "genome_id": "romanesque_cloister_v1",
        "props": dict(
            arch_type="GB_ROMANESQUE_ARCADE",
            gb_width=3.2,
            gb_height=4.2,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=3.2,
            style_genome_id="romanesque_cloister_v1",
        ),
    },
    "scifi_deck_graph": {
        "label": "Sci-Fi Deck Spine",
        "description": "Corridor trunk, T-junction, hab module",
        "research_ref": "Sci-fi deck spine - scifi_deck_spine_v1 genome + SCI_FI_DECK graph",
        "group": "SCIFI",
        "graph_id": "SCI_FI_DECK",
        "genome_id": "scifi_deck_spine_v1",
        "props": dict(
            arch_type="GREYBOX_CORRIDOR",
            gb_length=12.0,
            gb_corridor_profile="DOUBLE",
            material_choice="AUTO",
            style_genome_id="scifi_deck_spine_v1",
        ),
    },
    "scifi_industrial_yard_graph": {
        "label": "Sci-Fi Industrial Yard",
        "description": "Pillar atrium, catwalk spine, bulkhead, service corridor",
        "research_ref": "Industrial sci-fi yard - scifi_industrial_yard_v1 genome + SCI_FI_INDUSTRIAL_YARD graph",
        "group": "SCIFI",
        "graph_id": "SCI_FI_INDUSTRIAL_YARD",
        "genome_id": "scifi_industrial_yard_v1",
        "props": dict(
            arch_type="GREYBOX_PILLAR_HALL",
            gb_cols_x=4,
            gb_cols_y=3,
            gb_spacing=4.0,
            gb_height=4.2,
            gb_trim_mode="RECESS",
            material_choice="AUTO",
            unit_size=4.0,
            style_genome_id="scifi_industrial_yard_v1",
        ),
    },
    "asian_city_graph": {
        "label": "Asian City Street",
        "description": "Pailou gate, market lane, pavilion and hanok bays",
        "research_ref": "East Asian urban typology - asian_city_v1 genome + ASIAN_CITY graph",
        "group": "ASIAN",
        "graph_id": "ASIAN_CITY",
        "genome_id": "asian_city_v1",
        "props": dict(
            arch_type="CN_PAILOU",
            gb_width=4.0,
            gb_height=7.5,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="asian_city_v1",
        ),
    },
    "asian_city_recursive_graph": {
        "label": "Asian City (Recursive Alley)",
        "description": "Surreal nested market lanes - recursive_interior on ASIAN_CITY graph",
        "research_ref": "Escher alley typology - asian_city_recursive_v1 + ASIAN_CITY graph",
        "group": "ASIAN",
        "graph_id": "ASIAN_CITY_RECURSIVE",
        "genome_id": "asian_city_recursive_v1",
        "props": dict(
            arch_type="GB_CORRIDOR_OFFSET",
            gb_length=8.0,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="asian_city_recursive_v1",
        ),
    },
    "brutalist_plaza_graph": {
        "label": "Brutalist Pilotis Plaza",
        "description": "Column grid, panel wall rhythm, offset slab corridor",
        "research_ref": "Le Corbusier pilotis plaza - brutalist_plaza_v1 genome + BRUTALIST_PLAZA graph",
        "group": "BRUTALIST",
        "graph_id": "BRUTALIST_PLAZA",
        "genome_id": "brutalist_plaza_v1",
        "props": dict(
            arch_type="GREYBOX_PILLAR_HALL",
            gb_cols_x=4,
            gb_cols_y=2,
            gb_spacing=4.0,
            gb_height=3.6,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=4.0,
            style_genome_id="brutalist_plaza_v1",
        ),
    },
    "art_nouveau_graph": {
        "label": "Art Nouveau Facade Walk",
        "description": "Ogee portal, filigree panels, balcony, baroque facade bay",
        "research_ref": "Art Nouveau ironwork - art_nouveau_v1 genome + ART_NOUVEAU graph",
        "group": "CIVIC",
        "graph_id": "ART_NOUVEAU",
        "genome_id": "art_nouveau_v1",
        "props": dict(
            arch_type="OGEE_ARCH",
            ogee_width=2.4,
            ogee_height=4.2,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="art_nouveau_v1",
        ),
    },
    "art_deco_lobby_graph": {
        "label": "Art Deco Lobby Walk",
        "description": "Tessellation tower, geometric panel wall, chevron filigree, cusped portal, obelisk",
        "research_ref": "1920s setback skyscraper lobby - art_deco_lobby_v1 + ART_DECO graph",
        "group": "CIVIC",
        "graph_id": "ART_DECO",
        "genome_id": "art_deco_lobby_v1",
        "props": dict(
            arch_type="TESSELLATION_TOWER",
            tess_grid_x=6,
            tess_grid_y=6,
            tess_size=0.45,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="art_deco_lobby_v1",
        ),
    },
    "moorish_courtyard_graph": {
        "label": "Moorish Courtyard Colonnade",
        "description": "Horseshoe portal, arabesque screen, arcade bays, fountain court",
        "research_ref": "Islamic riyad typology - moorish_courtyard_v1 + MOORISH_COURTYARD graph",
        "group": "CIVIC",
        "graph_id": "MOORISH_COURTYARD",
        "genome_id": "moorish_courtyard_v1",
        "props": dict(
            arch_type="ARCHWAY_ADV",
            archway_style="HORSESHOE",
            archway_width=2.6,
            archway_height=2.2,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="moorish_courtyard_v1",
        ),
    },
    "renaissance_piazza_graph": {
        "label": "Renaissance Piazza",
        "description": "Baroque facade, arcade colonnade, balustrade, fountain, dome",
        "research_ref": "Italian piazza typology - renaissance_piazza_v1 + RENAISSANCE_PIAZZA graph",
        "group": "CIVIC",
        "graph_id": "RENAISSANCE_PIAZZA",
        "genome_id": "renaissance_piazza_v1",
        "props": dict(
            arch_type="BAROQUE_FACADE",
            baroque_facade_bays=5,
            baroque_facade_height=14.0,
            baroque_order="CORINTHIAN",
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="renaissance_piazza_v1",
        ),
    },
    "byzantine_basilica_graph": {
        "label": "Byzantine Basilica",
        "description": "Horseshoe narthex, cusped arch, vault nave, rose window, crossing dome",
        "research_ref": "Hagia Sophia typology - byzantine_basilica_v1 + BYZANTINE_BASILICA graph",
        "group": "CIVIC",
        "graph_id": "BYZANTINE_BASILICA",
        "genome_id": "byzantine_basilica_v1",
        "props": dict(
            arch_type="CUSPED_ARCH",
            gothic_width=2.4,
            gb_height=4.2,
            gb_trim_mode="RECESS",
            material_choice="MARBLE",
            unit_size=3.4,
            style_genome_id="byzantine_basilica_v1",
        ),
    },
    "baroque_church_graph": {
        "label": "Baroque Church",
        "description": "Ornate facade, ogee portal, ribbed vault, niche chapel, balustrade choir, dome",
        "research_ref": "Counter-Reformation church typology - baroque_church_v1 + BAROQUE_CHURCH graph",
        "group": "CIVIC",
        "graph_id": "BAROQUE_CHURCH",
        "genome_id": "baroque_church_v1",
        "props": dict(
            arch_type="BAROQUE_FACADE",
            baroque_facade_bays=5,
            baroque_facade_height=16.0,
            baroque_order="CORINTHIAN",
            baroque_ornament_density=0.78,
            material_choice="MARBLE",
            unit_size=2.0,
            style_genome_id="baroque_church_v1",
        ),
    },
    "romanesque_apse_graph": {
        "label": "Romanesque Choir + Apse",
        "description": "Arcade walk terminating in semicircular apse",
        "research_ref": "Cistercian choir typology - romanesque_apse_v1 + ROMANESQUE_APSE graph",
        "group": "ROMANESQUE",
        "graph_id": "ROMANESQUE_APSE",
        "genome_id": "romanesque_apse_v1",
        "props": dict(
            arch_type="GB_ROMANESQUE_ARCADE",
            gb_width=3.2,
            gb_height=4.2,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=3.2,
            style_genome_id="romanesque_apse_v1",
        ),
    },
    "venetian_canal_graph": {
        "label": "Venetian Canal Block",
        "description": "Loggia rhythm along offset corridor - waterfront facade",
        "research_ref": "Venetian sottoportego typology - venetian_canal_v1 + VENETIAN_CANAL graph",
        "group": "VENETIAN",
        "graph_id": "VENETIAN_CANAL",
        "genome_id": "venetian_canal_v1",
        "props": dict(
            arch_type="GB_VENETIAN_LOGGIA",
            gothic_width=2.8,
            gb_height=4.0,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="venetian_canal_v1",
        ),
    },
    "zen_roji_path_graph": {
        "label": "Zen Roji Approach",
        "description": "Torii gate, dew-path steps, tsukubai basin, stone lantern",
        "research_ref": "Roji tea-garden entry - zen_roji_path_v1 genome + ZEN_ROJI_PATH graph",
        "group": "ZEN",
        "graph_id": "ZEN_ROJI_PATH",
        "genome_id": "zen_roji_path",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.6,
            torii_height=4.2,
            gb_trim_mode="RECESS",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_roji_path",
        ),
    },
    "zen_roji_step": {
        "label": "Zen Roji Dew Path",
        "description": "Flat slab + raised edge stones - roji approach segment with path snaps",
        "research_ref": "Roji dew-path typology - stepping stones flanking central slab (tea garden entry)",
        "props": dict(
            arch_type="GB_ZEN_ROJI_STEP",
            gb_length=4.5,
            gb_width=1.8,
            gb_wall_thick=0.12,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_torii_gate_modular": {
        "label": "Zen Torii Gate (Greybox)",
        "description": "Hashira posts, nuki tie beam, kasagi lintel - MUST_CONNECT path snaps",
        "research_ref": "Shinto torii typology - hashira / nuki / kasagi modular kit for shrine entry",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.6,
            torii_height=4.2,
            torii_post_radius=0.18,
            gb_wall_thick=0.2,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.05,
            material_choice="STONE",
            unit_size=3.6,
        ),
    },
    "zen_tsukubai_basin": {
        "label": "Zen Tsukubai Basin",
        "description": "Stone pad with recess bowl + surround flagstones - ritual hand-wash station",
        "research_ref": "Tsukubai chōzubachi typology - basin recess + flagstone surround for roji tea path",
        "props": dict(
            arch_type="GB_ZEN_TSUKUBAI",
            gb_width=1.6,
            gb_depth=1.6,
            gb_height=0.45,
            gb_wall_thick=0.14,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.06,
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_engawa_veranda": {
        "label": "Zen Engawa Veranda",
        "description": "Raised deck slab with post row and railing - connects roji to teahouse",
        "research_ref": "Engawa typology - transitional veranda between garden and interior (sukiya-zukuri)",
        "props": dict(
            arch_type="GB_ZEN_ENGAWA",
            gb_width=5.0,
            gb_depth=2.4,
            gb_height=0.35,
            gb_wall_thick=0.12,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            material_choice="AUTO",
            unit_size=2.5,
        ),
    },
    "zen_bamboo_fence": {
        "label": "Zen Bamboo Fence",
        "description": "Tileable bamboo screen - posts and horizontal rails for garden boundary",
        "research_ref": "Take-gaki typology - low bamboo fence rhythm screening tea garden from outer path",
        "props": dict(
            arch_type="GB_ZEN_BAMBOO_FENCE",
            gb_length=4.0,
            zen_fence_height=1.2,
            gb_wall_thick=0.06,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.03,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_tobiishi_path": {
        "label": "Zen Tobi-ishi Path",
        "description": "Scattered flat stepping stones along path strip - informal roji approach",
        "research_ref": "Tobi-ishi typology - irregular stone placement guiding gait through roji dew path",
        "props": dict(
            arch_type="GB_ZEN_TOBIISHI",
            gb_length=5.0,
            gb_width=1.6,
            gb_wall_thick=0.1,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_karesansui_garden": {
        "label": "Zen Karesansui Garden",
        "description": "Dry rock garden slab - raked gravel, border stones, parallel groove trim zones",
        "research_ref": "Karesansui typology - ishigumi border + rake groove recess panels for TRIM_SHEET",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_KARESANSUI",
            gb_width=8.0,
            gb_depth=6.0,
            gb_wall_thick=0.12,
            gb_trim_mode="RECESS",
            gb_trim_recess=0.03,
            gb_bake_trim_colors=True,
            uv_unwrap_mode="TRIM_SHEET",
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_machiai_pavilion": {
        "label": "Zen Machiai Pavilion",
        "description": "Open waiting pavilion - posts, roof beam, bench facing dry garden",
        "research_ref": "Machiai typology - contemplation pause before teahouse entry",
        "group": "ZEN",
        "graph_id": "ZEN_KARESANSHUI_WALK",
        "props": dict(
            arch_type="GB_ZEN_MACHIAI",
            gb_width=3.2,
            gb_depth=2.4,
            gb_height=2.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            uv_unwrap_mode="BOX",
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_stone_bridge": {
        "label": "Zen Stone Bridge",
        "description": "Greybox garden bridge - deck, rails, abutments for stream crossings",
        "research_ref": "Taikobashi typology - low stone arch deck with TRIM_SHEET recess panels",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_STONE_BRIDGE",
            zen_bridge_span=5.0,
            zen_bridge_rise=0.55,
            gb_width=1.8,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            uv_unwrap_mode="TRIM_SHEET",
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_cherry_allee": {
        "label": "Zen Cherry Allee",
        "description": "Sakura path segment - trunk bases, blossom canopy, petal scatter trim",
        "research_ref": "Sakura tunnel typology - paired blossom_canopy recess zones along central walk",
        "group": "ZEN",
        "graph_id": "ZEN_SAKURA_WALK",
        "props": dict(
            arch_type="GB_ZEN_CHERRY_ALLEE",
            gb_length=6.0,
            gb_width=2.6,
            gb_height=0.32,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            uv_unwrap_mode="TRIM_SHEET",
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_shrine_axis": {
        "label": "Zen Shrine Axis",
        "description": "Torii -> sando -> kairo -> karesansui - zen_shrine_v1 genome pilot",
        "research_ref": "research/zen/02_shrine_axis.md - sacred approach spine",
        "group": "ZEN",
        "graph_id": "ZEN_SHRINE_AXIS",
        "genome_id": "zen_shrine_axis",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.6,
            torii_height=4.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            uv_unwrap_mode="TRIM_SHEET",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_shrine_axis",
        ),
    },
    "zen_shrine_courtyard": {
        "label": "Zen Shrine Courtyard",
        "description": "Courtyard compose pilot - goju corner tower, tahōtō monument, GB torii gate",
        "research_ref": "research/zen/02_shrine_axis.md - courtyard compose roles",
        "group": "ZEN",
        "graph_id": "ZEN_SHRINE_COURTYARD",
        "genome_id": "zen_shrine_courtyard",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=4.0,
            torii_height=4.5,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_shrine_courtyard",
        ),
    },
    "zen_tea_garden": {
        "label": "Zen Tea Garden",
        "description": "Roji tea garden - tobi-ishi, bamboo screen, tsukubai, engawa, teahouse",
        "research_ref": "research/zen/02_shrine_axis.md - tea garden graph typology",
        "group": "ZEN",
        "graph_id": "ZEN_TEA_GARDEN",
        "genome_id": "zen_tea_garden",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.2,
            torii_height=3.8,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="zen_tea_garden",
        ),
    },
    "zen_sando_approach": {
        "label": "Zen Sando Approach",
        "description": "Shrine approach paving with tōrō rhythm and edge stones",
        "research_ref": "research/zen/02_shrine_axis.md - sando paving module",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_SANDO",
            gb_length=8.0,
            gb_width=2.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="STONE",
            unit_size=2.0,
        ),
    },
    "zen_kairo_cloister": {
        "label": "Zen Kairo Cloister",
        "description": "Covered cloister walk - columns, beam, eave, garden wall",
        "research_ref": "research/zen/02_shrine_axis.md - kairo courtyard edge",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_KAIRO",
            gb_length=6.0,
            gb_width=2.4,
            gb_height=2.8,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_haiden_worship": {
        "label": "Zen Haiden Worship Hall",
        "description": "Worship hall - genkan steps, raised haijo floor, ranma transom, noki eave",
        "research_ref": "research/zen/02_shrine_axis.md - haiden platform atom",
        "group": "ZEN",
        "graph_id": "ZEN_SHRINE_AXIS",
        "props": dict(
            arch_type="GB_ZEN_HAIDEN",
            gb_width=5.0,
            gb_depth=4.0,
            gb_height=3.2,
            zen_genkan_rise=0.45,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_goju_pagoda": {
        "label": "Zen Goju-no-tō Pagoda",
        "description": "Five-story pagoda greybox - tapered tier cores, flared eaves, sorin finial",
        "research_ref": "research/zen/02_shrine_axis.md - corner_tower compose role",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_GOJU_PAGODA",
            pagoda_tiers=5,
            pagoda_base_radius=2.0,
            pagoda_tier_height=1.2,
            pagoda_taper=0.82,
            pagoda_roof_overhang=0.4,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_sakura_torii": {
        "label": "Zen Sakura Torii",
        "description": "Torii variant - blossom band on kasagi + petal accent strips on hashira",
        "research_ref": "Sakura path typology - torii_frame sakura variant",
        "group": "ZEN",
        "graph_id": "ZEN_SAKURA_WALK",
        "genome_id": "zen_shrine_sakura",
        "props": dict(
            arch_type="GB_ZEN_SAKURA_TORII",
            torii_width=3.4,
            torii_height=4.0,
            torii_post_radius=0.16,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="zen_shrine_sakura",
        ),
    },
    "zen_tahoto_tower": {
        "label": "Zen Tahoto Treasure Tower",
        "description": "Tahōtō typology - square mokoshi, drum body, double roof, sorin",
        "research_ref": "Tier C sacred tower - treasure pagoda grammar",
        "group": "ZEN",
        "props": dict(
            arch_type="GB_ZEN_TAHOTO",
            gb_width=3.2,
            gb_height=6.5,
            zen_tahoto_roof_span=0.35,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_honden_sanctuary": {
        "label": "Zen Honden Sanctuary",
        "description": "Main shrine core - raised moya, engawa margin, threshold, deep noki",
        "research_ref": "Tier C sacred core - honden sanctuary atom",
        "group": "ZEN",
        "graph_id": "ZEN_SHRINE_AXIS",
        "props": dict(
            arch_type="GB_ZEN_HONDEN",
            gb_width=5.5,
            gb_depth=4.5,
            gb_height=3.6,
            zen_honden_platform_rise=0.55,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
        ),
    },
    "zen_karesansui_graph": {
        "label": "Zen Karesansui Walk",
        "description": "Torii, roji step, dry garden, machiai, lantern - contemplation spine",
        "research_ref": "research/zen/03_karesansui_grammar.md - zen_karesansui_v1 genome",
        "group": "ZEN",
        "graph_id": "ZEN_KARESANSHUI_WALK",
        "genome_id": "zen_karesansui_v1",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.4,
            torii_height=4.0,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            uv_unwrap_mode="TRIM_SHEET",
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_karesansui_v1",
        ),
    },
    "zen_stream_garden_graph": {
        "label": "Zen Stream Garden",
        "description": "Sando, stream edge, stone bridge, cherry allée, karesansui, engawa",
        "research_ref": "Strolling water garden - zen_stream_garden_v1 genome + ZEN_STREAM_GARDEN graph",
        "group": "ZEN",
        "graph_id": "ZEN_STREAM_GARDEN",
        "genome_id": "zen_stream_garden_v1",
        "props": dict(
            arch_type="GB_ZEN_SANDO",
            gb_length=8.0,
            gb_width=2.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="AUTO",
            unit_size=2.0,
            style_genome_id="zen_stream_garden_v1",
        ),
    },
    "zen_pagoda_spire_graph": {
        "label": "Zen Pagoda Spire",
        "description": "Torii, sando ascent, goju pagoda, tahoto, honden sanctuary",
        "research_ref": "Vertical monument spine - zen_pagoda_spire_v1 genome + ZEN_PAGODA_SPIRE graph",
        "group": "ZEN",
        "graph_id": "ZEN_PAGODA_SPIRE",
        "genome_id": "zen_pagoda_spire_v1",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.6,
            torii_height=4.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_pagoda_spire_v1",
        ),
    },
    "zen_kairo_enclosure_graph": {
        "label": "Zen Kairo Enclosure",
        "description": "Torii, cloister L-turn, karesansui court, haiden, honden, machiai",
        "research_ref": "Enclosed temple compound - zen_kairo_enclosure_v1 genome + ZEN_KAIRO_ENCLOSURE graph",
        "group": "ZEN",
        "graph_id": "ZEN_KAIRO_ENCLOSURE",
        "genome_id": "zen_kairo_enclosure_v1",
        "props": dict(
            arch_type="GB_ZEN_TORII_GATE",
            torii_width=3.6,
            torii_height=4.2,
            gb_trim_mode="RECESS",
            gb_bake_trim_colors=True,
            material_choice="STONE",
            unit_size=2.0,
            style_genome_id="zen_kairo_enclosure_v1",
        ),
    },
}


def apply_research_preset(props, preset_id, monolith=None):
    spec = RESEARCH_PRESETS.get(preset_id)
    if not spec:
        raise KeyError(preset_id)
    for key, val in spec["props"].items():
        if hasattr(props, key):
            setattr(props, key, val)
    gid = spec.get("genome_id")
    if gid and monolith is not None:
        try:
            import sys
            import os
            deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if deploy not in sys.path:
                sys.path.insert(0, deploy)
            from surreal_os import genome as os_genome
            os_genome.apply_genome(props, gid, monolith=monolith)
        except Exception:
            pass
    return spec


def run_research_preset(context, preset_id, monolith=None):
    """Apply preset - spawns full graph chain when graph_id is set, else single module."""
    spec = RESEARCH_PRESETS.get(preset_id)
    if not spec:
        raise KeyError(preset_id)

    graph_id = spec.get("graph_id")
    if graph_id:
        from .greybox_graph import GRAPH_REGISTRY, spawn_graph, resolve_graph_spacing

        obj = context.active_object
        if obj and hasattr(obj, "surreal_arch_props"):
            apply_research_preset(obj.surreal_arch_props, preset_id, monolith=monolith)
        elif spec.get("genome_id") and monolith is not None:
            try:
                import sys
                import os
                deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if deploy not in sys.path:
                    sys.path.insert(0, deploy)
                from surreal_os import genome as os_genome
                monolith._active_style_genome = os_genome.load_genome(spec["genome_id"])
            except Exception:
                pass

        meta = GRAPH_REGISTRY.get(graph_id)
        if not meta:
            raise KeyError(f"graph {graph_id} not in GRAPH_REGISTRY")
        spacing = resolve_graph_spacing(context)
        objs = spawn_graph(
            context, monolith, meta["spec"],
            spacing=spacing, graph_id=graph_id,
        )
        return {"mode": "graph", "graph_id": graph_id, "count": len(objs)}

    obj = context.active_object
    if not obj or not hasattr(obj, "surreal_arch_props"):
        raise RuntimeError("Select a mesh with Surreal Architecture")
    apply_research_preset(obj.surreal_arch_props, preset_id, monolith=monolith)
    bpy.ops.surreal_arch.generate()
    return {"mode": "single", "arch_type": spec["props"].get("arch_type", "")}


def audit_graph_presets(graph_registry: dict) -> list[str]:
    """Return errors for research presets whose graph_id is missing from registry."""
    errors = []
    for preset_id, spec in RESEARCH_PRESETS.items():
        graph_id = spec.get("graph_id")
        if not graph_id:
            continue
        if graph_id not in graph_registry:
            errors.append(f"{preset_id}: graph {graph_id} missing")
    return errors


_VALID_MATERIAL = frozenset({
    "AUTO", "STONE", "MARBLE", "WATER", "STAINED", "IRIDESCENT",
    "GOLD", "CLEF_GLOW", "GOTHIC_DARK", "GENSHIN",
})
_VALID_TRIM = frozenset({"RECESS", "OFFSET", "NONE"})


def audit_grammar_enums(graph_registry: dict) -> list[str]:
    """Return errors for invalid material_choice / gb_trim_mode in OS grammar specs."""
    errors = []
    for graph_id, meta in graph_registry.items():
        if not meta.get("os_grammar"):
            continue
        for arch_type, overrides in meta.get("spec", []):
            mc = overrides.get("material_choice")
            if mc and mc not in _VALID_MATERIAL:
                errors.append(f"{graph_id}/{arch_type}: material_choice={mc}")
            tm = overrides.get("gb_trim_mode")
            if tm and tm not in _VALID_TRIM:
                errors.append(f"{graph_id}/{arch_type}: gb_trim_mode={tm}")
    return errors


def register_research_preset_operators(monolith):
    classes = []
    for preset_id, spec in RESEARCH_PRESETS.items():
        op_id = f"surreal_arch.preset_research_{preset_id}"

        def _make_execute(pid=preset_id):
            def execute(self, context):
                try:
                    result = run_research_preset(context, pid, monolith=monolith)
                except Exception as err:
                    self.report({"WARNING"}, str(err))
                    return {"CANCELLED"}
                if result["mode"] == "graph":
                    self.report(
                        {"INFO"},
                        f"Spawned {result['count']} modules ({result['graph_id']})",
                    )
                else:
                    self.report({"INFO"}, f"Generated {result.get('arch_type', 'module')}")
                return {"FINISHED"}

            return execute

        cls_name = f"SURREAL_ARCH_OT_preset_research_{preset_id}"
        has_graph = bool(spec.get("graph_id"))
        cls = type(
            cls_name,
            (bpy.types.Operator,),
            {
                "bl_idname": op_id,
                "bl_label": spec["label"],
                "bl_description": spec.get("description", ""),
                "bl_options": {"REGISTER", "UNDO"},
                "execute": _make_execute(preset_id),
                "poll": classmethod(
                    lambda c, ctx: (
                        has_graph or (ctx.active_object and ctx.active_object.type == "MESH")
                    )
                ),
            },
        )
        classes.append(cls)
    return classes
