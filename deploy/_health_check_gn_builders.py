"""Health check for all Melodia Studio GN builders — run inside Blender 5.2.

Loads the monolith from deploy/surreal_architecture_gen.py explicitly so the
incomplete surreal_architecture_gen/ package stub cannot shadow it.

Usage:
  blender --background --factory-startup --python deploy/_health_check_gn_builders.py
"""
import sys
import os
import json
import importlib.util

DEPLOY = os.path.dirname(os.path.abspath(__file__))
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

# Prefer deploy over AppData if both are present.
addons = os.path.join(
    os.environ.get("APPDATA", ""),
    "Blender Foundation", "Blender", "5.2", "scripts", "addons",
)
if os.path.isdir(addons) and addons not in sys.path:
    sys.path.append(addons)

# Load monolith .py by path (avoids broken surreal_architecture_gen/ package).
mono_path = os.path.join(DEPLOY, "surreal_architecture_gen.py")
if not os.path.isfile(mono_path):
    raise SystemExit(f"Missing monolith: {mono_path}")

# If a stub package already claimed the name, remove it first.
sys.modules.pop("surreal_architecture_gen", None)
# Prevent package directory from winning on re-import.
pkg_dir = os.path.join(DEPLOY, "surreal_architecture_gen")
# importlib file location binds the module name to the .py file.
spec = importlib.util.spec_from_file_location(
    "surreal_architecture_gen",
    mono_path,
    submodule_search_locations=[],
)
mono = importlib.util.module_from_spec(spec)
sys.modules["surreal_architecture_gen"] = mono
assert spec.loader is not None
spec.loader.exec_module(mono)
mono.register()

from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA, STUDIO_LABELS, CATEGORY_META

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

print("=== Melodia Studio GN Builder Health Check ===")
print(f"Total: {len(GROUP_BUILDERS)} | Pass: {results['pass']} | Fail: {results['fail']} | Skip: {results['skip']}")
print(f"Categories: {len(set(b.get('category','?') for b in results['builders']))}")
print()

if results["fail"]:
    print("FAILED BUILDERS:")
    for b in results["builders"]:
        if b["status"] == "fail":
            print(f"  [{b['category']}] {b['name']} ({b['label']}): {b['error'][:100]}")

print()
print(f"=== SUMMARY: {results['pass']}/{len(GROUP_BUILDERS)} builders healthy ===")
print(f"STUDIO_LABELS count: {len(STUDIO_LABELS)}")
print(f"GROUP_BUILDERS count: {len(GROUP_BUILDERS)}")
print(f"GROUP_METADATA count: {len(GROUP_METADATA)}")
print(f"CATEGORY_META count: {len(CATEGORY_META)}")

out_path = os.path.join(
    os.path.dirname(DEPLOY), "Saved", "Audit", "gn_builder_health_last.json"
)
try:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {out_path}")
except Exception as exc:
    print(f"Could not write audit JSON: {exc}")

if results["fail"]:
    sys.exit(1)
