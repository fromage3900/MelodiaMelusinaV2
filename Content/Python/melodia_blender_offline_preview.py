"""Build a deterministic Blender-only preview of a Melodia MIDI world.

This is an offline authoring/render utility.  It consumes the canonical
``Tools/midi_to_voxel/midi_voxel.py`` parser, creates a small materialized
voxel scene, renders a standalone PNG, and writes provenance beside it.

It intentionally never imports ``unreal`` and never edits a UE map, PCG graph,
gameplay save, or portfolio stage.  Run inside Blender::

    blender --background --python Content/Python/melodia_blender_offline_preview.py -- \
        --project-root C:/EnvironmentPortfolio/BS_GodFile \
        --midi Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid \
        --output-dir Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900
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


def _load_midi_parser(project_root: Path):
    parser_path = project_root / "Tools" / "midi_to_voxel" / "midi_voxel.py"
    spec = importlib.util.spec_from_file_location("melodia_midi_voxel_preview", parser_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load MIDI parser: {parser_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)


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


def _make_voxel_mesh(grid: dict[tuple[int, int, int], int], scale: float):
    if not grid:
        raise ValueError("MIDI produced an empty voxel grid")
    min_x = min(cell[0] for cell in grid)
    min_y = min(cell[1] for cell in grid)
    min_z = min(cell[2] for cell in grid)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    material_indices: list[int] = []
    # Corner order matches the exposed-face indices below.
    face_indices = (
        (0, 1, 3, 2),
        (4, 6, 7, 5),
        (0, 4, 5, 1),
        (2, 3, 7, 6),
        (0, 2, 6, 4),
        (1, 5, 7, 3),
    )
    neighbors = ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1))

    for (vx, vy, vz), velocity in sorted(grid.items()):
        base = len(vertices)
        x = (vx - min_x) * scale
        y = (vy - min_y) * scale
        z = (vz - min_z) * scale
        for cz in (0, 1):
            for cy in (0, 1):
                for cx in (0, 1):
                    vertices.append((x + cx * scale, y + cy * scale, z + cz * scale))
        # Bass cells are dark violet, chord tones are gold, and upper melody
        # cells are blossom pink.  Velocity selects a brighter variant.
        if vz - min_z <= 1:
            material_index = 0
        elif (vy % 12) in {0, 4, 7}:
            material_index = 2 if velocity >= 80 else 1
        else:
            material_index = 1
        for face, neighbor in zip(face_indices, neighbors):
            if (vx + neighbor[0], vy + neighbor[1], vz + neighbor[2]) not in grid:
                faces.append(tuple(base + index for index in face))
                material_indices.append(material_index)

    mesh = bpy.data.meshes.new("Melodia_MIDI_Environment_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Melodia_MIDI_Environment", mesh)
    bpy.context.collection.objects.link(obj)
    return obj, material_indices, (len(vertices), len(faces))


def _look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


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


def _add_resonance_rings(target: Vector, radius: float, material) -> None:
    for index, tilt in enumerate((0.0, math.radians(14.0))):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=radius + index * 0.75,
            minor_radius=0.035,
            major_segments=96,
            minor_segments=12,
            location=(target.x, target.y, target.z + 0.25 + index * 0.12),
            rotation=(tilt, math.radians(5.0 * index), math.radians(4.0 * index)),
        )
        ring = bpy.context.object
        ring.name = f"Melodia_Resonance_Ring_{index + 1:02d}"
        ring.data.materials.append(material)


def _add_route_thread(max_x: float, target: Vector, material) -> None:
    curve_data = bpy.data.curves.new("Melodia_MIDI_Route_Thread_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.045
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(3)
    control_points = (
        (0.0, target.y, 0.04),
        (max_x * 0.28, target.y + 0.35, 0.04),
        (max_x * 0.70, target.y - 0.25, 0.04),
        (max_x, target.y, 0.04),
    )
    for point, coordinate in zip(spline.bezier_points, control_points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    route = bpy.data.objects.new("Melodia_MIDI_Route_Thread", curve_data)
    bpy.context.collection.objects.link(route)
    curve_data.materials.append(material)


def _setup_scene(grid: dict[tuple[int, int, int], int], output_png: Path):
    _clear_scene()
    scale = 0.62
    terrain, material_indices, mesh_stats = _make_voxel_mesh(grid, scale)
    materials = [
        _material("Melodia_Bass_Violet", (0.10, 0.025, 0.18, 1.0), metallic=0.35, roughness=0.28, emission=(0.12, 0.01, 0.22, 1.0), emission_strength=0.35),
        _material("Melodia_Harmony_Gold", (0.72, 0.26, 0.08, 1.0), metallic=0.55, roughness=0.23, emission=(0.30, 0.04, 0.01, 1.0), emission_strength=0.55),
        _material("Melodia_Melody_Blossom", (0.95, 0.20, 0.42, 1.0), metallic=0.32, roughness=0.20, emission=(0.50, 0.02, 0.12, 1.0), emission_strength=0.80),
    ]
    for material in materials:
        terrain.data.materials.append(material)
    for polygon, material_index in zip(terrain.data.polygons, material_indices):
        polygon.material_index = material_index

    max_x = max(cell[0] for cell in grid) * scale
    max_y = max(cell[1] for cell in grid) * scale
    max_z = max(cell[2] for cell in grid) * scale
    target = Vector((max_x * 0.5, max_y * 0.5, max_z * 0.40))
    ground_material = _material("Melodia_Offline_Ground", (0.012, 0.006, 0.028, 1.0), metallic=0.10, roughness=0.40)
    bpy.ops.mesh.primitive_plane_add(size=max(max_x, max_y) * 2.2, location=(target.x, target.y, -0.05))
    ground = bpy.context.object
    ground.name = "Melodia_Offline_Ground_Plane"
    ground.data.materials.append(ground_material)
    ring_material = _material("Melodia_Resonance_Gold", (0.95, 0.30, 0.06, 1.0), metallic=0.72, roughness=0.18, emission=(0.90, 0.06, 0.01, 1.0), emission_strength=1.8)
    _add_resonance_rings(target, max(2.6, min(max_x, max_y) * 0.32), ring_material)
    route_material = _material("Melodia_Route_Thread", (0.32, 0.025, 0.16, 1.0), metallic=0.35, roughness=0.20, emission=(0.28, 0.01, 0.08, 1.0), emission_strength=0.8)
    _add_route_thread(max_x, target, route_material)

    _add_area_light("Melodia_Key", (target.x - 5.0, target.y - 8.0, max_z + 9.0), 1200.0, (1.0, 0.35, 0.45), 5.0, target)
    _add_area_light("Melodia_Fill", (target.x + 8.0, target.y - 1.0, max_z + 4.0), 850.0, (0.26, 0.42, 1.0), 4.0, target)
    _add_area_light("Melodia_Rim", (target.x, target.y + 8.0, max_z + 8.0), 1500.0, (1.0, 0.18, 0.06), 3.0, target)

    camera_data = bpy.data.cameras.new("Melodia_Offline_Camera")
    camera = bpy.data.objects.new("Melodia_Offline_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (target.x, -max_y * 3.0, max_z * 1.35 + 7.0)
    camera_data.type = "ORTHO"
    # Keep the full phrase readable while reserving enough vertical pixels for
    # the voxel skyline; this is an intentional hero crop, not an editor shot.
    camera_data.ortho_scale = max(38.0, max_z * 2.25, max_y * 2.25)
    _look_at(camera, target)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        # Some Blender 5.x builds retain the legacy enum even though the
        # renderer is the current Eevee implementation.
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_png)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.world.use_nodes = True
    world_background = scene.world.node_tree.nodes.get("Background")
    if world_background is not None:
        world_background.inputs["Color"].default_value = (0.003, 0.001, 0.012, 1.0)
        world_background.inputs["Strength"].default_value = 0.18
    scene.render.filepath = str(output_png)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_png.with_suffix(".blend")))
    bpy.ops.render.render(write_still=True)
    return {
        "mesh_vertices": mesh_stats[0],
        "mesh_faces": mesh_stats[1],
        "camera": {"location": list(camera.location), "type": camera_data.type, "ortho_scale": camera_data.ortho_scale},
        "render_resolution": [scene.render.resolution_x, scene.render.resolution_y],
    }


def _cli_args() -> dict[str, str]:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    values: dict[str, str] = {}
    index = 0
    while index < len(raw):
        token = raw[index]
        if token.startswith("--") and index + 1 < len(raw):
            values[token[2:].replace("-", "_")] = raw[index + 1]
            index += 2
        else:
            index += 1
    return values


def main() -> int:
    args = _cli_args()
    project_root = Path(args.get("project_root", Path(__file__).resolve().parents[2])).resolve()
    midi_path = Path(args.get("midi", project_root / "Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid"))
    if not midi_path.is_absolute():
        midi_path = (project_root / midi_path).resolve()
    output_dir = Path(args.get("output_dir", project_root / "Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900"))
    if not output_dir.is_absolute():
        output_dir = (project_root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    parser = _load_midi_parser(project_root)
    notes, ticks_per_beat = parser.parse_midi_notes(str(midi_path))
    grid = parser.notes_to_voxel_grid(notes, ticks_per_beat, beat_division=4)
    output_png = output_dir / "MelodiaMIDIEnvironment_OfflinePreview_1920x1080.png"
    render = _setup_scene(grid, output_png)
    manifest = {
        "format": "melodia_blender_offline_preview_manifest",
        "schema_version": 1,
        "source_midi": str(midi_path),
        "source_midi_sha256": _sha256(midi_path),
        "generator": "Content/Python/melodia_blender_offline_preview.py + Tools/midi_to_voxel/midi_voxel.py",
        "ticks_per_beat": ticks_per_beat,
        "note_count": len(notes),
        "voxel_count": len(grid),
        "render": {**render, "png": str(output_png), "png_sha256": _sha256(output_png)},
        "blend": str(output_png.with_suffix(".blend")),
        "runtime_boundary": {
            "offline_only": True,
            "does_not_call_unreal": True,
            "does_not_apply_pcg": True,
            "does_not_modify_protected_maps": True,
            "does_not_write_gameplay_save": True,
        },
        "ok": True,
    }
    manifest_path = output_dir / "MelodiaMIDIEnvironment_OfflinePreview.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "png": str(output_png), "blend": manifest["blend"], "manifest": str(manifest_path), "notes": len(notes), "voxels": len(grid)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
