"""Build the additive twenty-four-node Arpeggio Bridge proof graph."""
from __future__ import annotations

from dataclasses import asdict
from math import atan2, degrees
from typing import Mapping


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_Hero_ArpeggioBridge"
PROFILE_PATH = f"{DEST_FOLDER}/DA_Hero_ArpeggioBridgeProfile"

# Three repetitions of the authored C-major ascent/return phrase. This keeps
# the 24 note identities stable while the bridge geometry continues to rise.
C_MAJOR_ARPEGGIO = (60, 64, 67, 72, 76, 79, 84, 79) * 3


def build_bridge_layout(
    note_count: int = 24,
    step_spacing: float = 180.0,
    bridge_rise: float = 1800.0,
    walk_width: float = 220.0,
    resample_spacing: float = 120.0,
    density: float = 0.40,
) -> tuple[tuple[tuple[float, float, float, int, int, int], ...], tuple[tuple[float, float, float, int], ...]]:
    """Return deterministic interactive and support layout tuples."""
    note_count = max(1, int(note_count))
    step_spacing = max(1.0, float(step_spacing))
    bridge_rise = max(1.0, float(bridge_rise))
    walk_width = max(1.0, float(walk_width))
    resample_spacing = max(1.0, float(resample_spacing))
    density = min(1.0, max(0.0, float(density)))

    notes = tuple(C_MAJOR_ARPEGGIO[index % len(C_MAJOR_ARPEGGIO)] for index in range(note_count))
    x_origin = -(note_count - 1) * step_spacing * 0.5
    interactive: list[tuple[float, float, float, int, int, int]] = []
    decorations: list[tuple[float, float, float, int]] = []
    for index, midi in enumerate(notes):
        alpha = index / max(1, note_count - 1)
        x = x_origin + index * step_spacing
        y = (alpha - 0.5) * walk_width * 0.70 + __import__("math").sin(alpha * __import__("math").pi * 1.2) * walk_width * 0.20
        z = 28.0 + alpha * bridge_rise
        lane = (index % 3) - 1
        interactive.append((x, y, z, index, lane, midi))

        if index == 0 or index == note_count - 1 or index % max(1, int(round(resample_spacing / step_spacing))) == 0:
            decorations.append((x, y - walk_width * 0.52, z + 38.0, 1000 + index * 2))
            decorations.append((x, y + walk_width * 0.52, z + 38.0, 1001 + index * 2))
        if density > 0.0 and index % max(1, int(round(1.0 / max(density, 0.01)))) == 0:
            decorations.append((x, y, z - bridge_rise * 0.16, 2000 + index))

    return tuple(interactive), tuple(decorations)


def build_bridge_curve_points(
    note_count: int = 24,
    step_spacing: float = 180.0,
    bridge_rise: float = 1800.0,
    walk_width: float = 220.0,
) -> tuple[tuple[float, float, float], ...]:
    """Return the exact planned traversal curve used by the PCGEx branch."""
    interactive, _ = build_bridge_layout(
        note_count=note_count,
        step_spacing=step_spacing,
        bridge_rise=bridge_rise,
        walk_width=walk_width,
    )
    # The curve is intentionally tied to the playable nodes, then lifted to
    # form a low rail guide. This keeps architecture and gameplay on one
    # measured path instead of making a second decorative trajectory.
    return tuple((x, y, z + 340.0) for x, y, z, _index, _lane, _midi in interactive)


