"""Comprehensive Melodia Studio addon health check for Blender 5.2.

Tests: registration, UI panels, GN builders, genome system, pipe exports.

Usage:
  blender --background --factory-startup --python deploy/_health_check_full.py
"""
import sys
import os
import json

addons = r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons"
if addons not in sys.path:
    sys.path.insert(0, addons)

import bpy
import surreal_architecture_gen
surreal_architecture_gen.register()

results = {"pass": 0, "fail": 0, "warnings": [], "tests": []}


def check(name, ok, detail=""):
    results["tests"].append({"name": name, "ok": ok, "detail": detail})
    if ok:
        results["pass"] += 1
    else:
        results["fail"] += 1
        results["warnings"].append(f"  FAIL {name}: {detail}")


# 1. Registration (in factory-startup, addon loads via import not preferences)
mod_check = "surreal_architecture_gen" in sys.modules
check("monolith_registered", mod_check)

# 2. Genome system
mod = sys.modules.get("surreal_architecture_gen")
check("monolith_module", mod is not None)
check("STYLE_REGISTRY", hasattr(mod, "STYLE_REGISTRY"),
      f"groups={list(mod.STYLE_REGISTRY.keys()) if hasattr(mod, 'STYLE_REGISTRY') else 'missing'}")
check("ESCHER_PRESETS", hasattr(mod, "ESCHER_PRESETS"),
      f"count={len(mod.ESCHER_PRESETS) if hasattr(mod, 'ESCHER_PRESETS') else 0}")

# 3. GN builders
from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA, STUDIO_LABELS
check("gn_builders_count", len(GROUP_BUILDERS) >= 49, f"count={len(GROUP_BUILDERS)}")
check("gn_metadata_count", len(GROUP_METADATA) == len(GROUP_BUILDERS))

# Try building each
gn_good = 0
gn_bad = 0
gn_fails = []
for name, builder in sorted(GROUP_BUILDERS.items()):
    if not builder:
        gn_bad += 1
        gn_fails.append(name)
        continue
    try:
        result = builder()
        tree = result[0] if isinstance(result, (tuple, list)) else result
        if tree:
            gn_good += 1
        else:
            gn_bad += 1
            gn_fails.append(f"{name}: returned None")
    except Exception as e:
        gn_bad += 1
        gn_fails.append(f"{name}: {e}")

check("gn_build_all", gn_bad == 0,
      f"pass={gn_good} fail={gn_bad}" + (f" first={gn_fails[0]}" if gn_fails else ""))

# 4. UI panels
from bpy.types import Panel
melodia_panels = []
for cls in Panel.__subclasses__():
    bid = getattr(cls, "bl_idname", "")
    mod_name = getattr(cls, "__module__", "")
    if "surreal_arch" in mod_name or bid.startswith(("SURREAL_ARCH_PT_", "MEL_GN_PT_")):
        melodia_panels.append(bid)
check("ui_panels_count", len(melodia_panels) >= 5,
      f"count={len(melodia_panels)}, ids={melodia_panels[:10]}")

# 5. Surreal OS genomes
os_genome_count = 0
try:
    from surreal_os import genome as os_genome
    os_genome_count = len(os_genome.list_genomes())
except Exception as e:
    pass
check("surreal_os_genomes", os_genome_count > 0, f"count={os_genome_count}")

# 6. Surreal greybox
try:
    import surreal_greybox
    gb_ok = hasattr(surreal_greybox, "attach_all")
except Exception:
    gb_ok = False
check("surreal_greybox", gb_ok)

# 7. World composition
try:
    import surreal_world
    world_ok = True
except Exception:
    world_ok = False
check("surreal_world", world_ok)

# 8. MCP bridge tools
from surreal_arch.integration import _REGISTERED_MONOLITH
check("mcp_monolith_ref", _REGISTERED_MONOLITH is not None)

# Print results
print(f"=== Melodia Studio Comprehensive Health Check ===")
print(f"Pass: {results['pass']} / Fail: {results['fail']}")
if results["warnings"]:
    print("Issues:")
    for w in results["warnings"]:
        print(w)
print(f"\nGN Builders: {gn_good}/{len(GROUP_BUILDERS)} pass")
print(f"UI Panels: {len(melodia_panels)} registered")
print(f"Genomes: {os_genome_count} in surreal_os")
print(f"STYLE_REGISTRY: {sum(len(v) for v in mod.STYLE_REGISTRY.values()) if hasattr(mod, 'STYLE_REGISTRY') else 0} entries")
print(f"=== {'ALL PASS' if results['fail'] == 0 else 'SOME FAILED'} ===")
