import json, urllib.request
MCP='http://127.0.0.1:9316/mcp'
def call(tool,args):
    b=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode()
    req=urllib.request.Request(MCP,data=b,headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=20).read())

# Find a working battle with enemyList>0 to copy
code = r'''
import json, unreal
# Find all BP_InteractionBattle actors in all levels? Search in current level for any with enemyList>0
actors = unreal.EditorLevelLibrary.get_all_level_actors()
candidates = []
for a in actors:
    try:
        if "Battle" in str(a.get_class().get_name()):
            try:
                el = a.get_editor_property("enemyList")
                if el and len(el) > 0:
                    # Try to inspect first entry
                    first = el[0]
                    candidates.append(str(a.get_fname()) + "|" + str(a.get_class().get_name()) + "|len=" + str(len(el)) + "|first=" + str(first)[:500])
            except Exception as e:
                candidates.append(str(a.get_fname()) + "|err " + str(e)[:200])
    except: pass
print("__CANDIDATES__"+json.dumps(candidates[:10]))

# Also check the placed interaction specifically and try to set it
tgt = None
for a in actors:
    if str(a.get_fname()) == "BP_InteractionBattle_C_0":
        tgt = a
        break
if tgt:
    # Try to get current enemyList details
    try:
        el = tgt.get_editor_property("enemyList")
        print("__CURRENT__len=" + str(len(el) if el else 0))
        if el and len(el)>0:
            import unreal as u
            # Try to dump struct fields
            try:
                s = el[0]
                print("__STRUCT_TYPE__"+str(type(s)))
                # Try to get struct properties via reflection if it's a struct
                # Use dir
                print("__DIR__"+json.dumps([x for x in dir(s) if not x.startswith("_")][:30]))
            except Exception as e:
                print("__STRUCT_ERR__"+str(e)[:500])
    except Exception as e:
        print("__CURRENT_ERR__"+str(e)[:500])

# Check what enum or struct S_EnemyUnitSpawnDataList looks like via asset
try:
    # Try to load a known enemy
    e1 = unreal.load_asset("/Game/Melodia/Enemies/BP_Enemy_CrystalShard.BP_Enemy_CrystalShard")
    print("__ENEMY_CRYS__"+str(e1))
    e2 = unreal.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Units/EnemyUnits/BP_EnemyUnitBase.BP_EnemyUnitBase")
    print("__ENEMY_BASE__"+str(e2))
except Exception as e:
    print("__LOAD_ERR__"+str(e))
'''
print(call('editor_query',{'action':'run_python','params':{'command':code}}))
