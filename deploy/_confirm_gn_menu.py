"""Confirm Melodia GN menu catalog size after _rebuild_derived_data."""
import importlib.util
import os
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

mono_path = os.path.join(DEPLOY, "surreal_architecture_gen.py")
sys.modules.pop("surreal_architecture_gen", None)
spec = importlib.util.spec_from_file_location(
    "surreal_architecture_gen", mono_path, submodule_search_locations=[]
)
mono = importlib.util.module_from_spec(spec)
sys.modules["surreal_architecture_gen"] = mono
spec.loader.exec_module(mono)
mono.register()

from surreal_arch.melodia_gn.core import (
    GROUP_BUILDERS,
    GROUP_METADATA,
    TREE_TYPES,
    TREE_CATEGORIES,
    _rebuild_derived_data,
)

_rebuild_derived_data()

n_builders = len(GROUP_BUILDERS)
n_meta = len(GROUP_METADATA)
n_trees = len(TREE_TYPES)
n_cats = len(TREE_CATEGORIES)
print(f"GROUP_BUILDERS={n_builders}")
print(f"GROUP_METADATA={n_meta}")
print(f"TREE_TYPES (GN menu)={n_trees}")
print(f"TREE_CATEGORIES={n_cats}")
for cid, info in TREE_CATEGORIES.items():
    print(f"  [{cid}] {info.get('label')} trees={len(info.get('trees', []))}")

ok = n_builders == 165 and n_trees >= 165
print(f"GN_MENU_OK={ok}")
if not ok:
    raise SystemExit(1)
