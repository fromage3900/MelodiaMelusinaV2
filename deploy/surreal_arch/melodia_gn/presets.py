"""Builder preset library for the Melodia GN node-group builders.

Pure-Python data + export layer: this module imports nothing from the Blender
stack, so it imports and runs on any Python (>=3.10) with or without bpy.
Registry-aware functions (audit_presets) import GROUP_METADATA lazily and
degrade gracefully when bpy/core are unavailable.

Data shape (QUALITY_GATES["preset_system"]: 2-3 curated presets per builder
+ JSON export):

    BUILDERS_PRESETS[builder_id] = {
        "label": builder display label,
        "presets": {preset_name: {param_ui_label: value, ...}},
        "preset_labels": {preset_name: human label},           # optional
        "preset_descriptions": {preset_name: one-liner},       # optional
    }

Param keys are the exact group-input socket names each builder creates via
core.make_group_input / add_*_param (e.g. "Wave Count", "Base Frequency").

Public API:
    builders_with_presets()      -> list[str]
    preset_names(builder_id)     -> list[str]
    preset_param_sets(builder_id)-> list[dict]  (name/label/description/params)
    export_builder_preset(builder_id, preset_name) -> dict (metadata + params)
    export_all_presets_json(path)-> str (path written)
    audit_presets()              -> dict report (reads GROUP_METADATA lazily)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

PRESET_SCHEMA_VERSION = 1
PRESET_SOURCE = "melodia_gn.presets"

# -----------------------------------------------------------------------------
# Preset data - one entry per builder, keys match actual builder input sockets.
# -----------------------------------------------------------------------------

BUILDERS_PRESETS: dict[str, dict[str, Any]] = {
    "MEL_mh_foundation_pod": {
        "label": "MH Foundation Pod",
        "preset_labels": {
            "COMPACT_DOLLHOUSE": "Compact Dollhouse Pod",
            "SALON_CORE": "Salon Core Pod",
            "BLUE_ROOM_BASE": "Blue Room Base",
        },
        "preset_descriptions": {
            "COMPACT_DOLLHOUSE": "Small intimate rounded room mass.",
            "SALON_CORE": "Default central oval salon footprint.",
            "BLUE_ROOM_BASE": "Lower, broader base for the water-grotto lane.",
        },
        "presets": {
            "COMPACT_DOLLHOUSE": {"Width": 3.8, "Depth": 3.2, "Foundation Height": 0.32, "Bevel": 0.05},
            "SALON_CORE": {"Width": 5.4, "Depth": 4.8, "Foundation Height": 0.36, "Bevel": 0.06},
            "BLUE_ROOM_BASE": {"Width": 5.0, "Depth": 4.2, "Foundation Height": 0.28, "Bevel": 0.08},
        },
    },
    "MEL_mh_foundation_cluster": {
        "label": "MH Foundation Cluster",
        "preset_labels": {
            "ROUND_BAROQUE_DEFAULT": "Round Baroque Default",
            "COMPACT_DOLLHOUSE": "Compact Dollhouse",
            "WIDE_SALON": "Wide Salon",
        },
        "preset_descriptions": {
            "ROUND_BAROQUE_DEFAULT": "Current concept-board lower-house massing.",
            "COMPACT_DOLLHOUSE": "Tighter intimate plan for fast silhouette tests.",
            "WIDE_SALON": "Broader social heart with wider central oval.",
        },
        "presets": {
            "ROUND_BAROQUE_DEFAULT": {"Center Width": 5.4, "Center Depth": 4.8, "Side Width": 3.7, "Side Depth": 3.4, "Side Spread": 4.1, "Rear Width": 4.2, "Rear Depth": 3.2, "Rear Offset": 3.8, "Foundation Height": 0.36, "Bevel": 0.06},
            "COMPACT_DOLLHOUSE": {"Center Width": 4.6, "Center Depth": 4.0, "Side Width": 3.0, "Side Depth": 2.8, "Side Spread": 3.4, "Rear Width": 3.6, "Rear Depth": 2.8, "Rear Offset": 3.1, "Foundation Height": 0.32, "Bevel": 0.05},
            "WIDE_SALON": {"Center Width": 6.6, "Center Depth": 5.2, "Side Width": 3.9, "Side Depth": 3.5, "Side Spread": 4.8, "Rear Width": 4.6, "Rear Depth": 3.4, "Rear Offset": 4.0, "Foundation Height": 0.38, "Bevel": 0.07},
        },
    },
    "MEL_mh_foundation_porch": {
        "label": "MH Foundation Porch",
        "preset_labels": {
            "CRESCENT_ENTRY": "Crescent Entry",
            "SEA_TERRACE": "Sea Terrace",
            "SMALL_LANDING": "Small Landing",
        },
        "preset_descriptions": {
            "CRESCENT_ENTRY": "Default soft oval arrival platform.",
            "SEA_TERRACE": "Wider, deeper porch for the water-facing side.",
            "SMALL_LANDING": "Compact entry proof for fast blockouts.",
        },
        "presets": {
            "CRESCENT_ENTRY": {"Porch Width": 5.2, "Porch Depth": 2.3, "Front Offset": 4.4, "Foundation Height": 0.28, "Bevel": 0.07},
            "SEA_TERRACE": {"Porch Width": 6.4, "Porch Depth": 3.0, "Front Offset": 4.8, "Foundation Height": 0.30, "Bevel": 0.08},
            "SMALL_LANDING": {"Porch Width": 3.8, "Porch Depth": 1.7, "Front Offset": 4.0, "Foundation Height": 0.24, "Bevel": 0.05},
        },
    },
    "MEL_mh_foundation_master": {
        "label": "MH Foundation Master",
        "preset_labels": {
            "ROUND_BAROQUE_DEFAULT": "Round Baroque Default",
            "COMPACT_DOLLHOUSE": "Compact Dollhouse",
            "WIDE_SALON": "Wide Salon + Tower",
        },
        "preset_descriptions": {
            "ROUND_BAROQUE_DEFAULT": "Recommended first Melusina House blockout.",
            "COMPACT_DOLLHOUSE": "Smaller, precious house footprint for intimacy checks.",
            "WIDE_SALON": "Expanded central salon and stronger tower counterweight.",
        },
        "presets": {
            "ROUND_BAROQUE_DEFAULT": {"Center Width": 5.4, "Center Depth": 4.8, "Side Width": 3.7, "Side Depth": 3.4, "Side Spread": 4.1, "Rear Width": 4.2, "Rear Depth": 3.2, "Rear Offset": 3.8, "Porch Width": 5.2, "Porch Depth": 2.3, "Porch Offset": 4.4, "Tower Radius": 1.15, "Tower X": 5.1, "Tower Y": 1.6, "Foundation Height": 0.36, "Bevel": 0.06},
            "COMPACT_DOLLHOUSE": {"Center Width": 4.6, "Center Depth": 4.0, "Side Width": 3.0, "Side Depth": 2.8, "Side Spread": 3.4, "Rear Width": 3.6, "Rear Depth": 2.8, "Rear Offset": 3.1, "Porch Width": 4.2, "Porch Depth": 1.8, "Porch Offset": 3.8, "Tower Radius": 0.9, "Tower X": 4.2, "Tower Y": 1.4, "Foundation Height": 0.32, "Bevel": 0.05},
            "WIDE_SALON": {"Center Width": 6.6, "Center Depth": 5.2, "Side Width": 3.9, "Side Depth": 3.5, "Side Spread": 4.8, "Rear Width": 4.6, "Rear Depth": 3.4, "Rear Offset": 4.0, "Porch Width": 6.0, "Porch Depth": 2.6, "Porch Offset": 4.8, "Tower Radius": 1.3, "Tower X": 5.7, "Tower Y": 1.8, "Foundation Height": 0.38, "Bevel": 0.07},
        },
    },
    "MEL_audio_spectrum_terrain": {
        "label": "Audio Spectrum Terrain",
        "preset_labels": {
            "DREAMING_HIGHLANDS": "Dreaming Highlands",
            "BASS_CANYON": "Bass Canyon",
            "FULL_SONG_CONTINENT": "Full Song Continent",
            "SEA_ABOVE_FALSE_HORIZON": "Sea Above False Horizon",
        },
        "preset_descriptions": {
            "DREAMING_HIGHLANDS": "Balanced melodic landscape for broad walkable composition studies.",
            "BASS_CANYON": "Low-frequency canyon relief with restrained upper-band detail.",
            "FULL_SONG_CONTINENT": "Large high-resolution terrain intended for tiled bake/export runs.",
            "SEA_ABOVE_FALSE_HORIZON": "Kilometre-scale subdued frequency terrain for the false-ocean horizon and Bell silhouette.",
        },
        "presets": {
            "DREAMING_HIGHLANDS": {"Low Hz": 80.0, "High Hz": 9000.0, "Band Width": 0.08, "Audio Gain": 7.0, "Size X M": 120.0, "Size Y M": 72.0, "Resolution X": 256, "Resolution Y": 128, "Height M": 16.0},
            "BASS_CANYON": {"Low Hz": 25.0, "High Hz": 800.0, "Band Width": 0.16, "Audio Gain": 12.0, "Size X M": 160.0, "Size Y M": 64.0, "Resolution X": 256, "Resolution Y": 96, "Height M": 35.0},
            "FULL_SONG_CONTINENT": {"Low Hz": 30.0, "High Hz": 16000.0, "Band Width": 0.04, "Audio Gain": 9.0, "Size X M": 1000.0, "Size Y M": 600.0, "Resolution X": 768, "Resolution Y": 384, "Height M": 90.0},
            "SEA_ABOVE_FALSE_HORIZON": {"Low Hz": 18.0, "High Hz": 1800.0, "Band Width": 0.06, "Audio Gain": 5.0, "Size X M": 1600.0, "Size Y M": 900.0, "Resolution X": 768, "Resolution Y": 384, "Height M": 42.0, "Music Influence": 0.08, "Musical Amplitude": 6.0, "Musical Freq A": 1.0, "Musical Freq B": 2.0},
        },
    },
    "MEL_audio_spectrum_towers": {
        "label": "Audio Spectrum Towers",
        "preset_labels": {"CHOIR_CITY": "Choir City", "BASS_FORTRESS": "Bass Fortress", "MEGASPECTRUM_WALL": "Megaspectrum Wall", "SEA_ABOVE_BELL_RIBS": "Sea Above Bell Ribs"},
        "preset_descriptions": {
            "CHOIR_CITY": "Mid/high-frequency skyline for choral architectural studies.",
            "BASS_FORTRESS": "Heavy low-band towers with large readable silhouettes.",
            "MEGASPECTRUM_WALL": "Dense 512-bin wall for large-scale instancing and export tests.",
            "SEA_ABOVE_BELL_RIBS": "Low-frequency kilometre-scale rib field for the Bell proxy silhouette.",
        },
        "presets": {
            "CHOIR_CITY": {"Low Hz": 120.0, "High Hz": 12000.0, "Band Width": 0.06, "Audio Gain": 10.0, "Size X M": 180.0, "Frequency Bins": 192, "Tower Width M": 0.7, "Tower Depth M": 4.0, "Height M": 45.0},
            "BASS_FORTRESS": {"Low Hz": 20.0, "High Hz": 500.0, "Band Width": 0.18, "Audio Gain": 16.0, "Size X M": 240.0, "Frequency Bins": 96, "Tower Width M": 2.0, "Tower Depth M": 12.0, "Height M": 80.0},
            "MEGASPECTRUM_WALL": {"Low Hz": 20.0, "High Hz": 20000.0, "Band Width": 0.025, "Audio Gain": 8.0, "Size X M": 1000.0, "Frequency Bins": 512, "Tower Width M": 1.4, "Tower Depth M": 8.0, "Height M": 120.0},
            "SEA_ABOVE_BELL_RIBS": {"Low Hz": 18.0, "High Hz": 900.0, "Band Width": 0.09, "Audio Gain": 7.0, "Size X M": 1400.0, "Frequency Bins": 384, "Tower Width M": 2.5, "Tower Depth M": 18.0, "Height M": 180.0, "Music Influence": 0.12, "Musical Amplitude": 8.0, "Musical Freq A": 1.0, "Musical Freq B": 5.0},
        },
    },
    "MEL_audio_radial_field": {
        "label": "Audio Radial Field",
        "preset_labels": {"MONOLITH_RIPPLES": "Monolith Ripples", "CHORAL_CRATER": "Choral Crater", "HORIZON_EATER_FIELD": "Horizon Eater Field", "SEA_ABOVE_MEMBRANE": "Sea Above Membrane"},
        "preset_descriptions": {
            "MONOLITH_RIPPLES": "Compact concentric response around a musical world key.",
            "CHORAL_CRATER": "Wide vocal-band arena membrane.",
            "HORIZON_EATER_FIELD": "Massive low-frequency environmental pulse field.",
            "SEA_ABOVE_MEMBRANE": "Regional circular membrane deformation tuned for the 12-20 second Bell pulse concept.",
        },
        "presets": {
            "MONOLITH_RIPPLES": {"Low Hz": 60.0, "High Hz": 6000.0, "Band Width": 0.08, "Audio Gain": 9.0, "Size X M": 100.0, "Radial Segments": 192, "Height M": 12.0, "Radius M": 50.0},
            "CHORAL_CRATER": {"Low Hz": 120.0, "High Hz": 12000.0, "Band Width": 0.05, "Audio Gain": 14.0, "Size X M": 260.0, "Radial Segments": 384, "Height M": 32.0, "Radius M": 130.0},
            "HORIZON_EATER_FIELD": {"Low Hz": 18.0, "High Hz": 1200.0, "Band Width": 0.12, "Audio Gain": 18.0, "Size X M": 1200.0, "Radial Segments": 768, "Height M": 140.0, "Radius M": 600.0},
            "SEA_ABOVE_MEMBRANE": {"Low Hz": 16.0, "High Hz": 700.0, "Band Width": 0.1, "Audio Gain": 6.0, "Size X M": 1800.0, "Radial Segments": 768, "Height M": 55.0, "Radius M": 900.0, "Music Influence": 0.16, "Musical Amplitude": 10.0, "Musical Freq A": 0.75, "Musical Freq B": 6.0},
        },
    },
    # water.py - MEL_water_gerstner (effects)
    "MEL_water_gerstner": {
        "label": "Gerstner Waves",
        "preset_labels": {
            "CALM_POND": "Calm Pond",
            "RIVER_FLOW": "River Flow",
            "OCEAN_SURF": "Ocean Surf",
            "WATERFALL": "Waterfall Pool",
            "RIPPLE_ZONE": "Ripple Zone",
        },
        "preset_descriptions": {
            "CALM_POND": "Slow, low-amplitude swell for ponds and reflecting pools.",
            "RIVER_FLOW": "Directional mid-strength flow for river channels.",
            "OCEAN_SURF": "High-amplitude multi-layer ocean swell.",
            "WATERFALL": "Short-period chop for pool bases under falls.",
            "RIPPLE_ZONE": "Tight symmetric ripple field for distributor chains.",
        },
        "presets": {
            "CALM_POND": {
                "Wave Count": 3, "Wind Direction X": 0.3, "Wind Direction Z": 0.1,
                "Scale": 0.8, "Amplitude": 0.15, "Base Frequency": 0.2,
                "Speed": 0.3, "Animated": True,
            },
            "RIVER_FLOW": {
                "Wave Count": 5, "Wind Direction X": 0.9, "Wind Direction Z": 0.2,
                "Scale": 1.2, "Amplitude": 0.4, "Base Frequency": 0.6,
                "Speed": 1.5, "Animated": True,
            },
            "OCEAN_SURF": {
                "Wave Count": 8, "Wind Direction X": 0.8, "Wind Direction Z": -0.35,
                "Scale": 2.5, "Amplitude": 1.2, "Base Frequency": 1.5,
                "Speed": 2.4, "Animated": True,
            },
            "WATERFALL": {
                "Wave Count": 4, "Wind Direction X": 0.2, "Wind Direction Z": 0.9,
                "Scale": 0.9, "Amplitude": 0.5, "Base Frequency": 2.0,
                "Speed": 0.8, "Animated": True,
            },
            "RIPPLE_ZONE": {
                "Wave Count": 6, "Wind Direction X": 0.0, "Wind Direction Z": 0.0,
                "Scale": 0.6, "Amplitude": 0.25, "Base Frequency": 0.8,
                "Speed": 0.5, "Animated": True,
            },
        },
    },

    # structures.py - MEL_gazebo (structures)
    "MEL_gazebo": {
        "label": "Gazebo",
        "preset_labels": {
            "GARDEN_GAZEBO": "Garden Gazebo",
            "MARKET_PAVILION": "Market Pavilion",
            "BANDSTAND_PARK": "Park Bandstand",
        },
        "preset_descriptions": {
            "GARDEN_GAZEBO": "Classic 10-column garden gazebo with steep roof.",
            "MARKET_PAVILION": "Wide 12-column trading pavilion, open crown.",
            "BANDSTAND_PARK": "Raised octagonal bandstand with finial.",
        },
        "presets": {
            "GARDEN_GAZEBO": {
                "Radius": 2.0, "Column Count": 10, "Column Height": 2.2,
                "Roof Pitch": 1.2, "Beam Radius": 0.05, "Has Finial": True,
                "Has Engawa": True, "Engawa Depth": 0.45, "Has Irimoya": False,
                "Use Default Column": True, "Music Influence": 0.0,
            },
            "MARKET_PAVILION": {
                "Radius": 3.5, "Column Count": 12, "Column Height": 2.8,
                "Roof Pitch": 0.5, "Beam Radius": 0.07, "Has Finial": False,
                "Has Engawa": True, "Engawa Depth": 0.7, "Has Irimoya": False,
                "Use Default Column": True, "Music Influence": 0.0,
            },
            "BANDSTAND_PARK": {
                "Radius": 2.8, "Column Count": 8, "Column Height": 3.2,
                "Roof Pitch": 0.6, "Beam Radius": 0.06, "Has Finial": True,
                "Has Engawa": True, "Engawa Depth": 0.35, "Has Irimoya": True,
                "Use Default Column": True, "Music Influence": 0.0,
            },
        },
    },

    # castle.py - MEL_castle_tower (castle)
    "MEL_castle_tower": {
        "label": "Castle Tower",
        "preset_labels": {
            "WATCHTOWER": "Slender Watchtower",
            "KEEP_BASTION": "Keep Bastion",
            "MINARET_SLIM": "Slim Minaret",
        },
        "preset_descriptions": {
            "WATCHTOWER": "Tall narrow tower with crenellated crown.",
            "KEEP_BASTION": "Massive curtain-wall bastion with high roof.",
            "MINARET_SLIM": "Uncrenellated slender spire tower.",
        },
        "presets": {
            "WATCHTOWER": {
                "Radius": 1.0, "Height": 8.0, "Roof Height": 1.2,
                "Segments": 16, "Wall Thick": 0.25, "Crenellation": True,
            },
            "KEEP_BASTION": {
                "Radius": 2.2, "Height": 7.5, "Roof Height": 2.4,
                "Segments": 32, "Wall Thick": 0.45, "Crenellation": True,
            },
            "MINARET_SLIM": {
                "Radius": 0.8, "Height": 12.0, "Roof Height": 3.0,
                "Segments": 12, "Wall Thick": 0.2, "Crenellation": False,
            },
        },
    },

    # ribbon.py - MEL_ribbon_curve (effects)
    "MEL_ribbon_curve": {
        "label": "Ribbon Curve",
        "preset_labels": {
            "GENTLE_BORDER": "Gentle Border Swirl",
            "PENDANT_SWAG": "Pendant Swag",
            "HELIX_GUARD": "Helix Guard Ring",
        },
        "preset_descriptions": {
            "GENTLE_BORDER": "Low-amplitude ribbon for trim and borders.",
            "PENDANT_SWAG": "Deep drooping swag between hanging points.",
            "HELIX_GUARD": "Twisted closed loop for rings and guards.",
        },
        "presets": {
            "GENTLE_BORDER": {
                "Segments": 96, "Length": 8.0, "Ribbon Width": 0.2,
                "Amplitude": 0.15, "Frequency": 1.2, "Twist": 0.0,
                "Closed Loop": False,
            },
            "PENDANT_SWAG": {
                "Segments": 128, "Length": 10.0, "Ribbon Width": 0.4,
                "Amplitude": 1.2, "Frequency": 0.8, "Twist": 0.0,
                "Closed Loop": False,
            },
            "HELIX_GUARD": {
                "Segments": 128, "Length": 6.0, "Ribbon Width": 0.35,
                "Amplitude": 0.4, "Frequency": 4.0, "Twist": 1.5708,
                "Closed Loop": True,
            },
        },
    },

    # ribbon.py - MEL_allee_ribbon (effects)
    "MEL_allee_ribbon": {
        "label": "Allee Ribbon",
        "preset_labels": {
            "GARDEN_ALLEE": "Garden Allee",
            "CEREMONY_AXIS": "Ceremony Axis",
            "MEADOW_S": "Meadow S",
        },
        "preset_descriptions": {
            "GARDEN_ALLEE": "Default cherry-allee walk: gentle S, crowned camber.",
            "CEREMONY_AXIS": "Straight wide axis for sando-to-porch approach.",
            "MEADOW_S": "Strong meadow curve with higher crown for runoff.",
        },
        "presets": {
            "GARDEN_ALLEE": {
                "Segments": 48, "Length": 8.0, "Path Width": 2.2,
                "S-Curve": 1.0, "Camber": 0.08, "Thickness": 0.12,
            },
            "CEREMONY_AXIS": {
                "Segments": 32, "Length": 10.0, "Path Width": 2.6,
                "S-Curve": 0.0, "Camber": 0.05, "Thickness": 0.12,
            },
            "MEADOW_S": {
                "Segments": 64, "Length": 12.0, "Path Width": 1.8,
                "S-Curve": 1.8, "Camber": 0.12, "Thickness": 0.1,
            },
        },
    },

    # ribbon.py - MEL_allee_ribbon (effects)
    "MEL_allee_ribbon": {
        "label": "Allee Ribbon",
        "preset_labels": {
            "GARDEN_ALLEE": "Garden Allee",
            "CEREMONY_AXIS": "Ceremony Axis",
            "MEADOW_S": "Meadow S",
        },
        "preset_descriptions": {
            "GARDEN_ALLEE": "Default cherry-allee walk: gentle S, crowned camber.",
            "CEREMONY_AXIS": "Straight wide axis for sando-to-porch approach.",
            "MEADOW_S": "Strong meadow curve with higher crown for runoff.",
        },
        "presets": {
            "GARDEN_ALLEE": {
                "Segments": 48, "Length": 8.0, "Path Width": 2.2,
                "S-Curve": 1.0, "Camber": 0.08, "Thickness": 0.12,
            },
            "CEREMONY_AXIS": {
                "Segments": 32, "Length": 10.0, "Path Width": 2.6,
                "S-Curve": 0.0, "Camber": 0.05, "Thickness": 0.12,
            },
            "MEADOW_S": {
                "Segments": 64, "Length": 12.0, "Path Width": 1.8,
                "S-Curve": 1.8, "Camber": 0.12, "Thickness": 0.1,
            },
        },
    },

    # set_dressing.py - MEL_water_them_gazebo (set_dressing)
    "MEL_water_them_gazebo": {
        "label": "Water-Themed Gazebo",
        "preset_labels": {
            "MOAT_RING": "Moat Ring Pavilion",
            "HARBOR_CAFE": "Harbor Cafe",
            "CANAL_PARK": "Canal Park Pavilion",
        },
        "preset_descriptions": {
            "MOAT_RING": "Gazebo set on a calm moat ring at dawn.",
            "HARBOR_CAFE": "Floating cafe pavilion on harbor water.",
            "CANAL_PARK": "Bustling canal-side pavilion with debris scatter.",
        },
        "presets": {
            "MOAT_RING": {
                "Water Level": 0.8, "Current Speed": 0.6, "Ripple Carve": 0.35,
                "Debris Count": 6, "Floating": False,
            },
            "HARBOR_CAFE": {
                "Water Level": 1.2, "Current Speed": 0.4, "Ripple Carve": 0.2,
                "Debris Count": 12, "Floating": True,
            },
            "CANAL_PARK": {
                "Water Level": 1.0, "Current Speed": 0.9, "Ripple Carve": 0.6,
                "Debris Count": 18, "Floating": True,
            },
        },
    },

    # set_dressing.py - MEL_music_them_gazebo (set_dressing)
    "MEL_music_them_gazebo": {
        "label": "Music-Themed Gazebo",
        "preset_labels": {
            "CONCERT_PAVILION": "Concert Pavilion",
            "QUIET_RECITAL": "Quiet Recital",
            "GARDEN_FETE": "Garden Fete",
        },
        "preset_descriptions": {
            "CONCERT_PAVILION": "Full orchestra pavilion, dense notation, 132 BPM.",
            "QUIET_RECITAL": "Small ensemble, sparse notation, slow tempo.",
            "GARDEN_FETE": "Mid-size outdoor chamber set with score lines.",
        },
        "presets": {
            "CONCERT_PAVILION": {
                "Instrument Count": 8, "Notation Density": 0.7,
                "Harmonic Panel Count": 6, "Tempo": 132.0, "Has Score Lines": True,
            },
            "QUIET_RECITAL": {
                "Instrument Count": 3, "Notation Density": 0.3,
                "Harmonic Panel Count": 3, "Tempo": 88.0, "Has Score Lines": False,
            },
            "GARDEN_FETE": {
                "Instrument Count": 6, "Notation Density": 0.6,
                "Harmonic Panel Count": 4, "Tempo": 108.0, "Has Score Lines": True,
            },
        },
    },

    # recursive_castle.py - MEL_recursive_castle_spire (castle)
    "MEL_recursive_castle_spire": {
        "label": "Recursive Castle Spire",
        "preset_labels": {
            "GOLDEN_SPIRE": "Golden-Ratio Spire",
            "SLIM_MINARET": "Slim Minaret Stack",
            "FORTRESS_MAIN": "Fortress Main Tower",
        },
        "preset_descriptions": {
            "GOLDEN_SPIRE": "Classic 0.618 golden-ratio recursive spire.",
            "SLIM_MINARET": "Tall aggressive ratio stack, five recursion levels.",
            "FORTRESS_MAIN": "Wide four-sub-tower fortress mast.",
        },
        "presets": {
            "GOLDEN_SPIRE": {
                "Base Radius": 1.5, "Base Height": 5.0, "Scale Ratio": 0.618,
                "Roof Height": 2.2, "Sub Tower Radius": 0.9, "Sub Tower Count": 4,
                "Recursion Levels": 4,
            },
            "SLIM_MINARET": {
                "Base Radius": 0.9, "Base Height": 8.0, "Scale Ratio": 0.55,
                "Roof Height": 3.0, "Sub Tower Radius": 0.5, "Sub Tower Count": 3,
                "Recursion Levels": 5,
            },
            "FORTRESS_MAIN": {
                "Base Radius": 2.4, "Base Height": 6.0, "Scale Ratio": 0.7,
                "Roof Height": 2.0, "Sub Tower Radius": 1.2, "Sub Tower Count": 6,
                "Recursion Levels": 3,
            },
        },
    },

    # nikki_quarter.py - MEL_nikki_quarter (structures)
    "MEL_nikki_quarter": {
        "label": "Nikki Flora Quarter",
        "preset_labels": {
            "TOWNHOUSE_SWEET": "Townhouse Sweet",
            "TEA_PAVILION": "Tea Pavilion",
            "RUINED_SHRINE": "Ruined Shrine",
        },
        "preset_descriptions": {
            "TOWNHOUSE_SWEET": "Three-floor bay-window townhouse (Mode 0).",
            "TEA_PAVILION": "Two-tier tea pavilion with awning (Mode 1).",
            "RUINED_SHRINE": "Weather-beaten ruined walkway with rubble (Mode 3).",
        },
        "presets": {
            "TOWNHOUSE_SWEET": {
                "Mode": 0, "Variation": 0.4, "Seed": 13,
                "Width": 4.0, "Depth": 3.5, "Floors": 3, "Floor Height": 2.7,
                "Window Count": 4, "Roof Mode": 1, "Roof Pitch": 0.7,
                "Eave Overhang": 0.5, "Bay Window": True, "Balcony": True,
                "Flower Boxes": True, "Chimney": True, "Lantern": True,
                "Porch": True, "Trim Cornice": True,
            },
            "TEA_PAVILION": {
                "Mode": 1, "Variation": 0.35, "Seed": 21,
                "Pavilion Width": 5.0, "Pavilion Depth": 4.0,
                "Column Height": 3.0, "Column Radius": 0.07, "Overhang": 0.6,
                "Tier Count": 2, "Awning": True, "Counter": True, "Cushions": True,
            },
            "RUINED_SHRINE": {
                "Mode": 3, "Variation": 0.6, "Seed": 42,
                "Ruin Width": 4.5, "Ruin Depth": 2.5, "Ruin Height": 4.0,
                "Wall Break": 2, "Lean": 0.3, "Broken Roof": True,
                "Rubble": True, "Column Stumps": True,
            },
        },
    },

    # sky_observatory.py - MEL_sky_observatory (structures)
    "MEL_sky_observatory": {
        "label": "Celestial Dream Observatory",
        "preset_labels": {
            "CELESTIAL_DREAM": "Celestial Dream",
            "MINIMAL_ISLE": "Minimal Sky Isle",
            "RING_TEMPLE": "Ring Temple",
        },
        "preset_descriptions": {
            "CELESTIAL_DREAM": "Full hero island: orrery rings, planets, lanterns.",
            "MINIMAL_ISLE": "Two rings, no fixtures - clean silhouette.",
            "RING_TEMPLE": "Five steep rings, lanterns and finial, high wobble.",
        },
        "presets": {
            "CELESTIAL_DREAM": {
                "Island Radius": 3.0, "Island Height": 1.4, "Drum Radius": 1.6,
                "Drum Height": 2.6, "Dome Radius": 1.8, "Ring Count": 4,
                "Ring Tilt": 20.0, "Planets": True, "Deck Railing": True,
                "Lanterns": True, "Star Finial": True, "Wobble": 0.05, "Seed": 7,
            },
            "MINIMAL_ISLE": {
                "Island Radius": 2.6, "Island Height": 1.8, "Drum Radius": 1.4,
                "Drum Height": 2.2, "Dome Radius": 1.6, "Ring Count": 2,
                "Ring Tilt": 12.0, "Planets": True, "Deck Railing": False,
                "Lanterns": False, "Star Finial": False, "Wobble": 0.02, "Seed": 11,
            },
            "RING_TEMPLE": {
                "Island Radius": 3.4, "Island Height": 1.2, "Drum Radius": 1.8,
                "Drum Height": 2.8, "Dome Radius": 2.0, "Ring Count": 5,
                "Ring Tilt": 30.0, "Planets": False, "Deck Railing": True,
                "Lanterns": True, "Star Finial": True, "Wobble": 0.08, "Seed": 3,
            },
        },
    },

    # escher_waterfall.py - MEL_escher_waterfall (castle)
    "MEL_escher_waterfall": {
        "label": "Escher Waterfall",
        "preset_labels": {
            "IMPOSSIBLE_TRIBAR": "Impossible Tribar",
            "QUIET_LOOP": "Quiet Loop",
            "CHAOS_CASCADE": "Chaos Cascade",
        },
        "preset_descriptions": {
            "IMPOSSIBLE_TRIBAR": "Canonical channel loop with pillars and splash ring.",
            "QUIET_LOOP": "Bare loop without fixtures - hero prop read.",
            "CHAOS_CASCADE": "Deep channel, wide cascade, all fixtures on.",
        },
        "presets": {
            "IMPOSSIBLE_TRIBAR": {
                "Channel Length X": 6.0, "Channel Length Y": 4.5, "Channel Width": 1.0,
                "Channel Depth": 0.5, "Water Level": 0.15, "Side Drop": 0.4,
                "Cascade Width": 1.4, "Cascade": True, "Pillars": True,
                "Tribar Arch": True, "Splash Ring": True, "Wobble": 0.05, "Seed": 7,
            },
            "QUIET_LOOP": {
                "Channel Length X": 7.0, "Channel Length Y": 5.0, "Channel Width": 1.2,
                "Channel Depth": 0.4, "Water Level": 0.1, "Side Drop": 0.25,
                "Cascade Width": 1.6, "Cascade": True, "Pillars": False,
                "Tribar Arch": False, "Splash Ring": False, "Wobble": 0.02, "Seed": 9,
            },
            "CHAOS_CASCADE": {
                "Channel Length X": 5.0, "Channel Length Y": 3.5, "Channel Width": 0.8,
                "Channel Depth": 0.7, "Water Level": 0.25, "Side Drop": 0.9,
                "Cascade Width": 2.2, "Cascade": True, "Pillars": True,
                "Tribar Arch": True, "Splash Ring": True, "Wobble": 0.12, "Seed": 101,
            },
        },
    },

    # music.py - MEL_music_staff (music)
    "MEL_music_staff": {
        "label": "Music Staff",
        "preset_labels": {
            "LESSON_LINE": "Lesson Single Bar",
            "CONCERT_SYSTEM": "Concert Grand System",
            "RAIL_CLEF": "Rail Staff",
        },
        "preset_descriptions": {
            "LESSON_LINE": "Short one-bar staff for practice cues.",
            "CONCERT_SYSTEM": "Eight-bar grand staff at concert spacing.",
            "RAIL_CLEF": "Wide staff without clef for balcony rails.",
        },
        "presets": {
            "LESSON_LINE": {
                "Length": 2.0, "Line Spacing": 0.12, "Thickness": 0.008,
                "Bar Count": 1, "Show Clef": True,
            },
            "CONCERT_SYSTEM": {
                "Length": 8.0, "Line Spacing": 0.18, "Thickness": 0.01,
                "Bar Count": 8, "Show Clef": True,
            },
            "RAIL_CLEF": {
                "Length": 6.0, "Line Spacing": 0.22, "Thickness": 0.02,
                "Bar Count": 6, "Show Clef": False,
            },
        },
    },

    # profiles.py - MEL_column (profiles)
    "MEL_column": {
        "label": "Column",
        "preset_labels": {
            "DORIC_SOBER": "Sober Doric",
            "FLUTED_IONIC": "Fluted Ionic",
            "PILASTER_SLIM": "Slim Pilaster",
        },
        "preset_descriptions": {
            "DORIC_SOBER": "16-sided unfluted column with modest caps.",
            "FLUTED_IONIC": "Tall 20-sided fluted column with tall capital.",
            "PILASTER_SLIM": "Narrow flat pilaster for wall reads.",
        },
        "presets": {
            "DORIC_SOBER": {
                "Height": 3.0, "Radius": 0.22, "Sides": 16, "Fluted": False,
                "Capital Height": 0.12, "Base Height": 0.08,
            },
            "FLUTED_IONIC": {
                "Height": 4.0, "Radius": 0.18, "Sides": 20, "Fluted": True,
                "Capital Height": 0.2, "Base Height": 0.12,
            },
            "PILASTER_SLIM": {
                "Height": 2.4, "Radius": 0.1, "Sides": 8, "Fluted": False,
                "Capital Height": 0.08, "Base Height": 0.05,
            },
        },
    },

    # pcg_integration.py - MEL_pcg_water_tags_v2 (set_dressing)
    "MEL_pcg_water_tags_v2": {
        "label": "PCG Water Tags v2",
        "preset_labels": {
            "RIVER_TAGS": "River Tag Field",
            "LAKE_TAGS": "Stilled Lake Tags",
            "WHITEWATER_TAGS": "Whitewater Tags",
        },
        "preset_descriptions": {
            "RIVER_TAGS": "Shallow fast water for river PCG fields.",
            "LAKE_TAGS": "Deep still water, static field.",
            "WHITEWATER_TAGS": "Near-surface high-foam fast flow.",
        },
        "presets": {
            "RIVER_TAGS": {
                "Tag Type": 0, "Water Depth": 1.5, "Current Speed": 2.0,
                "Foam Intensity": 0.7, "Is Dynamic": True,
            },
            "LAKE_TAGS": {
                "Tag Type": 0, "Water Depth": 3.0, "Current Speed": 0.4,
                "Foam Intensity": 0.3, "Is Dynamic": False,
            },
            "WHITEWATER_TAGS": {
                "Tag Type": 0, "Water Depth": 0.8, "Current Speed": 3.5,
                "Foam Intensity": 1.0, "Is Dynamic": True,
            },
        },
    },

    # effects.py - MEL_effect_wave (effects)
    "MEL_effect_wave": {
        "label": "Wave Effect",
        "preset_labels": {
            "FAIRY_RIPPLE": "Fairy Ripple",
            "EARTHQUAKE_SURGE": "Earthquake Surge",
            "MIDNIGHT_SWELL": "Midnight Swell",
        },
        "preset_descriptions": {
            "FAIRY_RIPPLE": "High-frequency soft ripple in normal space.",
            "EARTHQUAKE_SURGE": "Low-frequency world-space displacement.",
            "MIDNIGHT_SWELL": "Phase-shifted mid swell for calm surfaces.",
        },
        "presets": {
            "FAIRY_RIPPLE": {
                "Amplitude": 0.15, "Frequency": 6.0, "Phase": 1.5708,
                "Normal Space": True,
            },
            "EARTHQUAKE_SURGE": {
                "Amplitude": 1.2, "Frequency": 0.8, "Phase": 0.0,
                "Normal Space": False,
            },
            "MIDNIGHT_SWELL": {
                "Amplitude": 0.5, "Frequency": 3.0, "Phase": 3.14159,
                "Normal Space": True,
            },
        },
    },

    # filigree.py - MEL_harmonic_orb (music)
    "MEL_harmonic_orb": {
        "label": "Harmonic Orb",
        "preset_labels": {
            "SOOTHING_ORB": "Soothing Orb",
            "DREAM_CHANDELIER": "Dream Chandelier",
            "SOLO_DESK_ORB": "Solo Desk Orb",
        },
        "preset_descriptions": {
            "SOOTHING_ORB": "Balanced orb with soft glow for bedside reads.",
            "DREAM_CHANDELIER": "Large double-ring orb, high glow, hero light.",
            "SOLO_DESK_ORB": "Compact single-scale desk prop.",
        },
        "presets": {
            "SOOTHING_ORB": {
                "Orb Radius": 0.45, "Ring Radius": 0.85, "Ring Thickness": 0.015,
                "Glow Intensity": 1.2, "Orb Subdivisions": 3,
            },
            "DREAM_CHANDELIER": {
                "Orb Radius": 0.6, "Ring Radius": 1.4, "Ring Thickness": 0.03,
                "Glow Intensity": 2.5, "Orb Subdivisions": 4,
            },
            "SOLO_DESK_ORB": {
                "Orb Radius": 0.35, "Ring Radius": 0.6, "Ring Thickness": 0.012,
                "Glow Intensity": 0.8, "Orb Subdivisions": 2,
            },
        },
    },

    # music_instruments.py - MEL_brass_pipe (music)
    "MEL_brass_pipe": {
        "label": "Brass Pipe",
        "preset_labels": {
            "TRUMPET_STOP": "Trumpet Stop",
            "HUNTING_HORN": "Hunting Horn",
        },
        "preset_descriptions": {
            "TRUMPET_STOP": "Short bright pipe with gentle bell flare.",
            "HUNTING_HORN": "Long conic horn with dramatic flare.",
        },
        "presets": {
            "TRUMPET_STOP": {
                "Pipe Length": 24.0, "Bore Profile": 0.6, "Bell Flare": 2.5,
                "Sections": 24, "Mouth Taper": 0.6, "Open Ends": True,
                "Bell Radius Start": 1.2, "Bell Radius End": 2.8,
            },
            "HUNTING_HORN": {
                "Pipe Length": 60.0, "Bore Profile": 0.4, "Bell Flare": 4.0,
                "Sections": 40, "Mouth Taper": 0.4, "Open Ends": True,
                "Bell Radius Start": 0.8, "Bell Radius End": 4.5,
            },
        },
    },

    # music.py - MEL_music_note_head (music)
    "MEL_music_note_head": {
        "label": "Music Note Head",
        "preset_labels": {
            "QUARTER_BEAT": "Quarter Beat",
            "TREMBLE_EIGHTH": "Eighth Tremble",
            "HOLDING_HALF": "Holding Half",
        },
        "preset_descriptions": {
            "QUARTER_BEAT": "Default quarter note with stem.",
            "TREMBLE_EIGHTH": "Flagged eighth note at higher LOD.",
            "HOLDING_HALF": "Open unbent half note, double duration.",
        },
        "presets": {
            "QUARTER_BEAT": {
                "Scale": 1.0, "Pitch": 0.0, "Duration": 1.0, "Velocity": 0.8,
                "Note Kind": 2, "LOD": 1, "Has Stem": True, "Has Flag": False,
                "Realize for export": False,
            },
            "TREMBLE_EIGHTH": {
                "Scale": 0.9, "Pitch": 0.5, "Duration": 0.5, "Velocity": 0.7,
                "Note Kind": 2, "LOD": 2, "Has Stem": True, "Has Flag": True,
                "Realize for export": False,
            },
            "HOLDING_HALF": {
                "Scale": 1.1, "Pitch": -1.0, "Duration": 2.0, "Velocity": 0.6,
                "Note Kind": 2, "LOD": 1, "Has Stem": False, "Has Flag": False,
                "Realize for export": False,
            },
        },
    },

    # effects.py - MEL_effect_magic (effects) - 3 of 10 legacy looks
    "MEL_effect_magic": {
        "label": "Magic Distortion",
        "preset_labels": {
            "LIQUID": "Liquid",
            "CRYSTAL": "Crystal",
            "GRAVITY_WELL": "Gravity Well",
        },
        "preset_descriptions": {
            "LIQUID": "Flowing animated noise, mid intensity - liquid-surface read.",
            "CRYSTAL": "High-frequency chromatic facets, static - gem/ice read.",
            "GRAVITY_WELL": "Low-frequency pull toward a downward attractor.",
        },
        "presets": {
            "LIQUID": {
                "Intensity": 0.8, "Frequency": 3.5, "Phase": 0.0,
                "Noise Scale": 2.0, "Layers": 3, "Chromatic": False,
                "Animate": True, "Attractor": [0.0, 0.0, 1.0],
            },
            "CRYSTAL": {
                "Intensity": 1.4, "Frequency": 12.0, "Phase": 1.5708,
                "Noise Scale": 0.4, "Layers": 5, "Chromatic": True,
                "Animate": False, "Attractor": [0.0, 0.0, 1.0],
            },
            "GRAVITY_WELL": {
                "Intensity": 2.4, "Frequency": 0.6, "Phase": 0.0,
                "Noise Scale": 4.0, "Layers": 4, "Chromatic": False,
                "Animate": True, "Attractor": [0.0, 0.0, -1.0],
            },
        },
    },

    # music.py - MEL_music_harmonic (music)
    "MEL_music_harmonic": {
        "label": "Harmonic Driver",
        "preset_labels": {
            "SOLO_FUNDAMENTAL": "Solo Fundamental",
            "CHOIR_STACK": "Choir Stack",
            "PHRASE_SWELL": "Phrase Swell",
        },
        "preset_descriptions": {
            "SOLO_FUNDAMENTAL": "Single-voice fundamental, short phrase, almost no overtones.",
            "CHOIR_STACK": "Five-voice stack with strong harmonic and octave mix.",
            "PHRASE_SWELL": "Mid ensemble with long fade-in/out envelope.",
        },
        "presets": {
            "SOLO_FUNDAMENTAL": {
                "Base Frequency": 1.0, "Harmonic Blend": 0.1, "Octave Mix": 0.0,
                "Voice Count": 1.0, "Amplitude": 0.6, "Fade In": 0.05,
                "Fade Out": 0.05, "Note Count": 8,
            },
            "CHOIR_STACK": {
                "Base Frequency": 2.5, "Harmonic Blend": 0.85, "Octave Mix": 0.7,
                "Voice Count": 5.0, "Amplitude": 0.9, "Fade In": 0.15,
                "Fade Out": 0.2, "Note Count": 32,
            },
            "PHRASE_SWELL": {
                "Base Frequency": 3.0, "Harmonic Blend": 0.5, "Octave Mix": 0.4,
                "Voice Count": 3.0, "Amplitude": 1.2, "Fade In": 0.4,
                "Fade Out": 0.5, "Note Count": 24,
            },
        },
    },

    # music.py - MEL_music_treble_clef (music)
    "MEL_music_treble_clef": {
        "label": "Treble Clef",
        "preset_labels": {
            "STAFF_MARK": "Staff Mark",
            "RAIL_ORNAMENT": "Rail Ornament",
            "TIGHT_CURL": "Tight Curl",
        },
        "preset_descriptions": {
            "STAFF_MARK": "Default G-clef scale for staff heads.",
            "RAIL_ORNAMENT": "Large thick clef for balcony rails.",
            "TIGHT_CURL": "Compact high-tightness ornamental curl.",
        },
        "presets": {
            "STAFF_MARK": {
                "Scale": 1.0, "Thickness": 0.018,
                "Spiral Tightness": 0.5, "Body Curve": 0.5,
            },
            "RAIL_ORNAMENT": {
                "Scale": 2.2, "Thickness": 0.05,
                "Spiral Tightness": 0.7, "Body Curve": 0.35,
            },
            "TIGHT_CURL": {
                "Scale": 0.6, "Thickness": 0.012,
                "Spiral Tightness": 0.95, "Body Curve": 0.8,
            },
        },
    },

    # music_heroes.py - MEL_music_key_unit (music)
    "MEL_music_key_unit": {
        "label": "Music Key Unit",
        "preset_labels": {
            "WHITE_IVORY": "White Ivory",
            "BLACK_ACCIDENTAL": "Black Accidental",
            "WALKABLE_TREAD": "Walkable Tread",
        },
        "preset_descriptions": {
            "WHITE_IVORY": "Life-size white key with a modest front lip.",
            "BLACK_ACCIDENTAL": "Raised accidental, shorter and narrower.",
            "WALKABLE_TREAD": "Oversized key you can walk as a stair tread.",
        },
        "presets": {
            "WHITE_IVORY": {
                "Width": 0.0235, "Length": 0.15, "Height": 0.018,
                "Is Accidental": False, "Pitch": 0.0, "Lip Depth": 0.012,
            },
            "BLACK_ACCIDENTAL": {
                "Width": 0.0235, "Length": 0.15, "Height": 0.018,
                "Is Accidental": True, "Pitch": 1.0, "Lip Depth": 0.008,
            },
            "WALKABLE_TREAD": {
                "Width": 0.28, "Length": 0.55, "Height": 0.08,
                "Is Accidental": False, "Pitch": 0.0, "Lip Depth": 0.06,
            },
        },
    },

    # music_heroes.py - MEL_music_piano_roll (music)
    "MEL_music_piano_roll": {
        "label": "Music Piano Roll",
        "preset_labels": {
            "ENDLESS_88": "Endless 88",
            "WALKABLE_XYLO_PATH": "Walkable Xylo Path",
            "MARIMBA_GALLERY": "Marimba Gallery",
        },
        "preset_descriptions": {
            "ENDLESS_88": "Concert piano: 88 keys, period = key width, endless along the spline.",
            "WALKABLE_XYLO_PATH": "Xylophone bars as a walkable path (Profile=1).",
            "MARIMBA_GALLERY": "Longer, taller marimba bars for a gallery walk (Profile=2).",
        },
        "presets": {
            "ENDLESS_88": {
                "Key Width": 0.0235, "Key Length": 0.15, "Key Height": 0.018,
                "Profile": 0, "Key Count": 88, "Endless": True,
                "Length": 2.07, "Pitch Start": 0.0, "Black Offset": 0.04,
            },
            "WALKABLE_XYLO_PATH": {
                "Key Width": 0.22, "Key Length": 0.55, "Key Height": 0.08,
                "Profile": 1, "Key Count": 24, "Endless": True,
                "Length": 8.0, "Pitch Start": 0.0, "Black Offset": 0.12,
            },
            "MARIMBA_GALLERY": {
                "Key Width": 0.28, "Key Length": 0.8, "Key Height": 0.1,
                "Profile": 2, "Key Count": 16, "Endless": True,
                "Length": 10.0, "Pitch Start": 0.0, "Black Offset": 0.16,
            },
        },
    },

    # music_heroes.py - MEL_music_sheet_rail (music)
    "MEL_music_sheet_rail": {
        "label": "Sheet Music Rail",
        "preset_labels": {
            "CONCERT_HALL_RAIL": "Concert Hall Rail",
            "BALCONY_STAFF": "Balcony Staff",
            "GALLERY_WALK": "Gallery Walk",
        },
        "preset_descriptions": {
            "CONCERT_HALL_RAIL": "Walkable five-line staff railing for a concert balcony.",
            "BALCONY_STAFF": "Shorter rail, denser notes, no clef.",
            "GALLERY_WALK": "Long thick-line gallery rail with sparse notes.",
        },
        "presets": {
            "CONCERT_HALL_RAIL": {
                "Length": 12.0, "Height": 1.05, "Line Thickness": 0.045,
                "Line Spacing": 0.12, "Note Count": 16, "Note Size": 0.2,
                "Post Count": 7, "Show Clef": True,
            },
            "BALCONY_STAFF": {
                "Length": 6.0, "Height": 0.95, "Line Thickness": 0.03,
                "Line Spacing": 0.1, "Note Count": 24, "Note Size": 0.14,
                "Post Count": 4, "Show Clef": False,
            },
            "GALLERY_WALK": {
                "Length": 18.0, "Height": 1.15, "Line Thickness": 0.06,
                "Line Spacing": 0.14, "Note Count": 8, "Note Size": 0.22,
                "Post Count": 10, "Show Clef": True,
            },
        },
    },

    # music_heroes.py - MEL_music_room_shell (structures)
    "MEL_music_room_shell": {
        "label": "Music Room Shell",
        "preset_labels": {
            "RECITAL_BOX": "Recital Box",
            "PRACTICE_CELL": "Practice Cell",
            "HALL_DADO": "Hall With Dado",
        },
        "preset_descriptions": {
            "RECITAL_BOX": "Mid-size recital room, door and window, dado staff band.",
            "PRACTICE_CELL": "Tight practice cell, door only, no dado.",
            "HALL_DADO": "Long hall with a high dado staff band.",
        },
        "presets": {
            "RECITAL_BOX": {
                "Room Length": 10.0, "Room Width": 7.0, "Room Height": 4.5,
                "Wall Thickness": 0.28, "Ceiling": True,
                "Cut Door": True, "Cut Window": True,
                "Dado Staff Band": True, "Dado Height": 1.05,
                "Dado Thickness": 0.03, "Line Spacing": 0.12,
            },
            "PRACTICE_CELL": {
                "Room Length": 4.5, "Room Width": 3.6, "Room Height": 3.2,
                "Wall Thickness": 0.22, "Ceiling": True,
                "Cut Door": True, "Cut Window": False,
                "Dado Staff Band": False, "Dado Height": 0.9,
                "Dado Thickness": 0.02, "Line Spacing": 0.1,
            },
            "HALL_DADO": {
                "Room Length": 16.0, "Room Width": 8.0, "Room Height": 6.0,
                "Wall Thickness": 0.35, "Ceiling": True,
                "Cut Door": True, "Cut Window": True,
                "Dado Staff Band": True, "Dado Height": 1.2,
                "Dado Thickness": 0.04, "Line Spacing": 0.14,
            },
        },
    },

    # music_heroes.py - MEL_music_harp (music)
    "MEL_music_harp": {
        "label": "Music Harp",
        "preset_labels": {
            "PEDAL_HARP_C": "Pedal Harp C",
            "LAP_HARP": "Lap Harp",
            "ENDLESS_NECK": "Endless Neck",
        },
        "preset_descriptions": {
            "PEDAL_HARP_C": "Concert pedal harp, 47 strings, C pitch start.",
            "LAP_HARP": "Small folk harp, fewer strings, short pillar.",
            "ENDLESS_NECK": "String count from neck length / spacing.",
        },
        "presets": {
            "PEDAL_HARP_C": {
                "Height": 1.8, "Depth": 0.55,
                "Soundboard Width": 0.42, "Soundboard Height": 0.95,
                "String Count": 47, "String Radius": 0.003, "String Spacing": 0.012,
                "Endless": False, "Pitch Start": 0.0, "Pillar Radius": 0.045,
            },
            "LAP_HARP": {
                "Height": 0.7, "Depth": 0.28,
                "Soundboard Width": 0.22, "Soundboard Height": 0.4,
                "String Count": 22, "String Radius": 0.0025, "String Spacing": 0.01,
                "Endless": False, "Pitch Start": 12.0, "Pillar Radius": 0.022,
            },
            "ENDLESS_NECK": {
                "Height": 1.6, "Depth": 0.7,
                "Soundboard Width": 0.38, "Soundboard Height": 0.85,
                "String Count": 36, "String Radius": 0.004, "String Spacing": 0.014,
                "Endless": True, "Pitch Start": 0.0, "Pillar Radius": 0.04,
            },
        },
    },

    # filigree.py - MEL_filigree_spiral (filigree)
    "MEL_filigree_spiral": {
        "label": "Filigree Spiral",
        "preset_labels": {
            "TIGHT_SCROLL": "Tight Scroll",
            "NOUVEAU_VOLUTE": "Nouveau Volute",
            "HELIX_CREST": "Helix Crest",
        },
        "preset_descriptions": {
            "TIGHT_SCROLL": "Small flat scroll for corners and insets.",
            "NOUVEAU_VOLUTE": "Classic Art Nouveau volute, modest lift.",
            "HELIX_CREST": "Tall many-turn helix for cresting.",
        },
        "presets": {
            "TIGHT_SCROLL": {
                "Inner Radius": 0.03, "Outer Radius": 0.35, "Turns": 1.5,
                "Taper Power": 1.2, "Profile Radius": 0.012, "Spiral Height": 0.0,
                "Resolution": 48, "Profile Resolution": 6,
            },
            "NOUVEAU_VOLUTE": {
                "Inner Radius": 0.05, "Outer Radius": 0.8, "Turns": 3.0,
                "Taper Power": 0.8, "Profile Radius": 0.02, "Spiral Height": 0.05,
                "Resolution": 96, "Profile Resolution": 10,
            },
            "HELIX_CREST": {
                "Inner Radius": 0.08, "Outer Radius": 1.4, "Turns": 6.0,
                "Taper Power": 0.4, "Profile Radius": 0.03, "Spiral Height": 0.7,
                "Resolution": 160, "Profile Resolution": 12,
            },
        },
    },

    # escher_belvedere.py - MEL_escher_belvedere (castle)
    "MEL_escher_belvedere": {
        "label": "Escher Belvedere",
        "preset_labels": {
            "CANONICAL_LOGGIA": "Canonical Loggia",
            "QUIET_PAVILION": "Quiet Pavilion",
            "TWISTED_TOWER": "Twisted Tower",
        },
        "preset_descriptions": {
            "CANONICAL_LOGGIA": "45-degree upper rotation with staircase, vines, threading columns.",
            "QUIET_PAVILION": "Unrotated two-story read, no fixtures.",
            "TWISTED_TOWER": "90-degree upper, dense columns, high wobble.",
        },
        "presets": {
            "CANONICAL_LOGGIA": {
                "Lower Width": 5.0, "Lower Depth": 4.0, "Upper Width": 3.0,
                "Upper Depth": 2.4, "Upper Height": 2.6, "Upper Rotation": 45.0,
                "Column Count X": 2, "Column Count Y": 2, "Column Radius": 0.08,
                "Floor Thickness": 0.2, "Staircase": True, "Vines": True,
                "Tall Threading Columns": True, "Wobble": 0.05, "Seed": 11,
            },
            "QUIET_PAVILION": {
                "Lower Width": 4.2, "Lower Depth": 3.4, "Upper Width": 2.4,
                "Upper Depth": 2.0, "Upper Height": 2.2, "Upper Rotation": 0.0,
                "Column Count X": 2, "Column Count Y": 2, "Column Radius": 0.06,
                "Floor Thickness": 0.16, "Staircase": False, "Vines": False,
                "Tall Threading Columns": False, "Wobble": 0.02, "Seed": 3,
            },
            "TWISTED_TOWER": {
                "Lower Width": 6.5, "Lower Depth": 5.5, "Upper Width": 4.5,
                "Upper Depth": 3.6, "Upper Height": 3.4, "Upper Rotation": 90.0,
                "Column Count X": 4, "Column Count Y": 4, "Column Radius": 0.12,
                "Floor Thickness": 0.28, "Staircase": True, "Vines": True,
                "Tall Threading Columns": True, "Wobble": 0.18, "Seed": 77,
            },
        },
    },

    # escher_penrose_stairs.py - MEL_escher_penrose_stairs (castle)
    "MEL_escher_penrose_stairs": {
        "label": "Escher Penrose Stairs",
        "preset_labels": {
            "CLASSIC_LOOP": "Classic Loop",
            "BARE_ASCENT": "Bare Ascent",
            "DOUBLE_CHAOS": "Double Chaos",
        },
        "preset_descriptions": {
            "CLASSIC_LOOP": "Four-run loop with railings and second tier.",
            "BARE_ASCENT": "Minimal three-run loop, no railings or second loop.",
            "DOUBLE_CHAOS": "Eight-run dense loop, high wobble, both tiers.",
        },
        "presets": {
            "CLASSIC_LOOP": {
                "Runs": 4, "Run Length": 4.0, "Run Width": 1.6,
                "Steps per Run": 5, "Step Rise": 0.22, "Step Depth": 0.45,
                "Railings": True, "Second Loop": True, "Loop Offset": 0.9,
                "Wobble": 0.05, "Seed": 7,
            },
            "BARE_ASCENT": {
                "Runs": 3, "Run Length": 3.2, "Run Width": 1.2,
                "Steps per Run": 4, "Step Rise": 0.18, "Step Depth": 0.35,
                "Railings": False, "Second Loop": False, "Loop Offset": 0.0,
                "Wobble": 0.02, "Seed": 2,
            },
            "DOUBLE_CHAOS": {
                "Runs": 8, "Run Length": 5.5, "Run Width": 2.2,
                "Steps per Run": 8, "Step Rise": 0.32, "Step Depth": 0.7,
                "Railings": True, "Second Loop": True, "Loop Offset": 1.6,
                "Wobble": 0.22, "Seed": 101,
            },
        },
    },

    # castle.py - MEL_castle_assembler (castle) - scalar sockets only
    "MEL_castle_assembler": {
        "label": "Castle Full Assembler",
        "preset_labels": {
            "KEEP_COURT": "Keep Court",
            "WIDE_BAILEY": "Wide Bailey",
            "COMPACT_CITADEL": "Compact Citadel",
        },
        "preset_descriptions": {
            "KEEP_COURT": "Default courtyard with complete walls and corner towers.",
            "WIDE_BAILEY": "Large scaled bailey, full curtain and corners.",
            "COMPACT_CITADEL": "Tight site, complete walls, no corner towers.",
        },
        "presets": {
            "KEEP_COURT": {
                "Site Scale": 1.0, "Courtyard Width": 20.0, "Courtyard Depth": 15.0,
                "Complete Walls": True, "Corner Towers": True, "Use Default Seed": True,
            },
            "WIDE_BAILEY": {
                "Site Scale": 2.2, "Courtyard Width": 48.0, "Courtyard Depth": 36.0,
                "Complete Walls": True, "Corner Towers": True, "Use Default Seed": True,
            },
            "COMPACT_CITADEL": {
                "Site Scale": 0.6, "Courtyard Width": 10.0, "Courtyard Depth": 8.0,
                "Complete Walls": True, "Corner Towers": False, "Use Default Seed": True,
            },
        },
    },

    "MEL_castle_gothic_window": {
        "label": "Castle Gothic Window",
        "preset_labels": {
            "PORTAL_LANCET": "Portal Lancet",
            "BAY_TRACERY": "Bay Tracery",
            "NARROW_SLIT": "Narrow Slit",
        },
        "preset_descriptions": {
            "PORTAL_LANCET": "Tall pointed portal with two mullions (gothic_kit language).",
            "BAY_TRACERY": "Wider bay with denser tracery.",
            "NARROW_SLIT": "Arrow-slit scale lancet, no bars.",
        },
        "presets": {
            "PORTAL_LANCET": {
                "Width": 1.4, "Height": 2.8, "Arch Point": 0.55,
                "Frame Thick": 0.1, "Tracery Bars": 2, "Bar Width": 0.04,
                "Music Influence": 0.0,
            },
            "BAY_TRACERY": {
                "Width": 2.2, "Height": 3.2, "Arch Point": 0.4,
                "Frame Thick": 0.12, "Tracery Bars": 4, "Bar Width": 0.05,
                "Music Influence": 0.0,
            },
            "NARROW_SLIT": {
                "Width": 0.55, "Height": 2.0, "Arch Point": 0.7,
                "Frame Thick": 0.06, "Tracery Bars": 0, "Bar Width": 0.03,
                "Music Influence": 0.0,
            },
        },
    },

    "MEL_stepped_pyramid": {
        "label": "Stepped Pyramid",
        "preset_labels": {
            "ZIGGURAT_FIVE": "Five-Step Ziggurat",
            "LOW_TERRACE": "Low Terrace",
            "TALL_KEEP": "Tall Keep",
        },
        "preset_descriptions": {
            "ZIGGURAT_FIVE": "Classic five-step shrinking pyramid.",
            "LOW_TERRACE": "Wide shallow terraces.",
            "TALL_KEEP": "Steep eight-step keep.",
        },
        "presets": {
            "ZIGGURAT_FIVE": {
                "Steps": 5, "Base Size": 4.0, "Step Height": 0.4, "Shrink": 0.75,
            },
            "LOW_TERRACE": {
                "Steps": 3, "Base Size": 6.0, "Step Height": 0.25, "Shrink": 0.82,
            },
            "TALL_KEEP": {
                "Steps": 8, "Base Size": 3.2, "Step Height": 0.55, "Shrink": 0.7,
            },
        },
    },

    # ornament.py - P1 thin-kit (vine / radial / frame before new generators)
    "MEL_ornament_vine": {
        "label": "Ornament Vine",
        "preset_labels": {
            "NOUVEAU_SPRAY": "Nouveau Spray",
            "TIGHT_TENDRIL": "Tight Tendril",
            "PANEL_SWAG": "Panel Swag",
        },
        "preset_descriptions": {
            "NOUVEAU_SPRAY": "Classic Art Nouveau S-curve vine for panel interiors.",
            "TIGHT_TENDRIL": "Dense thin tendril for jewelry-scale insets.",
            "PANEL_SWAG": "Wide low-frequency swag for door and wall panels.",
        },
        "presets": {
            "NOUVEAU_SPRAY": {
                "Panel Width": 1.6, "Panel Height": 2.0, "Branch Count": 3.0,
                "Density": 0.5, "Taper Power": 0.7, "Thickness": 0.02,
                "Wave Amp": 0.15, "Wave Freq": 2.0, "Segments": 32,
            },
            "TIGHT_TENDRIL": {
                "Panel Width": 0.9, "Panel Height": 1.2, "Branch Count": 5.0,
                "Density": 0.85, "Taper Power": 1.4, "Thickness": 0.01,
                "Wave Amp": 0.08, "Wave Freq": 3.5, "Segments": 64,
            },
            "PANEL_SWAG": {
                "Panel Width": 2.8, "Panel Height": 1.4, "Branch Count": 2.0,
                "Density": 0.35, "Taper Power": 0.4, "Thickness": 0.035,
                "Wave Amp": 0.28, "Wave Freq": 1.1, "Segments": 48,
            },
        },
    },
    "MEL_ornament_radial": {
        "label": "Ornament Radial",
        "preset_labels": {
            "ROSE_WINDOW": "Rose Window",
            "COMPASS_STAR": "Compass Star",
            "OCULUS_VOID": "Oculus Void",
        },
        "preset_descriptions": {
            "ROSE_WINDOW": "Eight-spoke gothic rose with three rings.",
            "COMPASS_STAR": "Dense twelve-spoke star, no center void.",
            "OCULUS_VOID": "Open oculus with a large center void.",
        },
        "presets": {
            "ROSE_WINDOW": {
                "Radius": 0.8, "Spoke Count": 8, "Ring Count": 3,
                "Profile Radius": 0.015, "Center Void": 0.0,
            },
            "COMPASS_STAR": {
                "Radius": 1.2, "Spoke Count": 12, "Ring Count": 2,
                "Profile Radius": 0.02, "Center Void": 0.0,
            },
            "OCULUS_VOID": {
                "Radius": 1.6, "Spoke Count": 6, "Ring Count": 4,
                "Profile Radius": 0.025, "Center Void": 0.35,
            },
        },
    },
    "MEL_ornament_frame": {
        "label": "Ornament Frame",
        "preset_labels": {
            "THIN_INSET": "Thin Inset",
            "HEAVY_MULLION": "Heavy Mullion",
            "SOFT_PICTURE": "Soft Picture Frame",
        },
        "preset_descriptions": {
            "THIN_INSET": "Narrow sharp frame for panel insets.",
            "HEAVY_MULLION": "Thick tapered mullion for window grids.",
            "SOFT_PICTURE": "Wide softened frame for hanging panels.",
        },
        "presets": {
            "THIN_INSET": {
                "Frame Width": 0.03, "Corner Taper": 0.4, "Smooth": 0.0,
            },
            "HEAVY_MULLION": {
                "Frame Width": 0.12, "Corner Taper": 1.6, "Smooth": 0.0,
            },
            "SOFT_PICTURE": {
                "Frame Width": 0.08, "Corner Taper": 1.0, "Smooth": 1.0,
            },
        },
    },

    # ornament_extras.py - remaining Filigree kit (3)
    "MEL_filigree_corner_volute": {
        "label": "Filigree Corner Volute",
        "preset_labels": {
            "CORNER_SCROLL": "Corner Scroll",
            "DEEP_VOLUTE": "Deep Volute",
            "TINY_EAR": "Tiny Ear",
        },
        "preset_descriptions": {
            "CORNER_SCROLL": "Default corner volute with a small finial.",
            "DEEP_VOLUTE": "Many-turn tapered volute for crest corners.",
            "TINY_EAR": "Compact ear scroll for jewelry-scale frames.",
        },
        "presets": {
            "CORNER_SCROLL": {
                "Outer Radius": 0.5, "Inner Radius": 0.06, "Turns": 1.5,
                "Taper Power": 1.2, "Profile Radius": 0.012,
                "Resolution": 128, "Finial Size": 0.03,
            },
            "DEEP_VOLUTE": {
                "Outer Radius": 0.9, "Inner Radius": 0.04, "Turns": 3.2,
                "Taper Power": 0.7, "Profile Radius": 0.018,
                "Resolution": 192, "Finial Size": 0.05,
            },
            "TINY_EAR": {
                "Outer Radius": 0.22, "Inner Radius": 0.03, "Turns": 1.1,
                "Taper Power": 1.8, "Profile Radius": 0.008,
                "Resolution": 64, "Finial Size": 0.015,
            },
        },
    },
    "MEL_filigree_finial_cross": {
        "label": "Filigree Finial Cross",
        "preset_labels": {
            "SPIRE_CROSS": "Spire Cross",
            "PROCESSIONAL": "Processional Cross",
            "BARE_CROSS": "Bare Cross",
        },
        "preset_descriptions": {
            "SPIRE_CROSS": "Default bar-and-ball finial for spire tips.",
            "PROCESSIONAL": "Taller arms with a large center ball.",
            "BARE_CROSS": "Slim cross, no center ball.",
        },
        "presets": {
            "SPIRE_CROSS": {
                "Height": 0.7, "Arm Width": 0.4, "Bar Thickness": 0.05,
                "Tip Size": 0.09, "Center Ball Size": 0.09, "Has Center Ball": True,
            },
            "PROCESSIONAL": {
                "Height": 1.4, "Arm Width": 0.7, "Bar Thickness": 0.07,
                "Tip Size": 0.14, "Center Ball Size": 0.16, "Has Center Ball": True,
            },
            "BARE_CROSS": {
                "Height": 0.55, "Arm Width": 0.28, "Bar Thickness": 0.035,
                "Tip Size": 0.05, "Center Ball Size": 0.04, "Has Center Ball": False,
            },
        },
    },
    "MEL_filigree_wreath_ring": {
        "label": "Filigree Wreath Ring",
        "preset_labels": {
            "LAUREL_CREST": "Laurel Crest",
            "CROWN_RING": "Crown Ring",
            "MINI_WREATH": "Mini Wreath",
        },
        "preset_descriptions": {
            "LAUREL_CREST": "Default eight-leaf laurel wreath.",
            "CROWN_RING": "Dense tilted wreath for cresting.",
            "MINI_WREATH": "Small four-leaf ring for jewelry.",
        },
        "presets": {
            "LAUREL_CREST": {
                "Radius": 0.3, "Tube Radius": 0.02, "Leaf Count": 8,
                "Leaf Length": 0.18, "Leaf Width": 0.08, "Leaf Tilt": 25.0,
            },
            "CROWN_RING": {
                "Radius": 0.55, "Tube Radius": 0.03, "Leaf Count": 16,
                "Leaf Length": 0.28, "Leaf Width": 0.12, "Leaf Tilt": 40.0,
            },
            "MINI_WREATH": {
                "Radius": 0.15, "Tube Radius": 0.01, "Leaf Count": 6,
                "Leaf Length": 0.08, "Leaf Width": 0.04, "Leaf Tilt": 12.0,
            },
        },
    },

    # operations.py + geometry_extras.py - remaining Operations kit (3)
    "MEL_op_iterate": {
        "label": "Iterate + Power Falloff",
        "preset_labels": {
            "COLONNADE": "Colonnade",
            "TAPER_STAIR": "Taper Stair",
            "DENSE_FENCE": "Dense Fence",
        },
        "preset_descriptions": {
            "COLONNADE": "Eight even-spaced instances, gentle falloff.",
            "TAPER_STAIR": "Few instances with strong power taper.",
            "DENSE_FENCE": "Many tight-spaced posts, even scale.",
        },
        "presets": {
            "COLONNADE": {
                "Count": 8, "Spacing": 1.0, "Base Scale": 1.0,
                "Power Falloff": 0.5, "Even Spacing": True,
            },
            "TAPER_STAIR": {
                "Count": 5, "Spacing": 1.4, "Base Scale": 1.2,
                "Power Falloff": 1.8, "Even Spacing": False,
            },
            "DENSE_FENCE": {
                "Count": 16, "Spacing": 0.35, "Base Scale": 0.8,
                "Power Falloff": 0.15, "Even Spacing": True,
            },
        },
    },
    "MEL_op_bounded": {
        "label": "Bounded Auto-Fit",
        "preset_labels": {
            "FLUSH_FIT": "Flush Fit",
            "PADDED_INSET": "Padded Inset",
            "SOFT_FILL": "Soft Fill",
        },
        "preset_descriptions": {
            "FLUSH_FIT": "Uniform centered fit, no padding.",
            "PADDED_INSET": "Uniform fit with a visible margin.",
            "SOFT_FILL": "Non-uniform fill with a soft exponent.",
        },
        "presets": {
            "FLUSH_FIT": {
                "Padding": 0.0, "Fit Exponent": 1.0,
                "Uniform Scale": True, "Center": True,
            },
            "PADDED_INSET": {
                "Padding": 0.08, "Fit Exponent": 1.0,
                "Uniform Scale": True, "Center": True,
            },
            "SOFT_FILL": {
                "Padding": 0.02, "Fit Exponent": 1.8,
                "Uniform Scale": False, "Center": True,
            },
        },
    },
    "MEL_op_power_clamp": {
        "label": "Clamped Power Scale",
        "preset_labels": {
            "GENTLE_CLAMP": "Gentle Clamp",
            "HARD_FLOOR": "Hard Floor",
            "WIDE_RANGE": "Wide Range",
        },
        "preset_descriptions": {
            "GENTLE_CLAMP": "Default falloff with a modest min/max.",
            "HARD_FLOOR": "Steep falloff, never below 0.25.",
            "WIDE_RANGE": "Shallow falloff, wide allowed scale.",
        },
        "presets": {
            "GENTLE_CLAMP": {
                "Base Scale": 1.0, "Power": 0.8, "Min": 0.05, "Max": 10.0,
            },
            "HARD_FLOOR": {
                "Base Scale": 1.2, "Power": 1.6, "Min": 0.25, "Max": 4.0,
            },
            "WIDE_RANGE": {
                "Base Scale": 0.8, "Power": 0.35, "Min": 0.1, "Max": 24.0,
            },
        },
    },

    "MEL_greybox_room_kit": {
        "label": "Greybox Room Kit",
        "preset_labels": {
            "SMALL_CELL": "Small Cell",
            "HALL": "Hall",
            "CLOISTER_WALK": "Cloister Walk",
            "SEA_ABOVE_REVEAL_GALLERY": "Sea Above Reveal Gallery",
            "BELL_ANATOMY_CHAMBER": "Bell Anatomy Chamber",
            "FALSE_HORIZON_OBSERVATORY": "False Horizon Observatory",
        },
        "preset_descriptions": {
            "SMALL_CELL": "Tight 4x4 cell with a ceiling.",
            "HALL": "Long assembly hall, high ceiling.",
            "CLOISTER_WALK": "Wide cloister bay with thinner walls.",
            "SEA_ABOVE_REVEAL_GALLERY": "Cinematic 16:9 approach gallery with a broad false-horizon reveal volume.",
            "BELL_ANATOMY_CHAMBER": "Monumental chamber sized for membrane ribs and low-frequency anatomy studies.",
            "FALSE_HORIZON_OBSERVATORY": "Open-ceiling review room for fixed-camera Sea Above composition.",
        },
        "presets": {
            "SMALL_CELL": {
                "Room Length": 4.0, "Room Width": 4.0, "Room Height": 3.0,
                "Wall Thickness": 0.25, "Ceiling": True,
            },
            "HALL": {
                "Room Length": 14.0, "Room Width": 7.0, "Room Height": 5.5,
                "Wall Thickness": 0.35, "Ceiling": True,
            },
            "CLOISTER_WALK": {
                "Room Length": 10.0, "Room Width": 4.5, "Room Height": 3.6,
                "Wall Thickness": 0.2, "Ceiling": True,
            },
            "SEA_ABOVE_REVEAL_GALLERY": {"Room Length": 30.0, "Room Width": 12.0, "Room Height": 9.0, "Wall Thickness": 0.45, "Ceiling": True, "Music Influence": 0.035, "Musical Amplitude": 1.5, "Musical Freq A": 1.0, "Musical Freq B": 3.0},
            "BELL_ANATOMY_CHAMBER": {"Room Length": 26.0, "Room Width": 26.0, "Room Height": 15.0, "Wall Thickness": 0.65, "Ceiling": True, "Music Influence": 0.06, "Musical Amplitude": 2.2, "Musical Freq A": 0.75, "Musical Freq B": 5.0},
            "FALSE_HORIZON_OBSERVATORY": {"Room Length": 22.0, "Room Width": 16.0, "Room Height": 11.0, "Wall Thickness": 0.4, "Ceiling": False, "Music Influence": 0.025, "Musical Amplitude": 1.2, "Musical Freq A": 2.0, "Musical Freq B": 4.0},
        },
    },
    "MEL_greybox_openings": {
        "label": "Greybox Openings",
        "preset_labels": {
            "SMALL_CELL": "Small Cell",
            "HALL": "Hall",
            "CLOISTER_WALK": "Cloister Walk",
        },
        "preset_descriptions": {
            "SMALL_CELL": "Single door, no window.",
            "HALL": "Door plus a high window.",
            "CLOISTER_WALK": "Open arcade-like window, no door.",
        },
        "presets": {
            "SMALL_CELL": {
                "Cut Door": True, "Cut Window": False,
                "Door Width": 0.85, "Door Height": 2.1, "Door X": 0.0,
                "Window Width": 1.0, "Window Height": 0.8, "Window X": 1.2,
                "Window Sill": 1.1, "Cut Depth": 12.0,
            },
            "HALL": {
                "Cut Door": True, "Cut Window": True,
                "Door Width": 1.2, "Door Height": 2.4, "Door X": -1.5,
                "Window Width": 1.6, "Window Height": 1.2, "Window X": 1.8,
                "Window Sill": 1.4, "Cut Depth": 16.0,
            },
            "CLOISTER_WALK": {
                "Cut Door": False, "Cut Window": True,
                "Door Width": 0.9, "Door Height": 2.1, "Door X": 0.0,
                "Window Width": 2.2, "Window Height": 1.8, "Window X": 0.0,
                "Window Sill": 0.8, "Cut Depth": 12.0,
            },
        },
    },
    "MEL_greybox_corridor": {
        "label": "Greybox Corridor",
        "preset_labels": {
            "SMALL_CELL": "Small Cell",
            "HALL": "Hall",
            "CLOISTER_WALK": "Cloister Walk",
        },
        "preset_descriptions": {
            "SMALL_CELL": "Short capped connector.",
            "HALL": "Long open hall.",
            "CLOISTER_WALK": "Wide cloister run, open ends.",
        },
        "presets": {
            "SMALL_CELL": {
                "Length": 4.0, "Width": 2.0, "Height": 2.8,
                "Wall Thickness": 0.22, "End Cap": True,
            },
            "HALL": {
                "Length": 16.0, "Width": 3.2, "Height": 4.5,
                "Wall Thickness": 0.3, "End Cap": False,
            },
            "CLOISTER_WALK": {
                "Length": 12.0, "Width": 3.6, "Height": 3.4,
                "Wall Thickness": 0.18, "End Cap": False,
            },
        },
    },
    "MEL_greybox_junction": {
        "label": "Greybox Junction",
        "preset_labels": {
            "SMALL_CELL": "Small Cell T",
            "HALL": "Hall Cross",
            "CLOISTER_WALK": "Cloister T",
        },
        "preset_descriptions": {
            "SMALL_CELL": "Compact T join.",
            "HALL": "Wide X crossing.",
            "CLOISTER_WALK": "Open T for cloister corners.",
        },
        "presets": {
            "SMALL_CELL": {
                "Size": 4.0, "Width": 2.0, "Height": 2.8,
                "Wall Thickness": 0.22, "Cross Junction": False,
            },
            "HALL": {
                "Size": 8.0, "Width": 3.2, "Height": 4.5,
                "Wall Thickness": 0.3, "Cross Junction": True,
            },
            "CLOISTER_WALK": {
                "Size": 6.0, "Width": 3.6, "Height": 3.4,
                "Wall Thickness": 0.18, "Cross Junction": False,
            },
        },
    },
    "MEL_church_bell": {
        "label": "Church Bell",
        "preset_labels": {
            "CHAPEL_BELL": "Chapel Bell",
            "CATHEDRAL_BOURDON": "Cathedral Bourdon",
            "HAND_BELL": "Hand Bell",
        },
        "preset_descriptions": {
            "CHAPEL_BELL": "Medium chapel bell with traditional crown and clapper.",
            "CATHEDRAL_BOURDON": "Large bourdon bell, wide mouth and slow swing.",
            "HAND_BELL": "Small hand bell, narrow crown, fast clapper.",
        },
        "presets": {
            "CHAPEL_BELL": {
                "Height": 0.6, "Mouth Radius": 0.25, "Wall Thickness": 0.012,
                "Crown Width": 0.08, "Has Clapper": True, "Clapper Swing": 5.0, "Pitch": 220.0,
            },
            "CATHEDRAL_BOURDON": {
                "Height": 1.4, "Mouth Radius": 0.72, "Wall Thickness": 0.032,
                "Crown Width": 0.18, "Has Clapper": True, "Clapper Swing": 12.0, "Pitch": 65.0,
            },
            "HAND_BELL": {
                "Height": 0.32, "Mouth Radius": 0.14, "Wall Thickness": 0.007,
                "Crown Width": 0.045, "Has Clapper": True, "Clapper Swing": 18.0, "Pitch": 440.0,
            },
        },
    },
    "MEL_bell_chime": {
        "label": "Bell/Chime",
        "preset_labels": {
            "CHIME_TUBE": "Chime Tube",
            "CUP_BELL": "Cup Bell",
            "SPHERE_BELL": "Sphere Bell",
        },
        "preset_descriptions": {
            "CHIME_TUBE": "Long tubular chime (22.4% node, shimmer bands).",
            "CUP_BELL": "Inverted cup bell with clapper.",
            "SPHERE_BELL": "Spherical bell with high partial count.",
        },
        "presets": {
            "CHIME_TUBE": {
                "Bell Type": 2, "Diameter": 0.32, "Depth": 1.8, "Wall Thickness": 0.04,
                "Partial Count": 10, "Has Clapper": False, "Clapper Mass": 0.4,
            },
            "CUP_BELL": {
                "Bell Type": 1, "Diameter": 0.42, "Depth": 0.55, "Wall Thickness": 0.06,
                "Partial Count": 8, "Has Clapper": True, "Clapper Mass": 0.5,
            },
            "SPHERE_BELL": {
                "Bell Type": 0, "Diameter": 0.38, "Depth": 0.42, "Wall Thickness": 0.05,
                "Partial Count": 12, "Has Clapper": True, "Clapper Mass": 0.7,
            },
        },
    },
    "MEL_singing_bowl": {
        "label": "Singing Bowl",
        "preset_labels": {
            "TEMPLE_BOWL": "Temple Bowl",
            "DEEP_BOWL": "Deep Bowl",
            "SHALLOW_BOWL": "Shallow Bowl",
        },
        "preset_descriptions": {
            "TEMPLE_BOWL": "Balanced temple bowl with clear strike point.",
            "DEEP_BOWL": "Deep resonating bowl, thick wall.",
            "SHALLOW_BOWL": "Shallow bowl, thin wall, bright overtones.",
        },
        "presets": {
            "TEMPLE_BOWL": {
                "Radius": 0.16, "Wall Thickness": 0.005, "Depth": 0.09, "Rim Width": 0.02,
                "Strike Point": 0.25, "Pitch": 256.0,
            },
            "DEEP_BOWL": {
                "Radius": 0.22, "Wall Thickness": 0.008, "Depth": 0.14, "Rim Width": 0.03,
                "Strike Point": 0.5, "Pitch": 128.0,
            },
            "SHALLOW_BOWL": {
                "Radius": 0.12, "Wall Thickness": 0.003, "Depth": 0.05, "Rim Width": 0.015,
                "Strike Point": 0.75, "Pitch": 512.0,
            },
        },
    },
    "MEL_tuning_fork": {
        "label": "Tuning Fork",
        "preset_labels": {
            "A440_FORK": "A440 Fork",
            "LOW_C_FORK": "Low C Fork",
            "HIGH_E_FORK": "High E Fork",
        },
        "preset_descriptions": {
            "A440_FORK": "Standard A440 fork with resonance box.",
            "LOW_C_FORK": "Long low C fork, wide gap.",
            "HIGH_E_FORK": "Short high E fork, narrow gap.",
        },
        "presets": {
            "A440_FORK": {
                "Tine Length": 0.35, "Tine Radius": 0.008, "Tine Gap": 0.04,
                "Handle Length": 0.25, "Handle Radius": 0.012, "Box Width": 0.08,
                "Box Height": 0.06, "Box Depth": 0.04, "Pitch": 440.0,
            },
            "LOW_C_FORK": {
                "Tine Length": 0.52, "Tine Radius": 0.011, "Tine Gap": 0.06,
                "Handle Length": 0.32, "Handle Radius": 0.014, "Box Width": 0.1,
                "Box Height": 0.07, "Box Depth": 0.05, "Pitch": 130.81,
            },
            "HIGH_E_FORK": {
                "Tine Length": 0.22, "Tine Radius": 0.006, "Tine Gap": 0.03,
                "Handle Length": 0.18, "Handle Radius": 0.009, "Box Width": 0.06,
                "Box Height": 0.045, "Box Depth": 0.03, "Pitch": 659.25,
            },
        },
    },
    "MEL_music_harmonograph": {
        "label": "Harmonograph Tracery",
        "preset_labels": {
            "OCTAVE_SPIRAL": "Octave 2:1 Spiral",
            "FIFTH_BLOOM": "Fifth 3:2 Bloom",
            "FOURTH_WEAVE": "Fourth 4:3 Weave",
        },
        "preset_descriptions": {
            "OCTAVE_SPIRAL": "2:1 octave ratio, classic damped spiral.",
            "FIFTH_BLOOM": "3:2 fifth ratio, slow phase bloom.",
            "FOURTH_WEAVE": "4:3 fourth ratio, tight lissajous weave.",
        },
        "presets": {
            "OCTAVE_SPIRAL": {
                "Turns": 3.0, "Frequency A": 2.0, "Frequency B": 1.0, "Phase": 0.0,
                "Damping": 0.35, "Amplitude": 1.2, "Resolution": 400, "Thickness": 0.02, "Scale": 1.0,
            },
            "FIFTH_BLOOM": {
                "Turns": 4.5, "Frequency A": 3.0, "Frequency B": 2.0, "Phase": 0.785,
                "Damping": 0.28, "Amplitude": 1.4, "Resolution": 560, "Thickness": 0.018, "Scale": 1.1,
            },
            "FOURTH_WEAVE": {
                "Turns": 5.0, "Frequency A": 4.0, "Frequency B": 3.0, "Phase": 1.57,
                "Damping": 0.42, "Amplitude": 1.0, "Resolution": 640, "Thickness": 0.016, "Scale": 0.95,
            },
        },
    },
    "MEL_music_bass_clef": {
        "label": "Bass Clef",
        "preset_labels": {
            "STANDARD_BASS": "Standard Bass",
            "WIDE_BASS": "Wide Bass",
            "TIGHT_CURL": "Tight Curl",
        },
        "preset_descriptions": {
            "STANDARD_BASS": "Classic F-clef curl with two dots.",
            "WIDE_BASS": "Broader curl for display sizes.",
            "TIGHT_CURL": "Compact curl for small staves.",
        },
        "presets": {
            "STANDARD_BASS": {
                "Scale": 1.0, "Thickness": 0.018, "Curl Depth": 0.5, "Dot Size": 0.06, "Tail Length": 0.42,
            },
            "WIDE_BASS": {
                "Scale": 1.3, "Thickness": 0.022, "Curl Depth": 0.62, "Dot Size": 0.075, "Tail Length": 0.52,
            },
            "TIGHT_CURL": {
                "Scale": 0.75, "Thickness": 0.014, "Curl Depth": 0.38, "Dot Size": 0.045, "Tail Length": 0.32,
            },
        },
    },
    "MEL_music_waveform_wall": {
        "label": "Waveform Wall",
        "preset_labels": {
            "SAW_WALL": "Saw Wall",
            "SQUARE_WALL": "Square Wall",
            "TRI_WALL": "Triangle Wall",
        },
        "preset_descriptions": {
            "SAW_WALL": "Sawtooth additive 1/n wall.",
            "SQUARE_WALL": "Square odd-harmonic wall.",
            "TRI_WALL": "Triangle 1/n^2 soft wall.",
        },
        "presets": {
            "SAW_WALL": {
                "Width": 4.0, "Amplitude": 0.8, "Base Freq": 1.0, "Harmonic Blend": 0.55,
                "Resolution": 128, "Thickness": 0.02, "Scale": 1.0,
            },
            "SQUARE_WALL": {
                "Width": 4.0, "Amplitude": 0.65, "Base Freq": 1.2, "Harmonic Blend": 0.42,
                "Resolution": 128, "Thickness": 0.018, "Scale": 1.0,
            },
            "TRI_WALL": {
                "Width": 4.0, "Amplitude": 0.5, "Base Freq": 0.8, "Harmonic Blend": 0.35,
                "Resolution": 128, "Thickness": 0.016, "Scale": 1.0,
            },
        },
    },
    "MEL_music_vinyl_disc": {
        "label": "Vinyl Disc",
        "preset_labels": {
            "LP_33": "33 RPM LP",
            "SINGLE_45": "45 Single",
            "ETCHED_B_SIDE": "Etched B-Side",
        },
        "preset_descriptions": {
            "LP_33": "Standard 12-inch 33 RPM with constant-pitch grooves.",
            "SINGLE_45": "7-inch 45 RPM, fewer grooves.",
            "ETCHED_B_SIDE": "Etched disc with sparse grooves and large label.",
        },
        "presets": {
            "LP_33": {
                "Radius": 0.15, "Thickness": 0.008, "Grooves": 42, "Has Label": True, "Spindle Hole": True, "Scale": 1.0,
            },
            "SINGLE_45": {
                "Radius": 0.09, "Thickness": 0.007, "Grooves": 28, "Has Label": True, "Spindle Hole": True, "Scale": 1.0,
            },
            "ETCHED_B_SIDE": {
                "Radius": 0.15, "Thickness": 0.009, "Grooves": 12, "Has Label": False, "Spindle Hole": True, "Scale": 1.0,
            },
        },
    },
    "MEL_music_lissajous_harp": {
        "label": "Lissajous Harp",
        "preset_labels": {
            "CONCERT_HARP": "Concert Harp",
            "SMALL_HARP": "Small Harp",
            "WIDE_HARP": "Wide Harp",
        },
        "preset_descriptions": {
            "CONCERT_HARP": "Full concert harp with lissajous string web.",
            "SMALL_HARP": "Compact lap harp.",
            "WIDE_HARP": "Broad orchestral harp, thick strings.",
        },
        "presets": {
            "CONCERT_HARP": {
                "Height": 1.6, "Width": 0.9, "Thickness": 0.04, "String Gauge": 0.004, "Scale": 1.0,
            },
            "SMALL_HARP": {
                "Height": 0.9, "Width": 0.5, "Thickness": 0.03, "String Gauge": 0.003, "Scale": 1.0,
            },
            "WIDE_HARP": {
                "Height": 1.8, "Width": 1.2, "Thickness": 0.05, "String Gauge": 0.005, "Scale": 1.0,
            },
        },
    },
    "MEL_music_frequency_ribcage": {
        "label": "Frequency Ribcage",
        "preset_labels": {
            "RIBCAGE_STANDARD": "Standard Ribcage",
            "TALL_RIBCAGE": "Tall Ribcage",
            "WIDE_RIBCAGE": "Wide Ribcage",
        },
        "preset_descriptions": {
            "RIBCAGE_STANDARD": "Harmonic rib tiers in 1/k decay.",
            "TALL_RIBCAGE": "High vaulted ribcage.",
            "WIDE_RIBCAGE": "Broad low ribcage.",
        },
        "presets": {
            "RIBCAGE_STANDARD": {
                "Span": 3.0, "Max Height": 2.2, "Rib Count": 7, "Spacing": 0.42, "Thickness": 0.04, "Scale": 1.0,
            },
            "TALL_RIBCAGE": {
                "Span": 3.2, "Max Height": 3.5, "Rib Count": 9, "Spacing": 0.38, "Thickness": 0.045, "Scale": 1.0,
            },
            "WIDE_RIBCAGE": {
                "Span": 5.0, "Max Height": 1.6, "Rib Count": 6, "Spacing": 0.62, "Thickness": 0.035, "Scale": 1.0,
            },
        },
    },
    "MEL_music_beam_cluster": {
        "label": "Beam Cluster",
        "preset_labels": {
            "BEAM_4": "Four-Beam Cluster",
            "BEAM_8_DENSE": "Eight Dense Beam",
            "BEAM_SLANT": "Slanted Beam",
        },
        "preset_descriptions": {
            "BEAM_4": "Standard 4-note beamed cluster.",
            "BEAM_8_DENSE": "Dense 8-note fast passage beaming.",
            "BEAM_SLANT": "Slanted beam with wide spacing.",
        },
        "presets": {
            "BEAM_4": {
                "Note Count": 4, "Spacing": 0.28, "Stem Length": 0.85, "Beam Thickness": 0.04, "Slant": 0.0, "Note Size": 0.38,
            },
            "BEAM_8_DENSE": {
                "Note Count": 8, "Spacing": 0.18, "Stem Length": 0.9, "Beam Thickness": 0.035, "Slant": 0.08, "Note Size": 0.34,
            },
            "BEAM_SLANT": {
                "Note Count": 4, "Spacing": 0.35, "Stem Length": 1.1, "Beam Thickness": 0.045, "Slant": 0.22, "Note Size": 0.42,
            },
        },
    },
    "MEL_music_chord_stack": {
        "label": "Chord Stack",
        "preset_labels": {
            "TRIAD_STACK": "Triad Stack",
            "SEVENTH_STACK": "Seventh Stack",
            "SPREAD_CHORD": "Spread Chord",
        },
        "preset_descriptions": {
            "TRIAD_STACK": "Three-note triad vertical stack.",
            "SEVENTH_STACK": "Four-note seventh chord.",
            "SPREAD_CHORD": "Wide spread voicing.",
        },
        "presets": {
            "TRIAD_STACK": {
                "Chord Size": 3, "Spread": 0.14, "Note Size": 0.4, "Stem Length": 0.9, "Stem Offset": 0.0, "Scale": 1.0,
            },
            "SEVENTH_STACK": {
                "Chord Size": 4, "Spread": 0.16, "Note Size": 0.38, "Stem Length": 1.0, "Stem Offset": 0.02, "Scale": 1.0,
            },
            "SPREAD_CHORD": {
                "Chord Size": 3, "Spread": 0.28, "Note Size": 0.42, "Stem Length": 1.2, "Stem Offset": 0.05, "Scale": 1.15,
            },
        },
    },
    "MEL_music_fermata": {
        "label": "Fermata",
        "preset_labels": {
            "FERMATA_ARC": "Arc Fermata",
            "FERMATA_DEEP": "Deep Fermata",
            "FERMATA_DOT": "Dotted Fermata",
        },
        "preset_descriptions": {
            "FERMATA_ARC": "Standard arc fermata over dot.",
            "FERMATA_DEEP": "Deep curve fermata for large pauses.",
            "FERMATA_DOT": "Dot-heavy fermata variant.",
        },
        "presets": {
            "FERMATA_ARC": {
                "Scale": 1.0, "Radius": 0.22, "Arc Height": 0.12, "Thickness": 0.018, "Dot Size": 0.04, "Has Dot": True,
            },
            "FERMATA_DEEP": {
                "Scale": 1.2, "Radius": 0.28, "Arc Height": 0.18, "Thickness": 0.022, "Dot Size": 0.05, "Has Dot": True,
            },
            "FERMATA_DOT": {
                "Scale": 1.0, "Radius": 0.2, "Arc Height": 0.1, "Thickness": 0.016, "Dot Size": 0.06, "Has Dot": True,
            },
        },
    },
    "MEL_music_repeat_bar": {
        "label": "Repeat Bar",
        "preset_labels": {
            "REPEAT_STANDARD": "Standard Repeat",
            "REPEAT_WIDE": "Wide Repeat",
            "REPEAT_COMPACT": "Compact Repeat",
        },
        "preset_descriptions": {
            "REPEAT_STANDARD": "Standard repeat bar with dots.",
            "REPEAT_WIDE": "Wide repeat bar for large staves.",
            "REPEAT_COMPACT": "Compact repeat for small notation.",
        },
        "presets": {
            "REPEAT_STANDARD": {
                "Scale": 1.0, "Height": 0.8, "Bar Thickness": 0.03, "Gap": 0.08, "Dot Size": 0.04,
            },
            "REPEAT_WIDE": {
                "Scale": 1.25, "Height": 1.0, "Bar Thickness": 0.04, "Gap": 0.1, "Dot Size": 0.05,
            },
            "REPEAT_COMPACT": {
                "Scale": 0.75, "Height": 0.55, "Bar Thickness": 0.022, "Gap": 0.06, "Dot Size": 0.03,
            },
        },
    },
    "MEL_music_soundhole_rosette": {
        "label": "Soundhole Rosette",
        "preset_labels": {
            "ROSETTE_CLASSIC": "Classic Rosette",
            "ROSETTE_MODERN": "Modern Rosette",
            "ROSETTE_MINIMAL": "Minimal Rosette",
        },
        "preset_descriptions": {
            "ROSETTE_CLASSIC": "Classic concentric ring rosette.",
            "ROSETTE_MODERN": "Modern offset ring rosette.",
            "ROSETTE_MINIMAL": "Minimal single-ring rosette.",
        },
        "presets": {
            "ROSETTE_CLASSIC": {
                "Outer Radius": 0.055, "Ring Thickness": 0.006, "Marker Count": 12, "Depth": 0.008, "Scale": 1.0,
            },
            "ROSETTE_MODERN": {
                "Outer Radius": 0.065, "Ring Thickness": 0.008, "Marker Count": 16, "Depth": 0.01, "Scale": 1.1,
            },
            "ROSETTE_MINIMAL": {
                "Outer Radius": 0.045, "Ring Thickness": 0.004, "Marker Count": 8, "Depth": 0.005, "Scale": 0.85,
            },
        },
    },
    "MEL_music_stand": {
        "label": "Music Stand",
        "preset_labels": {
            "STAND_ORCHESTRAL": "Orchestral Stand",
            "STAND_CHAMBER": "Chamber Stand",
            "STAND_PRACTICE": "Practice Stand",
        },
        "preset_descriptions": {
            "STAND_ORCHESTRAL": "Full orchestral stand with wide panel.",
            "STAND_CHAMBER": "Chamber stand, narrower panel.",
            "STAND_PRACTICE": "Compact practice stand.",
        },
        "presets": {
            "STAND_ORCHESTRAL": {
                "Panel Width": 0.55, "Panel Height": 0.38, "Panel Thickness": 0.012, "Stand Height": 1.1, "Lean": 12.0, "Leg Spread": 0.35, "Scale": 1.0,
            },
            "STAND_CHAMBER": {
                "Panel Width": 0.42, "Panel Height": 0.32, "Panel Thickness": 0.01, "Stand Height": 0.95, "Lean": 10.0, "Leg Spread": 0.28, "Scale": 1.0,
            },
            "STAND_PRACTICE": {
                "Panel Width": 0.32, "Panel Height": 0.26, "Panel Thickness": 0.008, "Stand Height": 0.85, "Lean": 8.0, "Leg Spread": 0.22, "Scale": 0.9,
            },
        },
    },
    "MEL_music_time_signature": {
        "label": "Time Signature",
        "preset_labels": {
            "TIME_4_4": "4/4 Common",
            "TIME_3_4": "3/4 Waltz",
            "TIME_6_8": "6/8 Compound",
        },
        "preset_descriptions": {
            "TIME_4_4": "Standard 4/4 common time.",
            "TIME_3_4": "Waltz 3/4 time.",
            "TIME_6_8": "Compound 6/8 time.",
        },
        "presets": {
            "TIME_4_4": {
                "Radius": 0.08, "Thickness": 0.012, "Beats": 4, "Cut Time": False, "Resolution": 16,
            },
            "TIME_3_4": {
                "Radius": 0.07, "Thickness": 0.011, "Beats": 3, "Cut Time": False, "Resolution": 14,
            },
            "TIME_6_8": {
                "Radius": 0.09, "Thickness": 0.013, "Beats": 6, "Cut Time": False, "Resolution": 18,
            },
        },
    },
    "MEL_music_triplet_note": {
        "label": "Triplet Note",
        "preset_labels": {
            "TRIPLET_3": "Three-Note Triplet",
            "TRIPLET_DENSE": "Dense Triplet",
            "TRIPLET_WIDE": "Wide Triplet",
        },
        "preset_descriptions": {
            "TRIPLET_3": "Standard 3-note triplet with bracket.",
            "TRIPLET_DENSE": "Dense triplet with tight spacing.",
            "TRIPLET_WIDE": "Wide spaced triplet.",
        },
        "presets": {
            "TRIPLET_3": {
                "Spacing": 0.28, "Stem Length": 0.85, "Beam Thickness": 0.04, "Slant": 0.0, "Note Size": 0.38, "Double Beam": False,
            },
            "TRIPLET_DENSE": {
                "Spacing": 0.2, "Stem Length": 0.8, "Beam Thickness": 0.035, "Slant": 0.05, "Note Size": 0.34, "Double Beam": True,
            },
            "TRIPLET_WIDE": {
                "Spacing": 0.36, "Stem Length": 0.95, "Beam Thickness": 0.045, "Slant": 0.0, "Note Size": 0.42, "Double Beam": False,
            },
        },
    },
    "MEL_music_tuning_fork": {
        "label": "Tuning Fork (Musical)",
        "preset_labels": {
            "FORK_A440": "A440 Fork",
            "FORK_C256": "C256 Fork",
            "FORK_HIGH": "High Fork",
        },
        "preset_descriptions": {
            "FORK_A440": "Standard A440 musical tuning fork.",
            "FORK_C256": "Low C256 fork.",
            "FORK_HIGH": "High overtone fork.",
        },
        "presets": {
            "FORK_A440": {
                "Total Height": 0.35, "Fork Width": 0.04, "Thickness": 0.008, "Prong Split": 0.5, "Scale": 1.0,
            },
            "FORK_C256": {
                "Total Height": 0.42, "Fork Width": 0.05, "Thickness": 0.01, "Prong Split": 0.55, "Scale": 1.1,
            },
            "FORK_HIGH": {
                "Total Height": 0.28, "Fork Width": 0.032, "Thickness": 0.006, "Prong Split": 0.45, "Scale": 0.85,
            },
        },
    },
    "MEL_music_metronome_pillar": {
        "label": "Metronome Pillar",
        "preset_labels": {
            "METRONOME_CLASSIC": "Classic Metronome",
            "METRONOME_TALL": "Tall Pillar",
            "METRONOME_COMPACT": "Compact Metronome",
        },
        "preset_descriptions": {
            "METRONOME_CLASSIC": "Classic pillar metronome with swinging pendulum.",
            "METRONOME_TALL": "Tall obelisk metronome.",
            "METRONOME_COMPACT": "Compact practice metronome.",
        },
        "presets": {
            "METRONOME_CLASSIC": {
                "Body Height": 1.8, "Base Width": 0.42, "Pendulum Angle": 18.0, "Show Pendulum": True, "Scale": 1.0,
            },
            "METRONOME_TALL": {
                "Body Height": 2.6, "Base Width": 0.5, "Pendulum Angle": 22.0, "Show Pendulum": True, "Scale": 1.1,
            },
            "METRONOME_COMPACT": {
                "Body Height": 1.2, "Base Width": 0.32, "Pendulum Angle": 15.0, "Show Pendulum": False, "Scale": 0.85,
            },
        },
    },
    "MEL_music_phrase": {
        "label": "Music Phrase",
        "preset_labels": {
            "PHRASE_4BAR": "4-Bar Phrase",
            "PHRASE_8BAR": "8-Bar Phrase",
            "PHRASE_SHORT": "Short Motif",
        },
        "preset_descriptions": {
            "PHRASE_4BAR": "Standard 4-bar phrase with staff and notes.",
            "PHRASE_8BAR": "Extended 8-bar phrase.",
            "PHRASE_SHORT": "Short 2-bar motif.",
        },
        "presets": {
            "PHRASE_4BAR": {
                "Length": 4.0, "Note Count": 16, "Staff Scale": 1.0, "Note Size": 1.0, "Show Clef": True,
            },
            "PHRASE_8BAR": {
                "Length": 8.0, "Note Count": 32, "Staff Scale": 1.2, "Note Size": 0.95, "Show Clef": True,
            },
            "PHRASE_SHORT": {
                "Length": 2.0, "Note Count": 8, "Staff Scale": 0.85, "Note Size": 1.1, "Show Clef": False,
            },
        },
    },

    "MEL_music_celesta": {
        "label": "Music Celesta",
        "preset_labels": {
            "CELESTA_8": "8-Plate Celesta",
            "CELESTA_12": "12-Plate Celesta",
            "CELESTA_5": "5-Plate Mini",
        },
        "preset_descriptions": {
            "CELESTA_8": "Standard 8 plates ET from A4, longest 0.42m.",
            "CELESTA_12": "12 plates, wider resonator.",
            "CELESTA_5": "Mini 5 plates, compact box.",
        },
        "presets": {
            "CELESTA_8": {
                "Plate Count": 8, "Longest Plate (m)": 0.42, "Plate Width": 0.042, "Plate Thickness": 0.012,
                "Spacing": 0.06, "Box Height": 0.28, "Root Semitone": 9, "Mode Steps": 7, "Scale": 1.0,
            },
            "CELESTA_12": {
                "Plate Count": 12, "Longest Plate (m)": 0.48, "Plate Width": 0.038, "Plate Thickness": 0.01,
                "Spacing": 0.055, "Box Height": 0.32, "Root Semitone": 9, "Mode Steps": 7, "Scale": 1.0,
            },
            "CELESTA_5": {
                "Plate Count": 5, "Longest Plate (m)": 0.32, "Plate Width": 0.045, "Plate Thickness": 0.014,
                "Spacing": 0.07, "Box Height": 0.22, "Root Semitone": 9, "Mode Steps": 5, "Scale": 1.0,
            },
        },
    },
    "MEL_music_glockenspiel": {
        "label": "Music Glockenspiel",
        "preset_labels": {
            "GLOCK_8": "8-Bar Glock",
            "GLOCK_12": "12-Bar Glock",
            "GLOCK_5": "5-Bar Mini",
        },
        "preset_descriptions": {
            "GLOCK_8": "GN twin of chime row, 8 plates.",
            "GLOCK_12": "12 plates, long frame.",
            "GLOCK_5": "5 plates mini.",
        },
        "presets": {
            "GLOCK_8": {
                "Plate Count": 8, "Longest Plate (m)": 0.32, "Plate Width": 0.038, "Plate Thickness": 0.009,
                "Gap": 0.052, "Support Height": 0.18, "Scale": 1.0,
            },
            "GLOCK_12": {
                "Plate Count": 12, "Longest Plate (m)": 0.36, "Plate Width": 0.034, "Plate Thickness": 0.008,
                "Gap": 0.048, "Support Height": 0.2, "Scale": 1.0,
            },
            "GLOCK_5": {
                "Plate Count": 5, "Longest Plate (m)": 0.26, "Plate Width": 0.042, "Plate Thickness": 0.011,
                "Gap": 0.06, "Support Height": 0.15, "Scale": 1.0,
            },
        },
    },
    "MEL_music_kalimba": {
        "label": "Music Kalimba",
        "preset_labels": {
            "KALIMBA_10": "10-Tine Kalimba",
            "KALIMBA_15": "15-Tine Kalimba",
            "KALIMBA_7": "7-Tine Mini",
        },
        "preset_descriptions": {
            "KALIMBA_10": "Standard 10 tines Mersenne.",
            "KALIMBA_15": "15 tines, wide box.",
            "KALIMBA_7": "7 tines mini.",
        },
        "presets": {
            "KALIMBA_10": {
                "Tine Count": 10, "Longest Tine (m)": 0.095, "Tine Width": 0.012, "Tine Thickness": 0.003,
                "Spacing": 0.018, "Box Width": 0.14, "Box Depth": 0.18, "Box Height": 0.04, "Scale": 1.0,
            },
            "KALIMBA_15": {
                "Tine Count": 15, "Longest Tine (m)": 0.11, "Tine Width": 0.01, "Tine Thickness": 0.0025,
                "Spacing": 0.015, "Box Width": 0.18, "Box Depth": 0.22, "Box Height": 0.045, "Scale": 1.0,
            },
            "KALIMBA_7": {
                "Tine Count": 7, "Longest Tine (m)": 0.08, "Tine Width": 0.014, "Tine Thickness": 0.0035,
                "Spacing": 0.02, "Box Width": 0.12, "Box Depth": 0.15, "Box Height": 0.035, "Scale": 1.0,
            },
        },
    },
    "MEL_music_harp_v2": {
        "label": "Music Harp v2",
        "preset_labels": {
            "HARP_V2_STANDARD": "Standard Parabolic Harp",
            "HARP_V2_TALL": "Tall Harp",
            "HARP_V2_WIDE": "Wide Harp",
        },
        "preset_descriptions": {
            "HARP_V2_STANDARD": "Parabolic board, 32 strings Mersenne.",
            "HARP_V2_TALL": "Tall board, 48 strings.",
            "HARP_V2_WIDE": "Wide board, 24 strings.",
        },
        "presets": {
            "HARP_V2_STANDARD": {
                "Height": 1.8, "Depth": 0.62, "Soundboard Width": 0.44, "String Count": 32, "String Radius": 0.003, "Curvature": 0.22, "Scale": 1.0,
            },
            "HARP_V2_TALL": {
                "Height": 2.4, "Depth": 0.75, "Soundboard Width": 0.5, "String Count": 48, "String Radius": 0.0025, "Curvature": 0.28, "Scale": 1.0,
            },
            "HARP_V2_WIDE": {
                "Height": 1.6, "Depth": 0.85, "Soundboard Width": 0.62, "String Count": 24, "String Radius": 0.004, "Curvature": 0.18, "Scale": 1.0,
            },
        },
    },
    "MEL_music_waveform_wall_v2": {
        "label": "Waveform Wall v2",
        "preset_labels": {
            "WAVEFORM_SAW_V2": "Saw V2",
            "WAVEFORM_SQUARE_V2": "Square V2",
            "WAVEFORM_TRI_V2": "Tri V2",
        },
        "preset_descriptions": {
            "WAVEFORM_SAW_V2": "Saw 1/n with correct 1/n^k.",
            "WAVEFORM_SQUARE_V2": "Square odd 1/n.",
            "WAVEFORM_TRI_V2": "Triangle 1/n^2.",
        },
        "presets": {
            "WAVEFORM_SAW_V2": {
                "Width": 4.0, "Amplitude": 0.6, "Base Freq": 1.0, "Harmonics": 5, "Falloff Exp": 1.0, "Resolution": 128, "Thickness": 0.02, "Scale": 1.0,
            },
            "WAVEFORM_SQUARE_V2": {
                "Width": 4.0, "Amplitude": 0.6, "Base Freq": 1.2, "Harmonics": 5, "Falloff Exp": 1.0, "Resolution": 128, "Thickness": 0.02, "Scale": 1.0,
            },
            "WAVEFORM_TRI_V2": {
                "Width": 4.0, "Amplitude": 0.5, "Base Freq": 1.0, "Harmonics": 5, "Falloff Exp": 2.0, "Resolution": 128, "Thickness": 0.02, "Scale": 1.0,
            },
        },
    },

    "MEL_music_jingle_tower": {
        "label": "Music Jingle Tower",
        "preset_labels": {
            "TOWER_12": "12-Note Tower",
            "TOWER_8": "8-Note Tower",
            "TOWER_16": "16-Note Tower",
        },
        "preset_descriptions": {
            "TOWER_12": "12 floors from 12-note jingle, 0.35m per floor.",
            "TOWER_8": "8 floors, compact.",
            "TOWER_16": "16 floors, tall.",
        },
        "presets": {
            "TOWER_12": {
                "Note Count": 12, "Floor Height": 0.35, "Radius": 1.2, "Wall Thick": 0.12, "Segments": 16, "Scale": 1.0,
            },
            "TOWER_8": {
                "Note Count": 8, "Floor Height": 0.4, "Radius": 1.0, "Wall Thick": 0.1, "Segments": 12, "Scale": 1.0,
            },
            "TOWER_16": {
                "Note Count": 16, "Floor Height": 0.32, "Radius": 1.5, "Wall Thick": 0.14, "Segments": 20, "Scale": 1.0,
            },
        },
    },
    "MEL_music_boss_gate": {
        "label": "Music Boss Gate",
        "preset_labels": {
            "BOSS_GATE_7": "7-Pipe Gate",
            "BOSS_GATE_5": "5-Pipe Gate",
            "BOSS_GATE_9": "9-Pipe Gate",
        },
        "preset_descriptions": {
            "BOSS_GATE_7": "7 pipes Mersenne, wide gate 3.2m.",
            "BOSS_GATE_5": "5 pipes, narrow.",
            "BOSS_GATE_9": "9 pipes, dense.",
        },
        "presets": {
            "BOSS_GATE_7": {
                "Width": 3.2, "Height": 4.5, "Depth": 0.45, "Pipe Radius": 0.09, "Pipe Count": 7, "Scale": 1.0,
            },
            "BOSS_GATE_5": {
                "Width": 2.6, "Height": 3.8, "Depth": 0.38, "Pipe Radius": 0.07, "Pipe Count": 5, "Scale": 1.0,
            },
            "BOSS_GATE_9": {
                "Width": 4.0, "Height": 5.2, "Depth": 0.52, "Pipe Radius": 0.11, "Pipe Count": 9, "Scale": 1.0,
            },
        },
    },
    "MEL_music_victory_plaza": {
        "label": "Music Victory Plaza",
        "preset_labels": {
            "VICTORY_12": "12-Ray Plaza",
            "VICTORY_8": "8-Ray Plaza",
            "VICTORY_16": "16-Ray Plaza",
        },
        "preset_descriptions": {
            "VICTORY_12": "12 rays Gold 500 radial.",
            "VICTORY_8": "8 rays, compact.",
            "VICTORY_16": "16 rays, dense.",
        },
        "presets": {
            "VICTORY_12": {
                "Radius": 6.0, "Ray Count": 12, "Ray Width": 0.6, "Ray Height": 0.15, "Center Height": 0.8, "Scale": 1.0,
            },
            "VICTORY_8": {
                "Radius": 4.5, "Ray Count": 8, "Ray Width": 0.5, "Ray Height": 0.12, "Center Height": 0.6, "Scale": 1.0,
            },
            "VICTORY_16": {
                "Radius": 7.5, "Ray Count": 16, "Ray Width": 0.7, "Ray Height": 0.18, "Center Height": 1.0, "Scale": 1.0,
            },
        },
    },
    "MEL_music_lullaby_nook": {
        "label": "Music Lullaby Nook",
        "preset_labels": {
            "NOOK_STANDARD": "Standard Nook",
            "NOOK_SMALL": "Small Nook",
            "NOOK_WIDE": "Wide Nook",
        },
        "preset_descriptions": {
            "NOOK_STANDARD": "3.2x2.8 nook, soft pocket.",
            "NOOK_SMALL": "2.2x1.8 mini.",
            "NOOK_WIDE": "4.5x3.5 wide.",
        },
        "presets": {
            "NOOK_STANDARD": {
                "Width": 3.2, "Depth": 2.8, "Height": 2.2, "Wall Thick": 0.18, "Nook Depth": 0.6, "Scale": 1.0,
            },
            "NOOK_SMALL": {
                "Width": 2.2, "Depth": 1.8, "Height": 1.6, "Wall Thick": 0.14, "Nook Depth": 0.4, "Scale": 1.0,
            },
            "NOOK_WIDE": {
                "Width": 4.5, "Depth": 3.5, "Height": 2.6, "Wall Thick": 0.22, "Nook Depth": 0.8, "Scale": 1.0,
            },
        },
    },

    "MEL_music_timpani": {
        "label": "Music Timpani",
        "preset_labels": {
            "TIMPANI_STANDARD": "Standard Timpani",
            "TIMPANI_SMALL": "Small Timpani",
            "TIMPANI_LARGE": "Large Timpani",
        },
        "preset_descriptions": {
            "TIMPANI_STANDARD": "Bowl 0.42m, tension 0.5, Bessel 1.59/2.14.",
            "TIMPANI_SMALL": "Small 0.32m, high tension.",
            "TIMPANI_LARGE": "Large 0.62m, low tension.",
        },
        "presets": {
            "TIMPANI_STANDARD": {
                "Bowl Radius": 0.42, "Bowl Depth": 0.38, "Membrane Tension": 0.5, "Rim Width": 0.04, "Scale": 1.0,
            },
            "TIMPANI_SMALL": {
                "Bowl Radius": 0.32, "Bowl Depth": 0.28, "Membrane Tension": 0.65, "Rim Width": 0.03, "Scale": 1.0,
            },
            "TIMPANI_LARGE": {
                "Bowl Radius": 0.62, "Bowl Depth": 0.52, "Membrane Tension": 0.35, "Rim Width": 0.055, "Scale": 1.0,
            },
        },
    },
    "MEL_music_tubular_bells": {
        "label": "Music Tubular Bells",
        "preset_labels": {
            "TUBULAR_8": "8-Tube Bells",
            "TUBULAR_6": "6-Tube Bells",
            "TUBULAR_10": "10-Tube Bells",
        },
        "preset_descriptions": {
            "TUBULAR_8": "8 long tubes ET, 1.45m longest.",
            "TUBULAR_6": "6 tubes, compact.",
            "TUBULAR_10": "10 tubes, extended.",
        },
        "presets": {
            "TUBULAR_8": {
                "Tube Count": 8, "Longest Tube (m)": 1.45, "Tube Radius": 0.038, "Spacing": 0.11, "Scale": 1.0,
            },
            "TUBULAR_6": {
                "Tube Count": 6, "Longest Tube (m)": 1.2, "Tube Radius": 0.032, "Spacing": 0.09, "Scale": 1.0,
            },
            "TUBULAR_10": {
                "Tube Count": 10, "Longest Tube (m)": 1.65, "Tube Radius": 0.042, "Spacing": 0.12, "Scale": 1.0,
            },
        },
    },
    "MEL_music_dulcimer": {
        "label": "Music Dulcimer",
        "preset_labels": {
            "DULCIMER_12": "12-Course Dulcimer",
            "DULCIMER_8": "8-Course Dulcimer",
            "DULCIMER_16": "16-Course Dulcimer",
        },
        "preset_descriptions": {
            "DULCIMER_12": "12 courses trapezoid, Mersenne.",
            "DULCIMER_8": "8 courses, small.",
            "DULCIMER_16": "16 courses, wide.",
        },
        "presets": {
            "DULCIMER_12": {
                "Width": 1.1, "Depth": 0.62, "Height": 0.09, "Course Count": 12, "String Radius": 0.0025, "Scale": 1.0,
            },
            "DULCIMER_8": {
                "Width": 0.85, "Depth": 0.48, "Height": 0.07, "Course Count": 8, "String Radius": 0.003, "Scale": 1.0,
            },
            "DULCIMER_16": {
                "Width": 1.35, "Depth": 0.75, "Height": 0.11, "Course Count": 16, "String Radius": 0.002, "Scale": 1.0,
            },
        },
    },
    "MEL_music_bamboo_chimes": {
        "label": "Music Bamboo Chimes",
        "preset_labels": {
            "BAMBOO_7": "7-Chime Bamboo",
            "BAMBOO_5": "5-Chime Bamboo",
            "BAMBOO_9": "9-Chime Bamboo",
        },
        "preset_descriptions": {
            "BAMBOO_7": "7 hollow bamboo, 0.9m longest, low density.",
            "BAMBOO_5": "5 chimes, compact.",
            "BAMBOO_9": "9 chimes, extended.",
        },
        "presets": {
            "BAMBOO_7": {
                "Chime Count": 7, "Longest (m)": 0.9, "Radius": 0.028, "Wall": 0.004, "Gap": 0.09, "Scale": 1.0,
            },
            "BAMBOO_5": {
                "Chime Count": 5, "Longest (m)": 0.75, "Radius": 0.022, "Wall": 0.003, "Gap": 0.08, "Scale": 1.0,
            },
            "BAMBOO_9": {
                "Chime Count": 9, "Longest (m)": 1.05, "Radius": 0.032, "Wall": 0.005, "Gap": 0.1, "Scale": 1.0,
            },
        },
    },

    "MEL_music_baroque_harpsichord": {
        "label": "Music Baroque Harpsichord",
        "preset_labels": {
            "HARPSICHORD_GILDED": "Gilded Harpsichord",
            "HARPSICHORD_EBONY": "Ebony Harpsichord",
            "HARPSICHORD_MINI": "Mini Harpsichord",
            "HARPSICHORD_SEA_ABOVE_HERO": "Sea Above Hero Harpsichord",
        },
        "preset_descriptions": {
            "HARPSICHORD_GILDED": "Gilded case, 56 strings, lid 42 deg, cabriole legs.",
            "HARPSICHORD_EBONY": "Ebony case, 48 strings, lid 35 deg.",
            "HARPSICHORD_MINI": "Mini 32 strings, compact.",
            "HARPSICHORD_SEA_ABOVE_HERO": "Room-scale gilded instrument architecture with restrained low-frequency influence.",
        },
        "presets": {
            "HARPSICHORD_GILDED": {
                "Length": 1.85, "Width": 0.92, "Height": 0.88, "Lid Angle": 42.0, "String Count": 56, "Leg Height": 0.72, "Scale": 1.0,
            },
            "HARPSICHORD_EBONY": {
                "Length": 1.65, "Width": 0.82, "Height": 0.78, "Lid Angle": 35.0, "String Count": 48, "Leg Height": 0.65, "Scale": 1.0,
            },
            "HARPSICHORD_MINI": {
                "Length": 1.25, "Width": 0.62, "Height": 0.58, "Lid Angle": 28.0, "String Count": 32, "Leg Height": 0.5, "Scale": 1.0,
            },
            "HARPSICHORD_SEA_ABOVE_HERO": {"Length": 2.7, "Width": 1.35, "Height": 1.15, "Lid Angle": 48.0, "String Count": 72, "Leg Height": 0.95, "Scale": 2.2, "Realize for export": True, "Music Influence": 0.08, "Musical Amplitude": 0.6, "Musical Freq A": 2.0, "Musical Freq B": 5.0},
        },
    },
    "MEL_music_baroque_violin": {
        "label": "Music Baroque Violin",
        "preset_labels": {
            "VIOLIN_BAROQUE": "Baroque Violin",
            "VIOLIN_GILDED": "Gilded Violin",
            "VIOLIN_MINI": "Mini Violin",
            "VIOLIN_BELL_RELIQUARY": "Bell Reliquary Violin",
        },
        "preset_descriptions": {
            "VIOLIN_BAROQUE": "Baroque scroll 2.2 turns, tailpiece wreath.",
            "VIOLIN_GILDED": "Gilded scroll 2.8 turns.",
            "VIOLIN_MINI": "Mini violin, 1.5 turns.",
            "VIOLIN_BELL_RELIQUARY": "Gallery-scale sculptural violin for Bell anatomy composition.",
        },
        "presets": {
            "VIOLIN_BAROQUE": {
                "Body Length": 0.59, "Body Width": 0.21, "Body Depth": 0.08, "Scroll Turns": 2.2, "Scale": 1.0,
            },
            "VIOLIN_GILDED": {
                "Body Length": 0.62, "Body Width": 0.23, "Body Depth": 0.09, "Scroll Turns": 2.8, "Scale": 1.0,
            },
            "VIOLIN_MINI": {
                "Body Length": 0.42, "Body Width": 0.16, "Body Depth": 0.06, "Scroll Turns": 1.5, "Scale": 1.0,
            },
            "VIOLIN_BELL_RELIQUARY": {"Body Length": 0.72, "Body Width": 0.27, "Body Depth": 0.11, "Scroll Turns": 3.2, "Scale": 4.0, "Realize for export": True, "Music Influence": 0.1, "Musical Amplitude": 0.45, "Musical Freq A": 3.0, "Musical Freq B": 7.0},
        },
    },
    "MEL_music_baroque_organ": {
        "label": "Music Baroque Organ",
        "preset_labels": {
            "ORGAN_CATHEDRAL": "Cathedral Organ",
            "ORGAN_CHAPEL": "Chapel Organ",
            "ORGAN_CHAMBER": "Chamber Organ",
            "ORGAN_ABYSSAL_CATHEDRAL": "Abyssal Cathedral Organ",
        },
        "preset_descriptions": {
            "ORGAN_CATHEDRAL": "Walkable facade 6.5x8.5m 19 pipes ET.",
            "ORGAN_CHAPEL": "Chapel 4.2x6.0m 13 pipes.",
            "ORGAN_CHAMBER": "Chamber 3.0x4.5m 9 pipes.",
            "ORGAN_ABYSSAL_CATHEDRAL": "Hero-scale walkable organ facade for Sea Above reveal staging.",
        },
        "presets": {
            "ORGAN_CATHEDRAL": {
                "Facade Width": 6.5, "Facade Height": 8.5, "Depth": 1.2, "Pipe Count": 19, "Longest Pipe (m)": 4.2, "Scale": 1.0,
            },
            "ORGAN_CHAPEL": {
                "Facade Width": 4.2, "Facade Height": 6.0, "Depth": 0.9, "Pipe Count": 13, "Longest Pipe (m)": 3.2, "Scale": 1.0,
            },
            "ORGAN_CHAMBER": {
                "Facade Width": 3.0, "Facade Height": 4.5, "Depth": 0.7, "Pipe Count": 9, "Longest Pipe (m)": 2.4, "Scale": 1.0,
            },
            "ORGAN_ABYSSAL_CATHEDRAL": {"Facade Width": 11.0, "Facade Height": 14.0, "Depth": 2.4, "Pipe Count": 31, "Longest Pipe (m)": 7.0, "Scale": 1.5, "Realize for export": True, "Music Influence": 0.07, "Musical Amplitude": 1.4, "Musical Freq A": 1.0, "Musical Freq B": 4.0},
        },
    },
    "MEL_music_baroque_lute": {
        "label": "Music Baroque Lute",
        "preset_labels": {
            "LUTE_STANDARD": "Standard Lute",
            "LUTE_THEORBO": "Theorbo",
            "LUTE_MANDORA": "Mandora",
            "LUTE_PELAGIC_VAULT": "Pelagic Vault Lute",
        },
        "preset_descriptions": {
            "LUTE_STANDARD": "Bowl 0.62x0.36 11 staves, neck 0.42.",
            "LUTE_THEORBO": "Long theorbo, 14 staves, neck 0.68.",
            "LUTE_MANDORA": "Mandora, 9 staves, short neck.",
            "LUTE_PELAGIC_VAULT": "Large vaulted-bowl sculpture with subtle membrane-like musical deformation.",
        },
        "presets": {
            "LUTE_STANDARD": {
                "Bowl Length": 0.62, "Bowl Width": 0.36, "Bowl Depth": 0.18, "Stave Count": 11, "Neck Length": 0.42, "Scale": 1.0,
            },
            "LUTE_THEORBO": {
                "Bowl Length": 0.72, "Bowl Width": 0.42, "Bowl Depth": 0.21, "Stave Count": 14, "Neck Length": 0.68, "Scale": 1.0,
            },
            "LUTE_MANDORA": {
                "Bowl Length": 0.48, "Bowl Width": 0.28, "Bowl Depth": 0.14, "Stave Count": 9, "Neck Length": 0.32, "Scale": 1.0,
            },
            "LUTE_PELAGIC_VAULT": {"Bowl Length": 0.9, "Bowl Width": 0.54, "Bowl Depth": 0.28, "Stave Count": 18, "Neck Length": 0.82, "Scale": 3.2, "Realize for export": True, "Music Influence": 0.12, "Musical Amplitude": 0.5, "Musical Freq A": 2.0, "Musical Freq B": 6.0},
        },
    },

    # --- Bevel polish V3 (Infinity Nikki soft look) ---
    "MEL_auto_bevel": {
        "label": "Auto Bevel (Ease)",
        "preset_labels": {
            "NIKKI_SOFT": "Nikki Soft",
            "HARD_SURFACE": "Hard Surface",
            "PORCELAIN": "Porcelain",
        },
        "preset_descriptions": {
            "NIKKI_SOFT": "Infinity Nikki pastel — 0.03 width, 3 segs, 30 deg, smooth on.",
            "HARD_SURFACE": "Crisp chamfer — 0.08 width, 2 segs, 45 deg.",
            "PORCELAIN": "Micro soft 0.015 width, 4 segs, 25 deg.",
        },
        "presets": {
            "NIKKI_SOFT": {"Width": 0.03, "Segments": 3, "Profile": 0.5, "Angle Threshold": 30.0, "Shade Smooth": True},
            "HARD_SURFACE": {"Width": 0.08, "Segments": 2, "Profile": 0.25, "Angle Threshold": 45.0, "Shade Smooth": True},
            "PORCELAIN": {"Width": 0.015, "Segments": 4, "Profile": 0.65, "Angle Threshold": 25.0, "Shade Smooth": True},
        },
    },
    "MEL_weighted_bevel": {
        "label": "Weighted Bevel",
        "preset_labels": {
            "NIK_SOFT_WEIGHTED": "Nikki Weighted Soft",
            "SHARP_INSET": "Sharp Inset",
            "AUTO_FALLBACK": "Auto Angle Fallback",
        },
        "preset_descriptions": {
            "NIK_SOFT_WEIGHTED": "Base 0.04 + weight scale 1.0, auto-angle 30 deg fallback.",
            "SHARP_INSET": "Base 0.06 weighted 1.5, narrow.",
            "AUTO_FALLBACK": "Base 0.03 weight on, auto angle handles unpainted edges.",
        },
        "presets": {
            "NIK_SOFT_WEIGHTED": {"Base Width": 0.04, "Segments": 3, "Weight Scale": 1.0, "Use Bevel Weight": True, "Auto Angle Threshold": 30.0},
            "SHARP_INSET": {"Base Width": 0.06, "Segments": 2, "Weight Scale": 1.5, "Use Bevel Weight": True, "Auto Angle Threshold": 45.0},
            "AUTO_FALLBACK": {"Base Width": 0.03, "Segments": 3, "Weight Scale": 1.0, "Use Bevel Weight": True, "Auto Angle Threshold": 30.0},
        },
    },
    "MEL_curvature_bevel": {
        "label": "Curvature Bevel",
        "preset_labels": {
            "DRAPE_SOFT": "Drape Soft",
            "FILIGREE_CRISP": "Filigree Crisp",
            "ORNATE_BLEND": "Ornate Blend",
        },
        "preset_descriptions": {
            "DRAPE_SOFT": "Drape curvature 0.8 thresh 0.5 — fabric-like.",
            "FILIGREE_CRISP": "Filigree 1.5 curvature, tight.",
            "ORNATE_BLEND": "Balanced ornate 1.0.",
        },
        "presets": {
            "DRAPE_SOFT": {"Base Width": 0.025, "Curvature Scale": 0.8, "Segments": 3, "Threshold": 0.5},
            "FILIGREE_CRISP": {"Base Width": 0.018, "Curvature Scale": 1.5, "Segments": 3, "Threshold": 0.35},
            "ORNATE_BLEND": {"Base Width": 0.022, "Curvature Scale": 1.0, "Segments": 3, "Threshold": 0.45},
        },
    },

    # --- Infinity Nikki expanded kit V3 ---
    "MEL_nikki_bloom_pavilion": {
        "label": "Nikki Bloom Pavilion",
        "preset_labels": {
            "SAKURA_BLOOM": "Sakura Bloom",
            "STARLIGHT_CANOPY": "Starlight Canopy",
            "HEART_PAVILION": "Heart Pavilion",
        },
        "preset_descriptions": {
            "SAKURA_BLOOM": "Radius 2.4, 8 petals, bloom 0.5, heart on.",
            "STARLIGHT_CANOPY": "Radius 3.2, 12 petals, bloom 0.8, heart on.",
            "HEART_PAVILION": "Small 1.8 radius, 6 petals, bloom 0.35.",
        },
        "presets": {
            "SAKURA_BLOOM": {"Radius": 2.4, "Height": 2.8, "Petal Count": 8, "Canopy Bloom": 0.5, "Heart Filigree": True, "Pastel Tint": 0.5},
            "STARLIGHT_CANOPY": {"Radius": 3.2, "Height": 3.4, "Petal Count": 12, "Canopy Bloom": 0.8, "Heart Filigree": True, "Pastel Tint": 0.75},
            "HEART_PAVILION": {"Radius": 1.8, "Height": 2.2, "Petal Count": 6, "Canopy Bloom": 0.35, "Heart Filigree": True, "Pastel Tint": 0.6},
        },
    },
    "MEL_nikki_wardrobe_nook": {
        "label": "Nikki Wardrobe Nook",
        "preset_labels": {
            "BOUDOIR": "Boudoir",
            "ATELIER": "Atelier",
            "CLOSET_PODIUM": "Closet Podium",
        },
        "preset_descriptions": {
            "BOUDOIR": "Width 3.2, depth 2.0, rods 2, mirror+pedestal.",
            "ATELIER": "Wide 4.0, 3 rods, mirror on.",
            "CLOSET_PODIUM": "Narrow 2.4, 1 rod, pedestal focus.",
        },
        "presets": {
            "BOUDOIR": {"Width": 3.2, "Depth": 2.0, "Height": 2.6, "Rod Count": 2, "Mirror": True, "Pedestal": True},
            "ATELIER": {"Width": 4.0, "Depth": 2.4, "Height": 2.8, "Rod Count": 3, "Mirror": True, "Pedestal": True},
            "CLOSET_PODIUM": {"Width": 2.4, "Depth": 1.6, "Height": 2.4, "Rod Count": 1, "Mirror": False, "Pedestal": True},
        },
    },
    "MEL_nikki_podium_runway": {
        "label": "Nikki Podium Runway",
        "preset_labels": {
            "RUNWAY_SHORT": "Short Runway",
            "RUNWAY_GRAND": "Grand Runway",
            "PETAL_RUNWAY": "Petal Runway",
        },
        "preset_descriptions": {
            "RUNWAY_SHORT": "Length 4, width 1.6, petals on.",
            "RUNWAY_GRAND": "Length 8, width 2.2, lights 8, petals on.",
            "PETAL_RUNWAY": "Length 6, sakura petals dense.",
        },
        "presets": {
            "RUNWAY_SHORT": {"Length": 4.0, "Width": 1.6, "Height": 0.4, "Light Count": 4, "Sakura Petals": True},
            "RUNWAY_GRAND": {"Length": 8.0, "Width": 2.2, "Height": 0.45, "Light Count": 8, "Sakura Petals": True},
            "PETAL_RUNWAY": {"Length": 6.0, "Width": 1.8, "Height": 0.38, "Light Count": 6, "Sakura Petals": True},
        },
    },
    "MEL_nikki_sheet_rail_hero": {
        "label": "Nikki Sheet Rail Hero",
        "preset_labels": {
            "BLOOM_PASTEL": "Bloom Pastel",
            "STARLIGHT_RAIL": "Starlight Rail",
            "HEART_RAIL": "Heart Rail",
        },
        "preset_descriptions": {
            "BLOOM_PASTEL": "Pastel bloom style 0 — soft nikki, 12 notes, clef on, auto bevel.",
            "STARLIGHT_RAIL": "Starlight style 1 — taller, airy.",
            "HEART_RAIL": "Heart style 2 — token crest, warm.",
        },
        "presets": {
            "BLOOM_PASTEL": {"Length": 6.0, "Height": 1.05, "Line Thickness": 0.04, "Line Spacing": 0.12, "Note Count": 12, "Style": 0, "Show Clef": True, "Auto Bevel": True},
            "STARLIGHT_RAIL": {"Length": 8.0, "Height": 1.25, "Line Thickness": 0.035, "Line Spacing": 0.14, "Note Count": 16, "Style": 1, "Show Clef": True, "Auto Bevel": True},
            "HEART_RAIL": {"Length": 5.0, "Height": 1.15, "Line Thickness": 0.045, "Line Spacing": 0.12, "Note Count": 8, "Style": 2, "Show Clef": True, "Auto Bevel": True},
        },
    },

    # profiles.py — column
    "MEL_column": {
        "label": "Column",
        "preset_labels": {
            "DORIC_SOBER": "Doric Sober",
            "FLUTED_IONIC": "Fluted Ionic",
            "PILASTER_SLIM": "Pilaster Slim",
        },
        "preset_descriptions": {
            "DORIC_SOBER": "Stately Doric column — no fluting, simple capital, wide base.",
            "FLUTED_IONIC": "Fluted Ionic column — 24 flutes, volute capital, tall slender profile.",
            "PILASTER_SLIM": "Wall pilaster — half-column, flat back, minimal projection.",
        },
        "presets": {
            "DORIC_SOBER": {"Height": 3.0, "Radius": 0.25, "Sides": 24, "Fluted": False, "Capital Height": 0.3, "Base Height": 0.2},
            "FLUTED_IONIC": {"Height": 4.0, "Radius": 0.18, "Sides": 24, "Fluted": True, "Capital Height": 0.45, "Base Height": 0.15},
            "PILASTER_SLIM": {"Height": 2.8, "Radius": 0.12, "Sides": 16, "Fluted": False, "Capital Height": 0.2, "Base Height": 0.1},
        },
    },

    # profiles.py — baluster
    "MEL_baluster": {
        "label": "Baluster",
        "preset_labels": {
            "CLASSIC_TURNED": "Classic Turned",
            "SQUARE_CHAMFER": "Square Chamfer",
            "GARDEN_GEM": "Garden Gem",
        },
        "preset_descriptions": {
            "CLASSIC_TURNED": "Traditional turned baluster — symmetrical bulge, smooth profile.",
            "SQUARE_CHAMFER": "Modern square baluster — chamfered edges, minimalist.",
            "GARDEN_GEM": "Short garden baluster — wide bulge, decorative gem top.",
        },
        "presets": {
            "CLASSIC_TURNED": {"Height": 0.9, "Width": 0.08, "Bulge": 0.5, "Segments": 24},
            "SQUARE_CHAMFER": {"Height": 0.8, "Width": 0.06, "Bulge": 0.1, "Segments": 4},
            "GARDEN_GEM": {"Height": 0.6, "Width": 0.12, "Bulge": 0.8, "Segments": 32},
        },
    },

    # profiles.py — post
    "MEL_post": {
        "label": "Post",
        "preset_labels": {
            "SQUARE_PLANTER": "Square Planter",
            "ROUNDED_BOLLARD": "Rounded Bollard",
            "CAPITAL_CROWN": "Capital Crown",
        },
        "preset_descriptions": {
            "SQUARE_PLANTER": "Square planter post — chamfered top, wide base.",
            "ROUNDED_BOLLARD": "Rounded bollard post — smooth dome cap, slim profile.",
            "CAPITAL_CROWN": "Crown post — ornate capital, decorative cap.",
        },
        "presets": {
            "SQUARE_PLANTER": {"Height": 0.7, "Width": 0.2, "Chamfer": 0.03, "Has Cap": False},
            "ROUNDED_BOLLARD": {"Height": 0.9, "Width": 0.12, "Chamfer": 0.05, "Has Cap": True},
            "CAPITAL_CROWN": {"Height": 1.2, "Width": 0.15, "Chamfer": 0.02, "Has Cap": True},
        },
    },

    # profiles.py — rail
    "MEL_rail": {
        "label": "Rail",
        "preset_labels": {
            "HANDRAIL_SMOOTH": "Handrail Smooth",
            "BALUSTRADE_TOP": "Balustrade Top",
            "WALL_MOUNT": "Wall Mount",
        },
        "preset_descriptions": {
            "HANDRAIL_SMOOTH": "Smooth handrail — ergonomic profile, comfortable grip.",
            "BALUSTRADE_TOP": "Balustrade top rail — wide flat profile, mounts balusters.",
            "WALL_MOUNT": "Wall-mounted rail — slim profile, minimal projection.",
        },
        "presets": {
            "HANDRAIL_SMOOTH": {"Profile Width": 0.06, "Profile Height": 0.04},
            "BALUSTRADE_TOP": {"Profile Width": 0.12, "Profile Height": 0.05},
            "WALL_MOUNT": {"Profile Width": 0.04, "Profile Height": 0.03},
        },
    },

    # profiles.py — star_finial
    "MEL_star_finial": {
        "label": "Star Finial",
        "preset_labels": {
            "FIVE_POINT": "Five-Point Star",
            "EIGHT_POINT": "Eight-Point Star",
            "COMPASS_ROSE": "Compass Rose",
        },
        "preset_descriptions": {
            "FIVE_POINT": "Classic five-point star finial — sharp points, tall profile.",
            "EIGHT_POINT": "Eight-point star — broader silhouette, shorter height.",
            "COMPASS_ROSE": "Compass rose finial — wide flat profile, navigational.",
        },
        "presets": {
            "FIVE_POINT": {"Points": 5, "Radius Outer": 0.3, "Radius Inner": 0.12, "Height": 0.4},
            "EIGHT_POINT": {"Points": 8, "Radius Outer": 0.35, "Radius Inner": 0.18, "Height": 0.25},
            "COMPASS_ROSE": {"Points": 16, "Radius Outer": 0.4, "Radius Inner": 0.2, "Height": 0.15},
        },
    },

    # primitives.py — circular_array
    "MEL_circular_array": {
        "label": "Circular Array",
        "preset_labels": {
            "COLUMN_RING": "Column Ring",
            "CHANDELIER": "Chandelier",
            "TURRET_CROWN": "Turret Crown",
        },
        "preset_descriptions": {
            "COLUMN_RING": "Ring of columns — evenly spaced, uniform scale.",
            "CHANDELIER": "Chandelier array — radial arms, varied scale.",
            "TURRET_CROWN": "Turret crown — tight ring, tall items, offset Z.",
        },
        "presets": {
            "COLUMN_RING": {"Count": 12, "Radius": 3.0, "Scale per item": 1.0, "Offset Z": 0.0},
            "CHANDELIER": {"Count": 8, "Radius": 1.5, "Scale per item": 0.6, "Offset Z": 0.5},
            "TURRET_CROWN": {"Count": 16, "Radius": 1.2, "Scale per item": 1.3, "Offset Z": 2.0},
        },
    },

    # primitives.py — linear_array
    "MEL_linear_array": {
        "label": "Linear Array",
        "preset_labels": {
            "COLONNADE": "Colonnade",
            "FENCE_LINE": "Fence Line",
            "TAPERED_ROW": "Tapered Row",
        },
        "preset_descriptions": {
            "COLONNADE": "Stately colonnade — evenly spaced columns, no taper.",
            "FENCE_LINE": "Fence line — close spacing, small items, slight taper.",
            "TAPERED_ROW": "Tapered row — items shrink along the line.",
        },
        "presets": {
            "COLONNADE": {"Count": 8, "Offset": (3.0, 0.0, 0.0), "Scale per item": 1.0, "Taper": 0.0},
            "FENCE_LINE": {"Count": 20, "Offset": (0.5, 0.0, 0.0), "Scale per item": 0.8, "Taper": 0.1},
            "TAPERED_ROW": {"Count": 10, "Offset": (2.0, 0.0, 0.0), "Scale per item": 1.0, "Taper": 0.5},
        },
    },

    # primitives.py — grid_array
    "MEL_grid_array": {
        "label": "Grid Array",
        "preset_labels": {
            "CITY_BLOCK": "City Block",
            "PLAZA_TILES": "Plaza Tiles",
            "GARDEN_PLOTS": "Garden Plots",
        },
        "preset_descriptions": {
            "CITY_BLOCK": "City block grid — dense, uniform spacing.",
            "PLAZA_TILES": "Plaza tiles — wide spacing, large items.",
            "GARDEN_PLOTS": "Garden plots — rectangular grid, varied spacing.",
        },
        "presets": {
            "CITY_BLOCK": {"Count X": 8, "Count Y": 8, "Spacing X": 4.0, "Spacing Y": 4.0},
            "PLAZA_TILES": {"Count X": 4, "Count Y": 4, "Spacing X": 8.0, "Spacing Y": 8.0},
            "GARDEN_PLOTS": {"Count X": 6, "Count Y": 3, "Spacing X": 3.0, "Spacing Y": 5.0},
        },
    },

    # primitives.py — instance_on_spline
    "MEL_instance_on_spline": {
        "label": "Instance on Spline",
        "preset_labels": {
            "RAILING_POSTS": "Railing Posts",
            "STREET_LAMPS": "Street Lamps",
            "VINE_TENDRILS": "Vine Tendrils",
        },
        "preset_descriptions": {
            "RAILING_POSTS": "Posts along a path — evenly spaced, uniform scale.",
            "STREET_LAMPS": "Street lamps — wide spacing, tall items, offset.",
            "VINE_TENDRILS": "Vine tendrils — dense spacing, small items, random offset.",
        },
        "presets": {
            "RAILING_POSTS": {"Count": 20, "Scale": 1.0, "Offset along curve": 0.0},
            "STREET_LAMPS": {"Count": 8, "Scale": 1.5, "Offset along curve": 0.1},
            "VINE_TENDRILS": {"Count": 50, "Scale": 0.3, "Offset along curve": 0.05},
        },
    },

    # structures.py — arch
    "MEL_arch": {
        "label": "Arch",
        "preset_labels": {
            "ROMAN_ROUND": "Roman Round",
            "GOTHIC_POINTED": "Gothic Pointed",
            "ELLIPTICAL": "Elliptical",
        },
        "preset_descriptions": {
            "ROMAN_ROUND": "Roman round arch — semicircular, thick walls.",
            "GOTHIC_POINTED": "Gothic pointed arch — tall rise, thin walls.",
            "ELLIPTICAL": "Elliptical arch — wide span, low rise.",
        },
        "presets": {
            "ROMAN_ROUND": {"Span": 3.0, "Height": 1.5, "Arch Rise": 0.5, "Thickness": 0.3, "Segments": 24},
            "GOTHIC_POINTED": {"Span": 2.5, "Height": 3.0, "Arch Rise": 0.8, "Thickness": 0.2, "Segments": 32},
            "ELLIPTICAL": {"Span": 5.0, "Height": 1.0, "Arch Rise": 0.25, "Thickness": 0.35, "Segments": 20},
        },
    },

    # structures.py — portico
    "MEL_portico": {
        "label": "Portico",
        "preset_labels": {
            "TEMPLE_FRONT": "Temple Front",
            "PORCH_ENTRY": "Porch Entry",
            "GRAND_STAIRCASE": "Grand Staircase",
        },
        "preset_descriptions": {
            "TEMPLE_FRONT": "Temple portico — wide column grid, tall pediment.",
            "PORCH_ENTRY": "Porch entry — small column pair, low profile.",
            "GRAND_STAIRCASE": "Grand staircase — wide portico, tall columns.",
        },
        "presets": {
            "TEMPLE_FRONT": {"Width": 8.0, "Depth": 4.0, "Column Height": 5.0, "Column Count": 6},
            "PORCH_ENTRY": {"Width": 3.0, "Depth": 2.0, "Column Height": 2.5, "Column Count": 2},
            "GRAND_STAIRCASE": {"Width": 12.0, "Depth": 6.0, "Column Height": 6.0, "Column Count": 8},
        },
    },

    # env_extras.py — lily_pond
    "MEL_env_lily_pond": {
        "label": "Lily Pond",
        "preset_labels": {
            "GARDEN_POND": "Garden Pond",
            "TEMPLE_POOL": "Temple Pool",
            "WILD_MARSH": "Wild Marsh",
        },
        "preset_descriptions": {
            "GARDEN_POND": "Garden lily pond — calm water, scattered pads, few lotus.",
            "TEMPLE_POOL": "Temple pool — still water, symmetrical pads, blooming lotus.",
            "WILD_MARSH": "Wild marsh — rippled water, dense pads, no lotus.",
        },
        "presets": {
            "GARDEN_POND": {"Pond Radius": 3.0, "Panel Depth": 0.3, "Water Level": 0.8, "Pad Count": 8, "Pad Size": 0.4, "Lotus Count": 3, "Current Speed": 0.1, "Ripple Carve": 0.2},
            "TEMPLE_POOL": {"Pond Radius": 5.0, "Panel Depth": 0.2, "Water Level": 0.9, "Pad Count": 12, "Pad Size": 0.5, "Lotus Count": 6, "Current Speed": 0.0, "Ripple Carve": 0.05},
            "WILD_MARSH": {"Pond Radius": 4.0, "Panel Depth": 0.5, "Water Level": 0.6, "Pad Count": 20, "Pad Size": 0.3, "Lotus Count": 0, "Current Speed": 0.4, "Ripple Carve": 0.6},
        },
    },

    # env_extras.py — campfire_ring
    "MEL_env_campfire_ring": {
        "label": "Campfire Ring",
        "preset_labels": {
            "CAMPFIRE_INTIMATE": "Campfire Intimate",
            "BONFIRE_PARTY": "Bonfire Party",
            "FIRE_PIT": "Fire Pit",
        },
        "preset_descriptions": {
            "CAMPFIRE_INTIMATE": "Intimate campfire — small ring, few logs, gentle flames.",
            "BONFIRE_PARTY": "Party bonfire — large ring, many logs, tall flames.",
            "FIRE_PIT": "Fire pit — stone ring, no logs, contained flames.",
        },
        "presets": {
            "CAMPFIRE_INTIMATE": {"Ring Radius": 0.8, "Stone Count": 8, "Log Count": 4, "Fire Scale": 0.5},
            "BONFIRE_PARTY": {"Ring Radius": 1.5, "Stone Count": 12, "Log Count": 8, "Fire Scale": 1.2},
            "FIRE_PIT": {"Ring Radius": 0.6, "Stone Count": 16, "Log Count": 0, "Fire Scale": 0.3},
        },
    },

    # env_extras.py — stepping_stones
    "MEL_env_stepping_stones": {
        "label": "Stepping Stones",
        "preset_labels": {
            "GARDEN_PATH": "Garden Path",
            "STREAM_CROSSING": "Stream Crossing",
            "ZEN_ROJI": "Zen Roji",
        },
        "preset_descriptions": {
            "GARDEN_PATH": "Garden path — evenly spaced, uniform stones.",
            "STREAM_CROSSING": "Stream crossing — irregular spacing, flat stones.",
            "ZEN_ROJI": "Zen roji — asymmetric placement, natural stones.",
        },
        "presets": {
            "GARDEN_PATH": {"Stone Count": 10, "Stone Size": 0.4, "Stone Height": 0.1, "Path Width": 1.5, "Path Length": 8.0},
            "STREAM_CROSSING": {"Stone Count": 6, "Stone Size": 0.5, "Stone Height": 0.15, "Path Width": 2.0, "Path Length": 6.0},
            "ZEN_ROJI": {"Stone Count": 8, "Stone Size": 0.35, "Stone Height": 0.08, "Path Width": 1.2, "Path Length": 5.0},
        },
    },

    # env_extras.py — market_stall
    "MEL_env_market_stall": {
        "label": "Market Stall",
        "preset_labels": {
            "BAKERY_STALL": "Bakery Stall",
            "FISH_MARKET": "Fish Market",
            "FLOWER_CART": "Flower Cart",
        },
        "preset_descriptions": {
            "BAKERY_STALL": "Bakery stall — wide awning, counter, bread shelves.",
            "FISH_MARKET": "Fish market — deep stall, awning, display counter.",
            "FLOWER_CART": "Flower cart — small stall, no awning, display shelves.",
        },
        "presets": {
            "BAKERY_STALL": {"Stall Width": 3.0, "Stall Depth": 2.0, "Post Height": 2.5, "Awning Drop": 0.8, "Counter Height": 1.0, "Stall Type": 0, "Has Stock": True},
            "FISH_MARKET": {"Stall Width": 4.0, "Stall Depth": 2.5, "Post Height": 2.8, "Awning Drop": 1.0, "Counter Height": 0.9, "Stall Type": 1, "Has Stock": True},
            "FLOWER_CART": {"Stall Width": 1.5, "Stall Depth": 1.0, "Post Height": 2.0, "Awning Drop": 0.0, "Counter Height": 0.8, "Stall Type": 2, "Has Stock": False},
        },
    },

    # mother.py — Faraway Mother Monolith
    "MEL_mother_head_silhouette": {
        "label": "Mother Head Silhouette",
        "preset_labels": {
            "MOONLIT_FACE": "Moonlit Face",
            "DISTANT_DREAMER": "Distant Dreamer",
            "AWASH_GRIEF": "Awash Grief",
        },
        "preset_descriptions": {
            "MOONLIT_FACE": "Default moonlit face profile — readable silhouette, soft ridges.",
            "DISTANT_DREAMER": "Distant dreamer — small silhouette, low noise, hazy.",
            "AWASH_GRIEF": "Awash grief — tall silhouette, sharp ridges, dramatic.",
        },
        "presets": {
            "MOONLIT_FACE": {"Width": 20.0, "Height": 8.0, "Depth": 6.0, "Noise Scale": 3.0, "Noise Detail": 4.0},
            "DISTANT_DREAMER": {"Width": 30.0, "Height": 5.0, "Depth": 8.0, "Noise Scale": 1.5, "Noise Detail": 2.0},
            "AWASH_GRIEF": {"Width": 15.0, "Height": 12.0, "Depth": 4.0, "Noise Scale": 5.0, "Noise Detail": 6.0},
        },
    },
    "MEL_mother_hair_cascade": {
        "label": "Mother Hair Cascade",
        "preset_labels": {
            "MOONLIT_FALLS": "Moonlit Falls",
            "SILKEN_DRIFT": "Silken Drift",
            "WILD_TRESSES": "Wild Tresses",
        },
        "preset_descriptions": {
            "MOONLIT_FALLS": "Moonlit waterfall cascade — long, slow, silver-blue.",
            "SILKEN_DRIFT": "Silken drift — short, wide, gentle flow.",
            "WILD_TRESSES": "Wild tresses — long, curled, untamed.",
        },
        "presets": {
            "MOONLIT_FALLS": {"Length": 12.0, "Width": 2.0, "Strand Count": 12, "Curl": 0.3},
            "SILKEN_DRIFT": {"Length": 6.0, "Width": 4.0, "Strand Count": 8, "Curl": 0.1},
            "WILD_TRESSES": {"Length": 18.0, "Width": 3.0, "Strand Count": 20, "Curl": 0.7},
        },
    },
    "MEL_mother_valley_depression": {
        "label": "Mother Valley Depression",
        "preset_labels": {
            "TORSO_WALK": "Torso Walk",
            "HEART_CHAMBER": "Heart Chamber",
            "DEEP_ABYSS": "Deep Abyss",
        },
        "preset_descriptions": {
            "TORSO_WALK": "Default torso valley — walkable depression, moderate fog.",
            "HEART_CHAMBER": "Heart chamber — small, deep, dense fog, intimate.",
            "DEEP_ABYSS": "Deep abyss — vast, deep, maximum fog.",
        },
        "presets": {
            "TORSO_WALK": {"Radius": 15.0, "Depth": 6.0, "Floor Noise": 1.0, "Fog Level": 0.6, "Steepness": 0.5},
            "HEART_CHAMBER": {"Radius": 8.0, "Depth": 10.0, "Floor Noise": 0.5, "Fog Level": 0.85, "Steepness": 0.8},
            "DEEP_ABYSS": {"Radius": 30.0, "Depth": 20.0, "Floor Noise": 2.0, "Fog Level": 0.95, "Steepness": 0.3},
        },
    },
    "MEL_mother_fog_volume": {
        "label": "Mother Fog Volume",
        "preset_labels": {
            "DISTANT_HINT": "Distant Hint",
            "CLOSING_IN": "Closing In",
            "TOTAL_OBSCURANCE": "Total Obscurance",
        },
        "preset_descriptions": {
            "DISTANT_HINT": "Distant hint — sparse fog, implied mass, silver-blue.",
            "CLOSING_IN": "Closing in — dense fog, looming presence.",
            "TOTAL_OBSCURANCE": "Total obscurance — thick fog, no visibility.",
        },
        "presets": {
            "DISTANT_HINT": {"Width": 40.0, "Height": 20.0, "Depth": 10.0, "Density": 0.02, "Tint Strength": 0.8, "Noise Scale": 1.5, "Falloff": 2.0},
            "CLOSING_IN": {"Width": 25.0, "Height": 15.0, "Depth": 8.0, "Density": 0.06, "Tint Strength": 0.9, "Noise Scale": 2.5, "Falloff": 1.5},
            "TOTAL_OBSCURANCE": {"Width": 15.0, "Height": 10.0, "Depth": 5.0, "Density": 0.12, "Tint Strength": 1.0, "Noise Scale": 4.0, "Falloff": 0.8},
        },
    },
    "MEL_mother_fabric_ridge": {
        "label": "Mother Fabric Ridge",
        "preset_labels": {
            "SKIN_FOLDS": "Skin Folds",
            "DRAPED_VEIL": "Draped Veil",
            "TENSE_MEMBRANE": "Tense Membrane",
        },
        "preset_descriptions": {
            "SKIN_FOLDS": "Default skin folds — regular ridges, medium depth, organic.",
            "DRAPED_VEIL": "Draped veil — long, flowing folds, gentle sharpness.",
            "TENSE_MEMBRANE": "Tense membrane — sharp, shallow folds, drum-like.",
        },
        "presets": {
            "SKIN_FOLDS": {"Width": 30.0, "Height": 6.0, "Fold Depth": 1.5, "Fold Count": 6, "Fold Sharpness": 2.0, "Noise Detail": 3.0},
            "DRAPED_VEIL": {"Width": 40.0, "Height": 4.0, "Fold Depth": 0.8, "Fold Count": 4, "Fold Sharpness": 1.0, "Noise Detail": 2.0},
            "TENSE_MEMBRANE": {"Width": 20.0, "Height": 8.0, "Fold Depth": 0.5, "Fold Count": 12, "Fold Sharpness": 4.0, "Noise Detail": 5.0},
        },
    },

    "MEL_mother_shoulder_fold": {
        "label": "Mother Shoulder Fold",
        "preset_labels": {
            "GENTLE_SLOPE": "Gentle Slope",
            "DRAMATIC_FOLD": "Dramatic Fold",
            "UNILATERAL_TORSO": "Unilateral Torso",
        },
        "preset_descriptions": {
            "GENTLE_SLOPE": "Gentle shoulder slope — low folds, subtle asymmetry.",
            "DRAMATIC_FOLD": "Dramatic fold — deep folds, strong asymmetry.",
            "UNILATERAL_TORSO": "Unilateral torso — one-sided fold, organic.",
        },
        "presets": {
            "GENTLE_SLOPE": {"Width": 25.0, "Length": 40.0, "Fold Count": 4, "Fold Depth": 1.2, "Asymmetry": 0.3, "Noise Detail": 3.0},
            "DRAMATIC_FOLD": {"Width": 30.0, "Length": 50.0, "Fold Count": 8, "Fold Depth": 3.0, "Asymmetry": 0.7, "Noise Detail": 5.0},
            "UNILATERAL_TORSO": {"Width": 20.0, "Length": 35.0, "Fold Count": 5, "Fold Depth": 2.0, "Asymmetry": 1.0, "Noise Detail": 2.0},
        },
    },

    "MEL_mother_heart_gate": {
        "label": "Mother Heart Gate",
        "preset_labels": {
            "INTIMATE_GATE": "Intimate Gate",
            "GRAND_ARCH": "Grand Arch",
            "PILLAR_HALL": "Pillar Hall",
        },
        "preset_descriptions": {
            "INTIMATE_GATE": "Intimate gate — small arch, subtle glow, personal scale.",
            "GRAND_ARCH": "Grand arch — tall pointed arch, strong glow, monumental.",
            "PILLAR_HALL": "Pillar hall — wide gate, many pillars, ceremonial.",
        },
        "presets": {
            "INTIMATE_GATE": {"Width": 3.0, "Height": 4.5, "Arch Point": 0.5, "Frame Thickness": 0.2, "Pillar Count": 2, "Glow Intensity": 1.0},
            "GRAND_ARCH": {"Width": 4.0, "Height": 7.0, "Arch Point": 0.7, "Frame Thickness": 0.35, "Pillar Count": 4, "Glow Intensity": 2.5},
            "PILLAR_HALL": {"Width": 8.0, "Height": 5.0, "Arch Point": 0.2, "Frame Thickness": 0.25, "Pillar Count": 8, "Glow Intensity": 1.5},
        },
    },

    "MEL_mother_moonlight_rig": {
        "label": "Mother Moonlight Rig",
        "preset_labels": {
            "SILVER_DREAM": "Silver Dream",
            "MOONLIT_KEY": "Moonlit Key",
            "DRAMATIC_SHADOW": "Dramatic Shadow",
        },
        "preset_descriptions": {
            "SILVER_DREAM": "Silver dream — soft key, gentle fill, ethereal.",
            "MOONLIT_KEY": "Moonlit key — standard three-point, silver-blue.",
            "DRAMATIC_SHADOW": "Dramatic shadow — strong key, deep shadows, high contrast.",
        },
        "presets": {
            "SILVER_DREAM": {"Key Intensity": 2.0, "Key Angle": 25.0, "Fill Intensity": 1.0, "Rim Intensity": 1.5, "Moon Tint": 0.9},
            "MOONLIT_KEY": {"Key Intensity": 3.0, "Key Angle": 35.0, "Fill Intensity": 0.5, "Rim Intensity": 1.5, "Moon Tint": 0.8},
            "DRAMATIC_SHADOW": {"Key Intensity": 5.0, "Key Angle": 45.0, "Fill Intensity": 0.2, "Rim Intensity": 2.0, "Moon Tint": 0.7},
        },
    },

    # white_current.py — The White Current Monolith
    "MEL_white_seam_spline": {
        "label": "White Seam Spline",
        "preset_labels": {
            "RIVER_TRACE": "River Trace",
            "LAKE_EDGE": "Lake Edge",
            "DEEP_CURRENT": "Deep Current",
        },
        "preset_descriptions": {
            "RIVER_TRACE": "Default river trace — moderate width, gentle flow.",
            "LAKE_EDGE": "Lake edge — wide seam, still water, high intensity.",
            "DEEP_CURRENT": "Deep current — narrow seam, fast flow, turbulent.",
        },
        "presets": {
            "RIVER_TRACE": {"Width": 0.15, "Flow Speed": 1.0, "Seam Intensity": 1.5, "Turbulence": 0.3, "Spline Resolution": 64},
            "LAKE_EDGE": {"Width": 0.4, "Flow Speed": 0.2, "Seam Intensity": 2.5, "Turbulence": 0.05, "Spline Resolution": 48},
            "DEEP_CURRENT": {"Width": 0.08, "Flow Speed": 3.0, "Seam Intensity": 1.0, "Turbulence": 0.8, "Spline Resolution": 96},
        },
    },
    "MEL_eel_silhouette": {
        "label": "Eel Silhouette",
        "preset_labels": {
            "PALE_GHOST": "Pale Ghost",
            "DEEP_DIVER": "Deep Diver",
            "SURFACE_SKIMMER": "Surface Skimmer",
        },
        "preset_descriptions": {
            "PALE_GHOST": "Pale ghost — translucent, glowing, slow movement.",
            "DEEP_DIVER": "Deep diver — long body, many fins, deep glow.",
            "SURFACE_SKIMMER": "Surface skimmer — short body, fast wave, bright glow.",
        },
        "presets": {
            "PALE_GHOST": {"Length": 15.0, "Body Width": 0.8, "Fin Count": 8, "Glow Intensity": 2.0, "Translucency": 0.7, "Wave Phase": 0.0},
            "DEEP_DIVER": {"Length": 25.0, "Body Width": 1.2, "Fin Count": 16, "Glow Intensity": 3.5, "Translucency": 0.5, "Wave Phase": 1.5},
            "SURFACE_SKIMMER": {"Length": 8.0, "Body Width": 0.5, "Fin Count": 4, "Glow Intensity": 4.0, "Translucency": 0.9, "Wave Phase": 3.0},
        },
    },
    "MEL_water_network": {
        "label": "Water Network",
        "preset_labels": {
            "RIVER_SYSTEM": "River System",
            "LAKE_CHAIN": "Lake Chain",
            "DELTAS": "Deltas",
        },
        "preset_descriptions": {
            "RIVER_SYSTEM": "River system — many nodes, high density, strong flow.",
            "LAKE_CHAIN": "Lake chain — few nodes, low density, still water.",
            "DELTAS": "Deltas — medium nodes, branching, moderate flow.",
        },
        "presets": {
            "RIVER_SYSTEM": {"Node Count": 24, "Connection Density": 0.7, "Flow Direction": 0.0, "White Level": 0.8, "Network Scale": 30.0},
            "LAKE_CHAIN": {"Node Count": 8, "Connection Density": 0.3, "Flow Direction": 0.5, "White Level": 0.95, "Network Scale": 20.0},
            "DELTAS": {"Node Count": 16, "Connection Density": 0.5, "Flow Direction": 1.0, "White Level": 0.7, "Network Scale": 25.0},
        },
    },
    "MEL_moonlit_surf": {
        "label": "Moonlit Surf",
        "preset_labels": {
            "CALM_MOON": "Calm Moon",
            "WAVES": "Waves",
            "STORM": "Storm",
        },
        "preset_descriptions": {
            "CALM_MOON": "Calm moon — still water, high reflection, visible seam.",
            "WAVES": "Waves — moderate waves, medium reflection.",
            "STORM": "Storm — high waves, low reflection, turbulent.",
        },
        "presets": {
            "CALM_MOON": {"Surface Size": 30.0, "Wave Height": 0.1, "Moon Reflection": 0.9, "Seam Visibility": 0.9, "Wave Scale": 1.0},
            "WAVES": {"Surface Size": 30.0, "Wave Height": 0.5, "Moon Reflection": 0.6, "Seam Visibility": 0.6, "Wave Scale": 2.0},
            "STORM": {"Surface Size": 30.0, "Wave Height": 1.5, "Moon Reflection": 0.3, "Seam Visibility": 0.3, "Wave Scale": 4.0},
        },
    },
    "MEL_white_haze_volume": {
        "label": "White Haze Volume",
        "preset_labels": {
            "DISTANT_MASS": "Distant Mass",
            "CLOSING_IN": "Closing In",
            "TOTAL_WHITE": "Total White",
        },
        "preset_descriptions": {
            "DISTANT_MASS": "Distant mass — sparse haze, white-blue, implies vast body.",
            "CLOSING_IN": "Closing in — dense haze, white tint, looming presence.",
            "TOTAL_WHITE": "Total white — thick haze, pure white, zero visibility.",
        },
        "presets": {
            "DISTANT_MASS": {"Width": 50.0, "Height": 15.0, "Depth": 8.0, "Density": 0.02, "Tint Strength": 0.85, "Noise Scale": 1.2, "Falloff": 2.5},
            "CLOSING_IN": {"Width": 30.0, "Height": 10.0, "Depth": 5.0, "Density": 0.05, "Tint Strength": 0.9, "Noise Scale": 2.0, "Falloff": 1.5},
            "TOTAL_WHITE": {"Width": 15.0, "Height": 8.0, "Depth": 3.0, "Density": 0.1, "Tint Strength": 1.0, "Noise Scale": 3.0, "Falloff": 0.8},
        },
    },
    "MEL_current_marker": {
        "label": "Current Marker",
        "preset_labels": {
            "FLOW_ARROWS": "Flow Arrows",
            "GLOW_TRAIL": "Glow Trail",
            "DENSE_PATH": "Dense Path",
        },
        "preset_descriptions": {
            "FLOW_ARROWS": "Flow arrows — moderate count, standard spacing, glow.",
            "GLOW_TRAIL": "Glow trail — many arrows, tight spacing, bright glow.",
            "DENSE_PATH": "Dense path — many arrows, wide spacing, fast flow.",
        },
        "presets": {
            "FLOW_ARROWS": {"Count": 16, "Spacing": 2.0, "Arrow Size": 0.3, "Glow Intensity": 1.5, "Flow Speed": 1.0},
            "GLOW_TRAIL": {"Count": 32, "Spacing": 1.0, "Arrow Size": 0.2, "Glow Intensity": 3.0, "Flow Speed": 2.0},
            "DENSE_PATH": {"Count": 24, "Spacing": 3.0, "Arrow Size": 0.4, "Glow Intensity": 1.0, "Flow Speed": 3.0},
        },
    },

    # god_molts.py — The God That Molts Monolith
    "MEL_shell_cephalon": {
        "label": "Shell Cephalon",
        "preset_labels": {
            "FRESH_MOLT": "Fresh Molt",
            "MINERALIZED": "Mineralized",
            "ANCIENT_RUIN": "Ancient Ruin",
        },
        "preset_descriptions": {
            "FRESH_MOLT": "Fresh molt — translucent, delicate, recent.",
            "MINERALIZED": "Mineralized — older shell, calcite deposits, ribbed.",
            "ANCIENT_RUIN": "Ancient ruin — weathered, cracked, glowing veins.",
        },
        "presets": {
            "FRESH_MOLT": {"Scale": 1.0, "Segment Count": 5, "Lobe Depth": 0.3, "Chitin Opacity": 0.9, "Vein Glow": 2.0, "Breathing Speed": 1.0},
            "MINERALIZED": {"Scale": 5.0, "Segment Count": 8, "Lobe Depth": 0.6, "Chitin Opacity": 0.6, "Vein Glow": 1.0, "Breathing Speed": 0.5},
            "ANCIENT_RUIN": {"Scale": 25.0, "Segment Count": 12, "Lobe Depth": 1.0, "Chitin Opacity": 0.3, "Vein Glow": 3.0, "Breathing Speed": 0.2},
        },
    },
    "MEL_shell_thorax": {
        "label": "Shell Thorax",
        "preset_labels": {
            "CATHERDRAL_RIBS": "Cathedral Ribs",
            "SEGMENTED_BODY": "Segmented Body",
            "CRUSHED_ARCHES": "Crushed Arches",
        },
        "preset_descriptions": {
            "CATHERDRAL_RIBS": "Cathedral ribs — tall arches, sacred space.",
            "SEGMENTED_BODY": "Segmented body — repeating arches, rhythmic.",
            "CRUSHED_ARCHES": "Crushed arches — broken, weathered, ancient.",
        },
        "presets": {
            "CATHERDRAL_RIBS": {"Segment Count": 8, "Arch Height": 3.0, "Rib Spacing": 0.5, "Breathing Speed": 1.0, "Chitin Thickness": 0.2},
            "SEGMENTED_BODY": {"Segment Count": 16, "Arch Height": 1.5, "Rib Spacing": 0.3, "Breathing Speed": 2.0, "Chitin Thickness": 0.1},
            "CRUSHED_ARCHES": {"Segment Count": 6, "Arch Height": 0.8, "Rib Spacing": 0.8, "Breathing Speed": 0.3, "Chitin Thickness": 0.4},
        },
    },
    "MEL_shell_pygidium": {
        "label": "Shell Pygidium",
        "preset_labels": {
            "TAIL_FAN": "Tail Fan",
            "BIOLUM_GLOW": "Biolum Glow",
            "DECAYING_FAN": "Decaying Fan",
        },
        "preset_descriptions": {
            "TAIL_FAN": "Tail fan — wide angle, glowing veins.",
            "BIOLUM_GLOW": "Biolum glow — intense bioluminescence, pulsing.",
            "DECAYING_FAN": "Decaying fan — broken, dim, ancient.",
        },
        "presets": {
            "TAIL_FAN": {"Fan Angle": 120.0, "Vein Count": 12, "Biolum Intensity": 2.0, "Pulse Phase": 0.0, "Scale": 1.0},
            "BIOLUM_GLOW": {"Fan Angle": 180.0, "Vein Count": 24, "Biolum Intensity": 5.0, "Pulse Phase": 1.5, "Scale": 2.0},
            "DECAYING_FAN": {"Fan Angle": 60.0, "Vein Count": 6, "Biolum Intensity": 0.5, "Pulse Phase": 3.0, "Scale": 0.5},
        },
    },
    "MEL_shell_interior": {
        "label": "Shell Interior",
        "preset_labels": {
            "SACRED_SPACE": "Sacred Space",
            "HOLLOW_CATHEDRAL": "Hollow Cathedral",
            "CRUSHED_INTERIOR": "Crushed Interior",
        },
        "preset_descriptions": {
            "SACRED_SPACE": "Sacred space — walkable hollow, ribbed walls.",
            "HOLLOW_CATHEDRAL": "Hollow cathedral — tall ceilings, breathing.",
            "CRUSHED_INTERIOR": "Crushed interior — collapsed, dark, ancient.",
        },
        "presets": {
            "SACRED_SPACE": {"Wall Thickness": 0.3, "Arch Count": 12, "Vein Spacing": 1.0, "Cathedral Height": 8.0, "Breathing Depth": 0.1},
            "HOLLOW_CATHEDRAL": {"Wall Thickness": 0.5, "Arch Count": 24, "Vein Spacing": 0.5, "Cathedral Height": 20.0, "Breathing Depth": 0.2},
            "CRUSHED_INTERIOR": {"Wall Thickness": 0.8, "Arch Count": 6, "Vein Spacing": 2.0, "Cathedral Height": 4.0, "Breathing Depth": 0.05},
        },
    },
    "MEL_fracture_seam": {
        "label": "Fracture Seam",
        "preset_labels": {
            "FRESH_CRACK": "Fresh Crack",
            "GLOWING_FRACTURE": "Glowing Fracture",
            "ANCIENT_DECAY": "Ancient Decay",
        },
        "preset_descriptions": {
            "FRESH_CRACK": "Fresh crack — recent break, sharp edges.",
            "GLOWING_FRACTURE": "Glowing fracture — light leaking through.",
            "ANCIENT_DECAY": "Ancient decay — weathered, overgrown.",
        },
        "presets": {
            "FRESH_CRACK": {"Crack Count": 4, "Crack Depth": 0.5, "Glow Leak": 2.0, "Decay Age": 0.1, "Scale": 1.0},
            "GLOWING_FRACTURE": {"Crack Count": 12, "Crack Depth": 1.5, "Glow Leak": 3.5, "Decay Age": 0.5, "Scale": 5.0},
            "ANCIENT_DECAY": {"Crack Count": 24, "Crack Depth": 3.0, "Glow Leak": 0.5, "Decay Age": 0.9, "Scale": 25.0},
        },
    },
    "MEL_biolum_vein": {
        "label": "Biolum Vein",
        "preset_labels": {
            "PULSE_TRAIL": "Pulse Trail",
            "BREATHING_WEB": "Breathing Web",
            "DIMMING_FLAME": "Dimming Flame",
        },
        "preset_descriptions": {
            "PULSE_TRAIL": "Pulse trail — bright, fast, rhythmic.",
            "BREATHING_WEB": "Breathing web — connected veins, slow pulse.",
            "DIMMING_FLAME": "Dimming flame — fading, ancient, weak.",
        },
        "presets": {
            "PULSE_TRAIL": {"Vein Count": 16, "Pulse Speed": 2.0, "Color Shift": 0.5, "Breathing Depth": 0.3, "Scale": 1.0},
            "BREATHING_WEB": {"Vein Count": 32, "Pulse Speed": 0.5, "Color Shift": 0.2, "Breathing Depth": 0.6, "Scale": 5.0},
            "DIMMING_FLAME": {"Vein Count": 8, "Pulse Speed": 0.2, "Color Shift": 0.8, "Breathing Depth": 0.1, "Scale": 25.0},
        },
    },
    "MEL_gravity_well": {
        "label": "Gravity Well",
        "preset_labels": {
            "SUBTLE_WARP": "Subtle Warp",
            "LENS_DISTORTION": "Lens Distortion",
            "TOTAL_COLLAPSE": "Total Collapse",
        },
        "preset_descriptions": {
            "SUBTLE_WARP": "Subtle warp — gentle distortion, barely visible.",
            "LENS_DISTORTION": "Lens distortion — clear warping, chromatic aberration.",
            "TOTAL_COLLAPSE": "Total collapse — extreme gravity, black hole.",
        },
        "presets": {
            "SUBTLE_WARP": {"Distortion Strength": 0.1, "Lens Radius": 5.0, "Chromatic Aberration": 0.1, "Breathing Pulse": 1.0, "Scale": 1.0},
            "LENS_DISTORTION": {"Distortion Strength": 1.0, "Lens Radius": 15.0, "Chromatic Aberration": 0.5, "Breathing Pulse": 2.0, "Scale": 5.0},
            "TOTAL_COLLAPSE": {"Distortion Strength": 4.0, "Lens Radius": 50.0, "Chromatic Aberration": 1.5, "Breathing Pulse": 0.5, "Scale": 25.0},
        },
    },
    "MEL_aftermath_fragment": {
        "label": "Aftermath Fragment",
        "preset_labels": {
            "FRESH_DEBRIS": "Fresh Debris",
            "SCATTERED_RUINS": "Scattered Ruins",
            "ANCIENT_DUST": "Ancient Dust",
        },
        "preset_descriptions": {
            "FRESH_DEBRIS": "Fresh debris — recent molt, sharp fragments.",
            "SCATTERED_RUINS": "Scattered ruins — weathered, overgrown.",
            "ANCIENT_DUST": "Ancient dust — crumbled, barely visible.",
        },
        "presets": {
            "FRESH_DEBRIS": {"Fragment Count": 24, "Scatter Range": 10.0, "Decay Age": 0.1, "Chitin Remnant": 0.8, "Scale": 1.0},
            "SCATTERED_RUINS": {"Fragment Count": 48, "Scatter Range": 30.0, "Decay Age": 0.5, "Chitin Remnant": 0.4, "Scale": 5.0},
            "ANCIENT_DUST": {"Fragment Count": 96, "Scatter Range": 60.0, "Decay Age": 0.9, "Chitin Remnant": 0.1, "Scale": 25.0},
        },
    },

}

# Melodia Studio v3 planetary families.  Mode is a continuous shared shape
# vocabulary: 0 continent, 1 canyon, 2 reef, 3 arches, 4 cave mouth,
# 5 monolith field, 6 settlement shelf, 7 false horizon, 8 floating island,
# 9 fully island-masked.
BUILDERS_PRESETS["MEL_planetary_musical_terrain"] = {
    "label": "Planetary Musical Terrain",
    "presets": {
    "PLANETARY_EXPLORATION_PREVIEW": {"Terrain Mode": 0, "Seed": 1337, "Size X M": 256.0, "Size Y M": 256.0, "Resolution X": 129, "Resolution Y": 129, "Macro Height M": 54.0, "Macro Scale M": 420.0, "Mid Height M": 13.0, "Mid Scale M": 90.0, "Micro Height M": 2.0, "Micro Scale M": 16.0, "Reserved Path M": 10.0, "Audio Height M": 0.0, "Music Influence": 0.0},
    "SEA_ABOVE_FALSE_HORIZON_V3": {"Terrain Mode": 7, "Seed": 8088, "Size X M": 1024.0, "Size Y M": 512.0, "Resolution X": 513, "Resolution Y": 257, "Base Height M": -18.0, "Macro Height M": 130.0, "Macro Scale M": 880.0, "Mid Height M": 22.0, "Mid Scale M": 140.0, "Shore Height M": 2.0, "Low Hz": 18.0, "High Hz": 600.0, "Audio Gain": 3.0, "Audio Height M": 18.0, "Music Influence": 0.06},
    "MUSICAL_RUINS_CANYON": {"Terrain Mode": 1, "Seed": 440, "Size X M": 512.0, "Size Y M": 512.0, "Resolution X": 257, "Resolution Y": 257, "Macro Height M": 105.0, "Macro Scale M": 360.0, "Mid Height M": 28.0, "Mid Scale M": 72.0, "Reserved Path M": 14.0, "Low Hz": 55.0, "High Hz": 2200.0, "Audio Height M": 9.0, "Music Influence": 0.04},
    "FLOATING_BAROQUE_SETTLEMENT": {"Terrain Mode": 8, "Seed": 1729, "Size X M": 384.0, "Size Y M": 384.0, "Resolution X": 257, "Resolution Y": 257, "Base Height M": 80.0, "Macro Height M": 76.0, "Macro Scale M": 300.0, "Island Radius": 0.66, "Reserved Path M": 18.0, "Low Hz": 80.0, "High Hz": 4200.0, "Audio Height M": 7.0, "Music Influence": 0.08},
    "REEF_CATHEDRAL_SHELF": {"Terrain Mode": 2, "Seed": 31415, "Size X M": 512.0, "Size Y M": 384.0, "Resolution X": 257, "Resolution Y": 193, "Base Height M": -42.0, "Macro Height M": 68.0, "Macro Scale M": 260.0, "Mid Height M": 34.0, "Mid Scale M": 54.0, "Shore Height M": -5.0, "Low Hz": 28.0, "High Hz": 1400.0, "Audio Height M": 14.0, "Music Influence": 0.1},
    "TRAVERSAL_CORRIDOR_CONTINENT": {"Terrain Mode": 6, "Seed": 20260830, "Size X M": 1024.0, "Size Y M": 1024.0, "Resolution X": 513, "Resolution Y": 513, "Macro Height M": 92.0, "Macro Scale M": 740.0, "Mid Height M": 18.0, "Reserved Path M": 24.0, "Audio Height M": 4.0, "Music Influence": 0.03},
    },
    "preset_descriptions": {
        "PLANETARY_EXPLORATION_PREVIEW": "Fast deterministic planetary composition and seam review.",
        "SEA_ABOVE_FALSE_HORIZON_V3": "Kilometre-scale false horizon with restrained low-frequency musical relief.",
        "MUSICAL_RUINS_CANYON": "Traversal-first canyon shelf for musical ruin placement.",
        "FLOATING_BAROQUE_SETTLEMENT": "Island-masked elevated shelf for a floating Baroque settlement.",
        "REEF_CATHEDRAL_SHELF": "Submerged reef/cathedral terrain with strong cavity and shoreline masks.",
        "TRAVERSAL_CORRIDOR_CONTINENT": "Continent tile with a wide reserved path mask for player routes.",
    },
}

# -----------------------------------------------------------------------------
# Accessors
# -----------------------------------------------------------------------------


def _entry(builder_id: str) -> dict[str, Any]:
    """Return a builder's preset entry; raise KeyError for unknown ids."""
    entry = BUILDERS_PRESETS.get(builder_id)
    if entry is None:
        raise KeyError(f"presets: no preset entry for builder '{builder_id}'")
    return entry


