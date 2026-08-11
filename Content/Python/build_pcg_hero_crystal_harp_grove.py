"""Build the additive Crystal Harp Grove proof graph.

The graph uses the existing APCGHeroMusicNode contract: player-pawn
proximity -> overlap press -> spring return -> note event/audio/rhythm
response. No new clock, MPC writer, or runtime interaction framework is
introduced.
"""
from __future__ import annotations

from dataclasses import asdict
from math import atan2, degrees, hypot
from typing import Any, Mapping

import pcg_hero_music_common as common
import pcg_hero_music_control as control
from pcg_crystal_harp_layout import build_crystal_harp_curve_points, build_crystal_harp_layout, crystal_harp_midi_pattern


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_Hero_CrystalHarpGrove"
PROFILE_PATH = f"{DEST_FOLDER}/DA_Hero_CrystalHarpGroveProfile"
PROOF_LEVEL_PATH = f"{DEST_FOLDER}/L_PCG_Hero_CrystalHarpGrove"
STONE_MATERIAL_PATH = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"
CRYSTAL_MATERIAL_PATH = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002"


def _point(unreal: Any, location, seed, scale=(1.0, 1.0, 1.0), bounds=(80.0, 80.0, 20.0), rotation=(0.0, 0.0, 0.0)):
    return common.make_point(unreal, tuple(float(value) for value in location), int(seed), scale=scale, bounds=bounds, rotation=rotation)


def _classic_branches(unreal: Any, nodes, landmarks, walk_width: float):
    floor_points = []
    columns = []
    arches = []
    for index, (x, y, z, _node_index, _lane, _midi, _station) in enumerate(nodes):
        previous = nodes[max(0, index - 1)]
        following = nodes[min(len(nodes) - 1, index + 1)]
        yaw = degrees(atan2(following[1] - previous[1], following[0] - previous[0]))
        floor_points.append(((x, y, z - 20.0), 0xF20000 + index, (1.08, 0.52, 0.12), (160.0, 100.0, 8.0), (0.0, yaw, 0.0)))
    # Bridge the station gaps with centerline landings. The four string pads
    # are intentionally offset across the corridor, but the authored floor
    # must remain continuous under the entire traversal.
    for station in range(len(landmarks) - 1):
        ax, ay, az, _ = landmarks[station]
        bx, by, bz, _ = landmarks[station + 1]
        for segment in range(1, 4):
            alpha = segment / 4.0
            floor_points.append(((ax + (bx - ax) * alpha, ay + (by - ay) * alpha, az + (bz - az) * alpha + 28.0), 0xF25000 + station * 4 + segment, (1.0, 0.48, 0.12), (160.0, 100.0, 8.0), (0.0, degrees(atan2(by - ay, bx - ax)), 0.0)))
    for station, (x, y, z, _landmark_seed) in enumerate(landmarks):
        support_height = max(160.0, z - 32.0)
        yaw = 0.0
        if station + 1 < len(landmarks):
            nx, ny, _nz, _seed = landmarks[station + 1]
            yaw = degrees(atan2(ny - y, nx - x))
        for side in (-1.0, 1.0):
            columns.append(((x, y + side * walk_width * 1.48, support_height * 0.5), 0xF30000 + station * 2 + int(side > 0), (0.42, 0.42, max(0.24, min(1.35, support_height / 760.0))), (90.0, 90.0, max(160.0, support_height)), (0.0, yaw, 0.0)))
        arches.append(((x, y, z + 330.0), 0xF40000 + station, (0.115, 0.115, 0.14), (500.0, 150.0, 420.0), (0.0, yaw + 90.0, 0.0)))

    def convert(entries):
        return tuple(_point(unreal, location, seed, scale=scale, bounds=bounds, rotation=rotation) for location, seed, scale, bounds, rotation in entries)

    return (
        {"label": "classic crystal harp walkable floor", "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4", "material": STONE_MATERIAL_PATH, "points": convert(floor_points)},
        {"label": "classic crystal harp station columns", "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_column_02", "material": STONE_MATERIAL_PATH, "points": convert(columns)},
        {"label": "classic crystal harp station arches", "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_arch_06", "material": STONE_MATERIAL_PATH, "points": convert(arches)},
    )


