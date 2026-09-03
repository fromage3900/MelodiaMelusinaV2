import json, urllib.request, time
MCP='http://127.0.0.1:9316/mcp'
def call(tool,args,timeout=20):
    b=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode()
    req=urllib.request.Request(MCP,data=b,headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=timeout).read())

# Start PIE on Kaleido
print("START PIE")
pie = call('editor_query',{'action':'run_pie_smoke','map':'/Game/EnvSandbox/Environments/L_KaleidoNave','duration':12})
print(pie)

# Wait 3 sec for PIE to load
time.sleep(5)
print("TRIGGER BATTLE VIA QUILL")

code = r'''
import json, unreal
# Try to get narrative subsystem via GameInstance
try:
    # Find GameInstance - need to get world
    # Try via EditorLevelLibrary.get_editor_world() but in PIE it's PIE world
    # Try via unreal.GameplayStatics
    world = None
    # Try to get PIE world via editor
    # Use GetGameInstance
    import unreal as u
    # Try to find the subsystem via any means
    # Use u.GameInstance
    # Alternative: get via Engine
    # Try to find UWorld
    # Use u.get_editor_world() deprecated but try PIE
    try:
        world = u.EditorLevelLibrary.get_editor_world()
        print("WORLD:"+str(world))
    except Exception as e:
        print("WORLD_ERR:"+str(e)[:300])
    
    # Try to get GameInstance from world
    gi = None
    if world:
        try:
            gi = world.get_game_instance()
            print("GI:"+str(gi))
        except Exception as e:
            print("GI_ERR:"+str(e)[:300])
    
    # Try direct subsystem access
    if gi:
        try:
            subs = gi.get_subsystem(unreal.load_class(None, "/Script/BS_GodFile.MelodiaNarrativeSubsystem"))
            print("SUBS_LOAD_CLASS:"+str(subs))
        except Exception as e:
            print("SUBS_ERR:"+str(e)[:500])
        
        # Try via GetMelodiaNarrativeSubsystem static
        try:
            # Import the subsystem class via Python
            import importlib
            # Try to find via FindObject
            subs2 = u.find_object(None, "/Script/BS_GodFile.MelodiaNarrativeSubsystem")
            print("FIND_SUBS:"+str(subs2))
        except Exception as e:
            print("FIND_ERR:"+str(e)[:300])
            
except Exception as e:
    print("OUTER:"+str(e)[:1000])
    import traceback
    print(traceback.format_exc()[:1000])
'''
print(call('editor_query',{'action':'run_python','params':{'command':code}}))
