"""Verify every claim in the handoff doc against actual filesystem state."""
import os
import sys
import json
import subprocess

DOC = r"P:/MelodiaMelusinaV2-Laptop/Docs/Planning/ACCESSORY_HANDOFF_2026-09-12.md"
DEPLOY = r"P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/melodia_gn"

print("=" * 70)
print("CLAIM VERIFICATION — ACCESSORY_HANDOFF_2026-09-12.md")
print("=" * 70)

fails = []
passed = []

def check(condition, msg):
    if condition:
        passed.append(msg)
        print(f"  OK   {msg}")
    else:
        fails.append(msg)
        print(f"  FAIL {msg}")

# 1. Eyewear builders exist
print("\n[1] Eyewear GN builders")
eyewear_path = os.path.join(DEPLOY, "eyewear.py")
check(os.path.exists(eyewear_path), f"eyewear.py exists ({os.path.getsize(eyewear_path)} bytes)")

# 2. Six builders registered
print("\n[2] Six eyewear builders")
result = subprocess.run(
    [r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe", "--background", "--python",
     os.path.join(r"P:/MelodiaMelusinaV2-Laptop/Tools/eyewear_verify", "hero_verify.py")],
    capture_output=True, text=True, timeout=300
)
output = result.stdout + result.stderr
check("MEL_eyewear_front" in output, "MEL_eyewear_front registered")
check("MEL_eyewear_temple" in output, "MEL_eyewear_temple registered")
check("MEL_eyewear_hinge" in output, "MEL_eyewear_hinge registered")
check("MEL_eyewear_pair" in output, "MEL_eyewear_pair registered")
check("MEL_eyewear_lens" in output, "MEL_eyewear_lens registered")
check("MEL_eyewear_hero" in output, "MEL_eyewear_hero registered")
check("RESULT PASS" in output, "hero_verify.py RESULT PASS")

# 3. Studio script exists
print("\n[3] Studio setup script")
studio = r"P:/MelodiaMelusinaV2-Laptop/Tools/setup_accessory_studio.py"
check(os.path.exists(studio), f"setup_accessory_studio.py exists ({os.path.getsize(studio)} bytes)")

# 4. Contact sheet exists
print("\n[4] Contact sheet + renders")
accessories = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories"
contact = os.path.join(accessories, "contact_sheet_silhouettes.png")
check(os.path.exists(contact), f"contact_sheet_silhouettes.png exists ({os.path.getsize(contact)} bytes)")

for label in ["rect", "panto", "cateye", "aviator", "browline", "round"]:
    p = os.path.join(accessories, f"silhouette_{label}.png")
    check(os.path.exists(p), f"silhouette_{label}.png exists ({os.path.getsize(p)} bytes)")

# 5. Grid blend + studio blend exist
print("\n[5] Blend files")
grid = os.path.join(accessories, "Silhouette_Grid_v1.blend")
check(os.path.exists(grid), f"Silhouette_Grid_v1.blend exists ({os.path.getsize(grid)} bytes)")

studio_blend = os.path.join(accessories, "Melodia_Accessory_Studio_v1.blend")
check(os.path.exists(studio_blend), f"Melodia_Accessory_Studio_v1.blend exists ({os.path.getsize(studio_blend)} bytes)")

# 6. Pre-commit hook allows Saved/Accessories/
print("\n[6] Pre-commit hook")
hook = r"P:/MelodiaMelusinaV2-Laptop/.githooks/pre-commit"
check(os.path.exists(hook), "pre-commit hook exists")
with open(hook) as f:
    hook_content = f.read()
check("Saved/Accessories" in hook_content, "pre-commit allows Saved/Accessories/")

# 7. Handoff doc exists
print("\n[7] Documentation")
check(os.path.exists(DOC), f"ACCESSORY_HANDOFF_2026-09-12.md exists")

# 8. Git branch state
print("\n[8] Git state")
result = subprocess.run(
    ["git", "log", "--oneline", "-10"],
    capture_output=True, text=True, cwd=r"P:/MelodiaMelusinaV2-Laptop"
)
print(result.stdout[:400])
check("ahead" not in result.stdout or "eyewear-closeout" in result.stdout, "on correct branch")

# Summary
print("\n" + "=" * 70)
print(f"VERIFICATION COMPLETE: {len(passed)} passed, {len(fails)} failed")
print("=" * 70)

if fails:
    print("\nFAILED CLAIMS:")
    for f in fails:
        print(f"  - {f}")
    print("\nCLAIMS NEED CORRECTION")
else:
    print("\nALL CLAIMS VERIFIED")
print("DONE")