def _visible_string_branch(unreal: Any, nodes, walk_width: float) -> dict[str, Any]:
    """Build real taut string meshes above each press bridge.

    SM_Pipe is an authored 1,000 cm long tubular mesh. Each PCG point
    rotates/scales that mesh between a lower bridge and an upper harp frame,
    so the strings remain visible in the graph output and are not implied by
    lighting or a material-only effect.
    """
    points = []
    for x, y, z, node_index, lane, _midi, _station in nodes:
        bottom = (x, y, z + 20.0)
        # Keep the strings in front of the station arches and give them a
        # readable harp-like fan instead of letting them disappear into the
        # architectural rails at wide capture distance.
        top = (x + 78.0 + lane * 14.0, y + (lane - 1.5) * 10.0, z + 340.0 + lane * 18.0)
        direction = tuple(top[axis] - bottom[axis] for axis in range(3))
        length = max(1.0, (direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) ** 0.5)
        yaw = degrees(atan2(direction[1], direction[0]))
        pitch = degrees(atan2(direction[2], hypot(direction[0], direction[1])))
        points.append(
            _point(
                unreal,
                tuple((bottom[axis] + top[axis]) * 0.5 for axis in range(3)),
                0xF60000 + node_index,
                scale=(length / 1000.0, 0.34, 0.34),
                bounds=(500.0, 12.0, 12.0),
                rotation=(pitch, yaw, 0.0),
            )
        )
    return {
        "label": "real crystal harp taut strings",
        "mesh": "/Game/ArtOfShader/Global/DemoRoom/Meshes/SM_Pipe",
        "material": CRYSTAL_MATERIAL_PATH,
        "points": tuple(points),
    }


def _harp_neck_branch(unreal: Any, nodes) -> dict[str, Any]:
    """Add an authored cross-neck over every four-string station.

    The neck is intentionally a separate mesh branch: the interactive pads
    remain CPU actors, while the visible harp frame remains cheap, deterministic
    PCG content that can be culled/partitioned independently.
    """
    points = []
    for station in range(5):
        station_nodes = nodes[station * 4 : station * 4 + 4]
        if not station_nodes:
            continue
        x = sum(node[0] for node in station_nodes) / len(station_nodes) + 98.0
        y = sum(node[1] for node in station_nodes) / len(station_nodes)
        z = sum(node[2] for node in station_nodes) / len(station_nodes) + 370.0
        points.append(
            _point(
                unreal,
                (x, y, z),
                0xF70000 + station,
                scale=(0.34, 0.34, 0.34),
                bounds=(500.0, 16.0, 16.0),
                rotation=(0.0, 90.0, 0.0),
            )
        )
    return {
        "label": "visible crystal harp station necks",
        "mesh": "/Game/ArtOfShader/Global/DemoRoom/Meshes/SM_Pipe",
        "material": CRYSTAL_MATERIAL_PATH,
        "points": tuple(points),
    }


