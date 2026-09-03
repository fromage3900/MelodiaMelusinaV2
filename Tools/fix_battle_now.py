import json, urllib.request
MCP='http://127.0.0.1:9316/mcp'
def call(tool,args):
    b=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode()
    req=urllib.request.Request(MCP,data=b,headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=25).read())

# Direct fix: set enemyList on the placed actor in L_KaleidoNave to a valid enemy
code = r'''
import json, unreal
actors = unreal.EditorLevelLibrary.get_all_level_actors()
tgt = None
for a in actors:
    if str(a.get_fname()) == "BP_InteractionBattle_C_0":
        tgt = a
        break
if not tgt:
    print("__NOTFOUND__")
else:
    # Try to set enemyList to have one valid enemy
    try:
        # Check current
        cur = tgt.get_editor_property("enemyList")
        print("__BEFORE_len__" + str(len(cur) if cur else 0))
        # Try to create a new entry
        # The struct is S_EnemyUnitSpawnDataList - need to find its type
        # Try to set via setting the array to have one element with enemy class
        # First, try to get the struct type by inspecting the property
        # Use reflection to get the array inner struct
        # Try simple: set to empty then add via Python list with dict?
        # Look at what the struct contains by exporting the level's T3D for this actor?
        # Alternative: try to use the editor's copy of a working enemyList from another level
        
        # Let's try to load a known working battle actor from Gameplay map to copy its enemyList
        # But we are in L_KaleidoNave, so we need to load the asset for a working battle
        # Try to find if there's a template with enemyList
        # For now, try to set enemyList to a simple array with one dict containing enemy class path
        # The property is likely a struct with a field like EnemyClass or UnitClass
        # Let's try to inspect the struct definition via Unreal's struct registry
        try:
            # Try to get the struct for S_EnemyUnitSpawnData
            # Use unreal.find_object
            s = unreal.find_object(None, "/Script/TurnBasedJRPGTemplate.S_EnemyUnitSpawnData")
            print("__STRUCT_S_EnemyUnitSpawnData__" + str(s))
            if s:
                # Try to get properties
                print("__STRUCT_PROPS__" + str([p.get_name() for p in s.get_properties()][:10]))
        except Exception as e:
            print("__STRUCT_FIND_ERR__" + str(e)[:500])
        
        # Also try S_EnemyUnitSpawnDataList
        try:
            s2 = unreal.find_object(None, "/Script/TurnBasedJRPGTemplate.S_EnemyUnitSpawnDataList")
            print("__STRUCT_S_EnemyUnitSpawnDataList__" + str(s2))
            if s2:
                print("__STRUCT2_PROPS__" + str([p.get_name() for p in s2.get_properties()][:10]))
        except Exception as e:
            print("__STRUCT2_ERR__" + str(e)[:500])

        # Try to directly set enemyList via JSON-like dict if we know the field
        # Common field names: EnemyClass, Unit, EnemyUnit, SpawnData
        # Let's try to brute force by setting the array via set_editor_property with a list containing a struct with those fields
        # First, try to see what the current struct's fields are via dir
        if cur and len(cur)>0:
            print("__CUR_FIRST_DIR__" + str([x for x in dir(cur[0]) if not x.startswith("_")][:30]))
            try:
                # Try to get its dict representation
                print("__CUR_FIRST_STR__" + str(cur[0])[:1000])
            except: pass
            
    except Exception as e:
        print("__ERR__" + str(e)[:1000])
        import traceback
        print(traceback.format_exc()[:1000])
'''
print(call('editor_query',{'action':'run_python','params':{'command':code}}))
