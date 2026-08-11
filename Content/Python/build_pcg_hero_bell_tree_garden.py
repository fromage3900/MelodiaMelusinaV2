"""Build the additive eighteen-bell BellTreeGarden proof graph."""
from __future__ import annotations

from dataclasses import asdict
from math import atan2, degrees, pi, sin, sqrt
from typing import Mapping


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_Hero_BellTreeGarden"
PROFILE_PATH = f"{DEST_FOLDER}/DA_Hero_BellTreeGardenProfile"

BELL_PATTERN = (60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86)
BELL_MATERIAL_PATH = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002"
STONE_MATERIAL_PATH = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"


def bell_midi_pattern(count: int = 18) -> tuple[int, ...]:
    return tuple(BELL_PATTERN[index % len(BELL_PATTERN)] for index in range(max(1, int(count))))


def build_bell_garden_layout(
    bell_count: int = 18,
    step_spacing: float = 260.0,
    garden_rise: float = 900.0,
    walk_width: float = 300.0,
    branch_count: int = 3,
) -> tuple[tuple[tuple[float, float, float, int, int, int, int], ...], tuple[tuple[float, float, float, int], ...]]:
    """Return deterministic, height-aware bell nodes and accent points.

    The garden uses a continuous guide curve and arc-length resampling, so
    the 18 bells remain evenly spaced in 3D while the traversal rises and
    bends between its three branches. Branch identity stays stable for the
    gameplay seed and architecture landmarks.
    """
    bell_count = max(1, int(bell_count))
    step_spacing = max(1.0, float(step_spacing))
    garden_rise = max(1.0, float(garden_rise))
    walk_width = max(1.0, float(walk_width))
    branch_count = max(1, int(branch_count))
    per_branch = max(1, (bell_count + branch_count - 1) // branch_count)
    total_span = (bell_count - 1) * step_spacing
    x_origin = -total_span * 0.5

    def guide(alpha: float) -> tuple[float, float, float]:
        alpha = max(0.0, min(1.0, float(alpha)))
        x = x_origin + total_span * alpha
        section_position = alpha * max(1, branch_count - 1)
        section = min(branch_count - 1, int(section_position))
        blend = section_position - section
        next_section = min(branch_count - 1, section + 1)
        blend = blend * blend * (3.0 - 2.0 * blend)
        center_a = (section - (branch_count - 1) * 0.5) * walk_width * 0.52
        center_b = (next_section - (branch_count - 1) * 0.5) * walk_width * 0.52
        y = (1.0 - blend) * center_a + blend * center_b
        y += sin(alpha * branch_count * pi) * walk_width * 0.22
        z = 48.0 + alpha * garden_rise
        return x, y, z

    sample_count = max(256, bell_count * 48)
    samples = [guide(index / float(sample_count - 1)) for index in range(sample_count)]
    cumulative = [0.0]
    for previous, current in zip(samples, samples[1:]):
        cumulative.append(
            cumulative[-1]
            + sqrt(
                (current[0] - previous[0]) ** 2
                + (current[1] - previous[1]) ** 2
                + (current[2] - previous[2]) ** 2
            )
        )
    total_length = cumulative[-1]

    def resample(distance: float) -> tuple[float, float, float]:
        if total_length <= 1e-6:
            return samples[0]
        target = max(0.0, min(total_length, distance))
        low, high = 0, len(cumulative) - 1
        while low < high:
            middle = (low + high) // 2
            if cumulative[middle] < target:
                low = middle + 1
            else:
                high = middle
        upper = max(1, low)
        lower = upper - 1
        span = max(1e-6, cumulative[upper] - cumulative[lower])
        t = (target - cumulative[lower]) / span
        return tuple(
            samples[lower][axis] + (samples[upper][axis] - samples[lower][axis]) * t
            for axis in range(3)
        )

    interactive: list[tuple[float, float, float, int, int, int, int]] = []
    accents: list[tuple[float, float, float, int]] = []
    for index, midi in enumerate(bell_midi_pattern(bell_count)):
        branch = min(branch_count - 1, index // per_branch)
        local_index = index % per_branch
        x, y, z = resample(total_length * index / max(1, bell_count - 1))
        lane = branch
        interactive.append((x, y, z, index, lane, midi, branch))

        # Accents are deterministic support/lantern points, not interactive
        # actors, so they can be replaced by a lower-quality tier later.
        if local_index in (0, per_branch - 1) or index % 3 == 0:
            accents.append((x, y - walk_width * 0.70, z + 24.0, 0xE00000 + index))
            accents.append((x, y + walk_width * 0.70, z + 24.0, 0xE10000 + index))

    return tuple(interactive), tuple(accents)


def build_bell_branch_curve_points(
    bell_count: int = 18,
    step_spacing: float = 260.0,
    garden_rise: float = 900.0,
    walk_width: float = 300.0,
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        (x, y, z + 260.0)
        for x, y, z, _index, _lane, _midi, _branch in build_bell_garden_layout(
            bell_count, step_spacing, garden_rise, walk_width
        )[0]
    )


def build_classic_bell_architecture_branches(
    bell_count: int,
    step_spacing: float,
    garden_rise: float,
    walk_width: float,
    branch_count: int = 3,
) -> tuple[dict, ...]:
    nodes, _ = build_bell_garden_layout(
        bell_count=bell_count,
        step_spacing=step_spacing,
        garden_rise=garden_rise,
        walk_width=walk_width,
        branch_count=branch_count,
    )
    deck = []
    columns = []
    arches = []
    for index, node in enumerate(nodes):
        x, y, z, _node_index, _lane, _midi, branch = node
        next_node = nodes[min(index + 1, len(nodes) - 1)]
        yaw = degrees(atan2(next_node[1] - y, next_node[0] - x)) if index + 1 < len(nodes) else 0.0
        deck.append(
            (
                (x, y, z - 22.0),
                0xE20000 + index,
                (max(1.0, step_spacing / 4.0), max(1.0, walk_width / 4.0), 18.0 / 0.30),
                (220.0, 260.0, 18.0),
                (0.0, yaw, 0.0),
            )
        )
        # Ground the classic columns against the rising landing instead of
        # leaving a fixed-height support floating below the early steps.
        support_top = max(24.0, z - 36.0)
        support_height = max(96.0, support_top)
        support_scale_z = max(0.30, min(2.40, support_height / 620.0))
        # One support pair per branch section preserves landmarks without
        # turning the path into a forest of identical columns.
        if index % max(1, len(nodes) // branch_count) == 0:
            for side in (-1.0, 1.0):
                columns.append(
                    (
                        (x, y + side * walk_width * 0.76, support_height * 0.5),
                        0xE30000 + index * 2 + (0 if side < 0 else 1),
                        (0.72, 0.72, support_scale_z),
                        (100.0, 100.0, max(96.0, support_height)),
                        (0.0, yaw, 0.0),
                    )
                )
        if index % max(1, len(nodes) // branch_count) == 0:
            arches.append(
                (
                    (x, y, z + 500.0),
                    0xE40000 + branch,
                    (0.20, 0.20, 0.24),
                    (700.0, 180.0, 600.0),
                    (0.0, yaw + 90.0, 0.0),
                )
            )
    return (
        {
            "label": "classic bell garden stepping plinths",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "material": STONE_MATERIAL_PATH,
            "points": tuple(deck),
        },
        {
            "label": "classic bell garden columns",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "material": STONE_MATERIAL_PATH,
            "points": tuple(columns),
        },
        {
            "label": "classic bell garden branch arches",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
            "material": STONE_MATERIAL_PATH,
            "points": tuple(arches),
        },
    )


def build_bell_tree_garden_graph(control_overrides: Mapping[str, object] | None = None) -> dict:
    import importlib
    import unreal
    import pcg_hero_music_common as common
    import pcg_hero_music_control as control

    common = importlib.reload(common)
    # A loaded control actor may belong to another proof level. Use the
    # garden's authored baseline unless the On-Demand caller supplies a
    # snapshot explicitly.
    if control_overrides is None:
        control_overrides = control.authoring_overrides("BellTreeGarden")
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    bell_count = snapshot.ArrayCount
    interactive, accents = build_bell_garden_layout(
        bell_count=bell_count,
        step_spacing=snapshot.ArraySpacing,
        garden_rise=snapshot.Depth,
        walk_width=snapshot.WalkWidth,
        branch_count=3,
    )
    points = []
    midi_notes: list[int] = []
    scale_span = snapshot.ScaleMax - snapshot.ScaleMin
    for x, y, z, node_index, lane, midi, _branch in interactive:
        seed = (node_index << 16) | ((lane + 1) << 8) | midi
        scale_alpha = (node_index % 6) / 5.0
        point_scale = snapshot.ScaleMin + scale_span * scale_alpha
        points.append(
            common.make_point(
                unreal,
                (x, y, z),
                seed,
                scale=(point_scale, point_scale, point_scale),
                bounds=(110.0, 110.0, 360.0),
            )
        )
        midi_notes.append(midi)

    classic_branches = []
    for branch in build_classic_bell_architecture_branches(
        bell_count, snapshot.ArraySpacing, snapshot.Depth, snapshot.WalkWidth, 3
    ):
        classic_branches.append(
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
        "label": "PCGEx measured BellTreeGarden traversal curve",
        "spline_tag": "PCG_Spline_BellTreeGarden",
        "curve_points": [
            common.make_point(unreal, location, 0xE50000 + index, bounds=(36.0, 36.0, 36.0))
            for index, location in enumerate(
                build_bell_branch_curve_points(
                    bell_count, snapshot.ArraySpacing, snapshot.Depth, snapshot.WalkWidth
                )
            )
        ],
        "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
        "material": STONE_MATERIAL_PATH,
        "distance_between_points": snapshot.ResampleSpacing,
        "scale": (0.18, 0.12, 0.14),
        "rotation_offset": (0.0, 0.0, 0.0),
    },)

    dimensions = {
        "width": 120.0,
        "depth": 120.0,
        "height": 64.0,
        "press_depth": 6.0,
        "spring_stiffness": 1000.0,
        "spring_damping": 96.0,
        "press_trigger_height": 28.0,
    }
    result = common.build_hero_graph(
        unreal,
        graph_path=GRAPH_PATH,
        profile_path=PROFILE_PATH,
        graph_kind="BellTreeGarden",
        actor_class_name="APCGBellTreeGardenNode",
        points=points,
        # The early proof used the generic structural scatter role for these
        # accents. That role includes wall/panel meshes whose imported bounds
        # overwhelm the tuned bells at this scale. Keep the accent locations
        # in the deterministic layout contract, but let the measured deck,
        # sparse branch supports, and bell actors own the composition.
        decoration_points=(),
        expected_note_count=len(points),
        midi_notes=midi_notes,
        dimensions=dimensions,
        sequential=True,
        beat_window_beats=1.0,
        control_overrides=asdict(snapshot),
        decoration_role="structural",
        classic_architecture_branches=classic_branches,
        pcgex_curve_branches=pcgex_curve_branches,
        architecture_source_path=None,
        architecture_in_graph=False,
    )

    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    bell_material = unreal.EditorAssetLibrary.load_asset(BELL_MATERIAL_PATH)
    if profile and bell_material:
        profile.set_editor_property("node_material", bell_material)
        profile.set_editor_property("white_node_material", bell_material)
        profile.set_editor_property("black_node_material", bell_material)
        unreal.EditorAssetLibrary.save_asset(PROFILE_PATH, only_if_is_dirty=False)

    result.update({
        "bell_count": len(points),
        "branch_count": 3,
        "midi_pattern": bell_midi_pattern(len(points)),
        "seed_identity": "(step, branch/lane, MIDI) packed into PCGPoint.Seed",
        "instrument_geometry": "runtime lathed bell body with tapered neck and flared beveled lip",
        "curve_system": "PCGEx tagged measured traversal spline -> nearest-spline PathDist -> classic branch arches",
        "layout": "three connected six-bell ascending garden sections with continuous stepping support",
        "decorative_accents": "reserved in layout metadata; proof static-panel scatter disabled for landmark clarity",
    })
    return result


if __name__ == "__main__":
    print(build_bell_garden_layout())