def build_classic_bridge_architecture_branches(
    note_count: int,
    step_spacing: float,
    bridge_rise: float,
    walk_width: float,
) -> tuple[dict, ...]:
    """Build the bridge from measured classic project-library pieces.

    The bridge collection meshes have inconsistent authored dimensions.  Each
    static branch therefore receives explicit section, portal, and pylon
    transforms derived from the same stepping curve as the playable notes.
    """
    note_count = max(1, int(note_count))
    step_spacing = max(1.0, float(step_spacing))
    bridge_rise = max(1.0, float(bridge_rise))
    walk_width = max(1.0, float(walk_width))
    nodes, _ = build_bridge_layout(
        note_count=note_count,
        step_spacing=step_spacing,
        bridge_rise=bridge_rise,
        walk_width=walk_width,
    )
    material = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"
    deck_material = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Universal_LayeredStone"
    # Supports are landmarks, not a repeating wall. Keep one sparse pair per
    # six-note section so the PCGEx stepping curve and the walkable deck stay
    # visually dominant in the proof composition.
    section_size = 6
    deck = []
    spans = []
    pylons = []
    rails = []
    for section_index, start in enumerate(range(0, note_count, section_size)):
        end = min(note_count - 1, start + section_size - 1)
        a = nodes[start]
        b = nodes[end]
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        dz = b[2] - a[2]
        target_span = abs(dx) + step_spacing
        yaw = degrees(atan2(dy, dx)) if abs(dx) > 0.001 else 0.0
        pitch = degrees(atan2(dz, max(1.0, (dx * dx + dy * dy) ** 0.5)))
        spans.append(
            (
                ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5 - 76.0),
                0xD00000 + section_index,
                (target_span / 4.0, 24.0, 18.0),
                (580.0, 120.0, 90.0),
                (pitch, yaw, 0.0),
            )
        )
        for side in (-1.0, 1.0):
            pylons.append(
                (
                    (a[0], a[1] + side * walk_width * 0.72, a[2] - 120.0),
                    0xD10000 + section_index * 2 + (0 if side < 0 else 1),
                    (0.42, 0.42, 0.36),
                    (72.0, 72.0, 420.0),
                    (0.0, yaw, 0.0),
                )
            )
    for index, node in enumerate(nodes):
        next_node = nodes[min(index + 1, len(nodes) - 1)]
        yaw = degrees(atan2(next_node[1] - node[1], next_node[0] - node[0])) if index + 1 < len(nodes) else 0.0
        segment_length = max(1.0, ((next_node[0] - node[0]) ** 2 + (next_node[1] - node[1]) ** 2) ** 0.5)
        pitch = degrees(atan2(next_node[2] - node[2], segment_length)) if index + 1 < len(nodes) else 0.0
        deck.append(
            (
                # SM_Greybox_Floor_4x4 is the authored floor tile (4 x 4 x
                # 0.30 uu). Scale it from measured bounds so adjacent tiles
                # form one continuous, visibly walkable ribbon.
                (node[0], node[1], node[2] - 10.0),
                0xD30000 + index,
                (max(1.0, step_spacing / 4.0), max(1.0, (walk_width * 1.40) / 4.0), 20.0 / 0.30),
                (220.0, 260.0, 18.0),
                (pitch, yaw, 0.0),
            )
        )
        if index + 1 < len(nodes):
            for side in (-1.0, 1.0):
                rails.append(
                    (
                        (node[0], node[1] + side * walk_width * 0.66, node[2] + 42.0),
                        0xD40000 + index * 2 + (0 if side < 0 else 1),
                        (segment_length / 4.0, 0.16, 0.20),
                        (segment_length * 0.55, 24.0, 90.0),
                        (pitch, yaw, 0.0),
                    )
                )
    return (
        {
            "label": "classic marble bridge deck",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "material": deck_material,
            "points": tuple(deck),
        },
        {
            "label": "classic measured bridge spans",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "material": material,
            "points": tuple(spans),
        },
        {
            "label": "classic bridge pylons",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "material": material,
            "points": tuple(pylons),
        },
        {
            "label": "classic bridge safety rails",
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "material": deck_material,
            "points": tuple(rails),
        },
    )


