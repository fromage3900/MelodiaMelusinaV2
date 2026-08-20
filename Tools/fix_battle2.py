import json, urllib.request
MCP='http://127.0.0.1:9316/mcp'
def call(tool,args):
    b=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode()
    req=urllib.request.Request(MCP,data=b,headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=25).read())

code = r'''
import json, unreal
actors = unreal.EditorLevelLibrary.get_all_level_actors()
tgt = None
for a in actors:
    if str(a.get_fname()) == "BP_InteractionBattle_C_0":
        tgt = a
        break
if tgt:
    cur = tgt.get_editor_property("enemyList")
    if cur and len(cur)>0:
        s = cur[0]
        print("__TO_DICT__" + str(s.to_dict())[:2000])
        print("__EXPORT_TEXT__" + s.export_text[:2000] if hasattr(s, 'export_text') else "no export")
        try:
            # Try to see what properties it has via to_dict keys
            d = s.to_dict()
            print("__DICT_KEYS__" + json.dumps(list(d.keys())[:20]))
            print("__DICT_VAL__" + json.dumps(d, indent=2)[:2000])
        except Exception as e:
            print("__DICT_ERR__" + str(e)[:1000])
    # Also check offLevelBattleData
    try:
        off = tgt.get_editor_property("offLevelBattleData")
        print("__OFF_TO_DICT__" + str(off.to_dict())[:2000])
    except Exception as e:
        print("__OFF_ERR__" + str(e)[:500])
'''
print(call('editor_query',{'action':'run_python','params':{'command':code}}))
