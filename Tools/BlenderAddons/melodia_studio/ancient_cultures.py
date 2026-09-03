"""Ancient Cultures - musical instrument presets for Melodia Studio.

Twelve deeply-researched presets, each derived from a real ancient instrument
tradition. The musical->spatial mapping honours how each instrument actually
behaves: its meter becomes chunk_beats, its register/attack becomes relief,
its drone/percussion split becomes the beatgrid (cave) layer.

Pure Python, no bpy. Merged into midi_bridge.load_presets() and
terrain_dressing.DRESSING_STYLES at import; tandem pairs extend
tandem_bridge.MELODIA_TO_SURREAL.

Fields per preset:
  label / description      - UI copy (instrument + culture + era)
  chunk_beats              - meter of the tradition's core pulse
  surface_height_divisor   - RESERVED (see midi_bridge note); lower = taller
  cave_height_divisor      - RESERVED; lower = deeper underworld
  use_beatgrid             - does the tradition layer drums under melody?
  aura_emission            - glow intensity (ritual fire = high)
  culture                  - metadata: civilization + instrument + era
"""

from __future__ import annotations

# ----------------------------------------------------------------- presets

ANCIENT_PRESETS = {
    "ur_lyre": {
        "label": "Lyre of Ur (Sumer)",
        "description": "Silver lyre of Puabi, ~2550 BCE. Stately heptatonic hymns; "
                       "broad processional ground with tall bull-headed resonator pillars.",
        "chunk_beats": 4,
        "surface_height_divisor": 26,
        "cave_height_divisor": 44,
        "use_beatgrid": True,
        "aura_emission": 3.4,
        "culture": "Sumer | Silver Lyre of Ur | Early Dynastic III",
    },
    "hurrian_hymn": {
        "label": "Hurrian Hymn to Nikkal",
        "description": "Oldest notated melody, Ugarit ~1400 BCE. Wide terraced plateaus "
                       "step down like the tablet's descending refrain; deep cult caves below.",
        "chunk_beats": 5,
        "surface_height_divisor": 22,
        "cave_height_divisor": 30,
        "use_beatgrid": True,
        "aura_emission": 3.8,
        "culture": "Hurrian | H6 tablet | Late Bronze Age",
    },
    "egypt_harp": {
        "label": "Arched Harp of Nebamun",
        "description": "New Kingdom Thebes. Flowing six-beat phrases sweep long dune "
                       "ridges along the Nile; tomb chambers hollow the floodplain.",
        "chunk_beats": 6,
        "surface_height_divisor": 28,
        "cave_height_divisor": 36,
        "use_beatgrid": False,
        "aura_emission": 2.9,
        "culture": "Egypt | Bow harp | New Kingdom (18th Dynasty)",
    },
    "greek_aulos": {
        "label": "Aulos of Delphi",
        "description": "Double-reed pipes driving Pythian dance. Sharp three-beat trochee "
                       "cuts switchback ravines; the oracle fissure runs beneath everything.",
        "chunk_beats": 3,
        "surface_height_divisor": 20,
        "cave_height_divisor": 24,
        "use_beatgrid": True,
        "aura_emission": 4.1,
        "culture": "Greece | Aulos | Archaic/Classical",
    },
    "guqin_seclusion": {
        "label": "Guqin in Bamboo Grove",
        "description": "Seven-string zither of the scholars. Sparse eight-beat breathing; "
                       "slides become long level ledges, harmonics float as lone spires.",
        "chunk_beats": 8,
        "surface_height_divisor": 38,
        "cave_height_divisor": 16,
        "use_beatgrid": False,
        "aura_emission": 2.2,
        "culture": "China | Guqin | Zhou/Tang literati",
    },
    "sho_gagaku": {
        "label": "Sho of the Gagaku Court",
        "description": "Seventeen-pipe mouth organ, Nara court. Sustained cluster chords "
                       "stack tiered temple plateaus; breath-cycles carve deep still caverns.",
        "chunk_beats": 7,
        "surface_height_divisor": 30,
        "cave_height_divisor": 22,
        "use_beatgrid": True,
        "aura_emission": 3.1,
        "culture": "Japan | Sho | Gagaku (Tang-derived)",
    },
    "siku_andes": {
        "label": "Siku of Titicaca",
        "description": "Interlocking panpipes played in dialogue pairs. Five-beat hocketing "
                       "terraces the altiplano in stepped agriculture bands; wind gods echo below.",
        "chunk_beats": 5,
        "surface_height_divisor": 18,
        "cave_height_divisor": 40,
        "use_beatgrid": True,
        "aura_emission": 3.7,
        "culture": "Andes | Siku/Zampona | Tiwanaku-Inca",
    },
    "kora_mande": {
        "label": "Kora of the Griots",
        "description": "Twenty-one string harp-lute, Mali empires. Rapid two-beat ostinato "
                       "weaves dense braided ridges; praise-song gold veins run through bedrock.",
        "chunk_beats": 2,
        "surface_height_divisor": 17,
        "cave_height_divisor": 34,
        "use_beatgrid": True,
        "aura_emission": 4.4,
        "culture": "Mande | Kora | Mali/Songhai griot tradition",
    },
    "crwth_drone": {
        "label": "Crwth of the Bards",
        "description": "Six-string bowed lyre of Welsh law. Open-fifth drones lay broad flat "
                       "moors crossed by eisteddfod causeways; bardic crypts sleep underneath.",
        "chunk_beats": 6,
        "surface_height_divisor": 32,
        "cave_height_divisor": 26,
        "use_beatgrid": True,
        "aura_emission": 2.7,
        "culture": "Wales | Crwth | Medieval bardic",
    },
    "lur_fjord": {
        "label": "Lur Across the Fjord",
        "description": "Bronze-age curved horns calling valley to valley. Long sustained "
                       "eighth-beat calls raise sheer cliff walls; answer-hollows sit far below.",
        "chunk_beats": 8,
        "surface_height_divisor": 15,
        "cave_height_divisor": 42,
        "use_beatgrid": False,
        "aura_emission": 4.8,
        "culture": "Nordic | Bronze Lur | Nordic Bronze Age",
    },
    "saman_vedic": {
        "label": "Saman Chant of the Rigs",
        "description": "Vedic three-tone chant on rolling syllables. Triple-beat liturgy "
                       "folds the ground into mandala rings around a silent yajna pit.",
        "chunk_beats": 3,
        "surface_height_divisor": 27,
        "cave_height_divisor": 20,
        "use_beatgrid": True,
        "aura_emission": 3.5,
        "culture": "Vedic India | Samaveda | Late Vedic",
    },
    "hydraulis_arena": {
        "label": "Hydraulis of the Arena",
        "description": "Water organ of Heron, Roman spectacles. Pounding four-beat air "
                       "pressure stamps amphitheatre terraces; aqueduct cisterns tunnel wide.",
        "chunk_beats": 4,
        "surface_height_divisor": 21,
        "cave_height_divisor": 32,
        "use_beatgrid": True,
        "aura_emission": 4.0,
        "culture": "Rome | Hydraulis water organ | Imperial",
    },
}

