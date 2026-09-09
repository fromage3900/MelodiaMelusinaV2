# -*- coding: utf-8 -*-
"""p03 — transformation rig: split-waist reel deployment via shape keys + drivers.

Pattern proven on WaveHarp: driver + shape-key rig, no armature.
Master control: ME_WaveViolin_Control.rotation_euler.x, -PI/2 (stowed) -> 0 (deployed).
Shape key values driven via shape_keys.driver_add('key_block_eval["X"]').
Idempotent: removes prior drivers/keys before rebuilding.
"""
import bpy, json, math, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p03] {m}", flush=True)
mc = bpy.data.objects["ME_WaveViolin_Control"]
EXPR_T = "max(0.0, min(1.0, (var + 1.5708) / 1.5708))"   # t 0..1

def bind_driver(fcurve, expr):
    for v in list(fcurve.driver.variables):
        fcurve.driver.variables.remove(v)
    fcurve.driver.expression = expr
    v = fcurve.driver.variables.new()
    v.name = "var"; v.type = 'SINGLE_PROP'
    v.targets[0].id = mc
    v.targets[0].data_path = "rotation_euler[0]"
    return fcurve

def ensure_basis(ob):
    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)

def set_shapekey(ob, name, fn):
    ensure_basis(ob)
    sks = ob.data.shape_keys
    if name in [k.name for k in sks.key_blocks]:
        ob.shape_key_remove(sks.key_blocks[name])
    sk = ob.shape_key_add(name=name, from_mix=False)
    for i, v in enumerate(ob.data.vertices):
        sk.data[i].co = fn(Vector(v.co))
    return sk

def drive_key(ob, name):
    """driver on the shape key value: fcurve lives on the Key datablock"""
    sks = ob.data.shape_keys
    if not sks.animation_data:
        sks.animation_data_create()
    for fc in list(sks.animation_data.drivers):
        if f'key_blocks["{name}"]' in fc.data_path:
            sks.driver_remove(fc.data_path)
    fc = sks.driver_add(f'key_blocks["{name}"].value')
    return bind_driver(fc, EXPR_T)

rigged = []

# 1) body split at waist: bouts separate laterally, belly rises
for nm, sign in (("ME_WaveViolin_UpperBout", 1), ("ME_WaveViolin_LowerBout", -1),
                 ("ME_WaveViolin_BellyPlate", 0)):
    ob = bpy.data.objects.get(nm)
    if not ob: continue
    if sign:
        set_shapekey(ob, "Reel_Deploy", lambda c, s=sign: c + Vector((0.09 * s, 0, 0)))
    else:
        set_shapekey(ob, "Reel_Deploy", lambda c: c + Vector((0, -0.025, 0)))
    drive_key(ob, "Reel_Deploy")
    rigged.append(nm)

# 2) scroll crank spins -360deg across deploy
scr = bpy.data.objects.get("ME_WaveViolin_Scroll")
if scr:
    for i in (0, 1, 2):
        try: scr.driver_remove("rotation_euler", i)
        except Exception: pass
    fc = scr.driver_add("rotation_euler", 2)
    bind_driver(fc, "((var + 1.5708) / 1.5708) * -6.2832")
    rigged.append("ME_WaveViolin_Scroll(crank)")

# 3) strings: lateral fan following the bout split (top-anchored spread)
for i in (1, 2, 3, 4):
    ob = bpy.data.objects.get(f"ME_WaveViolin_String_{i}")
    if not ob: continue
    x0 = ob.location.x or 0.001
    set_shapekey(ob, "Reel_Deploy",
        lambda c, x=x0: c + Vector((math.copysign(0.09, x) * max(c.z, 0) / 0.43, 0, 0)))
    drive_key(ob, "Reel_Deploy")
    rigged.append(ob.name)

# 4) three pose plates
scn = bpy.context.scene
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = -math.pi / 2   # basis for render below at stow
bpy.context.view_layer.update()
for tag, rx in (("stow", -math.pi/2), ("half", -math.pi/4), ("deploy", 0.0)):
    mc.rotation_euler.x = rx
    bpy.context.view_layer.update()
    scn.render.filepath = os.path.join(OUT, f"p03_{tag}.png")
    bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -math.pi / 2
bpy.ops.wm.save_mainfile()
json.dump({"phase": "p03", "ok": True, "rigged": rigged, "plates": 3},
          open(os.path.join(OUT, "p03_report.json"), "w"), indent=1)
log(f"done rigged={len(rigged)}")
