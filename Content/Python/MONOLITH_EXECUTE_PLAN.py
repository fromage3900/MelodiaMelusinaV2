"""
MASTER EXECUTION SCRIPT: Full Plan via Monolith MCP

Orchestrates all remaining work using Monolith HTTP REST API:
  Phase A: MelodiaCore + IridescenceEdgeSoftness (Monolith material_query)
  Phase B: Melusina hair + WP lighting/captures (Monolith mesh_query + export)
  Phase C: Documentation (Python audit scripts)

REQUIREMENTS:
  - Unreal Editor running (BS_GodFile.uproject)
  - Monolith MCP active on port 9316
  - Python 3.9+
  - ~30-45 minutes (mostly async operations)

USAGE:
    python MONOLITH_EXECUTE_PLAN.py

OUTPUT:
    - IridescenceEdgeSoftness parameter added to M_Master_Toon_Universal
    - SK_Melusina_Hair imported
    - 4 WP level captures exported (1920x1080 EXR)
    - ASSET_CATALOG.md, PLATFORM_ONBOARDING.md, KNOWN_ISSUES.md generated
    - Ready to commit + push
"""

import subprocess
import sys
import requests
from pathlib import Path

PROJECT_ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
SCRIPTS_DIR = PROJECT_ROOT / "Content" / "Python"
MONOLITH_BASE = "http://localhost:9316"


def check_monolith():
    """Verify Monolith is running."""
    try:
        response = requests.get(f"{MONOLITH_BASE}/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Monolith v{data.get('version')} on port 9316")
            return True
    except:
        pass
    return False


def check_editor():
    """Verify Unreal Editor is running."""
    import psutil
    try:
        for proc in psutil.process_iter(['name']):
            if 'UE4Editor' in proc.name() or 'UnrealEditor' in proc.name():
                return True
    except:
        pass
    return False


def run_phase(phase_name, script_name):
    """Run a phase script."""
    print(f"\n{'=' * 80}")
    print(f"EXECUTING: {phase_name}")
    print(f"{'=' * 80}\n")

    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            timeout=600  # 10 min per phase
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠ {phase_name} timed out")
        return False
    except Exception as e:
        print(f"❌ {phase_name} error: {e}")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║             ENVIRONMENT PORTFOLIO — MONOLITH MCP EXECUTION PLAN            ║
║                         Full Automation (A → B → C)                        ║
╚════════════════════════════════════════════════════════════════════════════╝

CHECKLIST:
  □ Unreal Editor is open (BS_GodFile.uproject)
  □ Monolith plugin loaded (should see "v0.20.3" message below)
  □ All C++ plugins compiled successfully (Ctrl+Shift+B)
  □ No compile errors in Output Log

ESTIMATED TIME: 30–45 minutes
  - Phase A: 10 min (Monolith material ops + tests)
  - Phase B: 15 min (Hair import + WP export loop)
  - Phase C: 10 min (Documentation generation)
  - Final: 5 min (Commit + push)

""")

    # Pre-flight checks
    print("PRE-FLIGHT CHECKS:")
    print("-" * 80)

    if not check_monolith():
        print("❌ Monolith not responding on port 9316")
        print("   Ensure:")
        print("   1. Unreal Editor is running")
        print("   2. Monolith plugin is enabled in BS_GodFile.uproject")
        print("   3. Editor has finished loading all plugins (check Output Log)")
        print("   4. No firewall blocking localhost:9316")
        return False

    # Editor check (optional)
    print("✓ Monolith is running")
    print("✓ Ready to execute")

    all_phases_ok = True

    # PHASE A
    print("\n" + "─" * 80)
    phase_a_ok = run_phase(
        "PHASE A: MelodiaCore + IridescenceEdgeSoftness",
        "monolith_execute_phase_a.py"
    )
    if not phase_a_ok:
        all_phases_ok = False

    # PHASE B
    print("\n" + "─" * 80)
    phase_b_ok = run_phase(
        "PHASE B: Melusina Hair + WP Lighting",
        "monolith_execute_phase_b.py"
    )
    if not phase_b_ok:
        all_phases_ok = False

    # PHASE C
    print("\n" + "─" * 80)
    phase_c_ok = run_phase(
        "PHASE C: Documentation",
        "execute_phase_c_docs.py"
    )
    if not phase_c_ok:
        all_phases_ok = False

    # FINAL SUMMARY
    print(f"\n{'=' * 80}")
    print("EXECUTION COMPLETE")
    print(f"{'=' * 80}\n")

    if phase_a_ok:
        print("✅ PHASE A: MelodiaCore tests + Iridescence parameter")
    else:
        print("⚠️ PHASE A: Needs manual Material Editor verification")

    if phase_b_ok:
        print("✅ PHASE B: Hair import + WP captures exported")
    else:
        print("⚠️ PHASE B: Check Content Browser for import status")

    if phase_c_ok:
        print("✅ PHASE C: Documentation generated")
    else:
        print("⚠️ PHASE C: Check Docs/ folder")

    print(f"\n{'=' * 80}")
    print("NEXT STEPS (Commit & Push):")
    print(f"{'=' * 80}\n")

    print("1. Review generated files:")
    print(f"   - Docs/ASSET_CATALOG.md")
    print(f"   - Docs/PLATFORM_ONBOARDING.md")
    print(f"   - Docs/KNOWN_ISSUES_AND_WORKAROUNDS.md")
    print(f"   - Saved/Captures/L_WP_*.exr (4 screenshots)")

    print("\n2. Verify material parameter:")
    print("   - Open M_Master_Toon_Universal")
    print("   - Find 'IridescenceEdgeSoftness' in parameter list")

    print("\n3. Verify MelodiaCore tests:")
    print("   - Window → Testing → Automation")
    print("   - Search 'Melodia.CoreRules'")
    print("   - Run tests (all 6 should PASS)")

    print("\n4. Commit:")
    print("   git add -A")
    print('   git commit -m "feat: Phase A-C complete (Monolith automation)"')
    print("   git push origin feature/recursive-learner")

    print("\n5. After verification, execute P0:")
    print("   - Snap Cam_Hero_Establishing to terrain per level")
    print("   - Fix MI_NikkiHero_* + MI_Show_CelestialNebula refs")
    print("   - Run MRQ preset capture")
    print("   - Website ingest")

    print("\n" + "=" * 80)
    if all_phases_ok:
        print("✓ ALL PHASES EXECUTED SUCCESSFULLY")
        print("  Portfolio is ready for P0 hero captures!")
    else:
        print("⚠ SOME PHASES NEED ATTENTION")
        print("  See notes above")
    print("=" * 80 + "\n")

    return all_phases_ok


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
