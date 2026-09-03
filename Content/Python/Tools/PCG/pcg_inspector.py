#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pcg_inspector.py — PCG graph introspection and structure analysis tool.

Scans PCG graph assets in the project and reports node topology, spawner
references, and common failure modes (0-instance generation).

Run inside Unreal Editor via Monolith:
  monolith run_python Content/Python/Tools/PCG/pcg_inspector.py

This is a read-only inspector. It does NOT modify PCG assets.
"""
# merk: TOOL | PCG | inspector | read-only

import json
import sys
import os

# UE Python imports
import unreal

def get_pcg_graph_asset_path(graph_name):
    """Get the full asset path for a PCG graph."""
    return f"/Game/PCG/Graphs/{graph_name}"

def load_pcg_graph(graph_name):
    """Load a PCG graph asset by name."""
    asset_path = get_pcg_graph_asset_path(graph_name)
    try:
        asset = unreal.load_asset(asset_path)
        if asset is None:
            # Try alternative paths
            alt_paths = [
                f"/Game/PCG/{graph_name}",
                f"/Game/ProceduralContent/{graph_name}",
                f"/Game/ProceduralContent/Graphs/{graph_name}",
                f"/Game/PCG_Graphs/{graph_name}",
                f"/Game/PCG/PCG_{graph_name}",
            ]
            for alt_path in alt_paths:
                asset = unreal.load_asset(alt_path)
                if asset is not None:
                    return asset, alt_path
        return asset, asset_path
    except Exception as e:
        return None, f"Error loading {asset_path}: {str(e)}"

def get_pcg_graph_from_settings(settings):
    """Extract the PCG graph from PCG graph settings/subgraph."""
    if settings is None:
        return None
    # Try to get the graph reference
    try:
        graph = settings.get_editor_property("graph")
        if graph:
            return graph
    except:
        pass
    try:
        graph = settings.get_editor_property("subgraph")
        if graph:
            return graph
    except:
        pass
    try:
        graph = settings.get_editor_property("pcg_graph")
        if graph:
            return graph
    except:
        pass
    return None

def inspect_pcg_graph(graph_name):
    """Inspect a PCG graph and return detailed node information."""
    result = {
        "graph_name": graph_name,
        "asset_path": None,
        "loaded": False,
        "error": None,
        "graph_class": None,
        "nodes": [],
        "spawner_nodes": [],
        "mesh_reference_properties": [],
        "uses_pcgex": False,
        "node_count": 0,
        "spawner_count": 0,
    }
    
    asset, path = load_pcg_graph(graph_name)
    result["asset_path"] = path
    
    if asset is None:
        result["error"] = f"Could not load asset at {path}"
        return result
    
    result["loaded"] = True
    result["graph_class"] = asset.get_class().get_name()
    
    # Check if it's a PCGGraph or PCGGraphInstance
    graph_class_name = asset.get_class().get_name()
    
    # Try to get the actual graph
    actual_graph = None
    
    if graph_class_name == "PCGGraph":
        actual_graph = asset
    elif graph_class_name == "PCGGraphInstance":
        try:
            actual_graph = asset.get_editor_property("graph")
        except:
            pass
    elif graph_class_name == "PCGGraphInterface":
        try:
            actual_graph = asset.get_editor_property("graph")
        except:
            pass
    else:
        # Try to find graph property
        try:
            actual_graph = asset.get_editor_property("graph")
        except:
            pass
        if actual_graph is None:
            try:
                actual_graph = asset.get_editor_property("subgraph")
            except:
                pass
    
    if actual_graph is None:
        # The asset itself might be the graph
        actual_graph = asset
    
    # Get nodes from the graph
    try:
        nodes = actual_graph.get_editor_property("nodes")
        if nodes is None:
            nodes = []
        result["node_count"] = len(nodes)
    except Exception as e:
        result["error"] = f"Could not get nodes: {str(e)}"
        nodes = []
    
    for i, node in enumerate(nodes):
        node_info = {
            "index": i,
            "class": node.get_class().get_name(),
            "node_type": None,
            "properties": [],
            "is_spawner": False,
            "mesh_refs": {},
        }
        
        class_name = node.get_class().get_name()
        
        # Check for PCGEx
        if "PCGEx" in class_name or "PCGEx" in str(node.get_class()):
            result["uses_pcgex"] = True
        
        # Determine node type
        if "StaticMeshSpawner" in class_name or "MeshSpawner" in class_name:
            node_info["is_spawner"] = True
            node_info["node_type"] = "StaticMeshSpawner"
            result["spawner_count"] += 1
        elif "SpawnActor" in class_name:
            node_info["is_spawner"] = True
            node_info["node_type"] = "SpawnActor"
            result["spawner_count"] += 1
        elif "SpawnStaticMesh" in class_name:
            node_info["is_spawner"] = True
            node_info["node_type"] = "SpawnStaticMesh"
            result["spawner_count"] += 1
        else:
            node_info["node_type"] = class_name
        
        # Get all properties of the node
        try:
            node_class = node.get_class()
            for prop in unreal.StructBaseProperties(node_class):
                prop_name = prop.get_name()
                try:
                    prop_value = node.get_editor_property(prop_name)
                    prop_type = prop.get_class().get_name()
                    
                    prop_info = {
                        "name": prop_name,
                        "type": prop_type,
                        "value": str(prop_value) if prop_value is not None else None,
                    }
                    node_info["properties"].append(prop_info)
                    
                    # Check for mesh-related properties
                    mesh_keywords = ["mesh", "static_mesh", "asset", "template", "component_class", "soft_object_path", "soft_class_path"]
                    if any(kw in prop_name.lower() for kw in mesh_keywords):
                        node_info["mesh_refs"][prop_name] = {
                            "type": prop_type,
                            "value": str(prop_value) if prop_value is not None else None,
                            "is_set": prop_value is not None and str(prop_value) != "None" and str(prop_value) != "" and str(prop_value) != "()",
                        }
                        
                except Exception as prop_e:
                    node_info["properties"].append({
                        "name": prop_name,
                        "type": prop_type,
                        "value": f"ERROR: {str(prop_e)}",
                    })
        except Exception as e:
            node_info["properties"] = [{"error": str(e)}]
        
        # For spawner nodes, do deeper inspection
        if node_info["is_spawner"]:
            spawner_detail = inspect_spawner_node(node, class_name)
            node_info["spawner_detail"] = spawner_detail
            result["spawner_nodes"].append(node_info)
        
        result["nodes"].append(node_info)
    
    return result

def inspect_spawner_node(node, class_name):
    """Deep inspection of a spawner node to find mesh reference properties."""
    detail = {
        "class_name": class_name,
        "is_pcgex": "PCGEx" in class_name,
        "mesh_properties": [],
        "settings_object": None,
        "settings_properties": [],
    }
    
    # Try to get settings/component
    settings = None
    settings_props = ["settings", "component", "spawner_settings", "mesh_spawner_settings", "static_mesh_spawner_settings"]
    
    for prop_name in settings_props:
        try:
            settings = node.get_editor_property(prop_name)
            if settings is not None:
                detail["settings_object"] = {
                    "class": settings.get_class().get_name(),
                    "path": prop_name,
                }
                break
        except:
            continue
    
    if settings is not None:
        # Inspect settings properties
        try:
            settings_class = settings.get_class()
            for prop in unreal.StructBaseProperties(settings_class):
                prop_name = prop.get_name()
                try:
                    prop_value = settings.get_editor_property(prop_name)
                    prop_type = prop.get_class().get_name()
                    
                    prop_info = {
                        "name": prop_name,
                        "type": prop_type,
                        "value": str(prop_value) if prop_value is not None else None,
                    }
                    detail["settings_properties"].append(prop_info)
                    
                    # Check for mesh-related properties
                    mesh_keywords = ["mesh", "static_mesh", "asset", "template", "component_class", "soft_object_path", "soft_class_path", "mesh_selector", "mesh_entry"]
                    if any(kw in prop_name.lower() for kw in mesh_keywords):
                        detail["mesh_properties"].append({
                            "name": prop_name,
                            "type": prop_type,
                            "value": str(prop_value) if prop_value is not None else None,
                            "is_set": prop_value is not None and str(prop_value) != "None" and str(prop_value) != "" and str(prop_value) != "()",
                        })
                except:
                    pass
        except:
            pass
    
    # Also check the node itself for mesh properties
    mesh_keywords = ["mesh", "static_mesh", "asset", "template", "component_class", "soft_object_path", "soft_class_path", "mesh_selector", "mesh_entry"]
    try:
        node_class = node.get_class()
        for prop in unreal.StructBaseProperties(node_class):
            prop_name = prop.get_name()
            if any(kw in prop_name.lower() for kw in mesh_keywords):
                try:
                    prop_value = node.get_editor_property(prop_name)
                    prop_type = prop.get_class().get_name()
                    detail["mesh_properties"].append({
                        "name": prop_name,
                        "type": prop_type,
                        "value": str(prop_value) if prop_value is not None else None,
                        "is_set": prop_value is not None and str(prop_value) != "None" and str(prop_value) != "" and str(prop_value) != "()",
                        "on_node": True,
                    })
                except:
                    pass
    except:
        pass
    
    return detail

def main():
    """Main investigation function."""
    graphs_to_investigate = [
        "PCG_BaroqueNaveVaultEx",
        "PCG_Baroque_Scatter",
        "PCG_WaterEdgeScatter",
        "PCG_BaroquePilasterEx",
    ]
    
    working_graph = "PCG_Hero_ResonanceCathedral"
    
    results = {
        "investigation": "PCGEx Node Structure Investigation",
        "timestamp": str(unreal.DateTime.now()),
        "silent_graphs": {},
        "working_graph": None,
        "comparison": {},
    }
    
    # Investigate silent graphs
    for graph_name in graphs_to_investigate:
        print(f"\n{'='*60}")
        print(f"Investigating: {graph_name}")
        print(f"{'='*60}")
        result = inspect_pcg_graph(graph_name)
        results["silent_graphs"][graph_name] = result
        print(f"  Loaded: {result['loaded']}")
        print(f"  Class: {result['graph_class']}")
        print(f"  Nodes: {result['node_count']}")
        print(f"  Spawners: {result['spawner_count']}")
        print(f"  Uses PCGEx: {result['uses_pcgex']}")
        if result['error']:
            print(f"  Error: {result['error']}")
        for spawner in result['spawner_nodes']:
            print(f"  Spawner: {spawner['class']}")
            for mesh_ref_key, mesh_ref_val in spawner.get('mesh_refs', {}).items():
                print(f"    Mesh ref: {mesh_ref_key} = {mesh_ref_val}")
    
    # Investigate working graph
    print(f"\n{'='*60}")
    print(f"Investigating WORKING: {working_graph}")
    print(f"{'='*60}")
    working_result = inspect_pcg_graph(working_graph)
    results["working_graph"] = working_result
    print(f"  Loaded: {working_result['loaded']}")
    print(f"  Class: {working_result['graph_class']}")
    print(f"  Nodes: {working_result['node_count']}")
    print(f"  Spawners: {working_result['spawner_count']}")
    print(f"  Uses PCGEx: {working_result['uses_pcgex']}")
    if working_result['error']:
        print(f"  Error: {working_result['error']}")
    for spawner in working_result['spawner_nodes']:
        print(f"  Spawner: {spawner['class']}")
        for mesh_ref_key, mesh_ref_val in spawner.get('mesh_refs', {}).items():
            print(f"    Mesh ref: {mesh_ref_key} = {mesh_ref_val}")
    
    # Comparison
    results["comparison"] = {
        "working_uses_pcgex": working_result.get("uses_pcgex", False),
        "silent_use_pcgex": {name: r.get("uses_pcgex", False) for name, r in results["silent_graphs"].items()},
        "working_spawner_count": working_result.get("spawner_count", 0),
        "silent_spawner_counts": {name: r.get("spawner_count", 0) for name, r in results["silent_graphs"].items()},
        "working_node_count": working_result.get("node_count", 0),
        "silent_node_counts": {name: r.get("node_count", 0) for name, r in results["silent_graphs"].items()},
    }
    
    return results

if __name__ == "__main__":
    results = main()
    print("\n\n" + "="*60)
    print("FINAL RESULTS (JSON)")
    print("="*60)
    print(json.dumps(results, indent=2, default=str))