def build_arpeggio_bridge_graph(control_overrides: Mapping[str, object] | None = None) -> dict:
    import unreal
    import importlib
    import pcg_hero_music_common as common
    import pcg_hero_music_control as control
    common = importlib.reload(common)

    # Keep the proof graph deterministic when a different level's tagged
    # driver is currently loaded. Explicit overrides are the On-Demand live
    # control path; the authoring baseline is always the 24-step bridge.
    if control_overrides is None:
        control_overrides = control.authoring_overrides("ArpeggioBridge")
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    interactive, decorations = build_bridge_layout(
        note_count=snapshot.ArrayCount,
        step_spacing=snapshot.ArraySpacing,
        bridge_rise=snapshot.Depth,
        walk_width=snapshot.WalkWidth,
        resample_spacing=snapshot.ResampleSpacing,
        density=snapshot.Density,
    )
    points = []
    midi_notes: list[int] = []
    scale_span = snapshot.ScaleMax - snapshot.ScaleMin
    for x, y, z, node_index, lane, midi in interactive:
        seed = (node_index << 16) | ((lane + 1) << 8) | midi
        scale_alpha = (node_index % 9) / 8.0
        point_scale = snapshot.ScaleMin + scale_span * scale_alpha
        points.append(common.make_point(unreal, (x, y, z), seed, scale=(point_scale, point_scale, point_scale), bounds=(92.0, 112.0, 22.0)))
        midi_notes.append(midi)
    decoration_points = ()
    classic_architecture = []
    for branch in build_classic_bridge_architecture_branches(
        snapshot.ArrayCount,
        snapshot.ArraySpacing,
        snapshot.Depth,
        snapshot.WalkWidth,
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
        "label": "PCGEx measured arpeggio bridge curve",
        "spline_tag": "PCG_Spline_ArpeggioBridge",
        "curve_points": [
            common.make_point(unreal, location, 0xC20000 + index, bounds=(36.0, 36.0, 36.0))
            for index, location in enumerate(
                build_bridge_curve_points(
                    snapshot.ArrayCount, snapshot.ArraySpacing, snapshot.Depth, snapshot.WalkWidth
                )
            )
        ],
        # A low authored half-wall keeps the measured curve legible as a rail
        # instead of producing a row of house-like gables.
        "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
        "material": "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral",
        "distance_between_points": snapshot.ResampleSpacing * 3.0,
        # HalfWall_4 is deliberately kept low and narrow; the far gate is the
        # only repeated arch landmark in this proof, so the bridge itself
        # reads as a traversable deck rather than a row of buildings.
        "scale": (0.20, 0.12, 0.16),
        "rotation_offset": (0.0, 0.0, 0.0),
    },)
    dimensions = {
        "width": max(120.0, min(170.0, snapshot.ArraySpacing * 0.88)),
        # Traversal keys remain long front-to-back and visibly piano-like;
        # the curve supplies the bridge motion, not blocky square pads.
        "depth": max(260.0, min(360.0, snapshot.WalkWidth * 1.28)),
        "height": 18.0,
        "press_depth": 7.0,
        "spring_stiffness": 1050.0,
        "spring_damping": 96.0,
        "press_trigger_height": 24.0,
    }
    result = common.build_hero_graph(
        unreal,
        graph_path=GRAPH_PATH,
        profile_path=PROFILE_PATH,
        graph_kind="ArpeggioBridge",
        actor_class_name="PCGHeroMusicNode",
        points=points,
        decoration_points=decoration_points,
        expected_note_count=len(points),
        midi_notes=midi_notes,
        dimensions=dimensions,
        sequential=True,
        beat_window_beats=1.0,
        control_overrides=asdict(snapshot),
        decoration_role="structural",
        classic_architecture_branches=classic_architecture,
        pcgex_curve_branches=pcgex_curve_branches,
        architecture_source_path="/Game/EnvSandbox/PCG/Styles/Escher/PCG_Escher_SpiralAscent",
        architecture_span=snapshot.ArrayCount * snapshot.ArraySpacing,
        architecture_aisle_width=snapshot.WalkWidth,
        architecture_vault_height=snapshot.Depth,
        architecture_resample_spacing=snapshot.ResampleSpacing,
        # The copied TensorSpin/Extrude branch remains explicitly disabled
        # until a finite guide-data contract is authored. It must not leak
        # its old arch/gable spawners into the playable bridge proof.
        architecture_in_graph=False,
        architecture_mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        architecture_material_path="/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral",
    )
    result["pcgex_tensor_safety"] = common.normalize_saved_pcgex_tensor_graph(
        unreal, GRAPH_PATH, snapshot.ResampleSpacing
    )
    result.update({
        "note_count": len(points),
        "target_pattern": "C-major arpeggio, C4-C6 range, deterministic step/lane/MIDI identity",
        "miss_behavior": "streak reset; bridge remains traversable",
        "layout": "24 measured rising stepping keys on a curved traversable path",
        "curve_system": "PCGEx tagged measured note spline -> nearest-spline PathDist -> low classic rail, plus measured deck/spans/pylons",
        "curve_points": build_bridge_curve_points(snapshot.ArrayCount, snapshot.ArraySpacing, snapshot.Depth, snapshot.WalkWidth),
    })
    return result


if __name__ == "__main__":
    print(build_bridge_layout())
