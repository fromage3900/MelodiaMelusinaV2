#!/usr/bin/env python3
"""Build BP_PhysicsPlacementSpawner via the project T3D pipeline (build_blueprint_from_spec).

Drop-and-settle physics placement spawner:
  BeginPlay -> Set Simulate Physics (self = PlacementMesh, bSimulate = true)
Component: PlacementMesh (StaticMeshComponent, root, pillow1, Movable).
"""
import json, sys, os, urllib.request

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
BP = "/Game/EnvSandbox/Blueprints/BP_PhysicsPlacementSpawner"

def monolith(tool, args, timeout=60):
    body = {"jsonrpc":"2.0","id":1,"method":"tools/call",
            "params":{"name":tool,"arguments":args}}
    req = urllib.request.Request(MONOLITH_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode())
        res = data.get("result", {})
        if res.get("isError"):
            return "ERROR:" + str(res.get("content"))[:500]
        return res.get("content",[{}])[0].get("text","")
    except Exception as e:
        return "ERROR:" + str(e)

def main():
    # 1. create the BP asset
    r = monolith("blueprint_query", {"action":"create_blueprint","save_path":BP,"parent_class":"Actor"})
    print("create:", r[:300])

    # 2. add PlacementMesh StaticMeshComponent (root)
    r = monolith("blueprint_query", {"action":"add_component","asset_path":BP,"component_name":"PlacementMesh","component_class":"StaticMeshComponent"})
    print("add_component:", r[:200])

    # 3. set mesh + mobility
    r = monolith("blueprint_query", {"action":"set_component_property","asset_path":BP,"component_name":"PlacementMesh","property_name":"StaticMesh","value":"/Game/pillow1"})
    print("set_mesh:", r[:200])
    r = monolith("blueprint_query", {"action":"set_component_property","asset_path":BP,"component_name":"PlacementMesh","property_name":"Mobility","value":"Movable"})
    print("set_mobility:", r[:200])

    # 4. build EventGraph in ONE transaction via build_blueprint_from_spec
    nodes = [
        {
            "id":"node_setsim","type":"CallFunction","function_name":"SetSimulatePhysics",
            "function_class":"/Script/Engine.PrimitiveComponent","position":[320,0]
        },
        {
            "id":"ref_mesh","type":"VariableGet","variable_name":"PlacementMesh","position":[320,-260]
        },
    ]
    connections = [
        {"source":"K2Node_Event_0","source_pin":"then","target":"node_setsim","target_pin":"execute"},
        {"source":"ref_mesh","source_pin":"PlacementMesh","target":"node_setsim","target_pin":"self"},
    ]
    pin_defaults = [
        {"node_id":"node_setsim","pin_name":"bSimulate","value":True},
    ]
    spec = {
        "asset_path": BP,
        "graph_name": "EventGraph",
        "nodes": nodes,
        "connections": connections,
        "pin_defaults": pin_defaults,
        "auto_compile": True,
    }
    r = monolith("blueprint_query", {"action":"build_blueprint_from_spec", **spec})
    print("build_spec:", r[:600])

    # 5. save
    r = monolith("blueprint_query", {"action":"save_asset","asset_path":BP})
    print("save:", r[:200])

if __name__ == "__main__":
    main()
