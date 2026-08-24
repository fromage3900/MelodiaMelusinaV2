"""End-to-end test: enable the addon, build a level, verify measured output."""

import bpy
import os
import sys
import json

report = {}


def main():
    bpy.ops.preferences.addon_enable(module="resonant_world_studio")
    report["enabled"] = True

    props = bpy.context.scene.resonant_world
    midis = [i[0] for i in
             props.bl_rna.properties["midi"].enum_items] if False else None

    # Pick the substantial project MIDI explicitly.
    from resonant_world_studio import bridge
    target = os.path.join(bridge.midi_dir(), "128BPMarpeggiomelody.mid")
    report["midi_exists"] = os.path.exists(target)
    props.midi = target
    props.preset = "walkable_highlands"
    props.style = "crystalline"
    props.eye_level = True
    props.with_melusina = True

    res = bpy.ops.resonant_world.build()
    report["build_result"] = list(res)

    raw = props.report_json
    report["has_report"] = bool(raw)
    if raw:
        report["metrics"] = json.loads(raw)

    # Scene assertions
    terrain = bpy.data.objects.get("RW_Terrain")
    report["terrain_present"] = terrain is not None
    if terrain:
        report["terrain_polys"] = len(terrain.data.polygons)
        report["has_aura_attr"] = "AuraColor" in {
            c.name for c in terrain.data.color_attributes}
        report["material_count"] = len(terrain.data.materials)
        report["has_uv"] = len(terrain.data.uv_layers) > 0

    dressing = bpy.data.collections.get("RW_Dressing")
    report["prop_instances"] = len(dressing.all_objects) if dressing else 0

    rig = bpy.data.collections.get("RW_Rig")
    report["rig_objects"] = len(rig.all_objects) if rig else 0
    report["scene_camera"] = (bpy.context.scene.camera.name
                             if bpy.context.scene.camera else None)

    # Melusina must stand on the local column, not the bbox top.
    root = bpy.data.objects.get("RW_Melusina_Root")
    report["melusina_present"] = root is not None
    if root:
        report["melusina_z"] = round(root.location.z, 3)
        from resonant_world_studio import bridge as br
        _ww, td = br.load_modules()
        field2, _p2, _m2 = br.build_field(target, "walkable_highlands")
        local_ground = td.surface_height_at(field2, root.location.x,
                                             root.location.y)
        report["melusina_local_ground"] = local_ground
        report["melusina_gap"] = round(root.location.z - local_ground, 3)

    # Eye-level camera must sit ABOVE the local column, not inside it.
    if terrain and bpy.context.scene.camera:
        from resonant_world_studio import bridge as br
        _ww, td = br.load_modules()
        field, _p, _m = br.build_field(target, "walkable_highlands")
        cam = bpy.context.scene.camera
        ground = td.surface_height_at(field, cam.location.x, cam.location.y)
        report["camera_z"] = round(cam.location.z, 3)
        report["camera_local_ground"] = ground
        report["camera_above_ground"] = round(cam.location.z - ground, 3)

    # Idempotency: build twice, prop count must not double.
    bpy.ops.resonant_world.build()
    d2 = bpy.data.collections.get("RW_Dressing")
    report["prop_instances_after_rebuild"] = len(d2.all_objects) if d2 else 0
    report["idempotent"] = (report["prop_instances"] ==
                            report["prop_instances_after_rebuild"])

    # Render proof
    out = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\resonant_world_studio\addon_proof.png"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc = bpy.context.scene
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    report["render_ok"] = os.path.exists(out)
    if report["render_ok"]:
        report["render_bytes"] = os.path.getsize(out)
        report["render_path"] = out

    bpy.ops.resonant_world.export_report()

    bpy.ops.resonant_world.clear()
    report["cleared"] = bpy.data.objects.get("RW_Terrain") is None

    verdict = (report.get("terrain_present") and report.get("has_aura_attr")
               and report.get("material_count", 0) > 0
               and report.get("prop_instances", 0) > 0
               and report.get("camera_above_ground", -1) > 0.5
               and report.get("melusina_present")
               and abs(report.get("melusina_gap", 99)) < 0.35
               and report.get("idempotent")
               and report.get("render_ok")
               and report.get("cleared"))
    report["verdict"] = "PASS" if verdict else "FAIL"


if __name__ == "__main__":
    code = 0
    try:
        main()
    except Exception:
        import traceback
        report["error"] = traceback.format_exc()[-1500:]
        report["verdict"] = "ERROR"
        code = 1
    dest = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                        "Temp", "rws_addon_test.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("VERDICT", report.get("verdict"))
    print(json.dumps(report, indent=2)[:2600])
    sys.stdout.flush()
    os._exit(code)
