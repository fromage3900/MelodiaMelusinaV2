"""Batch Blender 5.2 audio-terrain authoring pipeline for Melodia Studio.

Controller mode launches Blender once per source audio file and writes an
editable .blend containing every selected builder/preset/time sample.  Blender
mode is internal and should not normally be called directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
BUILDERS = (
    "MEL_audio_spectrum_terrain",
    "MEL_audio_spectrum_towers",
    "MEL_audio_radial_field",
)
BATCH_PROFILES = {
    "preview": {"tile_grid": [1, 1], "tile_size": 128.0, "times": [0.0], "builders": list(BUILDERS), "export_fbx": False},
    "region": {"tile_grid": [4, 4], "tile_size": 256.0, "times": [0.0, 15.0, 30.0],
               "builders": ["MEL_audio_spectrum_terrain", "MEL_audio_radial_field"], "export_fbx": True},
    "continent": {"tile_grid": [16, 16], "tile_size": 512.0, "times": [0.0, 30.0, 60.0, 90.0],
                  "builders": ["MEL_audio_spectrum_terrain"], "export_fbx": True},
}


def _safe_stem(path: Path) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in path.stem).strip("_") or "audio"


def _controller(args: argparse.Namespace) -> int:
    if args.profile:
        profile = BATCH_PROFILES[args.profile]
        args.tile_grid = list(profile["tile_grid"])
        args.tile_size = float(profile["tile_size"])
        args.times = list(profile["times"])
        args.builders = list(profile["builders"])
        args.export_fbx = bool(profile["export_fbx"])
    if not BLENDER.exists():
        raise SystemExit(f"Blender 5.2 not found: {BLENDER}")
    sources = [Path(p).resolve() for p in args.audio]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise SystemExit(f"Missing audio files: {missing}")
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for source in sources:
        output = out_dir / f"AudioTerrain_{_safe_stem(source)}.blend"
        handoff = output.with_suffix(".audio_terrain_handoff.json")
        jobs.append({"audio": str(source), "output": str(output), "handoff": str(handoff)})
        if args.dry_run:
            continue
        command = [
            str(BLENDER), "--background", "--factory-startup",
            "--python", str(Path(__file__).resolve()), "--", "--inside-blender",
            "--audio", str(source), "--output", str(output),
            "--times", *[str(t) for t in args.times],
            "--tile-grid", str(args.tile_grid[0]), str(args.tile_grid[1]),
            "--tile-size", str(args.tile_size),
        ]
        if args.builders:
            command.extend(["--builders", *args.builders])
        if args.presets:
            command.extend(["--presets", *args.presets])
        if args.export_fbx:
            command.append("--export-fbx")
        subprocess.run(command, cwd=PROJECT, check=True)
        if not output.is_file():
            raise RuntimeError(f"Blender completed without writing expected scene: {output}")
    manifest = {
        "schema": "melodia.audio_terrain_batch.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "blender": str(BLENDER),
        "profile": args.profile,
        "builders": list(args.builders or BUILDERS),
        "presets": list(args.presets or ["ALL"]),
        "times": args.times,
        "tile_grid": args.tile_grid,
        "tile_size_m": args.tile_size,
        "export_fbx": args.export_fbx,
        "estimated_objects_per_audio": (
            len(args.builders or BUILDERS)
            * (len(args.presets) if args.presets else 3)
            * len(args.times)
            * int(args.tile_grid[0])
            * int(args.tile_grid[1])
        ),
        "dry_run": args.dry_run,
        "jobs": jobs,
    }
    manifest_path = out_dir / "audio_terrain_batch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "jobs": len(jobs), "manifest": str(manifest_path)}))
    return 0


def _set_modifier_input(modifier, tree, socket_name, value) -> bool:
    for item in tree.interface.items_tree:
        if getattr(item, "item_type", "") != "SOCKET" or getattr(item, "in_out", "") != "INPUT":
            continue
        if item.name == socket_name:
            if hasattr(item, "default_value"):
                item.default_value = value
                return True
    return False


def _inside_blender(args: argparse.Namespace) -> int:
    import bpy
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS
    from surreal_arch.melodia_gn.presets import preset_param_sets

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    audio_arg = args.audio[0] if isinstance(args.audio, list) else args.audio
    sound = bpy.data.sounds.load(str(Path(audio_arg).resolve()), check_existing=True)
    x_spacing, y_spacing = 170.0, 110.0
    tile_x_count, tile_y_count = args.tile_grid
    selected_builders = tuple(args.builders or BUILDERS)
    unknown = sorted(set(selected_builders) - set(BUILDERS))
    if unknown:
        raise RuntimeError(f"Unknown audio builders: {unknown}")
    built = []
    artifacts = []
    output_path = Path(args.output).resolve()
    export_dir = output_path.with_suffix("")
    if args.export_fbx:
        export_dir.mkdir(parents=True, exist_ok=True)
    for builder_index, builder_id in enumerate(selected_builders):
        base_tree = GROUP_BUILDERS[builder_id]()
        presets = preset_param_sets(builder_id)
        if args.presets:
            wanted = set(args.presets)
            presets = [p for p in presets if p["name"] in wanted]
        if not presets:
            raise RuntimeError(f"No selected presets found for {builder_id}")
        for preset_index, preset in enumerate(presets):
            for time_index, sample_time in enumerate(args.times):
                base_low = float(preset["params"].get("Low Hz", 20.0))
                base_high = float(preset["params"].get("High Hz", 20000.0))
                band_span = (base_high - base_low) / max(1, tile_x_count)
                for tile_y in range(tile_y_count):
                    for tile_x in range(tile_x_count):
                        tree = base_tree.copy()
                        suffix = f"{preset['name']}_T{sample_time:g}_X{tile_x:02d}_Y{tile_y:02d}"
                        tree.name = f"{builder_id}_{suffix}"
                        mesh = bpy.data.meshes.new(f"{builder_id}_{suffix}_Mesh")
                        obj = bpy.data.objects.new(f"{builder_id}_{suffix}", mesh)
                        bpy.context.collection.objects.link(obj)
                        obj.location = (
                            tile_x * args.tile_size + preset_index * x_spacing,
                            tile_y * args.tile_size + builder_index * y_spacing,
                            time_index * 30.0,
                        )
                        for key, value in preset["params"].items():
                            _set_modifier_input(None, tree, key, value)
                        low_hz = base_low + band_span * tile_x
                        high_hz = base_low + band_span * (tile_x + 1)
                        _set_modifier_input(None, tree, "Low Hz", low_hz)
                        _set_modifier_input(None, tree, "High Hz", high_hz)
                        _set_modifier_input(None, tree, "Size X M", float(args.tile_size))
                        _set_modifier_input(None, tree, "Size Y M", float(args.tile_size))
                        _set_modifier_input(None, tree, "Radius M", float(args.tile_size) * 0.5)
                        _set_modifier_input(None, tree, "Sound", sound)
                        _set_modifier_input(None, tree, "Time", float(sample_time))
                        mod = obj.modifiers.new(name=builder_id, type="NODES")
                        mod.node_group = tree
                        obj["melodia_audio_source"] = str(Path(audio_arg).resolve())
                        obj["melodia_builder"] = builder_id
                        obj["melodia_preset"] = preset["name"]
                        obj["melodia_sample_time"] = float(sample_time)
                        obj["melodia_tile_x"] = tile_x
                        obj["melodia_tile_y"] = tile_y
                        obj["melodia_frequency_low_hz"] = low_hz
                        obj["melodia_frequency_high_hz"] = high_hz
                        built.append(obj.name)
                        record = {
                            "object": obj.name,
                            "builder": builder_id,
                            "preset": preset["name"],
                            "sample_time": float(sample_time),
                            "tile": {"x": tile_x, "y": tile_y, "size_m": float(args.tile_size)},
                            "world_origin_m": list(obj.location),
                            "frequency_hz": [low_hz, high_hz],
                            "named_attributes": ["audio_amplitude"] + (["frequency_hz"] if builder_id != "MEL_audio_radial_field" else []),
                        }
                        if args.export_fbx:
                            bpy.ops.object.select_all(action="DESELECT")
                            obj.select_set(True)
                            bpy.context.view_layer.objects.active = obj
                            fbx_path = export_dir / f"SM_{obj.name}.fbx"
                            bpy.ops.export_scene.fbx(
                                filepath=str(fbx_path), use_selection=True,
                                use_mesh_modifiers=True, add_leaf_bones=False,
                                apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
                            )
                            record["fbx"] = {
                                "path": str(fbx_path), "bytes": fbx_path.stat().st_size,
                                "sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest(),
                            }
                        artifacts.append(record)
    scene = bpy.context.scene
    scene["melodia_audio_terrain_schema"] = "melodia.audio_terrain_scene.v1"
    scene["melodia_audio_source"] = str(Path(audio_arg).resolve())
    scene["melodia_generated_objects"] = len(built)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    handoff = {
        "schema": "melodia.audio_terrain_ue_handoff.v1",
        "source_audio": str(Path(audio_arg).resolve()),
        "blend": str(output_path),
        "coordinate_system": {"source": "Blender Z-up meters", "unreal_scale_cm_per_meter": 100.0},
        "tile_grid": {"x": tile_x_count, "y": tile_y_count, "tile_size_m": float(args.tile_size)},
        "ue": {
            "engine": "5.8", "asset_kind": "StaticMesh",
            "recommended_content_path": "/Game/Melodia/World/AudioTerrain",
            "runtime_audio_authority": "MPC_Portfolio_Audio / Melodia presentation subsystem",
        },
        "artifacts": artifacts,
    }
    handoff_path = output_path.with_suffix(".audio_terrain_handoff.json")
    handoff_path.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "objects": len(built), "output": args.output,
                      "handoff": str(handoff_path), "fbx": sum(1 for a in artifacts if "fbx" in a)}))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", nargs="+", required=True, help="One or more WAV/MP3/FLAC sources")
    parser.add_argument("--output", required=True, help="Output directory, or .blend path in Blender mode")
    parser.add_argument("--profile", choices=sorted(BATCH_PROFILES), help="Scale profile; overrides grid, size, times, builders, and FBX mode")
    parser.add_argument("--times", nargs="+", type=float, default=[0.0, 5.0, 15.0, 30.0])
    parser.add_argument("--tile-grid", nargs=2, type=int, metavar=("X", "Y"), default=[1, 1])
    parser.add_argument("--tile-size", type=float, default=256.0, help="World tile width/depth in meters")
    parser.add_argument("--builders", nargs="+", choices=BUILDERS)
    parser.add_argument("--presets", nargs="+", help="Preset names to include; defaults to all")
    parser.add_argument("--export-fbx", action="store_true", help="Export one UE-oriented FBX per generated tile")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inside-blender", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = _parser().parse_args(argv)
    return _inside_blender(args) if args.inside_blender else _controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
