"""Build a simple, reusable walkable Xylophone Trail PCG graph.

The bars use the existing APCGHeroMusicNode overlap/spring contract and the
existing procedural beveled surface. This is visual/interaction authoring only:
it does not add a clock, audio subsystem, MPC writer, or new runtime framework.
"""
from __future__ import annotations

from typing import Any, Mapping

import pcg_hero_music_common as common
import pcg_hero_music_control as control
from pcg_xylophone_layout import build_xylophone_path_specs


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_Hero_XylophoneTrail"
PROFILE_PATH = f"{DEST_FOLDER}/DA_Hero_XylophoneTrailProfile"
PROOF_LEVEL_PATH = f"{DEST_FOLDER}/L_PCG_Hero_XylophoneTrail"
FLOOR_MESH = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4"
RAIL_MESH = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4"
STONE_MATERIAL = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"
GOLD_MATERIAL = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Gold_Trim"


def _set_if_present(obj: Any, prop: str, value: Any) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _point(unreal: Any, spec: Any, *, scale=(1.0, 1.0, 1.0), bounds=(120.0, 120.0, 12.0), rotation=None) -> Any:
    return common.make_point(
        unreal,
        (float(spec.x), float(spec.y), float(spec.z)),
        int(spec.seed),
        scale=tuple(float(value) for value in scale),
        bounds=tuple(float(value) for value in bounds),
        rotation=(0.0, float(spec.yaw if rotation is None else rotation), 0.0),
    )


def build_xylophone_trail_graph(control_overrides: Mapping[str, object] | None = None) -> dict[str, Any]:
    import importlib
    import unreal

    # Text-injected editor sessions retain imported modules between runs; keep
    # the new BarSection/BarSpacing alias contract live without an editor restart.
    importlib.reload(control)
    if control_overrides is None:
        control_overrides = control.authoring_overrides("XylophoneTrail")
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    bar_count = max(6, int(snapshot.ArrayCount) * 6)
    step_spacing = max(280.0, float(snapshot.ArraySpacing) * 0.75)
    bar_width = max(360.0, float(snapshot.WalkWidth) * 1.65)
    path_amplitude = max(280.0, float(snapshot.WalkWidth) * 2.4)
    path_rise = max(120.0, min(float(snapshot.Depth) * 0.32, 900.0))
    bar_depth = max(190.0, min(float(snapshot.WalkWidth) * 0.72, 300.0))
    specs = build_xylophone_path_specs(
        note_count=bar_count,
        step_spacing=step_spacing,
        path_amplitude=path_amplitude,
        path_rise=path_rise,
        bar_length=bar_width,
        bar_depth=bar_depth,
    )

    bar_points = [
        _point(
            unreal,
            spec,
            scale=(spec.bar_length / bar_width, 1.0, 1.0),
            bounds=(bar_width * 0.5, bar_depth * 0.5, 14.0),
        )
        for spec in specs
    ]

    floor_points = [
        _point(
            unreal,
            spec,
            scale=(1.35, 0.78, 0.12),
            bounds=(160.0, 160.0, 6.0),
        )
        for spec in specs
    ]
    rail_points = [
        _point(
            unreal,
            spec,
            scale=(0.42, 0.18, 0.34),
            bounds=(120.0, 120.0, 30.0),
            rotation=spec.yaw - 90.0,
        )
        for spec in specs[::max(1, int(round(1.0 / max(0.05, snapshot.Density))))]
    ]
    curve_points = [
        common.make_point(
            unreal,
            (float(spec.x), float(spec.y + path_amplitude * 0.92), float(spec.z + 55.0)),
            int(spec.seed) ^ 0x40000000,
            bounds=(80.0, 80.0, 12.0),
            rotation=(0.0, float(spec.yaw), 0.0),
        )
        for spec in specs
    ]

    result = common.build_hero_graph(
        unreal,
        graph_path=GRAPH_PATH,
        profile_path=PROFILE_PATH,
        graph_kind="XylophoneTrail",
        actor_class_name="APCGHeroMusicNode",
        points=bar_points,
        decoration_points=(),
        expected_note_count=len(specs),
        midi_notes=[spec.midi_note for spec in specs],
        dimensions={
            "Width": bar_width,
            "Depth": bar_depth,
            "Height": 28.0,
            "PressDepth": 9.0,
            "SpringStiffness": 1050.0,
            "SpringDamping": 96.0,
            "PressTriggerHeight": 26.0,
        },
        sequential=True,
        beat_window_beats=1.0,
        control_overrides=control_overrides,
        classic_architecture_branches=(
            {
                "label": "xylophone authored walkable floor ribbon",
                "mesh": FLOOR_MESH,
                "material": STONE_MATERIAL,
                "points": floor_points,
            },
            {
                "label": "xylophone low edge rails",
                "mesh": RAIL_MESH,
                "material": GOLD_MATERIAL,
                "points": rail_points,
            },
        ),
        pcgex_curve_branches=(
            {
                "label": "PCGEx measured xylophone guide rail",
                "spline_tag": "PCG_Spline_XylophoneTrail",
                "curve_points": curve_points,
                "mesh": RAIL_MESH,
                "material": GOLD_MATERIAL,
                "distance_between_points": snapshot.ResampleSpacing,
                "scale": (0.38, 0.16, 0.26),
            },
        ),
        architecture_source_path=None,
        architecture_in_graph=False,
    )

    # Reuse the generic beveled geometry but give the new instrument family a
    # single authored gold trim finish, with stone only on the walkable ribbon.
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    gold = unreal.EditorAssetLibrary.load_asset(GOLD_MATERIAL)
    white = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/PCG/Musical/SM_PianoKey_White_Bevel")
    if profile and gold:
        _set_if_present(profile, "node_material", gold)
        _set_if_present(profile, "white_node_material", gold)
        _set_if_present(profile, "black_node_material", gold)
        if white:
            _set_if_present(profile, "node_mesh", white)
            _set_if_present(profile, "white_node_mesh", white)
            _set_if_present(profile, "black_node_mesh", white)
        unreal.EditorAssetLibrary.save_asset(PROFILE_PATH, only_if_is_dirty=False)

    result.update(
        {
            "graph": GRAPH_PATH,
            "profile": PROFILE_PATH,
            "proof_level": PROOF_LEVEL_PATH,
            "instrument_family": "pitched_percussion_xylophone",
            "bar_count": len(specs),
            "midi_notes": [spec.midi_note for spec in specs],
            "layout": "crosswise beveled bars on an ascending S-curve with low rails",
            "curve_system": "PCGEx measured guide rail over a deterministic walkable bar path",
            "interaction": "existing APCGHeroMusicNode player overlap -> spring press/release",
            "music_framework_changes": [],
        }
    )
    unreal.log(f"[PCG Xylophone Trail] built {result}")
    return result


if __name__ == "__main__":
    print(build_xylophone_trail_graph())
