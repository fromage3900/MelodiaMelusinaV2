# -*- coding: utf-8 -*-
"""Cadence Strike - Gothic Cathedral Kit builder (Blender-only, reusable GN setups).

Zero new python builders. Every kit piece is an object whose geometry comes from a
stack of existing registered melodia_gn Geometry Node groups (modifiers left live and
editable in the review .blend; applied only on export copies).

Usage:
  blender 5.2 --factory-startup -b -P Tools/build_cathedral_kit.py

Outputs:
  KitbashExport/CadenceCathedral_Review_2026-08-11.blend   (live GN setups)
  KitbashExport/CathedralKit/SM_Cathedral_*.fbx             (realized export)
  KitbashExport/CathedralKit/*.meta.json                    (role/dims/provenance)
  Saved/Audit/cathedral_kit_build.json                      (evidence)
  Saved/Audit/cathedral_world_manifest.json                 (RPG-tagged rooms)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone

import bpy
from mathutils import Vector

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEPLOY = os.path.join(ROOT, "deploy")
KIT_DIR = os.path.join(ROOT, "KitbashExport", "CathedralKit")
REVIEW_BLEND = os.path.join(ROOT, "KitbashExport", "CadenceCathedral_Review_2026-08-11.blend")
AUDIT = os.path.join(ROOT, "Saved", "Audit", "cathedral_kit_build.json")
MANIFEST = os.path.join(ROOT, "Saved", "Audit", "cathedral_world_manifest.json")
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

# piece name -> list of (builder_name, {param: value}) modifier stacks
# Every builder below is an existing registered melodia_gn reusable GN group.
KIT = [
    # --- structural nave ---
    ("SM_Cathedral_VaultBay", [
        ("MEL_math_gothic_cathedral", {
            "Nave Length": 8.0, "Nave Width": 6.0, "Vault Height": 8.0,
            "Buttress Reach": 3.0, "Rose Window Radius": 0.5, "Petal Count": 8,
            "Grid Segments": 32}),
    ]),
    ("SM_Cathedral_RoseWindow", [
        ("MEL_math_gothic_cathedral", {
            "Nave Length": 0.8, "Nave Width": 6.0, "Vault Height": 6.0,
            "Rose Window Radius": 2.2, "Petal Count": 8, "Grid Segments": 8}),
    ]),
    ("SM_Cathedral_Wall", [
        ("MEL_castle_wall_segment", {
            "Length": 8.0, "Height": 9.0, "Thickness": 0.8,
            "Crenellation": False, "Merlon Count": 8}),
    ]),
    ("SM_Cathedral_WallParapet", [
        ("MEL_castle_wall_segment", {
            "Length": 8.0, "Height": 9.0, "Thickness": 0.8,
            "Crenellation": True, "Merlon Height": 0.9, "Merlon Count": 8}),
    ]),
    ("SM_Cathedral_LancetWindow", [
        ("MEL_castle_gothic_window", {
            "Width": 2.4, "Height": 6.0, "Frame Thick": 0.16,
            "Tracery Bars": 3, "Bar Width": 0.08}),
    ]),
    ("SM_Cathedral_Buttress", [
        ("MEL_castle_buttress", {
            "Height": 9.0, "Reach": 4.5, "Thickness": 0.9, "Segments": 8}),
    ]),
    ("SM_Cathedral_Pier", [
        ("MEL_castle_tower", {
            "Radius": 0.9, "Height": 11.0, "Roof Height": 0.6,
            "Segments": 24, "Crenellation": False}),
    ]),
    ("SM_Cathedral_Portal", [
        ("MEL_castle_gatehouse", {
            "Width": 6.0, "Height": 9.0, "Depth": 3.0,
            "Arch Width": 3.2, "Arch Height": 5.5, "Tower Radius": 0.8}),
    ]),
    ("SM_Cathedral_SpiralStairs", [
        ("MEL_castle_spiral_stairs", {
            "Shaft Radius": 1.5, "Height": 8.0, "Steps": 40,
            "Tread Depth": 0.3, "Riser Height": 0.2, "Inner Radius": 0.25,
            "Wall Thick": 0.25}),
    ]),
    ("SM_Cathedral_Tower", [
        ("MEL_castle_tower", {
            "Radius": 2.2, "Height": 18.0, "Roof Height": 6.0,
            "Segments": 24, "Crenellation": True}),
    ]),
    ("SM_Cathedral_Spire", [
        ("MEL_recursive_castle_spire", {
            "Base Radius": 2.2, "Base Height": 14.0, "Scale Ratio": 0.618,
            "Roof Height": 6.0, "Sub Tower Radius": 1.1,
            "Sub Tower Count": 6, "Recursion Levels": 3}),
    ]),
    ("SM_Cathedral_Crypt", [
        ("MEL_castle_keep", {
            "Width": 7.0, "Depth": 9.0, "Height": 3.5, "Wall Thick": 0.6,
            "Tiers": 1, "Towers": False, "Battlements": False, "Windows Per Tier": 0}),
    ]),
    ("SM_Cathedral_CryptVault", [
        ("MEL_math_gothic_cathedral", {
            "Nave Length": 7.0, "Nave Width": 5.0, "Vault Height": 3.5,
            "Rose Window Radius": 0.4, "Petal Count": 6, "Grid Segments": 24}),
    ]),
    ("SM_Cathedral_ChapterHouse", [
        ("MEL_castle_keep", {
            "Width": 8.0, "Depth": 8.0, "Height": 7.0, "Wall Thick": 0.8,
            "Tiers": 2, "Tier Taper": 0.85, "Towers": True,
            "Battlements": True, "Windows Per Tier": 3}),
    ]),
    ("SM_Cathedral_Chapel", [
        ("MEL_castle_keep", {
            "Width": 6.0, "Depth": 6.0, "Height": 5.0, "Wall Thick": 0.6,
            "Tiers": 1, "Towers": False, "Battlements": False, "Windows Per Tier": 1}),
    ]),
    # --- musical architecture ---
    ("SM_Cathedral_Chandelier", [
        ("MEL_music_note_head", {"Scale": 0.35, "LOD": 1}),
        ("MEL_radial_array", {"Count": 8, "Arc Angle": 6.283, "Radius": 1.3, "Rotate with Arc": True}),
    ], True),
    ("SM_Cathedral_StaffBalustrade", [
        ("MEL_music_sheet_rail", {"Length": 3.0, "Height": 1.2, "Line Thickness": 0.06,
                                  "Note Count": 3, "Note Size": 0.5, "Post Count": 4,
                                  "Show Clef": False}),
        ("MEL_linear_array", {"Count": 6, "Offset": (3.0, 0.0, 0.0)}),
    ], True),
    ("SM_Cathedral_HarmonicOrb", [
        ("MEL_harmonic_orb", {"Orb Radius": 1.0, "Ring Radius": 1.5,
                              "Ring Thickness": 0.08, "Orb Subdivisions": 4}),
    ]),
    ("SM_Cathedral_Altar", [
        ("MEL_castle_keep", {
            "Width": 4.0, "Depth": 2.4, "Height": 1.6, "Wall Thick": 1.6,
            "Tiers": 2, "Tier Taper": 0.9, "Towers": False,
            "Battlements": False, "Windows Per Tier": 0}),
    ]),
    # --- ornament / decoration ---
    ("SM_Cathedral_TraceryPanel", [
        ("MEL_ornament_panel", {"Panel Width": 3.0, "Panel Height": 4.5,
                                "Frame Width": 0.12, "Show Frame": True}),
    ]),
    ("SM_Cathedral_RosetteMedallion", [
        ("MEL_decorative_rosette", {"Outer Radius": 1.1, "Inner Radius": 0.35,
                                    "Petal Count": 8, "Bevel Thickness": 0.12}),
    ]),
    # --- slice props (documented missing meshes) ---
    ("SM_Cathedral_Bed", [
        ("MEL_castle_keep", {
            "Width": 2.2, "Depth": 1.4, "Height": 0.8, "Wall Thick": 1.1,
            "Tiers": 1, "Towers": False, "Battlements": False, "Windows Per Tier": 0}),
    ]),
    ("SM_Cathedral_Perch", [
        ("MEL_arch", {"Span": 1.0, "Height": 0.9, "Arch Rise": 0.5, "Thickness": 0.06, "Segments": 24}),
    ]),
    ("SM_Cathedral_ResonantDoor", [
        ("MEL_arch", {"Span": 2.4, "Height": 3.2, "Arch Rise": 1.6, "Thickness": 0.3, "Segments": 32}),
    ]),
    ("SM_Cathedral_CombatFloor", [
        ("MEL_castle_keep", {
            "Width": 16.0, "Depth": 10.0, "Height": 0.5, "Wall Thick": 5.5,
            "Tiers": 1, "Towers": False, "Battlements": False, "Windows Per Tier": 0}),
    ]),
    ("SM_Cathedral_BeatMedallion", [
        ("MEL_decorative_rosette", {"Outer Radius": 0.6, "Inner Radius": 0.18,
                                    "Petal Count": 8, "Bevel Thickness": 0.08}),
    ]),
    # --- hero centerpiece + speedcore segment ---
    ("SM_Cathedral_Observatory", [
        ("MEL_sky_observatory", {"Island Radius": 2.5, "Island Height": 1.2,
                                 "Drum Radius": 1.6, "Drum Height": 2.0,
                                 "Ring Count": 4, "Planets": True,
                                 "Deck Railing": True, "Lanterns": True, "Star Finial": True}),
    ]),
    ("SM_Cathedral_EscherBridge", [
        ("MEL_endless_escher_bridge", {"Bridge Length": 14.0, "Bridge Width": 2.2,
                                       "Step Height": 0.2, "Wave Amplitude": 0.8,
                                       "Wave Frequency": 2.0, "Arch Height": 2.5,
                                       "Step Count": 56}),
    ]),
    # --- dress-pass expansion (W1): statuary, stained glass, bridge kit, pavilions ---
    ("SM_Cathedral_SaintStatue", [
        ("MEL_column", {"Height": 3.4, "Radius": 0.38, "Sides": 16, "Fluted": True,
                        "Capital Height": 0.3, "Base Height": 0.22}),
    ]),
    ("SM_Cathedral_StainedGlassPanel", [
        ("MEL_ornament_panel", {"Panel Width": 1.6, "Panel Height": 3.2,
                                "Frame Width": 0.1, "Show Frame": True}),
    ]),
    ("SM_Cathedral_StainedRose", [
        ("MEL_decorative_rosette", {"Outer Radius": 1.5, "Inner Radius": 0.4,
                                    "Petal Count": 12, "Bevel Thickness": 0.15,
                                    "Center Dome Scale": 0.5}),
    ]),
    ("SM_Cathedral_BifrostBridge", [
        ("MEL_endless_escher_bridge", {"Bridge Length": 18.0, "Bridge Width": 2.6,
                                       "Step Height": 0.12, "Wave Amplitude": 0.35,
                                       "Wave Frequency": 1.5, "Arch Height": 3.0,
                                       "Step Count": 72}),
    ]),
    ("SM_Cathedral_Pavilion", [
        ("MEL_nikki_quarter", {"Mode": 1, "Tier Count": 3}),
    ]),
    ("SM_Cathedral_Stall", [
        ("MEL_gazebo", {"Radius": 1.7, "Column Count": 4, "Column Height": 2.4,
                        "Roof Pitch": 0.9, "Beam Radius": 0.06, "Has Finial": False}),
    ]),
    ("SM_Cathedral_Garland", [
        ("MEL_filigree_spiral", {"Inner Radius": 0.2, "Outer Radius": 1.1, "Turns": 4,
                                 "Taper Power": 1.2, "Profile Radius": 0.06,
                                 "Spiral Height": 0.15, "Resolution": 128}),
    ]),
    ("SM_Cathedral_TrebleRelief", [
        ("MEL_music_treble_clef", {"Scale": 2.5, "Thickness": 0.06}),
    ]),
    ("SM_Cathedral_MusicOrb", [
        ("MEL_harmonic_orb", {"Orb Radius": 0.6, "Ring Radius": 0.9,
                              "Ring Thickness": 0.05, "Orb Subdivisions": 3}),
    ]),
    # --- hero bakes (W4) ---
    ("SM_Cathedral_EscherBelvedere", [
        ("MEL_escher_belvedere", {}),
    ]),
    ("SM_Cathedral_EscherPenrose", [
        ("MEL_escher_penrose_stairs", {}),
    ]),
    ("SM_Cathedral_EscherWaterfall", [
        ("MEL_escher_waterfall", {}),
    ]),
]

# piece -> role tag (for world manifest + RPG mapping)
ROLES = {
    "SM_Cathedral_VaultBay": "nave_bay",
    "SM_Cathedral_RoseWindow": "facade_rose",
    "SM_Cathedral_Wall": "nave_wall",
    "SM_Cathedral_WallParapet": "parapet",
    "SM_Cathedral_LancetWindow": "clerestory_window",
    "SM_Cathedral_Buttress": "flying_buttress",
    "SM_Cathedral_Pier": "nave_pier",
    "SM_Cathedral_Portal": "portal",
    "SM_Cathedral_SpiralStairs": "tower_stairs",
    "SM_Cathedral_Tower": "tower",
    "SM_Cathedral_Spire": "spire",
    "SM_Cathedral_Crypt": "treasure_vault",
    "SM_Cathedral_CryptVault": "treasure_vault_ceiling",
    "SM_Cathedral_ChapterHouse": "puzzle_chamber",
    "SM_Cathedral_Chapel": "rest_sanctuary",
    "SM_Cathedral_Chandelier": "chandelier",
    "SM_Cathedral_StaffBalustrade": "triforium_rail",
    "SM_Cathedral_HarmonicOrb": "harmonic_orb",
    "SM_Cathedral_Altar": "boss_throne",
    "SM_Cathedral_TraceryPanel": "tracery_panel",
    "SM_Cathedral_RosetteMedallion": "rosette",
    "SM_Cathedral_Bed": "bed_save_sanctuary",
    "SM_Cathedral_Perch": "companion_perch",
    "SM_Cathedral_ResonantDoor": "resonant_door",
    "SM_Cathedral_CombatFloor": "combat_arena_floor",
    "SM_Cathedral_BeatMedallion": "beat_marker",
    "SM_Cathedral_Observatory": "observatory_centerpiece",
    "SM_Cathedral_EscherBridge": "corridor_bridge",
    "SM_Cathedral_SaintStatue": "statuary",
    "SM_Cathedral_StainedGlassPanel": "stained_glass",
    "SM_Cathedral_StainedRose": "stained_glass",
    "SM_Cathedral_BifrostBridge": "dreamstate_bridge",
    "SM_Cathedral_Pavilion": "festival_pavilion",
    "SM_Cathedral_Stall": "festival_stall",
    "SM_Cathedral_Garland": "festival_garland",
    "SM_Cathedral_TrebleRelief": "instrument_relief",
    "SM_Cathedral_MusicOrb": "instrument_artifact",
    "SM_Cathedral_EscherBelvedere": "escher_belvedere",
    "SM_Cathedral_EscherPenrose": "escher_penrose",
    "SM_Cathedral_EscherWaterfall": "escher_waterfall",
}

# simple trim materials (stone / gold / glass) - plain node materials, not builders
MATS = {
    "stone": (0.62, 0.60, 0.58, 1.0),
    "gold": (0.92, 0.78, 0.42, 1.0),
    "glass": (0.35, 0.55, 0.75, 0.6),
}
PIECE_MAT = {  # piece -> material key
    "SM_Cathedral_Chandelier": "gold",
    "SM_Cathedral_HarmonicOrb": "gold",
    "SM_Cathedral_Altar": "gold",
    "SM_Cathedral_TraceryPanel": "gold",
    "SM_Cathedral_RosetteMedallion": "gold",
    "SM_Cathedral_BeatMedallion": "gold",
    "SM_Cathedral_RoseWindow": "glass",
    "SM_Cathedral_LancetWindow": "glass",
    "SM_Cathedral_StaffBalustrade": "gold",
    "SM_Cathedral_StainedGlassPanel": "glass",
    "SM_Cathedral_StainedRose": "glass",
    "SM_Cathedral_SaintStatue": "stone",
    "SM_Cathedral_Garland": "gold",
    "SM_Cathedral_TrebleRelief": "gold",
    "SM_Cathedral_MusicOrb": "gold",
}


def log(msg: str) -> None:
    print(f"[cathedral-kit] {msg}", flush=True)


def ensure_materials() -> dict:
    made = {}
    for key, rgba in MATS.items():
        mat = bpy.data.materials.get(f"M_Cathedral_{key.title()}")
        if mat is None:
            mat = bpy.data.materials.new(f"M_Cathedral_{key.title()}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = rgba
                bsdf.inputs["Roughness"].default_value = 0.5
                bsdf.inputs["Metallic"].default_value = 0.25 if key == "gold" else 0.05
        made[key] = mat
    return made


def socket_identifier(tree, param_name: str) -> str | None:
    for item in tree.interface.items_tree:
        if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == param_name:
            return item.identifier
    return None


def set_socket(mod, param_name: str, value) -> bool:
    ident = socket_identifier(mod.node_group, param_name)
    if ident is None:
        log(f"  WARN no input '{param_name}' on {mod.node_group.name}")
        return False
    sock = getattr(mod.properties.inputs, ident, None)
    if sock is None or not hasattr(sock, "value"):
        log(f"  WARN input '{param_name}' not settable (geometry/enum)")
        return False
    try:
        from mathutils import Vector
        if isinstance(value, (tuple, list)):
            sock.value = Vector(value)
        else:
            sock.value = value
        return True
    except Exception as exc:
        log(f"  WARN set '{param_name}'={value}: {exc}")
        return False


def ensure_realize_helper() -> None:
    """Plumbing group (not a builder, not registered in the addon): feeds the
    instance-output of array stacks into a Realize Instances node. Blender 5.2
    does not realize GN instances at export time, so the tree must."""
    name = "CathedralKit_Realize"
    if name in bpy.data.node_groups:
        return
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    gin = tree.nodes.new("NodeGroupInput")
    gout = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    real = tree.nodes.new("GeometryNodeRealizeInstances")
    tree.links.new(gin.outputs[0], real.inputs[0])
    tree.links.new(real.outputs[0], gout.inputs[0])
    gin.location = (-300, 0)
    real.location = (0, 0)
    gout.location = (300, 0)


def build_piece(name: str, spec: list, materials: dict, realize: bool = False) -> bpy.types.Object | None:
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.modifiers.clear()
    for builder_name, params in spec:
        from surreal_arch.melodia_gn.core import GROUP_BUILDERS
        builder = GROUP_BUILDERS[builder_name]
        if builder_name not in bpy.data.node_groups:
            builder(builder_name)
        mod = obj.modifiers.new(builder_name, "NODES")
        mod.node_group = bpy.data.node_groups[builder_name]
        mod.name = builder_name
        for pname, pval in params.items():
            set_socket(mod, pname, pval)
    mat_key = PIECE_MAT.get(name)
    if mat_key:
        obj.data.materials.append(materials[mat_key])
    if realize:
        mod = obj.modifiers.new("RealizeInstances", "NODES")
        mod.node_group = bpy.data.node_groups["CathedralKit_Realize"]
    return obj


def real_dims(obj: bpy.types.Object) -> tuple[float, float, float]:
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    try:
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        return (round(max(xs) - min(xs), 3) if xs else 0.0,
                round(max(ys) - min(ys), 3) if ys else 0.0,
                round(max(zs) - min(zs), 3) if zs else 0.0)
    finally:
        ev.to_mesh_clear()


def count_mesh(obj: bpy.types.Object) -> tuple[int, int]:
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    try:
        return len(mesh.vertices), len(mesh.polygons)
    finally:
        ev.to_mesh_clear()


def export_fbx(obj: bpy.types.Object, path: str) -> tuple[bool, int, int]:
    """Export a realized copy: duplicate, apply every NODES modifier (this
    realizes instanced array geometry), then export. The original keeps its
    live, editable GN stack."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = obj.name + "_export"
    bpy.context.collection.objects.link(dup)
    bpy.ops.object.select_all(action="DESELECT")
    dup.select_set(True)
    bpy.context.view_layer.objects.active = dup
    try:
        bpy.ops.object.convert(target="MESH")
    except Exception as exc:
        log(f"  WARN convert: {exc}")
        for mod in list(dup.modifiers):
            if mod.type == "NODES":
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as exc2:
                    log(f"  WARN apply {mod.name}: {exc2}")
    verts = len(dup.data.vertices)
    tris = len(dup.data.polygons)
    tmp = os.path.join(ROOT, "Saved", "Audit", f"_tmp_{obj.name}.fbx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    try:
        bpy.ops.export_scene.fbx(
            filepath=tmp,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_NONE",
            axis_forward="-Y",
            axis_up="Z",
            mesh_smooth_type="FACE",
            use_mesh_modifiers=True,
        )
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
        shutil.copy2(tmp, path)
    except Exception as exc:
        log(f"  FAIL export {path}: {exc}")
        return False, verts, tris
    finally:
        bpy.data.objects.remove(dup, do_unlink=True)
    return True, verts, tris


def assemble_nave_scene() -> None:
    """Compose the 126 m Cadence Cathedral review composition (scene-level only)."""

    def place(src: bpy.types.Object, name: str, loc, rot=None):
        dup = src.copy()
        dup.data = src.data
        bpy.context.collection.objects.link(dup)
        dup.name = name
        dup.hide_viewport = False
        dup.hide_render = False
        dup.location = loc
        if rot:
            dup.rotation_euler = rot
        return dup

    pieces = {o.name: o for o in bpy.data.objects}
    bays = 15
    for i in range(bays):
        place(pieces["SM_Cathedral_VaultBay"], f"NAVE_Bay_{i:02d}", (8.0 * i, 0.0, 0.0))
    for side in (-1, 1):
        for i in range(bays):
            place(pieces["SM_Cathedral_Pier"], f"PIER_{side:+d}_{i:02d}", (8.0 * i + 4.0, side * 4.5, 0.0))
    for side in (-1, 1):
        for i in range(bays):
            place(pieces["SM_Cathedral_Buttress"], f"BUTTRESS_{side:+d}_{i:02d}",
                  (8.0 * i + 4.0, side * 7.6, 0.0), (0, 0, 1.5708))
    place(pieces["SM_Cathedral_RoseWindow"], "FACADE_RoseWindow", (8.0 * bays + 0.4, 0.0, 4.0))
    place(pieces["SM_Cathedral_Portal"], "FACADE_Portal", (8.0 * bays - 0.8, 0.0, 0.0))
    place(pieces["SM_Cathedral_Observatory"], "CROSSING_Observatory", (8.0 * 7, 0.0, 0.0))
    place(pieces["SM_Cathedral_EscherBridge"], "CORRIDOR_EscherBridge",
          (8.0 * 15 + 10.0, 0.0, 2.0), (0, 0, 1.5708))


def write_meta(name: str, dims, verts, tris, builders: list) -> None:
    meta = {
        "name": name,
        "role": ROLES.get(name, "prop"),
        "dims_m": list(dims),
        "verts": verts,
        "tris": tris,
        "gn_stack": [b[0] for b in builders],
    }
    with open(os.path.join(KIT_DIR, f"{name}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def main() -> int:
    from surreal_arch import melodia_gn  # registers every builder
    materials = ensure_materials()
    ensure_realize_helper()
    os.makedirs(KIT_DIR, exist_ok=True)
    results = []
    pieces = {}

    for entry in KIT:
        name, spec = entry[0], entry[1]
        realize = len(entry) > 2 and entry[2]
        obj = build_piece(name, spec, materials, realize=realize)
        if obj is None:
            results.append({"name": name, "ok": False})
            continue
        pieces[name] = obj
        verts, tris = count_mesh(obj)
        dims = real_dims(obj)
        log(f"built {name}: verts={verts} tris={tris} dims={dims}")
        out = os.path.join(KIT_DIR, f"{name}.fbx")
        ok, exp_verts, exp_tris = export_fbx(obj, out)
        verts, tris = (exp_verts, exp_tris) if ok else (verts, tris)
        write_meta(name, dims, verts, tris, spec)
        results.append({
            "name": name, "ok": ok, "verts": verts, "tris": tris,
            "dims_m": list(dims), "fbx": out if ok else None,
            "size": os.path.getsize(out) if ok else 0,
        })
        obj.hide_viewport = True
        obj.hide_render = True

    assemble_nave_scene()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "zero_face": [r["name"] for r in results if r["tris"] == 0],
        "results": results,
    }
    with open(AUDIT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    manifest = {
        "format": "surreal_arch_world_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "style": "gothic",
        "nave_length_m": 126.0,
        "rooms": [
            {"id": "combat_arena", "space": "nave_crossing", "pieces": ["SM_Cathedral_CombatFloor", "SM_Cathedral_BeatMedallion"], "rpg_tags": ["encounter_anchor", "rhythm_arena"]},
            {"id": "rest_sanctuary", "space": "side_chapel", "pieces": ["SM_Cathedral_Chapel", "SM_Cathedral_Bed"], "rpg_tags": ["save_point", "rest"]},
            {"id": "treasure_vault", "space": "crypt", "pieces": ["SM_Cathedral_Crypt", "SM_Cathedral_CryptVault"], "rpg_tags": ["treasure", "sealed"]},
            {"id": "boss_throne", "space": "high_altar", "pieces": ["SM_Cathedral_Altar", "SM_Cathedral_HarmonicOrb"], "rpg_tags": ["boss", "harmonic_power"]},
            {"id": "puzzle_chamber", "space": "chapter_house", "pieces": ["SM_Cathedral_ChapterHouse", "SM_Cathedral_TraceryPanel"], "rpg_tags": ["puzzle", "door_anchor"]},
            {"id": "corridor_bridge", "space": "cloister_gallery", "pieces": ["SM_Cathedral_StaffBalustrade", "SM_Cathedral_EscherBridge"], "rpg_tags": ["traversal", "speedcore_segment"]},
        ],
        "slice_props": [
            {"piece": "SM_Cathedral_Bed", "doc": "MELODIA_OPENING_BUILD_PREP bed/save sanctuary (no confirmed mesh)"},
            {"piece": "SM_Cathedral_Perch", "doc": "MELODIA_OPENING_BUILD_PREP Sir Melodious perch (no confirmed mesh)"},
            {"piece": "SM_Cathedral_ResonantDoor", "doc": "FIRST_20_MINUTES first Resonant Door"},
            {"piece": "SM_Cathedral_Observatory", "doc": "HERO_GRAPH_REVIEW_QUEUE KaleidoNave centerpiece"},
        ],
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    log(f"evidence {AUDIT} / manifest {MANIFEST}")

    try:
        bpy.ops.wm.save_as_mainfile(filepath=REVIEW_BLEND)
        log(f"review blend saved {REVIEW_BLEND}")
    except Exception as exc:
        log(f"WARN review blend save: {exc}")
    return 0 if summary["ok"] == len(KIT) else 1


if __name__ == "__main__":
    raise SystemExit(main())
