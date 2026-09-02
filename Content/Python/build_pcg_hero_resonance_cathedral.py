"""Build the additive six-station Resonance Cathedral proof graph — 18 pads, 6 chords."""
from __future__ import annotations

from dataclasses import asdict
from math import pi, sin
from typing import Mapping


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_Hero_ResonanceCathedral"
PROFILE_PATH = f"{DEST_FOLDER}/DA_Hero_ResonanceCathedralProfile"

CHORD_PROGRESS = (
    (60, 64, 67),  # C major
    (62, 65, 69),  # D minor
    (65, 69, 72),  # F major
    (67, 71, 74),  # G major
    (57, 60, 64),  # A minor (Am — relative, shares C/E)
    (64, 68, 71),  # E major (E — G# lift)
)


def chord_for_station(station: int) -> tuple[int, int, int]:
    octave = station // len(CHORD_PROGRESS)
    source = CHORD_PROGRESS[station % len(CHORD_PROGRESS)]
    return tuple(note + 12 * octave for note in source)


def build_piano_roll_positions(
    station_count: int = 6,
    station_spacing: float = 480.0,
    walk_width: float = 220.0,
) -> tuple[tuple[float, float, float], ...]:
    """Measured continuous roll path: 3 keys per station, no floating pads."""
    station_count = max(1, int(station_count))
    station_spacing = max(1.0, float(station_spacing))
    walk_width = max(1.0, float(walk_width))
    key_count = station_count * 3
    key_pitch = station_spacing / 3.0
    x_origin = -(key_count - 1) * key_pitch * 0.5
    positions = []
    for key_index in range(key_count):
        alpha = key_index / max(1, key_count - 1)
        x = x_origin + key_index * key_pitch
        y = sin(alpha * pi) * walk_width * 0.24
        z = 28.0 + sin(alpha * pi) * min(16.0, walk_width * 0.06)
        positions.append((x, y, z))
    return tuple(positions)


def build_cathedral_layout(
    station_count: int = 6,
    station_spacing: float = 480.0,
    walk_width: float = 220.0,
    vault_height: float = 1800.0,
    resample_spacing: float = 120.0,
    density: float = 0.40,
) -> tuple[tuple[tuple[float, float, float, int, int, int], ...], tuple[tuple[float, float, float, int], ...]]:
    """Return interactive ``(x,y,z,node_index,lane,midi)`` and decor points.

    The layout is pure and deterministic so it can be audited without an
    Unreal session. Seed identity is packed as ``node_index/lane/midi``.
    """
    station_count = max(1, int(station_count))
    station_spacing = max(1.0, float(station_spacing))
    walk_width = max(1.0, float(walk_width))
    vault_height = max(1.0, float(vault_height))
    resample_spacing = max(1.0, float(resample_spacing))
    density = min(1.0, max(0.0, float(density)))

    interactive: list[tuple[float, float, float, int, int, int]] = []
    decorations: list[tuple[float, float, float, int]] = []
    roll_positions = build_piano_roll_positions(station_count, station_spacing, walk_width)
    for station in range(station_count):
        for degree, midi in enumerate(chord_for_station(station)):
            node_index = station * 3 + degree
            seed = (node_index << 16) | (degree << 8) | midi
            x, y, z = roll_positions[node_index]
            interactive.append((x, y, z, node_index, degree, midi))

        # Side columns and vault accents are deliberately deterministic and
        # scaled by the same driver snapshot as the interactive pads.
        for side in (-1, 1):
            decorations.append((x, side * (walk_width * 0.5 + 190.0), vault_height * 0.5, station * 2 + (0 if side < 0 else 1)))
        samples = max(1, int(round(station_spacing / resample_spacing)))
        for sample in range(samples):
            if density <= 0.0 or ((sample + station) % max(1, int(round(1.0 / max(density, 0.01))))) != 0:
                continue
            alpha = (sample + 0.5) / samples
            decorations.append((x - station_spacing * 0.5 + alpha * station_spacing, 0.0, vault_height * 0.88, 10000 + station * 100 + sample))

    return tuple(interactive), tuple(decorations)


