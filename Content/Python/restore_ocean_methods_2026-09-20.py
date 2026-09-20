import unreal, json
from pathlib import Path

BP = '/Oceanology_Plugin/Design/Ocean/Blueprints/Ocean/BP_OceanologyInfiniteOcean'
EAL = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset = EAL.load_asset(BP)
cls = EAL.load_blueprint_class(BP)
notes = [f'asset={asset}', f'cls={cls}']
spawned = []

# Method A: spawn_actor_from_object
try:
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
    notes.append(f'from_object={a}')
    if a:
        a.set_actor_label('SeaAbove_InfiniteOcean_Canopy')
        spawned.append('from_object')
except Exception as e:
    notes.append(f'from_object err={e}')

# Method B: ActorFactory
if not spawned:
    try:
        factory = unreal.ActorFactoryBlueprint()
        # set blueprint
        notes.append(f'factory={factory}')
    except Exception as e:
        notes.append(f'factory err={e}')

# Method C: World.spawn_actor
if not spawned:
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        a = world.spawn_actor(cls, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        notes.append(f'world.spawn={a}')
        if a:
            a.set_actor_label('SeaAbove_InfiniteOcean_Canopy')
            spawned.append('world')
    except Exception as e:
        notes.append(f'world.spawn err={e}')

# Method D: EditorActorSubsystem.spawn_actor_from_class with deferred
if not spawned:
    try:
        a = svc.spawn_actor_from_class(cls, unreal.Vector(0,0,0), unreal.Rotator(0,0,0), False)
        notes.append(f'svc={a}')
        if a:
            a.set_actor_label('SeaAbove_InfiniteOcean_Canopy')
            spawned.append('svc')
    except Exception as e:
        notes.append(f'svc err={e}')

# List World Partition / streaming levels
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    notes.append(f'world={world.get_name()}')
    try:
        levels = world.get_levels()
        notes.append(f'levels={[str(l.get_outer().get_name()) if l else None for l in levels][:20]}')
    except Exception as e:
        notes.append(f'levels err={e}')
except Exception as e:
    notes.append(f'world err={e}')

# Search ALL actors for canopy / infinite / water volume
hits=[]
for a in svc.get_all_level_actors():
    L=(a.get_actor_label() or '')
    C=a.get_class().get_name()
    if any(k in (L+C).lower() for k in ('canopy','infinite','oceanology','watervolume','waterbody','seaabove')):
        hits.append({'label':L,'class':C})

out={'spawned':spawned,'notes':notes,'hits':hits}
Path(unreal.Paths.project_dir()).joinpath('Saved/Audit/restore_ocean_methods_2026-09-20.json').write_text(json.dumps(out,indent=2,default=str),encoding='utf-8')
if spawned:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('METHODS', json.dumps(out, default=str)[:8000])