def builders_with_presets() -> list[str]:
    """Sorted ids of all builders that have curated presets."""
    return sorted(BUILDERS_PRESETS)


def preset_names(builder_id: str) -> list[str]:
    """Preset names for one builder (insertion order)."""
    return list(_entry(builder_id)["presets"])


def preset_param_sets(builder_id: str) -> list[dict]:
    """List of preset dicts: {name, label, description?, params}."""
    entry = _entry(builder_id)
    out = []
    for name, params in entry["presets"].items():
        item = {
            "name": name,
            "label": entry.get("preset_labels", {}).get(
                name, name.replace("_", " ").title()),
            "params": dict(params),
        }
        desc = entry.get("preset_descriptions", {}).get(name)
        if desc:
            item["description"] = desc
        out.append(item)
    return out


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------


def export_builder_preset(builder_id: str, preset_name: str) -> dict:
    """One preset as a metadata + param-map dict (JSON-serializable)."""
    entry = _entry(builder_id)
    params = entry["presets"].get(preset_name)
    if params is None:
        raise KeyError(
            f"presets: '{preset_name}' not defined for builder '{builder_id}'"
        )
    return {
        "schema_version": PRESET_SCHEMA_VERSION,
        "source": PRESET_SOURCE,
        "builder_id": builder_id,
        "builder_label": entry["label"],
        "preset_name": preset_name,
        "preset_label": entry.get("preset_labels", {}).get(
            preset_name, preset_name.replace("_", " ").title()),
        "description": entry.get("preset_descriptions", {}).get(preset_name, ""),
        "params": dict(params),
    }