def build_piano_roll_detail_points(
    station_count: int,
    station_spacing: float,
    walk_width: float,
) -> tuple[tuple[float, float, float, int], tuple[tuple[float, float, float, int], ...]]:
    """Return one long keybed plus correctly offset ebony keys between ivory keys — 6 stations → 18 ivory, 12 ebony."""
    positions = build_piano_roll_positions(station_count, station_spacing, walk_width)
    key_pitch = max(1.0, float(station_spacing) / 3.0)
    # Piano: black after white where white_index % 7 in {0,1,3,4,5} — generates correct C# D# F# G# A# pattern for any length
    black_after_white = {w for w in range(len(positions) - 1) if w % 7 in (0, 1, 3, 4, 5)}
    black_points = []
    for white_index in sorted(black_after_white):
        if white_index + 1 >= len(positions):
            continue
        a = positions[white_index]
        b = positions[white_index + 1]
        black_points.append(
            (
                (a[0] + b[0]) * 0.5,
                (a[1] + b[1]) * 0.5 + key_pitch * 0.18,
                max(a[2], b[2]) + 23.0,
                0x500000 + white_index,
            )
        )
    row_length = max(1263.5, (len(positions) - 1) * key_pitch + 180.0)
    keybed = (0.0, 0.0, 0.0, 0x5FFFFF)
    return keybed, tuple(black_points)


def build_cathedral_vault_curve_points(
    station_count: int = 6,
    station_spacing: float = 480.0,
    vault_height: float = 1800.0,
    sample_count: int = 9,
) -> tuple[tuple[float, float, float], ...]:
    """Return the planned overhead nave curve used by the PCGEx branch."""
    station_count = max(1, int(station_count))
    station_spacing = max(1.0, float(station_spacing))
    vault_height = max(1.0, float(vault_height))
    sample_count = max(5, int(sample_count))
    span = (station_count - 1) * station_spacing + station_spacing * 1.5
    base_z = vault_height * 0.62
    apex_rise = vault_height * 0.28
    points = []
    for index in range(sample_count):
        alpha = index / float(sample_count - 1)
        x = -span * 0.5 + alpha * span
        z = base_z + sin(alpha * pi) * apex_rise
        points.append((x, 0.0, z))
    return tuple(points)


def build_classic_architecture_branches(
    station_count: int,
    station_spacing: float,
    walk_width: float,
    vault_height: float,
) -> tuple[dict, ...]:
    """Place the project's authored classic pieces using measured bounds.

    The source classic meshes carry inconsistent authored scales, so the
    graph receives explicit transforms rather than inheriting PCG collection
    scale values.  The resulting aisle is still driven by the same station
    spacing and vault-height controls as the playable row.
    """
    station_count = max(1, int(station_count))
    station_spacing = max(1.0, float(station_spacing))
    walk_width = max(1.0, float(walk_width))
    vault_height = max(1.0, float(vault_height))
    station_x = [
        (index - (station_count - 1) * 0.5) * station_spacing
        for index in range(station_count)
    ]
    # Keep the columns outside the playable roll's camera corridor. The old
    # 520 cm half-width put the front row directly over the keys in the proof
    # capture; the wider nave preserves the classic silhouette while leaving
    # a clear negative-space frame around the hero geometry.
    # Push the architectural frame outside the playable camera corridor. The
    # proof camera approaches from the negative-Y end of the nave, so a bank
    # at roughly 1.5m leaves the piano roll in the foreground while the
    # columns still establish scale behind it.
    aisle_half_width = max(1500.0, walk_width * 5.5)
    # The first proof render let the columns dominate the playable surface.
    # Keep a vaulted silhouette, but reserve enough negative space for the
    # piano roll to read as the hero landmark.
    column_height = min(860.0, max(620.0, vault_height * 0.42))
    column_scale_z = column_height / (2.0 * 587.19635)
    column_base_z = (587.19635 - 579.92230) * column_scale_z
    classic_material = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"

    # Each point is ``(location, seed, scale, bounds, rotation)``.  These
    # transforms are intentionally authored here instead of inheriting the
    # source collection transforms; the classic library contains several
    # meshes with wildly different import scales.
    columns = []
    arches = []
    # From the proof camera's near side, a symmetric pair places columns in
    # front of the piano roll. Keep the authored symmetry in plan-data, but
    # render the far-bank columns only in this compact hero composition so the
    # playable foreground remains continuously readable.
    for index, x in enumerate(station_x):
        # Two measured columns are enough to frame the hero without turning
        # the foreground into a picket fence. The arches carry the repeated
        # station rhythm across the full nave.
        for side in (1.0,) if index in (0, station_count - 1) else ():
            columns.append(
                (
                    (x, side * aisle_half_width * 1.25, column_base_z),
                    0xA00000 + index * 2 + (0 if side < 0 else 1),
                    # SM_column_02 carries a very broad imported lateral
                    # extent. Explicitly normalize X/Y so the far-bank
                    # columns read as slender landmarks in the compact proof
                    # composition rather than opaque foreground slabs.
                    (0.28, 0.28, column_scale_z * 0.78),
                    (96.0, 96.0, 620.0),
                    (0.0, 0.0, 0.0),
                )
            )
        # SM_arch_06 is a real classic arch piece. Its measured Y span is
        # 362.5 units, so yaw 90 degrees and scale it to the aisle span. A
        # breathing margin keeps the arch from reading as a solid wall.
        # Two smaller end arches establish the cathedral scale while keeping
        # every station's playable surface visible from the proof camera.
        if index in (0, station_count - 1):
            arch_scale = min(0.58, max(0.42, (2.0 * aisle_half_width) / (2.0 * 972.78) * 0.32))
            arches.append(
                (
                    # Place the full-height landmark at the far end of the
                    # nave. The piano roll sits at negative Y, so a transverse
                    # arch at Y=0 becomes a foreground wall in the overview.
                    (x, 3200.0, column_height + 130.0),
                    0xB00000 + index,
                    (arch_scale, arch_scale, arch_scale),
                    (520.0, 210.0, 360.0),
                    (0.0, 90.0, 0.0),
                )
            )
    # Tile the nave with the authored floor piece. The old proof floor was a
    # single oversized slab, which hid the scale grammar and made the hero row
    # look detached. Explicit tiles provide readable seams and a deterministic
    # authored footprint for future chunk stitching.
    floor_tiles = []
    tile_pitch = 360.0
    for tile_x in range(-3, 4):
        for tile_y in range(-3, 5):
            floor_tiles.append(
                (
                    (tile_x * tile_pitch, tile_y * tile_pitch, -10.0),
                    0xA80000 + (tile_x + 3) * 16 + (tile_y + 3),
                    (tile_pitch / 4.0, tile_pitch / 4.0, 20.0 / 0.30),
                    (220.0, 220.0, 18.0),
                    (0.0, 0.0, 0.0),
                )
            )
    return (
        {
            "label": "classic measured columns",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "material": classic_material,
            "points": tuple(columns),
        },
        {
            "label": "classic transverse arches",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
            "material": classic_material,
            "points": tuple(arches),
        },
        {
            "label": "classic tiled nave floor",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "material": classic_material,
            "points": tuple(floor_tiles),
        },
    )


