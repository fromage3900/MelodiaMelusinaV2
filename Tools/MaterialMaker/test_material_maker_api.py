#!/usr/bin/env python3
"""Test Material Maker API access and .ptex graph handling"""

import sys
import os
import json
from pathlib import Path

# Add potential Material Maker paths
MM_PATHS = [
    r"C:\Program Files\MaterialMaker\python",
    r"C:\Program Files (x86)\MaterialMaker\python",
    r"C:\MaterialMaker\python",
    r"G:\EnvironmentPortfolio\BS_GodFile\Tools\MaterialMaker",
    os.path.expanduser("~/MaterialMaker/python"),
    os.path.expanduser("~/AppData/Local/Programs/MaterialMaker/python")
]

print("Testing Material Maker API Access...")
print("=" * 50)

# Try to locate Material Maker
mm_found = False
for path in MM_PATHS:
    if os.path.exists(path):
        print(f"[OK] Found potential Material Maker path: {path}")
        if "python" in path:
            sys.path.append(path)
        mm_found = True
        break

if not mm_found:
    print("[X] Material Maker installation not found")
    print("\nSearching for .ptex graph files...")

# Check for existing .ptex files
project_tools = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\MaterialMaker")
if project_tools.exists():
    ptex_files = list(project_tools.glob("*.ptex"))
    if ptex_files:
        print(f"[OK] Found {len(ptex_files)} .ptex graph files:")
        for ptex in ptex_files:
            print(f"  - {ptex.name}")
        
        # Try to read one of the graph files
        if ptex_files:
            sample_graph = ptex_files[0]
            print(f"\n[OK] Examining graph structure: {sample_graph.name}")
            try:
                with open(sample_graph, 'r') as f:
                    graph_data = json.load(f)
                
                print(f"  Nodes: {len(graph_data.get('nodes', []))}")
                print(f"  Connections: {len(graph_data.get('connections', []))}")
                
                if 'remote' in graph_data:
                    print(f"  Remote parameters: {len(graph_data['remote'].get('widgets', []))}")
                    
                    # Show some parameters
                    widgets = graph_data['remote'].get('widgets', [])
                    if widgets:
                        print("  Sample parameters:")
                        for widget in widgets[:5]:
                            name = widget.get('name', 'unknown')
                            default = widget.get('default', 'N/A')
                            print(f"    - {name}: {default}")
                
                print("[OK] Graph structure analysis successful")
                
            except Exception as e:
                print(f"[X] Failed to read graph: {e}")
    else:
        print("[X] No .ptex files found in MaterialMaker tools directory")
else:
    print("[X] MaterialMaker tools directory not found")

# Try to import Material Maker API
print("\nAttempting Material Maker API import...")
try:
    import material_maker as mm
    print("[OK] Material Maker API imported successfully")
    
    if hasattr(mm, '__version__'):
        print(f"[OK] Material Maker version: {mm.__version__}")
    
    # Test basic operations
    try:
        graph = mm.new_graph()
        print("[OK] Created new graph successfully")
        
        # Test with existing graph
        if ptex_files:
            loaded_graph = mm.load_graph(str(ptex_files[0]))
            print(f"[OK] Loaded existing graph: {ptex_files[0].name}")
            
            # Test parameter operations
            if 'remote' in graph_data:
                widgets = graph_data['remote'].get('widgets', [])
                if widgets:
                    test_param = widgets[0].get('name')
                    test_value = widgets[0].get('default', 0.5)
                    loaded_graph.set_parameter(test_param, test_value)
                    print(f"[OK] Parameter operations working")
        
        print("\n[OK] All API tests passed!")
        print("Material Maker API is fully functional")
        
    except Exception as e:
        print(f"[X] API test failed: {e}")
        print("API may have limited functionality")

except ImportError as e:
    print(f"[X] Failed to import Material Maker API: {e}")
    print("\nTo enable Material Maker API:")
    print("1. Download Material Maker from https://rodzill4.github.io/material-maker/")
    print("2. Install to C:\\Program Files\\MaterialMaker\\")
    print("3. Restart this script")
    print("\nAlternative: Use .ptex graph files directly without API")
    print("The Melodia pipeline can work with .ptex files using JSON manipulation")

print("\n" + "=" * 50)
print("Test complete")