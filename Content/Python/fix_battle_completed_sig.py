"""Fix HandleBattleCompleted function signature inside the editor via Python API.

Created by the agent to set the Result param to the native EMelodiaBattleResult
enum. The MCP type resolver falls back to bool for unknown type strings, so we
edit the K2Node_FunctionEntry pin type directly through the Blueprint editor.
"""
from __future__ import annotations

import unreal

ASSET = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
FUNCTION = "HandleBattleCompleted"


def find_graph(bp: unreal.Blueprint, graph_name: str):
    for graph in bp.get_editor_graphs():
        if graph.get_name() == graph_name:
            return graph
    return None


def main():
    bp = unreal.load_asset(ASSET)
    if bp is None:
        print("ERROR: blueprint not loaded")
        return
    graph = find_graph(bp, FUNCTION)
    if graph is None:
        print("ERROR: function graph not found:", FUNCTION)
        return
    print("Found graph:", graph.get_name(), "nodes:", graph.get_nodes())
    entry = None
    for node in graph.get_nodes():
        if node.get_class().get_name().startswith("K2Node_FunctionEntry"):
            entry = node
            break
    if entry is None:
        print("ERROR: FunctionEntry not found")
        return
    print("Entry found:", entry.get_name())
    pins = entry.get_pins()
    for pin in pins:
        print("  pin:", pin.get_name(), "| type:", pin.get_pin_type())
        if pin.get_name() == "Result":
            pin_type = unreal.PinCategory.byt
            print("    -> would set to byte/enum:", unreal.PinCategory.byt)
    print("DONE: inspect output")


if __name__ == "__main__":
    main()
