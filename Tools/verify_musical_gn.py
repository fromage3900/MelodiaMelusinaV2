"""Verify and polish musical GN builders in Blender 5.2.

Checks:
1. All builders register without errors
2. Node IDs are valid for 5.2
3. Builders produce non-empty geometry
4. No NaN/Inf in outputs

  blender --background --factory-startup --python verify_musical_gn.py
"""

import bpy
import os
import sys
import json
import math
import traceback

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
GN_DIR = os.path.join(REPO, "deploy", "surreal_arch", "melodia_gn")
PARENT = os.path.join(REPO, "deploy", "surreal_arch")
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

# Import as package to handle relative imports
from surreal_arch.melodia_gn import core
from surreal_arch.melodia_gn import music
from surreal_arch.melodia_gn import music_aaa
from surreal_arch.melodia_gn import music_heroes
from surreal_arch.melodia_gn import music_instruments

report = {"blender": bpy.app.version_string, "builders": []}


def probe_builder(name, builder_fn, params=None):
    """Build a group, verify interface, produce render-proof mesh."""
    entry = {"name": name, "ok": False, "errors": []}
    try:
        # Clear any existing group
        if name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[name])

        builder_fn(name)

        if name not in bpy.data.node_groups:
            entry["errors"].append("group not created")
            return entry

        ng = bpy.data.node_groups[name]
        entry["nodes"] = len(ng.nodes)
        entry["links"] = len(ng.links)

        # Check for NaN in default values — skip geometry/shader sockets
        nan_found = False
        for node in ng.nodes:
            for inp in node.inputs:
                if inp.type in ('GEOMETRY', 'SHADER', 'TEXTURE', 'MATERIAL',
                                'COLLECTION', 'OBJECT', 'IMAGE', 'STRING'):
                    continue
                try:
                    dv = inp.default_value
                except AttributeError:
                    continue
                for val in (dv if hasattr(dv, '__iter__') else [dv]):
                    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                        nan_found = True
            if nan_found:
                break
        entry["nan_values"] = nan_found

        # Verify interface: count inputs/outputs
        iface = getattr(ng, "interface", None)
        if iface is not None:
            # Blender 5.2 uses items_tree (not sockets)
            items = list(iface.items_tree) if hasattr(iface, "items_tree") else []
            entry["inputs"] = len([s for s in items if getattr(s, "in_out", None) == "INPUT"])
            entry["outputs"] = len([s for s in items if getattr(s, "in_out", None) == "OUTPUT"])
            in_names = [s.name for s in items if getattr(s, "in_out", None) == "INPUT"]
            entry["duplicate_inputs"] = len(in_names) != len(set(in_names))
        else:
            entry["inputs"] = len([s for s in ng.inputs])
            entry["outputs"] = len([s for s in ng.outputs])

        # Render-proof: need a mesh object for GN modifier input
        proof_name = "_proof_%s" % name
        for obj in [o for o in bpy.data.objects if o.name.startswith(proof_name)]:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Create a simple plane mesh as input for the modifier
        me = bpy.data.meshes.new(proof_name)
        me.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)], [], [(0,1,2,3)])
        empty = bpy.data.objects.new(proof_name, me)
        bpy.context.scene.collection.objects.link(empty)

        mod = empty.modifiers.new(name=proof_name, type='NODES')
        mod.node_group = ng

        # Force depsgraph eval
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = empty.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        if mesh is None:
            entry["errors"].append("evaluated to no mesh")
        else:
            entry["verts"] = len(mesh.vertices)
            entry["edges"] = len(mesh.edges)
            entry["polygons"] = len(mesh.polygons)

            # Check for NaN in vertex positions
            nan_verts = 0
            for v in mesh.vertices:
                for co in v.co:
                    if math.isnan(co) or math.isinf(co):
                        nan_verts += 1
                        break
            entry["nan_vertices"] = nan_verts

            # Check for zero-area faces
            zero_area = sum(1 for p in mesh.polygons if p.area < 1e-12)
            entry["zero_area_faces"] = zero_area

            eval_obj.to_mesh_clear()

        # Self-contained pass criteria
        has_geometry = entry.get("polygons", 0) > 0
        no_nans = not entry.get("nan_values", False) and not entry.get("nan_vertices", False)
        no_dup_inputs = not entry.get("duplicate_inputs", False)
        entry["ok"] = has_geometry and no_nans and no_dup_inputs and not entry["errors"]

    except Exception as e:
        entry["errors"].append(traceback.format_exc()[-800:])

    return entry


