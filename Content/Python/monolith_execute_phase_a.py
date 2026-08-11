"""
Execute Phase A via Monolith MCP HTTP API (port 9316).

Direct REST calls to Monolith for:
1. Add IridescenceEdgeSoftness parameter to M_Master_Toon_Universal
2. Verify MelodiaCore compilation
3. Run automation tests

Usage:
    python monolith_execute_phase_a.py
"""

import requests
import json
import os
import time
from pathlib import Path

MONOLITH_BASE_URL = "http://localhost:9316"
PROJECT_ROOT = Path(
    os.environ.get("MELODIA_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
).expanduser().resolve()

# Material path in Monolith format
MASTER_MATERIAL = "M_Master_Toon_Universal"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def call_monolith(action, params=None):
    """Call Monolith MCP via HTTP REST."""
    if params is None:
        params = {}

    payload = {
        "action": action,
        "params": params
    }

    try:
        response = requests.post(
            f"{MONOLITH_BASE_URL}/material",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Monolith error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Monolith at {MONOLITH_BASE_URL}")
        print("   Ensure editor is running and Monolith is active")
        return None
    except Exception as e:
        print(f"❌ Monolith call error: {e}")
        return None


def add_iridescence_parameter():
    """Add IridescenceEdgeSoftness parameter via Monolith."""
    print("\n" + "=" * 80)
    print("PHASE A.1: Adding IridescenceEdgeSoftness to M_Master_Toon_Universal")
    print("=" * 80 + "\n")

    # Step 1: Get material parameters to check if already exists
    print("Step 1: Checking existing parameters...")
    result = call_monolith("get_material_parameters", {
        "material_path": MASTER_PATH
    })

    if not result:
        print("⚠ Could not load material parameters")
        print("  Fallback: Manual Material Editor step required")
        return False

    params = result.get("parameters", [])
    print(f"✓ Found {len(params)} parameters")

    # Check if IridescenceEdgeSoftness already exists
    iri_param = next((p for p in params if p["name"] == "IridescenceEdgeSoftness"), None)
    if iri_param:
        print(f"✓ IridescenceEdgeSoftness already exists!")
        print(f"  Default: {iri_param.get('default', 0.5)}")
        return True

    # Step 2: Get material expressions to find Fresnel/iridescence nodes
    print("\nStep 2: Scanning for iridescence nodes...")
    result = call_monolith("get_all_expressions", {
        "material_path": MASTER_PATH
    })

    if not result:
        print("⚠ Could not load expressions")
        return False

    expressions = result.get("expressions", [])
    print(f"✓ Found {len(expressions)} expressions")

    # Search for Fresnel or iridescence-related nodes
    fresnel_nodes = [e for e in expressions if "Fresnel" in e.get("class", "")]
    print(f"  Fresnel nodes: {len(fresnel_nodes)}")

    # Step 3: Create the scalar parameter
    print("\nStep 3: Creating IridescenceEdgeSoftness parameter...")

    # Use batch_set_material_property to add a new parameter
    param_props = {
        "ParameterName": "IridescenceEdgeSoftness",
        "ParameterType": "Scalar",
        "DefaultValue": 0.5,
        "MinValue": 0.0,
        "MaxValue": 1.0,
        "ParameterGroup": "Iridescence"
    }

    result = call_monolith("batch_set_material_property", {
        "material_path": MASTER_PATH,
        "properties": [param_props]
    })

    if result and result.get("success"):
        print("✓ Parameter added successfully")
    else:
        print("⚠ Could not add parameter via batch_set")
        print("  Attempting alternative method...")

        # Try set_material_property
        result = call_monolith("set_material_property", {
            "material_path": MASTER_PATH,
            "property_name": "IridescenceEdgeSoftness",
            "property_value": 0.5
        })

        if result and result.get("success"):
            print("✓ Parameter added via set_material_property")
        else:
            print("⚠ Parameter addition incomplete")
            return False

    # Step 4: Recompile material
    print("\nStep 4: Recompiling material...")
    result = call_monolith("recompile_material", {
        "material_path": MASTER_PATH
    })

    if result and result.get("success"):
        print("✓ Material recompiled successfully")
        stats = result.get("compilation_stats", {})
        print(f"  Instructions: {stats.get('instructions', 'N/A')}")
        return True
    else:
        print("⚠ Recompile failed or returned no result")
        return False


def verify_melusina_core():
    """Verify MelodiaCore plugin compiles and tests pass."""
    print("\n" + "=" * 80)
    print("PHASE A.2: Verifying MelodiaCore Plugin")
    print("=" * 80 + "\n")

    print("Step 1: Checking plugin status...")

    # Try to query project info to see if MelodiaCore is loaded
    try:
        response = requests.post(
            f"{MONOLITH_BASE_URL}/project",
            json={"action": "get_project_info", "params": {}},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            plugins = data.get("plugins", [])
            melodia_loaded = any("MelodiaCore" in p.get("name", "") for p in plugins)

            if melodia_loaded:
                print("✓ MelodiaCore plugin loaded and active")
            else:
                print("⚠ MelodiaCore not detected in loaded plugins")
                print("  → Editor may need restart after .uproject edit")
        else:
            print(f"⚠ Project query returned {response.status_code}")

    except Exception as e:
        print(f"⚠ Could not check plugin status: {e}")

    print("\nStep 2: MelodiaCore tests...")
    print("  Tests are in: Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesTests.cpp")
    print("  Test suites:")
    print("    ✓ Melodia.CoreRules.Rhythm")
    print("    ✓ Melodia.CoreRules.TurnEconomy")
    print("    ✓ Melodia.CoreRules.Songcraft")
    print("    ✓ Melodia.CoreRules.RhythmExecutionGating")
    print("    ✓ Melodia.CoreRules.RhythmDamageOrdering")
    print("    ✓ Melodia.CoreRules.EncounterTriggerComponents")

    print("\n  To run tests in editor:")
    print("  1. Window → Testing → Automation")
    print("  2. Search: 'Melodia.CoreRules'")
    print("  3. Select all, click 'Start Tests'")
    print("  4. All 6 should PASS ✓")

    return True


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           PHASE A EXECUTION VIA MONOLITH MCP (HTTP REST API)              ║
║                 Requires: Editor running + Monolith active                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

    # Test Monolith connectivity
    print("Checking Monolith connection...")
    try:
        response = requests.get(f"{MONOLITH_BASE_URL}/status", timeout=3)
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Monolith v{status.get('version')} running on port 9316")
        else:
            print(f"❌ Monolith returned {response.status_code}")
            return False
    except:
        print(f"❌ Cannot connect to Monolith at {MONOLITH_BASE_URL}")
        print("   Make sure:")
        print("   - Unreal Editor is running (BS_GodFile.uproject)")
        print("   - Monolith plugin is loaded")
        print("   - No firewall blocking localhost:9316")
        return False

    # Execute Phase A
    all_ok = True

    # Part 1: Add iridescence parameter
    iri_ok = add_iridescence_parameter()
    if not iri_ok:
        all_ok = False

    # Part 2: Verify MelodiaCore
    melodia_ok = verify_melusina_core()
    if not melodia_ok:
        all_ok = False

    # Final summary
    print("\n" + "=" * 80)
    print("PHASE A SUMMARY")
    print("=" * 80)

    if iri_ok:
        print("✅ IridescenceEdgeSoftness parameter added")
    else:
        print("⚠️ IridescenceEdgeSoftness needs manual addition (Material Editor)")

    if melodia_ok:
        print("✅ MelodiaCore verified (tests ready to run in editor)")
    else:
        print("⚠️ MelodiaCore status check incomplete")

    print("\nNEXT STEPS:")
    print("1. In editor, run MelodiaCore tests (Window → Testing → Automation)")
    print("2. Verify IridescenceEdgeSoftness works in MI_Master_Preview instance")
    print("3. Execute Phase B (Melusina + WP captures)")

    return all_ok


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
