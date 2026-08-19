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

# —————————————————————————————————————————————————————————————————————————————
# Preset data — one entry per builder, keys match actual builder input sockets.
# —————————————————————————————————————————————————————————————————————————————

BUILDERS_PRESETS: dict[str, dict[str, Any]] = {
    # water.py — MEL_water_gerstner (effects)
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

    # structures.py — MEL_gazebo (structures)
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

    # castle.py — MEL_castle_tower (castle)
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

    # ribbon.py — MEL_ribbon_curve (effects)
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

    # set_dressing.py — MEL_water_them_gazebo (set_dressing)
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

    # set_dressing.py — MEL_music_them_gazebo (set_dressing)
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

    # recursive_castle.py — MEL_recursive_castle_spire (castle)
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

    # nikki_quarter.py — MEL_nikki_quarter (structures)
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

    # sky_observatory.py — MEL_sky_observatory (structures)
    "MEL_sky_observatory": {
        "label": "Celestial Dream Observatory",
        "preset_labels": {
            "CELESTIAL_DREAM": "Celestial Dream",
            "MINIMAL_ISLE": "Minimal Sky Isle",
            "RING_TEMPLE": "Ring Temple",
        },
        "preset_descriptions": {
            "CELESTIAL_DREAM": "Full hero island: orrery rings, planets, lanterns.",
            "MINIMAL_ISLE": "Two rings, no fixtures — clean silhouette.",
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

    # escher_waterfall.py — MEL_escher_waterfall (castle)
    "MEL_escher_waterfall": {
        "label": "Escher Waterfall",
        "preset_labels": {
            "IMPOSSIBLE_TRIBAR": "Impossible Tribar",
            "QUIET_LOOP": "Quiet Loop",
            "CHAOS_CASCADE": "Chaos Cascade",
        },
        "preset_descriptions": {
            "IMPOSSIBLE_TRIBAR": "Canonical channel loop with pillars and splash ring.",
            "QUIET_LOOP": "Bare loop without fixtures — hero prop read.",
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

    # music.py — MEL_music_staff (music)
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

    # profiles.py — MEL_column (profiles)
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

    # pcg_integration.py — MEL_pcg_water_tags_v2 (set_dressing)
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

    # effects.py — MEL_effect_wave (effects)
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

    # filigree.py — MEL_harmonic_orb (music)
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

    # music_instruments.py — MEL_brass_pipe (music)
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

    # music.py — MEL_music_note_head (music)
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

    # effects.py — MEL_effect_magic (effects) — 3 of 10 legacy looks
    "MEL_effect_magic": {
        "label": "Magic Distortion",
        "preset_labels": {
            "LIQUID": "Liquid",
            "CRYSTAL": "Crystal",
            "GRAVITY_WELL": "Gravity Well",
        },
        "preset_descriptions": {
            "LIQUID": "Flowing animated noise, mid intensity — liquid-surface read.",
            "CRYSTAL": "High-frequency chromatic facets, static — gem/ice read.",
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

    # music.py — MEL_music_harmonic (music)
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

    # music.py — MEL_music_treble_clef (music)
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

    # music_heroes.py — MEL_music_key_unit (music)
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

    # music_heroes.py — MEL_music_piano_roll (music)
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

    # music_heroes.py — MEL_music_sheet_rail (music)
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

    # music_heroes.py — MEL_music_room_shell (structures)
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

    # music_heroes.py — MEL_music_harp (music)
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

    # filigree.py — MEL_filigree_spiral (filigree)
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

    # escher_belvedere.py — MEL_escher_belvedere (castle)
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

    # escher_penrose_stairs.py — MEL_escher_penrose_stairs (castle)
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

    # castle.py — MEL_castle_assembler (castle) — scalar sockets only
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

    # ornament.py — P1 thin-kit (vine / radial / frame before new generators)
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

    # ornament_extras.py — remaining Filigree kit (3)
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

    # operations.py + geometry_extras.py — remaining Operations kit (3)
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
        },
        "preset_descriptions": {
            "SMALL_CELL": "Tight 4x4 cell with a ceiling.",
            "HALL": "Long assembly hall, high ceiling.",
            "CLOISTER_WALK": "Wide cloister bay with thinner walls.",
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
}

# —————————————————————————————————————————————————————————————————————————————
# Accessors
# —————————————————————————————————————————————————————————————————————————————


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


# —————————————————————————————————————————————————————————————————————————————
# Export
# —————————————————————————————————————————————————————————————————————————————


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


# —————————————————————————————————————————————————————————————————————————————
# Audit (registry-aware; lazy GROUP_METADATA import so this file stays pure)
# —————————————————————————————————————————————————————————————————————————————


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


# —————————————————————————————————————————————————————————————————————————————
# Standalone entry point (for QA without bpy)
# —————————————————————————————————————————————————————————————————————————————


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