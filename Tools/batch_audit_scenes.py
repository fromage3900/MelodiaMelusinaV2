"""Batch audit all GeneratedScenes: open, verify, render preview, ledger.

For each scene directory in Tools/MelodiaProceduralStudio/GeneratedScenes:
  - Open the .blend headless
  - Capture stats (objects, meshes, materials, triangles, bounds)
  - Render a preview PNG
  - Record to a JSON ledger

Scenes that fail to open or render are flagged, not silently skipped.

  blender --background --factory-startup --python batch_audit_scenes.py
"""

import bpy
import os
import sys
import json
import math
import time

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
SCENES_DIR = os.path.join(REPO, "Tools", "MelodiaProceduralStudio", "GeneratedScenes")
OUT_DIR = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\scene_batch_audit"
LEDGER = os.path.join(OUT_DIR, "ledger.json")

report = {"blender": bpy.app.version_string, "scenes": [], "started": time.strftime("%Y-%m-%d %H:%M:%S")}


def scene_stats():
    """Collect measurable stats from the current scene.
    
    After open_mainfile, the load is async — force an update so
    bpy.data.objects is actually populated before we count.
    """
    # Force depsgraph update to complete async load
    bpy.context.view_layer.update()
    if bpy.context.evaluated_depsgraph_get() is not None:
        try:
            bpy.context.evaluated_depsgraph_get().update()
        except Exception:
            pass
    
    stats = {
        "objects": len(bpy.data.objects),
        "meshes": len(bpy.data.meshes),
        "materials": len(bpy.data.materials),
        "lights": len(bpy.data.lights),
        "cameras": len(bpy.data.cameras),
        "collections": len(bpy.data.collections),
        "worlds": len(bpy.data.worlds),
    }
    
    # Triangle count
    tris = 0
    for me in bpy.data.meshes:
        for p in me.polygons:
            tris += len(p.vertices) - 2
    stats["triangles"] = tris
    
    # Bounds
    mn = [1e18, 1e18, 1e18]
    mx = [-1e18, -1e18, -1e18]
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                for i in range(3):
                    mn[i] = min(mn[i], w[i])
                    mx[i] = max(mx[i], w[i])
    stats["bounds_min"] = [round(v, 3) for v in mn]
    stats["bounds_max"] = [round(v, 3) for v in mx]
    
    # Active camera
    stats["active_camera"] = bpy.context.scene.camera.name if bpy.context.scene.camera else None
    
    return stats


def render_preview(output_path):
    """Render the current scene to a PNG."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 640
    sc.render.resolution_y = 360
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = output_path
    
    # Use active camera or create one
    if sc.camera is None:
        # Find first camera
        cam = None
        for o in bpy.data.objects:
            if o.type == 'CAMERA':
                cam = o
                break
        if cam is None:
            # Create camera at origin looking at scene
            cam_data = bpy.data.cameras.new("BatchCam")
            cam = bpy.data.objects.new("BatchCam", cam_data)
            bpy.context.scene.collection.objects.link(cam)
            cam.location = (5, -5, 3)
            cam.rotation_euler = (math.radians(70), 0, math.radians(45))
        sc.camera = cam
    
    bpy.ops.render.render(write_still=True)
    return os.path.exists(output_path)


def process_scene(dir_name, blend_files):
    """Process a single scene directory."""
    entry = {"name": dir_name, "blends": blend_files, "ok": False, "errors": []}
    
    if not blend_files:
        entry["errors"].append("no .blend files")
        return entry
    
    # Use the first (or primary) blend
    blend_path = os.path.join(SCENES_DIR, dir_name, blend_files[0])
    entry["file"] = blend_files[0]
    
    try:
        # Open the blend directly (replaces current scene)
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        entry["opened"] = True
        
        # Poll for load completion — use scene collection refresh
        for i in range(30):
            # Access scene collection to force refresh
            if bpy.context.scene:
                bpy.context.scene.collection.name  # touch collection
                bpy.context.scene.update_tag()
            bpy.context.view_layer.update() if bpy.context.view_layer else None
            if len(bpy.data.objects) > 0:
                break
        
        print("  loaded %d objs after %d polls" % (len(bpy.data.objects), i+1), flush=True)
        
        # Collect stats
        entry["stats"] = scene_stats()
        
        # Render preview
        preview_path = os.path.join(OUT_DIR, "previews", dir_name + ".png")
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        
        try:
            entry["preview_ok"] = render_preview(preview_path)
            entry["preview_path"] = preview_path
        except Exception as e:
            entry["preview_ok"] = False
            entry["errors"].append("render: %s" % str(e)[:100])
        
        entry["ok"] = True
        
    except Exception as e:
        entry["errors"].append(str(e)[:200])
    
    return entry


def main():
    import mathutils
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "previews"), exist_ok=True)
    
    # Find all scene directories
    scene_dirs = []
    for d in sorted(os.listdir(SCENES_DIR)):
        full = os.path.join(SCENES_DIR, d)
        if not os.path.isdir(full):
            continue
        blends = [f for f in os.listdir(full) if f.endswith('.blend')]
        scene_dirs.append((d, blends))
    
    print("Found %d scene directories" % len(scene_dirs), flush=True)
    
    for i, (dir_name, blends) in enumerate(scene_dirs):
        print("[%d/%d] %s ..." % (i+1, len(scene_dirs), dir_name), flush=True)
        entry = process_scene(dir_name, blends)
        report["scenes"].append(entry)
        status = "OK" if entry["ok"] else "FAIL"
        tris = entry.get("stats", {}).get("triangles", 0)
        print("  %s | objs=%d tris=%d" % (status, entry.get("stats", {}).get("objects", 0), tris), flush=True)
    
    # Summary
    ok_count = sum(1 for s in report["scenes"] if s["ok"])
    report["summary"] = {
        "total": len(report["scenes"]),
        "ok": ok_count,
        "fail": len(report["scenes"]) - ok_count,
    }
    report["verdict"] = "PASS" if ok_count == len(report["scenes"]) else "FAIL"
    
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print("\n%s/%d scenes OK" % (ok_count, len(report["scenes"])), flush=True)
    print("LEDGER %s" % LEDGER, flush=True)


if __name__ == "__main__":
    code = 0
    try:
        main()
    except Exception:
        import traceback
        report["error"] = traceback.format_exc()[-1500:]
        report["verdict"] = "ERROR"
        code = 1
    finally:
        sys.stdout.flush()
        os._exit(code)
