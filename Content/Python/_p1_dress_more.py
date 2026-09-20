"""Fill more WC_PortfolioDress_ along approach with looser ground rules."""
import unreal, json, math, random
from pathlib import Path

DRESS_MESHES = [
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_01/S_Rock_01",
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_02/S_Rock_02",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Small",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Medium",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_01",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_02",
]

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def ground_at(world, x, y, z_hint=2000.0):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x,y,z_hint+4000), unreal.Vector(x,y,z_hint-5000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    return {'loc': t[4], 'normal': t[5], 'actor': t[9].get_actor_label() if t[9] else None}

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
# keep existing dress; add more
existing = [a for a in svc.get_all_level_actors() if label(a).startswith('WC_PortfolioDress_')]
start_idx = len(existing)

landing = next((a for a in svc.get_all_level_actors() if label(a)=='WC_EscherWalk_platform_landing_00'), None)
field = next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)
meadow = next((a for a in svc.get_all_level_actors() if label(a)=='WC_EscherWalk_spur_westbank_00'), None)
a0 = landing.get_actor_location()
a1 = field.get_actor_location()
if meadow:
    a1 = unreal.Vector((a1.x+meadow.get_actor_location().x)*0.5, (a1.y+meadow.get_actor_location().y)*0.5, a1.z)

meshes = [(p, unreal.EditorAssetLibrary.load_asset(p)) for p in DRESS_MESHES]
meshes = [(p,m) for p,m in meshes if m]
rng = random.Random(20260921)
spawned = []
attempts = 0
# denser: 24 tries along path
for i in range(24):
    attempts += 1
    t = (i + 0.5) / 24.0
    x = a0.x + (a1.x - a0.x) * t
    y = a0.y + (a1.y - a0.y) * t
    dx, dy = a1.x - a0.x, a1.y - a0.y
    length = math.sqrt(dx*dx + dy*dy) or 1.0
    px, py = -dy/length, dx/length
    off = rng.uniform(80.0, 650.0) * rng.choice([-1.0, 1.0])
    x += px * off; y += py * off
    g = ground_at(world, x, y, z_hint=max(a0.z, a1.z, 800))
    if not g:
        continue
    lab = g['actor'] or ''
    # allow Brushify island OR any Brushify mesh OR EscherWalk
    ok = lab.startswith('Brushify') or lab.startswith('WC_EscherWalk_') or 'Island' in lab
    if not ok:
        continue
    if float(g['normal'].z) < 0.45:
        continue
    path, mesh = meshes[i % len(meshes)]
    loc = unreal.Vector(g['loc'].x, g['loc'].y, g['loc'].z)
    yaw = rng.uniform(0, 360)
    scale = rng.uniform(0.7, 1.5)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, yaw, 0))
    if not actor:
        continue
    name = 'WC_PortfolioDress_%02d_%s' % (start_idx + len(spawned), Path(path).name)
    actor.set_actor_label(name)
    try:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        actor.set_folder_path('PortfolioDress/Approach')
        actor.tags = ['Portfolio','SetDress','ApproachFill']
    except Exception:
        pass
    spawned.append({'label': name, 'mesh': path, 'ground': lab, 'loc':[loc.x,loc.y,loc.z]})

total = len([a for a in svc.get_all_level_actors() if label(a).startswith('WC_PortfolioDress_')])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('DRESS2', json.dumps({'added': len(spawned), 'total': total, 'attempts': attempts, 'sample': spawned[:8]}, default=str))
