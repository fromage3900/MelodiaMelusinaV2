"""
Deep analysis of battle damage path, AnimBP transitions, and widget lifecycle.
Read-only - no damage values or CDO properties are changed.
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

# == 1. Export skill EventGraphs (damage execution path) ==
print("=" * 60)
print("1. SKILL EVENTGRAPHS (DAMAGE EXECUTION PATH)")
print("=" * 60)

skills = {
    "BP_MelusinaFocusAttack": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaFocusAttack",
    "BP_MelusinaDoubleHit": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaDoubleHit",
    "BP_MelusinaTrueStrike": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaTrueStrike",
    "BP_MelusinaPetalCadence": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence",
}

for name, path in skills.items():
    print(f"\n-- {name} EventGraph --")
    g = call("blueprint_query", {"action": "export_graph", "asset_path": path, "graph_name": "EventGraph"})
    save(f"1_skill_{name}_EventGraph", g)

# == 2. BP_BattleController EventGraph (turn resolution) ==
print("\n-- BP_BattleController EventGraph --")
g = call("blueprint_query", {"action": "export_graph", "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController", "graph_name": "EventGraph"})
save("1_BP_BattleController_EventGraph", g)

# == 3. BP_UnitBase EventGraph (damage application) ==
print("\n-- BP_UnitBase EventGraph --")
g = call("blueprint_query", {"action": "export_graph", "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase", "graph_name": "EventGraph"})
save("1_BP_UnitBase_EventGraph", g)

# == 4. BP_MelusinaSwordsman_Presentation EventGraph ==
print("\n-- BP_MelusinaSwordsman_Presentation EventGraph --")
g = call("blueprint_query", {"action": "export_graph", "asset_path": "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation", "graph_name": "EventGraph"})
save("1_BP_MelusinaSwordsman_Presentation_EventGraph", g)

# == 5. ABP state machine transitions ==
print("\n" + "=" * 60)
print("2. ABP STATE MACHINE TRANSITIONS")
print("=" * 60)

for abp_name, abp_path in [
    ("ABP_Melusina_Current", "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"),
    ("ABP_Melusina_JRPGPresentation", "/Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation"),
]:
    print(f"\n-- {abp_name} --")
    sm = call("animation_query", {"action": "get_state_machines", "asset_path": abp_path})
    save(f"2_{abp_name}_state_machines_v2", sm)
    if sm.get("success") and sm.get("state_machines"):
        for machine in sm["state_machines"]:
            mname = machine if isinstance(machine, str) else machine.get("name", machine.get("machine_name", ""))
            if mname:
                print(f"  Machine: {mname}")
                tr = call("animation_query", {"action": "get_transitions", "asset_path": abp_path, "state_machine_name": mname})
                save(f"2_{abp_name}_sm_{mname}_transitions_v2", tr)
                si = call("animation_query", {"action": "get_state_info", "asset_path": abp_path, "state_machine_name": mname})
                save(f"2_{abp_name}_sm_{mname}_states_v2", si)

# == 6. Sequence info for T-pose frame ranges ==
print("\n" + "=" * 60)
print("3. SEQUENCE INFO (T-POSE FRAME RANGES)")
print("=" * 60)

seqs = {
    "A_Melusina_JumpStart_Mocap_RootX": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX",
    "A_Melusina_JumpLoop_Mocap_RootX": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpLoop_Mocap_RootX",
    "A_Mocap_Jump": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Jump",
    "A_Land": "/Game/Melodia/Characters/Melusina/Animations/A_Land",
    "AM_Mocap_BasicAttack": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack",
}
for name, path in seqs.items():
    print(f"  {name}")
    si = call("animation_query", {"action": "get_sequence_info", "asset_path": path})
    save(f"2_seq_{name}_info_v2", si)

# == 7. Widget construct/destruct graphs ==
print("\n" + "=" * 60)
print("4. WIDGET CONSTRUCT/DESTRUCT GRAPHS")
print("=" * 60)

widgets = {
    "WBP_Battle_Results": "/Game/Melodia/UI/WBP_Battle_Results",
    "WBP_Battle_Rhythm": "/Game/Melodia/UI/WBP_Battle_Rhythm",
    "WBP_Battle_Mobile": "/Game/Melodia/UI/WBP_Battle_Mobile",
}
for name, path in widgets.items():
    print(f"\n-- {name} --")
    graphs = call("blueprint_query", {"action": "list_graphs", "asset_path": path})
    save(f"3_{name}_graphs_v2", graphs)
    if graphs.get("success") and graphs.get("graphs"):
        for g in graphs["graphs"]:
            gname = g if isinstance(g, str) else g.get("name", g.get("graph_name", "unknown"))
            print(f"  Graph: {gname}")
            gdata = call("blueprint_query", {"action": "export_graph", "asset_path": path, "graph_name": gname})
            save(f"3_{name}_graph_{gname}_v2", gdata)

# == 8. Post-LoadThisGame runtime export ==
print("\n" + "=" * 60)
print("5. POST-LOADTHISGAME RUNTIME EXPORT")
print("=" * 60)

# Search for LoadThisGame references
for q in ["LoadThisGame", "LoadGame", "SaveGame", "LoadSlot"]:
    res = call("project_query", {"action": "search", "query": q})
    if res.get("success") and res.get("results"):
        for r in res["results"][:5]:
            print(f"  Found: {r['asset_path']} ({r['asset_class']})")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print(f"Output: {os.path.abspath(OUT_DIR)}")
print("=" * 60)