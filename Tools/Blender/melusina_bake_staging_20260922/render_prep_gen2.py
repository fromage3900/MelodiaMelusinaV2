# Render prep gen2: Nikki polish on the prep blend.
# 1. Duplicate the water material per hair mesh and multiply THAT mesh's baked AO
#    into the emission color path (strand-depth variation; kills the "purple jelly" read).
# 2. Add a three-point area rig (key/fill/rim) aimed at the character — the review's
#    single biggest win (silhouette -> readable hero).
# 3. Save gen2, render one verify still, gate exposure, auto-adjust energy once.
import bpy, json, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922"
PREP2 = os.path.join(LANE, "harp_render_prep_gen2.blend")
EV = os.path.join(LANE, "render_prep_gen2_evidence.json")
COP = os.path.join(LANE, "copernicus_out")
RENDER_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\PIE\melusina_hair_flip_20260922"

HAIR = [("Hair Strand.004", "Melusina_HairA_Strand004"),
        ("Hair Strand.007", "Melusina_HairB_Strand007"),
        ("Hair Strand.010", "Melusina_C_Strand010_will_fallback")]
HAIR = [("Hair Strand.004", "Melusina_HairA_Strand004"),
        ("Hair Strand.007", "Melusina_HairB_Strand007"),
        ("Hair Strand.010", "Melusina_HairC_Strand010")]

scene = bpy.context.scene
ev = {"schema": "melodia.render_prep_gen2.v1", "water_wiring": [], "lights": []}

# ---- 1. per-mesh water materials with baked AO in the emission path ----
base = bpy.data.materials.get("Water (Advance).002")
for obj_name, stem in HAIR:
    ob = bpy.data.objects.get(obj_name)
    if not ob or not base:
        ev["water_wiring"].append({"object": obj_name, "verdict": "MISSING"})
        continue
    mat = base.copy()
    mat.name = "Water_Advance_AO_" + stem.split("_")[-1]
    nt = mat.node_tree
    ao_png = os.path.join(COP, stem, "T_%s_BaseColor.png" % stem)
    if not os.path.isfile(ao_png):
        ev["water_wiring"].append({"object": obj_name, "verdict": "AO_PNG_MISSING"})
        continue
    img = bpy.data.images.load(ao_png, check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.label = "Copernicus AO " + stem
    tex.name = "COPERNICUS_AO"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.label = "AO strand-depth multiply"
    mix.inputs[0].default_value = 0.85   # keep some unmodulated glow
    emiss = next((n for n in nt.nodes if n.type == "EMISSION"), None)
    wired = False
    if emiss:
        cin = emiss.inputs["Color"]
        if cin.is_linked:
            src = cin.links[0].from_socket
            nt.links.new(src, mix.inputs[6])
        else:
            mix.inputs[6].default_value = tuple(cin.default_value)
        nt.links.new(tex.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], cin)
        wired = True
    # assign
    for ms in ob.material_slots:
        if ms.material == base:
            ms.material = mat
    ev["water_wiring"].append({"object": obj_name, "material": mat.name,
                               "verdict": "WIRED" if wired else "NO_EMISSION_NODE"})

# ---- 2. three-point rig ----
TARGET = Vector((0.0, -0.05, 1.15))
def add_area(name, loc, energy, color, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.color = color
    data.size = size
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    d = TARGET - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob

key = add_area("RIG_Key_Warm", (2.6, -2.2, 2.4), 1800, (1.0, 0.92, 0.80), 2.0)
fill = add_area("RIG_Fill_Neutral", (-2.8, -1.8, 1.6), 540, (0.95, 0.97, 1.0), 2.5)
rim = add_area("RIG_Rim_Cool", (-1.5, 3.0, 2.6), 3000, (0.72, 0.84, 1.0), 1.2)
ev["lights"] = [{"name": l.name, "energy": l.data.energy} for l in (key, fill, rim)]

# ---- 3. save gen2 + verify still with exposure gate ----
# The sequence runs Cycles (EEVEE animation crashes the NV GL driver headless);
# the exposure gate must measure the same engine.
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for dev_type in ('OPTIX', 'CUDA', 'NONE'):
    try:
        prefs.compute_device_type = dev_type
        prefs.get_devices()
        for d in prefs.devices:
            d.use = dev_type != 'NONE'
        scene.cycles.device = 'GPU' if dev_type != 'NONE' else 'CPU'
        ev["cycles_device"] = dev_type
        break
    except Exception as e:
        ev["cycles_device_error"] = str(e)[:120]
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.filepath = os.path.join(RENDER_DIR, "lit_")
bpy.ops.wm.save_as_mainfile(filepath=PREP2)
scene.frame_set(60)
bpy.ops.render.render(write_still=True)
still = os.path.join(RENDER_DIR, "lit_.png")

def exposure_stats(path):
    """Subject-region gate: center 40% crop (the character), not the whole frame —
    the full frame is dominated by sky and passes even when the subject is a silhouette."""
    img = bpy.data.images.load(path)
    w, h = img.size
    px = img.pixels[:]
    bpy.data.images.remove(img)
    vals = []
    r0, r1, c0, c1 = int(h * 0.3), int(h * 0.7), int(w * 0.3), int(w * 0.7)
    step = max(1, ((r1 - r0) * (c1 - c0)) // 150000)
    for row in range(r0, r1, 2):
        base = row * w
        for col in range(c0, c1, 2 * step):
            i = (base + col) * 4
            vals.append(px[i] * 0.299 + px[i + 1] * 0.587 + px[i + 2] * 0.114)
    mean = sum(vals) / len(vals)
    nb = sum(1 for v in vals if v < 0.05) / len(vals)
    return round(mean, 3), round(nb, 3)

mean, nb = exposure_stats(still)
ev["verify_still"] = {"path": still, "subject_mean": mean, "subject_near_black": nb}
if mean < 0.10 or mean > 0.32:
    k = 0.20 / max(mean, 1e-3)
    k = min(max(k, 0.5), 3.0)
    for l in (key, fill, rim):
        l.data.energy = min(l.data.energy * k, 12000)
    bpy.ops.render.render(write_still=True)
    mean2, nb2 = exposure_stats(still)
    ev["verify_still"]["subject_mean_after_adjust"] = mean2
    ev["verify_still"]["subject_near_black_after_adjust"] = nb2
    ev["verify_still"]["energy_scale"] = round(k, 3)
bpy.ops.wm.save_as_mainfile(filepath=PREP2)
ev["prep2"] = PREP2
with open(EV, "w", encoding="utf-8") as f:
    json.dump(ev, f, indent=1)
print("PREP2:", json.dumps(ev["verify_still"]))
print("water wiring:", [(w["object"], w["verdict"]) for w in ev["water_wiring"]])
print("lights:", [(l["name"], l["energy"]) for l in ev["lights"]])