# ----------------------------------------------------------------- dressing kinds
# New prop archetypes mapped onto existing terrain tags (peak/ridge/valley/path/slope)

ANCIENT_DRESSING_KINDS = {
    "sun_disc": {
        "label": "Sun Disc",
        "on": "peak",
        "density": 0.22,
        "scale": (0.45, 0.95),
        "emissive": True,
        "colour": (0.79, 0.66, 0.42),          # gold #C9A86A
        "description": "Gilded solar disc crowning summits - Egypt/Hurrian royal icon.",
    },
    "oracle_stone": {
        "label": "Oracle Stone",
        "on": "ridge",
        "density": 0.14,
        "scale": (0.9, 2.4),
        "emissive": True,
        "colour": (0.43, 0.35, 0.65),          # iris #6E5AA6
        "description": "Fissured basalt stele on ridgelines, faintly glowing with vapour.",
    },
    "papyrus_reed": {
        "label": "Papyrus Reed",
        "on": "valley",
        "density": 0.48,
        "scale": (0.25, 0.7),
        "emissive": False,
        "colour": (0.55, 0.62, 0.34),
        "description": "Nile reed clusters softening low ground and riverbanks.",
    },
    "processional_mark": {
        "label": "Processional Mark",
        "on": "path",
        "density": 0.30,
        "scale": (0.2, 0.5),
        "emissive": True,
        "colour": (0.91, 0.78, 0.81),          # sakura milk #E7C9CE
        "description": "Rose-chalk waymarkers lining ritual routes between stations.",
    },
    "lotus_bloom": {
        "label": "Lotus Bloom",
        "on": "slope",
        "density": 0.30,
        "scale": (0.18, 0.42),
        "emissive": True,
        "colour": (0.84, 0.66, 0.69),          # dusty rose #D6A9B0
        "description": "Half-open stone lotus on transitions - rebirth motif.",
    },
}