def export_all_presets_json(path: str) -> str:
    """Write every curated preset to `path` as pretty JSON. Returns `path`."""
    builders = {}
    for bid, entry in sorted(BUILDERS_PRESETS.items()):
        builders[bid] = {
            "label": entry["label"],
            "presets": {name: dict(params) for name, params in entry["presets"].items()},
        }
    payload = {
        "schema_version": PRESET_SCHEMA_VERSION,
        "source": PRESET_SOURCE,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "builder_count": len(builders),
        "preset_count": sum(len(b["presets"]) for b in builders.values()),
        "builders": builders,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


# -----------------------------------------------------------------------------
# Audit (registry-aware; lazy GROUP_METADATA import so this file stays pure)
# -----------------------------------------------------------------------------


def audit_presets() -> dict:
    """Report which registered builders have curated presets and which do not.

    Reads the live registry GROUP_METADATA via a deferred import so the module
    still imports and runs on a naked Python (no bpy). When the registry is
    unavailable the report covers the preset library's own inventory instead
    and sets registry_available=False.
    """
    report = {
        "registry_available": False,
        "registered_builders": 0,
        "preset_builders": len(BUILDERS_PRESETS),
        "preset_count": sum(
            len(entry["presets"]) for entry in BUILDERS_PRESETS.values()),
        "builders_with_presets": [],
        "builders_without_presets": [],
        "orphan_preset_builders": [],
    }
    try:
        from .core import GROUP_METADATA  # deferred: needs bpy
    except Exception as exc:  # no bpy / core unavailable
        report["registry_error"] = f"{type(exc).__name__}: {exc}"
        report["builders_with_presets"] = builders_with_presets()
        return report

    report["registry_available"] = True
    registry = set(GROUP_METADATA)
    report["registered_builders"] = len(registry)
    report["builders_with_presets"] = sorted(registry & set(BUILDERS_PRESETS))
    report["builders_without_presets"] = sorted(registry - set(BUILDERS_PRESETS))
    report["orphan_preset_builders"] = sorted(
        set(BUILDERS_PRESETS) - registry)
    covered = len(report["builders_with_presets"])
    total = len(registry)
    report["coverage_ratio"] = round(covered / total, 4) if total else 0.0
    return report


# -----------------------------------------------------------------------------
# Standalone entry point (for QA without bpy)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Melusina House Round Interior presets
# -----------------------------------------------------------------------------

BUILDERS_PRESETS["MEL_melusina_house_round_interior"] = {
    "label": "Melusina House Round Interior",
    "presets": {
        "Default_Charming": {
            "Interior Height": 3.1,
            "Wall Thickness": 0.24,
            "Show Interior": True,
            "Include Stair": True,
        },
        "Compact_SeaVilla": {
            "Interior Height": 2.8,
            "Wall Thickness": 0.18,
            "Show Interior": True,
            "Include Stair": True,
        },
        "Grand_Salon": {
            "Interior Height": 4.2,
            "Wall Thickness": 0.30,
            "Show Interior": True,
            "Include Stair": False,
        },
    },
    "preset_labels": {
        "Default_Charming": "Default Charming",
        "Compact_SeaVilla": "Compact Sea Villa",
        "Grand_Salon": "Grand Salon",
    },
    "preset_descriptions": {
        "Default_Charming": "The round-plan interior as specified in melusinashouseplan.md §12/§16.",
        "Compact_SeaVilla": "Lower ceilings, slimmer walls — a cozy seaside villa read.",
        "Grand_Salon": "Taller, thicker walls, no stair — an open grand salon interior.",
    },
}


# -----------------------------------------------------------------------------
# Melodia City Gen presets
# -----------------------------------------------------------------------------

BUILDERS_PRESETS["MEL_city_house_cell"] = {
    "label": "City House Cell",
    "presets": {
        "Charming_Cottage": {"Width": 5.5, "Depth": 4.0, "Height": 3.2,
                             "Wall Thickness": 0.24, "Roof Rise": 0.8, "Show Interior": True},
        "Sea_Villa": {"Width": 6.5, "Depth": 5.0, "Height": 3.5,
                      "Wall Thickness": 0.26, "Roof Rise": 1.0, "Show Interior": True},
        "Urban_Maison": {"Width": 4.5, "Depth": 7.0, "Height": 4.2,
                         "Wall Thickness": 0.30, "Roof Rise": 1.2, "Show Interior": False},
    },
    "preset_labels": {
        "Charming_Cottage": "Charming Cottage",
        "Sea_Villa": "Sea Villa",
        "Urban_Maison": "Urban Maison",
    },
    "preset_descriptions": {
        "Charming_Cottage": "A cozy round-Baroque cottage, slightly square.",
        "Sea_Villa": "A wider seaside villa with a taller roof rise.",
        "Urban_Maison": "A tall, deep street maisonette (interior hidden).",
    },
}

BUILDERS_PRESETS["MEL_city_avenue"] = {
    "label": "City Avenue",
    "presets": {
        "Lakeside_Row": {"Count": 6, "Cell Width": 6.0, "Cell Depth": 4.5,
                         "Cell Height": 3.4, "Street Gap": 2.0},
        "Old_Town": {"Count": 8, "Cell Width": 4.5, "Cell Depth": 6.0,
                     "Cell Height": 4.0, "Street Gap": 1.0},
        "Grand_Boulevard": {"Count": 10, "Cell Width": 7.0, "Cell Depth": 5.0,
                            "Cell Height": 4.5, "Street Gap": 3.0},
    },
    "preset_labels": {
        "Lakeside_Row": "Lakeside Row",
        "Old_Town": "Old Town Street",
        "Grand_Boulevard": "Grand Boulevard",
    },
    "preset_descriptions": {
        "Lakeside_Row": "A relaxed street of six villas with wide gaps.",
        "Old_Town": "A tight, tall older street, more units.",
        "Grand_Boulevard": "A wide ceremonial avenue of large houses.",
    },
}

BUILDERS_PRESETS["MEL_city_block"] = {
    "label": "City Block",
    "presets": {
        "District_Heart": {"Rows": 3, "Row Pitch": 6.0},
        "Harbour_West": {"Rows": 2, "Row Pitch": 8.0},
        "Quarter_Est": {"Rows": 4, "Row Pitch": 5.5},
    },
    "preset_labels": {
        "District_Heart": "District Heart",
        "Harbour_West": "Harbour West",
        "Quarter_Est": "Quarter East",
    },
    "preset_descriptions": {
        "District_Heart": "A three-row city block district.",
        "Harbour_West": "A looser two-row set facing the water.",
        "Quarter_Est": "A dense four-row grid quarter.",
    },
}

BUILDERS_PRESETS["MEL_city_plan_salon"] = {
    "label": "Plan — Rectangular Salon",
    "presets": {
        "Grand_Hall": {"Interior Height": 3.8, "Wall Thickness": 0.26, "Show Interior": True},
        "Intimate_Parlor": {"Interior Height": 3.0, "Wall Thickness": 0.20, "Show Interior": True},
        "Open_Shell": {"Interior Height": 3.4, "Wall Thickness": 0.24, "Show Interior": False},
    },
    "preset_labels": {"Grand_Hall": "Grand Hall", "Intimate_Parlor": "Intimate Parlor", "Open_Shell": "Open Shell"},
    "preset_descriptions": {
        "Grand_Hall": "A tall, formal rectangular salon.",
        "Intimate_Parlor": "A lower, cozy parlor read.",
        "Open_Shell": "Exterior shell only — no interior shown.",
    },
}

BUILDERS_PRESETS["MEL_city_plan_courtyard"] = {
    "label": "Plan — Courtyard Quad",
    "presets": {
        "Cloister_Quad": {"Interior Height": 3.4, "Wall Thickness": 0.24, "Show Interior": True},
        "Walled_Garden": {"Interior Height": 3.0, "Wall Thickness": 0.30, "Show Interior": True},
        "Open_Quad": {"Interior Height": 3.2, "Wall Thickness": 0.24, "Show Interior": False},
    },
    "preset_labels": {"Cloister_Quad": "Cloister Quad", "Walled_Garden": "Walled Garden", "Open_Quad": "Open Quad"},
    "preset_descriptions": {
        "Cloister_Quad": "Four wings around a central courtyard void.",
        "Walled_Garden": "Thicker walls for a sheltered garden feel.",
        "Open_Quad": "The quad massing without interior walls.",
    },
}

BUILDERS_PRESETS["MEL_city_corridors"] = {
    "label": "Corridor Variants",
    "presets": {
        "Straight_Hall": {"Corridor Type": 0, "Length": 8.0, "Width": 2.4, "Height": 3.2, "Wall Thickness": 0.25},
        "L_Elbow": {"Corridor Type": 1, "Length": 6.0, "Width": 2.4, "Height": 3.2, "Wall Thickness": 0.25},
        "Gallery": {"Corridor Type": 2, "Length": 10.0, "Width": 4.0, "Height": 3.6, "Wall Thickness": 0.30},
        "Dog_Leg": {"Corridor Type": 3, "Length": 8.0, "Width": 2.4, "Height": 3.2, "Wall Thickness": 0.25},
    },
    "preset_labels": {
        "Straight_Hall": "Straight Hall", "L_Elbow": "L-Elbow",
        "Gallery": "Gallery", "Dog_Leg": "Dog-Leg",
    },
    "preset_descriptions": {
        "Straight_Hall": "A straight tiled corridor.",
        "L_Elbow": "A corner turning corridor.",
        "Gallery": "A wide arcade-like gallery hall.",
        "Dog_Leg": "A two-run dog-leg corridor.",
    },
}


def main() -> None:
    report = audit_presets()
    print("[Melodia GN presets] audit:")
    for key in (
        "registry_available", "registered_builders", "preset_builders",
        "preset_count", "coverage_ratio",
    ):
        if key in report:
            print(f"  {key}: {report[key]}")
    if report.get("registry_error"):
        print(f"  registry_error: {report['registry_error']}")
    print(f"  builders_with_presets ({len(report['builders_with_presets'])}):")
    for bid in report["builders_with_presets"]:
        print(f"    {bid}: {len(BUILDERS_PRESETS[bid]['presets'])} presets")
    if report["registry_available"]:
        missing = report["builders_without_presets"]
        print(f"  builders_without_presets ({len(missing)}):")
        for bid in missing:
            print(f"    {bid}")


if __name__ == "__main__":
    main()