def build_resonance_cathedral_graph(control_overrides: Mapping[str, object] | None = None) -> dict:
    import unreal
    import importlib
    import pcg_hero_music_common as common
    import pcg_hero_music_control as control
    common = importlib.reload(common)

    # Authoring must be deterministic even when another proof map or editor
    # lane happens to contain a tagged control actor. Runtime/editor preview
    # can still pass an explicit snapshot through the On-Demand path.
    if control_overrides is None:
        control_overrides = control.authoring_overrides("ResonanceCathedral")
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    interactive, decorations = build_cathedral_layout(
        station_count=snapshot.ArrayCount,
        station_spacing=snapshot.ArraySpacing,
        walk_width=snapshot.WalkWidth,
        vault_height=snapshot.Depth,
        resample_spacing=snapshot.ResampleSpacing,
        density=snapshot.Density,
    )
    points = []
    midi_notes: list[int] = []
    scale_span = snapshot.ScaleMax - snapshot.ScaleMin
    # Put the playable roll in the near foreground of the nave. The
    # architecture remains behind it, so a camera aimed down the aisle reads
    # the walkable keys before the vertical frame pieces.
    piano_row_offset = -980.0
    for x, y, z, node_index, lane, midi in interactive:
        seed = (node_index << 16) | (lane << 8) | midi
        scale_alpha = (node_index % 7) / 6.0
        point_scale = snapshot.ScaleMin + scale_span * scale_alpha
        points.append(common.make_point(unreal, (x, y + piano_row_offset, z), seed, scale=(point_scale, point_scale, point_scale), bounds=(78.0, 86.0, 22.0)))
        midi_notes.append(midi)
    keybed_detail, black_detail = build_piano_roll_detail_points(snapshot.ArrayCount, snapshot.ArraySpacing, snapshot.WalkWidth)
    piano_black_points = [
        # Measured ebony mesh: narrow in X and shorter front-to-back than the
        # ivory keys, with the standard semitone offset along the row.
        common.make_point(unreal, (x, y + piano_row_offset, z), seed, scale=(6.3, 1.65, 0.95), bounds=(55.0, 160.0, 24.0))
        for x, y, z, seed in black_detail
    ]
    keybed_location = (keybed_detail[0], keybed_detail[1] + piano_row_offset, keybed_detail[2], keybed_detail[3])
    piano_keybed_points = [
        common.make_point(
            unreal,
            keybed_location[:3],
            keybed_detail[3],
            scale=(max(1.0, ((snapshot.ArrayCount * snapshot.ArraySpacing) / 3.0 + 240.0) / 1100.0), 2.85, 1.0),
            bounds=(900.0, 380.0, 20.0),
        )
    ]
    classic_architecture = []
    for branch in build_classic_architecture_branches(
        snapshot.ArrayCount,
        snapshot.ArraySpacing,
        snapshot.WalkWidth,
        snapshot.Depth,
    ):
        classic_architecture.append(
            {
                **branch,
                "points": [
                    common.make_point(
                        unreal,
                        location,
                        seed,
                        scale=scale,
                        bounds=bounds,
                        rotation=rotation,
                    )
                    for location, seed, scale, bounds, rotation in branch["points"]
                ],
            }
        )
    pcgex_curve_branches = ({
        "label": "PCGEx measured cathedral vault curve",
        "spline_tag": "PCG_Spline_CathedralVault",
        "curve_points": [
            common.make_point(unreal, location, 0xC10000 + index, bounds=(36.0, 36.0, 36.0))
            for index, location in enumerate(
                build_cathedral_vault_curve_points(
                    snapshot.ArrayCount, snapshot.ArraySpacing, snapshot.Depth
                )
            )
        ],
        # The curve spine is a measured guide/trim branch. Keep the full
        # authored arch mesh on the four station landmarks below; using that
        # mesh at every spline sample creates a wall of imported arch
        # silhouettes in the foreground. The low classic half-wall preserves
        # the PCGEx path read and leaves the piano roll visually dominant.
        "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
        "material": "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral",
        "distance_between_points": snapshot.ResampleSpacing * 2.0,
        "scale": (0.28, 0.10, 0.10),
        "rotation_offset": (0.0, 0.0, 0.0),
    },)
    dimensions = {
        "width": max(90.0, min(150.0, snapshot.ArraySpacing / 3.0 * 0.90)),
        # Long front-to-back ivory keys make the row read as a piano rather
        # than twelve isolated beveled blocks.
        "depth": 360.0,
        "height": 20.0,
        "press_depth": 8.0,
        "spring_stiffness": 1100.0,
        "spring_damping": 100.0,
        "press_trigger_height": 24.0,
    }
    result = common.build_hero_graph(
        unreal,
        graph_path=GRAPH_PATH,
        profile_path=PROFILE_PATH,
        graph_kind="ResonanceCathedral",
        actor_class_name="PCGHeroMusicNode",
        points=points,
        decoration_points=(),
        expected_note_count=len(points),
        midi_notes=midi_notes,
        dimensions=dimensions,
        sequential=False,
        beat_window_beats=2.0,
        control_overrides=asdict(snapshot),
        decoration_role="structural",
        piano_black_points=piano_black_points,
        piano_keybed_points=piano_keybed_points,
        classic_architecture_branches=classic_architecture,
        pcgex_curve_branches=pcgex_curve_branches,
        architecture_source_path="/Game/EnvSandbox/PCG/Styles/Escher/PCG_Escher_SpiralAscent",
        architecture_span=snapshot.ArrayCount * snapshot.ArraySpacing + 900.0,
        architecture_aisle_width=snapshot.WalkWidth,
        architecture_vault_height=snapshot.Depth,
        architecture_resample_spacing=snapshot.ResampleSpacing,
        architecture_in_graph=True,
        # Keep the project's expanded TensorSpin/Extrude setup serialized for
        # reuse/audit, but let the measured spline and classic architecture
        # branches own the visible cathedral until a finite guide-data
        # contract is authored for the copied source graph.
        architecture_emit_to_output=False,
        architecture_mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        architecture_material_path="/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral",
    )
    result["pcgex_tensor_safety"] = common.normalize_saved_pcgex_tensor_graph(
        unreal, GRAPH_PATH, snapshot.ResampleSpacing
    )
    result.update({
        "stations": snapshot.ArrayCount,
        "pads_per_station": 3,
        "interactive_points": snapshot.ArrayCount * 3,
        "seed_identity": "(station, chord-degree, MIDI) packed into PCGPoint.Seed",
        "piano_surfaces": "SM_PianoKey_White_Bevel/SM_PianoKey_Black_Bevel with MI_Piano_Ivory/MI_Piano_Ebony",
        "layout": f"continuous measured piano roll with {snapshot.ArrayCount*3} ivory interactives, one scaled keybed",
        "curve_system": "PCGEx tagged measured vault spline -> nearest-spline PathDist -> low classic half-wall spine, plus measured classic SM_arch_06 columns/arches",
        "vault_curve_points": build_cathedral_vault_curve_points(snapshot.ArrayCount, snapshot.ArraySpacing, snapshot.Depth),
    })
    return result


if __name__ == "__main__":
    print(build_cathedral_layout())