# ----------------------------------------------------------------- dressing styles
# Recipes pairing the new kinds with the classic five (moss/crystal/pillar/songstone/bloom)

ANCIENT_DRESSING_STYLES = {
    "ur_royal": {
        "label": "Ur Royal Tomb",
        "dressing": ["sun_disc", "chime_pillar", "songstone"],
        "magic": ["harmonic_rings", "ground_glow"],
        "description": "Gold discs on peaks, lyre-pillars on ridges, grave-glow beneath. Sumer.",
    },
    "ugarit_tablet": {
        "label": "Ugarit Tablet Terrace",
        "dressing": ["oracle_stone", "sun_disc", "songstone"],
        "magic": ["aurora_veil", "cadence_pool"],
        "description": "Steles step down the hymn's refrain above a reflecting basin. Hurrian.",
    },
    "theban_nile": {
        "label": "Theban Nilebank",
        "dressing": ["papyrus_reed", "lotus_bloom", "sun_disc"],
        "magic": ["motif_wisps", "cadence_pool"],
        "description": "Reeds and lotus line dunes; sun discs crown the harp's horizon. Egypt.",
    },
    "delphic_ravine": {
        "label": "Delphic Ravine",
        "dressing": ["oracle_stone", "note_bloom", "resonance_crystal"],
        "magic": ["aurora_veil", "ground_glow"],
        "description": "Vapour-glowing steles guard the aulos switchbacks. Greece.",
    },
    "bamboo_seclusion": {
        "label": "Bamboo Seclusion",
        "dressing": ["papyrus_reed", "moss_cluster"],
        "magic": ["motif_wisps"],
        "description": "Minimal: reeds and moss only, one wisp trail. Guqin restraint.",
    },
    "gagaku_court": {
        "label": "Gagaku Court Tier",
        "dressing": ["lotus_bloom", "chime_pillar", "processional_mark"],
        "magic": ["harmonic_rings", "aurora_veil"],
        "description": "Tiered plateaus ringed with marks; chord-rings overhead. Japan court.",
    },
    "titicaca_terrace": {
        "label": "Titicaca Terraces",
        "dressing": ["processional_mark", "moss_cluster", "resonance_crystal"],
        "magic": ["motif_wisps", "ground_glow"],
        "description": "Hocket-marks stair the siku terraces; wind-light from below. Andes.",
    },
    "mande_goldvein": {
        "label": "Mande Goldvein",
        "dressing": ["songstone", "sun_disc", "note_bloom"],
        "magic": ["harmonic_rings", "motif_wisps"],
        "description": "Kora ostinato braid with praise-gold discs flashing. Mali.",
    },
    "bardic_moors": {
        "label": "Bardic Moors",
        "dressing": ["moss_cluster", "processional_mark", "oracle_stone"],
        "magic": ["ground_glow", "aurora_veil"],
        "description": "Drone-flat moor with causeway marks and watching stones. Wales.",
    },
    "fjord_calls": {
        "label": "Fjord Call Walls",
        "dressing": ["resonance_crystal", "oracle_stone"],
        "magic": ["aurora_veil", "harmonic_rings"],
        "description": "Sheer lur-walls with answering crystals across the water. Nordic.",
    },
    "vedic_mandala": {
        "label": "Vedic Mandala Rings",
        "dressing": ["lotus_bloom", "processional_mark", "songstone"],
        "magic": ["harmonic_rings", "cadence_pool"],
        "description": "Chant-folded rings around a still yajna pool. Vedic.",
    },
    "arena_aqueduct": {
        "label": "Arena Aqueduct",
        "dressing": ["chime_pillar", "processional_mark", "moss_cluster"],
        "magic": ["cadence_pool", "ground_glow"],
        "description": "Organ-pressure terraces fed by singing cisterns below. Rome.",
    },
}

