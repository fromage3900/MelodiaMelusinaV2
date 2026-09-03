"""Render a real DEM terrain with the offline Melodia MIDI environment.

This is a Blender-only bridge. It consumes the metric OBJ emitted by
``melodia_mesh_terrain_source.py`` and the canonical MIDI parser/output. It
does not import ``unreal`` or modify a UE map, PCG graph, gameplay save, or
production asset.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load Blender helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


def _look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _material(name: str, color: tuple[float, float, float, float], *, metallic: float, roughness: float, emission: tuple[float, float, float, float] | None = None, emission_strength: float = 0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission is not None:
        emission_input = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        if emission_input is not None:
            emission_input.default_value = emission
        strength_input = shader.inputs.get("Emission Strength")
        if strength_input is not None:
            strength_input.default_value = emission_strength
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _terrain_material():
    material = bpy.data.materials.new("Melodia_ASTER_Terrain")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.003
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.012, 0.065, 0.030, 1.0)
    ramp.color_ramp.elements[1].color = (0.18, 0.14, 0.055, 1.0)
    shader.inputs["Roughness"].default_value = 0.86
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _import_obj(path: Path):
    before = set(bpy.data.objects)
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=str(path))
    else:
        bpy.ops.import_scene.obj(filepath=str(path))
    imported = [obj for obj in bpy.context.selected_objects if obj not in before and obj.type == "MESH"]
    if not imported:
        imported = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    if not imported:
        raise RuntimeError(f"OBJ import produced no mesh: {path}")
    if len(imported) == 1:
        return imported[0]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in imported:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]
    bpy.ops.object.join()
    return bpy.context.object


def _add_area_light(name: str, location: tuple[float, float, float], energy: float, color: tuple[float, float, float], size: float, target: Vector):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    _look_at(obj, target)
    return obj


def _add_music_materials(music_obj, helper) -> dict[str, str]:
    materials = [
        helper._material("Melodia_Bass_Violet", (0.10, 0.025, 0.18, 1.0), metallic=0.35, roughness=0.28, emission=(0.12, 0.01, 0.22, 1.0), emission_strength=0.35),
        helper._material("Melodia_Harmony_Gold", (0.72, 0.26, 0.08, 1.0), metallic=0.55, roughness=0.23, emission=(0.30, 0.04, 0.01, 1.0), emission_strength=0.55),
        helper._material("Melodia_Melody_Blossom", (0.95, 0.20, 0.42, 1.0), metallic=0.32, roughness=0.20, emission=(0.50, 0.02, 0.12, 1.0), emission_strength=0.80),
    ]
    for material in materials:
        music_obj.data.materials.append(material)
    z_min = min((vertex.co.z for vertex in music_obj.data.vertices), default=0.0)
    for polygon in music_obj.data.polygons:
        z = polygon.center.z - z_min
        polygon.material_index = 0 if z < 1.0 else (2 if int(z * 10) % 3 == 0 else 1)
    return {"bass": materials[0].name, "harmony": materials[1].name, "melody": materials[2].name}


def _setup_and_render(terrain, music, terrain_manifest: dict, output_png: Path, midi_path: Path, helper) -> dict:
    terrain.data.materials.append(_terrain_material())
    for polygon in terrain.data.polygons:
        polygon.use_smooth = True
    bounds = [terrain.matrix_world @ vertex.co for vertex in terrain.data.vertices]
    if not bounds:
        raise RuntimeError("terrain mesh has no vertices")
    min_z = min(vertex.z for vertex in bounds)
    max_z = max(vertex.z for vertex in bounds)
    center_z = (min_z + max_z) * 0.5
    center_x = (min(vertex.x for vertex in bounds) + max(vertex.x for vertex in bounds)) * 0.5
    center_y = (min(vertex.y for vertex in bounds) + max(vertex.y for vertex in bounds)) * 0.5
    samples_x = int(terrain_manifest["geometry"]["samples_x"])
    samples_y = int(terrain_manifest["geometry"]["samples_y"])
    center_vertex_index = (samples_y // 2) * samples_x + (samples_x // 2)
    anchor_z = (terrain.matrix_world @ terrain.data.vertices[center_vertex_index].co).z

    # The MIDI environment is intentionally enlarged for a readable offline
    # hero while remaining anchored in the source terrain's meter space.
    music.scale = (72.0, 72.0, 72.0)
    music.location = (center_x, center_y, anchor_z + 8.0)
    music_materials = _add_music_materials(music, helper)
    hero_target = Vector((center_x, center_y, anchor_z + 28.0))
    resonance_material = helper._material(
        "Melodia_ASTER_Resonance_Ring",
        (0.95, 0.30, 0.06, 1.0),
        metallic=0.72,
        roughness=0.18,
        emission=(0.90, 0.06, 0.01, 1.0),
        emission_strength=1.8,
    )
    helper._add_resonance_rings(hero_target, 270.0, resonance_material)
    target = Vector((center_x, center_y, anchor_z + 70.0))
    _add_area_light("Melodia_ASTER_Key", (center_x - 1900.0, center_y - 2500.0, max_z + 1800.0), 120000.0, (1.0, 0.42, 0.36), 1300.0, target)
    _add_area_light("Melodia_ASTER_Fill", (center_x + 2200.0, center_y - 400.0, max_z + 1000.0), 90000.0, (0.30, 0.45, 1.0), 1000.0, target)
    _add_area_light("Melodia_ASTER_Rim", (center_x, center_y + 2600.0, max_z + 1500.0), 130000.0, (1.0, 0.18, 0.08), 900.0, target)
    sun_data = bpy.data.lights.new("Melodia_ASTER_Sun", type="SUN")
    sun_data.energy = 3.2
    sun_data.angle = math.radians(8.0)
    sun = bpy.data.objects.new("Melodia_ASTER_Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(28.0), math.radians(-24.0), math.radians(32.0))

    camera_data = bpy.data.cameras.new("Melodia_ASTER_Offline_Camera")
    camera = bpy.data.objects.new("Melodia_ASTER_Offline_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (center_x + 720.0, center_y - 1120.0, anchor_z + 620.0)
    camera_data.type = "PERSP"
    camera_data.lens = 52.0
    camera_data.clip_start = 1.0
    camera_data.clip_end = 50000.0
    _look_at(camera, target)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_png)
    scene.render.film_transparent = False
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.006, 0.012, 0.025, 1.0)
        background.inputs["Strength"].default_value = 0.45
    scene.view_settings.exposure = 1.5
    bpy.ops.wm.save_as_mainfile(filepath=str(output_png.with_suffix(".blend")))
    bpy.ops.render.render(write_still=True)
    return {
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "terrain_vertices": len(terrain.data.vertices),
        "terrain_triangles": len(terrain.data.polygons),
        "terrain_elevation_range_m": [min_z, max_z],
        "music_scale": list(music.scale),
        "camera": {"location": list(camera.location), "lens": camera_data.lens},
        "music_materials": music_materials,
        "midi": str(midi_path),
        "terrain_source_manifest": terrain_manifest,
    }


def _cli_args() -> dict[str, str]:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    values: dict[str, str] = {}
    index = 0
    while index < len(raw):
        if raw[index].startswith("--") and index + 1 < len(raw):
            values[raw[index][2:].replace("-", "_")] = raw[index + 1]
            index += 2
        else:
            index += 1
    return values


def main() -> int:
    args = _cli_args()
    project_root = Path(args.get("project_root", Path(__file__).resolve().parents[2])).resolve()
    terrain_obj = Path(args["terrain_obj"]).resolve()
    terrain_manifest_path = Path(args["terrain_manifest"]).resolve()
    midi_path = Path(args.get("midi", project_root / "Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid"))
    if not midi_path.is_absolute():
        midi_path = (project_root / midi_path).resolve()
    output_dir = Path(args.get("output_dir", project_root / "Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900/TerrainPreview"))
    if not output_dir.is_absolute():
        output_dir = (project_root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    terrain_manifest = json.loads(terrain_manifest_path.read_text(encoding="utf-8"))
    if terrain_manifest.get("unreal", {}).get("target") != "Mesh Terrain":
        raise ValueError("terrain manifest is not a Mesh Terrain source")
    if terrain_manifest.get("unreal", {}).get("classic_landscape_used") is not False:
        raise ValueError("terrain manifest permits classic Landscape; refusing overlay")

    helper = _load_module(project_root / "Content/Python/melodia_blender_offline_preview.py", "melodia_blender_offline_preview_helpers")
    parser = helper._load_midi_parser(project_root)
    notes, ticks_per_beat = parser.parse_midi_notes(str(midi_path))
    grid = parser.notes_to_voxel_grid(notes, ticks_per_beat, beat_division=4)

    _clear_scene()
    terrain = _import_obj(terrain_obj)
    terrain.name = "Melodia_ASTER_MeshTerrain_Source"
    music, _, _ = helper._make_voxel_mesh(grid, 0.62)
    music.name = "Melodia_MIDI_Environment_On_ASTER_Terrain"
    output_png = output_dir / "PetalCantata_Yoshino_ASTER_MIDI_Overlay_1920x1080.png"
    render = _setup_and_render(terrain, music, terrain_manifest, output_png, midi_path, helper)
    manifest = {
        "format": "melodia_blender_mesh_terrain_overlay_manifest",
        "schema_version": 1,
        "terrain_obj": {"path": str(terrain_obj), "sha256": _sha256(terrain_obj)},
        "terrain_manifest": {"path": str(terrain_manifest_path), "sha256": _sha256(terrain_manifest_path)},
        "midi": {"path": str(midi_path), "sha256": _sha256(midi_path), "note_count": len(notes), "voxel_count": len(grid)},
        "render": {**render, "png": str(output_png), "png_sha256": _sha256(output_png)},
        "blend": str(output_png.with_suffix(".blend")),
        "runtime_boundary": {
            "offline_only": True,
            "does_not_call_unreal": True,
            "uses_mesh_terrain_source_only": True,
            "does_not_modify_protected_maps": True,
            "does_not_write_gameplay_save": True,
        },
        "ok": True,
    }
    manifest_path = output_dir / "PetalCantata_Yoshino_ASTER_MIDI_Overlay.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "png": str(output_png), "blend": manifest["blend"], "manifest": str(manifest_path), "notes": len(notes), "voxels": len(grid)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
