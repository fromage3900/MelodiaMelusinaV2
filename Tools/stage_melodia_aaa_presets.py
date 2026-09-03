"""Build the Melodia AAA preset review stage and UE-ready FBX package in Blender 5.2."""

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
TARGETS = {
    "01_AUDIO_TERRAIN": [
        ("MEL_audio_spectrum_terrain", "SEA_ABOVE_FALSE_HORIZON"),
        ("MEL_audio_spectrum_towers", "SEA_ABOVE_BELL_RIBS"),
        ("MEL_audio_radial_field", "SEA_ABOVE_MEMBRANE"),
    ],
    "02_GREYBOX_ROOMS": [
        ("MEL_greybox_room_kit", "SEA_ABOVE_REVEAL_GALLERY"),
        ("MEL_greybox_room_kit", "BELL_ANATOMY_CHAMBER"),
        ("MEL_greybox_room_kit", "FALSE_HORIZON_OBSERVATORY"),
    ],
    "03_BAROQUE_HEROES": [
        ("MEL_music_baroque_harpsichord", "HARPSICHORD_SEA_ABOVE_HERO"),
        ("MEL_music_baroque_violin", "VIOLIN_BELL_RELIQUARY"),
        ("MEL_music_baroque_organ", "ORGAN_ABYSSAL_CATHEDRAL"),
        ("MEL_music_baroque_lute", "LUTE_PELAGIC_VAULT"),
    ],
}


def _controller(args) -> int:
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(BLENDER), "--background", "--factory-startup", "--python", str(Path(__file__).resolve()), "--",
               "--inside-blender", "--audio", str(Path(args.audio).resolve()), "--output", str(output)]
    if args.export:
        command.append("--export")
    subprocess.run(command, cwd=PROJECT, check=True)
    if not output.is_file():
        raise RuntimeError(f"stage was not written: {output}")
    return 0


def _set_input(tree, name, value):
    for item in tree.interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "in_out", "") == "INPUT" and item.name == name:
            if hasattr(item, "default_value"):
                item.default_value = value
                return True
    return False


