import os
import sys

sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile")

# Check project structure
print("=== PROJECT STRUCTURE CHECK ===")
print()

# Check MIs
mi_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Instances\Character"
if os.path.exists(mi_dir):
    print(f"Character MIs in {mi_dir}:")
    for f in sorted(os.listdir(mi_dir)):
        if f.startswith("MI_Character_Melusina"):
            full = os.path.join(mi_dir, f)
            size = os.path.getsize(full)
            print(f"  - {f} ({size} bytes)")
else:
    print(f"Directory not found: {mi_dir}")

# Check masters
master_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Masters"
if os.path.exists(master_dir):
    print(f"\nMasters in {master_dir}:")
    for f in sorted(os.listdir(master_dir)):
        if "MelodiaInk" in f or "SDF" in f or "Glitter" in f:
            full = os.path.join(master_dir, f)
            size = os.path.getsize(full)
            print(f"  - {f} ({size} bytes)")
else:
    print(f"Directory not found: {master_dir}")

# Check SDF directory
sdf_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina"
if os.path.exists(sdf_dir):
    print(f"\nMelusina directory contents:")
    for f in sorted(os.listdir(sdf_dir)):
        if f.startswith("SDF") or "Musical" in f:
            full = os.path.join(sdf_dir, f)
            size = os.path.getsize(full)
            print(f"  - {f} ({size} bytes)")
else:
    print(f"Directory not found: {sdf_dir}")

# Check glitter masters
glitter_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Masters"
if os.path.exists(glitter_dir):
    print(f"\nGlitter-related masters:")
    for f in sorted(os.listdir(glitter_dir)):
        if "Glitter" in f:
            full = os.path.join(glitter_dir, f)
            size = os.path.getsize(full)
            print(f"  - {f} ({size} bytes)")
PYEOF