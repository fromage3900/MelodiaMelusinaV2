"""Deterministic musical world generation for Melodia Melusina.

This module is deliberately engine-agnostic.  It owns the *identity* of a
Resonant World (seed, mode, harmonic geography, stable chunk/voxel addresses)
and the data needed to hand a chunk to Unreal PCG.  It does not own narrative,
combat, inventory, or save writes.

The design goal is "Minecraft, but the thing you build is a composition":
terrain is made from resonant voxel material, biomes are musical modes,
landmarks are instruments, and player-built note structures can be scored as a
small arrangement.  Every result is derived from an explicit seed and
coordinate so a world can be streamed, regenerated, and patched without
storing the whole world.

Run directly for an inspection manifest:

    python Content/Python/resonant_world_generator.py --seed 3900 --radius 1
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping


GENERATOR_VERSION = "resonant_world_v1"
GRID_SIZE = 16
VOXEL_SIZE_CM = 1_600
WORLD_PARTITION_CHUNK_SIZE_CM = 25_600
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True)
class ModeProfile:
    """A scale plus the world grammar it unlocks."""

    mode_id: str
    display_name: str
    intervals: tuple[int, ...]
    region_names: tuple[str, ...]
    surface_materials: tuple[str, ...]
    timbres: tuple[str, ...]
    mood: str


MODE_LIBRARY: dict[str, ModeProfile] = {
    "ionian": ModeProfile(
        "ionian",
        "Ionian Bloom",
        (0, 2, 4, 5, 7, 9, 11),
        ("sunlit_court", "ribbon_meadow", "glass_orchard", "wind_shelf", "bell_garden", "rose_tide", "quiet_void"),
        ("rootstone", "sunclay", "sunglass", "windstone", "bellmoss", "rosetide", "silence_slate"),
        ("harp", "piano", "music_box", "bell", "choir", "glass", "drone"),
        "clear, welcoming, ceremonial",
    ),
    "dorian": ModeProfile(
        "dorian",
        "Dorian Moon",
        (0, 2, 3, 5, 7, 9, 10),
        ("moon_court", "moss_rim", "silver_grove", "wind_shelf", "bell_marsh", "lunar_tide", "hush_basin"),
        ("moonstone", "mossclay", "silverglass", "windstone", "bellmoss", "lunartide", "hush_slate"),
        ("harp", "celesta", "wood_flute", "bell", "alto_choir", "glass", "bowed_drone"),
        "tender, nocturnal, searching",
    ),
    "lydian": ModeProfile(
        "lydian",
        "Lydian Sky",
        (0, 2, 4, 6, 7, 9, 11),
        ("sky_court", "cloud_meadow", "star_glass", "high_wind", "chime_garden", "aurora_tide", "blue_void"),
        ("skystone", "cloudclay", "starglass", "highwind", "chime_moss", "auroratide", "blue_slate"),
        ("harp", "synth_bell", "flute", "chime", "head_voice", "crystal", "sub_drone"),
        "weightless, radiant, uncanny",
    ),
    "aeolian": ModeProfile(
        "aeolian",
        "Aeolian Dusk",
        (0, 2, 3, 5, 7, 8, 10),
        ("dusk_court", "bramble_rim", "smoke_grove", "rain_shelf", "hollow_garden", "deep_tide", "starless_basin"),
        ("duskstone", "brambleclay", "smokeglass", "rainstone", "hollowmoss", "deeptide", "starless_slate"),
        ("felt_piano", "plucked_string", "low_flute", "iron_bell", "whisper_choir", "dark_glass", "sub_drone"),
        "melancholic, intimate, deep",
    ),
    "phrygian": ModeProfile(
        "phrygian",
        "Phrygian Ember",
        (0, 1, 3, 5, 7, 8, 10),
        ("ember_court", "ash_rim", "cinder_grove", "heat_shelf", "iron_garden", "lava_tide", "black_basin"),
        ("emberstone", "ashclay", "cinderglass", "heatstone", "ironmoss", "lavatide", "black_slate"),
        ("prepared_piano", "hammered_string", "reed", "iron_bell", "ritual_choir", "obsidian_glass", "granular_drone"),
        "ritual, volcanic, defiant",
    ),
}


LANDMARK_GRAMMARS = {
    "ResonanceCathedral": {"role": "nave_landmark", "instrument": "organ", "scale": "grand"},
    "ArpeggioBridge": {"role": "traversal_landmark", "instrument": "marimba", "scale": "rising"},
    "BellTreeGarden": {"role": "branch_landmark", "instrument": "bell", "scale": "orbital"},
    "XylophoneTrail": {"role": "walkable_instrument_landmark", "instrument": "xylophone", "scale": "stepped"},
    "CrystalHarpGrove": {"role": "pitched_string_landmark", "instrument": "harp", "scale": "arpeggiated"},
    "MotifShrine": {"role": "motif_landmark", "instrument": "choir", "scale": "cadential"},
}


@dataclass(frozen=True)
class WorldMovement:
    """An authored ecology that a deterministic world can arrange and remix.

    A movement is intentionally broader than a biome.  It is the contract
    between musical geography, PCG art direction, wardrobe expression, VFX,
    NPC population, and the player-facing verb that changes the place.  The
    asset fragments are queries for the companion asset atlas; they are not
    runtime asset loads.
    """

    movement_id: str
    display_name: str
    description: str
    mode_affinities: tuple[str, ...]
    world_verb: str
    resonant_form_id: str
    style_axes: tuple[str, ...]
    pcg_asset_fragments: tuple[str, ...]
    vfx_systems: tuple[str, ...]
    water_profiles: tuple[str, ...]
    outfit_archetypes: tuple[str, ...]
    npc_zones: tuple[str, ...]
    musical_asset_fragments: tuple[str, ...]
    quantum_objective: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "movement_id": self.movement_id,
            "display_name": self.display_name,
            "description": self.description,
            "mode_affinities": list(self.mode_affinities),
            "world_verb": self.world_verb,
            "resonant_form_id": self.resonant_form_id,
            "style_axes": list(self.style_axes),
            "pcg_asset_fragments": list(self.pcg_asset_fragments),
            "vfx_systems": list(self.vfx_systems),
            "water_profiles": list(self.water_profiles),
            "outfit_archetypes": list(self.outfit_archetypes),
            "npc_zones": list(self.npc_zones),
            "musical_asset_fragments": list(self.musical_asset_fragments),
            "quantum_objective": list(self.quantum_objective),
        }


# These are deliberately authored combinations of the project's current
# assets.  The generator can remix them, but it never invents an unreviewed
# Unreal asset path.  A future movement is a data addition, not a rewrite of
# the chunk algorithm.
WORLD_MOVEMENT_LIBRARY: dict[str, WorldMovement] = {
    "petal_cantata": WorldMovement(
        "petal_cantata",
        "Petal Cantata",
        "A healing garden whose flowers open in the key of the player's current voicing.",
        ("ionian", "dorian"),
        "bloom",
        "ResonantForm_PetalRipple",
        ("resonance", "lilt"),
        ("PCG/Sakura", "PCG_Nikki_PhyllotaxisGarden", "PCG_Nikki_MandalaBloom", "PCG_Hero_TeaGarden", "PCG_MeadowBloom"),
        ("NS_Nikki_FlowerPetals", "NS_Nikki_SparkleDrift", "NS_Nikki_FabricTrail"),
        ("pond_shrine",),
        ("SakuraDreamer",),
        ("SakuraGrove", "HealingShrine", "PetalPlaza", "DreamGarden"),
        ("MIDI", "128BPM", "BellTreeGarden", "Piano"),
        ("outfit_synergy", "walkable_beauty", "gentle_contrast", "motif_continuity"),
    ),
    "star_loom": WorldMovement(
        "star_loom",
        "Star Loom",
        "A cosmic textile of observatories, floating motes, and constellations that can be rewoven.",
        ("lydian", "dorian"),
        "weave",
        "ResonantForm_StarWeave",
        ("resonance", "orbit"),
        ("PCG/Cosmic", "PCG_WP_SpaceCathedral", "PCG_WP_CosmicOrrery", "PCG_Nikki_DreamStones"),
        ("NS_Nikki_FloatingMotes", "NS_Nikki_WishBurst", "NS_Nikki_SparkleDrift"),
        (),
        ("CosmicWeaver",),
        ("StarObservatory", "CosmicLibrary", "VoidLoom", "AstralNexus"),
        ("MIDI", "144", "CrystalHarpGrove", "MusicalOrnament"),
        ("outfit_synergy", "route_variety", "visual_novelty", "star_density"),
    ),
    "liquid_cathedral": WorldMovement(
        "liquid_cathedral",
        "Liquid Cathedral",
        "A water-born sanctuary where hair, rivers, and crystal strings answer the same pulse.",
        ("dorian", "lydian", "aeolian"),
        "conduct",
        "ResonantForm_TidalConduction",
        ("resonance", "flow"),
        ("PCG_Hero_CrystalHarpGrove", "PCG_Hero_ResonanceCathedral", "PCG/BaroqueGrotto", "PCG_WP_BaroqueGrotto"),
        ("NS_Melusina_ChaosDrift", "NS_Melusina_EntropyDust", "NS_Nikki_FloatingMotes"),
        ("pond_shrine", "melusina_hair", "river_clear", "waterfall_sheet"),
        ("Melusina",),
        ("HealingShrine", "CrystalHarpGrove", "RainShelf"),
        ("MIDI", "CrystalHarpGrove", "Melusina", "Water"),
        ("outfit_synergy", "flow_continuity", "audio_reactivity", "safe_traversal"),
    ),
    "cadence_cathedral": WorldMovement(
        "cadence_cathedral",
        "Cadence Cathedral",
        "The proof-space of Melodia: architecture, bridges, bells, and piano voxels become one playable score.",
        ("ionian", "lydian", "phrygian"),
        "compose",
        "ResonantForm_CadenceBuild",
        ("resonance", "cadence"),
        ("PCG_Hero_ResonanceCathedral", "PCG_Hero_ArpeggioBridge", "PCG_Hero_BellTreeGarden", "PCG_Hero_XylophoneTrail", "PCG_Hero_CrystalHarpGrove"),
        ("NS_Nikki_SparkleDrift", "NS_Nikki_WishBurst"),
        (),
        ("Melusina",),
        ("ResonanceCathedral", "ArpeggioBridge", "BellTreeGarden", "XylophoneTrail", "CrystalHarpGrove"),
        ("Piano", "MIDI", "MusicalOrnamentKitbash", "SM_Orn_", "PCG_Musical"),
        ("arrangement_quality", "motif_continuity", "route_variety", "landmark_coverage"),
    ),
    "mirage_gala": WorldMovement(
        "mirage_gala",
        "Mirage Gala",
        "A wind-cut theatre of ribbons, dunes, and reflective paths where movement itself writes the phrase.",
        ("lydian", "aeolian", "phrygian"),
        "drift",
        "ResonantForm_MirageStep",
        ("cadence", "lilt"),
        ("PCG_MeadowBloom", "PCG_SplinePath", "PCG_WP_Escher", "PCG_WP_Cyberpunk", "PCG_Nikki"),
        ("NS_Nikki_FabricTrail", "NS_Nikki_SparkleDrift", "NS_Nikki_FloatingMotes"),
        (),
        ("MirageDancer",),
        ("TwilightDunes", "WindTemple", "MirageOasis", "ZephyrPeak"),
        ("MIDI", "180", "ankle_bells", "MusicalOrnament"),
        ("outfit_synergy", "route_variety", "traversal_safety", "silhouette_readability"),
    ),
    "dissonant_expanse": WorldMovement(
        "dissonant_expanse",
        "Dissonant Expanse",
        "A black-basin frontier where unresolved notes become portals, ruins, and strange but survivable routes.",
        ("aeolian", "phrygian"),
        "resolve",
        "ResonantForm_DissonanceResolve",
        ("tension", "resonance"),
        ("PCG_WP_Escher", "PCG_WP_Cyberpunk", "PCG_WP_BaroqueGrotto", "PCG_GardenRuins", "PCG_WP_SpaceCathedral"),
        ("NS_Melusina_EntropyDust", "NS_Melusina_ChaosDrift", "NS_Nikki_WishBurst"),
        ("river_clear", "waterfall_sheet"),
        ("CosmicWeaver", "MirageDancer"),
        ("VoidLoom", "AstralNexus", "TwilightDunes"),
        ("UmbralNocturne", "MIDI", "MusicalOrnament"),
        ("constraint_satisfaction", "route_variety", "controlled_tension", "safe_traversal"),
    ),
}


WORLD_MOVEMENT_ORDER = tuple(WORLD_MOVEMENT_LIBRARY)


# These are the existing authored hero grammars in the scale-world PCG
# pipeline.  The generator selects them; it never clones or rewrites them.
PCG_GRAPH_BY_LANDMARK = {
    "ResonanceCathedral": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral",
    "ArpeggioBridge": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge",
    "BellTreeGarden": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden",
    "XylophoneTrail": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_XylophoneTrail",
    "CrystalHarpGrove": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove",
    # A motif shrine is a controlled variation of the cathedral grammar until
    # it earns a dedicated authored PCG graph.
    "MotifShrine": "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral",
}


def _digest(seed: int, *parts: object) -> bytes:
    payload = "|".join((str(int(seed)), *(str(part) for part in parts))).encode("utf-8")
    return hashlib.sha256(payload).digest()


def stable_int(seed: int, *parts: object) -> int:
    """Return a positive deterministic integer for a world coordinate."""
    return int.from_bytes(_digest(seed, *parts)[:8], "little")


def stable_float(seed: int, *parts: object) -> float:
    return stable_int(seed, *parts) / float(2**64 - 1)


def shared_border_signature(seed: int, ax: int, ay: int, bx: int, by: int) -> str:
    """Return an order-independent identity for one streamed chunk edge."""
    first, second = sorted(((int(ax), int(ay)), (int(bx), int(by))))
    return hashlib.sha256(
        f"{int(seed)}|{first[0]}|{first[1]}|{second[0]}|{second[1]}|{GENERATOR_VERSION}".encode("utf-8")
    ).hexdigest()[:16]


@dataclass(frozen=True)
class WorldConfig:
    world_seed: int
    root_pitch_class: int
    mode_id: str
    bpm: int
    beats_per_bar: int
    motif_id: str
    generator_version: str = GENERATOR_VERSION
    movement_id: str = "cadence_cathedral"

    @property
    def mode(self) -> ModeProfile:
        return MODE_LIBRARY[self.mode_id]

    @property
    def root_note(self) -> str:
        return NOTE_NAMES[self.root_pitch_class]

    @classmethod
    def from_seed(
        cls,
        world_seed: int,
        *,
        root_pitch_class: int | None = None,
        mode_id: str | None = None,
        bpm: int | None = None,
    ) -> "WorldConfig":
        seed = int(world_seed)
        modes = tuple(MODE_LIBRARY)
        chosen_root = stable_int(seed, "world", "root") % len(NOTE_NAMES) if root_pitch_class is None else int(root_pitch_class) % 12
        chosen_mode = modes[stable_int(seed, "world", "mode") % len(modes)] if mode_id is None else str(mode_id)
        if chosen_mode not in MODE_LIBRARY:
            raise ValueError(f"unknown mode_id: {chosen_mode}")
        chosen_bpm = 72 + stable_int(seed, "world", "tempo") % 89 if bpm is None else max(40, min(220, int(bpm)))
        motif = hashlib.sha256(_digest(seed, "world", "motif")).hexdigest()[:10]
        compatible_movements = tuple(
            movement_id
            for movement_id in WORLD_MOVEMENT_ORDER
            if chosen_mode in WORLD_MOVEMENT_LIBRARY[movement_id].mode_affinities
        ) or WORLD_MOVEMENT_ORDER
        movement_id = compatible_movements[stable_int(seed, "world", "movement") % len(compatible_movements)]
        return cls(seed, chosen_root, chosen_mode, chosen_bpm, 4, motif, GENERATOR_VERSION, movement_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "world_seed": self.world_seed,
            "root_note": self.root_note,
            "root_pitch_class": self.root_pitch_class,
            "mode_id": self.mode_id,
            "mode_name": self.mode.display_name,
            "scale_intervals": list(self.mode.intervals),
            "bpm": self.bpm,
            "beats_per_bar": self.beats_per_bar,
            "motif_id": self.motif_id,
            "generator_version": self.generator_version,
            "mood": self.mode.mood,
            "movement_id": self.movement_id,
            "movement": WORLD_MOVEMENT_LIBRARY[self.movement_id].to_dict(),
        }


def movement_for_chunk(config: WorldConfig, chunk_x: int, chunk_y: int) -> WorldMovement:
    """Select a stable movement for a chunk without changing the world seed.

    The origin anchors the world's headline movement.  Nearby chunks are
    allowed to become companion movements, which creates a readable journey
    instead of a single biome stretched forever.  This is a macro decision;
    voxel generation remains deterministic and local.
    """
    if (int(chunk_x), int(chunk_y)) == (0, 0):
        return WORLD_MOVEMENT_LIBRARY[config.movement_id]
    mode = config.mode_id
    candidates = [
        movement for movement in WORLD_MOVEMENT_LIBRARY.values()
        if mode in movement.mode_affinities
    ]
    if not candidates:
        candidates = list(WORLD_MOVEMENT_LIBRARY.values())
    index = stable_int(config.world_seed, "movement", chunk_x, chunk_y) % len(candidates)
    return candidates[index]


def region_for_chunk(config: WorldConfig, chunk_x: int, chunk_y: int) -> dict[str, Any]:
    """Assign a harmonic region; repeated regions are expected and useful."""
    if (int(chunk_x), int(chunk_y)) == (0, 0):
        degree = 0
    else:
        degree = stable_int(config.world_seed, "region", chunk_x, chunk_y) % 7
    degree_name = ("tonic", "supertonic", "mediant", "subdominant", "dominant", "submediant", "leading")[degree]
    mode = config.mode
    return {
        "degree": degree,
        "degree_name": degree_name,
        "region_id": mode.region_names[degree],
        "surface_material": mode.surface_materials[degree],
        "timbre": mode.timbres[degree],
        "pitch_class": (config.root_pitch_class + mode.intervals[degree]) % 12,
    }


def landmark_for_chunk(config: WorldConfig, chunk_x: int, chunk_y: int) -> str | None:
    """Keep a readable authored proof ring, then open into sparse procedural landmarks."""
    coord = (int(chunk_x), int(chunk_y))
    authored_ring = {
        (0, 0): "ResonanceCathedral",
        (1, 0): "ArpeggioBridge",
        (-1, 0): "BellTreeGarden",
        (0, 1): "XylophoneTrail",
        (1, 1): "CrystalHarpGrove",
    }
    if coord in authored_ring:
        return authored_ring[coord]
    roll = stable_int(config.world_seed, "landmark", *coord) % 23
    if roll == 0:
        return "MotifShrine"
    if roll == 7:
        return "BellTreeGarden"
    if roll == 13:
        return "ArpeggioBridge"
    return None


def edge_anchor(config: WorldConfig, chunk_x: int, chunk_y: int, side: str) -> dict[str, Any]:
    """Return a seam-safe anchor shared by both chunks on an edge."""
    neighbors = {
        "west": (chunk_x - 1, chunk_y),
        "east": (chunk_x + 1, chunk_y),
        "south": (chunk_x, chunk_y - 1),
        "north": (chunk_x, chunk_y + 1),
    }
    if side not in neighbors:
        raise ValueError(f"unknown edge side: {side}")
    nx, ny = neighbors[side]
    signature = shared_border_signature(config.world_seed, chunk_x, chunk_y, nx, ny)
    transverse = 2 + stable_int(config.world_seed, "anchor", signature) % (GRID_SIZE - 4)
    if side in {"west", "east"}:
        local_x, local_y = (0 if side == "west" else GRID_SIZE - 1), transverse
    else:
        local_x, local_y = transverse, (0 if side == "south" else GRID_SIZE - 1)
    return {
        "side": side,
        "signature": signature,
        "local_x": local_x,
        "local_y": local_y,
        "clearance_voxels": 2,
        "route_note_degree": stable_int(config.world_seed, "route-note", signature) % 7,
    }


def pcg_binding_for_chunk(
    region: Mapping[str, Any],
    landmark_id: str | None,
    movement: WorldMovement | None = None,
) -> dict[str, Any]:
    """Map a musical chunk decision to an existing authored PCG grammar."""
    movement = movement or WORLD_MOVEMENT_LIBRARY["cadence_cathedral"]
    return {
        "graph_path": PCG_GRAPH_BY_LANDMARK.get(landmark_id) if landmark_id else None,
        "hero_slot_assignments": [landmark_id] if landmark_id else [],
        "region_id": str(region["region_id"]),
        "movement_id": movement.movement_id,
        "movement_world_verb": movement.world_verb,
        "movement_pcg_asset_fragments": list(movement.pcg_asset_fragments),
        "data_layer": "DL_Musical_HeroGameplay" if landmark_id else "DL_Musical_BiomeDressing",
        "exclude_interactive_from_hlod": bool(landmark_id),
        "audio_palette_bus": "MPC_Melodia_Palette",
        "generator_version": GENERATOR_VERSION,
    }


def surface_height(config: WorldConfig, chunk_x: int, chunk_y: int, local_x: int, local_y: int) -> int:
    """Generate a compact voxel column height without mutable random state."""
    gx = int(chunk_x) * GRID_SIZE + int(local_x)
    gy = int(chunk_y) * GRID_SIZE + int(local_y)
    base = 2 + stable_int(config.world_seed, "height", gx // 4, gy // 4) % 4
    detail = stable_int(config.world_seed, "height-detail", gx, gy) % 3
    degree = (gx + (2 * gy) + stable_int(config.world_seed, "terrain-degree", chunk_x, chunk_y)) % 7
    harmonic_lift = 1 if degree in {0, 4} else 0
    return int(min(7, base + detail + harmonic_lift))


@dataclass(frozen=True)
class ResonantVoxel:
    cell_id: str
    local_x: int
    local_y: int
    z: int
    material_id: str
    pitch_class: int
    pitch_name: str
    scale_degree: int
    voice: str
    timbre: str
    energy: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def voxel_at(config: WorldConfig, chunk_x: int, chunk_y: int, local_x: int, local_y: int, z: int) -> ResonantVoxel:
    """Derive one voxel.  Air is represented explicitly for editor previews."""
    local_x, local_y, z = int(local_x), int(local_y), int(z)
    if not 0 <= local_x < GRID_SIZE or not 0 <= local_y < GRID_SIZE:
        raise ValueError("local voxel coordinates must be within the chunk grid")
    if not 0 <= z <= 7:
        raise ValueError("prototype voxel z must be in the 0..7 preview band")
    region = region_for_chunk(config, chunk_x, chunk_y)
    height = surface_height(config, chunk_x, chunk_y, local_x, local_y)
    gx = int(chunk_x) * GRID_SIZE + local_x
    gy = int(chunk_y) * GRID_SIZE + local_y
    degree = (gx + (2 * gy) + region["degree"]) % 7
    pitch_class = (config.root_pitch_class + config.mode.intervals[degree]) % 12
    if z > height:
        material = "air"
        voice = "silence"
        timbre = "silence"
        energy = 0
    elif z == height:
        material = config.mode.surface_materials[degree]
        voice = "melody" if degree in {0, 2, 4} else "harmony"
        timbre = config.mode.timbres[degree]
        energy = 60 + stable_int(config.world_seed, "energy", gx, gy) % 41
    elif z == 0:
        material = "rootstone"
        voice = "bass"
        timbre = "drone"
        energy = 35 + stable_int(config.world_seed, "energy", gx, gy, z) % 26
    else:
        material = "echo_clay" if (z + degree) % 2 else "resonant_silt"
        voice = "harmony"
        timbre = region["timbre"]
        energy = 20 + stable_int(config.world_seed, "energy", gx, gy, z) % 31
    cell_id = f"{GENERATOR_VERSION}:{int(chunk_x)},{int(chunk_y)}:{local_x},{local_y},{z}"
    return ResonantVoxel(
        cell_id,
        local_x,
        local_y,
        z,
        material,
        pitch_class,
        NOTE_NAMES[pitch_class],
        degree,
        voice,
        timbre,
        int(energy),
    )


def iter_chunk_voxels(config: WorldConfig, chunk_x: int, chunk_y: int, *, include_air: bool = False) -> Iterator[ResonantVoxel]:
    for local_y in range(GRID_SIZE):
        for local_x in range(GRID_SIZE):
            height = surface_height(config, chunk_x, chunk_y, local_x, local_y)
            for z in range(8):
                voxel = voxel_at(config, chunk_x, chunk_y, local_x, local_y, z)
                if include_air or voxel.z <= height:
                    yield voxel


@dataclass(frozen=True)
class ResonantEdit:
    """A compact persistent edit: the world is regenerated, then this is applied."""

    chunk_x: int
    chunk_y: int
    local_x: int
    local_y: int
    z: int
    material_id: str
    pitch_class: int
    timbre: str
    intent_id: str

    @property
    def cell_id(self) -> str:
        return f"{GENERATOR_VERSION}:{self.chunk_x},{self.chunk_y}:{self.local_x},{self.local_y},{self.z}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cell_id"] = self.cell_id
        return data


def arrangement_score(edits: Iterable[ResonantEdit], config: WorldConfig) -> dict[str, Any]:
    """Score a player-built note structure as an encouraging arrangement, not a fail state."""
    notes = sorted((edit for edit in edits if edit.material_id not in {"air", "silence"}), key=lambda edit: (edit.chunk_y, edit.chunk_x, edit.z, edit.local_y, edit.local_x))
    unique: dict[str, ResonantEdit] = {note.cell_id: note for note in notes}
    notes = list(unique.values())
    allowed_pitch_classes = {
        (config.root_pitch_class + interval) % 12 for interval in config.mode.intervals
    }
    consonant = 0
    tension = 0
    for left, right in zip(notes, notes[1:]):
        left_is_diatonic = left.pitch_class % 12 in allowed_pitch_classes
        right_is_diatonic = right.pitch_class % 12 in allowed_pitch_classes
        if left_is_diatonic and right_is_diatonic:
            consonant += 1
        else:
            tension += 1
    raw = 50 + (consonant * 8) - (tension * 2)
    score = max(0, min(100, raw if notes else 0))
    return {
        "score": score,
        "note_count": len(notes),
        "consonant_transitions": consonant,
        "tension_transitions": tension,
        "mode_id": config.mode_id,
        "root_note": config.root_note,
        "interpretation": (
            "a quiet fragment waiting for another voice" if not notes else
            "a stable refrain" if score >= 60 else
            "a searching phrase" if score >= 45 else
            "a beautiful dissonance"
        ),
    }


def chunk_manifest(config: WorldConfig, chunk_x: int, chunk_y: int, *, include_voxels: bool = False) -> dict[str, Any]:
    region = region_for_chunk(config, chunk_x, chunk_y)
    landmark_id = landmark_for_chunk(config, chunk_x, chunk_y)
    movement = movement_for_chunk(config, chunk_x, chunk_y)
    manifest: dict[str, Any] = {
        "chunk_x": int(chunk_x),
        "chunk_y": int(chunk_y),
        "world_partition_origin_cm": [int(chunk_x) * WORLD_PARTITION_CHUNK_SIZE_CM, int(chunk_y) * WORLD_PARTITION_CHUNK_SIZE_CM, 0],
        "voxel_size_cm": VOXEL_SIZE_CM,
        "grid_size": GRID_SIZE,
        "stable_seed": stable_int(config.world_seed, "chunk", chunk_x, chunk_y) & 0x7FFFFFFF or 1,
        "region": region,
        "movement_id": movement.movement_id,
        "movement": movement.to_dict(),
        "landmark_id": landmark_id,
        "landmark_grammar": LANDMARK_GRAMMARS.get(landmark_id) if landmark_id else None,
        "motif_id": f"{config.motif_id}:{region['degree']}:{stable_int(config.world_seed, 'motif', chunk_x, chunk_y) % 64:02d}",
        "border_anchors": {side: edge_anchor(config, chunk_x, chunk_y, side) for side in ("west", "east", "south", "north")},
        "pcg_binding": pcg_binding_for_chunk(region, landmark_id, movement),
    }
    if include_voxels:
        manifest["voxels"] = [voxel.to_dict() for voxel in iter_chunk_voxels(config, chunk_x, chunk_y)]
    return manifest


def build_world_manifest(world_seed: int, radius: int = 1, *, include_voxels: bool = False) -> dict[str, Any]:
    config = WorldConfig.from_seed(world_seed)
    radius = max(0, int(radius))
    chunks = [
        chunk_manifest(config, chunk_x, chunk_y, include_voxels=include_voxels)
        for chunk_y in range(-radius, radius + 1)
        for chunk_x in range(-radius, radius + 1)
    ]
    result = {
        "format": "melodia_resonant_world_manifest",
        "schema_version": 1,
        "generator_version": GENERATOR_VERSION,
        "world": config.to_dict(),
        "rules": {
            "world_is_regenerated_from_seed": True,
            "player_changes_are_sparse_edits": True,
            "narrative_completion_is_external": True,
            "combat_and_save_authority_are_external": True,
            "building_is_scored_as_arrangement": True,
            "movement_is_an_authored_asset_grammar": True,
            "quantum_is_optional_async_macro_selection": True,
        },
        "chunks": chunks,
    }
    result["validation_errors"] = validate_world_manifest(result)
    result["ok"] = not result["validation_errors"]
    return result


def validate_world_manifest(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    world = manifest.get("world", {})
    if manifest.get("format") != "melodia_resonant_world_manifest":
        errors.append("format is not melodia_resonant_world_manifest")
    if world.get("mode_id") not in MODE_LIBRARY:
        errors.append("world mode_id is not registered")
    if world.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
        errors.append("world movement_id is not registered")
    chunks = manifest.get("chunks", [])
    if not isinstance(chunks, list) or not chunks:
        return errors + ["chunks must be a non-empty list"]
    by_coord = {(int(chunk["chunk_x"]), int(chunk["chunk_y"])): chunk for chunk in chunks}
    for chunk in chunks:
        x, y = int(chunk["chunk_x"]), int(chunk["chunk_y"])
        if chunk.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
            errors.append(f"chunk {x},{y} has an unregistered movement")
        if chunk.get("generator_version", GENERATOR_VERSION) not in {GENERATOR_VERSION, world.get("generator_version")}:
            errors.append(f"chunk {x},{y} has an incompatible generator version")
        anchors = chunk.get("border_anchors", {})
        for side, dx, dy, opposite in (("east", 1, 0, "west"), ("north", 0, 1, "south")):
            neighbor = by_coord.get((x + dx, y + dy))
            if not neighbor:
                continue
            own_signature = anchors.get(side, {}).get("signature")
            neighbor_signature = neighbor.get("border_anchors", {}).get(opposite, {}).get("signature")
            if own_signature != neighbor_signature:
                errors.append(f"seam signature mismatch {x},{y} {side}")
            own = anchors.get(side, {})
            other = neighbor.get("border_anchors", {}).get(opposite, {})
            if side in {"east", "west"} and own.get("local_y") != other.get("local_y"):
                errors.append(f"seam anchor mismatch {x},{y} {side}")
            if side in {"north", "south"} and own.get("local_x") != other.get("local_x"):
                errors.append(f"seam anchor mismatch {x},{y} {side}")
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--voxels", action="store_true", help="include the prototype voxel columns")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = build_world_manifest(args.seed, args.radius, include_voxels=args.voxels)
    encoded = json.dumps(manifest, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
