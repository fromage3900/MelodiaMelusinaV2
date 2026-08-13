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
            },
            "MARKET_PAVILION": {
                "Radius": 3.5, "Column Count": 12, "Column Height": 2.8,
                "Roof Pitch": 0.5, "Beam Radius": 0.07, "Has Finial": False,
            },
            "BANDSTAND_PARK": {
                "Radius": 2.8, "Column Count": 8, "Column Height": 3.2,
                "Roof Pitch": 0.6, "Beam Radius": 0.06, "Has Finial": True,
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
                "Complete Walls": True, "Corner Towers": True,
            },
            "WIDE_BAILEY": {
                "Site Scale": 2.2, "Courtyard Width": 48.0, "Courtyard Depth": 36.0,
                "Complete Walls": True, "Corner Towers": True,
            },
            "COMPACT_CITADEL": {
                "Site Scale": 0.6, "Courtyard Width": 10.0, "Courtyard Depth": 8.0,
                "Complete Walls": True, "Corner Towers": False,
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