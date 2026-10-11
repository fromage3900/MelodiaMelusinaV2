# Infinite Score dressing (editor only, idempotent): linear AAA keys, Chladni stepping garden (GrokPrep Houdini field),
# floating melody notes, oculus chimes, rail pendants. Meshes: /Game/Melodia/Meshes/ScoreKit_GP (GrokPrep kits).
import csv, math, sys, unreal

K = "/Game/Melodia/Meshes/ScoreKit_GP/"
PADS = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/GrokPrep/houdini_chladni_field/experimental/out/stepping_pads.csv"
TAG = unreal.Name("InfiniteScore.Dress")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not ues.get_editor_world() or ues.get_game_world():
    print("BUSY"); raise SystemExit
if ues.get_editor_world().get_name() != "L_InfiniteScore":   # never run (and never delete anything) in another level
    print("WRONG_LEVEL", ues.get_editor_world().get_name()); raise SystemExit

for a in list(sub.get_all_level_actors()):          # idempotent: drop the previous dressing and the old key run
    n = a.get_class().get_name()
    if TAG in a.tags or n in ("PCGPianoKeyboard", "PCGPianoWhiteKey", "PCGPianoBlackKey") or a.get_actor_label().startswith("Piano Walkway"):
        sub.destroy_actor(a)

sys.path.insert(0, "C:/EnvironmentPortfolio/BS_GodFile/Content/Python")
import importlib, pcg_piano_walkway as w
importlib.reload(w)
w.build_walkway(spline_actor_label="NavProxy_ScoreWalk_Curved", biome="FarawayFabric", name="InfiniteScore_PianoRoll", pattern=None)

spl = [a for a in sub.get_all_level_actors() if a.get_actor_label() == "NavProxy_ScoreWalk_Curved"][0].get_component_by_class(unreal.SplineComponent)
length = spl.get_spline_length()


def at(s, lat=0.0, dz=0.0):
    p = spl.get_location_at_distance_along_spline(s, unreal.SplineCoordinateSpace.WORLD)
    t = spl.get_direction_at_distance_along_spline(s, unreal.SplineCoordinateSpace.WORLD)
    n = math.hypot(t.x, t.y) or 1.0
    return unreal.Vector(p.x - t.y / n * lat, p.y + t.x / n * lat, p.z + dz), math.degrees(math.atan2(t.y, t.x))


def ism_actor(label):
    return label


def add_ism(group, mesh_name, xforms):
    """One StaticMeshActor per instance (no component API for ISM in this build), grouped under an outliner folder."""
    mesh = unreal.load_asset(K + mesh_name)
    for i, t in enumerate(xforms):
        a = sub.spawn_actor_from_object(mesh, t.translation, t.rotation.rotator())
        a.set_actor_scale3d(t.scale3d)
        a.set_actor_label(f"{group}_{mesh_name[6:]}_{i:03d}")
        a.set_folder_path("InfiniteScoreDress/" + group)
        a.tags = [TAG]


def T(loc, yaw=0.0, scale=1.0, pitch=0.0):
    return unreal.Transform(location=loc, rotation=unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw), scale=unreal.Vector(scale, scale, scale))


# 1. Chladni stepping garden (human-scale pads on a chord plate's nodal paths), beside the walkway start
cen, _ = at(0.12 * length, lat=0.0, dz=-80.0)
garden = [T(unreal.Vector(cen.x + float(r["x"]), cen.y + 2600.0 + float(r["y"]), cen.z), float(r["yaw"]) - 90.0, 0.85)
          for r in csv.DictReader(open(PADS, encoding="utf-8"))]
g = ism_actor("IS_ChladniSteppingGarden")
add_ism(g, "SM_GP_PetalPad", garden)

# 2. floating melody: lydian arpeggio contour, head + stem (+ beam every fourth pair), riding above the staff
steps = [0, 2, 4, 7, 9, 11, 14, 11, 9, 7, 4, 2, 0, 4, 7, 11, 14, 16, 14, 11]
heads, stems, beams = [], [], []
for i, st in enumerate(steps):
    s = (0.08 + 0.84 * i / (len(steps) - 1)) * length
    lat = 1500.0 * (1 if i % 2 else -1)
    p, yaw = at(s, lat, 650.0 + st * 70.0)
    heads.append(T(p, yaw, 3.2))
    stems.append(T(unreal.Vector(p.x, p.y, p.z + 30.0), yaw, 3.2))
    if i % 4 == 0 and i + 1 < len(steps):
        q, _ = at((0.08 + 0.84 * (i + 1) / (len(steps) - 1)) * length, 1500.0 * (-1 if i % 2 else 1), 650.0 + steps[i + 1] * 70.0)
        beams.append(T(unreal.Vector((p.x + q.x) / 2, (p.y + q.y) / 2, p.z + 3.2 * 183 * 0.9), yaw, 3.2))
m = ism_actor("IS_FloatingMelody")
add_ism(m, "SM_GP_NoteHead", heads); add_ism(m, "SM_GP_NoteStem", stems); add_ism(m, "SM_GP_NoteBeam", beams)

# 3. chime curtain hanging from the lower arc of the crescendo oculus (frame lies in the YZ plane at x=12800)
oc = [a for a in sub.get_all_level_actors() if a.get_actor_label() == "CrescendoOculus"][0].get_actor_location()
chimes = {"SM_GP_ChimeTube_120": [], "SM_GP_ChimeTube_150": [], "SM_GP_ChimeTube_180": []}
names = list(chimes)
for k in range(28):
    th = math.radians(200 + 140 * k / 27)
    y, z = oc.y + 2500.0 * math.cos(th), oc.z + 2500.0 * math.sin(th)
    chimes[names[k % 3]].append(T(unreal.Vector(oc.x, y, z), 0.0, 2.6))
c = ism_actor("IS_OculusChimes")
for n, xs in chimes.items():
    add_ism(c, n, xs)

# 4. pendants (orb + lantern) hanging along both rails
pend_o, pend_l = [], []
for k in range(14):
    s = (0.06 + 0.88 * k / 13) * length
    for side in (1, -1):
        p, yaw = at(s, side * 420.0, 520.0)
        (pend_o if (k + (side > 0)) % 2 else pend_l).append(T(p, yaw, 3.0))
d = ism_actor("IS_RailPendants")
add_ism(d, "SM_GP_OrbPendant", pend_o); add_ism(d, "SM_GP_Lantern", pend_l)

for a in sub.get_all_level_actors():
    if TAG in a.tags or "Walkway" in a.get_actor_label() or "Piano" in a.get_class().get_name():
        a.modify()
print("DRESS_OK garden", len(garden), "notes", len(heads), "beams", len(beams), "chimes", sum(len(v) for v in chimes.values()), "pendants", len(pend_o) + len(pend_l))
print("saved", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
