import json
import sys
from pathlib import Path

# Check v2 graph structure
v2_graph = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\MaterialMaker\MM_Master_SurrealAnimatedPBR_v2_Static.ptex")

with open(v2_graph, 'r') as f:
    graph = json.load(f)

print(f"Graph: {v2_graph.name}")
print(f"Has remote: {'remote' in graph}")

if 'remote' in graph:
    remote = graph['remote']
    widgets = remote.get('widgets', [])
    print(f"Number of widgets: {len(widgets)}")
    
    if widgets:
        print("\nFirst 10 widgets:")
        for widget in widgets[:10]:
            name = widget.get('name', 'unknown')
            widget_type = widget.get('type', 'unknown')
            default = widget.get('default', 'N/A')
            print(f"  {name} ({widget_type}): {default}")
else:
    print("No remote section found")