def build_crystal_harp_grove_graph(control_overrides: Mapping[str, object] | None = None) -> dict[str, Any]:
    import importlib
    import unreal

    importlib.reload(control)
    if control_overrides is None:
        control_overrides = control.authoring_overrides("CrystalHarpGrove")
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    station_count = 5
    node_count = station_count * 4
    nodes, landmarks = build_crystal_harp_layout(
        node_count=node_count,
        station_count=station_count,
        step_spacing=snapshot.ArraySpacing,
        grove_rise=snapshot.Depth,
        walk_width=snapshot.WalkWidth,
    )
    midi_notes = crystal_harp_midi_pattern(node_count)
    scale_span = snapshot.ScaleMax - snapshot.ScaleMin
    interactive_points = []
    for x, y, z, node_index, lane, midi, _station in nodes:
        alpha = node_index / max(1, node_count - 1)
        point_scale = snapshot.ScaleMin + scale_span * (0.35 + 0.65 * alpha)
        seed = (node_index << 16) | ((lane + 1) << 8) | midi
        interactive_points.append(_point(unreal, (x, y, z), seed, scale=(point_scale, point_scale, point_scale), bounds=(90.0, 72.0, 28.0)))

    curve_branches = []
    for side, label in ((-1.0, "left"), (1.0, "right")):
        curve_branches.append({
            "label": f"PCGEx crystal harp {label} frame rail",
            "spline_tag": f"PCG_Spline_CrystalHarpGrove_{label}",
            "curve_points": tuple(_point(unreal, location, 0xF50000 + index + (0x100 if side > 0 else 0), bounds=(36.0, 36.0, 36.0)) for index, location in enumerate(build_crystal_harp_curve_points(5, snapshot.ArraySpacing, snapshot.Depth, snapshot.WalkWidth, side))),
            "mesh": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "material": CRYSTAL_MATERIAL_PATH,
            "distance_between_points": snapshot.ResampleSpacing,
            "scale": (0.12, 0.08, 0.18),
        })

    classic_branches = list(_classic_branches(unreal, nodes, landmarks, snapshot.WalkWidth))
    classic_branches.append(_visible_string_branch(unreal, nodes, snapshot.WalkWidth))
    classic_branches.append(_harp_neck_branch(unreal, nodes))
    result = common.build_hero_graph(
        unreal,
        graph_path=GRAPH_PATH,
        profile_path=PROFILE_PATH,
        graph_kind="CrystalHarpGrove",
        actor_class_name="APCGHeroMusicNode",
        points=interactive_points,
        decoration_points=(),
        expected_note_count=node_count,
        midi_notes=midi_notes,
        dimensions={
            "Width": 210.0,
            "Depth": 128.0,
            "Height": 30.0,
            "PressDepth": 9.0,
            "SpringStiffness": 1120.0,
            "SpringDamping": 98.0,
            "PressTriggerHeight": 38.0,
        },
        sequential=True,
        beat_window_beats=1.0,
        control_overrides=asdict(snapshot),
        classic_architecture_branches=tuple(classic_branches),
        pcgex_curve_branches=tuple(curve_branches),
        architecture_source_path=None,
        architecture_in_graph=False,
    )

    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    crystal_material = unreal.EditorAssetLibrary.load_asset(CRYSTAL_MATERIAL_PATH)
    if profile and crystal_material:
        for prop in ("node_material", "white_node_material", "black_node_material"):
            try:
                profile.set_editor_property(prop, crystal_material)
            except Exception:
                pass
        unreal.EditorAssetLibrary.save_asset(PROFILE_PATH, only_if_is_dirty=False)

    result.update({
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "proof_level": PROOF_LEVEL_PATH,
        "instrument_family": "crystal_harp_pitched_strings",
        "station_count": station_count,
        "string_count": node_count,
          "visual_string_mesh": "/Game/ArtOfShader/Global/DemoRoom/Meshes/SM_Pipe",
          "visual_string_count": node_count,
          "visual_neck_mesh": "/Game/ArtOfShader/Global/DemoRoom/Meshes/SM_Pipe",
          "visual_neck_count": station_count,
        "midi_notes": list(midi_notes),
        "seed_identity": "(station, lane, MIDI) packed into PCGPoint.Seed",
        "layout": "five four-string harp gates on an evenly resampled rising S-curve",
        "curve_system": "paired PCGEx CreateSpline -> SplineSampler -> NearestSpline PathDist frame rails",
        "interaction_contract": "player-pawn proximity trigger -> spring press/release -> note event/audio/rhythm response",
        "music_framework_changes": [],
    })
    unreal.log(f"[PCG Crystal Harp Grove] built {result}")
    return result


if __name__ == "__main__":
    print(build_crystal_harp_grove_graph())
