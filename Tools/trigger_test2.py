import json, urllib.request, time
MCP='http://127.0.0.1:9316/mcp'
def call(tool,args,timeout=20):
    b=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode()
    req=urllib.request.Request(MCP,data=b,headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=timeout).read())

code = r'''
import json, unreal
# Try to find subsystem via object iterator
try:
    # Try to find all MelodiaNarrativeSubsystem objects
    import unreal as u
    # Use object library
    # Try via GEngine
    try:
        engine = u.find_object(None, "/Engine/Transient.Engine_1")
        print("ENGINE:"+str(engine))
    except Exception as e:
        print("ENGINE_ERR:"+str(e)[:300])
    
    # Try via GameInstance static
    try:
        # Try to get all worlds
        worlds = u.find_objects(None, "/Script/Engine.World")
        print("WORLDS:"+str(len(worlds)) + str([str(w) for w in worlds[:5]]))
        for w in worlds:
            try:
                gi = w.get_game_instance()
                print("WORLD_GI:"+str(w)+"->"+str(gi))
                if gi:
                    # Try to get subsystem
                    try:
                        subs = gi.get_subsystem(u.load_class(None, "/Script/BS_GodFile.MelodiaNarrativeSubsystem"))
                        print("SUBS_VIA_GI:"+str(subs))
                    except Exception as e:
                        print("SUBS_GI_ERR:"+str(e)[:400])
            except Exception as e:
                print("WORLD_GI_ERR:"+str(e)[:300])
    except Exception as e:
        print("WORLDS_ERR:"+str(e)[:500])
        import traceback
        print(traceback.format_exc()[:1000])

    # Also try to find subsystem directly via find
    try:
        # Find by class
        objs = u.find_objects(None, "/Script/BS_GodFile.MelodiaNarrativeSubsystem")
        print("FIND_OBJS:"+str(len(objs)) + str([str(o) for o in objs[:3]]))
    except Exception as e:
        print("FIND_OBJS_ERR:"+str(e)[:400])
        
except Exception as e:
    print("OUTER:"+str(e)[:1000])
    import traceback
    print(traceback.format_exc()[:1000])
'''
print(call('editor_query',{'action':'run_python','params':{'command':code}}))
# Also try to stop PIE after
time.sleep(2)
print(call('editor_query',{'action':'poll_pie_smoke','session_id':'pie_smoke_9_140944'}))
