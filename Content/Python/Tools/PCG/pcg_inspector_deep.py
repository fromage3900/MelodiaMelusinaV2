#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pcg_inspector_deep.py — deep single-graph PCG inspector.

Inspects one PCG graph's full node topology, mesh spawner references, and
parameter overrides. Used by pcg_inspector.py for targeted analysis.

Run inside Unreal Editor via Monolith:
  monolith run_python Content/Python/Tools/PCG/pcg_inspector_deep.py /Game/PCG/Graphs/MyGraph

Read-only. Does NOT modify PCG assets.
"""
# merk: TOOL | PCG | inspector-deep | read-only
import unreal
import json
import sys

graph_path = sys.argv[1] if len(sys.argv) > 1 else "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueNaveVaultEx.PCG_BaroqueNaveVaultEx"

result = {
    "graph_path": graph_path,
    "loaded": False,
    "error": None,
    "graph_class": None,
    "node_count": 0,
    "nodes": [],
    "spawner_nodes": [],
    "all_pcgex_nodes": [],
    "uses_pcgex": False,
    "mesh_reference_properties": {},
}

try:
    asset = unreal.EditorAssetLibrary.load_asset(graph_path)
    if asset is None:
        result["error"] = f"Asset not found: {graph_path}"
        print(json.dumps(result, indent=2, default=str))
        sys.exit(1)
    
    result["loaded"] = True
    result["graph_class"] = asset.get_class().get_name()
    
    # Try to get the graph object
    actual_graph = None
    
    # PCGGraph has nodes directly
    if hasattr(asset, 'nodes'):
        actual_graph = asset
    elif hasattr(asset, 'graph'):
        try:
            actual_graph = asset.get_editor_property('graph')
        except:
            pass
    
    if actual_graph is None:
        actual_graph = asset
    
    # Get nodes
    nodes = []
    try:
        nodes = actual_graph.get_editor_property('nodes') or []
    except:
        try:
            nodes = actual_graph.nodes or []
        except:
            pass
    
    result["node_count"] = len(nodes)
    
    for i, node in enumerate(nodes):
        class_name = node.get_class().get_name()
        
        if "PCGEx" in class_name:
            result["uses_pcgex"] = True
            result["all_pcgex_nodes"].append({"index": i, "class": class_name})
        
        node_info = {
            "index": i,
            "class": class_name,
            "properties": {},
            "mesh_refs": {},
            "is_spawner": False,
            "spawner_type": None,
        }
        
        # Check if this is a spawner node
        spawner_classes = [
            "PCGStaticMeshSpawnerSettings",
            "PCGStaticMeshSpawnerNode", 
            "PCGStaticMeshSpawner",
            "PCGSpawnActorNode",
            "PCGExStaticMeshSpawner",
            "PCGExStaticMeshSpawnerSettings",
            "PCGExSpawnActor",
            "PCGExSpawnStaticMesh",
        ]
        
        for sc in spawner_classes:
            if sc in class_name:
                node_info["is_spawner"] = True
                node_info["spawner_type"] = class_name
                break
        
        # Also check by keywords
        if "spawner" in class_name.lower() or "spawn" in class_name.lower():
            node_info["is_spawner"] = True
            if node_info["spawner_type"] is None:
                node_info["spawner_type"] = class_name
        
        # Get all properties
        try:
            node_class = node.get_class()
            for prop in unreal.StructBaseProperties(node_class):
                prop_name = prop.get_name()
                try:
                    prop_value = node.get_editor_property(prop_name)
                    prop_type = prop.get_class().get_name()
                    
                    # Store all properties
                    val_str = str(prop_value) if prop_value is not None else None
                    node_info["properties"][prop_name] = {
                        "type": prop_type,
                        "value": val_str,
                        "is_set": prop_value is not None and val_str not in ("None", "", "()", "False"),
                    }
                    
                    # Check for mesh references
                    mesh_kw = ["mesh", "static_mesh", "asset", "template", "component_class", 
                              "soft_object_path", "soft_class_path", "mesh_selector", 
                              "mesh_entry", "reference", "hard_object", "object_path"]
                    if any(kw in prop_name.lower() for kw in mesh_kw):
                        node_info["mesh_refs"][prop_name] = {
                            "type": prop_type,
                            "value": val_str,
                            "is_set": prop_value is not None and val_str not in ("None", "", "()", "False"),
                        }
                        
                except Exception as e:
                    node_info["properties"][prop_name] = {"error": str(e)}
        except Exception as e:
            node_info["properties"] = {"error": str(e)}
        
        result["nodes"].append(node_info)
        
        if node_info["is_spawner"]:
            spawner_detail = {
                "index": i,
                "class": class_name,
                "is_pcgex": "PCGEx" in class_name,
                "mesh_refs": node_info["mesh_refs"],
                "all_props": node_info["properties"],
            }
            
            # Try to get settings sub-object
            settings_props = ["settings", "component", "spawner_settings", "mesh_spawner_settings",
                            "static_mesh_spawner_settings", "user_settings"]
            for sp in settings_props:
                try:
                    settings = node.get_editor_property(sp)
                    if settings is not None:
                        spawner_detail["settings_property"] = sp
                        spawner_detail["settings_class"] = settings.get_class().get_name()
                        
                        # Inspect settings
                        settings_info = {}
                        for sprop in unreal.StructBaseProperties(settings.get_class()):
                            sname = sprop.get_name()
                            try:
                                sval = settings.get_editor_property(sname)
                                stype = sprop.get_class().get_name()
                                sval_str = str(sval) if sval is not None else None
                                settings_info[sname] = {
                                    "type": stype,
                                    "value": sval_str,
                                    "is_set": sval is not None and sval_str not in ("None", "", "()", "False"),
                                }
                                
                                if any(kw in sname.lower() for kw in mesh_kw):
                                    node_info["mesh_refs"][f"{sp}.{sname}"] = {
                                        "type": stype,
                                        "value": sval_str,
                                        "is_set": sval is not None and sval_str not in ("None", "", "()", "False"),
                                        "path": f"node.{sp}.{sname}",
                                    }
                            except:
                                pass
                        spawner_detail["settings_properties"] = settings_info
                        break
                except:
                    continue
            
            result["spawner_nodes"].append(spawner_detail)
    
    # Summary
    result["summary"] = {
        "total_nodes": len(nodes),
        "spawner_count": len(result["spawner_nodes"]),
        "pcgex_spawner_count": sum(1 for s in result["spawner_nodes"] if s["is_pcgex"]),
        "standard_spawner_count": sum(1 for s in result["spawner_nodes"] if not s["is_pcgex"]),
        "total_mesh_refs": len(result["mesh_reference_properties"]),
    }

except Exception as e:
    result["error"] = str(e)
    import traceback
    result["traceback"] = traceback.format_exc()

print(json.dumps(result, indent=2, default=str))