def _material(bpy, name, base, metallic, roughness, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.6
    return mat


def _inside(args) -> int:
    import bpy
    from mathutils import Vector
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS
    from surreal_arch.melodia_gn.presets import preset_param_sets

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    root = bpy.context.scene.collection
    collections = {}
    for name in ("00_STAGE", *TARGETS.keys(), "90_CAMERAS_LIGHTS"):
        collection = bpy.data.collections.new(name)
        root.children.link(collection)
        collections[name] = collection
    collections["01_AUDIO_TERRAIN"]["review_role"] = "Sea Above false horizon, Bell ribs, and membrane terrain"
    collections["02_GREYBOX_ROOMS"]["review_role"] = "Cinematic approach, anatomy chamber, and observatory blockouts"
    collections["03_BAROQUE_HEROES"]["review_role"] = "AAA musical architecture hero presets"

    sound = bpy.data.sounds.load(str(Path(args.audio).resolve()), check_existing=True)
    mats = {
        "01_AUDIO_TERRAIN": _material(bpy, "M_Review_AudioPearl", (0.08, 0.22, 0.42), 0.25, 0.22, (0.08, 0.4, 0.8)),
        "02_GREYBOX_ROOMS": _material(bpy, "M_Review_GreyboxIvory", (0.62, 0.57, 0.48), 0.05, 0.58),
        "03_BAROQUE_HEROES": _material(bpy, "M_Review_BaroqueGold", (0.52, 0.25, 0.055), 0.82, 0.2, (0.18, 0.06, 0.01)),
    }
    placements = {
        "01_AUDIO_TERRAIN": (-900.0, 0.0),
        "02_GREYBOX_ROOMS": (0.0, 0.0),
        "03_BAROQUE_HEROES": (250.0, 0.0),
    }
    spacing = {"01_AUDIO_TERRAIN": 1000.0, "02_GREYBOX_ROOMS": 42.0, "03_BAROQUE_HEROES": 20.0}
    artifacts = []
    export_dir = Path(args.output).resolve().with_suffix("") / "UE_Exports"
    if args.export:
        export_dir.mkdir(parents=True, exist_ok=True)

    for family, targets in TARGETS.items():
        base_x, base_y = placements[family]
        for index, (builder_id, preset_name) in enumerate(targets):
            base_tree = GROUP_BUILDERS[builder_id]()
            preset = next(p for p in preset_param_sets(builder_id) if p["name"] == preset_name)
            tree = base_tree.copy()
            tree.name = f"{builder_id}_{preset_name}_REVIEW"
            for key, value in preset["params"].items():
                _set_input(tree, key, value)
            _set_input(tree, "Sound", sound)
            _set_input(tree, "Time", 0.0)
            _set_input(tree, "Realize for export", True)
            mesh = bpy.data.meshes.new(f"SM_{preset_name}_Source")
            obj = bpy.data.objects.new(f"SM_{preset_name}", mesh)
            collections[family].objects.link(obj)
            gap = spacing[family]
            obj.location = (base_x + (index % 2) * gap, base_y + (index // 2) * gap, 0.0)
            obj.data.materials.append(mats[family])
            gn = obj.modifiers.new(builder_id, "NODES")
            gn.node_group = tree
            bevel = obj.modifiers.new("AAA_Edge_Polish", "BEVEL")
            bevel.width = 0.025 if family != "02_GREYBOX_ROOMS" else 0.08
            bevel.segments = 3
            obj["melodia_builder"] = builder_id
            obj["melodia_preset"] = preset_name
            obj["melodia_preset_params"] = json.dumps(preset["params"], sort_keys=True)
            obj["melodia_ue_destination"] = f"/Game/Melodia/World/AudioTerrain/{family}/{preset_name}"
            record = {"family": family, "builder": builder_id, "preset": preset_name, "object": obj.name,
                      "parameters": preset["params"], "ue_destination": obj["melodia_ue_destination"]}
            if args.export:
                review_location = obj.location.copy()
                obj.location = (0.0, 0.0, 0.0)
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                fbx = export_dir / f"SM_{preset_name}.fbx"
                bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, use_mesh_modifiers=True,
                                         add_leaf_bones=False, apply_scale_options="FBX_SCALE_ALL",
                                         axis_forward="-Y", axis_up="Z")
                obj.location = review_location
                record["fbx"] = {"path": str(fbx), "bytes": fbx.stat().st_size,
                                 "sha256": hashlib.sha256(fbx.read_bytes()).hexdigest()}
            artifacts.append(record)

    bpy.ops.mesh.primitive_plane_add(size=2400.0, location=(0.0, 0.0, -0.05))
    generated_floor = bpy.context.object
    for collection in list(generated_floor.users_collection):
        collection.objects.unlink(generated_floor)
    collections["00_STAGE"].objects.link(generated_floor)
    generated_floor.name = "Review_Floor"
    generated_floor.data.materials.append(_material(bpy, "M_Review_Floor", (0.018, 0.022, 0.035), 0.0, 0.32))

    world = bpy.context.scene.world or bpy.data.worlds.new("Melodia Review World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.012, 0.028, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.2
    for name, location, energy, color in (
        ("Key_RoseGold", (80, -180, 180), 7000, (1.0, 0.42, 0.28)),
        ("Fill_MoonBlue", (-300, 100, 240), 9000, (0.18, 0.38, 1.0)),
        ("Rim_Pearl", (500, 300, 300), 11000, (0.72, 0.86, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA"); data.energy = energy; data.color = color; data.shape = "DISK"; data.size = 80.0
        light = bpy.data.objects.new(name, data); collections["90_CAMERAS_LIGHTS"].objects.link(light); light.location = location
        light.rotation_euler = (Vector((-250.0, 80.0, 20.0)) - light.location).to_track_quat("-Z", "Y").to_euler()
    cameras = {}
    for name, location, target, lens in (
        ("CAM_00_AllPresets", (300.0, -1800.0, 820.0), (-300.0, 80.0, 35.0), 52.0),
        ("CAM_01_AudioTerrain", (-800.0, -1450.0, 680.0), (-820.0, 80.0, 20.0), 50.0),
        ("CAM_02_Greybox", (22.0, -105.0, 48.0), (20.0, 18.0, 5.0), 52.0),
        ("CAM_03_Baroque", (260.0, -62.0, 25.0), (260.0, 10.0, 4.5), 52.0),
    ):
        camera_data = bpy.data.cameras.new(name)
        camera = bpy.data.objects.new(name, camera_data)
        collections["90_CAMERAS_LIGHTS"].objects.link(camera)
        camera.location = location
        direction = Vector(target) - camera.location
        camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        camera_data.lens = lens
        camera_data.clip_end = 5000.0
        cameras[name] = camera
    bpy.context.scene.camera = cameras["CAM_00_AllPresets"]
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene["melodia_review_schema"] = "melodia.aaa_preset_stage.v1"
    bpy.context.scene["source_audio"] = str(Path(args.audio).resolve())
    bpy.context.scene["preset_count"] = len(artifacts)
    output = Path(args.output).resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    manifest = {"schema": "melodia.aaa_preset_export.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "blend": str(output), "source_audio": str(Path(args.audio).resolve()), "artifacts": artifacts}
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "blend": str(output), "manifest": str(manifest_path),
                      "presets": len(artifacts), "fbx": sum(1 for a in artifacts if "fbx" in a)}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--inside-blender", action="store_true", help=argparse.SUPPRESS)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    return _inside(args) if args.inside_blender else _controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
