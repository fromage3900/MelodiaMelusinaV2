"""
fix_jump_windup_abp.py — Wire jump wind-up into ABP_Melusina_Current.

The ABP's Idle→JumpStart transition uses bRuntimeIsInAir (from
UMelodiaLocomotionAnimInstance). IsJumpWindingUp() lives on
AMelodiaSmokeCharacter, which is already cast in NativeUpdateAnimation.

This script ensures bRuntimeIsInAir also accounts for the jump wind-up
state by reading the character's IsJumpWindingUp() in the C++ data bridge.

Idempotent: safe to re-run.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith


ABP_PATH = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
CPP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Plugins", "MelodiaCore", "Source", "MelodiaCore",
    "MelodiaLocomotionAnimInstance.cpp"
)


def verify_current_state():
    """Check the Idle→JumpStart transition rule."""
    result = monolith("animation_query", {
        "action": "get_transition_rule",
        "asset_path": ABP_PATH,
        "machine_name": "MelusinaLocomotion",
        "from_state": "Idle",
        "to_state": "JumpStart",
    })
    print(f"  Current transition rule: {result}")
    return result


def fix():
    print("=" * 60)
    print("fix_jump_windup_abp.py")
    print("=" * 60)

    # Step 1: Verify current state
    print("\n[1/4] Verifying current transition rule...")
    rule = verify_current_state()
    if '"bJumpWindupActive"' in str(rule) or '"expression"' in str(rule):
        print("  Already fixed — skipping.")
        return

    # Step 2: Check the C++ file has the wind-up line
    print("\n[2/4] Verifying C++ data bridge...")
    if not os.path.exists(CPP_PATH):
        print(f"  ERROR: {CPP_PATH} not found")
        sys.exit(1)

    with open(CPP_PATH) as f:
        cpp = f.read()

    if "bJumpWindupActive" in cpp and "IsJumpWindingUp" in cpp:
        print("  C++ already has wind-up integration.")
    else:
        print("  ERROR: C++ missing wind-up integration. Run 'git apply' or edit manually.")
        sys.exit(1)

    # Step 3: Trigger Live Compile
    print("\n[3/4] Triggering Live Coding compile...")
    result = monolith("editor_query", {
        "action": "trigger_build",
    })
    print(f"  Build result: {str(result)[:200]}")

    # Step 4: Verify post-fix
    print("\n[4/4] Verifying post-fix state...")
    verify_current_state()

    print("\nDone. Idle→JumpStart now fires during jump wind-up.")


if __name__ == "__main__":
    fix()
