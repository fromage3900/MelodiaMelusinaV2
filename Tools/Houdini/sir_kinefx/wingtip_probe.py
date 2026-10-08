"""Wing-tip travel probe: v5 vs v6 Sir clips (Blender headless, read-only).

For each A_Sir_*_{v5,v6}_ARP.fbx in exports/ue_arp: import, find the
armature, sample every deform feather-bone head (world space) across the
clip frame range, and report per-side max vertical travel, L/R symmetry,
loop seam (first-vs-last pose), and stroke count estimate.

Writes Saved/Audit/sirmelodious_kinefx_doctor/wingtip_probe.json.
Touches no source, exports nothing.

  blender --background --python Tools/Houdini/sir_kinefx/wingtip_probe.py
"""
import bpy
import json
import math
from mathutils import Vector
from pathlib import Path

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
CLIP_DIR = REPO / "Saved/Audit/SirMelodious_FlightUnit_20261003/exports/ue_arp"
OUT = REPO / "Saved/Audit/sirmelodious_kinefx_doctor/wingtip_probe.json"
FPS = 24

CLIPS = sorted(p for p in CLIP_DIR.glob("A_Sir_*_ARP.fbx")
               if any(f"_v{i}_ARP.fbx" in p.name for i in (5, 6)))


def wipe():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for b in list(datablocks):
            datablocks.remove(b)


def analyze(path: Path) -> dict:
    wipe()
    bpy.ops.import_scene.fbx(filepath=str(path))
    rig = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if rig is None:
        return {"file": path.name, "error": "no armature on import"}
    bpy.context.view_layer.objects.active = rig
    action = rig.animation_data.action if rig.animation_data else None
    feathers = [b.name for b in rig.data.bones
                if "feather" in b.name.lower() and not b.name.endswith("_bone")]
    per_side: dict[str, dict] = {}
    scene = bpy.context.scene
    if action:
        f0, f1 = int(action.frame_range[0]), int(action.frame_range[1])
    else:
        f0, f1 = 1, 1
    n = f1 - f0 + 1
    for side in ("l", "r"):
        names = sorted(b for b in feathers
                       if b.endswith("_" + side) or b.endswith("." + side))
        tracks = {}
        for bname in names:
            zs = []
            for f in range(f0, f1 + 1):
                scene.frame_set(f)
                bpy.context.view_layer.update()
                pb = rig.pose.bones[bname]
                zs.append((rig.matrix_world @ pb.head).z)
            tracks[bname] = zs
        if not tracks:
            per_side[side] = {"error": "no feather bones"}
            continue
        travel = {k: max(v) - min(v) for k, v in tracks.items()}
        tip = max(travel, key=travel.get)
        zs = tracks[tip]
        mean = sum(zs) / len(zs)
        # stroke estimate: mean up-crossings / duration
        ups = sum(1 for a, b in zip(zs, zs[1:]) if a < mean <= b)
        secs = n / FPS
        per_side[side] = {
            "tip_bone": tip,
            "tip_travel_cm": round(travel[tip] * 100, 2),
            "bones_measured": len(tracks),
            "upstrokes": ups,
            "stroke_hz": round(ups / secs, 2) if secs else 0,
            "frames": n,
        }
    # loop seam: first-vs-last head distance over feather bones
    seam = None
    if action and n > 1:
        ds = []
        for side in ("l", "r"):
            for bname in sorted(b for b in feathers
                               if b.endswith("_" + side) or b.endswith("." + side)):
                scene.frame_set(f0)
                bpy.context.view_layer.update()
                p0 = (rig.matrix_world @ rig.pose.bones[bname].head).copy()
                scene.frame_set(f1)
                bpy.context.view_layer.update()
                p1 = rig.matrix_world @ rig.pose.bones[bname].head
                ds.append((p1 - p0).length)
        seam = round(max(ds) * 1000, 2) if ds else None
    l, r = per_side.get("l", {}), per_side.get("r", {})
    sym = (round(min(l.get("tip_travel_cm", 0), r.get("tip_travel_cm", 0))
                 / max(l.get("tip_travel_cm", 1e-9), r.get("tip_travel_cm", 1e-9)), 3)
           if "tip_travel_cm" in l and "tip_travel_cm" in r else None)
    return {"file": path.name, "frames": n, "fps": FPS,
            "left": l, "right": r, "lr_symmetry": sym, "seam_max_mm": seam}


def main():
    rep = {"clips": {}}
    for p in CLIPS:
        try:
            rep["clips"][p.name] = analyze(p)
        except Exception as e:  # noqa: BLE001
            import traceback
            rep["clips"][p.name] = {"error": traceback.format_exc()[-800:]}
    OUT.write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "error"}
                      for k, v in rep["clips"].items()}, indent=1))
    print("wrote", OUT)


main()
