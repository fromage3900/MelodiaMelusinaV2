"""
Export battle damage, animation, and widget data via Monolith JSON-RPC.
Read-only - no damage values or CDO properties are changed.
All Monolith actions use 'asset_path' as the universal parameter name.
"""
import json, requests, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MONO = "http://127.0.0.1:9316/mcp"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Exports", "battle_anim_ui_export")
os.makedirs(OUT_DIR, exist_ok=True)

def call(tool, args, id=1):
    payload = {"jsonrpc":"2.0","method":"tools/call","params":{"name":tool,"arguments":args},"id":id}
    try:
        r = requests.post(MONO, json=payload, timeout=120)
        data = r.json()
        if "error" in data:
            return {"_rpc_error": data["error"]}
        result = data.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            txt = content[0].get("text","") if content else ""
            return {"_monolith_error": txt}
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            raw = content[0]["text"]
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"_raw_text": raw}
        return {"_raw_result": str(result)}
    except Exception as e:
        return {"_exception": str(e)}

def save(name, data):
    path = os.path.join(OUT_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Saved {name}.json")

# == SECTION 1: BATTLE DAMAGE ==
print("=" * 60)
print("SECTION 1: BATTLE DAMAGE EXPORT")
print("=" * 60)

battle_assets = {
    "BP_MelusinaSwordsman_Presentation": "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation",
    "BP_UnitBase": "/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase",
    "BP_BattleController": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
    "BP_MelodySlimeBattle": "/Game/_PROJECT/Characters/Enemies/BP_MelodySlimeBattle",
}

for name, path in battle_assets.items():
    print(f"\n-- {name} --")
    cdo = call("blueprint_query", {"action": "get_cdo_properties", "asset_path": path})
    save(f"1_{name}_cdo", cdo)
    variables = call("blueprint_query", {"action": "get_variables", "asset_path": path})
    save(f"1_{name}_variables", variables)
    graphs = call("blueprint_query", {"action": "list_graphs", "asset_path": path})
    save(f"1_{name}_graphs", graphs)
    if graphs.get("success") and graphs.get("graphs"):
        for g in graphs["graphs"]:
            gname = g if isinstance(g, str) else g.get("name", g.get("graph_name", "unknown"))
            print(f"  Exporting graph: {gname}")
            gdata = call("blueprint_query", {"action": "export_graph", "asset_path": path, "graph_name": gname})
            save(f"1_{name}_graph_{gname}", gdata)
    parent = call("blueprint_query", {"action": "get_parent_class", "asset_path": path})
    save(f"1_{name}_parent", parent)

# Search for skill/ability BPs
print("\n-- Searching for skill/ability Blueprints --")
for q in ["BP_MelusinaFocusAttack", "BP_MelusinaDoubleHit", "BP_MelusinaTrueStrike", "BP_MelusinaPetalCadence"]:
    res = call("project_query", {"action": "search", "query": q})
    if res.get("success") and res.get("results"):
        for r in res["results"][:2]:
            print(f"  Found: {r['asset_path']} ({r['asset_class']})")
            if r.get("asset_class") == "Blueprint":
                sk_cdo = call("blueprint_query", {"action": "get_cdo_properties", "asset_path": r["asset_path"]})
                save(f"1_skill_{r['asset_name']}_cdo", sk_cdo)
                sk_graphs = call("blueprint_query", {"action": "list_graphs", "asset_path": r["asset_path"]})
                save(f"1_skill_{r['asset_name']}_graphs", sk_graphs)
                if sk_graphs.get("success") and sk_graphs.get("graphs"):
                    for g in sk_graphs["graphs"]:
                        gname = g if isinstance(g, str) else g.get("name", "unknown")
                        gdata = call("blueprint_query", {"action": "export_graph", "asset_path": r["asset_path"], "graph_name": gname})
                        save(f"1_skill_{r['asset_name']}_graph_{gname}", gdata)

# == SECTION 2: ANIMATION ==
print("\n" + "=" * 60)
print("SECTION 2: ANIMBP AND MOCAP EXPORT")
print("=" * 60)

anim_assets = {
    "ABP_Melusina_Current": "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current",
    "ABP_Melusina_JRPGPresentation": "/Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation",
}

for name, path in anim_assets.items():
    print(f"\n-- {name} --")
    info = call("animation_query", {"action": "get_abp_info", "asset_path": path})
    save(f"2_{name}_abp_info", info)
    sm = call("animation_query", {"action": "get_state_machines", "asset_path": path})
    save(f"2_{name}_state_machines", sm)
    if sm.get("success") and sm.get("state_machines"):
        for machine in sm["state_machines"]:
            mname = machine if isinstance(machine, str) else machine.get("name", machine.get("machine_name", ""))
            if mname:
                print(f"  State machine: {mname}")
                si = call("animation_query", {"action": "get_state_info", "asset_path": path, "state_machine_name": mname})
                save(f"2_{name}_sm_{mname}_states", si)
                tr = call("animation_query", {"action": "get_transitions", "asset_path": path, "state_machine_name": mname})
                save(f"2_{name}_sm_{mname}_transitions", tr)
    abp_vars = call("animation_query", {"action": "get_abp_variables", "asset_path": path})
    save(f"2_{name}_variables", abp_vars)
    graphs = call("animation_query", {"action": "get_graphs", "asset_path": path})
    save(f"2_{name}_graphs", graphs)
    ll = call("animation_query", {"action": "get_linked_layers", "asset_path": path})
    save(f"2_{name}_linked_layers", ll)

# Montage info
print("\n-- AM_Mocap_BasicAttack --")
montage_path = "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack"
mi = call("animation_query", {"action": "get_montage_info", "asset_path": montage_path})
save("2_AM_Mocap_BasicAttack_montage_info", mi)
si = call("animation_query", {"action": "get_sequence_info", "asset_path": montage_path})
save("2_AM_Mocap_BasicAttack_sequence_info", si)
ni = call("animation_query", {"action": "get_sequence_notifies", "asset_path": montage_path})
save("2_AM_Mocap_BasicAttack_notifies", ni)
curves = call("animation_query", {"action": "get_sequence_curves", "asset_path": montage_path})
save("2_AM_Mocap_BasicAttack_curves", curves)

# Jump/Land/Glide/Mercy sequences
print("\n-- Key animation sequences --")
key_anims = {
    "A_Melusina_JumpStart_Mocap_RootX": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX",
    "A_Melusina_JumpLoop_Mocap_RootX": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpLoop_Mocap_RootX",
    "A_Mocap_Jump": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Jump",
    "A_Land": "/Game/Melodia/Characters/Melusina/Animations/A_Land",
}
for aname, apath in key_anims.items():
    print(f"  {aname}")
    si = call("animation_query", {"action": "get_sequence_info", "asset_path": apath})
    save(f"2_seq_{aname}_info", si)

# == SECTION 3: WIDGETS ==
print("\n" + "=" * 60)
print("SECTION 3: AUTHORED WIDGET EXPORT")
print("=" * 60)

widget_assets = {
    "WBP_Battle_Results": "/Game/Melodia/UI/WBP_Battle_Results",
    "WBP_Battle_Rhythm": "/Game/Melodia/UI/WBP_Battle_Rhythm",
    "WBP_Battle_Mobile": "/Game/Melodia/UI/WBP_Battle_Mobile",
}

# Search for more widgets
for q in ["WBP_Grade", "WBP_Ultimate", "WBP_Token", "WBP_Stock", "WBP_CutIn", "WBP_RhythmHUD"]:
    res = call("project_query", {"action": "search", "query": q})
    if res.get("success") and res.get("results"):
        for r in res["results"][:3]:
            if r.get("asset_class") == "WidgetBlueprint":
                wname = r["asset_name"]
                wpath = r["asset_path"]
                if wname not in widget_assets:
                    widget_assets[wname] = wpath
                    print(f"  Found widget: {wpath}")

for name, path in widget_assets.items():
    print(f"\n-- {name} --")
    tree = call("ui_query", {"action": "get_widget_tree", "asset_path": path})
    save(f"3_{name}_tree", tree)
    props = call("ui_query", {"action": "list_widget_properties", "asset_path": path})
    save(f"3_{name}_properties", props)
    events = call("ui_query", {"action": "list_widget_events", "asset_path": path})
    save(f"3_{name}_events", events)
    bindings = call("ui_query", {"action": "get_widget_bindings", "asset_path": path})
    save(f"3_{name}_bindings", bindings)
    anims = call("ui_query", {"action": "list_animations", "asset_path": path})
    save(f"3_{name}_animations", anims)
    info = call("blueprint_query", {"action": "get_blueprint_info", "asset_path": path})
    save(f"3_{name}_bp_info", info)
    parent = call("blueprint_query", {"action": "get_parent_class", "asset_path": path})
    save(f"3_{name}_parent", parent)
    graphs = call("blueprint_query", {"action": "list_graphs", "asset_path": path})
    save(f"3_{name}_graphs", graphs)
    if graphs.get("success") and graphs.get("graphs"):
        for g in graphs["graphs"]:
            gname = g if isinstance(g, str) else g.get("name", g.get("graph_name", "unknown"))
            if "event" in gname.lower() or "construct" in gname.lower() or "destruct" in gname.lower():
                print(f"  Exporting graph: {gname}")
                gdata = call("blueprint_query", {"action": "export_graph", "asset_path": path, "graph_name": gname})
                save(f"3_{name}_graph_{gname}", gdata)
    cdo = call("blueprint_query", {"action": "get_cdo_properties", "asset_path": path})
    save(f"3_{name}_cdo", cdo)

print("\n" + "=" * 60)
print("EXTRACTION COMPLETE")
print(f"Output: {os.path.abspath(OUT_DIR)}")
print("=" * 60)