def main():
    # Imported as package at top of file — use those references.
    builders = [
        # music.py
        ("MEL_music_note_head", music.build_music_note_head),
        ("MEL_music_treble_clef", music.build_music_treble_clef),
        ("MEL_music_staff", music.build_music_staff),
        ("MEL_music_harmonic", music.build_music_harmonic),
        ("MEL_music_phrase", music.build_music_phrase),
        ("MEL_music_sheet_rail", music.build_music_sheet_rail),
        # music_aaa.py
        ("MEL_music_waveform_wall", music_aaa.build_music_waveform_wall),
        ("MEL_music_vinyl_disc", music_aaa.build_music_vinyl_disc),
        ("MEL_music_lissajous_harp", music_aaa.build_music_lissajous_harp),
        ("MEL_imm_piano_keys", music_aaa.build_imm_piano_keys),
        ("MEL_music_frequency_ribcage", music_aaa.build_music_frequency_ribcage),
        ("MEL_music_tuning_fork", music_aaa.build_music_tuning_fork),
        ("MEL_music_metronome_pillar", music_aaa.build_music_metronome_pillar),
        ("MEL_music_soundhole_rosette", music_aaa.build_music_soundhole_rosette),
        ("MEL_music_harmonograph", music_aaa.build_music_harmonograph),
        # music_heroes.py
        ("MEL_music_key_unit", music_heroes.build_music_key_unit),
        ("MEL_music_piano_roll", music_heroes.build_music_piano_roll),
        ("MEL_music_room_shell", music_heroes.build_music_room_shell),
        ("MEL_music_harp", music_heroes.build_music_harp),
        # music_instruments.py
        ("MEL_brass_pipe", music_instruments.build_brass_pipe),
        ("MEL_reed_body", music_instruments.build_reed_body),
        ("MEL_bell_chime", music_instruments.build_bell_chime),
        ("MEL_tuning_fork", music_instruments.build_tuning_fork),
        ("MEL_singing_bowl", music_instruments.build_singing_bowl),
        ("MEL_church_bell", music_instruments.build_church_bell),
    ]

    ok_count = 0
    for name, fn in builders:
        entry = probe_builder(name, fn)
        if entry["ok"]:
            ok_count += 1
        report["builders"].append(entry)
        status = "OK" if entry["ok"] else "FAIL"
        extra = ""
        if entry.get("errors"):
            extra = " | " + str(entry["errors"])[:60]
        if entry.get("nan_values"):
            extra += " | NaN defaults!"
        if entry.get("nan_vertices", 0):
            extra += " | NaN verts!"
        if entry.get("duplicate_inputs"):
            extra += " | DUP INPUTS!"
        print("  %-38s %s nodes=%-4d in=%-3d out=%-3d v=%-6d p=%-6d%s" % (
            name, status, entry.get("nodes", 0), entry.get("inputs", 0),
            entry.get("outputs", 0), entry.get("verts", 0),
            entry.get("polygons", 0), extra), flush=True)

    report["summary"] = {"total": len(builders), "ok": ok_count, "fail": len(builders) - ok_count}
    report["verdict"] = "PASS" if ok_count == len(builders) else "FAIL"

    dest = os.path.join(os.environ.get("LOCALAPPDATA", REPO), "Temp", "musical_gn_verify.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\n%s/%d builders OK" % (ok_count, len(builders)), flush=True)
    print("VERDICT:", report["verdict"], flush=True)
    print("REPORT %s" % dest, flush=True)


if __name__ == "__main__":
    code = 0
    try:
        main()
    except Exception:
        import traceback
        report["error"] = traceback.format_exc()[-1500:]
        report["verdict"] = "ERROR"
        code = 1
    dest = os.path.join(os.environ.get("LOCALAPPDATA", REPO), "Temp", "musical_gn_verify.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("REPORT %s" % dest, flush=True)
    sys.stdout.flush()
    os._exit(code)