# ----------------------------------------------------------------- tandem pairs
# preset_id -> (surreal COMPOSE_STYLE, plan_kind, dressing_style)

ANCIENT_TANDEM_PAIRS = {
    "ur_lyre":           ("BYZANTINE_BASILICA",   "castle",       "ur_royal"),
    "hurrian_hymn":      ("BYZANTINE_BASILICA",   "zen_temple",   "ugarit_tablet"),
    "egypt_harp":        ("MOORISH_COURTYARD",    "zen_temple",   "theban_nile"),
    "greek_aulos":       ("ROMANESQUE_APSE",      "village",      "delphic_ravine"),
    "guqin_seclusion":   ("ZEN_SHRINE",           "zen_roji",     "bamboo_seclusion"),
    "sho_gagaku":        ("ASIAN_CITY_RECURSIVE", "zen_temple",   "gagaku_court"),
    "siku_andes":        ("BRUTALIST_PLAZA",      "motte_bailey", "titicaca_terrace"),
    "kora_mande":        ("ART_NOUVEAU",          "village",      "mande_goldvein"),
    "crwth_drone":       ("GOTHIC_CLOISTER",      "castle",       "bardic_moors"),
    "lur_fjord":         ("WESTERN_CASTLE",       "motte_bailey", "fjord_calls"),
    "saman_vedic":       ("ROMANESQUE_CLOISTER",  "zen_roji",     "vedic_mandala"),
    "hydraulis_arena":   ("BAROQUE_CHURCH",       "grid_city",    "arena_aqueduct"),
}


def merge_into(midi_bridge_mod=None, terrain_dressing_mod=None, tandem_mod=None):
    """Idempotent merge into live modules. Safe to call repeatedly."""
    if midi_bridge_mod is not None:
        try:
            base = dict(getattr(midi_bridge_mod, "DEFAULT_PRESETS", {}))
            for k, v in ANCIENT_PRESETS.items():
                if k not in base:
                    base[k] = dict(v)
            midi_bridge_mod.DEFAULT_PRESETS = base
            # invalidate any cached disk presets handled by load_presets fallback
        except Exception as exc:  # pragma: no cover
            print(f"[ancient] midi_bridge merge failed: {exc}")
    if terrain_dressing_mod is not None:
        try:
            td = terrain_dressing_mod
            kinds = dict(getattr(td, "DRESSING_KINDS", {}))
            for k, v in ANCIENT_DRESSING_KINDS.items():
                kinds.setdefault(k, dict(v))
            td.DRESSING_KINDS = kinds
            styles = dict(getattr(td, "DRESSING_STYLES", {}))
            for k, v in ANCIENT_DRESSING_STYLES.items():
                styles.setdefault(k, dict(v))
            td.DRESSING_STYLES = styles
        except Exception as exc:  # pragma: no cover
            print(f"[ancient] terrain_dressing merge failed: {exc}")
    if tandem_mod is not None:
        try:
            table = dict(getattr(tandem_mod, "MELODIA_TO_SURREAL", {}))
            for k, v in ANCIENT_TANDEM_PAIRS.items():
                table.setdefault(k, tuple(v))
            tandem_mod.MELODIA_TO_SURREAL = table
        except Exception as exc:  # pragma: no cover
            print(f"[ancient] tandem merge failed: {exc}")


if __name__ == "__main__":
    import os, sys
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_here, "..", ".."))  # BlenderAddons root
    import melodia_studio.midi_bridge as mb  # type: ignore
    import melodia_studio.terrain_dressing as td  # type: ignore
    import melodia_studio.tandem_bridge as tb  # type: ignore
    merge_into(mb, td, tb)
    print("presets:", len(mb.DEFAULT_PRESETS))
    print("styles:", len(td.DRESSING_STYLES))
    print("kinds:", len(td.DRESSING_KINDS))
    print("tandem:", len(tb.MELODIA_TO_SURREAL))
