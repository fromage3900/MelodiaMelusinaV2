"""Health check for all 49 Melodia Studio GN builders — run inside Blender 5.2.

Usage:
  blender --background --factory-startup --python deploy/_health_check_gn_builders.py

Reports: total builders, pass count, fail count, per-builder status.
"""
import sys
import os
import json

addons = r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons"
if addons not in sys.path:
    sys.path.insert(0, addons)

import surreal_architecture_gen
surreal_architecture_gen.register()

from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA, STUDIO_LABELS
from surreal_arch.melodia_gn import logging as melodia_log

results = {"pass": 0, "fail": 0, "skip": 0, "builders": []}

for name, builder in sorted(GROUP_BUILDERS.items()):
    meta = GROUP_METADATA.get(name, {})
    label = meta.get("label", name)
    category = meta.get("category", "Uncategorized")

    if not builder:
        results["skip"] += 1
        results["builders"].append({"name": name, "label": label, "status": "skip", "reason": "no builder"})
        continue

    try:
        result = builder()
        if isinstance(result, (tuple, list)):
            tree = result[0]
        else:
            tree = result
        node_count = len(tree.nodes) if tree else 0
        link_count = len(tree.links) if tree else 0
        if tree:
            tree.name = f"__health_{name}"
        results["pass"] += 1
        results["builders"].append({
            "name": name, "label": label, "status": "pass",
            "category": category, "nodes": node_count, "links": link_count,
        })
    except Exception as e:
        results["fail"] += 1
        results["builders"].append({
            "name": name, "label": label, "status": "fail",
            "category": category, "error": str(e)[:200],
        })

print(f"=== Melodia Studio GN Builder Health Check ===")
print(f"Total: {len(GROUP_BUILDERS)} | Pass: {results['pass']} | Fail: {results['fail']} | Skip: {results['skip']}")
print(f"Categories: {len(set(b.get('category','?') for b in results['builders']))}")
print()

if results["fail"]:
    print("FAILED BUILDERS:")
    for b in results["builders"]:
        if b["status"] == "fail":
            print(f"  [{b['category']}] {b['name']} ({b['label']}): {b['error'][:100]}")

print()
print("PASSED BUILDERS:")
for b in results["builders"]:
    if b["status"] == "pass":
        print(f"  [{b['category']}] {b['name']} ({b['label']}) — {b['nodes']} nodes, {b['links']} links")

print()
print(f"=== SUMMARY: {results['pass']}/{len(GROUP_BUILDERS)} builders healthy ===")

# Also verify the 49 count
print(f"STUDIO_LABELS count: {len(STUDIO_LABELS)}")
print(f"GROUP_BUILDERS count: {len(GROUP_BUILDERS)}")
print(f"GROUP_METADATA count: {len(GROUP_METADATA)}")
